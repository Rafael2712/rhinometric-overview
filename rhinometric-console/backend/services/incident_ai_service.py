"""
Incident AI Service ? Phase 3.

Generates incident summaries, investigation hints, and postmortems
by analysing anomaly context data from the AI anomaly engine.

Deterministic approach: uses structured anomaly context (explanation_summary,
evidence_summary, reason_codes, category scores, risk predictions) to produce
human-readable operational guidance.

Hard rules:
  - NO executable commands ? only guidance, explanation, and hints.
  - Hints tell the operator WHERE to look and WHAT to verify, never HOW to fix.
  - All text is factual and derived from actual telemetry signals.
"""

import httpx
import os
from typing import Optional, List, Dict, Any
from logging_config import get_logger

logger = get_logger(__name__)

# The anomaly engine is reachable from backend container via its internal URL
# or via the nginx proxy.  We try the internal Docker hostname first.
AI_ANOMALY_URL = os.getenv("AI_ANOMALY_URL", "http://ai-anomaly:8091")


# ?? Hint templates keyed by reason-code prefix ??????????????????

_REASON_HINTS: Dict[str, str] = {
    "LatencyBaseline": "Check recent latency trends ? the service exceeded its learned baseline. Look at upstream dependencies and recent deployments.",
    "Latency": "Investigate latency-related signals. Review response-time percentiles (p50/p95/p99) and check for upstream slowdowns or resource contention.",
    "ErrorRate": "Elevated error rate detected. Inspect application logs for new exception patterns, recent config changes, or dependency failures.",
    "Error": "Error signals were flagged. Examine error logs and trace spans for failing endpoints or unexpected HTTP status codes.",
    "Throughput": "Throughput anomaly observed. Verify whether traffic volume changed (organic spike vs. bot/attack) and check auto-scaling status.",
    "Saturation": "Resource saturation indicated. Review CPU, memory, and connection-pool utilisation for the service and its host.",
    "Availability": "Availability concern raised. Confirm the service health-check status and look for pod restarts or deployment rollouts.",
    "Traffic": "Unusual traffic pattern. Compare current request rate against the normal daily/weekly pattern for this service.",
    "CPU": "CPU-related signal. Check container/host CPU utilisation, throttling metrics, and whether recent code changes increased compute cost.",
    "Memory": "Memory-related signal. Look at heap/RSS trends, garbage-collection pressure, and potential memory leaks in recent releases.",
    "Disk": "Disk-related signal. Verify available disk space, I/O wait times, and log/data growth rates.",
    "Network": "Network-related signal. Inspect packet loss, DNS resolution times, and inter-service connectivity.",
    "Prediction": "The anomaly engine predicted an escalation risk. Review the prediction window and prepare mitigation if the trend continues.",
    "Composite": "Multiple signal categories contributed. Triage by checking the highest-scoring category first, then correlate across dimensions.",
}

_SEVERITY_CONTEXT = {
    "critical": "This is a **critical** incident requiring immediate attention.",
    "warning": "This is a **warning**-level incident that should be investigated promptly.",
    "info": "This is an **informational** incident flagged for awareness.",
}


