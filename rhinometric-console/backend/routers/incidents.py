"""
Incidents router — Phase 2.3 Incident Management Engine.

Groups related alert events into operational incidents.
Provides list, detail, and status-update endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func, case

from database import get_db
from routers.auth import get_current_user
from models.user import User as UserModel
from models.incident import Incident
from models.alert_event import AlertEvent
from logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

VALID_STATUSES = {"open", "investigating", "resolved"}
SEVERITY_RANK = {"critical": 4, "warning": 3, "info": 2}


# ── Schemas ─────────────────────────────────────────────────────

class IncidentStatusUpdate(BaseModel):
    status: str


# ── Helpers ─────────────────────────────────────────────────────

def _incident_key(entity_type: str, entity_name: str) -> str:
    """Deterministic grouping key for incidents."""
    return f"{entity_type}:{entity_name}"


def _highest_severity(current: str, incoming: str) -> str:
    """Return the higher severity between two values."""
    if SEVERITY_RANK.get(incoming, 0) > SEVERITY_RANK.get(current, 0):
        return incoming
    return current


def find_or_create_incident(db: Session, entity_type: str, entity_name: str,
                             severity: str, started_at: datetime) -> "Incident":
    """Find an existing open/investigating incident for the entity, or create one."""
    key = _incident_key(entity_type, entity_name)

    existing = db.query(Incident).filter(
        Incident.incident_key == key,
        Incident.status.in_(["open", "investigating"]),
    ).first()

    if existing:
        # Escalate severity if incoming is higher
        new_sev = _highest_severity(existing.severity, severity)
        if new_sev != existing.severity:
            existing.severity = new_sev
            existing.updated_at = datetime.now(timezone.utc)
        return existing

    import uuid
    incident = Incident(
        id=uuid.uuid4(),
        incident_key=key,
        entity_name=entity_name,
        entity_type=entity_type,
        severity=severity,
        status="open",
        started_at=started_at,
    )
    db.add(incident)
    db.flush()  # get the ID before commit
    logger.info(f"Created incident {incident.id} for {key}")
    return incident


def check_incident_resolution(db: Session, incident_id) -> None:
    """If all linked alert events are resolved, resolve the incident."""
    if incident_id is None:
        return

    still_active = db.query(AlertEvent).filter(
        AlertEvent.incident_id == incident_id,
        AlertEvent.status.in_(["firing", "acknowledged"]),
    ).count()

    if still_active == 0:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if incident and incident.status != "resolved":
            incident.status = "resolved"
            incident.resolved_at = datetime.now(timezone.utc)
            incident.updated_at = datetime.now(timezone.utc)
            logger.info(f"Auto-resolved incident {incident.id} — all alerts resolved")


# ── Endpoints ───────────────────────────────────────────────────

@router.get("")
async def list_incidents(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    entity_name: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    time_range: Optional[str] = Query("7d"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List incidents with optional filters."""
    query = db.query(Incident)

    # Time range filter
    if time_range:
        cutoff = _parse_time_range(time_range)
        if cutoff:
            query = query.filter(Incident.started_at >= cutoff)

    if status:
        query = query.filter(Incident.status == status)
    if entity_name:
        query = query.filter(Incident.entity_name.ilike(f"%{entity_name}%"))
    if severity:
        query = query.filter(Incident.severity == severity)

    total = query.count()

    incidents = query.order_by(Incident.started_at.desc()).offset(offset).limit(limit).all()

    # Get alert counts per incident
    incident_ids = [i.id for i in incidents]
    alert_counts = {}
    if incident_ids:
        counts = db.query(
            AlertEvent.incident_id,
            sa_func.count(AlertEvent.id).label("cnt")
        ).filter(
            AlertEvent.incident_id.in_(incident_ids)
        ).group_by(AlertEvent.incident_id).all()
        alert_counts = {row[0]: row[1] for row in counts}

    results = []
    for inc in incidents:
        duration = None
        if inc.resolved_at and inc.started_at:
            duration = int((inc.resolved_at - inc.started_at).total_seconds())

        results.append({
            "id": str(inc.id),
            "incident_key": inc.incident_key,
            "entity_name": inc.entity_name,
            "entity_type": inc.entity_type,
            "severity": inc.severity,
            "status": inc.status,
            "started_at": inc.started_at.isoformat() if inc.started_at else None,
            "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
            "duration_seconds": duration,
            "alert_count": alert_counts.get(inc.id, 0),
            "created_at": inc.created_at.isoformat() if inc.created_at else None,
            "updated_at": inc.updated_at.isoformat() if inc.updated_at else None,
        })

    return {"incidents": results, "total": total}


