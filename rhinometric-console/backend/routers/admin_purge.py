"""
Task 4 — Admin Purge Router.

Provides manual purge endpoints for admin users to clear historical
data from Alerts, Incidents, and Anomalies.

Safety: requires ADMIN role + explicit confirm=true in request body.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

from database import get_db
from models.alert_event import AlertEvent
from models.incident import Incident
from models.user import User as UserModel
from routers.auth import get_current_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Schemas ─────────────────────────────────────────────────────

class PurgeRequest(BaseModel):
    confirm: bool = Field(False, description="Must be true to execute purge")
    older_than_days: int = Field(30, ge=1, le=365, description="Purge records older than N days")


class PurgeResponse(BaseModel):
    module: str
    deleted_count: int
    older_than_days: int
    message: str


# ── Helpers ─────────────────────────────────────────────────────

# ── POST /api/admin/purge/alerts ────────────────────────────────

@router.post("/alerts", response_model=PurgeResponse)
async def purge_alerts(
    body: PurgeRequest,
    current_user: UserModel = Depends(require_role(["OWNER"])),
    db: Session = Depends(get_db),
):
    """Purge resolved alert events older than N days.

    - Only resolved/suppressed alerts are deleted.
    - Firing/acknowledged alerts are NEVER deleted.
    - Requires admin role + confirm=true.
    """
    if not body.confirm:
        raise HTTPException(
            status_code=400,
            detail="Purge not confirmed. Set confirm=true to execute."
        )

    cutoff = datetime.now(timezone.utc) - timedelta(days=body.older_than_days)

    count = db.query(AlertEvent).filter(
        AlertEvent.status.in_(["resolved", "suppressed"]),
        AlertEvent.started_at < cutoff,
    ).delete(synchronize_session='fetch')

    db.commit()
    logger.info(f"PURGE alerts: {count} resolved events older than {body.older_than_days}d deleted by {current_user.username}")

    return PurgeResponse(
        module="alerts",
        deleted_count=count,
        older_than_days=body.older_than_days,
        message=f"Purged {count} resolved alert events older than {body.older_than_days} days",
    )


# ── POST /api/admin/purge/incidents ─────────────────────────────

@router.post("/incidents", response_model=PurgeResponse)
async def purge_incidents(
    body: PurgeRequest,
    current_user: UserModel = Depends(require_role(["OWNER"])),
    db: Session = Depends(get_db),
):
    """Purge resolved incidents older than N days.

    - Only resolved incidents are deleted.
    - Open/investigating incidents are NEVER deleted.
    - Related timeline events and comments are cascaded by FK.
    - Requires admin role + confirm=true.
    """
    if not body.confirm:
        raise HTTPException(
            status_code=400,
            detail="Purge not confirmed. Set confirm=true to execute."
        )

    cutoff = datetime.now(timezone.utc) - timedelta(days=body.older_than_days)

    # Find resolved incidents older than cutoff
    old_incidents = db.query(Incident).filter(
        Incident.status == "resolved",
        Incident.started_at < cutoff,
    ).all()

    count = 0
    for inc in old_incidents:
        # Unlink alert events (set incident_id to NULL rather than cascade-delete alerts)
        db.query(AlertEvent).filter(
            AlertEvent.incident_id == inc.id
        ).update({AlertEvent.incident_id: None}, synchronize_session='fetch')

        # Delete timeline events and comments (cascade)
        from models.incident_event import IncidentEvent
        from models.incident_comment import IncidentComment
        db.query(IncidentEvent).filter(IncidentEvent.incident_id == inc.id).delete(synchronize_session='fetch')
        db.query(IncidentComment).filter(IncidentComment.incident_id == inc.id).delete(synchronize_session='fetch')

        db.delete(inc)
        count += 1

    db.commit()
    logger.info(f"PURGE incidents: {count} resolved incidents older than {body.older_than_days}d deleted by {current_user.username}")

    return PurgeResponse(
        module="incidents",
        deleted_count=count,
        older_than_days=body.older_than_days,
        message=f"Purged {count} resolved incidents older than {body.older_than_days} days",
    )


# ── POST /api/admin/purge/anomalies ────────────────────────────

@router.post("/anomalies", response_model=PurgeResponse)
async def purge_anomalies(
    body: PurgeRequest,
    current_user: UserModel = Depends(require_role(["OWNER"])),
):
    """Purge anomaly status overrides (in-memory lifecycle data).

    Since anomalies are fetched live from the AI service and have no
    persistent DB table, purging means clearing the in-memory
    _status_overrides dict for resolved/suppressed/false_positive entries.

    - Active/acknowledged statuses are NOT cleared.
    - Requires admin role + confirm=true.
    """
    if not body.confirm:
        raise HTTPException(
            status_code=400,
            detail="Purge not confirmed. Set confirm=true to execute."
        )

    from routers.anomalies import _status_overrides

    purgeable_statuses = {"resolved", "suppressed", "false_positive"}
    keys_to_remove = [
        fp for fp, status in _status_overrides.items()
        if status in purgeable_statuses
    ]

    for fp in keys_to_remove:
        del _status_overrides[fp]

    count = len(keys_to_remove)
    logger.info(f"PURGE anomalies: {count} status overrides cleared by {current_user.username}")

    return PurgeResponse(
        module="anomalies",
        deleted_count=count,
        older_than_days=body.older_than_days,
        message=f"Purged {count} anomaly status overrides (resolved/suppressed/false_positive)",
    )