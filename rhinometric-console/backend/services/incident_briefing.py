"""
Incident Briefing Service — Phase 5.1 AI Operations Layer.

Generates a structured 10-point AI Incident Briefing for any incident.

Strategy:
  1. Collects all real platform data (incident, linked alerts, service
     status, recent checks, anomalies, alert history).
  2. If OPENAI_API_KEY is configured: calls GPT-4o-mini via httpx for
     a narrative analysis using the collected context.
  3. If no API key: generates a deterministic rule-based briefing from
     the same context — factual, no invented data.

Output schema (stored as JSON in incidents.ai_briefing):
  {
    "executive_summary": str,
    "probable_cause": str,
    "affected_service": str,
    "related_alerts": [...],
    "related_anomalies": [...],
    "evidence": [...],
    "impact_assessment": str,
    "recommended_actions": [...],
    "confidence": "high" | "medium" | "low",
    "generated_at": ISO timestamp,
    "engine": "openai-gpt4o-mini" | "rule-based",
    "model": str | None,
  }
"""

import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

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

    # Recent service checks (last 50)
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

    # Anomalies: try fetching from AI service
    anomalies = _fetch_anomalies_sync(entity)

    # Build serialisable context
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
        "service": {
            "name": svc.name if svc else entity,
            "type": svc.service_type.value if svc and svc.service_type else "unknown",
            "status": svc.status.value if svc and svc.status else "unknown",
            "environment": svc.environment if svc else None,
            "enabled": svc.enabled if svc else None,
        } if svc else {"name": entity},
        "linked_alerts": alert_list,
        "recent_alert_history": recent_alert_summary,
        "service_checks": check_summary,
        "anomalies": anomalies,
    }


def _fetch_anomalies_sync(entity_name: str) -> List[Dict]:
    """Best-effort sync fetch of anomalies for the entity from AI service."""
    try:
        import httpx as _httpx
        url = getattr(settings, "AI_ANOMALY_URL", "http://rhinometric-ai-anomaly:8085")
        r = _httpx.get(f"{url}/anomalies?service={entity_name}&time_range=24h&limit=5", timeout=3.0)
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


# ── Rule-based briefing ───────────────────────────────────────────────

