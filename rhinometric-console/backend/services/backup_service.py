"""
Backup service - Phase 3: Management, Delete, Storage, Audit.
Generates ZIP backups, validates integrity, supports restore with
checksum verification, delete, storage stats, and restore audit.
"""

import os
import json
import hashlib
import shutil
import zipfile
import logging
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

from models.external_service import ExternalService
from models.service_dependency import ServiceDependency
from models.backup_artifact import BackupArtifact
from models.restore_log import RestoreLog

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_file_checksum(filepath: str) -> str:
    """Compute SHA256 hex digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


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
    """Validate preconditions before creating a backup."""
    try:
        Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise BackupError(f"Cannot create backup directory: {BACKUP_DIR} - Permission denied", error_type="permission_error")
    except OSError as e:
        raise BackupError(f"Cannot create backup directory: {BACKUP_DIR} - {e}", error_type="storage_error")

    test_file = os.path.join(BACKUP_DIR, f".preflight_{os.getpid()}")
    try:
        with open(test_file, "w") as f:
            f.write("preflight_check")
        os.remove(test_file)
    except PermissionError:
        raise BackupError("Backup directory not writable - Permission denied", error_type="permission_error")
    except OSError as e:
        raise BackupError(f"Backup directory not writable - {e}", error_type="storage_error")

    try:
        usage = shutil.disk_usage(BACKUP_DIR)
        free_mb = usage.free / (1024 * 1024)
        if free_mb < MIN_DISK_SPACE_MB:
            raise BackupError(f"Insufficient disk space: {free_mb:.1f}MB available, {MIN_DISK_SPACE_MB}MB required", error_type="storage_error")
    except BackupError:
        raise
    except Exception:
        pass


def _validate_zip_integrity(storage_path: str) -> None:
    """Validate that the generated ZIP is complete and correct."""
    if not os.path.isfile(storage_path):
        raise BackupError("Backup file was not created", error_type="integrity_error")
    if os.path.getsize(storage_path) == 0:
        raise BackupError("Backup file is empty (0 bytes)", error_type="integrity_error")
    try:
        with zipfile.ZipFile(storage_path, "r") as zf:
            bad = zf.testzip()
            if bad is not None:
                raise BackupError(f"Backup ZIP is corrupted: bad entry '{bad}'", error_type="integrity_error")
            names = zf.namelist()
            for required in REQUIRED_ZIP_ENTRIES:
                if required not in names:
                    raise BackupError(f"Backup ZIP missing required file: {required}", error_type="integrity_error")
    except zipfile.BadZipFile:
        raise BackupError("Backup file is not a valid ZIP archive", error_type="integrity_error")
    except BackupError:
        raise
    except Exception as e:
        raise BackupError(f"Backup integrity check failed: {e}", error_type="integrity_error")


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


# ---------------------------------------------------------------------------
# Create Backup
# ---------------------------------------------------------------------------

def create_backup(db: Session, created_by: str) -> BackupArtifact:
    """Generate a manual backup ZIP with preflight checks, integrity validation, and SHA256 checksum."""
    ts = datetime.now(timezone.utc)
    ts_str = ts.strftime("%Y%m%d_%H%M%S")
    filename = f"rhinometric_backup_{ts_str}.zip"
    storage_path = os.path.join(BACKUP_DIR, filename)

    # Preflight
    try:
        _preflight_check()
    except BackupError as e:
        artifact = BackupArtifact(
            filename=filename, status="failed", backup_type="manual",
            storage_path=storage_path, created_by=created_by,
            platform_version=PLATFORM_VERSION,
            error_message=e.message, error_type=e.error_type,
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        logger.error(f"Backup preflight failed: [{e.error_type}] {e.message}")
        return artifact

    artifact = BackupArtifact(
        filename=filename, status="in_progress", backup_type="manual",
        storage_path=storage_path, created_by=created_by,
        platform_version=PLATFORM_VERSION,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    try:
        total_records = 0

        services = db.query(ExternalService).all()
        services_data = []
        for s in services:
            services_data.append({
                "id": s.id, "name": s.name,
                "service_type": s.service_type.value if s.service_type else None,
                "environment": s.environment, "description": s.description,
                "catalog_type": s.catalog_type, "category": s.category,
                "tags": s.tags, "enabled": s.enabled, "config": s.config,
                "timeout_seconds": s.timeout_seconds,
                "check_interval_seconds": s.check_interval_seconds,
            })
        total_records += len(services_data)

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

        with zipfile.ZipFile(storage_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2, default=str))
            zf.writestr("external_services.json", json.dumps(services_data, indent=2, default=str))
            zf.writestr("service_dependencies.json", json.dumps(deps_data, indent=2, default=str))

        # Integrity validation
        try:
            _validate_zip_integrity(storage_path)
        except BackupError as e:
            _cleanup_corrupt_file(storage_path)
            return _fail_artifact(db, artifact, e.message, e.error_type)

        # Compute checksum
        checksum = _compute_file_checksum(storage_path)
        file_size = os.path.getsize(storage_path)

        artifact.status = "completed"
        artifact.size_bytes = file_size
        artifact.records_exported = total_records
        artifact.checksum = checksum
        db.commit()
        db.refresh(artifact)

        logger.info(f"Backup created: {filename} ({file_size} bytes, {total_records} records, sha256={checksum[:16]}...)")
        return artifact

    except PermissionError as e:
        _cleanup_corrupt_file(storage_path)
        return _fail_artifact(db, artifact, f"Permission denied: {e}", "permission_error")
    except OSError as e:
        _cleanup_corrupt_file(storage_path)
        return _fail_artifact(db, artifact, f"Storage error: {e}", "storage_error")
    except Exception as e:
        _cleanup_corrupt_file(storage_path)
        return _fail_artifact(db, artifact, f"Unexpected error: {type(e).__name__}: {e}", "unexpected_error")


# ---------------------------------------------------------------------------
# Preview Backup
# ---------------------------------------------------------------------------

def preview_backup(db: Session, backup_id: str) -> dict:
    """Read manifest from a completed backup ZIP and return summary info."""
    artifact = get_backup_by_id(db, backup_id)
    if not artifact:
        raise BackupError("Backup not found", error_type="unexpected_error")
    if artifact.status != "completed":
        raise BackupError("Only completed backups can be previewed", error_type="unexpected_error")

    storage_path = artifact.storage_path
    if not os.path.isfile(storage_path):
        raise BackupError("Backup file not found on disk", error_type="storage_error")

    try:
        with zipfile.ZipFile(storage_path, "r") as zf:
            manifest = json.loads(zf.read("manifest.json"))
            services_data = json.loads(zf.read("external_services.json"))
            deps_data = json.loads(zf.read("service_dependencies.json"))
    except Exception as e:
        raise BackupError(f"Could not read backup ZIP: {e}", error_type="integrity_error")

    return {
        "backup_id": str(artifact.id),
        "filename": artifact.filename,
        "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
        "platform_version": manifest.get("platform_version"),
        "created_by": manifest.get("created_by"),
        "checksum": artifact.checksum,
        "contents": {
            "external_services": len(services_data),
            "service_dependencies": len(deps_data),
        },
        "service_names": [s.get("name", "?") for s in services_data[:50]],
    }


# ---------------------------------------------------------------------------
# Restore Backup
# ---------------------------------------------------------------------------

def restore_backup(db: Session, backup_id: str, restored_by: str) -> dict:
    """
    Restore configuration from a completed backup.
    Replaces ExternalService and ServiceDependency tables.
    Validates checksum before restoring.
    Logs the restore for audit.
    """
    artifact = get_backup_by_id(db, backup_id)
    if not artifact:
        raise BackupError("Backup not found", error_type="unexpected_error")
    if artifact.status != "completed":
        raise BackupError("Only completed backups can be restored", error_type="unexpected_error")

    storage_path = artifact.storage_path
    if not os.path.isfile(storage_path):
        raise BackupError("Backup file not found on disk", error_type="storage_error")

    # Validate checksum if available
    if artifact.checksum:
        current_checksum = _compute_file_checksum(storage_path)
        if current_checksum != artifact.checksum:
            raise BackupError(
                f"Checksum mismatch: expected {artifact.checksum[:16]}..., got {current_checksum[:16]}... - backup may be corrupted",
                error_type="integrity_error",
            )

    # Validate ZIP integrity
    _validate_zip_integrity(storage_path)

    # Read data from ZIP
    try:
        with zipfile.ZipFile(storage_path, "r") as zf:
            manifest = json.loads(zf.read("manifest.json"))
            services_data = json.loads(zf.read("external_services.json"))
            deps_data = json.loads(zf.read("service_dependencies.json"))
    except Exception as e:
        raise BackupError(f"Could not read backup ZIP: {e}", error_type="integrity_error")

    # Count current data for summary
    old_services_count = db.query(ExternalService).count()
    old_deps_count = db.query(ServiceDependency).count()

    # Delete current data (order matters: deps first due to FK)
    try:
        db.query(ServiceDependency).delete()
        db.query(ExternalService).delete()
        db.flush()
    except Exception as e:
        db.rollback()
        raise BackupError(f"Failed to clear current data: {e}", error_type="unexpected_error")

    # Insert restored services
    restored_services = 0
    for s_data in services_data:
        try:
            svc = ExternalService(
                id=s_data.get("id"),
                name=s_data["name"],
                service_type=s_data.get("service_type"),
                environment=s_data.get("environment"),
                description=s_data.get("description"),
                catalog_type=s_data.get("catalog_type"),
                category=s_data.get("category"),
                tags=s_data.get("tags"),
                enabled=s_data.get("enabled", True),
                config=s_data.get("config"),
                timeout_seconds=s_data.get("timeout_seconds"),
                check_interval_seconds=s_data.get("check_interval_seconds"),
            )
            db.add(svc)
            restored_services += 1
        except Exception as e:
            logger.warning(f"Skipped service '{s_data.get('name', '?')}': {e}")

    # Insert restored dependencies
    restored_deps = 0
    for d_data in deps_data:
        try:
            dep = ServiceDependency(
                source_service_id=d_data["source_service_id"],
                target_service_id=d_data["target_service_id"],
                dependency_type=d_data.get("dependency_type"),
                description=d_data.get("description"),
            )
            db.add(dep)
            restored_deps += 1
        except Exception as e:
            logger.warning(f"Skipped dependency: {e}")

    # Write restore audit log
    restore_entry = RestoreLog(
        backup_id=artifact.id,
        backup_filename=artifact.filename,
        restored_by=restored_by,
        services_restored=restored_services,
        dependencies_restored=restored_deps,
    )
    db.add(restore_entry)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise BackupError(f"Failed to commit restored data: {e}", error_type="unexpected_error")

    logger.info(
        f"Restore completed from {artifact.filename}: "
        f"{restored_services} services, {restored_deps} dependencies "
        f"(replaced {old_services_count} services, {old_deps_count} dependencies)"
    )

    return {
        "status": "restored",
        "backup_id": str(artifact.id),
        "backup_filename": artifact.filename,
        "restored_by": restored_by,
        "previous": {
            "external_services": old_services_count,
            "service_dependencies": old_deps_count,
        },
        "restored": {
            "external_services": restored_services,
            "service_dependencies": restored_deps,
        },
    }


# ---------------------------------------------------------------------------
# Delete Backup
# ---------------------------------------------------------------------------

def delete_backup(db: Session, backup_id: str) -> dict:
    """Delete a backup artifact and its file from disk. Only completed or failed allowed."""
    artifact = get_backup_by_id(db, backup_id)
    if not artifact:
        raise BackupError("Backup not found", error_type="unexpected_error")
    if artifact.status not in ("completed", "failed"):
        raise BackupError("Only completed or failed backups can be deleted", error_type="unexpected_error")

    filename = artifact.filename
    storage_path = artifact.storage_path

    # Remove file from disk (ignore if missing)
    if storage_path and os.path.isfile(storage_path):
        try:
            os.remove(storage_path)
            logger.info(f"Deleted backup file: {storage_path}")
        except Exception as e:
            logger.warning(f"Could not delete backup file {storage_path}: {e}")

    # Remove DB record
    db.delete(artifact)
    db.commit()
    logger.info(f"Deleted backup record: {filename}")

    return {"status": "deleted", "backup_id": str(backup_id), "filename": filename}


# ---------------------------------------------------------------------------
# Storage Usage
# ---------------------------------------------------------------------------

def get_storage_usage(db: Session) -> dict:
    """Compute total storage used by backups."""
    total_bytes = db.query(sa_func.coalesce(sa_func.sum(BackupArtifact.size_bytes), 0)).scalar()
    completed_count = db.query(BackupArtifact).filter(BackupArtifact.status == "completed").count()
    failed_count = db.query(BackupArtifact).filter(BackupArtifact.status == "failed").count()

    # Disk free space
    disk_free = None
    try:
        usage = shutil.disk_usage(BACKUP_DIR)
        disk_free = usage.free
    except Exception:
        pass

    return {
        "total_bytes": int(total_bytes),
        "completed_count": completed_count,
        "failed_count": failed_count,
        "storage_path": BACKUP_DIR,
        "disk_free_bytes": disk_free,
    }


# ---------------------------------------------------------------------------
# Restore Audit
# ---------------------------------------------------------------------------

def get_last_restore(db: Session) -> dict | None:
    """Get the most recent restore log entry."""
    entry = db.query(RestoreLog).order_by(RestoreLog.restored_at.desc()).first()
    if not entry:
        return None
    return entry.to_dict()


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def list_backups(db: Session, limit: int = 50, offset: int = 0):
    return (
        db.query(BackupArtifact)
        .order_by(BackupArtifact.created_at.desc())
        .offset(offset).limit(limit).all()
    )

def count_backups(db: Session) -> int:
    return db.query(BackupArtifact).count()

def get_latest_backup(db: Session):
    return db.query(BackupArtifact).order_by(BackupArtifact.created_at.desc()).first()

def get_latest_successful(db: Session):
    return (
        db.query(BackupArtifact)
        .filter(BackupArtifact.status == "completed")
        .order_by(BackupArtifact.created_at.desc()).first()
    )

def get_latest_failed(db: Session):
    return (
        db.query(BackupArtifact)
        .filter(BackupArtifact.status == "failed")
        .order_by(BackupArtifact.created_at.desc()).first()
    )

def get_backup_by_id(db: Session, backup_id: str):
    return db.query(BackupArtifact).filter(BackupArtifact.id == backup_id).first()
