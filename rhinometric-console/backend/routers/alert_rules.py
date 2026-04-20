"""
Synthetic Monitoring Alert Policies ÔÇö CRUD and evaluation.

Product-oriented alert configuration for synthetic monitoring.
Three rule types: SERVICE_DOWN, HIGH_LATENCY, DEGRADED_HEALTH.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import hashlib

from database import get_db
from routers.auth import get_current_user, require_role
from models.user import User as UserModel
from models.alert_rule import AlertRule
from models.external_service import ExternalService
from logging_config import get_logger

logger = get_logger("alert_rules")

router = APIRouter()

# ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
# Constants
# ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
VALID_RULE_TYPES = {"SERVICE_DOWN", "HIGH_LATENCY", "DEGRADED_HEALTH"}
VALID_SEVERITIES = {"info", "warning", "critical"}

# Legacy compat
VALID_METRICS = {"latency_ms", "error_rate", "availability_pct", "response_time_p95"}
VALID_OPERATORS = {">", "<", ">=", "<="}

# ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
# Schemas
# ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ

class AlertPolicyCreate(BaseModel):
    name: str
    rule_type: str = "SERVICE_DOWN"
    service_id: Optional[int] = None

    # SERVICE_DOWN
    consecutive_failures: int = 3
    critical_escalation_failures: int = 6
    incident_after_seconds: int = 120

    # HIGH_LATENCY
    latency_threshold_ms: Optional[float] = 1000.0
    latency_deviation_pct: Optional[float] = None

    # DEGRADED_HEALTH
    anomaly_score_threshold: Optional[float] = 70.0

    # Common
    sustained_checks: int = 3
    severity: str = "warning"
    cooldown_seconds: int = 120
    enabled: bool = True
    description: Optional[str] = None

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, v):
        if v not in VALID_RULE_TYPES:
            raise ValueError(f"rule_type must be one of {VALID_RULE_TYPES}")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v):
        if v not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {VALID_SEVERITIES}")
        return v

    @field_validator("consecutive_failures")
    @classmethod
    def validate_failures(cls, v):
        if v < 1 or v > 100:
            raise ValueError("consecutive_failures must be 1ÔÇô100")
        return v

    @field_validator("cooldown_seconds")
    @classmethod
    def validate_cooldown(cls, v):
        if v < 0 or v > 86400:
            raise ValueError("cooldown_seconds must be 0ÔÇô86400")
        return v


class AlertPolicyUpdate(BaseModel):
    name: Optional[str] = None
    rule_type: Optional[str] = None
    service_id: Optional[int] = None
    consecutive_failures: Optional[int] = None
    critical_escalation_failures: Optional[int] = None
    incident_after_seconds: Optional[int] = None
    latency_threshold_ms: Optional[float] = None
    latency_deviation_pct: Optional[float] = None
    anomaly_score_threshold: Optional[float] = None
    sustained_checks: Optional[int] = None
    severity: Optional[str] = None
    cooldown_seconds: Optional[int] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, v):
        if v is not None and v not in VALID_RULE_TYPES:
            raise ValueError(f"rule_type must be one of {VALID_RULE_TYPES}")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v):
        if v is not None and v not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {VALID_SEVERITIES}")
        return v


# ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
# Helpers
# ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ

def _rule_to_dict(rule: AlertRule, service_name: str = "") -> dict:
    return {
        "id": str(rule.id),
        "name": rule.name,
        "rule_type": rule.rule_type or "SERVICE_DOWN",
        "service_id": rule.service_id,
        "service_name": service_name or "All Services",

        # SERVICE_DOWN
        "consecutive_failures": rule.consecutive_failures or 3,
        "critical_escalation_failures": rule.critical_escalation_failures or 6,
        "incident_after_seconds": rule.incident_after_seconds or 120,

        # HIGH_LATENCY
        "latency_threshold_ms": rule.latency_threshold_ms,
        "latency_deviation_pct": rule.latency_deviation_pct,

        # DEGRADED_HEALTH
        "anomaly_score_threshold": rule.anomaly_score_threshold,

        # Common
        "sustained_checks": rule.sustained_checks or 3,
        "severity": rule.severity or "warning",
        "cooldown_seconds": rule.cooldown_seconds or 120,
        "enabled": rule.enabled if rule.enabled is not None else True,
        "is_default": rule.is_default if hasattr(rule, 'is_default') and rule.is_default is not None else False,
        "description": rule.description if hasattr(rule, 'description') else None,

        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }


# ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
# CRUD Endpoints
# ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ

admin_only = require_role(["OWNER", "ADMIN"])


@router.get("")
async def list_alert_rules(
    service_id: Optional[int] = Query(None),
    rule_type: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_only),
):
    """List all alert policies with optional filtering."""
    query = db.query(AlertRule)
    if service_id is not None:
        query = query.filter(AlertRule.service_id == service_id)
    if rule_type is not None:
        query = query.filter(AlertRule.rule_type == rule_type)
    if enabled is not None:
        query = query.filter(AlertRule.enabled == enabled)
    query = query.order_by(AlertRule.created_at.desc())
    rules = query.all()

    # Batch-fetch service names
    svc_ids = list({r.service_id for r in rules if r.service_id is not None})
    svc_map = {}
    if svc_ids:
        svcs = db.query(ExternalService.id, ExternalService.name).filter(
            ExternalService.id.in_(svc_ids)
        ).all()
        svc_map = {s.id: s.name for s in svcs}

    return {
        "rules": [_rule_to_dict(r, svc_map.get(r.service_id, "")) for r in rules],
        "total": len(rules),
    }


# Static sub-paths MUST come before /{rule_id} to avoid route conflicts

@router.get("/services/list")
async def list_services_for_rules(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_only),
):
    """Return simplified list of services for rule creation dropdown."""
    svcs = db.query(ExternalService.id, ExternalService.name).filter(
        ExternalService.enabled == True
    ).order_by(ExternalService.name).all()
    return {"services": [{"id": s.id, "name": s.name} for s in svcs]}


@router.post("", status_code=201)
async def create_alert_rule(
    body: AlertPolicyCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
):
    """Create a new alert policy."""
    # Validate service exists if specified
    svc_name = "All Services"
    if body.service_id is not None:
        svc = db.query(ExternalService).filter(ExternalService.id == body.service_id).first()
        if not svc:
            raise HTTPException(status_code=404, detail=f"Service {body.service_id} not found")
        svc_name = svc.name

    rule = AlertRule(
        id=uuid.uuid4(),
        name=body.name,
        rule_type=body.rule_type,
        service_id=body.service_id,
        consecutive_failures=body.consecutive_failures,
        critical_escalation_failures=body.critical_escalation_failures,
        incident_after_seconds=body.incident_after_seconds,
        latency_threshold_ms=body.latency_threshold_ms,
        latency_deviation_pct=body.latency_deviation_pct,
        anomaly_score_threshold=body.anomaly_score_threshold,
        sustained_checks=body.sustained_checks,
        severity=body.severity,
        cooldown_seconds=body.cooldown_seconds,
        enabled=body.enabled,
        description=body.description,
        is_default=False,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    logger.info(f"Alert policy created: {rule.name} ({rule.rule_type})")
    return _rule_to_dict(rule, svc_name)


@router.get("/{rule_id}")
async def get_alert_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_only),
):
    """Get a single alert policy."""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    svc_name = ""
    if rule.service_id:
        svc = db.query(ExternalService).filter(ExternalService.id == rule.service_id).first()
        svc_name = svc.name if svc else ""
    return _rule_to_dict(rule, svc_name)


@router.patch("/{rule_id}")
async def update_alert_rule(
    rule_id: str,
    body: AlertPolicyUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
):
    """Update an existing alert policy."""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    update_data = body.model_dump(exclude_unset=True)

    # Validate service if changing
    if "service_id" in update_data and update_data["service_id"] is not None:
        svc = db.query(ExternalService).filter(
            ExternalService.id == update_data["service_id"]
        ).first()
        if not svc:
            raise HTTPException(status_code=404, detail=f"Service {update_data['service_id']} not found")

    for field, value in update_data.items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)

    svc_name = ""
    if rule.service_id:
        svc = db.query(ExternalService).filter(ExternalService.id == rule.service_id).first()
        svc_name = svc.name if svc else ""

    logger.info(f"Alert policy updated: {rule.name}")
    return _rule_to_dict(rule, svc_name)


@router.delete("/{rule_id}", status_code=204)
async def delete_alert_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
):
    """Delete an alert policy."""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    logger.info(f"Alert policy deleted: {rule.name}")
    return None




# ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
# Auto-resolution: resolve alerts for recovered services
# ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ

def _resolve_recovered_services(db: Session):
    """Resolve alert events for services that have recovered.

    For each enabled service currently UP, find any firing AlertEvent
    from alert_policy source and resolve it. Then check linked incidents.
    Also resolves orphaned incidents for deleted services.
    """
    from models.alert_event import AlertEvent
    from routers.incidents import check_incident_resolution
    from services.alert_noise_filter import on_recovery

    now = datetime.now(timezone.utc)

    # Phase 1.5 Rule 5: SERVICE_DOWN alerts only resolve when service is truly UP
    # Other alerts (HIGH_LATENCY, DEGRADED_HEALTH) resolve when UP or DEGRADED
    truly_up_services = db.query(ExternalService).filter(
        ExternalService.enabled == True,
        ExternalService.status == "up",
    ).all()
    truly_up_names = {svc.name for svc in truly_up_services}

    up_or_degraded_services = db.query(ExternalService).filter(
        ExternalService.enabled == True,
        ExternalService.status.in_(["up", "degraded"]),
    ).all()
    up_or_degraded_names = {svc.name for svc in up_or_degraded_services}

    all_candidate_names = up_or_degraded_names
    if all_candidate_names:
        firing_events = db.query(AlertEvent).filter(
            AlertEvent.status == "firing",
            AlertEvent.source == "alert_policy",
            AlertEvent.entity_name.in_(list(all_candidate_names)),
        ).all()

        resolved_count = 0
        for event in firing_events:
            # Determine rule_type from stored labels
            rule_type = ""
            if event.labels and isinstance(event.labels, dict):
                rule_type = event.labels.get("rule_type", "")

            # Phase 1.5: SERVICE_DOWN only resolves when service is truly UP
            if rule_type == "SERVICE_DOWN":
                if event.entity_name not in truly_up_names:
                    continue  # Service is DEGRADED, not truly recovered from DOWN

            event.status = "resolved"
            event.ended_at = now
            resolved_count += 1
            if event.incident_id:
                try:
                    check_incident_resolution(db, event.incident_id)
                except Exception as e:
                    logger.error(f"Resolution check error: {e}")
            on_recovery(event.entity_name)

            # Send recovery email and endsAt to Alertmanager
            try:
                from services.alert_email_service import send_recovery_notification, resolve_alertmanager_alert
                event.recovery_notification_sent_at = now
                send_recovery_notification(event)
                resolve_alertmanager_alert(
                    event.alert_name, event.entity_name, event.severity,
                    labels=event.labels if isinstance(event.labels, dict) else None,
                )
            except Exception as _recov_err:
                logger.warning("Recovery notification failed (non-fatal): %s", _recov_err)

        if resolved_count:
            logger.info(f"Auto-resolved {resolved_count} alert(s) for recovered services")

    # ÔöÇÔöÇ 2. Resolve orphaned incidents for deleted services ÔöÇÔöÇ
    from models.incident import Incident
    existing_names = {svc.name.lower() for svc in db.query(ExternalService).all()}
    orphan_incidents = db.query(Incident).filter(
        Incident.status.in_(["open", "investigating"]),
        Incident.entity_type.in_(["service", "external-services"]),
    ).all()

    orphan_resolved = 0
    for inc in orphan_incidents:
        if inc.entity_name.lower() not in existing_names:
            inc.status = "resolved"
            inc.resolved_at = now
            inc.updated_at = now
            orphan_resolved += 1
            logger.info(f"Auto-resolved orphan incident {inc.id} for deleted service '{inc.entity_name}'")

    if orphan_resolved:
        logger.info(f"Resolved {orphan_resolved} orphan incident(s) for deleted services")

    # ── 3. Resolve orphaned firing alerts for deleted services ──
    # Alerts whose entity_name references a service that no longer exists
    # must be resolved to prevent permanently-firing phantom alerts.
    existing_names_exact = {svc.name for svc in db.query(ExternalService).all()}
    orphan_alerts = db.query(AlertEvent).filter(
        AlertEvent.status == "firing",
        AlertEvent.source.in_(["alert_policy", "assertion_evaluator"]),
    ).all()

    orphan_alerts_resolved = 0
    for alert in orphan_alerts:
        if alert.entity_name not in existing_names_exact:
            alert.status = "resolved"
            alert.ended_at = now
            alert.resolved_at = now
            alert.annotations = {
                **(alert.annotations if isinstance(alert.annotations, dict) else {}),
                "resolve_reason": "orphan_service_deleted",
            }
            orphan_alerts_resolved += 1
            logger.info(
                "Auto-resolved orphan alert %s for deleted service '%s'",
                alert.alert_name, alert.entity_name,
            )

    if orphan_alerts_resolved:
        logger.info(f"Resolved {orphan_alerts_resolved} orphan alert(s) for deleted services")

# ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
# Default rules seeding
# ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ

DEFAULT_POLICIES = [
    {
        "name": "Service Down",
        "rule_type": "SERVICE_DOWN",
        "description": "Alerts when a monitored service becomes unreachable after consecutive failed checks.",
        "consecutive_failures": 3,
        "critical_escalation_failures": 6,
        "incident_after_seconds": 120,
        "sustained_checks": 3,
        "severity": "warning",
        "cooldown_seconds": 120,
    },
    {
        "name": "High Latency",
        "rule_type": "HIGH_LATENCY",
        "description": "Alerts when response time exceeds the configured threshold for sustained checks.",
        "latency_threshold_ms": 1000.0,
        "sustained_checks": 3,
        "severity": "warning",
        "cooldown_seconds": 120,
        "consecutive_failures": 3,
        "critical_escalation_failures": 6,
        "incident_after_seconds": 300,
    },
    {
        "name": "Degraded Health",
        "rule_type": "DEGRADED_HEALTH",
        "description": "Alerts when AI anomaly detection score exceeds the threshold for sustained checks.",
        "anomaly_score_threshold": 70.0,
        "sustained_checks": 3,
        "severity": "warning",
        "cooldown_seconds": 120,
        "consecutive_failures": 3,
        "critical_escalation_failures": 6,
        "incident_after_seconds": 300,
    },
]


def seed_default_policies(db: Session) -> int:
    """Create default alert policies if none exist. Returns count created."""
    existing = db.query(AlertRule).filter(AlertRule.is_default == True).count()
    if existing > 0:
        return 0

    created = 0
    for policy in DEFAULT_POLICIES:
        rule = AlertRule(
            id=uuid.uuid4(),
            is_default=True,
            enabled=True,
            service_id=None,  # Global ÔÇö applies to all services
            **policy,
        )
        db.add(rule)
        created += 1

    db.commit()
    logger.info(f"Seeded {created} default alert policies")
    return created


@router.post("/seed-defaults", status_code=200)
async def seed_defaults_endpoint(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
):
    """Seed default alert policies if none exist."""
    count = seed_default_policies(db)
    if count == 0:
        return {"message": "Default policies already exist", "created": 0}
    return {"message": f"Created {count} default alert policies", "created": count}


# ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
# Rule Evaluation (called by health checker cycle)
# ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ

def evaluate_alert_rules(db: Session):
    """
    Evaluate all enabled alert rules against recent metrics.
    Called from the monitoring cycle, feeds into existing alert + incident pipeline.

    Architecture (Phase 1 repair):
      - Layer 1: User-configurable Alert Policies (SERVICE_DOWN, HIGH_LATENCY, DEGRADED_HEALTH)
        Only evaluated when user-created AlertRule rows exist.
      - Layer 2: Built-in internal alert logic (assertion-failure evaluation,
        recovery processing, orphan cleanup)
        ALWAYS runs regardless of whether any user policies are configured.
    """
    fired = 0

    # ── Layer 1: User-configurable policy evaluation ────────────────────
    rules = db.query(AlertRule).filter(AlertRule.enabled == True).all()
    if rules:
        for rule in rules:
            try:
                rule_type = rule.rule_type or "SERVICE_DOWN"

                if rule_type == "SERVICE_DOWN":
                    fired += _evaluate_service_down(db, rule)
                elif rule_type == "HIGH_LATENCY":
                    fired += _evaluate_high_latency(db, rule)
                elif rule_type == "DEGRADED_HEALTH":
                    fired += _evaluate_degraded_health(db, rule)
                else:
                    # Legacy metric/operator rules
                    value = _compute_metric(db, rule.service_id, rule.metric,
                                            rule.window_minutes or 5)
                    if value is not None and _check_threshold(value, rule.operator, rule.threshold):
                        _fire_rule_alert(db, rule, value)
                        fired += 1
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {e}")
    else:
        logger.debug("No user-configured alert policies found \u2014 skipping policy evaluation")

    # ── Layer 2: Built-in internal alert logic (always runs) ────────────

    # Phase 2a: Assertion-failure evaluation (internal defaults, no AlertRule needed)
    try:
        af_fired = _evaluate_assertion_failures(db)
        if af_fired:
            fired += af_fired
    except Exception as _af_err:
        logger.error("[Assertions] Assertion-failure evaluation error: %s", _af_err)

    # Phase 2b: Recovery processing + orphan cleanup (always runs)
    try:
        _resolve_recovered_services(db)
    except Exception as _res_err:
        logger.error(f"Error resolving recovered services: {_res_err}")

    db.commit()

    if fired:
        logger.info(f"Alert evaluation: {fired} alert(s) triggered (policies={len(rules)})")


def _get_target_services(db: Session, rule: AlertRule) -> list:
    """Get services this rule applies to."""
    if rule.service_id is not None:
        svc = db.query(ExternalService).filter(
            ExternalService.id == rule.service_id,
            ExternalService.enabled == True,
        ).first()
        return [svc] if svc else []
    else:
        return db.query(ExternalService).filter(
            ExternalService.enabled == True
        ).all()


def _evaluate_service_down(db: Session, rule: AlertRule) -> int:
    """Evaluate SERVICE_DOWN rule."""
    services = _get_target_services(db, rule)
    fired = 0
    threshold = rule.consecutive_failures or 3

    for svc in services:
        # Count consecutive recent failures
        rows = db.execute(text("""
            SELECT status FROM external_service_checks
            WHERE service_id = :sid
            ORDER BY checked_at DESC
            LIMIT :limit
        """), {"sid": svc.id, "limit": threshold}).fetchall()

        if len(rows) < threshold:
            continue

        # Phase 1.5: Only truly down/error statuses count as DOWN
            # DEGRADED is NOT treated as DOWN (Rule 5)
            consecutive_down = all(r.status in ('down', 'error') for r in rows)
        if consecutive_down:
            _fire_rule_alert(db, rule, threshold, service=svc,
                             detail=f"{threshold} consecutive failures")
            fired += 1

    return fired


def _evaluate_high_latency(db: Session, rule: AlertRule) -> int:
    """Evaluate HIGH_LATENCY rule."""
    services = _get_target_services(db, rule)
    fired = 0
    threshold_ms = rule.latency_threshold_ms or 1000.0
    sustained = rule.sustained_checks or 3

    for svc in services:
        rows = db.execute(text("""
            SELECT response_time_ms FROM external_service_checks
            WHERE service_id = :sid AND status = 'up'
            ORDER BY checked_at DESC
            LIMIT :limit
        """), {"sid": svc.id, "limit": sustained}).fetchall()

        if len(rows) < sustained:
            continue

        all_exceed = all(
            r.response_time_ms is not None and r.response_time_ms > threshold_ms
            for r in rows
        )
        if all_exceed:
            avg = sum(r.response_time_ms for r in rows) / len(rows)
            _fire_rule_alert(db, rule, avg, service=svc,
                             detail=f"Latency {avg:.0f}ms > {threshold_ms}ms for {sustained} checks")
            fired += 1

    return fired


def _evaluate_degraded_health(db: Session, rule: AlertRule) -> int:
    """Evaluate DEGRADED_HEALTH rule using health checker state.

    The external_service_checks table does NOT have a health_score column.
    Instead, we compute health from the health checker's in-memory state
    (uptime ratio, latency, stability) or fall back to recent check status.
    """
    services = _get_target_services(db, rule)
    fired = 0
    score_threshold = rule.anomaly_score_threshold or 70.0
    sustained = rule.sustained_checks or 3

    for svc in services:
        # Primary: use health checker's computed health score
        health_score = None
        try:
            from services.health_checker import _compute_health_score, _recent_checks
            if svc.id in _recent_checks and len(_recent_checks[svc.id]) >= sustained:
                svc_type_str = svc.service_type.value if hasattr(svc.service_type, 'value') else str(svc.service_type)
                health_score = _compute_health_score(
                    svc.id, svc.name, svc_type_str, svc.group_name or "default"
                )
        except Exception:
            pass

        # Fallback: compute from recent check statuses
        if health_score is None:
            rows = db.execute(text("""
                SELECT status FROM external_service_checks
                WHERE service_id = :sid
                ORDER BY checked_at DESC
                LIMIT :limit
            """), {"sid": svc.id, "limit": sustained}).fetchall()

            if len(rows) < sustained:
                continue

            up_count = sum(1 for r in rows if r.status == 'up')
            health_score = (up_count / len(rows)) * 100.0

        # anomaly_score = 100 - health_score (higher = more anomalous)
        anomaly_score = 100.0 - health_score
        if anomaly_score >= score_threshold:
            _fire_rule_alert(db, rule, anomaly_score, service=svc,
                             detail=f"Health score {health_score:.0f}% (anomaly {anomaly_score:.0f} >= {score_threshold})")
            fired += 1

    return fired


# ÔöÇÔöÇ Legacy metric evaluation (backward compat) ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ

# ── Assertion failure detection (Phase 3 — internal defaults, no AlertRule) ──────

# Internal defaults — NOT exposed to users in phase 1
_AF_CONSECUTIVE_FAILURES = 3   # reachable checks with assertion failures before firing
_AF_SUSTAINED_PASSES     = 3   # reachable checks with all-pass before resolving
_AF_SEVERITY             = "warning"
_AF_COOLDOWN_SECONDS     = 120


def _evaluate_assertion_failures(db: Session) -> int:
    """
    Inline assertion-failure alerting.  No AlertRule object — pure internal logic.

    For each enabled service that has assertions:
      1. Fetch last N reachable checks (status != 'down','error')
      2. If last _AF_CONSECUTIVE_FAILURES all have assertions_failed>0 → fire/update alert
      3. If last _AF_SUSTAINED_PASSES all have assertions_failed==0 → resolve alert
      4. If service is currently DOWN → resolve any active assertion-failure alert

    Returns count of new alerts fired (not updates).
    """
    from models.alert_event import AlertEvent
    from models.service_assertion import ServiceAssertion

    now = datetime.now(timezone.utc)
    fired = 0

    # Find services that have at least one enabled assertion
    svc_ids_with_assertions = (
        db.query(ServiceAssertion.service_id)
        .filter(ServiceAssertion.enabled == True)
        .distinct()
        .all()
    )
    svc_ids_set = {row[0] for row in svc_ids_with_assertions}
    if not svc_ids_set:
        return 0

    services = (
        db.query(ExternalService)
        .filter(
            ExternalService.enabled == True,
            ExternalService.id.in_(svc_ids_set),
        )
        .all()
    )

    window = max(_AF_CONSECUTIVE_FAILURES, _AF_SUSTAINED_PASSES)

    for svc in services:
        entity_name = svc.name
        fp_seed = f"assertion_failure:{entity_name}"
        fingerprint = hashlib.sha256(fp_seed.encode()).hexdigest()[:16]

        # ── Rule 5: if service is currently DOWN, resolve any active assertion alert ──
        if svc.status in ("down", "error"):
            existing = db.query(AlertEvent).filter(
                AlertEvent.fingerprint == fingerprint,
                AlertEvent.status == "firing",
            ).first()
            if existing:
                existing.status = "resolved"
                existing.ended_at = now
                existing.resolved_at = now
                existing.annotations = {
                    **(existing.annotations or {}),
                    "resolve_reason": "superseded_by_service_down",
                }
                logger.info(
                    "[Assertions] Resolved assertion-failure alert for %s "
                    "(superseded by SERVICE_DOWN)", entity_name
                )
            continue  # skip evaluation — service is unreachable

        # ── Fetch recent reachable checks ──
        rows = db.execute(text("""
            SELECT assertions_failed, assertions_total,
                   first_failed_assertion, first_failed_message
            FROM external_service_checks
            WHERE service_id = :sid
              AND status NOT IN ('down', 'error')
            ORDER BY checked_at DESC
            LIMIT :limit
        """), {"sid": svc.id, "limit": window}).fetchall()

        if len(rows) < _AF_CONSECUTIVE_FAILURES:
            continue  # not enough data

        # ── Check for consecutive assertion failures ──
        recent_fails = [r for r in rows[:_AF_CONSECUTIVE_FAILURES]]
        all_failing = all(
            (r.assertions_failed or 0) > 0
            for r in recent_fails
        )

        # ── Check for sustained passes (for resolution) ──
        recent_passes = [r for r in rows[:_AF_SUSTAINED_PASSES]]
        all_passing = (
            len(recent_passes) >= _AF_SUSTAINED_PASSES
            and all((r.assertions_failed or 0) == 0 for r in recent_passes)
        )

        # ── Look up existing firing alert ──
        existing = db.query(AlertEvent).filter(
            AlertEvent.fingerprint == fingerprint,
            AlertEvent.status == "firing",
        ).first()

        if all_failing:
            # Gather context from the most recent failing check
            latest = rows[0]
            fail_count = latest.assertions_failed or 0
            first_name = latest.first_failed_assertion or "unknown"
            first_msg = latest.first_failed_message or ""
            summary_text = (
                f"Assertion failure on {entity_name}: "
                f"{fail_count} assertion(s) failed — {first_name}: {first_msg}"
            )

            if existing:
                # ── UPDATE existing alert (no duplicate) ──
                existing.last_evaluated_at = now
                existing.annotations = {
                    "summary": summary_text,
                    "service_name": entity_name,
                    "assertions_failed": fail_count,
                    "first_failed_assertion": first_name,
                    "first_failed_message": first_msg[:500],
                }
                # Cooldown: don't log on every cycle
            else:
                # ── Cooldown check: don't re-fire too soon after resolution ──
                last_resolved = db.query(AlertEvent).filter(
                    AlertEvent.fingerprint == fingerprint,
                    AlertEvent.status == "resolved",
                ).order_by(AlertEvent.ended_at.desc()).first()

                if last_resolved and last_resolved.ended_at:
                    elapsed = (now - last_resolved.ended_at).total_seconds()
                    if elapsed < _AF_COOLDOWN_SECONDS:
                        continue  # still in cooldown

                # ── CREATE new assertion-failure alert ──
                alert_name = f"assertion_failure:{entity_name}"
                event = AlertEvent(
                    id=uuid.uuid4(),
                    alert_name=alert_name,
                    entity_type="external-services",
                    entity_name=entity_name,
                    metric_name="ASSERTION_FAILURE",
                    severity=_AF_SEVERITY,
                    status="firing",
                    started_at=now,
                    fingerprint=fingerprint,
                    labels={
                        "alertname": alert_name,
                        "service_name": entity_name,
                        "severity": _AF_SEVERITY,
                        "rule_type": "ASSERTION_FAILURE",
                        "source": "assertion_evaluator",
                    },
                    annotations={
                        "summary": summary_text,
                        "service_name": entity_name,
                        "assertions_failed": fail_count,
                        "first_failed_assertion": first_name,
                        "first_failed_message": first_msg[:500],
                    },
                    summary=summary_text,
                    source="assertion_evaluator",
                    generator_url="",
                    escalation_count=0,
                    last_evaluated_at=now,
                )
                db.add(event)
                fired += 1
                logger.info(
                    "[Assertions] Fired assertion-failure alert for %s: %s",
                    entity_name, summary_text[:200],
                )

        elif all_passing and existing:
            # ── RESOLVE: assertions passing consistently ──
            existing.status = "resolved"
            existing.ended_at = now
            existing.resolved_at = now
            existing.annotations = {
                **(existing.annotations or {}),
                "resolve_reason": "assertions_passing",
            }
            logger.info(
                "[Assertions] Resolved assertion-failure alert for %s "
                "(all assertions passing)", entity_name
            )

    return fired


def _compute_metric(db: Session, service_id: int, metric: str, window_minutes: int) -> float:
    """Compute a metric value from recent checks (legacy path)."""
    if not service_id or not metric:
        return None
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

    row = db.execute(text("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status = 'up') AS up_count,
            AVG(response_time_ms) AS avg_latency,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) AS p95_latency
        FROM external_service_checks
        WHERE service_id = :sid AND checked_at >= :cutoff
    """), {"sid": service_id, "cutoff": cutoff}).fetchone()

    if not row or row.total == 0:
        return None

    total = row.total
    up = row.up_count or 0

    if metric == "latency_ms":
        return round(row.avg_latency, 2) if row.avg_latency else None
    elif metric == "response_time_p95":
        return round(row.p95_latency, 2) if row.p95_latency else None
    elif metric == "availability_pct":
        return round((up / total) * 100, 2)
    elif metric == "error_rate":
        return round(((total - up) / total) * 100, 2)
    return None


