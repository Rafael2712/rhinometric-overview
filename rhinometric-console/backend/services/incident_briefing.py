"""
Incident Briefing Service — Phase 5.1 AI Operations Layer (v2).

Generates a 9-section structured AI Incident Briefing for any incident.

Strategy:
  1. Collects all real platform data (incident, linked alerts, service
     status, recent checks, anomalies, alert history).
  2. If OPENAI_API_KEY is configured: calls GPT-4o-mini via httpx.
  3. If no API key: generates a deterministic rule-based briefing from
     the same context — factual, no invented data.

Output schema (stored as JSON in incidents.ai_briefing):
  {
    "status_snapshot":        str,   # compact one-liner at the top
    "executive_summary":      str,
    "likely_cause":           str,
    "operational_impact":     str,   # separates incident severity from customer impact
    "evidence":               [str],
    "recommended_actions":    [str],
    "related_alerts":         [...],
    "related_anomalies":      [...],
    "confidence_explanation": str,
    "confidence":             "high" | "medium" | "low",
    "generated_at":           ISO timestamp,
    "engine":                 "rule-based" | "openai-gpt4o-mini",
    "model":                  str | None,
  }
"""

import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

import httpx
from sqlalchemy.orm import Session

from config import settings
from models.incident import Incident
from models.alert_event import AlertEvent
from models.external_service import ExternalService
from models.external_service_check import ExternalServiceCheck

logger = logging.getLogger("rhinometric.incident_briefing")


# ── Public entry point ────────────────────────────────────────────────

async def generate_briefing(incident_id: str, db: Session) -> Dict[str, Any]:
    """Generate (or regenerate) a full AI briefing for the given incident."""
    import uuid as _uuid
    try:
        inc_uuid = _uuid.UUID(incident_id)
    except ValueError:
        return _error("Invalid incident ID")

    incident = db.query(Incident).filter(Incident.id == inc_uuid).first()
    if not incident:
        return _error("Incident not found")

    ctx = _collect_context(incident, db)
    key = getattr(settings, "OPENAI_API_KEY", None)

    if key and key.startswith("sk-"):
        try:
            briefing = await _openai_briefing(ctx, key)
        except Exception as exc:
            logger.warning("[briefing] OpenAI call failed (%s), falling back to rule-based", exc)
            briefing = _rule_based_briefing(ctx)
    else:
        briefing = _rule_based_briefing(ctx)

    briefing["generated_at"] = datetime.now(timezone.utc).isoformat()
    return briefing


# ── Context collection ────────────────────────────────────────────────

