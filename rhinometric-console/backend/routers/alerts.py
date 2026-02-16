"""
Alerts router with Silence (Alertmanager API) and Acknowledge (PostgreSQL) support.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import httpx
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from routers.auth import get_current_user
from models.user import User as UserModel
from models.alert_acknowledgement import AlertAcknowledgement, AckStatus

router = APIRouter()


# ====================================================================
# PYDANTIC SCHEMAS
# ====================================================================

class Alert(BaseModel):
    fingerprint: str
    status: str
    labels: dict
    annotations: dict
    startsAt: str
    endsAt: Optional[str] = None
    generatorURL: str
    severity: str


class AlertsResponse(BaseModel):
    alerts: list[Alert]
    total: int


class SilenceRequest(BaseModel):
    duration: str = "1h"
    comment: Optional[str] = None


class SilenceResponse(BaseModel):
    silenceID: str
    status: str
    message: str


class AckRequest(BaseModel):
    note: Optional[str] = None


class AckResponse(BaseModel):
    id: int
    fingerprint: str
    alertname: str
    status: str
    ack_by: str
    ack_at: str
    note: Optional[str] = None


class AckStatusResponse(BaseModel):
    fingerprint: str
    acknowledged: bool
    ack_by: Optional[str] = None
    ack_at: Optional[str] = None
    status: Optional[str] = None
    note: Optional[str] = None


# ====================================================================
# GET /api/alerts — List alerts from Alertmanager
# ====================================================================

@router.get("", response_model=AlertsResponse)
async def get_alerts(
    current_user: UserModel = Depends(get_current_user),
    active: Optional[bool] = Query(True, description="Filter active alerts"),
    severity: Optional[str] = Query(None, description="Filter by severity")
):
    """
    Get alerts from AlertManager (port 9093).
    Enriches each alert with acknowledgement status from PostgreSQL.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{settings.ALERTMANAGER_URL}/api/v2/alerts"
            response = await client.get(url)

            if response.status_code == 200:
                alerts_data = response.json()

                if active:
                    alerts_data = [
                        a for a in alerts_data
                        if a.get("status", {}).get("state") == "active"
                    ]

                if severity:
                    alerts_data = [
                        a for a in alerts_data
                        if a.get("labels", {}).get("severity", "").lower() == severity.lower()
                    ]

                formatted_alerts = []
                for alert in alerts_data:
                    formatted_alerts.append(Alert(
                        fingerprint=alert.get("fingerprint", ""),
                        status=alert.get("status", {}).get("state", "unknown"),
                        labels=alert.get("labels", {}),
                        annotations=alert.get("annotations", {}),
                        startsAt=alert.get("startsAt", ""),
                        endsAt=alert.get("endsAt"),
                        generatorURL=alert.get("generatorURL", ""),
                        severity=alert.get("labels", {}).get("severity", "unknown")
                    ))

                return AlertsResponse(alerts=formatted_alerts, total=len(formatted_alerts))
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"AlertManager error: {response.text}"
                )

    except httpx.ConnectError:
        return AlertsResponse(alerts=[], total=0)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")


# ====================================================================
# POST /api/alerts/{fingerprint}/silence — Create Alertmanager silence
# ====================================================================

def parse_duration(duration: str) -> timedelta:
    """Parse duration string like '1h', '4h', '30m', '24h' into timedelta."""
    try:
        value = int(duration[:-1])
        unit = duration[-1]
        if unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
    except (ValueError, IndexError):
        pass
    return timedelta(hours=1)


@router.post("/{fingerprint}/silence", response_model=SilenceResponse)
async def silence_alert(
    fingerprint: str,
    body: SilenceRequest,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a silence in Alertmanager for a specific alert.
    Uses the alert's labels (alertname, instance, job) as matchers.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # First, get the alert details to build proper matchers
            alerts_url = f"{settings.ALERTMANAGER_URL}/api/v2/alerts"
            alerts_response = await client.get(alerts_url)

            if alerts_response.status_code != 200:
                raise HTTPException(status_code=503, detail="Cannot reach Alertmanager")

            alerts_data = alerts_response.json()
            target_alert = None
            for alert in alerts_data:
                if alert.get("fingerprint") == fingerprint:
                    target_alert = alert
                    break

            if not target_alert:
                raise HTTPException(status_code=404, detail=f"Alert with fingerprint {fingerprint} not found")

            # Build matchers from the alert's key labels
            labels = target_alert.get("labels", {})
            matchers = []

            # Always match on alertname
            if "alertname" in labels:
                matchers.append({
                    "name": "alertname",
                    "value": labels["alertname"],
                    "isRegex": False,
                    "isEqual": True
                })

            # Add instance matcher if present
            if "instance" in labels:
                matchers.append({
                    "name": "instance",
                    "value": labels["instance"],
                    "isRegex": False,
                    "isEqual": True
                })

            # Add job matcher if present
            if "job" in labels:
                matchers.append({
                    "name": "job",
                    "value": labels["job"],
                    "isRegex": False,
                    "isEqual": True
                })

            if not matchers:
                raise HTTPException(status_code=400, detail="No valid labels to create silence matchers")

            # Calculate time range
            now = datetime.now(timezone.utc)
            delta = parse_duration(body.duration)
            ends_at = now + delta

            comment = body.comment or f"Silenced from Rhinometric Console for {body.duration}"

            silence_data = {
                "matchers": matchers,
                "startsAt": now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "endsAt": ends_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "createdBy": current_user.username,
                "comment": comment
            }

            response = await client.post(
                f"{settings.ALERTMANAGER_URL}/api/v2/silences",
                json=silence_data
            )

            if response.status_code in (200, 201):
                result = response.json()
                silence_id = result.get("silenceID", result) if isinstance(result, dict) else str(result)
                return SilenceResponse(
                    silenceID=str(silence_id),
                    status="success",
                    message=f"Alert silenced for {body.duration} by {current_user.username}"
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Alertmanager silence failed: {response.text}"
                )

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="AlertManager is not available")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create silence: {str(e)}")


