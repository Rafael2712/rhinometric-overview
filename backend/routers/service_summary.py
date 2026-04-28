"""
Service Summary router — lightweight aggregation endpoint
for the Home dashboard.

GET /api/services/summary

Returns a unified health overview combining external monitored
services and internal platform services.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from routers.auth import get_current_user
from models.user import User as UserModel
from services.service_summary_service import get_services_summary

router = APIRouter()


@router.get("/summary")
async def services_summary(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Global service health summary combining external monitored services
    and internal platform services.

    Response:
    {
        "total_services": 53,
        "external_services": 41,
        "internal_services": 12,
        "healthy": 49,
        "degraded": 2,
        "down": 2,
        "overall_status": "OPERATIONAL"
    }

    Status rules:
    - OPERATIONAL: All services healthy
    - DEGRADED: Any service down OR latency anomalies detected
    - CRITICAL: More than 10% of services down
    """
    return await get_services_summary(db)
