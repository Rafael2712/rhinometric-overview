"""
SLO / SLA Tracking router — v2

Computes service-level SLO metrics from real monitoring data:
  - external_service_checks  → availability (up/total), latency (p95)
  - anomaly_engine_results_v1 → health score (100 - avg anomaly_score)
  - alert_events             → alert count per service
  - incidents                → incident count per service

Three SLI types, each with configurable target:
  availability  ≥ 99.0%  (default)
  latency       ≤ 1000ms (default, p95)
  health_score  ≥ 70     (default, 0-100)

Existing endpoints preserved, new /summary endpoint added.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func, text, and_
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
from uuid import UUID

from database import get_db
from routers.auth import get_current_user, require_role
from models.user import User as UserModel
from models.external_service import ExternalService
from models.external_service_check import ExternalServiceCheck
from models.alert_event import AlertEvent
from models.incident import Incident
from models.slo_target import SLOTarget
from logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# ── Platform defaults ────────────────────────────────────────────

DEFAULTS = {
    "availability": 99.0,   # percentage
    "latency": 1000.0,      # ms (p95 upper bound)
    "health_score": 70.0,   # 0-100 (lower bound)
}

TIME_RANGES = {
    "24h": timedelta(hours=24),
    "7d":  timedelta(days=7),
    "30d": timedelta(days=30),
}


# ── Pydantic schemas ────────────────────────────────────────────

class SLOTargetUpdate(BaseModel):
    availability: Optional[float] = Field(None, ge=0, le=100)
    latency: Optional[float] = Field(None, ge=1, le=60000)
    health_score: Optional[float] = Field(None, ge=0, le=100)


# ── Helpers ──────────────────────────────────────────────────────

def _time_cutoff(time_range: str) -> datetime:
    delta = TIME_RANGES.get(time_range, timedelta(hours=24))
    return datetime.now(timezone.utc) - delta


def _percentile(sorted_values: list, pct: float) -> float:
    if not sorted_values:
        return 0.0
    n = len(sorted_values)
    idx = (pct / 100.0) * (n - 1)
    lower = int(idx)
    upper = lower + 1
    if upper >= n:
        return sorted_values[-1]
    frac = idx - lower
    return sorted_values[lower] + frac * (sorted_values[upper] - sorted_values[lower])


def _get_targets(db: Session, service_id: int) -> Dict[str, float]:
    """Return the effective SLO targets for a service (custom or defaults)."""
    targets = dict(DEFAULTS)  # copy defaults
    rows = db.query(SLOTarget).filter(SLOTarget.service_id == service_id).all()
    for row in rows:
        if row.slo_type in targets:
            targets[row.slo_type] = row.target_value
    return targets


def _availability_status(avail_pct: float, target: float) -> str:
    """healthy / at_risk / breached for availability SLI."""
    budget_total = 100.0 - target
    at_risk_threshold = target - 0.1 * budget_total
    if avail_pct >= target:
        return "healthy"
    elif avail_pct >= at_risk_threshold:
        return "at_risk"
    return "breached"


def _latency_status(p95_ms: float, target_ms: float) -> str:
    """healthy / at_risk / breached for latency SLI."""
    if p95_ms <= target_ms:
        return "healthy"
    elif p95_ms <= target_ms * 1.2:  # within 20% overshoot
        return "at_risk"
    return "breached"


def _health_status(score: float, target: float) -> str:
    """healthy / at_risk / breached for health_score SLI."""
    margin = (100.0 - target) * 0.1  # 10% of available budget
    if score >= target:
        return "healthy"
    elif score >= target - margin:
        return "at_risk"
    return "breached"


def _error_budget_remaining_availability(avail_pct: float, target: float) -> float:
    budget_total = 100.0 - target
    if budget_total <= 0:
        return 0.0
    consumed = max(0.0, target - avail_pct)
    return round(max(0.0, (budget_total - consumed) / budget_total * 100.0), 2)


def _error_budget_remaining_latency(p95_ms: float, target_ms: float) -> float:
    """100% if under target, decreases linearly as p95 exceeds target."""
    if p95_ms <= target_ms:
        return 100.0
    overshoot = p95_ms - target_ms
    budget_range = target_ms  # budget exhausted when p95 = 2x target
    return round(max(0.0, (budget_range - overshoot) / budget_range * 100.0), 2)


def _error_budget_remaining_health(score: float, target: float) -> float:
    budget_total = 100.0 - target  # room below 100
    if score >= target:
        return 100.0
    consumed = target - score
    if budget_total <= 0:
        return 0.0
    return round(max(0.0, (budget_total - consumed) / budget_total * 100.0), 2)


def _compute_slo_for_service(db: Session, svc: ExternalService, cutoff: datetime) -> dict:
    """Compute all SLO metrics for one external service."""

    targets = _get_targets(db, svc.id)

    # 1. Availability + latency from synthetic checks
    checks = db.query(ExternalServiceCheck).filter(
        ExternalServiceCheck.service_id == svc.id,
        ExternalServiceCheck.checked_at >= cutoff,
    ).all()

    total_checks = len(checks)

    if total_checks == 0:
        return {
            "service_id": svc.id,
            "service_name": svc.name,
            "service_type": svc.service_type.value if svc.service_type else "unknown",
            "availability_pct": None,
            "avg_latency_ms": None,
            "p95_latency_ms": None,
            "health_score": None,
            "incident_count": 0,
            "alert_count": 0,
            "targets": targets,
            "slo_target_pct": targets["availability"],
            "error_budget_remaining_pct": None,
            "error_budget_availability": None,
            "error_budget_latency": None,
            "error_budget_health": None,
            "slo_status": "no_data",
            "slo_status_availability": "no_data",
            "slo_status_latency": "no_data",
            "slo_status_health": "no_data",
            "total_checks": 0,
            "successful_checks": 0,
            "data_source": "synthetic",
            "monitoring_mode": svc.monitoring_mode.value if svc.monitoring_mode else "synthetic_only",
            "telemetry_status": svc.telemetry_status.value if svc.telemetry_status else "not_configured",
        }

    successful = sum(1 for c in checks if c.status == "up")
    availability = round(successful / total_checks * 100, 4)

    latencies = sorted([
        c.response_time_ms for c in checks
        if c.response_time_ms and c.response_time_ms > 0
    ])
    avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    p95_lat = round(_percentile(latencies, 95), 2) if latencies else 0.0

    # 2. Health score from anomaly engine (if any data exists)
    health_score: Optional[float] = None
    try:
        result = db.execute(text("""
            SELECT round(100.0 - avg(anomaly_score)::numeric, 2) as health
            FROM anomaly_engine_results_v1
            WHERE service_id = :sid
              AND created_at >= :cutoff
              AND anomaly_score IS NOT NULL
        """), {"sid": svc.id, "cutoff": cutoff}).fetchone()
        if result and result[0] is not None:
            health_score = float(result[0])
    except Exception:
        pass  # table may not exist yet; degrade gracefully

    # 3. Alert count
    alert_count = db.query(sa_func.count(AlertEvent.id)).filter(
        AlertEvent.entity_name == svc.name,
        AlertEvent.started_at >= cutoff,
    ).scalar() or 0

    # 4. Incident count
    incident_count = db.query(sa_func.count(Incident.id)).filter(
        Incident.entity_name == svc.name,
        Incident.started_at >= cutoff,
    ).scalar() or 0

    # 5. Status per SLI
    avail_status = _availability_status(availability, targets["availability"])
    lat_status = _latency_status(p95_lat, targets["latency"]) if p95_lat > 0 else "no_data"
    health_status_val = _health_status(health_score, targets["health_score"]) if health_score is not None else "no_data"

    # 6. Error budgets
    eb_avail = _error_budget_remaining_availability(availability, targets["availability"])
    eb_lat = _error_budget_remaining_latency(p95_lat, targets["latency"]) if p95_lat > 0 else None
    eb_health = _error_budget_remaining_health(health_score, targets["health_score"]) if health_score is not None else None

    # 7. Overall status (worst of the three that have data)
    statuses = [avail_status]
    if lat_status != "no_data":
        statuses.append(lat_status)
    if health_status_val != "no_data":
        statuses.append(health_status_val)

    if "breached" in statuses:
        overall_status = "breached"
    elif "at_risk" in statuses:
        overall_status = "at_risk"
    else:
        overall_status = "healthy"

    # 8. Composite error budget (minimum of available budgets)
    budgets = [eb_avail]
    if eb_lat is not None:
        budgets.append(eb_lat)
    if eb_health is not None:
        budgets.append(eb_health)
    composite_budget = min(budgets) if budgets else None

    return {
        "service_id": svc.id,
        "service_name": svc.name,
        "service_type": svc.service_type.value if svc.service_type else "unknown",
        "availability_pct": availability,
        "avg_latency_ms": avg_lat,
        "p95_latency_ms": p95_lat,
        "health_score": health_score,
        "incident_count": incident_count,
        "alert_count": alert_count,
        "targets": targets,
        "slo_target_pct": targets["availability"],
        "error_budget_remaining_pct": composite_budget,
        "error_budget_availability": eb_avail,
        "error_budget_latency": eb_lat,
        "error_budget_health": eb_health,
        "slo_status": overall_status,
        "slo_status_availability": avail_status,
        "slo_status_latency": lat_status,
        "slo_status_health": health_status_val,
        "total_checks": total_checks,
        "successful_checks": successful,
        "data_source": "synthetic",
        "monitoring_mode": svc.monitoring_mode.value if svc.monitoring_mode else "synthetic_only",
        "telemetry_status": svc.telemetry_status.value if svc.telemetry_status else "not_configured",
    }


# ── Endpoints ────────────────────────────────────────────────────
# Existing endpoints (preserved — same contract, enriched response)

@router.get("/services")
async def list_slo_services(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    time_range: str = Query("24h", regex="^(24h|7d|30d)$"),
):
    """List all monitored services with SLO metrics."""
    cutoff = _time_cutoff(time_range)

    services = db.query(ExternalService).filter(
        ExternalService.enabled == True,
    ).order_by(ExternalService.name).all()

    results = []
    for svc in services:
        metrics = _compute_slo_for_service(db, svc, cutoff)
        results.append(metrics)

    total = len(results)
    with_data = [r for r in results if r["slo_status"] != "no_data"]
    healthy = sum(1 for r in with_data if r["slo_status"] == "healthy")
    at_risk = sum(1 for r in with_data if r["slo_status"] == "at_risk")
    breached = sum(1 for r in with_data if r["slo_status"] == "breached")

    return {
        "services": results,
        "summary": {
            "total": total,
            "healthy": healthy,
            "at_risk": at_risk,
            "breached": breached,
        },
        "time_range": time_range,
    }


@router.get("/summary")
async def slo_summary(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    time_range: str = Query("24h", regex="^(24h|7d|30d)$"),
):
    """
    Global SLO summary — aggregated across all enabled services.

    Returns platform-wide:
      - availability_pct (weighted average)
      - latency_p95_ms (worst p95 across services)
      - health_score_avg (average health score)
      - error budget remaining per SLI type
      - per-SLI status
      - overall status
    """
    cutoff = _time_cutoff(time_range)

    services = db.query(ExternalService).filter(
        ExternalService.enabled == True,
    ).order_by(ExternalService.name).all()

    if not services:
        return {
            "availability_pct": None,
            "latency_p95_ms": None,
            "health_score_avg": None,
            "error_budget_availability": None,
            "error_budget_latency": None,
            "error_budget_health": None,
            "status_availability": "no_data",
            "status_latency": "no_data",
            "status_health": "no_data",
            "overall_status": "no_data",
            "total_services": 0,
            "services_healthy": 0,
            "services_at_risk": 0,
            "services_breached": 0,
            "total_incidents": 0,
            "total_alerts": 0,
            "time_range": time_range,
            "defaults": DEFAULTS,
        }

    all_metrics = [_compute_slo_for_service(db, svc, cutoff) for svc in services]

    # Weighted availability (by check count)
    total_up = sum(m["successful_checks"] for m in all_metrics)
    total_ch = sum(m["total_checks"] for m in all_metrics)
    platform_avail = round(total_up / total_ch * 100, 4) if total_ch > 0 else None

    # Worst p95 latency
    p95s = [m["p95_latency_ms"] for m in all_metrics if m["p95_latency_ms"] and m["p95_latency_ms"] > 0]
    platform_p95 = round(max(p95s), 2) if p95s else None

    # Average health score
    healths = [m["health_score"] for m in all_metrics if m["health_score"] is not None]
    platform_health = round(sum(healths) / len(healths), 2) if healths else None

    # Use platform defaults for summary-level status
    avail_target = DEFAULTS["availability"]
    lat_target = DEFAULTS["latency"]
    health_target = DEFAULTS["health_score"]

    s_avail = _availability_status(platform_avail, avail_target) if platform_avail is not None else "no_data"
    s_lat = _latency_status(platform_p95, lat_target) if platform_p95 is not None else "no_data"
    s_health = _health_status(platform_health, health_target) if platform_health is not None else "no_data"

    eb_avail = _error_budget_remaining_availability(platform_avail, avail_target) if platform_avail is not None else None
    eb_lat = _error_budget_remaining_latency(platform_p95, lat_target) if platform_p95 is not None else None
    eb_health = _error_budget_remaining_health(platform_health, health_target) if platform_health is not None else None

    statuses = [s for s in [s_avail, s_lat, s_health] if s != "no_data"]
    if "breached" in statuses:
        overall = "breached"
    elif "at_risk" in statuses:
        overall = "at_risk"
    elif statuses:
        overall = "healthy"
    else:
        overall = "no_data"

    with_data = [m for m in all_metrics if m["slo_status"] != "no_data"]

    return {
        "availability_pct": platform_avail,
        "latency_p95_ms": platform_p95,
        "health_score_avg": platform_health,
        "error_budget_availability": eb_avail,
        "error_budget_latency": eb_lat,
        "error_budget_health": eb_health,
        "status_availability": s_avail,
        "status_latency": s_lat,
        "status_health": s_health,
        "overall_status": overall,
        "total_services": len(all_metrics),
        "services_healthy": sum(1 for m in with_data if m["slo_status"] == "healthy"),
        "services_at_risk": sum(1 for m in with_data if m["slo_status"] == "at_risk"),
        "services_breached": sum(1 for m in with_data if m["slo_status"] == "breached"),
        "total_incidents": sum(m["incident_count"] for m in all_metrics),
        "total_alerts": sum(m["alert_count"] for m in all_metrics),
        "time_range": time_range,
        "defaults": DEFAULTS,
    }


@router.get("/services/{service_id}")
async def get_slo_service_detail(
    service_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    time_range: str = Query("24h", regex="^(24h|7d|30d)$"),
):
    """Get detailed SLO metrics for a single service."""
    svc = db.query(ExternalService).filter(ExternalService.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    cutoff = _time_cutoff(time_range)
    metrics = _compute_slo_for_service(db, svc, cutoff)

    # Availability trend — hourly buckets
    checks = db.query(ExternalServiceCheck).filter(
        ExternalServiceCheck.service_id == svc.id,
        ExternalServiceCheck.checked_at >= cutoff,
    ).order_by(ExternalServiceCheck.checked_at).all()

    buckets: Dict[str, dict] = {}
    for c in checks:
        hour_key = c.checked_at.strftime("%Y-%m-%d %H:00")
        if hour_key not in buckets:
            buckets[hour_key] = {"total": 0, "up": 0, "latencies": []}
        buckets[hour_key]["total"] += 1
        if c.status == "up":
            buckets[hour_key]["up"] += 1
        if c.response_time_ms and c.response_time_ms > 0:
            buckets[hour_key]["latencies"].append(c.response_time_ms)

    availability_trend = []
    for hour, data in sorted(buckets.items()):
        avail = round(data["up"] / data["total"] * 100, 2) if data["total"] > 0 else 0
        avg_lat = round(sum(data["latencies"]) / len(data["latencies"]), 2) if data["latencies"] else 0
        availability_trend.append({
            "time": hour,
            "availability_pct": avail,
            "avg_latency_ms": avg_lat,
            "check_count": data["total"],
        })

    # Recent alerts
    recent_alerts = db.query(AlertEvent).filter(
        AlertEvent.entity_name == svc.name,
        AlertEvent.started_at >= cutoff,
    ).order_by(AlertEvent.started_at.desc()).limit(10).all()

    alerts_list = [{
        "id": str(a.id),
        "alert_name": a.alert_name,
        "severity": a.severity,
        "status": a.status,
        "started_at": a.started_at.isoformat() if a.started_at else None,
        "ended_at": a.ended_at.isoformat() if a.ended_at else None,
    } for a in recent_alerts]

    # Recent incidents
    recent_incidents = db.query(Incident).filter(
        Incident.entity_name == svc.name,
        Incident.started_at >= cutoff,
    ).order_by(Incident.started_at.desc()).limit(10).all()

    incidents_list = [{
        "id": str(inc.id),
        "status": inc.status,
        "severity": inc.severity,
        "started_at": inc.started_at.isoformat() if inc.started_at else None,
        "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
    } for inc in recent_incidents]

    return {
        "service": metrics,
        "availability_trend": availability_trend,
        "recent_alerts": alerts_list,
        "recent_incidents": incidents_list,
        "time_range": time_range,
    }


# ── SLO Targets CRUD (new) ──────────────────────────────────────

@router.get("/services/{service_id}/targets")
async def get_service_targets(
    service_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the effective SLO targets for a service."""
    svc = db.query(ExternalService).filter(ExternalService.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    targets = _get_targets(db, service_id)
    return {"service_id": service_id, "targets": targets, "defaults": DEFAULTS}


@router.put("/services/{service_id}/targets")
async def update_service_targets(
    service_id: int,
    body: SLOTargetUpdate,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
):
    """Update SLO targets for a service. Omitted fields keep current value."""
    svc = db.query(ExternalService).filter(ExternalService.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    updates = {}
    if body.availability is not None:
        updates["availability"] = body.availability
    if body.latency is not None:
        updates["latency"] = body.latency
    if body.health_score is not None:
        updates["health_score"] = body.health_score

    for slo_type, value in updates.items():
        existing = db.query(SLOTarget).filter(
            SLOTarget.service_id == service_id,
            SLOTarget.slo_type == slo_type,
        ).first()
        if existing:
            existing.target_value = value
        else:
            db.add(SLOTarget(service_id=service_id, slo_type=slo_type, target_value=value))

    db.commit()
    targets = _get_targets(db, service_id)
    return {"service_id": service_id, "targets": targets, "defaults": DEFAULTS}


@router.delete("/services/{service_id}/targets")
async def reset_service_targets(
    service_id: int,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
):
    """Reset a service's SLO targets to platform defaults."""
    db.query(SLOTarget).filter(SLOTarget.service_id == service_id).delete()
    db.commit()
    return {"service_id": service_id, "targets": dict(DEFAULTS), "defaults": DEFAULTS, "reset": True}
