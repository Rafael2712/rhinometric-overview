"""
External Services router - CRUD + test connection for HTTP and PostgreSQL connectors.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta, timedelta
from sqlalchemy.orm import Session

from database import get_db
from routers.auth import get_current_user, require_role
from models.user import User as UserModel
from models.external_service import ExternalService, ServiceType, ServiceStatus
from models.external_service_check import ExternalServiceCheck
from models.external_service_check import ExternalServiceCheck
from services.connector_service import test_http_connection, test_postgresql_connection

import logging

logger = logging.getLogger("rhinometric.external_services")

router = APIRouter()


# Write operations require ADMIN or OWNER role
admin_only = require_role(["OWNER", "ADMIN"])


# Write operations require ADMIN or OWNER role


# ── Pydantic schemas ────────────────────────────────────────────

class ExternalServiceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    service_type: str = Field(..., pattern="^(http|postgresql)$")
    environment: Optional[str] = None
    description: Optional[str] = None
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=10, ge=1, le=120)
    check_interval_seconds: int = Field(default=60, ge=10, le=86400)


class ExternalServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    environment: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    timeout_seconds: Optional[int] = Field(None, ge=1, le=120)
    check_interval_seconds: Optional[int] = Field(None, ge=10, le=86400)


class TestConnectionRequest(BaseModel):
    service_type: str = Field(..., pattern="^(http|postgresql)$")
    config: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=10, ge=1, le=120)


class ExternalServiceResponse(BaseModel):
    id: int
    name: str
    service_type: str
    environment: Optional[str]
    description: Optional[str]
    enabled: bool
    config: Dict[str, Any]
    timeout_seconds: int
    check_interval_seconds: int
    status: str
    status_message: Optional[str]
    last_check_at: Optional[str]
    last_response_time_ms: Optional[float]
    last_status_code: Optional[int]
    created_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]


# ── Helpers ─────────────────────────────────────────────────────

def _run_test(service_type: str, config: dict, timeout_seconds: int) -> dict:
    """Run a test connection based on service type."""
    if service_type == "http":
        return test_http_connection(
            url=config.get("url", ""),
            method=config.get("method", "GET"),
            health_path=config.get("health_path", ""),
            headers=config.get("headers"),
            auth_type=config.get("auth_type"),
            auth_value=config.get("auth_value"),
            timeout_seconds=timeout_seconds,
        )
    elif service_type == "postgresql":
        return test_postgresql_connection(
            host=config.get("host", "localhost"),
            port=int(config.get("port", 5432)),
            database_name=config.get("database_name", "postgres"),
            username=config.get("username", "postgres"),
            password=config.get("password", ""),
            ssl_mode=config.get("ssl_mode", "prefer"),
            timeout_seconds=timeout_seconds,
        )
    else:
        return {"success": False, "status": "error", "message": f"Unknown type: {service_type}"}


def _update_status(svc: ExternalService, result: dict):
    """Update the service status fields from a test result."""
    svc.status = ServiceStatus(result.get("status", "error"))
    svc.status_message = result.get("message", "")[:500]
    svc.last_response_time_ms = result.get("response_time_ms")
    svc.last_status_code = result.get("status_code")
    svc.last_check_at = datetime.now(timezone.utc)


# ── CRUD Endpoints ──────────────────────────────────────────────

@router.get("", response_model=List[ExternalServiceResponse])
def list_external_services(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """List all external services."""
    services = (
        db.query(ExternalService)
        .order_by(ExternalService.created_at.desc())
        .all()
    )
    return [s.to_dict() for s in services]


@router.get("/summary")
def get_external_services_summary(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Summary stats for the External Services tab header."""
    all_svc = db.query(ExternalService).all()
    total = len(all_svc)
    enabled = sum(1 for s in all_svc if s.enabled)
    up = sum(1 for s in all_svc if s.status == ServiceStatus.UP and s.enabled)
    down = sum(1 for s in all_svc if s.status == ServiceStatus.DOWN and s.enabled)
    degraded = sum(1 for s in all_svc if s.status == ServiceStatus.DEGRADED and s.enabled)
    unknown = sum(1 for s in all_svc if s.status == ServiceStatus.UNKNOWN and s.enabled)
    return {
        "total": total,
        "enabled": enabled,
        "up": up,
        "down": down,
        "degraded": degraded,
        "unknown": unknown,
    }


