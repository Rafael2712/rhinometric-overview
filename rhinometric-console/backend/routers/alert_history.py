"""
Phase 2.2 — Alert Event Store: Alert History API.

Provides endpoints to query the persistent alert event history and
ingest alert lifecycle transitions.

Task 4: 30-day retention policy (query-level), deleted-service exclusion.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc

from database import get_db
from models.alert_event import AlertEvent
from models.external_service import ExternalService
from models.user import User as UserModel
from routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ───────────────────────────────────────────────────
MAX_RETENTION_DAYS = 30


# ── Helpers ─────────────────────────────────────────────────────

def _alert_fingerprint(alert_name: str, entity_name: str, metric_name: str = "") -> str:
    """Generate deterministic fingerprint for alert-anomaly correlation."""
    seed = f"{alert_name}|{entity_name}|{metric_name}"
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


def _parse_time_range(time_range: str) -> Optional[datetime]:
    """Convert time_range string (e.g. '24h', '7d') to a cutoff datetime."""
    now = datetime.now(timezone.utc)
    multipliers = {"m": 60, "h": 3600, "d": 86400, "w": 604800}
    if not time_range:
        return None
    unit = time_range[-1].lower()
    if unit not in multipliers:
        return None
    try:
        value = int(time_range[:-1])
    except ValueError:
        return None
    return now - timedelta(seconds=value * multipliers[unit])


# Entity types that reference external services
_SERVICE_ENTITY_TYPES = {"service", "external-services"}


def _get_existing_service_names(db: Session) -> set:
    """Return the set of service names that currently exist in external_services.

    Task 5 fix: instead of checking enabled == False (which misses
    fully-deleted rows), we now collect ALL existing names.  Any
    alert/incident whose entity_type is service-related AND whose
    entity_name is NOT in this set is treated as orphaned and hidden.
    """
    rows = db.query(ExternalService.name).all()
    return {r[0].lower() for r in rows}


def _apply_retention_and_exclusion(query, db: Session, time_range: str = None):
    """Apply 30-day retention cap and deleted-service exclusion.

    Retention: resolved alerts older than 30 days are hidden;
               firing/acknowledged alerts are always shown.
    Exclusion: alerts whose entity_name matches a disabled service are hidden.
    """
    # ── Retention cap ───────────────────────────────────────────
    retention_cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_RETENTION_DAYS)

    # If user-requested cutoff is within 30d, use that; otherwise cap at 30d
    user_cutoff = _parse_time_range(time_range) if time_range else None
    effective_cutoff = max(retention_cutoff, user_cutoff) if user_cutoff else retention_cutoff

    # Always show firing/acknowledged regardless of age; apply cutoff to resolved
    from sqlalchemy import or_, and_
    query = query.filter(
        or_(
            AlertEvent.status.in_(["firing", "acknowledged"]),
            AlertEvent.started_at >= effective_cutoff,
        )
    )

    # ── Deleted-service exclusion (Task 5: existence-based) ─────
    existing_names = _get_existing_service_names(db)
    # For service-related alerts: only keep those whose entity_name
    # still exists in the external_services table.
    # Non-service alerts (website, infrastructure, etc.) pass through.
    if existing_names:
        # Exclude service-type alerts whose name is NOT in existing set
        query = query.filter(
            or_(
                ~AlertEvent.entity_type.in_(list(_SERVICE_ENTITY_TYPES)),
                sqlfunc.lower(AlertEvent.entity_name).in_(existing_names),
            )
        )
    else:
        # No services exist at all → exclude ALL service-type alerts
        query = query.filter(
            ~AlertEvent.entity_type.in_(list(_SERVICE_ENTITY_TYPES))
        )


    # Infrastructure alert exclusion: only show external-service alerts.
    # Grafana alert rules use human-readable names like "External Service Down",
    # "SSL Certificate Critical", etc.  The reliable discriminator is entity_type
    # which the webhook sets from the Grafana "category" label.
    _ALLOWED_ENTITY_TYPES = {"external-services"}
    _ALLOWED_ALERT_PREFIXES = ("External Service", "SSL Certificate")
    query = query.filter(
        or_(
            AlertEvent.entity_type.in_(list(_ALLOWED_ENTITY_TYPES)),
            AlertEvent.alert_name.like("External Service%"),
            AlertEvent.alert_name.like("SSL Certificate%"),
        )
    )

    return query


# ── GET /api/alerts/history ─────────────────────────────────────

@router.get("")
async def get_alert_event_history(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    time_range: Optional[str] = Query("24h", description="Time range: 1h, 6h, 24h, 7d, 30d"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_name: Optional[str] = Query(None, description="Filter by entity name"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status (firing/resolved/acknowledged/suppressed)"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get alert event history from the persistent store, newest first.

    Task 4: 30-day retention policy applied; deleted services excluded.
    """
    query = db.query(AlertEvent)

    # Task 4: retention + deleted-service exclusion
    query = _apply_retention_and_exclusion(query, db, time_range)

    if entity_type:
        query = query.filter(AlertEvent.entity_type == entity_type)
    if entity_name:
        query = query.filter(AlertEvent.entity_name == entity_name)
    if severity:
        query = query.filter(AlertEvent.severity == severity)
    if status:
        query = query.filter(AlertEvent.status == status)

    total = query.count()
    records = query.order_by(AlertEvent.started_at.desc()).offset(offset).limit(limit).all()

    events = []
    for r in records:
        duration = None
        if r.ended_at and r.started_at:
            duration = int((r.ended_at - r.started_at).total_seconds())

        events.append({
            "id": str(r.id),
            "alert_name": r.alert_name,
            "entity_type": r.entity_type,
            "entity_name": r.entity_name,
            "metric_name": r.metric_name,
            "severity": r.severity,
            "status": r.status,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "ended_at": r.ended_at.isoformat() if r.ended_at else None,
            "duration_seconds": duration,
            "fingerprint": r.fingerprint,
            "summary": r.summary,
            "source": r.source,
            "labels": r.labels,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return {
        "alert_events": events,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ── GET /api/alerts/history/stats ───────────────────────────────

@router.get("/stats")
async def get_alert_stats(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    time_range: Optional[str] = Query("24h"),
):
    """Aggregate alert event statistics.

    Task 4: retention + deleted-service exclusion applied.
    """
    query = db.query(AlertEvent)

    # Task 4: retention + deleted-service exclusion
    query = _apply_retention_and_exclusion(query, db, time_range)

    total = query.count()
    firing = query.filter(AlertEvent.status == "firing").count()
    resolved = query.filter(AlertEvent.status == "resolved").count()
    acknowledged = query.filter(AlertEvent.status == "acknowledged").count()

    # Average duration of resolved alerts
    avg_duration = None
    resolved_with_end = query.filter(
        AlertEvent.status == "resolved",
        AlertEvent.ended_at.isnot(None),
    ).all()
    if resolved_with_end:
        durations = [(r.ended_at - r.started_at).total_seconds() for r in resolved_with_end if r.ended_at and r.started_at]
        if durations:
            avg_duration = int(sum(durations) / len(durations))

    return {
        "total": total,
        "firing": firing,
        "resolved": resolved,
        "acknowledged": acknowledged,
        "avg_resolution_seconds": avg_duration,
    }