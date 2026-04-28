from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from models.alert_event import AlertEvent
from models.alert_history import AlertHistory
from models.incident import Incident
from services.service_summary_service import get_services_summary


SUPPORTED_RANGES = {"24h", "7d", "30d"}

# ─── Noise / test-entity filter ────────────────────────────────────────────────
_TEST_PREFIXES = ("E2E_", "VALID_", "TEST_", "DEBUG_", "e2e_", "valid_", "test_", "debug_")


def _is_test_entity(name: str | None) -> bool:
    if not name:
        return False
    return name.startswith(_TEST_PREFIXES)


def _clean_incidents(incidents: List[Incident]) -> List[Incident]:
    return [i for i in incidents if not _is_test_entity(i.entity_name)]


def _clean_alerts(alerts: List[AlertEvent]) -> List[AlertEvent]:
    return [a for a in alerts if not _is_test_entity(a.entity_name)]


# ─── Time helpers ───────────────────────────────────────────────────────────────

def _parse_time_range(time_range: str) -> datetime:
    now = datetime.now(timezone.utc)
    if time_range == "24h":
        return now - timedelta(hours=24)
    if time_range == "7d":
        return now - timedelta(days=7)
    if time_range == "30d":
        return now - timedelta(days=30)
    raise ValueError("Unsupported range. Use 24h, 7d or 30d")


def _to_iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _duration_seconds(started_at: datetime | None, resolved_at: datetime | None) -> int | None:
    if not started_at:
        return None
    end = resolved_at or datetime.now(timezone.utc)
    return max(0, int((end - started_at).total_seconds()))


def _duration_text(seconds: int | None) -> str:
    if seconds is None:
        return "-"
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m"


def _status_from_summary(overall_status: str) -> str:
    v = (overall_status or "").upper()
    if v in {"DOWN", "CRITICAL"}:
        return "Critical"
    if v in {"DEGRADED"}:
        return "Degraded"
    return "Operational"


def _incident_impact(incident: Incident) -> str:
    sev = (incident.severity or "warning").lower()
    if sev == "critical":
        return "High impact"
    if sev == "warning":
        return "Medium impact"
    return "Low impact"


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


# ─── EXECUTIVE REPORT ──────────────────────────────────────────────────────────

