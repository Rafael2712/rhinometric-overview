"""
System administration endpoints.
"""
from fastapi import APIRouter, Depends
from routers.auth import get_current_user, require_role
from models.user import User as UserModel
from services.retention_cleanup import get_storage_info, run_cleanup, get_retention_days

import logging

logger = logging.getLogger("rhinometric.system")

router = APIRouter()

admin_only = require_role(["OWNER", "ADMIN"])


@router.get("/storage")
def get_system_storage(
    current_user: UserModel = Depends(admin_only),
):
    """
    Return storage statistics for external_service_checks.
    Includes row count, table size, retention configuration.
    """
    return get_storage_info()


@router.post("/retention/run")
def trigger_retention_cleanup(
    current_user: UserModel = Depends(admin_only),
):
    """
    Manually trigger the retention cleanup job.
    Returns number of deleted rows and duration.
    """
    deleted, duration = run_cleanup()
    return {
        "deleted": deleted,
        "duration_seconds": duration,
        "retention_days": get_retention_days(),
    }