def _check_threshold(value: float, operator: str, threshold: float) -> bool:
    """Evaluate: value <operator> threshold (legacy)."""
    if operator == ">":  return value > threshold
    elif operator == "<":  return value < threshold
    elif operator == ">=": return value >= threshold
    elif operator == "<=": return value <= threshold
    return False


def _fire_rule_alert(db: Session, rule: AlertRule, current_value: float,
                     service=None, detail: str = ""):
    """
    Canonical alert lifecycle handler (v2).

    ONE active alert per (entity_name + rule_type) fingerprint.
    - If a firing event ALREADY EXISTS: update severity in-place
      (escalation), refresh last_evaluated_at, and optionally link
      to an incident on critical escalation.
    - If NO firing event exists: run noise-filter checks (recovery
      buffer + transient filter) and create a new AlertEvent.

    This eliminates duplicate alerts: severity changes are UPDATEs,
    not new rows.
    """
    from models.alert_event import AlertEvent
    from routers.incidents import find_or_create_incident
    import hashlib

    entity_name = service.name if service else _get_service_name(db, rule.service_id)
    alert_name = f"policy:{rule.rule_type or rule.name}:{entity_name}"
    entity_type = "service"

    fp_seed = f"{alert_name}|{entity_name}|{rule.rule_type or rule.metric or ''}"
    fingerprint = hashlib.sha256(fp_seed.encode()).hexdigest()[:16]

    now = datetime.now(timezone.utc)

    # -- Severity escalation (always computed, whether updating or creating) --
    from services.alert_noise_filter import (
        should_create_alert, escalate_severity, should_create_incident,
    )
    effective_severity = escalate_severity(entity_name, rule.severity)

    # Phase 1.5 Rule 2: SERVICE_DOWN alerts are ALWAYS critical severity
    if rule.rule_type == 'SERVICE_DOWN':
        effective_severity = 'critical'

    # -- Check for existing firing event with this fingerprint --
    existing = db.query(AlertEvent).filter(
        AlertEvent.fingerprint == fingerprint,
        AlertEvent.status == "firing",
    ).first()

    if existing:
        # ÔöÇÔöÇ UPDATE PATH: severity escalation + touch timestamp ÔöÇÔöÇ
        old_severity = existing.severity
        existing.last_evaluated_at = now

        if effective_severity != old_severity:
            _SEV_ORDER = {"info": 0, "warning": 1, "critical": 2}
            if _SEV_ORDER.get(effective_severity, 0) > _SEV_ORDER.get(old_severity, 0):
                existing.severity = effective_severity
                existing.escalation_count = (existing.escalation_count or 0) + 1
                # Update labels dict with new severity
                if existing.labels and isinstance(existing.labels, dict):
                    updated_labels = dict(existing.labels)
                    updated_labels["severity"] = effective_severity
                    existing.labels = updated_labels
                logger.info(
                    "Alert severity escalated: %s (%s -> %s) for %s",
                    rule.name, old_severity, effective_severity, entity_name,
                )

                # On escalation to critical: link to incident if not already linked
                if effective_severity == "critical" and not existing.incident_id:
                    _should_inc, _inc_reason = should_create_incident(
                        entity_name, effective_severity
                    )
                    if _should_inc:
                        try:
                            inc = find_or_create_incident(
                                db, entity_type, entity_name,
                                effective_severity, existing.started_at,
                            )
                            existing.incident_id = inc.id
                        except Exception as e:
                            logger.warning("Incident linkage on escalation failed: %s", e)

        db.flush()
        return  # no new row

    # -- CREATION PATH: no existing firing event --

    # Noise filter: recovery buffer + transient failure checks
    # Phase 1.5 Rule 4: SERVICE_DOWN bypasses noise filter (immediate alert)
    if rule.rule_type == 'SERVICE_DOWN':
        _should_alert, _nf_reason = True, "SERVICE_DOWN bypass"
    else:
        _should_alert, _nf_reason = should_create_alert(entity_name, fingerprint, db)
    if not _should_alert:
        logger.info("[NoiseFilter] Policy alert suppressed: %s for %s -- %s",
                     rule.name, entity_name, _nf_reason)
        return

    summary = detail or f"{rule.name}: value={current_value}"
    event = AlertEvent(
        id=uuid.uuid4(),
        alert_name=alert_name,
        entity_type=entity_type,
        entity_name=entity_name,
        metric_name=rule.rule_type or rule.metric or "",
        severity=effective_severity,
        status="firing",
        started_at=now,
        fingerprint=fingerprint,
        labels={
            "alertname": alert_name,
            "service_name": entity_name,
            "severity": effective_severity,
            "rule_type": rule.rule_type or "",
            "source": "alert_policy",
            "rule_id": str(rule.id),
        },
        annotations={"summary": summary},
        summary=summary,
        source="alert_policy",
        generator_url="",
        escalation_count=0,
        last_evaluated_at=now,
    )
    db.add(event)
    db.flush()

    # Link to incident pipeline (noise-gated)
    _should_inc, _inc_reason = should_create_incident(entity_name, effective_severity)
    if _should_inc:
        try:
            inc = find_or_create_incident(db, entity_type, entity_name, effective_severity, now)
            event.incident_id = inc.id
        except Exception as e:
            logger.warning(f"Incident linkage for policy alert failed: {e}")
    else:
        logger.info("[NoiseFilter] Incident gated for policy %s: %s", rule.name, _inc_reason)

    logger.info(f"Policy alert fired: {rule.name} ({rule.rule_type}) -> {entity_name}")

    # ── Forward new policy alert to Alertmanager for Slack/email notifications ──
    try:
        import httpx
        from config import settings as _cfg
        am_payload = [{
            "labels": {
                "alertname": alert_name,
                "service_name": entity_name,
                "severity": effective_severity,
                "rule_type": rule.rule_type or "",
                "source": "alert_policy",
                "category": "external-services",
                "metric": rule.rule_type or rule.metric or "",
            },
            "annotations": {
                "summary": summary,
                "description": detail or summary,
            },
            "startsAt": now.isoformat(),
            "generatorURL": "",
        }]
        with httpx.Client(timeout=5.0) as _fwd:
            _fwd.post(f"{_cfg.ALERTMANAGER_URL}/api/v2/alerts", json=am_payload)
        logger.info("Forwarded policy alert to Alertmanager for notification: %s", alert_name)
    except Exception as _fwd_err:
        logger.warning("Alertmanager forward failed (non-fatal): %s", _fwd_err)

    # ── Send direct email notification via Zoho API (bypasses Alertmanager SMTP) ──
    try:
        from services.alert_email_service import send_firing_notification
        event.notification_sent_at = now
        db.flush()
        send_firing_notification(event, current_value=current_value)
        logger.info("Direct email notification triggered for: %s", alert_name)
    except Exception as _email_err:
        logger.warning("Direct email notification failed (non-fatal): %s", _email_err)
def _get_service_name(db: Session, service_id: int) -> str:
    if not service_id:
        return "all-services"
    svc = db.query(ExternalService).filter(ExternalService.id == service_id).first()
    return svc.name if svc else f"service-{service_id}"


