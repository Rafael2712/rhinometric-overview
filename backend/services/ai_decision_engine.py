"""
AI Decision Engine — Phase 5.2 Operational Triage Layer.

Evaluates alerts, anomalies, and incidents and produces a structured
operational recommendation (ignore / monitor / notify / escalate).

Strategy:
  1. Collect real platform data — no invented facts.
  2. Run deterministic rule-based decision first.
  3. If OPENAI_API_KEY is configured, enhance with GPT-4o-mini.
  4. Validate LLM output shape — fall back to rule-based on failure.

Output schema (stored in *.ai_decision JSONB):
  {
    "decision":          "ignore" | "monitor" | "notify" | "escalate",
    "confidence":        "low" | "medium" | "high",
    "risk_level":        "low" | "medium" | "high" | "critical",
    "summary":           str,
    "reason":            str,
    "evidence":          [str],
    "recommended_actions": [str],
    "noise_assessment": {
      "is_likely_noise":      bool,
      "noise_reason":         str,
      "recurrence_detected":  bool,
    },
    "customer_impact":   "none" | "low" | "medium" | "high",
    "created_at":        ISO timestamp,
    "engine":            "rule-based" | "llm",
    "model":             str | None,
  }

SAFETY CONTRACT:
  - The AI may NOT delete, close, suppress, or notify autonomously.
  - Decisions are advisory only — store and display for operators.
  - The existing alert/incident lifecycle is never modified here.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from config import settings

logger = logging.getLogger("rhinometric.ai_decision_engine")

# ── Constants ────────────────────────────────────────────────────────

_SEV_RANK = {"info": 0, "warning": 1, "critical": 2}
_RECENT_WINDOW = timedelta(hours=6)
_RECURRENCE_THRESHOLD = 3  # occurrences within window = recurrence


# ════════════════════════════════════════════════════════════════════
# 1.  CONTEXT BUILDERS
# ════════════════════════════════════════════════════════════════════

def build_alert_context(alert_event, db: Session) -> Dict[str, Any]:
    """
    Gather all real platform data for an alert event.
    Never invents or interpolates facts.
    """
    from models.alert_event import AlertEvent
    from models.external_service import ExternalService
    from models.external_service_check import ExternalServiceCheck

    now = datetime.now(timezone.utc)
    ctx: Dict[str, Any] = {}

    # ── Core alert fields ────────────────────────────────────────
    ctx["alert_id"]     = str(alert_event.id)
    ctx["alert_name"]   = alert_event.alert_name or ""
    ctx["entity_name"]  = alert_event.entity_name or ""
    ctx["entity_type"]  = alert_event.entity_type or ""
    ctx["severity"]     = alert_event.severity or "warning"
    ctx["status"]       = alert_event.status or "firing"
    ctx["source"]       = alert_event.source or ""
    ctx["started_at"]   = alert_event.started_at.isoformat() if alert_event.started_at else None
    ctx["incident_id"]  = str(alert_event.incident_id) if alert_event.incident_id else None
    ctx["escalation_count"] = alert_event.escalation_count or 0
    ctx["summary"]      = alert_event.summary or ""

    # ── Duration ────────────────────────────────────────────────
    if alert_event.started_at:
        started = alert_event.started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        ctx["duration_minutes"] = round((now - started).total_seconds() / 60, 1)
    else:
        ctx["duration_minutes"] = 0

    # ── Current service status ───────────────────────────────────
    svc = db.query(ExternalService).filter(
        ExternalService.name == alert_event.entity_name
    ).first()

    if svc:
        ctx["service_current_status"] = svc.status.lower() if svc.status else "unknown"
        ctx["service_enabled"]        = svc.enabled
        ctx["service_type"]           = svc.service_type
    else:
        ctx["service_current_status"] = "unknown"
        ctx["service_enabled"]        = None
        ctx["service_type"]           = None

    # ── Recent service checks (last 10) ──────────────────────────
    if svc:
        recent_checks = (
            db.query(ExternalServiceCheck)
            .filter(ExternalServiceCheck.service_id == svc.id)
            .order_by(ExternalServiceCheck.checked_at.desc())
            .limit(10)
            .all()
        )
        ctx["recent_check_statuses"] = [c.status for c in recent_checks]
        ctx["recent_down_count"]     = sum(1 for c in recent_checks if c.status == "down")
        ctx["recent_check_count"]    = len(recent_checks)
    else:
        ctx["recent_check_statuses"] = []
        ctx["recent_down_count"]     = 0
        ctx["recent_check_count"]    = 0

    # ── Recurrence — same entity recent firing events ────────────
    cutoff = now - _RECENT_WINDOW
    recent_events = (
        db.query(AlertEvent)
        .filter(
            AlertEvent.entity_name == alert_event.entity_name,
            AlertEvent.started_at >= cutoff,
        )
        .all()
    )
    ctx["recent_event_count"] = len(recent_events)
    ctx["recurrence_detected"] = len(recent_events) >= _RECURRENCE_THRESHOLD

    # ── Anomaly correlation ───────────────────────────────────────
    try:
        from sqlalchemy import text as _text
        anomaly_row = db.execute(
            _text("""
                SELECT anomaly_score, severity, confidence_label, primary_category,
                       predicted_risk_level, status, last_seen_at
                FROM anomaly_engine_results_v1
                WHERE service_name = :name AND status = 'active'
                ORDER BY last_seen_at DESC
                LIMIT 1
            """),
            {"name": alert_event.entity_name},
        ).fetchone()
        if anomaly_row:
            ctx["correlated_anomaly"] = {
                "score": anomaly_row[0],
                "severity": anomaly_row[1],
                "confidence": anomaly_row[2],
                "category": anomaly_row[3],
                "predicted_risk": anomaly_row[4],
            }
        else:
            ctx["correlated_anomaly"] = None
    except Exception:
        ctx["correlated_anomaly"] = None

    return ctx


def build_anomaly_context(anomaly_row, db: Session) -> Dict[str, Any]:
    """
    Gather context for an anomaly_engine_results_v1 record.
    """
    from models.alert_event import AlertEvent
    from models.external_service import ExternalService
    from models.external_service_check import ExternalServiceCheck

    now = datetime.now(timezone.utc)
    ctx: Dict[str, Any] = {}

    ctx["anomaly_id"]       = str(anomaly_row.id)
    ctx["service_name"]     = anomaly_row.service_name or ""
    ctx["anomaly_score"]    = anomaly_row.anomaly_score
    ctx["severity"]         = anomaly_row.severity or "low"
    ctx["confidence"]       = anomaly_row.confidence_label or "low"
    ctx["primary_category"] = anomaly_row.primary_category or ""
    ctx["status"]           = anomaly_row.status or "active"
    ctx["occurrence_count"] = anomaly_row.occurrence_count or 1
    ctx["evidence_summary"] = anomaly_row.evidence_summary or ""
    ctx["predicted_risk"]   = anomaly_row.predicted_risk_level or "none"
    ctx["last_seen_at"]     = anomaly_row.last_seen_at.isoformat() if anomaly_row.last_seen_at else None

    # Duration since first seen
    if anomaly_row.first_seen_at:
        fs = anomaly_row.first_seen_at
        if fs.tzinfo is None:
            fs = fs.replace(tzinfo=timezone.utc)
        ctx["duration_minutes"] = round((now - fs).total_seconds() / 60, 1)
    else:
        ctx["duration_minutes"] = 0

    # Current service status
    svc = db.query(ExternalService).filter(
        ExternalService.name == anomaly_row.service_name
    ).first()
    ctx["service_current_status"] = svc.status.lower() if svc and svc.status else "unknown"

    # Correlated active alert
    cutoff = now - _RECENT_WINDOW
    active_alert = (
        db.query(AlertEvent)
        .filter(
            AlertEvent.entity_name == anomaly_row.service_name,
            AlertEvent.status.in_(["firing", "escalated", "acknowledged"]),
        )
        .first()
    )
    if active_alert:
        ctx["correlated_alert"] = {
            "id": str(active_alert.id),
            "severity": active_alert.severity,
            "status": active_alert.status,
            "alert_name": active_alert.alert_name,
            "incident_id": str(active_alert.incident_id) if active_alert.incident_id else None,
        }
    else:
        ctx["correlated_alert"] = None

    return ctx


def build_incident_context(incident, db: Session) -> Dict[str, Any]:
    """
    Gather operational context for an incident.
    """
    from models.alert_event import AlertEvent
    from models.external_service import ExternalService
    from models.external_service_check import ExternalServiceCheck

    now = datetime.now(timezone.utc)
    ctx: Dict[str, Any] = {}

    ctx["incident_id"]   = str(incident.id)
    ctx["entity_name"]   = incident.entity_name or ""
    ctx["severity"]      = incident.severity or "warning"
    ctx["status"]        = incident.status or "open"
    ctx["started_at"]    = incident.started_at.isoformat() if incident.started_at else None

    if incident.started_at:
        st = incident.started_at
        if st.tzinfo is None:
            st = st.replace(tzinfo=timezone.utc)
        ctx["duration_minutes"] = round((now - st).total_seconds() / 60, 1)
    else:
        ctx["duration_minutes"] = 0

    # Linked alerts
    linked_alerts = (
        db.query(AlertEvent)
        .filter(AlertEvent.incident_id == incident.id)
        .all()
    )
    ctx["linked_alert_count"] = len(linked_alerts)
    ctx["linked_alert_severities"] = list({a.severity for a in linked_alerts})

    # Current service status
    svc = db.query(ExternalService).filter(
        ExternalService.name == incident.entity_name
    ).first()
    ctx["service_current_status"] = svc.status.lower() if svc and svc.status else "unknown"

    # Recent checks
    if svc:
        recent_checks = (
            db.query(ExternalServiceCheck)
            .filter(ExternalServiceCheck.service_id == svc.id)
            .order_by(ExternalServiceCheck.checked_at.desc())
            .limit(10)
            .all()
        )
        ctx["recent_down_count"] = sum(1 for c in recent_checks if c.status == "down")
        ctx["recent_check_count"] = len(recent_checks)
    else:
        ctx["recent_down_count"] = 0
        ctx["recent_check_count"] = 0

    # Correlated anomalies
    try:
        from sqlalchemy import text as _text
        anomaly_row = db.execute(
            _text("""
                SELECT anomaly_score, severity, primary_category, predicted_risk_level
                FROM anomaly_engine_results_v1
                WHERE service_name = :name AND status = 'active'
                ORDER BY last_seen_at DESC LIMIT 1
            """),
            {"name": incident.entity_name},
        ).fetchone()
        ctx["correlated_anomaly"] = {
            "score": anomaly_row[0],
            "severity": anomaly_row[1],
            "category": anomaly_row[2],
            "predicted_risk": anomaly_row[3],
        } if anomaly_row else None
    except Exception:
        ctx["correlated_anomaly"] = None

    # Existing AI briefing indicator
    ctx["has_ai_briefing"] = incident.ai_briefing is not None

    return ctx


# ════════════════════════════════════════════════════════════════════
# 2.  RULE-BASED DECISION ENGINE
# ════════════════════════════════════════════════════════════════════

def _evidence_limited(ctx: Dict) -> bool:
    """Return True if the context has very little data to reason from."""
    checks   = ctx.get("recent_check_count", 0)
    has_svc  = ctx.get("service_current_status", "unknown") != "unknown"
    has_anom = ctx.get("correlated_anomaly") is not None or ctx.get("correlated_alert") is not None
    return not has_svc and checks == 0 and not has_anom


def rule_based_decision_for_alert(ctx: Dict) -> Dict[str, Any]:
    """
    Deterministic rule-based triage for alert events.
    Returns a full decision object.
    """
    severity        = ctx.get("severity", "warning")
    svc_status      = ctx.get("service_current_status", "unknown")
    status          = ctx.get("status", "firing")
    recurrence      = ctx.get("recurrence_detected", False)
    recent_events   = ctx.get("recent_event_count", 0)
    down_count      = ctx.get("recent_down_count", 0)
    check_count     = ctx.get("recent_check_count", 0)
    sev_rank        = _SEV_RANK.get(severity, 1)
    anomaly         = ctx.get("correlated_anomaly")
    incident_id     = ctx.get("incident_id")
    duration_min    = ctx.get("duration_minutes", 0)
    entity          = ctx.get("entity_name", "service")
    alert_name      = ctx.get("alert_name", "")

    evidence: List[str]  = []
    actions:  List[str]  = []

    # Collect evidence
    if svc_status != "unknown":
        evidence.append(f"Service '{entity}' current status: {svc_status.upper()}")
    if check_count > 0:
        evidence.append(f"Recent checks: {down_count}/{check_count} failed")
    if recurrence:
        evidence.append(f"Seen {recent_events} alerts for this service in the last 6 hours")
    if anomaly:
        evidence.append(
            f"Active anomaly detected — score {anomaly['score']}, "
            f"severity {anomaly['severity']}, category {anomaly.get('category', 'unknown')}"
        )
    if incident_id:
        evidence.append(f"Alert is linked to incident {incident_id}")
    if duration_min > 0:
        evidence.append(f"Alert has been active for {duration_min:.0f} minute(s)")
    if not evidence:
        evidence.append("Evidence is limited — insufficient telemetry to fully assess")

    # ── Rule 1: Already escalated to incident ────────────────────
    if status == "escalated" or incident_id:
        actions.append(f"Review incident linked to alert for {entity}")
        actions.append("Verify root cause before resolving the incident")
        return _make_decision(
            decision="escalate",
            confidence="high" if sev_rank >= 2 else "medium",
            risk_level="critical" if sev_rank >= 2 else "high",
            summary=f"Alert for '{entity}' has been escalated to an active incident.",
            reason="This alert is already linked to an incident and requires incident-level management.",
            evidence=evidence,
            actions=actions,
            is_noise=False,
            noise_reason="Alert has an active incident — operational signal confirmed.",
            recurrence=recurrence,
            impact="high" if sev_rank >= 2 else "medium",
        )

    # ── Rule 2: Service recovered, alert still firing ────────────
    if svc_status == "up" and sev_rank < 2:
        failure_rate = down_count / check_count if check_count > 0 else 0
        if failure_rate < 0.3 and not recurrence:
            actions.append(f"Verify '{entity}' remains stable over the next 30 minutes")
            actions.append("Consider tuning alert thresholds to reduce transient noise")
            actions.append(
                "Confirm stability over the next monitoring cycle "
                "and close if no recurrence is detected."
            )
            return _make_decision(
                decision="monitor",
                confidence="high" if check_count >= 5 else "medium",
                risk_level="low",
                summary=f"Service '{entity}' has recovered. Alert condition appears transient.",
                reason=(
                    "Service is currently UP with acceptable check pass rate and no recurrence. "
                    "Alert condition is likely transient."
                ),
                evidence=evidence,
                actions=actions,
                is_noise=True,
                noise_reason=f"Service recovered — {down_count}/{check_count} checks failed, no recurrence.",
                recurrence=False,
                impact="none",
            )

    # ── Rule 3: Critical + service DOWN ──────────────────────────
    if sev_rank >= 2 and svc_status in ("down", "unknown", "degraded"):
        actions.append(f"Investigate '{entity}' immediately — service is DOWN")
        actions.append("Check recent deployment or infrastructure changes")
        actions.append("Notify on-call if not already escalated")
        if anomaly:
            actions.append(
                f"Correlate with active anomaly ({anomaly['category']}) — "
                f"may indicate a deeper pattern"
            )
        return _make_decision(
            decision="escalate",
            confidence="high",
            risk_level="critical",
            summary=f"Critical alert: '{entity}' is DOWN. Immediate attention required.",
            reason=(
                f"Service is currently {svc_status.upper()} with a CRITICAL severity alert. "
                "This pattern indicates an active outage requiring incident response."
            ),
            evidence=evidence,
            actions=actions,
            is_noise=False,
            noise_reason="Service is DOWN with critical alert — operational signal.",
            recurrence=recurrence,
            impact="high",
        )

    # ── Rule 4: Critical + service UP ────────────────────────────
    if sev_rank >= 2 and svc_status == "up":
        # If no recent checks are failing, the condition has fully recovered → monitor
        if down_count == 0 and not recurrence:
            actions.append(f"Verify '{entity}' is genuinely healthy (check metrics)")
            actions.append("Review alert rule thresholds — may have fired on a brief spike")
            actions.append(
                "Confirm stability over the next monitoring cycle and close if no recurrence is detected."
            )
            return _make_decision(
                decision="monitor",
                confidence="high" if check_count >= 5 else "medium",
                risk_level="low",
                summary=f"Critical alert for '{entity}': service is UP with no recent failures. Triggering condition appears recovered.",
                reason=(
                    "Critical alert fired but service is UP and all recent checks pass. "
                    "The triggering condition appears transient and recovered."
                ),
                evidence=evidence,
                actions=actions,
                is_noise=True,
                noise_reason="Service UP + 0 recent failures — likely brief spike or threshold sensitivity.",
                recurrence=False,
                impact="none",
            )
        # Service UP but with ongoing failures or recurrence → notify
        actions.append(f"Verify '{entity}' is genuinely healthy (check metrics)")
        actions.append("Review alert rule thresholds — may have fired on a brief spike")
        if recurrence:
            actions.append("Recurrence detected — review alert policy for this service")
        actions.append(
            "Confirm stability over the next monitoring cycle and close if no recurrence is detected."
        )
        return _make_decision(
            decision="notify",
            confidence="medium",
            risk_level="medium",
            summary=f"Critical alert for '{entity}' but service is currently UP — some failures remain.",
            reason=(
                "Critical severity alert fired and service now reports UP, but recent check failures "
                "or recurrence indicate the condition may not be fully resolved. Investigate."
            ),
            evidence=evidence,
            actions=actions,
            is_noise=False,
            noise_reason=(
                "Recurrence detected — repeated pattern, not noise."
                if recurrence else
                "Recent failures present — not classified as noise."
            ),
            recurrence=recurrence,
            impact="medium",
        )

    # ── Rule 5: Warning + recurrence ─────────────────────────────
    if sev_rank < 2 and recurrence:
        actions.append(f"Review alert history for '{entity}' — pattern is recurring")
        actions.append("Consider tightening monitoring checks or reviewing service stability")
        return _make_decision(
            decision="notify",
            confidence="medium",
            risk_level="medium",
            summary=f"Recurring warning alerts for '{entity}' — pattern warrants attention.",
            reason=(
                f"Service '{entity}' has fired {recent_events} alerts in the last 6 hours. "
                "Recurrence suggests instability."
            ),
            evidence=evidence,
            actions=actions,
            is_noise=False,
            noise_reason="Recurring pattern — not classified as noise.",
            recurrence=True,
            impact="medium",
        )

    # ── Rule 6: Warning + no recurrence ──────────────────────────
    if sev_rank < 2 and not recurrence:
        recovery_note = " Service is currently UP." if svc_status == "up" else ""
        actions.append(f"Monitor '{entity}' over the next hour")
        actions.append("No action required unless condition persists or severity increases")
        if svc_status == "up":
            actions.append(
                "Confirm stability over the next monitoring cycle "
                "and close if no recurrence is detected."
            )
        return _make_decision(
            decision="monitor",
            confidence="medium" if check_count > 0 else "low",
            risk_level="low",
            summary=f"Single non-critical alert for '{entity}'.{recovery_note} No immediate action needed.",
            reason=(
                f"Non-critical severity with no recurrence.{recovery_note} "
                "Condition does not meet escalation threshold."
            ),
            evidence=evidence,
            actions=actions,
            is_noise=svc_status == "up",
            noise_reason=(
                "Service UP + non-critical + no recurrence — likely transient."
                if svc_status == "up" else
                "Non-critical with no evidence of recurrence."
            ),
            recurrence=False,
            impact="low" if svc_status != "up" else "none",
        )

    # ── Default fallback ─────────────────────────────────────────
    actions.append(f"Review '{entity}' manually — automatic classification inconclusive")
    return _make_decision(
        decision="monitor",
        confidence="low",
        risk_level="medium",
        summary=f"Alert for '{entity}' requires manual review. Insufficient context.",
        reason="Rule-based engine could not classify this alert with high confidence.",
        evidence=evidence,
        actions=actions,
        is_noise=False,
        noise_reason="Insufficient data for noise classification.",
        recurrence=recurrence,
        impact="low",
    )


def rule_based_decision_for_anomaly(ctx: Dict) -> Dict[str, Any]:
    """Deterministic triage for anomaly records."""
    score        = ctx.get("anomaly_score", 0)
    severity     = ctx.get("severity", "low")
    sev_rank     = _SEV_RANK.get(severity, 0)
    svc_status   = ctx.get("service_current_status", "unknown")
    corr_alert   = ctx.get("correlated_alert")
    predicted    = ctx.get("predicted_risk", "none")
    occurrences  = ctx.get("occurrence_count", 1)
    entity       = ctx.get("service_name", "service")
    category     = ctx.get("primary_category", "")
    evidence_sum = ctx.get("evidence_summary", "")
    duration_min = ctx.get("duration_minutes", 0)

    evidence: List[str] = []
    actions:  List[str] = []

    if score is not None:
        evidence.append(f"Anomaly score: {score}/100 ({severity} severity)")
    if svc_status != "unknown":
        evidence.append(f"Service '{entity}' current status: {svc_status.upper()}")
    if corr_alert:
        evidence.append(
            f"Correlated alert: {corr_alert['alert_name']} "
            f"({corr_alert['severity']}, status: {corr_alert['status']})"
        )
    if occurrences > 1:
        evidence.append(f"Anomaly seen {occurrences} time(s)")
    if category:
        evidence.append(f"Primary category: {category}")
    if evidence_sum:
        evidence.append(f"Engine note: {evidence_sum[:200]}")
    if not evidence:
        evidence.append("Evidence is limited — insufficient telemetry available")

    # ── Rule 1: Correlated with critical active alert/incident ────
    if corr_alert and corr_alert.get("severity") == "critical":
        actions.append(f"Investigate '{entity}' — anomaly correlated with critical alert")
        if corr_alert.get("incident_id"):
            actions.append(f"Review linked incident {corr_alert['incident_id']}")
        return _make_decision(
            decision="escalate",
            confidence="high",
            risk_level="critical",
            summary=f"Anomaly for '{entity}' is correlated with an active critical alert.",
            reason="A concurrent critical alert confirms the anomaly is part of an operational incident.",
            evidence=evidence,
            actions=actions,
            is_noise=False,
            noise_reason="Correlated with critical alert — operational signal.",
            recurrence=occurrences > 1,
            impact="high",
        )

    # ── Rule 2: Correlated with non-critical alert ────────────────
    if corr_alert:
        actions.append(f"Monitor '{entity}' — anomaly and alert are concurrent")
        return _make_decision(
            decision="notify",
            confidence="medium",
            risk_level="medium",
            summary=f"Anomaly for '{entity}' coincides with a non-critical active alert.",
            reason="Concurrent anomaly and alert suggest elevated risk but not confirmed outage.",
            evidence=evidence,
            actions=actions,
            is_noise=False,
            noise_reason="Concurrent alert detected.",
            recurrence=occurrences > 1,
            impact="medium",
        )

    # ── Rule 3: High anomaly score, no alert ─────────────────────
    if score is not None and score >= 70:
        actions.append(f"Investigate '{entity}' metrics — high anomaly score with no active alert")
        actions.append("Check if alert rules cover this anomaly category")
        return _make_decision(
            decision="notify",
            confidence="medium",
            risk_level="high",
            summary=f"High anomaly score ({score}) for '{entity}' without a correlated alert.",
            reason="High anomaly score suggests real deviation even without a corresponding alert.",
            evidence=evidence,
            actions=actions,
            is_noise=False,
            noise_reason="High anomaly score — cannot classify as noise.",
            recurrence=occurrences > 1,
            impact="medium",
        )

    # ── Rule 4: Low/medium score, no alert ───────────────────────
    actions.append(f"Monitor '{entity}' for further anomaly escalation")
    return _make_decision(
        decision="monitor",
        confidence="medium" if score is not None else "low",
        risk_level="low",
        summary=f"Anomaly for '{entity}' (score {score}) — no correlated alert. Observe.",
        reason="Anomaly score is below notification threshold and no concurrent alert exists.",
        evidence=evidence,
        actions=actions,
        is_noise=score is not None and score < 40,
        noise_reason=(
            f"Score {score} is below threshold (40) — likely statistical variation."
            if score is not None and score < 40
            else "Score is in ambiguous range."
        ),
        recurrence=occurrences > 1,
        impact="none",
    )


def rule_based_decision_for_incident(ctx: Dict) -> Dict[str, Any]:
    """Deterministic triage for incidents."""
    severity     = ctx.get("severity", "warning")
    sev_rank     = _SEV_RANK.get(severity, 1)
    status       = ctx.get("status", "open")
    svc_status   = ctx.get("service_current_status", "unknown")
    down_count   = ctx.get("recent_down_count", 0)
    check_count  = ctx.get("recent_check_count", 0)
    alert_count  = ctx.get("linked_alert_count", 0)
    anomaly      = ctx.get("correlated_anomaly")
    entity       = ctx.get("entity_name", "service")
    duration_min = ctx.get("duration_minutes", 0)

    evidence: List[str] = []
    actions:  List[str] = []

    evidence.append(f"Incident status: {status.upper()}, severity: {severity.upper()}")
    if svc_status != "unknown":
        evidence.append(f"Service '{entity}' current status: {svc_status.upper()}")
    if alert_count > 0:
        evidence.append(f"{alert_count} alert(s) linked to this incident")
    if check_count > 0:
        evidence.append(f"Recent checks: {down_count}/{check_count} failed")
    if anomaly:
        evidence.append(
            f"Active anomaly: score {anomaly['score']}, severity {anomaly['severity']}, "
            f"category {anomaly.get('category', 'unknown')}"
        )
    if duration_min > 0:
        evidence.append(f"Incident duration: {duration_min:.0f} minute(s)")
    if not evidence:
        evidence.append("Evidence is limited")

    # ── Already resolved ─────────────────────────────────────────
    if status == "resolved":
        actions.append("Conduct post-incident review if duration exceeded 30 minutes")
        actions.append("Verify recovery is stable before closing monitoring")
        return _make_decision(
            decision="monitor",
            confidence="high",
            risk_level="low",
            summary=f"Incident for '{entity}' is resolved. Verify stability.",
            reason="Incident status is resolved. Recommend confirming service stability.",
            evidence=evidence,
            actions=actions,
            is_noise=False,
            noise_reason="Resolved incident — post-incident monitoring recommended.",
            recurrence=False,
            impact="none",
        )

    # ── Critical + service still DOWN ────────────────────────────
    if sev_rank >= 2 and svc_status in ("down", "degraded"):
        actions.append(f"Immediate intervention required — '{entity}' remains DOWN")
        actions.append("Escalate to senior on-call if not already done")
        actions.append("Check infrastructure, deployment pipeline, and dependencies")
        if anomaly:
            actions.append(
                f"Correlated anomaly ({anomaly['category']}) — check for cascading failure"
            )
        return _make_decision(
            decision="escalate",
            confidence="high",
            risk_level="critical",
            summary=f"Critical incident: '{entity}' service is still DOWN after {duration_min:.0f}m.",
            reason="Critical incident with service still down — active outage requiring urgent response.",
            evidence=evidence,
            actions=actions,
            is_noise=False,
            noise_reason="Active critical incident with service DOWN — confirmed signal.",
            recurrence=True,
            impact="high",
        )

    # ── Service healthy: UP + zero recent failures (any severity) ─
    # Primary noise-reduction rule. If the service is UP and no recent
    # checks are failing, the triggering condition has recovered.
    # Downgrade to monitor regardless of incident severity.
    if svc_status in ("up", "healthy") and down_count == 0:
        actions.append(
            "Confirm stability over the next monitoring cycle "
            "and close the incident if no recurrence is detected."
        )
        if check_count == 0:
            actions.append("No recent check data — verify monitoring is active for this service")
        return _make_decision(
            decision="monitor",
            confidence="high" if check_count >= 5 else "medium",
            risk_level="low" if sev_rank < 2 else "medium",
            summary=(
                f"Incident for '{entity}' (severity {severity.upper()}): "
                "service is currently UP with no recent failures. "
                "Triggering condition appears recovered."
            ),
            reason=(
                f"Service '{entity}' is UP and all recent checks are passing "
                f"({check_count} check(s), 0 failures). "
                "The condition that triggered this incident has recovered. "
                "No active failure signal exists to justify escalation or operator notification."
            ),
            evidence=evidence,
            actions=actions,
            is_noise=False,
            noise_reason="Service is healthy — incident condition resolved, post-recovery monitoring advised.",
            recurrence=False,
            impact="none" if sev_rank < 2 else "low",
        )

    # ── Critical + service UP but checks still show failures ─────
    if sev_rank >= 2 and svc_status == "up":
        actions.append(f"Service '{entity}' reports UP but recent checks show failures — verify")
        actions.append("Update incident status to 'investigating' or 'resolved' as appropriate")
        actions.append("Identify root cause before closing")
        actions.append(
            "Confirm stability over the next monitoring cycle "
            "and close the incident if no recurrence is detected."
        )
        return _make_decision(
            decision="notify",
            confidence="medium",
            risk_level="medium",
            summary=f"Critical incident for '{entity}': service is UP but recent check failures remain.",
            reason=(
                "Service is UP but recent checks still show failures. "
                "Condition may be intermittent. Recommend completing root cause analysis before closing."
            ),
            evidence=evidence,
            actions=actions,
            is_noise=False,
            noise_reason="Recent failures present despite UP status — not classified as noise.",
            recurrence=False,
            impact="medium",
        )

    # ── Warning / non-critical + degraded or unknown ─────────────
    actions.append(f"Monitor '{entity}' and update incident status as situation develops")
    actions.append(
        "Confirm stability over the next monitoring cycle "
        "and close the incident if no recurrence is detected."
    )
    return _make_decision(
        decision="notify" if svc_status not in ("up", "healthy") else "monitor",
        confidence="medium",
        risk_level="medium" if svc_status not in ("up", "healthy") else "low",
        summary=f"Non-critical incident for '{entity}' in {status} state.",
        reason=(
            "Non-critical incident with service in a degraded or unknown state. "
            "Operator awareness recommended."
            if svc_status not in ("up", "healthy") else
            "Non-critical incident with service UP — conditions do not meet escalation threshold."
        ),
        evidence=evidence,
        actions=actions,
        is_noise=False,
        noise_reason="Open incident — monitoring recommended.",
        recurrence=False,
        impact="medium" if svc_status not in ("up", "healthy") else "low",
    )


# ════════════════════════════════════════════════════════════════════
# 3.  LLM ENHANCEMENT  (optional — GPT-4o-mini only)
# ════════════════════════════════════════════════════════════════════

async def llm_decision(
    context_type: str,
    ctx: Dict[str, Any],
    rule_result: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Enhance a rule-based decision with GPT-4o-mini.
    Returns the enhanced decision or None on any failure.
    The LLM may refine summary, reason, evidence, and recommended_actions.
    It may NOT change the decision or risk_level to anything more severe
    than what the rule engine determined (safety guard).
    """
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        return None

    system_prompt = (
        "You are an AI operations triage assistant for an observability platform. "
        "You are given real operational context and a preliminary rule-based decision. "
        "Your job is to refine the summary, reason, evidence, and recommended_actions "
        "to be more specific, helpful, and operationally actionable. "
        "You MUST NOT change the 'decision' or 'risk_level' field. "
        "You MUST NOT invent systems, incidents, or metrics not present in the context. "
        "If evidence is sparse, state 'Evidence is limited' explicitly. "
        "Return ONLY valid JSON matching the exact schema provided — no extra text."
    )

    user_prompt = (
        f"Context type: {context_type}\n"
        f"Operational context:\n{json.dumps(ctx, default=str, indent=2)}\n\n"
        f"Preliminary decision:\n{json.dumps(rule_result, default=str, indent=2)}\n\n"
        "Return refined JSON with these fields only: "
        "summary, reason, evidence (array), recommended_actions (array), "
        "noise_assessment (object with is_likely_noise bool, noise_reason str, recurrence_detected bool), "
        "customer_impact (none/low/medium/high). "
        "Keep decision, confidence, risk_level, created_at, engine, model unchanged."
    )

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
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
                        {"role": "user",   "content": user_prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 800,
                    "response_format": {"type": "json_object"},
                },
            )

        if resp.status_code != 200:
            logger.warning("OpenAI returned %s — falling back to rule-based", resp.status_code)
            return None

        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        refined = json.loads(content)

        # Safety: preserve decision and risk_level from rule engine
        refined["decision"]   = rule_result["decision"]
        refined["risk_level"] = rule_result["risk_level"]
        refined["confidence"] = rule_result["confidence"]
        refined["created_at"] = rule_result["created_at"]
        refined["engine"]     = "llm"
        refined["model"]      = "gpt-4o-mini"

        # Validate required fields present
        for field in ["summary", "reason", "evidence", "recommended_actions", "noise_assessment"]:
            if field not in refined:
                logger.warning("LLM missing field '%s' — falling back", field)
                return None
        if not isinstance(refined["evidence"], list):
            refined["evidence"] = [str(refined["evidence"])]
        if not isinstance(refined["recommended_actions"], list):
            refined["recommended_actions"] = [str(refined["recommended_actions"])]

        return refined

    except Exception as exc:
        logger.warning("LLM decision failed (%s) — falling back to rule-based", exc)
        return None


