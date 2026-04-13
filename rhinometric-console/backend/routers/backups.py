"""
Backup router - Phase 3: Create, History, Summary, Preview, Restore, Delete, Storage, Audit.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from routers.auth import get_current_user, require_role
from services.backup_service import (
    get_backup_scope,
    BackupError,
    create_backup,
    list_backups,
    count_backups,
    get_latest_backup,
    get_latest_successful,
    get_latest_failed,
    get_backup_by_id,
    preview_backup,
    restore_backup,
    delete_backup,
    get_storage_usage,
    get_last_restore,
)

router = APIRouter(tags=["backups"])


class RestoreRequest(BaseModel):
    confirm: bool = False


class DeleteRequest(BaseModel):
    confirm: bool = False



@router.get("/scope")
def get_scope_endpoint():
    """Return backup scope — what is included and excluded."""
    return get_backup_scope()

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


@router.get("/storage")
def get_storage_endpoint(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get backup storage usage stats."""
    return get_storage_usage(db)


@router.get("/last-restore")
def get_last_restore_endpoint(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get most recent restore audit info."""
    result = get_last_restore(db)
    return result or {"message": "No restores performed yet"}


@router.get("/{backup_id}/preview")
def preview_backup_endpoint(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Preview contents of a backup without restoring."""
    try:
        return preview_backup(db, backup_id)
    except BackupError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/{backup_id}/restore")
def restore_backup_endpoint(
    backup_id: str,
    body: RestoreRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["OWNER", "ADMIN"])),
):
    """
    Restore configuration from a backup.
    Requires confirm=true in the request body.
    Admin/Owner only.
    """
    if not body.confirm:
        raise HTTPException(
            status_code=400,
            detail="Restore requires explicit confirmation. Send {\"confirm\": true} to proceed.",
        )
    try:
        return restore_backup(db, backup_id, restored_by=current_user.username)
    except BackupError as e:
        status_code = 400
        if e.error_type == "integrity_error":
            status_code = 422
        elif e.error_type == "storage_error":
            status_code = 500
        raise HTTPException(status_code=status_code, detail=e.message)


@router.delete("/{backup_id}")
def delete_backup_endpoint(
    backup_id: str,
    body: DeleteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["OWNER", "ADMIN"])),
):
    """
    Delete a backup artifact and file.
    Requires confirm=true. Admin/Owner only.
    Only completed or failed backups can be deleted.
    """
    if not body.confirm:
        raise HTTPException(
            status_code=400,
            detail="Delete requires explicit confirmation. Send {\"confirm\": true} to proceed.",
        )
    try:
        return delete_backup(db, backup_id)
    except BackupError as e:
        raise HTTPException(status_code=400, detail=e.message)


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
