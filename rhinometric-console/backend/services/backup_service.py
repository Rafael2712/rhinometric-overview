"""
Backup service - Phase 1: Manual backup of external services config.
Generates a ZIP containing exported data + manifest.json.
"""

import os
import json
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


def ensure_backup_dir():
    """Create backup directory if it does not exist."""
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)


def create_backup(db: Session, created_by: str) -> BackupArtifact:
    """
    Generate a manual backup ZIP with:
    - external_services.json
    - service_dependencies.json
    - manifest.json
    """
    ensure_backup_dir()

    ts = datetime.now(timezone.utc)
    ts_str = ts.strftime("%Y%m%d_%H%M%S")
    filename = f"rhinometric_backup_{ts_str}.zip"
    storage_path = os.path.join(BACKUP_DIR, filename)

    # Create DB record first (in_progress)
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

        # ?? Export external services ??
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

        # ?? Export service dependencies ??
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

        # ?? Build manifest ??
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

        # ?? Write ZIP ??
        with zipfile.ZipFile(storage_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2, default=str))
            zf.writestr("external_services.json", json.dumps(services_data, indent=2, default=str))
            zf.writestr("service_dependencies.json", json.dumps(deps_data, indent=2, default=str))

        file_size = os.path.getsize(storage_path)

        # Update record
        artifact.status = "completed"
        artifact.size_bytes = file_size
        artifact.records_exported = total_records
        db.commit()
        db.refresh(artifact)

        logger.info(f"Backup created: {filename} ({file_size} bytes, {total_records} records)")
        return artifact

    except Exception as e:
        logger.error(f"Backup failed: {e}")
        artifact.status = "failed"
        artifact.error_message = str(e)[:2000]
        db.commit()
        db.refresh(artifact)
        return artifact


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