# ════════════════════════════════════════════════════════════════════
# 4.  PUBLIC EVALUATE FUNCTIONS
# ════════════════════════════════════════════════════════════════════

async def evaluate_alert_decision(alert_event, db: Session) -> Dict[str, Any]:
    """Full triage pipeline for an alert event."""
    ctx         = build_alert_context(alert_event, db)
    rule_result = rule_based_decision_for_alert(ctx)
    llm_result  = await llm_decision("alert", ctx, rule_result)
    return llm_result if llm_result else rule_result


async def evaluate_anomaly_decision(anomaly_row, db: Session) -> Dict[str, Any]:
    """Full triage pipeline for an anomaly record."""
    ctx         = build_anomaly_context(anomaly_row, db)
    rule_result = rule_based_decision_for_anomaly(ctx)
    llm_result  = await llm_decision("anomaly", ctx, rule_result)
    return llm_result if llm_result else rule_result


async def evaluate_incident_decision(incident, db: Session) -> Dict[str, Any]:
    """Full triage pipeline for an incident."""
    ctx         = build_incident_context(incident, db)
    rule_result = rule_based_decision_for_incident(ctx)
    llm_result  = await llm_decision("incident", ctx, rule_result)
    return llm_result if llm_result else rule_result


# ════════════════════════════════════════════════════════════════════
# 5.  HELPERS
# ════════════════════════════════════════════════════════════════════

def _make_decision(
    *,
    decision: str,
    confidence: str,
    risk_level: str,
    summary: str,
    reason: str,
    evidence: List[str],
    actions: List[str],
    is_noise: bool,
    noise_reason: str,
    recurrence: bool,
    impact: str,
) -> Dict[str, Any]:
    return {
        "decision": decision,
        "confidence": confidence,
        "risk_level": risk_level,
        "summary": summary,
        "reason": reason,
        "evidence": evidence,
        "recommended_actions": actions,
        "noise_assessment": {
            "is_likely_noise":     is_noise,
            "noise_reason":        noise_reason,
            "recurrence_detected": recurrence,
        },
        "customer_impact": impact,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "engine": "rule-based",
        "model": None,
    }