def _collect_context(incident: Incident, db: Session) -> Dict[str, Any]:
    entity = incident.entity_name
    inc_started = incident.started_at
    if inc_started and inc_started.tzinfo is None:
        inc_started = inc_started.replace(tzinfo=timezone.utc)

    # Linked alert events
    linked_alerts = (
        db.query(AlertEvent)
        .filter(AlertEvent.incident_id == incident.id)
        .order_by(AlertEvent.started_at.desc())
        .limit(20)
        .all()
    )

    # Recent alert history for same entity (last 7 days)
    cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)
    recent_alerts = (
        db.query(AlertEvent)
        .filter(
            AlertEvent.entity_name == entity,
            AlertEvent.started_at >= cutoff_7d,
        )
        .order_by(AlertEvent.started_at.desc())
        .limit(30)
        .all()
    )

    # Service record
    svc = (
        db.query(ExternalService)
        .filter(ExternalService.name == entity)
        .first()
    )

    # Recent service checks (last 50 in 1h window around incident start)
    recent_checks: List[ExternalServiceCheck] = []
    if svc:
        window = inc_started - timedelta(hours=1) if inc_started else datetime.now(timezone.utc) - timedelta(hours=1)
        recent_checks = (
            db.query(ExternalServiceCheck)
            .filter(
                ExternalServiceCheck.service_id == svc.id,
                ExternalServiceCheck.checked_at >= window,
            )
            .order_by(ExternalServiceCheck.checked_at.desc())
            .limit(50)
            .all()
        )

    anomalies = _fetch_anomalies_sync(entity)

    alert_list = [
        {
            "id": str(a.id),
            "alert_name": a.alert_name,
            "status": a.status,
            "severity": a.severity,
            "started_at": a.started_at.isoformat() if a.started_at else None,
            "ended_at": a.ended_at.isoformat() if a.ended_at else None,
            "source": a.source,
            "labels": a.labels or {},
        }
        for a in linked_alerts
    ]

    recent_alert_summary = {
        "total_7d": len(recent_alerts),
        "firing": sum(1 for a in recent_alerts if a.status in ("firing", "escalated")),
        "resolved": sum(1 for a in recent_alerts if a.status == "resolved"),
        "critical": sum(1 for a in recent_alerts if a.severity == "critical"),
        "names": list({a.alert_name for a in recent_alerts if a.alert_name}),
    }

    check_summary = {}
    if recent_checks:
        total = len(recent_checks)
        downs = sum(1 for c in recent_checks if c.status in ("down", "error"))
        lats = [c.response_time_ms for c in recent_checks if c.response_time_ms and c.response_time_ms > 0]
        check_summary = {
            "total": total,
            "down_count": downs,
            "down_pct": round(downs / total * 100, 1),
            "avg_latency_ms": round(sum(lats) / len(lats), 1) if lats else None,
            "last_status": recent_checks[0].status if recent_checks else None,
        }

    return {
        "incident": {
            "id": str(incident.id),
            "entity_name": entity,
            "entity_type": incident.entity_type,
            "severity": incident.severity,
            "status": incident.status,
            "started_at": incident.started_at.isoformat() if incident.started_at else None,
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
            "title": incident.title,
            "summary": incident.summary,
            "tags": incident.tags or [],
        },
        "service": (
            {
                "name": svc.name,
                "type": svc.service_type.value if svc.service_type else "unknown",
                "status": svc.status.value if svc.status else "unknown",
                "environment": svc.environment,
                "enabled": svc.enabled,
            }
            if svc
            else {"name": entity}
        ),
        "linked_alerts": alert_list,
        "recent_alert_history": recent_alert_summary,
        "service_checks": check_summary,
        "anomalies": anomalies,
    }


def _fetch_anomalies_sync(entity_name: str) -> List[Dict]:
    """Best-effort sync fetch of anomalies for the entity from AI service."""
    try:
        url = getattr(settings, "AI_ANOMALY_URL", "http://rhinometric-ai-anomaly:8085")
        r = httpx.get(f"{url}/anomalies?service={entity_name}&time_range=24h&limit=5", timeout=3.0)
        if r.status_code == 200:
            data = r.json()
            groups = data.get("groups", data if isinstance(data, list) else [])
            return [
                {
                    "service": g.get("entity_name", entity_name),
                    "anomaly_score": g.get("anomaly_score"),
                    "severity": g.get("severity"),
                    "timestamp": g.get("first_seen"),
                    "predicted_risk": g.get("predicted_risk_level"),
                }
                for g in (groups[:5] if isinstance(groups, list) else [])
            ]
    except Exception:
        pass
    return []


# ── Duration helper ───────────────────────────────────────────────────

def _duration_str(start_iso: str, end_iso: str) -> str:
    try:
        s = datetime.fromisoformat(start_iso)
        e = datetime.fromisoformat(end_iso)
        secs = int((e - s).total_seconds())
        if secs < 0:
            secs = 0
        if secs < 120:
            return f"{secs}s"
        if secs < 3600:
            return f"{secs // 60}m"
        return f"{secs // 3600}h {(secs % 3600) // 60}m"
    except Exception:
        return "unknown"


# ── Rule-based briefing ───────────────────────────────────────────────

