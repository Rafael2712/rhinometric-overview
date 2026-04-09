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
    Get operational alerts from both sources:
      1. External Alertmanager -- AI anomaly engine alerts
      2. Grafana internal alertmanager -- synthetic monitoring rule alerts
    Merges, deduplicates, and filters to show only external-service alerts.
    """
    import asyncio as _aio

    alerts_data: list[dict] = []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # ---- fire both queries concurrently ----
            am_coro = client.get(f"{settings.ALERTMANAGER_URL}/api/v2/alerts")
            gf_url = f"{settings.GRAFANA_URL}/api/alertmanager/grafana/api/v2/alerts"
            gf_coro = client.get(
                gf_url,
                auth=(settings.GRAFANA_USER, settings.GRAFANA_PASSWORD),
            )
            am_resp, gf_resp = await _aio.gather(
                am_coro, gf_coro, return_exceptions=True
            )

            # -- Source 1: External Alertmanager (AI anomaly engine) --
            if not isinstance(am_resp, Exception) and am_resp.status_code == 200:
                am_alerts = am_resp.json()
                if active:
                    am_alerts = [
                        a for a in am_alerts
                        if a.get("status", {}).get("state") == "active"
                    ]
                # Keep only external-service AI anomaly alerts
                am_alerts = [
                    a for a in am_alerts
                    if a.get("labels", {}).get("metric", "").startswith("external_service_")
                ]
                alerts_data.extend(am_alerts)

            # -- Source 2: Grafana internal alertmanager (synthetic monitoring) --
            if not isinstance(gf_resp, Exception) and gf_resp.status_code == 200:
                gf_alerts = gf_resp.json()
                if active:
                    gf_alerts = [
                        a for a in gf_alerts
                        if a.get("status", {}).get("state") == "active"
                    ]
                # Keep only external-service category (hide infra alerts)
                gf_alerts = [
                    a for a in gf_alerts
                    if a.get("labels", {}).get("category") == "external-services"
                ]
                alerts_data.extend(gf_alerts)

        # -- Severity filter --
        if severity:
            alerts_data = [
                a for a in alerts_data
                if a.get("labels", {}).get("severity", "").lower() == severity.lower()
            ]

        # -- Deduplicate by fingerprint --
        seen: set[str] = set()
        deduped: list[dict] = []
        for alert in alerts_data:
            fp = alert.get("fingerprint", "")
            if fp and fp in seen:
                continue
            if fp:
                seen.add(fp)
            deduped.append(alert)

        formatted_alerts = []
        for alert in deduped:
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


# ==================================================================
# POST /api/alerts/webhook — Grafana webhook contact point receiver
# ==================================================================

from models.alert_history import AlertHistory
from models.alert_event import AlertEvent
from routers.incidents import find_or_create_incident, check_incident_resolution
from datetime import datetime as dt_parser
import hashlib
import logging

logger = logging.getLogger(__name__)


@router.post("/webhook")
async def grafana_webhook(
    request_body: dict,
    db: Session = Depends(get_db)
):
    """
    Receives alert notifications from Grafana webhook contact point.
    Stores each alert in alert_history table for in-console display.
    No authentication required (internal Docker network only).
    """
    alerts = request_body.get("alerts", [])
    stored = 0

    for alert in alerts:
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})

        # Generate fingerprint from labels if not provided
        fingerprint = alert.get("fingerprint", "")
        if not fingerprint:
            fp_str = str(sorted(labels.items()))
            fingerprint = hashlib.md5(fp_str.encode()).hexdigest()[:16]

        # Parse timestamps
        starts_at = None
        ends_at = None
        try:
            if alert.get("startsAt"):
                starts_at = datetime.fromisoformat(alert["startsAt"])
            if alert.get("endsAt") and alert["endsAt"] != "0001-01-01T00:00:00Z":
                ends_at = datetime.fromisoformat(alert["endsAt"])
        except Exception:
            pass

        # Extract value if present
        value = None
        try:
            value_str = alert.get("valueString", "")
            if value_str:
                # Try to extract numeric value from Grafana value string
                import re
                nums = re.findall(r'[-+]?\d*\.?\d+', value_str)
                if nums:
                    value = float(nums[0])
        except Exception:
            pass

        record = AlertHistory(
            fingerprint=fingerprint,
            alertname=labels.get("alertname", "unknown"),
            status=alert.get("status", "unknown"),
            severity=labels.get("severity", "unknown"),
            category=labels.get("category", ""),
            service_name=labels.get("service_name", ""),
            summary=annotations.get("summary", ""),
            description=annotations.get("description", ""),
            labels=labels,
            annotations=annotations,
            value=value,
            starts_at=starts_at,
            ends_at=ends_at,
            generator_url=alert.get("generatorURL", ""),
        )
        db.add(record)
        stored += 1

    # ── Phase 2.2: Persist in alert_events for lifecycle history ──
    events_stored = 0
    for alert in alerts:
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        alert_name = labels.get("alertname", "unknown")
        entity_name = labels.get("service_name", "") or labels.get("instance", "unknown")
        entity_type = labels.get("category", "service")
        metric_name = labels.get("metric_name", "") or labels.get("__name__", "")
        severity = labels.get("severity", "warning")
        a_status = alert.get("status", "firing")

        # Build correlation fingerprint
        import hashlib as _hl
        fp_seed = f"{alert_name}|{entity_name}|{metric_name}"
        event_fp = _hl.sha256(fp_seed.encode()).hexdigest()[:16]

        starts_at = None
        ends_at = None
        try:
            if alert.get("startsAt"):
                starts_at = datetime.fromisoformat(alert["startsAt"])
            if alert.get("endsAt") and alert["endsAt"] != "0001-01-01T00:00:00Z":
                ends_at = datetime.fromisoformat(alert["endsAt"])
        except Exception:
            pass

        if a_status == "resolved":
            # Try to update existing firing event
            existing = db.query(AlertEvent).filter(
                AlertEvent.fingerprint == event_fp,
                AlertEvent.status == "firing",
            ).order_by(AlertEvent.started_at.desc()).first()
            if existing:
                existing.status = "resolved"
                existing.ended_at = ends_at or datetime.utcnow()
                db.flush()  # Flush status change so resolution query sees it
                # Phase 2.3: Check incident resolution
                if existing.incident_id:
                    try:
                        check_incident_resolution(db, existing.incident_id)
                    except Exception as e:
                        logger.error(f"Resolution check error: {e}")
                else:
                    # Event may have been created before Phase 2.3; try to find incident by entity
                    try:
                        from routers.incidents import _incident_key
                        from models.incident import Incident
                        key = _incident_key(entity_type, entity_name)
                        inc = db.query(Incident).filter(
                            Incident.incident_key == key,
                            Incident.status.in_(["open", "investigating"]),
                        ).first()
                        if inc:
                            existing.incident_id = inc.id
                            check_incident_resolution(db, inc.id)
                    except Exception as e:
                        logger.error(f"Fallback resolution check error: {e}")
                events_stored += 1
                continue

        # Create new event row
        import uuid
        event = AlertEvent(
            id=uuid.uuid4(),
            alert_name=alert_name,
            entity_type=entity_type,
            entity_name=entity_name,
            metric_name=metric_name,
            severity=severity,
            status=a_status,
            started_at=starts_at or datetime.utcnow(),
            ended_at=ends_at if a_status == "resolved" else None,
            fingerprint=event_fp,
            labels=labels,
            annotations=annotations,
            summary=annotations.get("summary", ""),
            source="alertmanager",
            generator_url=alert.get("generatorURL", ""),
        )
        db.add(event)
        db.flush()

        # Phase 2.3: Link alert event to incident
        try:
            inc = find_or_create_incident(db, entity_type, entity_name, severity, event.started_at)
            event.incident_id = inc.id
        except Exception as _inc_err:
            logger.warning(f"Incident linkage failed: {_inc_err}")

        events_stored += 1

    # Phase 2.3: Flush all event changes, then check incident resolution
    db.flush()
    for alert in alerts:
        if alert.get("status") == "resolved":
            labels_r = alert.get("labels", {})
            alert_name_r = labels_r.get("alertname", "unknown")
            entity_name_r = labels_r.get("service_name", "") or labels_r.get("instance", "unknown")
            metric_name_r = labels_r.get("metric_name", "") or labels_r.get("__name__", "")
            import hashlib as _hl2
            fp_r = _hl2.sha256(f"{alert_name_r}|{entity_name_r}|{metric_name_r}".encode()).hexdigest()[:16]
            ev_r = db.query(AlertEvent).filter(
                AlertEvent.fingerprint == fp_r,
            ).order_by(AlertEvent.started_at.desc()).first()
            if ev_r and ev_r.incident_id:
                try:
                    check_incident_resolution(db, ev_r.incident_id)
                except Exception as e:
                    logger.error(f"Post-loop resolution check error: {e}")

    db.commit()

    # ---- Forward external-service alerts to Alertmanager for Slack/email notifications ----
    svc_alerts = [
        a for a in alerts
        if a.get("labels", {}).get("category") == "external-services"
    ]
    if svc_alerts:
        try:
            am_payload = []
            for a in svc_alerts:
                entry = {
                    "labels": a.get("labels", {}),
                    "annotations": a.get("annotations", {}),
                    "startsAt": a.get("startsAt", datetime.now(timezone.utc).isoformat()),
                    "generatorURL": a.get("generatorURL", ""),
                }
                if a.get("status") == "resolved":
                    entry["endsAt"] = a.get("endsAt", datetime.now(timezone.utc).isoformat())
                am_payload.append(entry)
            async with httpx.AsyncClient(timeout=5.0) as _fwd:
                await _fwd.post(
                    f"{settings.ALERTMANAGER_URL}/api/v2/alerts",
                    json=am_payload,
                )
            logger.info(f"Forwarded {len(am_payload)} service alerts to Alertmanager for notifications")
        except Exception as _fwd_err:
            logger.warning(f"Alertmanager forward failed (non-fatal): {_fwd_err}")

    logger.info(f"Webhook received {len(alerts)} alerts, stored {stored} history + {events_stored} events")
    return {"status": "ok", "received": len(alerts), "stored": stored, "events": events_stored}


# ==================================================================
# GET /api/alerts/history — Query alert history from database
# ==================================================================

@router.get("/history")
async def get_alert_history(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by category (e.g. external-services)"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    status: Optional[str] = Query(None, description="Filter by status (firing/resolved)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get alert history from the database, newest first."""
    query = db.query(AlertHistory)

    if category:
        query = query.filter(AlertHistory.category == category)
    if severity:
        query = query.filter(AlertHistory.severity == severity)
    if service_name:
        query = query.filter(AlertHistory.service_name == service_name)
    if status:
        query = query.filter(AlertHistory.status == status)

    total = query.count()
    records = query.order_by(AlertHistory.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "alerts": [
            {
                "id": r.id,
                "fingerprint": r.fingerprint,
                "alertname": r.alertname,
                "status": r.status,
                "severity": r.severity,
                "category": r.category,
                "service_name": r.service_name,
                "summary": r.summary,
                "description": r.description,
                "value": r.value,
                "starts_at": r.starts_at.isoformat() if r.starts_at else None,
                "ends_at": r.ends_at.isoformat() if r.ends_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }