"""
Phase 2.2 — Alert Event Store: Alert History API.

Provides endpoints to query the persistent alert event history and
ingest alert lifecycle transitions.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.alert_event import AlertEvent
from models.user import User as UserModel
from routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Helpers ───────────────────────────────────────────────────────

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


# ── GET /api/alerts/history ───────────────────────────────────────

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
    """Get alert event history from the persistent store, newest first."""
    query = db.query(AlertEvent)

    # Time range filter
    cutoff = _parse_time_range(time_range) if time_range else None
    if cutoff:
        query = query.filter(AlertEvent.started_at >= cutoff)

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


# ── GET /api/alerts/history/stats ─────────────────────────────────

@router.get("/stats")
async def get_alert_stats(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    time_range: Optional[str] = Query("24h"),
):
    """Aggregate alert event statistics."""
    from sqlalchemy import func as sqlfunc

    query = db.query(AlertEvent)
    cutoff = _parse_time_range(time_range) if time_range else None
    if cutoff:
        query = query.filter(AlertEvent.started_at >= cutoff)

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
