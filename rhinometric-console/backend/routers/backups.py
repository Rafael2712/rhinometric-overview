"""
Backup router - API endpoints for backup management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from routers.auth import get_current_user
from services.backup_service import (
    create_backup,
    list_backups,
    count_backups,
    get_latest_backup,
    get_latest_successful,
    get_latest_failed,
    get_backup_by_id,
)

router = APIRouter(tags=["backups"])


@router.post("/create")
def create_backup_endpoint(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new backup. Returns artifact (even on failure)."""
    artifact = create_backup(db, created_by=current_user.username)
    response = artifact.to_dict()
    if artifact.status == "failed":
        response["_warning"] = "Backup failed - see error_type and error_message"
    return response


@router.get("/history")
def get_backup_history(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get paginated backup history."""
    backups = list_backups(db, limit=limit, offset=offset)
    total = count_backups(db)
    return {
        "items": [b.to_dict() for b in backups],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/summary")
def get_backup_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get backup summary stats for dashboard cards."""
    total = count_backups(db)
    latest = get_latest_backup(db)
    latest_success = get_latest_successful(db)
    latest_failed = get_latest_failed(db)

    return {
        "total_backups": total,
        "latest_backup": latest.to_dict() if latest else None,
        "latest_successful": latest_success.to_dict() if latest_success else None,
        "latest_failed": latest_failed.to_dict() if latest_failed else None,
    }


@router.get("/{backup_id}")
def get_backup_detail(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get details of a specific backup."""
    backup = get_backup_by_id(db, backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    return backup.to_dict()
