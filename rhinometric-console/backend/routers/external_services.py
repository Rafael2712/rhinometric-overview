"""
External Services router - CRUD + test connection for HTTP and PostgreSQL connectors.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta, timedelta
from sqlalchemy.orm import Session

from database import get_db
from routers.auth import get_current_user, require_role
from models.user import User as UserModel
from models.external_service import ExternalService, ServiceType, ServiceStatus, MonitoringMode, TelemetryStatus
from routers.telemetry_ingest import generate_telemetry_token
from services.capability_helper import derive_capability_from_dict
from models.external_service_check import ExternalServiceCheck
from models.external_service_check import ExternalServiceCheck
from services.connector_service import test_http_connection, test_postgresql_connection
from services.config_validation import validate_service_config
from services.bulk_http_service import process_bulk_http
from services.bulk_import_service import (
    parse_csv, parse_json, process_import,
    generate_csv_template, generate_json_template,
)
from services.state_repository import clear_in_memory_state
from fastapi.responses import PlainTextResponse

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
    # Classification metadata (optional)
    catalog_type: Optional[str] = Field(None, max_length=50, description="Service classification: REST_API, SOAP_API, WEB_APP, MOBILE_API, DATABASE, QUEUE, MICROSERVICE, INTERNAL_SERVICE, EXTERNAL_SERVICE, or custom")
    category: Optional[str] = Field(None, max_length=100, description="Logical grouping: payments, authentication, mobile-backend, analytics, etc.")
    tags: Optional[List[str]] = Field(None, description="Array of string labels: ['critical', 'external', 'payments']")

    # Task 22: Service grouping
    group_name: Optional[str] = Field("Default", max_length=100, description="Service group name")

    # ── Monitoring-mode & telemetry (new domain fields) ──
    monitoring_mode: str = Field(default="synthetic_only", pattern="^(synthetic_only|telemetry_enabled)$")
    synthetic_enabled: bool = True
    metrics_enabled: bool = False
    logs_enabled: bool = False
    traces_enabled: bool = False
    telemetry_attached: bool = False
    telemetry_source_type: Optional[str] = Field(None, max_length=50)
    telemetry_service_key: Optional[str] = Field(None, max_length=255)


class ExternalServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    environment: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    timeout_seconds: Optional[int] = Field(None, ge=1, le=120)
    check_interval_seconds: Optional[int] = Field(None, ge=10, le=86400)
    # Classification metadata (optional)
    catalog_type: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None

    # Task 22: Service grouping
    group_name: Optional[str] = Field(None, max_length=100)

    # ── Monitoring-mode & telemetry (new domain fields) ──
    monitoring_mode: Optional[str] = Field(None, pattern="^(synthetic_only|telemetry_enabled)$")
    synthetic_enabled: Optional[bool] = None
    metrics_enabled: Optional[bool] = None
    logs_enabled: Optional[bool] = None
    traces_enabled: Optional[bool] = None
    telemetry_attached: Optional[bool] = None
    telemetry_source_type: Optional[str] = Field(None, max_length=50)
    telemetry_service_key: Optional[str] = Field(None, max_length=255)


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
    catalog_type: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    group_name: Optional[str] = "Default"
    enabled: bool
    config: Dict[str, Any]
    timeout_seconds: int
    check_interval_seconds: int
    monitoring_mode: str = "synthetic_only"
    synthetic_enabled: bool = True
    metrics_enabled: bool = False
    logs_enabled: bool = False
    traces_enabled: bool = False
    telemetry_attached: bool = False
    telemetry_source_type: Optional[str] = None
    telemetry_service_key: Optional[str] = None
    telemetry_token: Optional[str] = None
    telemetry_status: str = "not_configured"
    last_telemetry_at: Optional[str] = None
    capability: str = "Synthetic only"
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
            service_name=config.get("name", "unknown"),
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
    result = []
    for s in services:
        d = s.to_dict()
        d["capability"] = derive_capability_from_dict(d)
        result.append(d)
    return result


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
    down = sum(1 for s in all_svc if s.status in (ServiceStatus.DOWN, ServiceStatus.ERROR) and s.enabled)
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




# ?????? Bulk Import ???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????

@router.post("/import")
async def import_external_services(
    file: UploadFile = File(...),
    dry_run: bool = Query(default=True, description="If true, validate only without creating services"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_only),
):
    """
    Bulk import external services from CSV or JSON file.

    Two-step flow:
      1. Call with dry_run=true to preview/validate.
      2. Call with dry_run=false to confirm and create services.

    Duplicate policy:
      - Services with the same name AND same primary target (URL or host:port/db)
        as an existing service are SKIPPED.
      - No existing services are modified or deleted.
    """
    # Determine format from filename
    filename = (file.filename or "").lower()
    if not (filename.endswith(".csv") or filename.endswith(".json")):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a .csv or .json file.",
        )

    # Read file content
    try:
        raw_bytes = await file.read()
        content = raw_bytes.decode("utf-8-sig")  # Handle BOM
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # Size guard (max 1MB)
    if len(raw_bytes) > 1_048_576:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 1 MB.")

    # Parse
    if filename.endswith(".csv"):
        rows, parse_error = parse_csv(content)
    else:
        rows, parse_error = parse_json(content)

    if parse_error:
        raise HTTPException(status_code=400, detail=parse_error)

    # Row limit guard
    if len(rows) > 200:
        raise HTTPException(
            status_code=400,
            detail=f"Too many rows ({len(rows)}). Maximum is 200 services per import.",
        )

    # Process
    result = process_import(rows, db, current_user.id, dry_run=dry_run)

    logger.info(
        f"[BulkImport] {'Preview' if dry_run else 'Import'} by user {current_user.username}: "
        f"received={result['total_received']}, valid={result['valid_count']}, "
        f"invalid={result['invalid_count']}, duplicates={result['duplicate_count']}, "
        f"created={result['created_count']}"
    )

    return result


@router.get("/import/template/csv")
def download_csv_template(
    current_user: UserModel = Depends(get_current_user),
):
    """Download a CSV template for bulk service import."""
    return PlainTextResponse(
        content=generate_csv_template(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=rhinometric_services_template.csv"},
    )


@router.get("/import/template/json")
def download_json_template(
    current_user: UserModel = Depends(get_current_user),
):
    """Download a JSON template for bulk service import."""
    return PlainTextResponse(
        content=generate_json_template(),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=rhinometric_services_template.json"},
    )




@router.post("/bulk-http")
def bulk_create_http_services(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_only),
):
    """
    Bulk create multiple HTTP/HTTPS services from a structured payload.

    Two-step flow:
      1. Call with dry_run=true (default) to preview/validate.
      2. Call with dry_run=false to confirm and create services.

    Payload:
    {
        "dry_run": true,
        "common": {
            "base_url": "https://api.example.com",
            "method": "GET",
            "environment": "production",
            "timeout_seconds": 10,
            "check_interval_seconds": 60,
            "enabled": true,
            "catalog_type": "REST_API",
            "category": "payments",
            "tags": ["api"],
            "auth_type": "bearer"
        },
        "items": [
            {"name": "Auth API", "path": "/auth"},
            {"name": "Payments API", "path": "/payments", "method": "POST"}
        ]
    }
    """
    items = payload.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="No items provided.")
    if len(items) > 100:
        raise HTTPException(status_code=400, detail=f"Too many items ({len(items)}). Maximum is 100.")

    result = process_bulk_http(payload, db, current_user.id)
    dry_run = payload.get("dry_run", True)

    logger.info(
        f"[BulkHTTP] {'Preview' if dry_run else 'Create'} by user {current_user.username}: "
        f"received={result['total_received']}, valid={result['valid_count']}, "
        f"invalid={result['invalid_count']}, duplicates={result['duplicate_count']}, "
        f"created={result['created_count']}"
    )

    return result

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
    d = svc.to_dict()
    d["capability"] = derive_capability_from_dict(d)
    return d


@router.post("", response_model=ExternalServiceResponse, status_code=status.HTTP_201_CREATED)
def create_external_service(
    payload: ExternalServiceCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_only),
):
    """Create a new external service (HTTP or PostgreSQL)."""
    # ── Strict config validation ──
    _, val_errors = validate_service_config(
        payload.service_type, payload.config, service_name=payload.name,
    )
    if val_errors:
        raise HTTPException(
            status_code=422,
            detail={"error": "Invalid service configuration", "details": val_errors},
        )

    # ── Validation: synthetic_only forces telemetry off ──
    if payload.monitoring_mode == "synthetic_only":
        payload.telemetry_attached = False
        payload.metrics_enabled = False
        payload.logs_enabled = False
        payload.traces_enabled = False
        payload.telemetry_source_type = None
        payload.telemetry_service_key = None

    # ── Validation: telemetry_enabled requires at least one signal + service key ──
    if payload.monitoring_mode == "telemetry_enabled":
        if not any([payload.metrics_enabled, payload.logs_enabled, payload.traces_enabled]):
            raise HTTPException(
                status_code=422,
                detail="When monitoring mode is 'telemetry_enabled', at least one telemetry signal (metrics, logs, or traces) must be enabled.",
            )
        if not payload.telemetry_service_key or not payload.telemetry_service_key.strip():
            raise HTTPException(
                status_code=422,
                detail="When monitoring mode is 'telemetry_enabled', a non-empty telemetry_service_key is required.",
            )

    svc = ExternalService(
        name=payload.name,
        service_type=ServiceType(payload.service_type),
        environment=payload.environment,
        description=payload.description,
        enabled=payload.enabled,
        config=payload.config,
        timeout_seconds=payload.timeout_seconds,
        check_interval_seconds=payload.check_interval_seconds,
        catalog_type=payload.catalog_type,
        category=payload.category,
        tags=payload.tags,
        group_name=payload.group_name,
        monitoring_mode=MonitoringMode(payload.monitoring_mode),
        synthetic_enabled=payload.synthetic_enabled,
        metrics_enabled=payload.metrics_enabled,
        logs_enabled=payload.logs_enabled,
        traces_enabled=payload.traces_enabled,
        telemetry_attached=payload.telemetry_attached,
        telemetry_source_type=payload.telemetry_source_type,
        telemetry_service_key=payload.telemetry_service_key,
        telemetry_token=generate_telemetry_token() if payload.monitoring_mode == "telemetry_enabled" else None,
        telemetry_status=TelemetryStatus.CONFIGURED if payload.monitoring_mode == "telemetry_enabled" else TelemetryStatus.NOT_CONFIGURED,
        status=ServiceStatus.UNKNOWN,
        created_by=current_user.id,
    )
    db.add(svc)
    db.flush()
    logger.info(f"Created external service: {svc.name} ({svc.service_type})")
    d = svc.to_dict()
    d["capability"] = derive_capability_from_dict(d)
    return d


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

    # ── Strict config validation (if config is being updated) ──
    if "config" in update_data and update_data["config"] is not None:
        # Determine effective service_type
        effective_type = svc.service_type.value
        # Merge secrets before validation: preserve masked passwords
        merged_cfg = dict(update_data["config"])
        existing_cfg = dict(svc.config) if svc.config else {}
        if effective_type == "postgresql":
            if "password" not in merged_cfg or merged_cfg.get("password") == "********":
                merged_cfg["password"] = existing_cfg.get("password", "")
        if effective_type == "http":
            if "auth_value" not in merged_cfg or merged_cfg.get("auth_value") == "********":
                merged_cfg["auth_value"] = existing_cfg.get("auth_value", "")
        _, val_errors = validate_service_config(
            effective_type, merged_cfg, service_name=svc.name,
        )
        if val_errors:
            raise HTTPException(
                status_code=422,
                detail={"error": "Invalid service configuration", "details": val_errors},
            )
        # Use the merged config (with preserved secrets) going forward
        update_data["config"] = merged_cfg

    # ── Validation: synthetic_only forces telemetry off ──
    effective_mode = update_data.get("monitoring_mode", svc.monitoring_mode.value if svc.monitoring_mode else "synthetic_only")
    if effective_mode == "synthetic_only":
        for tf in ("metrics_enabled", "logs_enabled", "traces_enabled", "telemetry_attached"):
            update_data[tf] = False
        update_data["telemetry_source_type"] = None
        update_data["telemetry_service_key"] = None

    # ── Validation: telemetry_enabled requires at least one signal + service key ──
    if effective_mode == "telemetry_enabled":
        eff_metrics = update_data.get("metrics_enabled", svc.metrics_enabled)
        eff_logs = update_data.get("logs_enabled", svc.logs_enabled)
        eff_traces = update_data.get("traces_enabled", svc.traces_enabled)
        if not any([eff_metrics, eff_logs, eff_traces]):
            raise HTTPException(
                status_code=422,
                detail="When monitoring mode is 'telemetry_enabled', at least one telemetry signal (metrics, logs, or traces) must be enabled.",
            )
        eff_key = update_data.get("telemetry_service_key", svc.telemetry_service_key)
        if not eff_key or not str(eff_key).strip():
            raise HTTPException(
                status_code=422,
                detail="When monitoring mode is 'telemetry_enabled', a non-empty telemetry_service_key is required.",
            )

    # Handle telemetry token and status on mode change
    if effective_mode == "telemetry_enabled":
        if not svc.telemetry_token:
            update_data["telemetry_token"] = generate_telemetry_token()
        if svc.telemetry_status == TelemetryStatus.NOT_CONFIGURED:
            update_data["telemetry_status"] = TelemetryStatus.CONFIGURED
    elif effective_mode == "synthetic_only":
        update_data["telemetry_status"] = TelemetryStatus.NOT_CONFIGURED

    # Convert monitoring_mode string to enum
    if "monitoring_mode" in update_data and update_data["monitoring_mode"] is not None:
        update_data["monitoring_mode"] = MonitoringMode(update_data["monitoring_mode"])

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
    d = svc.to_dict()
    d["capability"] = derive_capability_from_dict(d)
    return d


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
    # ── Strict config validation before testing ──
    _, val_errors = validate_service_config(
        payload.service_type, payload.config, service_name="adhoc-test",
    )
    if val_errors:
        raise HTTPException(
            status_code=422,
            detail={"error": "Invalid service configuration", "details": val_errors},
        )

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




# -- Analytics / SLA / MTTR / MTTF -----------------------------------------

@router.get("/{service_id}/analytics")
def get_service_analytics(
    service_id: int,
    hours: int = Query(default=24, ge=1, le=720, description="Hours of history to analyze"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Compute SLA, MTTR, MTTF, incident count, and availability for a service.
    Uses check history to derive all operational intelligence metrics.
    """
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
        .order_by(ExternalServiceCheck.checked_at.asc())
        .all()
    )

    if not checks:
        return {
            "service_id": service_id,
            "service_name": svc.name,
            "period_hours": hours,
            "total_checks": 0,
            "sla_percent": None,
            "uptime_percent": None,
            "mttr_minutes": None,
            "mttf_hours": None,
            "incidents": 0,
            "longest_outage_minutes": None,
            "avg_latency_ms": None,
            "p50_latency_ms": None,
            "p95_latency_ms": None,
            "p99_latency_ms": None,
            "current_streak": 0,
            "current_streak_type": None,
        }

    # ── Basic stats ──
    total = len(checks)
    successes = sum(1 for c in checks if c.status == "up")
    uptime_pct = round((successes / total) * 100, 3) if total else 0

    # ── Latency percentiles ──
    latencies = sorted([c.response_time_ms for c in checks if c.response_time_ms and c.response_time_ms > 0])
    if latencies:
        avg_lat = round(sum(latencies) / len(latencies), 2)
        p50 = round(latencies[int(len(latencies) * 0.50)], 2)
        p95 = round(latencies[min(int(len(latencies) * 0.95), len(latencies) - 1)], 2)
        p99 = round(latencies[min(int(len(latencies) * 0.99), len(latencies) - 1)], 2)
    else:
        avg_lat = p50 = p95 = p99 = None

    # ── Incident detection, MTTR, MTTF ──
    incidents = []
    outage_start = None
    recovery_times = []     # durations of each outage (minutes)
    uptime_durations = []   # durations between incidents (hours)
    last_recovery = None

    for i, c in enumerate(checks):
        is_up = c.status in ("up", "degraded")

        if not is_up and outage_start is None:
            # Start of an outage
            outage_start = c.checked_at
            if last_recovery:
                uptime_durations.append((c.checked_at - last_recovery).total_seconds() / 3600)
            incidents.append({"start": c.checked_at.isoformat()})

        elif is_up and outage_start is not None:
            # Recovery from outage
            outage_mins = (c.checked_at - outage_start).total_seconds() / 60
            recovery_times.append(outage_mins)
            if incidents:
                incidents[-1]["end"] = c.checked_at.isoformat()
                incidents[-1]["duration_minutes"] = round(outage_mins, 1)
            outage_start = None
            last_recovery = c.checked_at

        elif is_up and outage_start is None and last_recovery is None:
            last_recovery = c.checked_at

    # If still in outage at end of window
    if outage_start is not None:
        now = datetime.now(timezone.utc)
        outage_mins = (now - outage_start).total_seconds() / 60
        recovery_times.append(outage_mins)
        if incidents:
            incidents[-1]["end"] = None
            incidents[-1]["duration_minutes"] = round(outage_mins, 1)
            incidents[-1]["ongoing"] = True

    incident_count = len(incidents)
    mttr = round(sum(recovery_times) / len(recovery_times), 1) if recovery_times else None
    mttf = round(sum(uptime_durations) / len(uptime_durations), 2) if uptime_durations else None
    longest_outage = round(max(recovery_times), 1) if recovery_times else None

    # ── Current streak ──
    streak = 0
    streak_type = None
    for c in reversed(checks):
        c_up = c.status in ("up", "degraded")
        if streak_type is None:
            streak_type = "up" if c_up else "down"
        if (c_up and streak_type == "up") or (not c_up and streak_type == "down"):
            streak += 1
        else:
            break

    return {
        "service_id": service_id,
        "service_name": svc.name,
        "period_hours": hours,
        "total_checks": total,
        "sla_percent": uptime_pct,
        "uptime_percent": uptime_pct,
        "mttr_minutes": mttr,
        "mttf_hours": mttf,
        "incidents": incident_count,
        "incident_details": incidents[:20],  # Last 20 incidents max
        "longest_outage_minutes": longest_outage,
        "avg_latency_ms": avg_lat,
        "p50_latency_ms": p50,
        "p95_latency_ms": p95,
        "p99_latency_ms": p99,
        "current_streak": streak,
        "current_streak_type": streak_type,
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

# ── AI Insights ──────────────────────────────────────────────────

from services.ai_analyzer import analyze_service, analyze_all_services


@router.get("/ai/summary")
def get_ai_summary(
    hours: int = Query(default=24, ge=1, le=720, description="Hours of history to analyze"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    AI-powered summary of all external services.
    Returns risk scores, trends, anomalies, and recommendations.
    """
    return analyze_all_services(db, hours)


@router.get("/{service_id}/ai-insights")
def get_service_ai_insights(
    service_id: int,
    hours: int = Query(default=24, ge=1, le=720, description="Hours of history to analyze"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Full AI analysis for a single external service.
    Includes latency analysis, trend detection, anomaly detection,
    failure patterns, predictions, and recommendations.
    """
    result = analyze_service(db, service_id, hours)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result