async def fetch_anomaly_context(service_name: str) -> Optional[Dict[str, Any]]:
    """Fetch current anomaly context for a service from the AI anomaly engine."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{AI_ANOMALY_URL}/api/v2/alerts/ai-context",
                params={"service_names": service_name},
            )
            if resp.status_code == 200:
                data = resp.json()
                # The endpoint returns a list; find the matching service
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
                if isinstance(data, dict):
                    # Might be wrapped in a key
                    services = data.get("services", data.get("results", [data]))
                    if isinstance(services, list) and services:
                        return services[0]
                    return data
            logger.warning(f"Anomaly context fetch for {service_name}: HTTP {resp.status_code}")
    except Exception as e:
        logger.warning(f"Failed to fetch anomaly context for {service_name}: {e}")
    return None


def _extract_reason_codes(ctx: Dict[str, Any]) -> List[str]:
    """Pull reason codes from anomaly context at any nesting level."""
    codes = []
    # Direct field
    if "reason_codes" in ctx:
        codes.extend(ctx["reason_codes"] if isinstance(ctx["reason_codes"], list) else [])
    # Nested in anomaly details
    for key in ("anomaly", "anomaly_details", "details"):
        sub = ctx.get(key, {})
        if isinstance(sub, dict) and "reason_codes" in sub:
            codes.extend(sub["reason_codes"])
    return list(dict.fromkeys(codes))  # dedupe preserving order


def _extract_category_scores(ctx: Dict[str, Any]) -> Dict[str, float]:
    """Pull category scores dict from context."""
    for key in ("category_scores", "categories"):
        if key in ctx and isinstance(ctx[key], dict):
            return ctx[key]
    for key in ("anomaly", "anomaly_details", "details"):
        sub = ctx.get(key, {})
        if isinstance(sub, dict):
            for k2 in ("category_scores", "categories"):
                if k2 in sub and isinstance(sub[k2], dict):
                    return sub[k2]
    return {}


def generate_incident_summary(
    service_name: str,
    severity: str,
    anomaly_ctx: Optional[Dict[str, Any]] = None,
    alert_summary: Optional[str] = None,
) -> str:
    """Build a concise incident summary from available context."""
    parts = []

    sev_line = _SEVERITY_CONTEXT.get(severity, f"Severity: {severity}.")
    parts.append(sev_line)

    if anomaly_ctx:
        # Use the engine's own explanation if available
        explanation = (
            anomaly_ctx.get("explanation_summary")
            or anomaly_ctx.get("explanation")
            or ""
        )
        if explanation:
            parts.append(explanation.strip())

        evidence = anomaly_ctx.get("evidence_summary") or anomaly_ctx.get("evidence") or ""
        if evidence:
            parts.append(f"Evidence: {evidence.strip()}")

        risk = anomaly_ctx.get("predicted_risk_level") or anomaly_ctx.get("risk_level") or ""
        risk_score = anomaly_ctx.get("predicted_risk_score") or anomaly_ctx.get("risk_score")
        if risk:
            risk_text = f"Predicted risk: {risk}"
            if risk_score is not None:
                risk_text += f" (score {risk_score})"
            parts.append(risk_text)

        anomaly_score = anomaly_ctx.get("anomaly_score")
        if anomaly_score is not None:
            parts.append(f"Anomaly score: {anomaly_score}")

    if alert_summary and not anomaly_ctx:
        parts.append(alert_summary)

    if not parts or len(parts) <= 1:
        parts.append(
            f"An incident has been opened for **{service_name}** based on detected anomalous behaviour. "
            "Further context will be added as signals are correlated."
        )

    return "\n\n".join(parts)


def generate_investigation_hints(
    service_name: str,
    severity: str,
    anomaly_ctx: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Generate 3-6 actionable investigation hints.

    Hints tell operators WHERE to look and WHAT to verify.
    They NEVER suggest executable commands or specific fixes.
    """
    hints: List[str] = []

    # 1) Hints driven by reason codes
    if anomaly_ctx:
        reason_codes = _extract_reason_codes(anomaly_ctx)
        for code in reason_codes:
            for prefix, hint in _REASON_HINTS.items():
                if prefix.lower() in code.lower() and hint not in hints:
                    hints.append(hint)
                    break

    # 2) Hints driven by top category scores
    if anomaly_ctx:
        cat_scores = _extract_category_scores(anomaly_ctx)
        if cat_scores:
            top_cats = sorted(cat_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            for cat_name, score in top_cats:
                if score > 0.3:
                    for prefix, hint in _REASON_HINTS.items():
                        if prefix.lower() in cat_name.lower() and hint not in hints:
                            hints.append(hint)
                            break

    # 3) Prediction-based hint
    if anomaly_ctx:
        pred_summary = anomaly_ctx.get("prediction_summary") or anomaly_ctx.get("prediction") or ""
        if pred_summary:
            hints.append(f"Prediction insight: {pred_summary.strip()}")

    # 4) Always-present baseline hints
    hints.append(
        f"Review the recent deployment and configuration change history for **{service_name}**."
    )
    hints.append(
        f"Check the **{service_name}** dashboard in Grafana for correlated metric shifts."
    )
    if severity == "critical":
        hints.append(
            "This is critical severity ? confirm customer-facing impact and consider engaging on-call."
        )

    # Cap at 6
    return hints[:6]


def generate_postmortem(
    service_name: str,
    severity: str,
    started_at: str,
    resolved_at: str,
    duration_seconds: Optional[int],
    anomaly_ctx: Optional[Dict[str, Any]] = None,
    timeline_events: Optional[List[Dict]] = None,
) -> str:
    """Generate a structured postmortem when an incident is resolved."""
    sections = []

    # Header
    dur_str = _format_duration(duration_seconds) if duration_seconds else "unknown"
    sections.append(f"## Postmortem ? {service_name}")
    sections.append(f"**Severity:** {severity}  ")
    sections.append(f"**Duration:** {dur_str}  ")
    sections.append(f"**Started:** {started_at}  ")
    sections.append(f"**Resolved:** {resolved_at}")

    # What happened
    sections.append("\n### What Happened")
    if anomaly_ctx:
        explanation = anomaly_ctx.get("explanation_summary") or anomaly_ctx.get("explanation") or ""
        if explanation:
            sections.append(explanation.strip())
        else:
            sections.append(f"An anomaly was detected for {service_name} that triggered this incident.")
    else:
        sections.append(f"An incident was opened for {service_name} based on alert signals.")

    # Key signals
    if anomaly_ctx:
        evidence = anomaly_ctx.get("evidence_summary") or anomaly_ctx.get("evidence") or ""
        if evidence:
            sections.append("\n### Key Signals")
            sections.append(evidence.strip())

        reason_codes = _extract_reason_codes(anomaly_ctx)
        if reason_codes:
            sections.append("\n### Contributing Factors")
            for rc in reason_codes[:5]:
                sections.append(f"- {rc}")

    # Timeline summary
    if timeline_events:
        sections.append("\n### Timeline")
        for evt in timeline_events[:10]:
            ts = evt.get("created_at", "")
            desc = evt.get("description", evt.get("event_type", ""))
            if ts:
                sections.append(f"- **{ts}** ? {desc}")
            else:
                sections.append(f"- {desc}")

    # Follow-up
    sections.append("\n### Recommended Follow-up")
    sections.append("- Review whether the root cause has been fully addressed.")
    sections.append("- Verify monitoring coverage for the contributing signal categories.")
    sections.append("- Document any manual actions taken during investigation.")

    return "\n".join(sections)


def _format_duration(seconds: Optional[int]) -> str:
    if seconds is None:
        return "unknown"
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    return f"{hours}h {mins}m"