async def generate_executive_report(db: Session, time_range: str) -> Dict[str, Any]:
    since = _parse_time_range(time_range)
    now = datetime.now(timezone.utc)

    raw_incidents = (
        db.query(Incident)
        .filter(Incident.started_at >= since)
        .order_by(Incident.started_at.desc())
        .all()
    )
    raw_alerts = (
        db.query(AlertEvent)
        .filter(AlertEvent.started_at >= since)
        .order_by(AlertEvent.started_at.desc())
        .all()
    )

    # Sanitize test data
    incidents = _clean_incidents(raw_incidents)
    alerts = _clean_alerts(raw_alerts)

    alert_history_count = db.query(AlertHistory).filter(AlertHistory.created_at >= since).count()

    # MTTR
    resolved_incidents = [i for i in incidents if i.resolved_at and i.started_at]
    mttr_seconds = (
        int(
            sum((i.resolved_at - i.started_at).total_seconds() for i in resolved_incidents)
            / len(resolved_incidents)
        )
        if resolved_incidents
        else 0
    )
    mttr_human = _duration_text(mttr_seconds)

    # Uptime
    active_alerts = [a for a in alerts if a.status not in ("resolved", "dismissed")]
    uptime = 100.0
    if alerts:
        uptime = round(max(0.0, 100.0 - ((len(active_alerts) / max(1, len(alerts))) * 100.0)), 2)

    services_summary = await get_services_summary(db)
    status = _status_from_summary(str(services_summary.get("overall_status", "OPERATIONAL")))

    # Top incidents (max 5, critical first)
    top_source = sorted(
        incidents,
        key=lambda i: (
            0 if (i.severity or "").lower() == "critical" else 1,
            -(_duration_seconds(i.started_at, i.resolved_at) or 0),
        ),
    )[:5]

    top_incidents = [
        {
            "service": i.entity_name,
            "severity": (i.severity or "warning").capitalize(),
            "impact": _incident_impact(i),
            "duration": _duration_text(_duration_seconds(i.started_at, i.resolved_at)),
            "summary": (
                (i.ai_briefing or {}).get("executive_summary")
                if isinstance(i.ai_briefing, dict)
                else None
            )
            or i.summary
            or "Service disruption recorded.",
        }
        for i in top_source
    ]

    # Risks (max 3, meaningful)
    risks: List[str] = []
    critical_svcs = list({i.entity_name for i in incidents if (i.severity or "").lower() == "critical" and i.entity_name})
    if critical_svcs:
        names = ", ".join(critical_svcs[:3])
        risks.append(f"Critical incidents recorded for: {names}.")
    still_firing = [a for a in alerts if (a.severity or "").lower() == "critical" and a.status == "firing"]
    if still_firing:
        firing_svcs = list({a.entity_name for a in still_firing if a.entity_name})[:3]
        risks.append(f"Active critical alerts still firing: {', '.join(firing_svcs)}.")
    if len(incidents) > 10:
        risks.append(f"High incident volume detected ({len(incidents)} incidents in {time_range}).")
    if not risks:
        risks.append("No significant operational risk identified in this period.")
    risks = risks[:3]

    # Recommendations (max 5, specific)
    recommendations: List[str] = []
    for i in incidents:
        if isinstance(i.ai_briefing, dict):
            recommendations.extend(
                [str(x) for x in _safe_list(i.ai_briefing.get("recommended_actions")) if str(x).strip()]
            )
    if not recommendations:
        if mttr_seconds > 1800:
            recommendations.append(f"MTTR is elevated ({mttr_human}). Review escalation and runbook procedures.")
        if still_firing:
            recommendations.append("Investigate and resolve currently firing critical alerts.")
        if critical_svcs:
            recommendations.append(f"Prioritize stability review for: {', '.join(critical_svcs[:3])}.")
        recommendations.append("Maintain monitoring coverage on all critical service endpoints.")
        recommendations.append("Review alert rules for false positive reduction opportunities.")
    recommendations = recommendations[:5]

    # Executive summary (3–5 clean lines)
    if incidents:
        crit_count = sum(1 for i in incidents if (i.severity or "").lower() == "critical")
        summary_parts = [
            f"In the past {time_range}, {len(incidents)} incident(s) were recorded across monitored services."
        ]
        if crit_count:
            summary_parts.append(f"{crit_count} of these were critical severity.")
        if resolved_incidents:
            summary_parts.append(f"Average resolution time (MTTR): {mttr_human}.")
        summary_parts.append(f"Platform status is currently {status}. Uptime: {uptime}%.")
        summary = " ".join(summary_parts)
    else:
        summary = f"No significant incidents were recorded in the past {time_range}. Platform is {status} with {uptime}% uptime."

    return {
        "status": status,
        "summary": summary,
        "kpis": {
            "total_incidents": len(incidents),
            "mttr": mttr_seconds,
            "mttr_human": mttr_human,
            "uptime": uptime,
            "total_alerts": len(alerts),
        },
        "top_incidents": top_incidents,
        "risks": risks,
        "recommendations": recommendations,
        "generated_at": now.isoformat(),
        "time_range": time_range,
        "engine": "rule-based",
    }


# ─── TECHNICAL REPORT ──────────────────────────────────────────────────────────

def _serialize_incident(i: Incident) -> Dict[str, Any]:
    return {
        "id": str(i.id),
        "entity_name": i.entity_name,
        "severity": i.severity,
        "status": i.status,
        "started_at": _to_iso(i.started_at),
        "resolved_at": _to_iso(i.resolved_at),
        "duration": _duration_text(_duration_seconds(i.started_at, i.resolved_at)),
        "summary": i.summary,
    }


def _serialize_alert(a: AlertEvent) -> Dict[str, Any]:
    return {
        "id": str(a.id),
        "alert_name": a.alert_name,
        "entity_name": a.entity_name,
        "severity": a.severity,
        "status": a.status,
        "started_at": _to_iso(a.started_at),
        "ended_at": _to_iso(a.ended_at),
    }


