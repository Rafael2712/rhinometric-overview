"""
SLO / SLA Tracking router — Phase 2.4

Computes service-level SLO metrics from real monitoring data:
  - external_service_checks  → availability, latency
  - alert_events             → alert count per service
  - incidents                → incident count per service

Default SLO target: 99.0%
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func, text
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from database import get_db
from routers.auth import get_current_user
from models.user import User as UserModel
from models.external_service import ExternalService
from models.external_service_check import ExternalServiceCheck
from models.alert_event import AlertEvent
from models.incident import Incident
from logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Platform-wide default SLO target (percentage)
DEFAULT_SLO_TARGET = 99.0

TIME_RANGES = {
    "24h": timedelta(hours=24),
    "7d":  timedelta(days=7),
    "30d": timedelta(days=30),
}


def _time_cutoff(time_range: str) -> datetime:
    """Return the UTC cutoff datetime for the given range key."""
    delta = TIME_RANGES.get(time_range, timedelta(hours=24))
    return datetime.now(timezone.utc) - delta


def _percentile(sorted_values: list, pct: float) -> float:
    """Calculate the p-th percentile from a sorted list."""
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


def _slo_status(availability_pct: float, slo_target: float) -> str:
    """
    Determine SLO compliance status.
      healthy  → availability >= target
      at_risk  → availability < target but error budget used < 90 %
      breached → availability < (100 - (100 - target))  i.e. below target
    Simplified:
      healthy  → availability >= target
      at_risk  → availability >= target - 0.1*(100-target)  (within 10% of exhaustion)
      breached → availability < target - 0.1*(100-target)
    """
    error_budget_total = 100.0 - slo_target          # e.g. 1.0 for 99%
    at_risk_threshold = slo_target - 0.1 * error_budget_total  # e.g. 98.9

    if availability_pct >= slo_target:
        return "healthy"
    elif availability_pct >= at_risk_threshold:
        return "at_risk"
    else:
        return "breached"


def _error_budget_remaining(availability_pct: float, slo_target: float) -> float:
    """
    Error budget remaining as a percentage of the total budget.

    total_budget = 100 - slo_target   (e.g. 1.0% for a 99% SLO)
    consumed     = max(0, slo_target - availability)   (only positive)
    remaining %  = max(0, (total_budget - consumed) / total_budget * 100)

    Example: target=99%, avail=99.5% → consumed=0 → 100% remaining
    Example: target=99%, avail=98.5% → consumed=0.5 → 50% remaining
    Example: target=99%, avail=97.0% → consumed=2.0 → 0% remaining (clamped)
    """
    total_budget = 100.0 - slo_target
    if total_budget <= 0:
        return 0.0
    consumed = max(0.0, slo_target - availability_pct)
    remaining = max(0.0, (total_budget - consumed) / total_budget * 100.0)
    return round(remaining, 2)


def _compute_slo_for_service(db: Session, svc: ExternalService, cutoff: datetime) -> dict:
    """Compute all SLO metrics for one external service."""

    # 1. Availability + latency from checks
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
            "incident_count": 0,
            "alert_count": 0,
            "slo_target_pct": DEFAULT_SLO_TARGET,
            "error_budget_remaining_pct": None,
            "slo_status": "no_data",
            "total_checks": 0,
            "successful_checks": 0,
        }

    successful = sum(1 for c in checks if c.status == "up")
    availability = round(successful / total_checks * 100, 4)

    latencies = sorted([c.response_time_ms for c in checks if c.response_time_ms and c.response_time_ms > 0])
    avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    p95_lat = round(_percentile(latencies, 95), 2) if latencies else 0.0

    # 2. Alert count — match by service name in entity_name
    alert_count = db.query(sa_func.count(AlertEvent.id)).filter(
        AlertEvent.entity_name == svc.name,
        AlertEvent.started_at >= cutoff,
    ).scalar() or 0

    # 3. Incident count
    incident_count = db.query(sa_func.count(Incident.id)).filter(
        Incident.entity_name == svc.name,
        Incident.started_at >= cutoff,
    ).scalar() or 0

    slo_target = DEFAULT_SLO_TARGET
    budget = _error_budget_remaining(availability, slo_target)
    status = _slo_status(availability, slo_target)

    return {
        "service_id": svc.id,
        "service_name": svc.name,
        "service_type": svc.service_type.value if svc.service_type else "unknown",
        "availability_pct": availability,
        "avg_latency_ms": avg_lat,
        "p95_latency_ms": p95_lat,
        "incident_count": incident_count,
        "alert_count": alert_count,
        "slo_target_pct": slo_target,
        "error_budget_remaining_pct": budget,
        "slo_status": status,
        "total_checks": total_checks,
        "successful_checks": successful,
    }


# ── Endpoints ──────────────────────────────────────────────────

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

    # Summary stats
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

    # Add availability trend — hourly buckets
    checks = db.query(ExternalServiceCheck).filter(
        ExternalServiceCheck.service_id == svc.id,
        ExternalServiceCheck.checked_at >= cutoff,
    ).order_by(ExternalServiceCheck.checked_at).all()

    # Group checks into hourly buckets for trend
    buckets = {}
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

    # Recent alerts for this service
    recent_alerts = db.query(AlertEvent).filter(
        AlertEvent.entity_name == svc.name,
        AlertEvent.started_at >= cutoff,
    ).order_by(AlertEvent.started_at.desc()).limit(10).all()

    alerts_list = []
    for a in recent_alerts:
        alerts_list.append({
            "id": str(a.id),
            "alert_name": a.alert_name,
            "severity": a.severity,
            "status": a.status,
            "started_at": a.started_at.isoformat() if a.started_at else None,
            "ended_at": a.ended_at.isoformat() if a.ended_at else None,
        })

    # Recent incidents for this service
    recent_incidents = db.query(Incident).filter(
        Incident.entity_name == svc.name,
        Incident.started_at >= cutoff,
    ).order_by(Incident.started_at.desc()).limit(10).all()

    incidents_list = []
    for inc in recent_incidents:
        incidents_list.append({
            "id": str(inc.id),
            "status": inc.status,
            "severity": inc.severity,
            "started_at": inc.started_at.isoformat() if inc.started_at else None,
            "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
        })

    return {
        "service": metrics,
        "availability_trend": availability_trend,
        "recent_alerts": alerts_list,
        "recent_incidents": incidents_list,
        "time_range": time_range,
    }
