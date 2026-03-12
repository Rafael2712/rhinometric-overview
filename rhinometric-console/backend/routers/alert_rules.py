"""
Alert Rules CRUD and evaluation — Phase 2.6
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid

from database import get_db
from routers.auth import get_current_user
from models.user import User as UserModel
from models.alert_rule import AlertRule
from models.external_service import ExternalService
from logging_config import get_logger

logger = get_logger("alert_rules")

router = APIRouter()

# ────────────────────────────────────────────────────────────────
# Schemas
# ────────────────────────────────────────────────────────────────
VALID_METRICS = {"latency_ms", "error_rate", "availability_pct", "response_time_p95"}
VALID_OPERATORS = {">", "<", ">=", "<="}
VALID_SEVERITIES = {"info", "warning", "critical"}


class AlertRuleCreate(BaseModel):
    name: str
    service_id: int
    metric: str
    operator: str
    threshold: float
    window_minutes: int = 5
    severity: str = "warning"
    enabled: bool = True

    @field_validator("metric")
    @classmethod
    def validate_metric(cls, v):
        if v not in VALID_METRICS:
            raise ValueError(f"metric must be one of {VALID_METRICS}")
        return v

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v):
        if v not in VALID_OPERATORS:
            raise ValueError(f"operator must be one of {VALID_OPERATORS}")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v):
        if v not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {VALID_SEVERITIES}")
        return v

    @field_validator("window_minutes")
    @classmethod
    def validate_window(cls, v):
        if v < 1 or v > 1440:
            raise ValueError("window_minutes must be between 1 and 1440")
        return v


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    service_id: Optional[int] = None
    metric: Optional[str] = None
    operator: Optional[str] = None
    threshold: Optional[float] = None
    window_minutes: Optional[int] = None
    severity: Optional[str] = None
    enabled: Optional[bool] = None

    @field_validator("metric")
    @classmethod
    def validate_metric(cls, v):
        if v is not None and v not in VALID_METRICS:
            raise ValueError(f"metric must be one of {VALID_METRICS}")
        return v

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v):
        if v is not None and v not in VALID_OPERATORS:
            raise ValueError(f"operator must be one of {VALID_OPERATORS}")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v):
        if v is not None and v not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {VALID_SEVERITIES}")
        return v


def _rule_to_dict(rule: AlertRule, service_name: str = "") -> dict:
    return {
        "id": str(rule.id),
        "name": rule.name,
        "service_id": rule.service_id,
        "service_name": service_name,
        "metric": rule.metric,
        "operator": rule.operator,
        "threshold": rule.threshold,
        "window_minutes": rule.window_minutes,
        "severity": rule.severity,
        "enabled": rule.enabled,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }


# ────────────────────────────────────────────────────────────────
# CRUD Endpoints
# ────────────────────────────────────────────────────────────────

@router.get("")
async def list_alert_rules(
    service_id: Optional[int] = Query(None),
    enabled: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """List all alert rules with optional filtering."""
    query = db.query(AlertRule)
    if service_id is not None:
        query = query.filter(AlertRule.service_id == service_id)
    if enabled is not None:
        query = query.filter(AlertRule.enabled == enabled)
    query = query.order_by(AlertRule.created_at.desc())
    rules = query.all()

    # Batch-fetch service names
    svc_ids = list({r.service_id for r in rules})
    svc_map = {}
    if svc_ids:
        svcs = db.query(ExternalService.id, ExternalService.name).filter(
            ExternalService.id.in_(svc_ids)
        ).all()
        svc_map = {s.id: s.name for s in svcs}

    return {
        "rules": [_rule_to_dict(r, svc_map.get(r.service_id, "Unknown")) for r in rules],
        "total": len(rules),
    }


@router.post("", status_code=201)
async def create_alert_rule(
    body: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new alert rule."""
    # Validate service exists
    svc = db.query(ExternalService).filter(ExternalService.id == body.service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail=f"Service {body.service_id} not found")

    rule = AlertRule(
        id=uuid.uuid4(),
        name=body.name,
        service_id=body.service_id,
        metric=body.metric,
        operator=body.operator,
        threshold=body.threshold,
        window_minutes=body.window_minutes,
        severity=body.severity,
        enabled=body.enabled,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    logger.info(f"Alert rule created: {rule.name} ({rule.metric} {rule.operator} {rule.threshold})")
    return _rule_to_dict(rule, svc.name)


@router.get("/{rule_id}")
async def get_alert_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get a single alert rule."""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    svc = db.query(ExternalService).filter(ExternalService.id == rule.service_id).first()
    return _rule_to_dict(rule, svc.name if svc else "Unknown")


@router.patch("/{rule_id}")
async def update_alert_rule(
    rule_id: str,
    body: AlertRuleUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Update an existing alert rule."""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    update_data = body.model_dump(exclude_unset=True)

    # Validate service if changing
    if "service_id" in update_data:
        svc = db.query(ExternalService).filter(ExternalService.id == update_data["service_id"]).first()
        if not svc:
            raise HTTPException(status_code=404, detail=f"Service {update_data['service_id']} not found")

    for field, value in update_data.items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)

    svc = db.query(ExternalService).filter(ExternalService.id == rule.service_id).first()
    logger.info(f"Alert rule updated: {rule.name}")
    return _rule_to_dict(rule, svc.name if svc else "Unknown")