def _rule_based_briefing(ctx: Dict) -> Dict:
    inc = ctx["incident"]
    svc = ctx.get("service", {})
    linked = ctx.get("linked_alerts", [])
    history = ctx.get("recent_alert_history", {})
    checks = ctx.get("service_checks", {})
    anomalies = ctx.get("anomalies", [])

    entity = inc["entity_name"]
    severity = inc["severity"] or "unknown"
    inc_status = inc["status"] or "unknown"
    svc_current_status = (svc.get("status") or "unknown").lower()
    is_production = (svc.get("environment") or "").lower() == "production"
    is_resolved = inc_status == "resolved"

    down_pct = checks.get("down_pct") or 0
    avg_lat = checks.get("avg_latency_ms")
    last_check = (checks.get("last_status") or "unknown").lower()

    # ── § 1  Status Snapshot ──────────────────────────────────────
    parts = []
    if svc_current_status == "up":
        parts.append("Service: HEALTHY")
    elif svc_current_status == "down":
        parts.append("Service: DOWN")
    elif svc_current_status != "unknown":
        parts.append(f"Service: {svc_current_status.upper()}")

    parts.append(f"Incident: {inc_status.upper()}")
    parts.append(f"Severity: {severity.upper()}")

    now_iso = datetime.now(timezone.utc).isoformat()
    if is_resolved and inc.get("resolved_at") and inc.get("started_at"):
        parts.append(f"Duration: {_duration_str(inc['started_at'], inc['resolved_at'])}")
    elif inc.get("started_at"):
        parts.append(f"Open for: {_duration_str(inc['started_at'], now_iso)}")

    if linked:
        parts.append(f"Alerts: {len(linked)}")

    status_snapshot = "  ·  ".join(parts)

    # ── § 2  Executive Summary ────────────────────────────────────
    if is_resolved:
        dur = ""
        if inc.get("resolved_at") and inc.get("started_at"):
            dur = f" It ran for {_duration_str(inc['started_at'], inc['resolved_at'])} before being resolved."
        executive_summary = (
            f"A {severity}-severity incident affecting '{entity}' has been resolved.{dur} "
            f"{len(linked)} alert event(s) were linked during the incident lifecycle."
        )
        if svc_current_status == "up":
            executive_summary += " The service is currently healthy and operational."
    else:
        if svc_current_status == "up" and last_check == "up":
            executive_summary = (
                f"A {severity}-severity incident is open for '{entity}', however the service "
                f"is currently responding as healthy. The triggering condition may have already "
                f"cleared — verify before closing this incident."
            )
        else:
            fail_note = f" Recent checks show a {down_pct}% failure rate." if down_pct else ""
            executive_summary = (
                f"An active {severity}-severity incident is ongoing for service '{entity}'.{fail_note} "
                f"{len(linked)} linked alert(s) require attention."
            )

    # ── § 3  Likely Cause ─────────────────────────────────────────
    alert_names = list({a["alert_name"] for a in linked if a.get("alert_name")})
    if alert_names:
        likely_cause = f"Triggered by alert rule(s): {', '.join(alert_names[:3])}."
        if len(alert_names) > 3:
            likely_cause += f" ({len(alert_names) - 3} additional rule(s) also fired.)"
    else:
        likely_cause = (
            "No alert rules are directly linked to this incident — "
            "it may have been created manually or via an external integration."
        )

    if down_pct >= 80:
        likely_cause += (
            f" Health checks are failing at {down_pct}% — consistent with a full service "
            "outage or unreachable endpoint."
        )
    elif down_pct >= 30:
        likely_cause += (
            f" Partial degradation detected ({down_pct}% check failure rate), "
            "suggesting intermittent connectivity or backend instability."
        )
    elif svc_current_status == "up" and last_check == "up":
        likely_cause += " All current health checks are passing — the service appears to have recovered."
    elif not checks:
        likely_cause += " No health check data is available for this service."

    if avg_lat and avg_lat > 3000:
        likely_cause += (
            f" Elevated response times ({avg_lat}ms average) may indicate "
            "resource exhaustion, slow downstream dependencies, or DNS delays."
        )

    # ── § 4  Operational Impact ───────────────────────────────────
    # Deliberately separate incident severity (classification) from current customer impact (evidence-based)
    if svc_current_status == "up" and last_check == "up":
        cust_level = "LOW"
        cust_note = (
            "The service is currently passing health checks and responding normally. "
            "Customer-facing impact, if any, has likely already resolved."
        )
    elif svc_current_status == "down" or down_pct >= 80:
        cust_level = "HIGH"
        cust_note = (
            "The service is currently unavailable or near-completely failing health checks. "
            "Customer requests to this endpoint are expected to be failing."
        )
    elif down_pct >= 30:
        cust_level = "MEDIUM"
        cust_note = (
            f"{down_pct}% of health checks are failing. "
            "A portion of customer requests may be affected intermittently."
        )
    elif is_resolved:
        cust_level = "NONE"
        cust_note = "The incident has been resolved. No ongoing customer impact is expected."
    else:
        cust_level = "UNDETERMINED"
        cust_note = (
            "Insufficient check data to assess customer-facing impact directly. "
            "Monitor the service closely."
        )

    prod_note = ""
    if is_production and cust_level not in ("NONE", "LOW"):
        prod_note = " This service runs in the PRODUCTION environment — impact is customer-visible."

    operational_impact = (
        f"Incident severity: {severity.upper()}  |  Customer impact: {cust_level}\n"
        f"{cust_note}{prod_note}"
    )

    # ── § 5  Evidence ─────────────────────────────────────────────
    evidence: List[str] = []
    if linked:
        crit_n = sum(1 for a in linked if a.get("severity") == "critical")
        suffix = f" ({crit_n} critical)" if crit_n else ""
        evidence.append(f"{len(linked)} alert event(s) directly linked to this incident{suffix}.")
    if checks.get("total"):
        evidence.append(
            f"{checks['total']} health checks in the incident window: "
            f"{checks.get('down_count', 0)} failed ({down_pct}% failure rate)"
            + (f", avg latency {avg_lat}ms." if avg_lat else ".")
        )
    if history.get("total_7d"):
        evidence.append(
            f"7-day alert history for '{entity}': {history['total_7d']} total, "
            f"{history.get('critical', 0)} critical, {history.get('resolved', 0)} resolved."
        )
    if anomalies:
        evidence.append(
            f"AI anomaly detection flagged {len(anomalies)} anomaly group(s) for this entity "
            "in the past 24 hours."
        )
    if svc.get("type") and svc.get("type") != "unknown":
        evidence.append(
            f"Service type: {svc['type']}, environment: {svc.get('environment', 'unknown')}."
        )
    if not evidence or len(evidence) < 2:
        evidence.append(
            "Evidence is limited — this briefing is based on incident metadata only. "
            "Linking alerts and enabling health checks will improve analysis quality."
        )

    # ── § 6  Recommended Actions ──────────────────────────────────
    actions: List[str] = []

    if svc_current_status == "down" or down_pct >= 80:
        if is_production:
            actions.append(
                f"IMMEDIATE: Escalate to on-call — '{entity}' is down in production. "
                "Notify stakeholders and activate the incident response protocol."
            )
        actions.append(
            f"Open service logs for '{entity}' from {inc.get('started_at', 'incident start')} "
            "and filter for ERROR or FATAL entries."
        )
        actions.append(
            "Verify DNS resolution and network connectivity to the service endpoint. "
            "Check upstream load balancers and proxy configuration."
        )
    elif down_pct >= 30:
        actions.append(
            f"Investigate intermittent failures on '{entity}': check for rate limiting, "
            "connection pool exhaustion, or upstream dependency timeouts."
        )
    elif svc_current_status == "up" and not is_resolved:
        actions.append(
            f"'{entity}' is currently healthy. Confirm the triggering condition is no longer "
            "active and close this incident if conditions remain stable."
        )

    if avg_lat and avg_lat > 2000:
        actions.append(
            f"Response time is elevated ({avg_lat}ms avg). "
            "Profile database queries, check external API dependencies, and review resource utilisation."
        )

    if history.get("critical", 0) >= 3:
        actions.append(
            f"'{entity}' has generated {history['critical']} critical alerts in the past 7 days. "
            "Consider a service reliability review and threshold tuning."
        )

    if anomalies:
        actions.append(
            f"Review {len(anomalies)} AI-flagged anomaly group(s) in the Anomaly Analysis panel "
            "for correlated metric deviations."
        )

    if is_resolved:
        actions.append(
            "Complete a post-incident review: document root cause, timeline, and corrective "
            "actions in the postmortem field."
        )
        actions.append(
            "Confirm monitoring is back to baseline and no residual alerts remain firing."
        )

    if not actions:
        actions.append(
            f"Continue monitoring '{entity}'. If conditions are stable for 30+ minutes, "
            "consider closing this incident."
        )
        actions.append(
            "Review alert rule thresholds to reduce noise and improve signal quality."
        )

    # ── § 7  Related Alerts ───────────────────────────────────────
    related_alerts_list = [
        {
            "alert_name": a["alert_name"],
            "severity": a["severity"],
            "status": a["status"],
            "started_at": a["started_at"],
            "ended_at": a.get("ended_at"),
        }
        for a in linked[:10]
    ]

    # ── § 8  Related Anomalies ────────────────────────────────────
    related_anomalies_list = [
        {
            "service": a.get("service", entity),
            "score": a.get("anomaly_score"),
            "severity": a.get("severity"),
            "predicted_risk": a.get("predicted_risk"),
            "timestamp": a.get("timestamp"),
        }
        for a in anomalies[:5]
    ]

    # ── § 9  Confidence Explanation ───────────────────────────────
    data_points = sum([
        bool(linked),
        checks.get("total", 0) > 0,
        history.get("total_7d", 0) > 0,
        bool(anomalies),
        svc.get("status") not in (None, "unknown"),
    ])

    if data_points >= 4:
        confidence = "high"
        confidence_explanation = (
            f"High — {data_points} of 5 data sources available "
            "(linked alerts, health checks, alert history, anomaly signals, service status)."
        )
    elif data_points >= 2:
        confidence = "medium"
        confidence_explanation = (
            f"Medium — {data_points} of 5 data sources available. "
            f"{5 - data_points} source(s) are missing or returned no data."
        )
    else:
        confidence = "low"
        confidence_explanation = (
            "Low — fewer than 2 data sources are available. "
            "This briefing is based on incident metadata only. "
            "Link alerts and enable health checks to improve analysis quality."
        )

    return {
        "status_snapshot": status_snapshot,
        "executive_summary": executive_summary,
        "likely_cause": likely_cause,
        "operational_impact": operational_impact,
        "evidence": evidence,
        "recommended_actions": actions,
        "related_alerts": related_alerts_list,
        "related_anomalies": related_anomalies_list,
        "confidence_explanation": confidence_explanation,
        "confidence": confidence,
        "engine": "rule-based",
        "model": None,
    }