@router.get("/{service_id}", response_model=ExternalServiceResponse)
def get_external_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get a single external service by ID."""
    svc = db.query(ExternalService).filter(ExternalService.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="External service not found")
    return svc.to_dict()


@router.post("", response_model=ExternalServiceResponse, status_code=status.HTTP_201_CREATED)
def create_external_service(
    payload: ExternalServiceCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_only),
):
    """Create a new external service (HTTP or PostgreSQL)."""
    svc = ExternalService(
        name=payload.name,
        service_type=ServiceType(payload.service_type),
        environment=payload.environment,
        description=payload.description,
        enabled=payload.enabled,
        config=payload.config,
        timeout_seconds=payload.timeout_seconds,
        check_interval_seconds=payload.check_interval_seconds,
        status=ServiceStatus.UNKNOWN,
        created_by=current_user.id,
    )
    db.add(svc)
    db.flush()
    logger.info(f"Created external service: {svc.name} ({svc.service_type})")
    return svc.to_dict()


@router.put("/{service_id}", response_model=ExternalServiceResponse)
def update_external_service(
    service_id: int,
    payload: ExternalServiceUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_only),
):
    """Update an existing external service."""
    svc = db.query(ExternalService).filter(ExternalService.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="External service not found")

    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "config" and value is not None:
            # Merge config: keep existing password if not provided
            existing = dict(svc.config) if svc.config else {}
            if svc.service_type == ServiceType.POSTGRESQL:
                if "password" not in value or value["password"] == "********":
                    value["password"] = existing.get("password", "")
            if svc.service_type == ServiceType.HTTP:
                if "auth_value" not in value or value["auth_value"] == "********":
                    value["auth_value"] = existing.get("auth_value", "")
            setattr(svc, field, value)
        else:
            setattr(svc, field, value)

    db.flush()
    logger.info(f"Updated external service: {svc.name} (id={svc.id})")
    return svc.to_dict()


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_external_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_only),
):
    """Delete an external service. Requires ADMIN or OWNER."""
    svc = db.query(ExternalService).filter(ExternalService.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="External service not found")
    db.delete(svc)
    logger.info(f"Deleted external service: {svc.name} (id={service_id})")
    return None


# ── Test Connection ─────────────────────────────────────────────

@router.post("/test-connection")
def test_connection_adhoc(
    payload: TestConnectionRequest,
    current_user: UserModel = Depends(admin_only),
):
    """Test a connection without saving (ad-hoc, from the form)."""
    result = _run_test(payload.service_type, payload.config, payload.timeout_seconds)
    return result


@router.post("/{service_id}/test")
def test_connection_saved(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_only),
):
    """Test connection for an existing saved service. Requires ADMIN or OWNER."""
    svc = db.query(ExternalService).filter(ExternalService.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="External service not found")

    result = _run_test(svc.service_type.value, svc.config, svc.timeout_seconds)
    _update_status(svc, result)
    db.flush()

    return {
        **result,
        "service_id": svc.id,
        "name": svc.name,
    }


# ── Check History ────────────────────────────────────────────────

@router.get("/{service_id}/history")
def get_service_check_history(
    service_id: int,
    hours: int = Query(default=24, ge=1, le=720, description="Hours of history to return"),
    limit: int = Query(default=200, ge=1, le=5000, description="Max records"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Return check history for a specific service (newest first)."""
    svc = db.query(ExternalService).filter(ExternalService.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="External service not found")

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    checks = (
        db.query(ExternalServiceCheck)
        .filter(
            ExternalServiceCheck.service_id == service_id,
            ExternalServiceCheck.checked_at >= since,
        )
        .order_by(ExternalServiceCheck.checked_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "service_id": service_id,
        "service_name": svc.name,
        "hours": hours,
        "total": len(checks),
        "checks": [
            {
                "id": c.id,
                "status": c.status,
                "response_time_ms": c.response_time_ms,
                "status_code": c.status_code,
                "message": c.message,
                "checked_at": c.checked_at.isoformat() if c.checked_at else None,
            }
            for c in checks
        ],
    }


# ── Toggle Enable/Disable ──────────────────────────────────────

@router.post("/{service_id}/toggle")
def toggle_external_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_only),
):
    """Toggle enabled/disabled. Requires ADMIN or OWNER."""
    svc = db.query(ExternalService).filter(ExternalService.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="External service not found")
    svc.enabled = not svc.enabled
    db.flush()
    return {"id": svc.id, "enabled": svc.enabled}