@router.delete("/{rule_id}", status_code=204)
async def delete_alert_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Delete an alert rule."""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    logger.info(f"Alert rule deleted: {rule.name}")
    return None


# ────────────────────────────────────────────────────────────────
# Rule Evaluation (called by health checker cycle)
# ────────────────────────────────────────────────────────────────

def evaluate_alert_rules(db: Session):
    """
    Evaluate all enabled alert rules against recent metrics.
    Called from the monitoring cycle, feeds into existing alert + incident pipeline.
    """
    rules = db.query(AlertRule).filter(AlertRule.enabled == True).all()
    if not rules:
        return

    fired = 0
    for rule in rules:
        try:
            value = _compute_metric(db, rule.service_id, rule.metric, rule.window_minutes)
            if value is None:
                continue

            triggered = _check_threshold(value, rule.operator, rule.threshold)
            if triggered:
                _fire_rule_alert(db, rule, value)
                fired += 1
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.name}: {e}")

    if fired:
        db.commit()
        logger.info(f"Alert rules: {fired} of {len(rules)} triggered")


def _compute_metric(db: Session, service_id: int, metric: str, window_minutes: int) -> float:
    """Compute a metric value from recent checks."""
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
    """Evaluate: value <operator> threshold."""
    if operator == ">":
        return value > threshold
    elif operator == "<":
        return value < threshold
    elif operator == ">=":
        return value >= threshold
    elif operator == "<=":
        return value <= threshold
    return False


def _fire_rule_alert(db: Session, rule: AlertRule, current_value: float):
    """
    Fire alert through the existing pipeline:
    1. Create AlertEvent
    2. Link to incident via find_or_create_incident
    """
    from models.alert_event import AlertEvent
    from routers.incidents import find_or_create_incident
    import hashlib

    alert_name = f"rule:{rule.name}"
    entity_name = _get_service_name(db, rule.service_id)
    entity_type = "service"

    fp_seed = f"{alert_name}|{entity_name}|{rule.metric}"
    fingerprint = hashlib.sha256(fp_seed.encode()).hexdigest()[:16]

    # Check if there's already a firing event for this fingerprint (avoid duplicates)
    existing = db.query(AlertEvent).filter(
        AlertEvent.fingerprint == fingerprint,
        AlertEvent.status == "firing",
    ).first()
    if existing:
        return  # Already firing, skip

    now = datetime.now(timezone.utc)
    event = AlertEvent(
        id=uuid.uuid4(),
        alert_name=alert_name,
        entity_type=entity_type,
        entity_name=entity_name,
        metric_name=rule.metric,
        severity=rule.severity,
        status="firing",
        started_at=now,
        fingerprint=fingerprint,
        labels={"alertname": alert_name, "service_name": entity_name,
                "severity": rule.severity, "metric_name": rule.metric,
                "source": "alert_rule", "rule_id": str(rule.id)},
        annotations={"summary": f"{rule.name}: {rule.metric} {rule.operator} {rule.threshold} (current: {current_value})"},
        summary=f"{rule.name}: {rule.metric} = {current_value} ({rule.operator} {rule.threshold})",
        source="alert_rule",
        generator_url="",
    )
    db.add(event)
    db.flush()

    # Link to incident pipeline
    try:
        inc = find_or_create_incident(db, entity_type, entity_name, rule.severity, now)
        event.incident_id = inc.id
    except Exception as e:
        logger.warning(f"Incident linkage for rule alert failed: {e}")

    logger.info(f"Rule alert fired: {rule.name} → {rule.metric}={current_value}")


def _get_service_name(db: Session, service_id: int) -> str:
    svc = db.query(ExternalService).filter(ExternalService.id == service_id).first()
    return svc.name if svc else f"service-{service_id}"


# ────────────────────────────────────────────────────────────────
# Services list (for frontend dropdown)
# ────────────────────────────────────────────────────────────────

@router.get("/services/list")
async def list_services_for_rules(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Return simplified list of services for rule creation dropdown."""
    svcs = db.query(ExternalService.id, ExternalService.name).filter(
        ExternalService.enabled == True
    ).order_by(ExternalService.name).all()
    return {"services": [{"id": s.id, "name": s.name} for s in svcs]}