# ── OpenAI briefing ───────────────────────────────────────────────────

async def _openai_briefing(ctx: Dict, api_key: str) -> Dict:
    """Call OpenAI GPT-4o-mini to generate the briefing."""
    system_prompt = (
        "You are an expert SRE analyst for an AIOps platform called Rhinometric. "
        "Produce a concise, factual operational incident briefing. "
        "RULES: (1) Use ONLY the data provided — never invent facts. "
        "(2) If the service is currently UP, state that impact is likely resolved. "
        "(3) Incident severity is the classification — assess actual customer impact separately. "
        "(4) If evidence is sparse, say 'Evidence is limited'. "
        "(5) Recommendations must be specific, operational, and reference actual service names. "
        "Return JSON with keys: executive_summary, likely_cause, operational_impact, confidence. "
        "confidence must be 'high', 'medium', or 'low'."
    )

    user_prompt = (
        f"Generate an operational incident briefing:\n\n"
        f"{json.dumps(ctx, indent=2, default=str)}"
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
                "max_tokens": 1200,
            },
        )
        resp.raise_for_status()

    ai_json = json.loads(resp.json()["choices"][0]["message"]["content"])
    rule = _rule_based_briefing(ctx)

    return {
        "status_snapshot": rule["status_snapshot"],
        "executive_summary": ai_json.get("executive_summary", rule["executive_summary"]),
        "likely_cause": ai_json.get("likely_cause", rule["likely_cause"]),
        "operational_impact": ai_json.get("operational_impact", rule["operational_impact"]),
        "evidence": rule["evidence"],
        "recommended_actions": rule["recommended_actions"],
        "related_alerts": rule["related_alerts"],
        "related_anomalies": rule["related_anomalies"],
        "confidence_explanation": rule["confidence_explanation"],
        "confidence": ai_json.get("confidence", rule["confidence"]),
        "engine": "openai-gpt4o-mini",
        "model": "gpt-4o-mini",
    }


# ── Helpers ───────────────────────────────────────────────────────────

def _error(msg: str) -> Dict:
    return {
        "error": msg,
        "engine": None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
