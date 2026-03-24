"""
Services Grouped Router — GET /api/services/grouped

Returns external services organized by group_name with aggregated
health status per group. Designed for the Services V2 UI (Task 22).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database import get_db
from routers.auth import get_current_user
from models.user import User as UserModel
from models.external_service import ExternalService, ServiceStatus

import logging

logger = logging.getLogger("rhinometric.services_grouped")

router = APIRouter()


# ── Response schemas ────────────────────────────────────────────

class GroupedServiceItem(BaseModel):
    id: int
    name: str
    service_type: str
    catalog_type: Optional[str] = None
    category: Optional[str] = None
    group_name: Optional[str] = None
    environment: Optional[str] = None
    enabled: bool = True
    status: str = "unknown"
    status_message: Optional[str] = None
    latency: Optional[float] = None
    telemetry_status: str = "not_configured"
    last_check: Optional[str] = None
    monitoring_mode: str = "synthetic_only"
    telemetry_attached: bool = False
    metrics_enabled: bool = False
    logs_enabled: bool = False
    traces_enabled: bool = False


class ServiceGroup(BaseModel):
    group_name: str
    status: str  # healthy | degraded | down
    total: int
    up: int
    down: int
    services: List[GroupedServiceItem]


# ── Health aggregation logic ────────────────────────────────────

def _compute_group_health(services: list) -> str:
    """
    Compute aggregated health for a group:
    - healthy: all enabled services are UP
    - degraded: at least one non-UP but majority still UP
    - down: majority of enabled services are DOWN/ERROR
    """
    enabled = [s for s in services if s.enabled]
    if not enabled:
        return "healthy"

    up_count = sum(
        1 for s in enabled
        if (s.status.value if hasattr(s.status, "value") else s.status) == "up"
    )
    down_count = sum(
        1 for s in enabled
        if (s.status.value if hasattr(s.status, "value") else s.status) in ("down", "error")
    )
    total = len(enabled)

    if up_count == total:
        return "healthy"
    if down_count > total / 2:
        return "down"
    return "degraded"


# ── Endpoint ────────────────────────────────────────────────────

@router.get("/grouped", response_model=List[ServiceGroup])
def get_services_grouped(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Returns all external services grouped by group_name.
    Groups sorted: degraded first, down second, healthy last.
    """
    all_services = (
        db.query(ExternalService)
        .order_by(ExternalService.name.asc())
        .all()
    )

    # Build groups
    groups_map: dict = {}
    for svc in all_services:
        gname = svc.group_name or "Default"
        if gname not in groups_map:
            groups_map[gname] = []
        groups_map[gname].append(svc)

    # Build response
    result = []
    for gname, svcs in groups_map.items():
        enabled_svcs = [s for s in svcs if s.enabled]
        up_count = sum(
            1 for s in enabled_svcs
            if (s.status.value if hasattr(s.status, "value") else s.status) == "up"
        )
        down_count = sum(
            1 for s in enabled_svcs
            if (s.status.value if hasattr(s.status, "value") else s.status) in ("down", "error")
        )

        items = []
        for s in svcs:
            status_val = s.status.value if hasattr(s.status, "value") else str(s.status)
            ts_val = s.telemetry_status.value if hasattr(s.telemetry_status, "value") else str(s.telemetry_status or "not_configured")
            mm_val = s.monitoring_mode.value if hasattr(s.monitoring_mode, "value") else str(s.monitoring_mode or "synthetic_only")

            items.append(GroupedServiceItem(
                id=s.id,
                name=s.name,
                service_type=s.service_type.value if hasattr(s.service_type, "value") else str(s.service_type),
                catalog_type=s.catalog_type,
                category=s.category,
                group_name=s.group_name or "Default",
                environment=s.environment,
                enabled=s.enabled,
                status=status_val,
                status_message=s.status_message,
                latency=s.last_response_time_ms,
                telemetry_status=ts_val,
                last_check=s.last_check_at.isoformat() if s.last_check_at else None,
                monitoring_mode=mm_val,
                telemetry_attached=s.telemetry_attached or False,
                metrics_enabled=s.metrics_enabled or False,
                logs_enabled=s.logs_enabled or False,
                traces_enabled=s.traces_enabled or False,
            ))

        health = _compute_group_health(svcs)
        result.append(ServiceGroup(
            group_name=gname,
            status=health,
            total=len(svcs),
            up=up_count,
            down=down_count,
            services=items,
        ))

    # Sort: degraded first, then down, then healthy
    priority = {"degraded": 0, "down": 1, "healthy": 2}
    result.sort(key=lambda g: priority.get(g.status, 2))

    return result