@router.get("/stats")
async def incident_stats(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregate incident statistics."""
    total = db.query(sa_func.count(Incident.id)).scalar() or 0
    open_count = db.query(sa_func.count(Incident.id)).filter(Incident.status == "open").scalar() or 0
    investigating = db.query(sa_func.count(Incident.id)).filter(Incident.status == "investigating").scalar() or 0
    resolved = db.query(sa_func.count(Incident.id)).filter(Incident.status == "resolved").scalar() or 0

    avg_res = None
    resolved_incidents = db.query(Incident).filter(
        Incident.status == "resolved",
        Incident.resolved_at.isnot(None),
    ).all()
    if resolved_incidents:
        durations = [(i.resolved_at - i.started_at).total_seconds() for i in resolved_incidents if i.resolved_at and i.started_at]
        if durations:
            avg_res = round(sum(durations) / len(durations))

    return {
        "total": total,
        "open": open_count,
        "investigating": investigating,
        "resolved": resolved,
        "avg_resolution_seconds": avg_res,
    }


@router.get("/{incident_id}")
async def get_incident(
    incident_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get incident details with related alert events."""
    import uuid as _uuid
    try:
        inc_uuid = _uuid.UUID(incident_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid incident ID")

    incident = db.query(Incident).filter(Incident.id == inc_uuid).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get linked alert events
    alert_events = db.query(AlertEvent).filter(
        AlertEvent.incident_id == inc_uuid
    ).order_by(AlertEvent.started_at.desc()).all()

    duration = None
    if incident.resolved_at and incident.started_at:
        duration = int((incident.resolved_at - incident.started_at).total_seconds())

    events_list = []
    for ev in alert_events:
        ev_duration = None
        if ev.ended_at and ev.started_at:
            ev_duration = int((ev.ended_at - ev.started_at).total_seconds())
        events_list.append({
            "id": str(ev.id),
            "alert_name": ev.alert_name,
            "entity_type": ev.entity_type,
            "entity_name": ev.entity_name,
            "metric_name": ev.metric_name,
            "severity": ev.severity,
            "status": ev.status,
            "started_at": ev.started_at.isoformat() if ev.started_at else None,
            "ended_at": ev.ended_at.isoformat() if ev.ended_at else None,
            "duration_seconds": ev_duration,
            "fingerprint": ev.fingerprint,
            "summary": ev.summary,
        })

    return {
        "incident": {
            "id": str(incident.id),
            "incident_key": incident.incident_key,
            "entity_name": incident.entity_name,
            "entity_type": incident.entity_type,
            "severity": incident.severity,
            "status": incident.status,
            "started_at": incident.started_at.isoformat() if incident.started_at else None,
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
            "duration_seconds": duration,
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
            "updated_at": incident.updated_at.isoformat() if incident.updated_at else None,
        },
        "alert_events": events_list,
        "alert_count": len(events_list),
    }


@router.patch("/{incident_id}")
async def update_incident_status(
    incident_id: str,
    body: IncidentStatusUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update incident status (investigating / resolved)."""
    import uuid as _uuid
    try:
        inc_uuid = _uuid.UUID(incident_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid incident ID")

    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status. Allowed: {VALID_STATUSES}")

    incident = db.query(Incident).filter(Incident.id == inc_uuid).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = body.status
    incident.updated_at = datetime.now(timezone.utc)
    if body.status == "resolved" and not incident.resolved_at:
        incident.resolved_at = datetime.now(timezone.utc)

    db.commit()
    logger.info(f"Incident {incident_id} status → {body.status} by {current_user.username}")

    return {
        "id": str(incident.id),
        "status": incident.status,
        "updated_at": incident.updated_at.isoformat() if incident.updated_at else None,
    }


# ── Private helpers ─────────────────────────────────────────────

def _parse_time_range(tr: str) -> Optional[datetime]:
    """Convert '24h', '7d', '30d' to a datetime cutoff."""
    now = datetime.now(timezone.utc)
    if tr.endswith("h"):
        return now - timedelta(hours=int(tr[:-1]))
    if tr.endswith("d"):
        return now - timedelta(days=int(tr[:-1]))
    return None