# ====================================================================
# GET /api/alerts/silences — List active silences
# ====================================================================

@router.get("/silences")
async def get_silences(current_user: UserModel = Depends(get_current_user)):
    """Get all active silences from Alertmanager."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.ALERTMANAGER_URL}/api/v2/silences")
            if response.status_code == 200:
                silences = response.json()
                # Filter only active silences
                active = [s for s in silences if s.get("status", {}).get("state") == "active"]
                return {"silences": active, "total": len(active)}
            return {"silences": [], "total": 0}
    except Exception:
        return {"silences": [], "total": 0}


# ====================================================================
# POST /api/alerts/{fingerprint}/ack — Acknowledge an alert
# ====================================================================

@router.post("/{fingerprint}/ack", response_model=AckResponse)
async def acknowledge_alert(
    fingerprint: str,
    body: AckRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Acknowledge an alert — records in PostgreSQL that someone is handling it.
    If already acknowledged, updates the record.
    """
    # Check if already acknowledged
    existing = db.query(AlertAcknowledgement).filter(
        AlertAcknowledgement.fingerprint == fingerprint,
        AlertAcknowledgement.status == AckStatus.ACKNOWLEDGED.value
    ).first()

    if existing:
        # Update existing acknowledgement
        existing.ack_by = current_user.username
        existing.ack_at = datetime.now(timezone.utc)
        existing.note = body.note or existing.note
        db.flush()
        ack = existing
    else:
        # Get alertname from Alertmanager
        alertname = fingerprint  # fallback
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.ALERTMANAGER_URL}/api/v2/alerts")
                if response.status_code == 200:
                    for alert in response.json():
                        if alert.get("fingerprint") == fingerprint:
                            alertname = alert.get("labels", {}).get("alertname", fingerprint)
                            break
        except Exception:
            pass

        ack = AlertAcknowledgement(
            fingerprint=fingerprint,
            alertname=alertname,
            status=AckStatus.ACKNOWLEDGED.value,
            ack_by=current_user.username,
            note=body.note
        )
        db.add(ack)
        db.flush()

    return AckResponse(
        id=ack.id,
        fingerprint=ack.fingerprint,
        alertname=ack.alertname,
        status=ack.status,
        ack_by=ack.ack_by,
        ack_at=ack.ack_at.isoformat() if ack.ack_at else "",
        note=ack.note
    )


# ====================================================================
# GET /api/alerts/ack-status — Get acknowledgement status for alerts
# ====================================================================

@router.get("/ack-status")
async def get_ack_status(
    fingerprints: str = Query(..., description="Comma-separated list of fingerprints"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get acknowledgement status for one or more alerts.
    Query param: fingerprints=fp1,fp2,fp3
    """
    fp_list = [fp.strip() for fp in fingerprints.split(",") if fp.strip()]

    acks = db.query(AlertAcknowledgement).filter(
        AlertAcknowledgement.fingerprint.in_(fp_list),
        AlertAcknowledgement.status == AckStatus.ACKNOWLEDGED.value
    ).all()

    ack_map = {}
    for ack in acks:
        ack_map[ack.fingerprint] = AckStatusResponse(
            fingerprint=ack.fingerprint,
            acknowledged=True,
            ack_by=ack.ack_by,
            ack_at=ack.ack_at.isoformat() if ack.ack_at else None,
            status=ack.status,
            note=ack.note
        )

    result = {}
    for fp in fp_list:
        if fp in ack_map:
            result[fp] = ack_map[fp]
        else:
            result[fp] = AckStatusResponse(fingerprint=fp, acknowledged=False)

    return result


# ====================================================================
# POST /api/alerts/{fingerprint}/resolve — Resolve an acknowledgement
# ====================================================================

@router.post("/{fingerprint}/resolve")
async def resolve_alert(
    fingerprint: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark an acknowledged alert as resolved."""
    ack = db.query(AlertAcknowledgement).filter(
        AlertAcknowledgement.fingerprint == fingerprint,
        AlertAcknowledgement.status == AckStatus.ACKNOWLEDGED.value
    ).first()

    if not ack:
        raise HTTPException(status_code=404, detail="No active acknowledgement found for this alert")

    ack.status = AckStatus.RESOLVED.value
    ack.resolved_at = datetime.now(timezone.utc)
    db.flush()

    return {"status": "resolved", "fingerprint": fingerprint, "resolved_by": current_user.username}
