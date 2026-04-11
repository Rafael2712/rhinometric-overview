"""
Synthetic Monitoring Alert Policies — CRUD and evaluation.

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

from database import get_db
from routers.auth import get_current_user, require_role
from models.user import User as UserModel
from models.alert_rule import AlertRule
from models.external_service import ExternalService
from logging_config import get_logger

logger = get_logger("alert_rules")

router = APIRouter()

# ────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────
VALID_RULE_TYPES = {"SERVICE_DOWN", "HIGH_LATENCY", "DEGRADED_HEALTH"}
VALID_SEVERITIES = {"info", "warning", "critical"}

# Legacy compat
VALID_METRICS = {"latency_ms", "error_rate", "availability_pct", "response_time_p95"}
VALID_OPERATORS = {">", "<", ">=", "<="}

# ────────────────────────────────────────────────────────────────
# Schemas
# ────────────────────────────────────────────────────────────────

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
            raise ValueError("consecutive_failures must be 1–100")
        return v

    @field_validator("cooldown_seconds")
    @classmethod
    def validate_cooldown(cls, v):
        if v < 0 or v > 86400:
            raise ValueError("cooldown_seconds must be 0–86400")
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


# ────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────

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


# ────────────────────────────────────────────────────────────────
# CRUD Endpoints
# ────────────────────────────────────────────────────────────────

@router.get("")
async def list_alert_rules(
    service_id: Optional[int] = Query(None),
    rule_type: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
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
    current_user: UserModel = Depends(get_current_user),
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
    current_user: UserModel = Depends(get_current_user),
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


# ────────────────────────────────────────────────────────────────
# Default rules seeding
# ────────────────────────────────────────────────────────────────

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
            service_id=None,  # Global — applies to all services
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

    if fired:
        db.commit()
        logger.info(f"Alert rules: {fired} of {len(rules)} triggered")


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

        consecutive_down = all(r.status != 'up' for r in rows)
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
    """Evaluate DEGRADED_HEALTH rule."""
    services = _get_target_services(db, rule)
    fired = 0
    score_threshold = rule.anomaly_score_threshold or 70.0
    sustained = rule.sustained_checks or 3

    for svc in services:
        rows = db.execute(text("""
            SELECT health_score FROM external_service_checks
            WHERE service_id = :sid AND health_score IS NOT NULL
            ORDER BY checked_at DESC
            LIMIT :limit
        """), {"sid": svc.id, "limit": sustained}).fetchall()

        if len(rows) < sustained:
            continue

        # health_score is 0-100 where lower = worse.
        # anomaly_score = 100 - health_score (higher = more anomalous)
        all_degraded = all(
            (100.0 - r.health_score) >= score_threshold
            for r in rows
        )
        if all_degraded:
            avg_anomaly = sum(100.0 - r.health_score for r in rows) / len(rows)
            _fire_rule_alert(db, rule, avg_anomaly, service=svc,
                             detail=f"Anomaly score {avg_anomaly:.0f} >= {score_threshold} for {sustained} checks")
            fired += 1

    return fired


# ── Legacy metric evaluation (backward compat) ──────────────────

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
    Fire alert through the existing pipeline:
    1. Create AlertEvent
    2. Link to incident via find_or_create_incident
    """
    from models.alert_event import AlertEvent
    from routers.incidents import find_or_create_incident
    import hashlib

    entity_name = service.name if service else _get_service_name(db, rule.service_id)
    alert_name = f"policy:{rule.rule_type or rule.name}:{entity_name}"
    entity_type = "service"

    fp_seed = f"{alert_name}|{entity_name}|{rule.rule_type or rule.metric or ''}"
    fingerprint = hashlib.sha256(fp_seed.encode()).hexdigest()[:16]

    # Check if there's already a firing event for this fingerprint
    existing = db.query(AlertEvent).filter(
        AlertEvent.fingerprint == fingerprint,
        AlertEvent.status == "firing",
    ).first()
    if existing:
        return

    # ── Noise filter: streak, cooldown, dedup ──
    from services.alert_noise_filter import (
        should_create_alert, escalate_severity, should_create_incident,
    )
    _should_alert, _nf_reason = should_create_alert(entity_name, fingerprint, db)
    if not _should_alert:
        logger.info("[NoiseFilter] Policy alert suppressed: %s for %s — %s",
                     rule.name, entity_name, _nf_reason)
        return

    # Severity escalation based on failure streak
    effective_severity = escalate_severity(entity_name, rule.severity)

    now = datetime.now(timezone.utc)
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

    logger.info(f"Policy alert fired: {rule.name} ({rule.rule_type}) → {entity_name}")


def _get_service_name(db: Session, service_id: int) -> str:
    if not service_id:
        return "all-services"
    svc = db.query(ExternalService).filter(ExternalService.id == service_id).first()
    return svc.name if svc else f"service-{service_id}"