def _rule_based_briefing(ctx: Dict) -> Dict:
    inc = ctx["incident"]
    svc = ctx.get("service", {})
    linked = ctx.get("linked_alerts", [])
    history = ctx.get("recent_alert_history", {})
    checks = ctx.get("service_checks", {})
    anomalies = ctx.get("anomalies", [])

    entity = inc["entity_name"]
    severity = inc["severity"]
    status = inc["status"]
    started_at = inc["started_at"]

    # ── 1. Executive summary ──────────────────────────────────────
    if status == "resolved":
        duration_note = ""
        if inc.get("resolved_at") and inc.get("started_at"):
            try:
                s = datetime.fromisoformat(inc["started_at"])
                e = datetime.fromisoformat(inc["resolved_at"])
                secs = int((e - s).total_seconds())
                if secs < 120:
                    duration_note = f" The incident lasted {secs} seconds."
                elif secs < 3600:
                    duration_note = f" The incident lasted {secs // 60} minutes."
                else:
                    duration_note = f" The incident lasted {secs // 3600}h {(secs % 3600) // 60}m."
            except Exception:
                pass
        executive_summary = (
            f"A {severity}-severity incident affecting '{entity}' has been resolved.{duration_note} "
            f"The incident was linked to {len(linked)} alert event(s) and is now closed."
        )
    else:
        checks_note = ""
        if checks.get("down_pct") is not None:
            checks_note = f" Recent checks show {checks['down_pct']}% failure rate."
        executive_summary = (
            f"An active {severity}-severity incident is ongoing for service '{entity}'.{checks_note} "
            f"Started at {started_at}. Currently {len(linked)} alert(s) are linked."
        )

    # ── 2. Probable cause ─────────────────────────────────────────
    alert_names = list({a["alert_name"] for a in linked if a.get("alert_name")})
    if alert_names:
        probable_cause = (
            f"The incident was triggered by the following alert rule(s): {', '.join(alert_names[:3])}. "
        )
    else:
        probable_cause = "No linked alerts found — incident may have been created manually. "

    if checks.get("down_pct", 0) >= 50:
        probable_cause += (
            f"Service health checks are failing at {checks['down_pct']}%, indicating a likely "
            f"service outage or connectivity issue."
        )
    elif checks.get("down_pct", 0) > 0:
        probable_cause += (
            f"Intermittent failures detected ({checks['down_pct']}% of recent checks are down), "
            f"suggesting instability rather than a full outage."
        )
    elif checks.get("last_status") == "up":
        probable_cause += "Service checks are currently returning UP — the trigger condition may have already cleared."
    else:
        probable_cause += "Insufficient check history to determine root cause from synthetic monitoring alone."

    # ── 3. Affected service ───────────────────────────────────────
    svc_env = f" ({svc.get('environment', 'unknown')} environment)" if svc.get("environment") else ""
    affected_service = (
        f"{entity}{svc_env} — type: {svc.get('type', 'unknown')}, "
        f"current status: {svc.get('status', 'unknown')}."
    )

    # ── 4. Related alerts ─────────────────────────────────────────
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

    # ── 5. Related anomalies ──────────────────────────────────────
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

    # ── 6. Evidence ───────────────────────────────────────────────
    evidence = []
    if linked:
        evidence.append(f"{len(linked)} alert event(s) linked directly to this incident.")
    if checks.get("total"):
        evidence.append(
            f"{checks['total']} service checks in the observed window: "
            f"{checks.get('down_count', 0)} failures, avg latency "
            f"{checks.get('avg_latency_ms', 'N/A')}ms."
        )
    if history.get("total_7d"):
        evidence.append(
            f"Alert history (7d): {history['total_7d']} alerts total, "
            f"{history.get('critical', 0)} critical, {history.get('resolved', 0)} resolved."
        )
    if anomalies:
        evidence.append(f"AI anomaly detection found {len(anomalies)} anomaly group(s) for this entity.")
    if not evidence:
        evidence.append("Insufficient data available to build a comprehensive evidence list.")

    # ── 7. Impact assessment ──────────────────────────────────────
    if severity == "critical":
        impact = (
            f"CRITICAL impact — service '{entity}' is experiencing a critical failure. "
            "This can directly affect end users or downstream services depending on this entity."
        )
    elif severity == "warning":
        impact = (
            f"Degraded service — '{entity}' is experiencing elevated error rates or latency. "
            "End users may encounter intermittent failures."
        )
    else:
        impact = (
            f"Low severity impact on '{entity}'. Monitoring is advisable to ensure the situation "
            "does not escalate."
        )
    if svc.get("environment") == "production":
        impact += " Note: This is a PRODUCTION environment — customer impact is possible."

    # ── 8. Recommended actions ────────────────────────────────────
    actions = []
    if checks.get("down_pct", 0) >= 50:
        actions.append("Immediately check service health via logs and infrastructure metrics.")
        actions.append("Verify network connectivity and DNS resolution for the affected endpoint.")
    if checks.get("avg_latency_ms") and checks["avg_latency_ms"] > 2000:
        actions.append(f"Investigate high latency ({checks['avg_latency_ms']}ms avg) — check DB connections, external dependencies, and resource usage.")
    if history.get("critical", 0) > 3:
        actions.append(f"Review recurring critical alerts ({history['critical']} in 7 days) — this may indicate a systemic issue.")
    if anomalies:
        actions.append("Review AI anomaly signals for correlated metric deviations.")
    if status == "resolved":
        actions.append("Conduct a post-incident review and document in the postmortem field.")
        actions.append("Verify the fix is stable and monitoring is back to baseline.")
    if not actions:
        actions.append("Continue monitoring and close the incident if conditions remain stable.")
        actions.append("If the situation recurs, review alert rule thresholds.")

    # ── 9. Confidence ─────────────────────────────────────────────
    data_points = sum([
        bool(linked),
        bool(checks.get("total")),
        bool(history.get("total_7d")),
        bool(anomalies),
        bool(svc.get("status")),
    ])
    if data_points >= 4:
        confidence = "high"
    elif data_points >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "executive_summary": executive_summary,
        "probable_cause": probable_cause,
        "affected_service": affected_service,
        "related_alerts": related_alerts_list,
        "related_anomalies": related_anomalies_list,
        "evidence": evidence,
        "impact_assessment": impact,
        "recommended_actions": actions,
        "confidence": confidence,
        "engine": "rule-based",
        "model": None,
    }


# ── OpenAI briefing ───────────────────────────────────────────────────

async def _openai_briefing(ctx: Dict, api_key: str) -> Dict:
    """Call OpenAI GPT-4o-mini to generate the briefing."""
    inc = ctx["incident"]
    entity = inc["entity_name"]

    system_prompt = (
        "You are an expert SRE analyst for an AIOps platform called Rhinometric. "
        "Your job is to produce a concise, factual incident briefing. "
        "Use ONLY the data provided. Do not invent facts. If data is missing, say so. "
        "Return a JSON object with these exact keys: "
        "executive_summary, probable_cause, affected_service, impact_assessment, confidence. "
        "confidence must be 'high', 'medium', or 'low' based on available evidence."
    )

    user_prompt = (
        f"Generate an incident briefing for this incident:\n\n"
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
                "max_tokens": 1000,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    ai_text = data["choices"][0]["message"]["content"]
    ai_json = json.loads(ai_text)

    # Merge: LLM provides narrative fields; rule-based fills the structured data
    rule = _rule_based_briefing(ctx)
    return {
        "executive_summary": ai_json.get("executive_summary", rule["executive_summary"]),
        "probable_cause": ai_json.get("probable_cause", rule["probable_cause"]),
        "affected_service": ai_json.get("affected_service", rule["affected_service"]),
        "related_alerts": rule["related_alerts"],
        "related_anomalies": rule["related_anomalies"],
        "evidence": rule["evidence"],
        "impact_assessment": ai_json.get("impact_assessment", rule["impact_assessment"]),
        "recommended_actions": rule["recommended_actions"],
        "confidence": ai_json.get("confidence", rule["confidence"]),
        "engine": "openai-gpt4o-mini",
        "model": "gpt-4o-mini",
    }


# ── Helpers ───────────────────────────────────────────────────────────

def _error(msg: str) -> Dict:
    return {"error": msg, "engine": None, "generated_at": datetime.now(timezone.utc).isoformat()}
