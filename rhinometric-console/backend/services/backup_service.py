"""
Backup service - Phase 1: Manual backup of external services config.
Generates a ZIP containing exported data + manifest.json.
Includes preflight checks and integrity validation.
"""

import os
import json
import shutil
import zipfile
import tempfile
import logging
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session

from models.external_service import ExternalService
from models.service_dependency import ServiceDependency
from models.backup_artifact import BackupArtifact

logger = logging.getLogger("rhinometric.backup_service")

BACKUP_DIR = os.getenv("RHINOMETRIC_BACKUP_DIR", "/opt/rhinometric/backups")
PLATFORM_VERSION = "2.6.0"
MIN_DISK_SPACE_MB = 10
REQUIRED_ZIP_ENTRIES = ["manifest.json", "external_services.json", "service_dependencies.json"]


class BackupError(Exception):
    """Structured backup error with type classification."""
    def __init__(self, message: str, error_type: str = "unexpected_error"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


def init_backup_directory():
    """Ensure backup directory exists and is writable. Called at app startup."""
    try:
        Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
        test_file = os.path.join(BACKUP_DIR, ".init_check")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        logger.info(f"Backup directory ready: {BACKUP_DIR}")
    except PermissionError:
        logger.warning(f"Backup directory not writable: {BACKUP_DIR}")
    except Exception as e:
        logger.warning(f"Could not initialize backup directory: {e}")


def _preflight_check():
    """
    Validate preconditions before creating a backup.
    Creates directory if missing. Checks write permissions and disk space.
    Raises BackupError with appropriate error_type on failure.
    """
    # 1. Ensure directory exists
    try:
        Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise BackupError(
            f"Cannot create backup directory: {BACKUP_DIR} - Permission denied",
            error_type="permission_error"
        )
    except OSError as e:
        raise BackupError(
            f"Cannot create backup directory: {BACKUP_DIR} - {e}",
            error_type="storage_error"
        )

    # 2. Check write permissions with temp file
    test_file = os.path.join(BACKUP_DIR, f".preflight_{os.getpid()}")
    try:
        with open(test_file, "w") as f:
            f.write("preflight_check")
        os.remove(test_file)
    except PermissionError:
        raise BackupError(
            "Backup directory not writable - Permission denied",
            error_type="permission_error"
        )
    except OSError as e:
        raise BackupError(
            f"Backup directory not writable - {e}",
            error_type="storage_error"
        )

    # 3. Check available disk space
    try:
        usage = shutil.disk_usage(BACKUP_DIR)
        free_mb = usage.free / (1024 * 1024)
        if free_mb < MIN_DISK_SPACE_MB:
            raise BackupError(
                f"Insufficient disk space: {free_mb:.1f}MB available, {MIN_DISK_SPACE_MB}MB required",
                error_type="storage_error"
            )
    except BackupError:
        raise
    except Exception:
        pass  # If disk_usage fails, proceed anyway


def _validate_zip_integrity(storage_path: str) -> None:
    """
    Validate that the generated ZIP is complete and correct.
    Raises BackupError if validation fails.
    """
    # 1. File must exist
    if not os.path.isfile(storage_path):
        raise BackupError(
            "Backup file was not created",
            error_type="integrity_error"
        )

    # 2. Size must be > 0
    file_size = os.path.getsize(storage_path)
    if file_size == 0:
        raise BackupError(
            "Backup file is empty (0 bytes)",
            error_type="integrity_error"
        )

    # 3. Must be a valid ZIP with required entries
    try:
        with zipfile.ZipFile(storage_path, "r") as zf:
            bad = zf.testzip()
            if bad is not None:
                raise BackupError(
                    f"Backup ZIP is corrupted: bad entry '{bad}'",
                    error_type="integrity_error"
                )
            names = zf.namelist()
            for required in REQUIRED_ZIP_ENTRIES:
                if required not in names:
                    raise BackupError(
                        f"Backup ZIP missing required file: {required}",
                        error_type="integrity_error"
                    )
    except zipfile.BadZipFile:
        raise BackupError(
            "Backup file is not a valid ZIP archive",
            error_type="integrity_error"
        )
    except BackupError:
        raise
    except Exception as e:
        raise BackupError(
            f"Backup integrity check failed: {e}",
            error_type="integrity_error"
        )


def _cleanup_corrupt_file(storage_path: str):
    """Remove a corrupt or incomplete backup file."""
    try:
        if os.path.isfile(storage_path):
            os.remove(storage_path)
            logger.info(f"Removed corrupt backup file: {storage_path}")
    except Exception as e:
        logger.warning(f"Could not remove corrupt file {storage_path}: {e}")


def _fail_artifact(db: Session, artifact: BackupArtifact, message: str, error_type: str) -> BackupArtifact:
    """Mark a backup artifact as failed with structured error info."""
    artifact.status = "failed"
    artifact.error_message = message[:2000]
    artifact.error_type = error_type
    db.commit()
    db.refresh(artifact)
    return artifact


def create_backup(db: Session, created_by: str) -> BackupArtifact:
    """
    Generate a manual backup ZIP with preflight checks and integrity validation.
    Returns artifact with status 'completed' only if all validations pass.
    """
    ts = datetime.now(timezone.utc)
    ts_str = ts.strftime("%Y%m%d_%H%M%S")
    filename = f"rhinometric_backup_{ts_str}.zip"
    storage_path = os.path.join(BACKUP_DIR, filename)

    # --- Preflight check BEFORE creating DB record ---
    try:
        _preflight_check()
    except BackupError as e:
        artifact = BackupArtifact(
            filename=filename,
            status="failed",
            backup_type="manual",
            storage_path=storage_path,
            created_by=created_by,
            platform_version=PLATFORM_VERSION,
            error_message=e.message,
            error_type=e.error_type,
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        logger.error(f"Backup preflight failed: [{e.error_type}] {e.message}")
        return artifact

    # Create DB record (in_progress)
    artifact = BackupArtifact(
        filename=filename,
        status="in_progress",
        backup_type="manual",
        storage_path=storage_path,
        created_by=created_by,
        platform_version=PLATFORM_VERSION,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    try:
        total_records = 0

        # Export external services
        services = db.query(ExternalService).all()
        services_data = []
        for s in services:
            services_data.append({
                "id": s.id,
                "name": s.name,
                "service_type": s.service_type.value if s.service_type else None,
                "environment": s.environment,
                "description": s.description,
                "catalog_type": s.catalog_type,
                "category": s.category,
                "tags": s.tags,
                "enabled": s.enabled,
                "config": s.config,
                "timeout_seconds": s.timeout_seconds,
                "check_interval_seconds": s.check_interval_seconds,
            })
        total_records += len(services_data)

        # Export service dependencies
        deps = db.query(ServiceDependency).all()
        deps_data = []
        for d in deps:
            deps_data.append({
                "id": str(d.id),
                "source_service_id": d.source_service_id,
                "target_service_id": d.target_service_id,
                "dependency_type": d.dependency_type,
                "description": d.description,
            })
        total_records += len(deps_data)

        # Build manifest
        manifest = {
            "timestamp": ts.isoformat(),
            "platform_version": PLATFORM_VERSION,
            "backup_type": "manual",
            "created_by": created_by,
            "records_exported": total_records,
            "contents": {
                "external_services": len(services_data),
                "service_dependencies": len(deps_data),
            },
        }

        # Write ZIP
        with zipfile.ZipFile(storage_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2, default=str))
            zf.writestr("external_services.json", json.dumps(services_data, indent=2, default=str))
            zf.writestr("service_dependencies.json", json.dumps(deps_data, indent=2, default=str))

        # --- Integrity validation ---
        try:
            _validate_zip_integrity(storage_path)
        except BackupError as e:
            _cleanup_corrupt_file(storage_path)
            return _fail_artifact(db, artifact, e.message, e.error_type)

        file_size = os.path.getsize(storage_path)

        # Mark completed
        artifact.status = "completed"
        artifact.size_bytes = file_size
        artifact.records_exported = total_records
        db.commit()
        db.refresh(artifact)

        logger.info(f"Backup created: {filename} ({file_size} bytes, {total_records} records)")
        return artifact

    except PermissionError as e:
        _cleanup_corrupt_file(storage_path)
        logger.error(f"Backup permission error: {e}")
        return _fail_artifact(db, artifact, f"Permission denied: {e}", "permission_error")

    except OSError as e:
        _cleanup_corrupt_file(storage_path)
        logger.error(f"Backup storage error: {e}")
        return _fail_artifact(db, artifact, f"Storage error: {e}", "storage_error")

    except Exception as e:
        _cleanup_corrupt_file(storage_path)
        logger.error(f"Backup unexpected error: {e}")
        return _fail_artifact(db, artifact, f"Unexpected error: {type(e).__name__}: {e}", "unexpected_error")


def list_backups(db: Session, limit: int = 50, offset: int = 0):
    """List backup artifacts ordered by newest first."""
    return (
        db.query(BackupArtifact)
        .order_by(BackupArtifact.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def count_backups(db: Session) -> int:
    return db.query(BackupArtifact).count()


def get_latest_backup(db: Session):
    """Get the most recent backup artifact."""
    return (
        db.query(BackupArtifact)
        .order_by(BackupArtifact.created_at.desc())
        .first()
    )


def get_latest_successful(db: Session):
    return (
        db.query(BackupArtifact)
        .filter(BackupArtifact.status == "completed")
        .order_by(BackupArtifact.created_at.desc())
        .first()
    )


def get_latest_failed(db: Session):
    return (
        db.query(BackupArtifact)
        .filter(BackupArtifact.status == "failed")
        .order_by(BackupArtifact.created_at.desc())
        .first()
    )


def get_backup_by_id(db: Session, backup_id: str):
    return db.query(BackupArtifact).filter(BackupArtifact.id == backup_id).first()