def _group_alerts_by_service(alerts: List[AlertEvent]) -> List[Dict[str, Any]]:
    """Collapse alerts to one entry per (entity_name, alert_name) pair."""
    seen: Dict[str, Dict[str, Any]] = {}
    for a in alerts:
        key = f"{a.entity_name or ''}|{a.alert_name or ''}"
        if key not in seen:
            seen[key] = {
                "entity_name": a.entity_name,
                "alert_name": a.alert_name,
                "severity": a.severity,
                "count": 1,
                "last_status": a.status,
                "last_seen": _to_iso(a.started_at),
            }
        else:
            seen[key]["count"] += 1
    return list(seen.values())


async def generate_technical_report(db: Session, time_range: str) -> Dict[str, Any]:
    since = _parse_time_range(time_range)
    now = datetime.now(timezone.utc)

    raw_incidents = (
        db.query(Incident)
        .filter(Incident.started_at >= since)
        .order_by(Incident.started_at.desc())
        .all()
    )
    raw_alerts = (
        db.query(AlertEvent)
        .filter(AlertEvent.started_at >= since)
        .order_by(AlertEvent.started_at.desc())
        .all()
    )
    history = (
        db.query(AlertHistory)
        .filter(AlertHistory.created_at >= since)
        .order_by(AlertHistory.created_at.desc())
        .limit(200)
        .all()
    )

    # Sanitize
    incidents = _clean_incidents(raw_incidents)[:50]
    alerts = _clean_alerts(raw_alerts)

    # Alert volume control
    total_alert_count = len(alerts)
    alert_volume_note: str | None = None
    if total_alert_count > 1000:
        alert_volume_note = f"High alert volume detected ({total_alert_count} alerts in {time_range}). Showing grouped summary."
        alerts_grouped = _group_alerts_by_service(alerts)[:50]
        alerts_serialized = alerts_grouped  # already dicts
    else:
        alerts_grouped = _group_alerts_by_service(alerts)
        alerts_serialized = alerts_grouped[:50]

    # Anomalies
    anomalies: List[Dict[str, Any]] = []
    try:
        from routers.anomalies import _fetch_and_normalize, _build_anomaly_groups  # type: ignore

        normalized = await _fetch_and_normalize(time_range, 300)
        groups = _build_anomaly_groups(normalized)
        anomalies = [
            {
                "entity_name": g.get("entity_name"),
                "metric_name": g.get("metric_name"),
                "severity": g.get("severity_current"),
                "status": g.get("status"),
                "last_seen": g.get("last_seen"),
                "occurrence_count": g.get("occurrence_count"),
            }
            for g in groups[:50]
            if not _is_test_entity(g.get("entity_name"))
        ]
    except Exception:
        anomalies = []

    # Timeline (top events only from incidents, not raw history spam)
    timeline: List[Dict[str, Any]] = []
    for i in incidents[:50]:
        timeline.append({
            "timestamp": _to_iso(i.started_at),
            "type": "incident_started",
            "entity": i.entity_name,
            "severity": i.severity,
            "status": i.status,
        })
        if i.resolved_at:
            timeline.append({
                "timestamp": _to_iso(i.resolved_at),
                "type": "incident_resolved",
                "entity": i.entity_name,
                "severity": i.severity,
                "status": "resolved",
            })
    # Add only critical/escalated history events (avoid noise)
    for h in history[:100]:
        if (h.status or "") in ("firing", "escalated", "resolved") and not _is_test_entity(h.service_name or h.alertname):
            timeline.append({
                "timestamp": _to_iso(h.created_at),
                "type": f"alert_{h.status}",
                "entity": h.service_name or h.alertname,
                "severity": h.severity,
                "status": h.status,
            })
    timeline.sort(key=lambda x: x.get("timestamp") or "", reverse=True)

    return {
        "incidents": [_serialize_incident(i) for i in incidents],
        "alerts": alerts_serialized,
        "alert_volume_note": alert_volume_note,
        "total_alert_count": total_alert_count,
        "anomalies": anomalies,
        "timeline": timeline[:100],
        "generated_at": now.isoformat(),
        "time_range": time_range,
    }
