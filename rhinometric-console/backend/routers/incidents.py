"""
Incidents router — Phase 2.3 Incident Management Engine.

Groups related alert events into operational incidents.
Provides list, detail, and status-update endpoints.

Task 2: Only customer-facing incidents are exposed.
Internal platform entity names are excluded from list and stats.

Task 4: 30-day retention policy (keep all open/investigating,
        only last 30 days resolved). Deleted-service exclusion.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func, case, and_, or_
import re

from database import get_db
from routers.auth import get_current_user
from models.user import User as UserModel
from models.incident import Incident
from models.alert_event import AlertEvent
from models.incident_event import IncidentEvent
from models.incident_comment import IncidentComment
from models.external_service import ExternalService
from logging_config import get_logger

logger = get_logger(__name__)

# Root Cause Assistant (Phase 2.7)
from services.root_cause_engine import analyze_incident_root_cause
router = APIRouter()

VALID_STATUSES = {"open", "investigating", "resolved"}
SEVERITY_RANK = {"critical": 4, "warning": 3, "info": 2}

# ── Task 4: Retention ──────────────────────────────────────────
MAX_RETENTION_DAYS = 30


# ── Customer-facing filter — Task 2 ────────────────────────────
# Incidents whose entity_name matches any of these internal platform
# services are hidden from list / stats endpoints.
# ────────────────────────────────────────────────────────────────
INTERNAL_ENTITY_NAMES: set = {
    "console-backend",
    "docker_logs",
    "rhinometric-audit",
    "grafana",
    "loki",
    "jaeger",
    "jaeger-all-in-one",
    "jaeger-query",
    "jaeger-collector",
    "alertmanager",
    "prometheus",
    "node-exporter",
    "cadvisor",
    "ai-anomaly",
    "ai_anomaly",
    "node cpu",
    "node memory",
    "node disk",
    "container cpu",
    "container memory",
    "network receive",
    "network transmit",
    "license validation",
    "expired licenses",
}

# Also exclude entity_type == "infrastructure"
INTERNAL_ENTITY_TYPES: set = {"infrastructure"}

INTERNAL_NAME_PATTERN = re.compile(
    r"^(rhinometric[-_]|console[-_]|grafana|loki|jaeger|alertmanager"
    r"|prometheus|cadvisor|node.exporter|ai[-_]anomaly)",
    re.IGNORECASE,
)


def _is_internal_incident(entity_name: str, entity_type: str) -> bool:
    """Return True if the incident belongs to internal platform telemetry."""
    if entity_type and entity_type.lower() in INTERNAL_ENTITY_TYPES:
        return True
    name_lower = (entity_name or "").lower()
    if name_lower in INTERNAL_ENTITY_NAMES:
        return True
    if INTERNAL_NAME_PATTERN.search(name_lower):
        return True
    return False


def _apply_customer_filter(query):
    """Add SQL WHERE clauses to exclude internal platform incidents."""
    # Exclude infrastructure entity_type
    query = query.filter(
        or_(
            Incident.entity_type.is_(None),
            Incident.entity_type != "infrastructure",
        )
    )
    # Exclude exact-match internal entity names (case-insensitive)
    for name in INTERNAL_ENTITY_NAMES:
        query = query.filter(
            sa_func.lower(Incident.entity_name) != name
        )
    return query


# Entity types that reference external services
_SERVICE_ENTITY_TYPES = {"service", "external-services"}


def _get_existing_service_names(db: Session) -> set:
    """Return the set of service names that currently exist in external_services.

    Task 5 fix: existence-based check instead of enabled-flag check.
    """
    rows = db.query(ExternalService.name).all()
    return {r[0].lower() for r in rows}


def _apply_deleted_service_exclusion(query, db: Session):
    """Exclude incidents whose service no longer exists in external_services.

    Task 5 fix: existence-based.  Service-type incidents are only shown
    if their entity_name matches an existing external service.
    Non-service incidents pass through unfiltered.
    """
    existing_names = _get_existing_service_names(db)
    if existing_names:
        query = query.filter(
            or_(
                ~Incident.entity_type.in_(list(_SERVICE_ENTITY_TYPES)),
                sa_func.lower(Incident.entity_name).in_(existing_names),
            )
        )
    else:
        # No services exist at all → hide ALL service-type incidents
        query = query.filter(
            ~Incident.entity_type.in_(list(_SERVICE_ENTITY_TYPES))
        )
    return query


def _apply_retention(query, time_range: str = None):
    """Apply 30-day retention policy.

    - Open / investigating incidents are ALWAYS shown (regardless of age).
    - Resolved incidents older than 30 days are hidden.
    - User-requested time_range is respected if tighter than 30d.
    """
    retention_cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_RETENTION_DAYS)

    user_cutoff = _parse_time_range(time_range) if time_range else None
    effective_cutoff = max(retention_cutoff, user_cutoff) if user_cutoff else retention_cutoff

    query = query.filter(
        or_(
            Incident.status.in_(["open", "investigating"]),
            Incident.started_at >= effective_cutoff,
        )
    )
    return query


# ── Schemas ─────────────────────────────────────────────────────

class IncidentStatusUpdate(BaseModel):
    status: str

class CommentCreate(BaseModel):
    comment: str

class TagsUpdate(BaseModel):
    tags: List[str]



# ── Helpers ─────────────────────────────────────────────────────



def create_timeline_event(db: Session, incident_id, event_type: str,
                                                   description: str = None,
                                                   created_by: str = None,
                                                   metadata: dict = None) -> None:
    """Insert a timeline event for an incident."""
    import uuid as _uuid
    evt = IncidentEvent(
        id=_uuid.uuid4(),
        incident_id=incident_id,
        event_type=event_type,
        description=description,
        created_by=created_by,
        metadata_=metadata,
    )
    db.add(evt)
    db.flush()

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
    """Find an existing open/investigating incident for the entity, or create one.

    Race-safe: handles concurrent INSERT attempts via savepoint + retry.
    """
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
    from sqlalchemy.exc import IntegrityError

    try:
        nested = db.begin_nested()  # SAVEPOINT
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
        create_timeline_event(db, incident.id, "incident_created",
                              description=f"Incident created automatically for {entity_name}",
                              metadata={"entity_type": entity_type, "severity": severity})
        logger.info(f"Created incident {incident.id} for {key}")
        return incident
    except IntegrityError:
        nested.rollback()
        logger.info(f"Incident race resolved for {key}, fetching existing")
        existing = db.query(Incident).filter(
            Incident.incident_key == key,
        ).order_by(Incident.started_at.desc()).first()
        if existing:
            return existing
        raise  # should never happen


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
            create_timeline_event(db, incident.id, "incident_resolved",
                                  description="Incident auto-resolved — all alerts resolved",
                                  created_by="system")
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
    """List incidents with optional filters.

    Task 2: Internal platform incidents are excluded automatically.
    Task 4: 30-day retention; deleted services excluded.
    """
    query = db.query(Incident)

    # ── Task 2: exclude internal platform incidents ─────────────
    query = _apply_customer_filter(query)

    # ── Task 4: retention + deleted-service exclusion ───────────
    query = _apply_retention(query, time_range)
    query = _apply_deleted_service_exclusion(query, db)

    if status:
        query = query.filter(Incident.status == status)
    if entity_name:
        query = query.filter(Incident.entity_name.ilike(f"%{entity_name}%"))
    if severity:
        query = query.filter(Incident.severity == severity)

    total = query.count()

    incidents = query.order_by(Incident.started_at.desc()).offset(offset).limit(limit).all()

    # Post-filter: also exclude incidents matching INTERNAL_NAME_PATTERN
    # (SQL can't easily do regex, so we do a final pass in Python)
    filtered_incidents = [
        inc for inc in incidents
        if not _is_internal_incident(inc.entity_name, inc.entity_type)
    ]

    # Get alert counts per incident
    incident_ids = [i.id for i in filtered_incidents]
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
    for inc in filtered_incidents:
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
            "tags": inc.tags or [],
        })

    return {"incidents": results, "total": len(results)}


@router.get("/stats")
async def incident_stats(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregate incident statistics.

    Task 2: Only customer-facing incidents are counted.
    Task 4: retention + deleted-service exclusion applied.
    """
    base_query = _apply_customer_filter(db.query(Incident))

    # Task 4: retention + deleted-service exclusion
    retention_cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_RETENTION_DAYS)
    base_query = base_query.filter(
        or_(
            Incident.status.in_(["open", "investigating"]),
            Incident.started_at >= retention_cutoff,
        )
    )
    base_query = _apply_deleted_service_exclusion(base_query, db)

    # Fetch all customer-facing incidents and post-filter for regex patterns
    all_incidents = base_query.all()
    customer_incidents = [
        inc for inc in all_incidents
        if not _is_internal_incident(inc.entity_name, inc.entity_type)
    ]

    total = len(customer_incidents)
    open_count = sum(1 for i in customer_incidents if i.status == "open")
    investigating = sum(1 for i in customer_incidents if i.status == "investigating")
    resolved = sum(1 for i in customer_incidents if i.status == "resolved")

    avg_res = None
    durations = [
        (i.resolved_at - i.started_at).total_seconds()
        for i in customer_incidents
        if i.status == "resolved" and i.resolved_at and i.started_at
    ]
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
            "tags": incident.tags or [],
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

    old_status = incident.status
    incident.status = body.status
    incident.updated_at = datetime.now(timezone.utc)
    if body.status == "resolved" and not incident.resolved_at:
        incident.resolved_at = datetime.now(timezone.utc)

    # Timeline event for status change
    evt_type = "investigation_started" if body.status == "investigating" else "incident_resolved" if body.status == "resolved" else "status_changed"
    create_timeline_event(db, inc_uuid, evt_type,
                          description=f"Status changed from {old_status} to {body.status}",
                          created_by=current_user.username)

    db.commit()
    logger.info(f"Incident {incident_id} status → {body.status} by {current_user.username}")

    return {
        "id": str(incident.id),
        "status": incident.status,
        "updated_at": incident.updated_at.isoformat() if incident.updated_at else None,
    }



