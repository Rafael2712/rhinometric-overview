"""
Backup & Recovery router - Phase 1.
Endpoints for manual backup creation, listing, downloading.
"""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from routers.auth import get_current_user, require_role
from models.user import User as UserModel
from services.backup_service import (
    create_backup,
    list_backups,
    count_backups,
    get_latest_backup,
    get_latest_successful,
    get_latest_failed,
    get_backup_by_id,
    BACKUP_DIR,
)

logger = logging.getLogger("rhinometric.backups")

router = APIRouter()


@router.post("", status_code=201)
def trigger_backup(
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
):
    """Create a manual backup. ADMIN/OWNER only."""
    artifact = create_backup(db, created_by=current_user.username)
    if artifact.status == "failed":
        raise HTTPException(status_code=500, detail=f"Backup failed: {artifact.error_message}")
    return artifact.to_dict()


@router.get("")
def get_backups(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List backup artifacts. Any authenticated user."""
    items = list_backups(db, limit=limit, offset=offset)
    total = count_backups(db)
    return {
        "items": [b.to_dict() for b in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/latest")
def get_latest(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Summary of the latest backup state."""
    latest = get_latest_backup(db)
    latest_ok = get_latest_successful(db)
    latest_fail = get_latest_failed(db)
    total = count_backups(db)

    return {
        "latest": latest.to_dict() if latest else None,
        "last_successful": latest_ok.to_dict() if latest_ok else None,
        "last_failed": latest_fail.to_dict() if latest_fail else None,
        "total_backups": total,
        "storage_location": BACKUP_DIR,
    }


@router.get("/{backup_id}/download")
def download_backup(
    backup_id: str,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
):
    """Download a backup ZIP file. ADMIN/OWNER only."""
    artifact = get_backup_by_id(db, backup_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Backup not found")
    if artifact.status != "completed":
        raise HTTPException(status_code=400, detail=f"Backup is not downloadable (status: {artifact.status})")
    if not os.path.isfile(artifact.storage_path):
        raise HTTPException(status_code=404, detail="Backup file not found on disk")

    return FileResponse(
        path=artifact.storage_path,
        filename=artifact.filename,
        media_type="application/zip",
    )