# ── Timeline endpoints ─────────────────────────────────────

@router.get("/{incident_id}/timeline")
async def get_incident_timeline(
    incident_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get chronological timeline for an incident."""
    import uuid as _uuid
    try:
        inc_uuid = _uuid.UUID(incident_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid incident ID")

    incident = db.query(Incident).filter(Incident.id == inc_uuid).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    events = db.query(IncidentEvent).filter(
        IncidentEvent.incident_id == inc_uuid,
    ).order_by(IncidentEvent.created_at.asc()).all()

    return {
        "timeline": [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "description": e.description,
                "created_by": e.created_by,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "metadata": e.metadata_,
            }
            for e in events
        ]
    }


# ── Comments endpoints ─────────────────────────────────────

@router.get("/{incident_id}/comments")
async def get_incident_comments(
    incident_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get comments for an incident."""
    import uuid as _uuid
    try:
        inc_uuid = _uuid.UUID(incident_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid incident ID")

    incident = db.query(Incident).filter(Incident.id == inc_uuid).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    comments = db.query(IncidentComment).filter(
        IncidentComment.incident_id == inc_uuid,
    ).order_by(IncidentComment.created_at.asc()).all()

    return {
        "comments": [
            {
                "id": str(c.id),
                "author": c.author,
                "comment": c.comment,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in comments
        ]
    }


@router.post("/{incident_id}/comments")
async def add_incident_comment(
    incident_id: str,
    body: CommentCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a comment to an incident."""
    import uuid as _uuid
    try:
        inc_uuid = _uuid.UUID(incident_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid incident ID")

    incident = db.query(Incident).filter(Incident.id == inc_uuid).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    comment = IncidentComment(
        id=_uuid.uuid4(),
        incident_id=inc_uuid,
        author=current_user.username,
        comment=body.comment,
    )
    db.add(comment)
    db.flush()

    # Timeline event
    create_timeline_event(db, inc_uuid, "comment_added",
                          description=f"Comment by {current_user.username}",
                          created_by=current_user.username,
                          metadata={"comment_id": str(comment.id)})

    return {
        "id": str(comment.id),
        "author": comment.author,
        "comment": comment.comment,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }


# ── Tags endpoint ──────────────────────────────────────────

@router.patch("/{incident_id}/tags")
async def update_incident_tags(
    incident_id: str,
    body: TagsUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update tags for an incident."""
    import uuid as _uuid
    try:
        inc_uuid = _uuid.UUID(incident_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid incident ID")

    incident = db.query(Incident).filter(Incident.id == inc_uuid).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    old_tags = set(incident.tags or [])
    new_tags = set(body.tags)

    added = new_tags - old_tags
    removed = old_tags - new_tags

    incident.tags = list(new_tags)
    incident.updated_at = datetime.now(timezone.utc)

    # Timeline events for tag changes
    for tag in added:
        create_timeline_event(db, inc_uuid, "tag_added",
                              description=f"Tag added: {tag}",
                              created_by=current_user.username,
                              metadata={"tag": tag})
    for tag in removed:
        create_timeline_event(db, inc_uuid, "tag_removed",
                              description=f"Tag removed: {tag}",
                              created_by=current_user.username,
                              metadata={"tag": tag})

    return {
        "id": str(incident.id),
        "tags": incident.tags,
        "updated_at": incident.updated_at.isoformat() if incident.updated_at else None,
    }




# ── Root Cause Analysis (Phase 2.7) ────────────────────────────

@router.get("/{incident_id}/root-cause")
async def get_incident_root_cause(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Analyse an incident and return a deterministic, explainable
    root-cause hypothesis based on metrics, alerts, anomalies,
    and log signals within a ±5-minute window.

    Read-only — never mutates any data.
    """
    result = await analyze_incident_root_cause(incident_id, db)
    return result


# ── Private helpers ─────────────────────────────────────────────

def _parse_time_range(tr: str) -> Optional[datetime]:
    """Convert '24h', '7d', '30d' to a datetime cutoff."""
    now = datetime.now(timezone.utc)
    if tr.endswith("h"):
        return now - timedelta(hours=int(tr[:-1]))
    if tr.endswith("d"):
        return now - timedelta(days=int(tr[:-1]))
    return None