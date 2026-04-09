"""
Incident AI Service - Phase 3 / 3.1 polish.

Generates incident summaries, investigation hints, and postmortems
by analysing anomaly context data from the AI anomaly engine.

Deterministic approach: parses real evidence_summary signals (latency,
errors, trace bottlenecks, throughput, availability) to produce
human-readable, signal-specific operational guidance.

Hard rules:
  - NO executable commands - only guidance, explanation, and hints.
  - Hints tell the operator WHERE to look and WHAT to verify, never HOW to fix.
  - All text is factual and derived from actual telemetry signals.
  - Summaries are concise: 2-3 lines max, referencing real signals.
  - Hints are specific to the detected signal type, max 5.
"""

import httpx
import os
import re
from typing import Optional, List, Dict, Any, Tuple
from logging_config import get_logger

logger = get_logger(__name__)

ANOMALY_ENGINE_V1_URL = os.getenv(
    "ANOMALY_ENGINE_V1_URL",
    "http://rhinometric-anomaly-engine-v1:8091",
)


# ---------------------------------------------------------------------------
# Evidence parsing - extract real signals from evidence_summary
# ---------------------------------------------------------------------------

# Patterns we look for inside `evidence_summary`
_SIGNAL_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("latency",       re.compile(r"latency", re.I)),
    ("trace",         re.compile(r"trace\s*bottleneck|slow\s*spans?|span\s*latency|critical.path", re.I)),
    ("error",         re.compile(r"error\s*rate|error\s*spike|error\s*burst|elevated\s*errors|failure", re.I)),
    ("throughput",    re.compile(r"throughput|request\s*rate|traffic", re.I)),
    ("availability",  re.compile(r"availabilit|uptime|downtime|health.check|pod.restart", re.I)),
    ("saturation",    re.compile(r"saturation|cpu|memory|disk|resource", re.I)),
    ("ssl",           re.compile(r"ssl|certificate|tls", re.I)),
]

_DETAIL_EXTRACT = re.compile(r"\(([^)]+)\)")


def _parse_evidence_signals(evidence: str) -> List[Dict[str, str]]:
    """Parse evidence_summary into structured signal list.

    Example input:
        "Trace Bottleneck (37% dominance, threshold 30%) \u00b7 Uptime Degraded (1 incidents in 24h) \u00b7 Score 4/100 normal"
    Returns:
        [{"type": "trace", "raw": "Trace Bottleneck", "detail": "37% dominance, threshold 30%"},
         {"type": "availability", "raw": "Uptime Degraded", "detail": "1 incidents in 24h"}]
    """
    if not evidence:
        return []

    signals = []
    # Split on middle-dot, pipe, or bullet separators
    parts = re.split(r"\s*[\u00b7|]\s*", evidence)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Skip the trailing score summary like "Score 4/100 normal"
        if re.match(r"^Score\s+\d+", part, re.I):
            continue

        detail_match = _DETAIL_EXTRACT.search(part)
        detail = detail_match.group(1) if detail_match else ""
        raw = _DETAIL_EXTRACT.sub("", part).strip()

        signal_type = "other"
        for stype, pattern in _SIGNAL_PATTERNS:
            if pattern.search(part):
                signal_type = stype
                break

        signals.append({"type": signal_type, "raw": raw, "detail": detail})

    return signals


# ---------------------------------------------------------------------------
# Hint bank - keyed by signal type
# ---------------------------------------------------------------------------

_SIGNAL_HINTS: Dict[str, List[str]] = {
    "latency": [
        "Verify recent latency trends against baseline -- check p50/p95/p99 percentiles for the affected service.",
        "Inspect upstream dependencies and database query times for correlated slowdowns.",
        "Review recent deployments or config changes that may have introduced processing overhead.",
    ],
    "trace": [
        "Inspect critical-path spans for latency concentration -- identify which operations dominate request time.",
        "Analyze trace waterfall for sequential bottlenecks that could be parallelised.",
        "Check if specific endpoints or downstream calls show disproportionate span durations.",
    ],
    "error": [
        "Check application logs for new exception patterns or error spikes in the last hour.",
        "Review recent failures by endpoint -- identify if errors are isolated or service-wide.",
        "Inspect dependency health -- upstream or downstream failures often cascade as error bursts.",
    ],
    "throughput": [
        "Compare current request rate against the normal daily pattern -- distinguish organic spikes from anomalies.",
        "Check auto-scaling status and queue depths if throughput exceeds provisioned capacity.",
        "Review load balancer metrics for uneven traffic distribution across instances.",
    ],
    "availability": [
        "Confirm service health-check status and look for recent pod restarts or deployment rollouts.",
        "Check uptime history and correlate downtime windows with deployment or infrastructure events.",
        "Review readiness/liveness probe results and container restart counts.",
    ],
    "saturation": [
        "Review CPU, memory, and connection-pool utilisation for the service and its host.",
        "Check for resource throttling or OOM events in container metrics.",
        "Inspect garbage-collection pressure and heap usage trends for memory-related signals.",
    ],
    "ssl": [
        "Check SSL certificate expiry dates and renewal pipeline status.",
        "Verify TLS handshake times and certificate chain validity.",
    ],
}


# ---------------------------------------------------------------------------
# Fetch anomaly context
# ---------------------------------------------------------------------------

async def fetch_anomaly_context(service_name: str) -> Optional[Dict[str, Any]]:
    """Fetch current anomaly context for a service from the AI anomaly engine."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{ANOMALY_ENGINE_V1_URL}/api/v2/alerts/ai-context",
                params={"service_names": service_name},
            )
            if resp.status_code == 200:
                data = resp.json()

                # Primary format: {"contexts": {"service_name": {...}}}
                if isinstance(data, dict) and "contexts" in data:
                    contexts = data["contexts"]
                    if isinstance(contexts, dict):
                        # Exact match first
                        if service_name in contexts:
                            return contexts[service_name]
                        # Case-insensitive fallback
                        for k, v in contexts.items():
                            if k.lower() == service_name.lower():
                                return v
                        # First available
                        if contexts:
                            return next(iter(contexts.values()))

                # Legacy format: list
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
                if isinstance(data, dict):
                    services = data.get("services", data.get("results", []))
                    if isinstance(services, list) and services:
                        return services[0]
                    return data

            logger.warning(f"Anomaly context fetch for {service_name}: HTTP {resp.status_code}")
    except Exception as e:
        logger.warning(f"Failed to fetch anomaly context for {service_name}: {e}")
    return None


# ---------------------------------------------------------------------------
# Summary generation
# ---------------------------------------------------------------------------

def generate_incident_summary(
    service_name: str,
    severity: str,
    anomaly_ctx: Optional[Dict[str, Any]] = None,
    alert_summary: Optional[str] = None,
) -> str:
    """Build a concise, signal-driven incident summary (2-3 lines max)."""

    if not anomaly_ctx:
        if alert_summary:
            return f"Incident opened for {service_name} ({severity}). {alert_summary}"
        return f"Incident opened for {service_name} ({severity}). Monitoring for correlated signals."

    evidence_raw = anomaly_ctx.get("evidence_summary") or ""
    signals = _parse_evidence_signals(evidence_raw)
    anomaly_score = anomaly_ctx.get("anomaly_score")
    confidence = anomaly_ctx.get("confidence")
    risk_level = anomaly_ctx.get("predicted_risk_level") or ""
    explanation = (anomaly_ctx.get("explanation_summary") or "").strip()

    # Build signal description from parsed evidence
    signal_parts = []
    for sig in signals:
        if sig["detail"]:
            signal_parts.append(f"{sig['raw']} ({sig['detail']})")
        else:
            signal_parts.append(sig["raw"])

    # Compose the summary
    lines = []

    # Line 1: What is happening
    if explanation:
        lines.append(explanation)
    elif signal_parts:
        lines.append(f"Detected signals for **{service_name}**: {', '.join(signal_parts)}.")
    else:
        lines.append(f"Anomalous behaviour detected for **{service_name}**.")

    # Line 2: Severity + score context (only if meaningful)
    context_bits = []
    if severity in ("critical", "warning"):
        context_bits.append(f"Severity: {severity}")
    if anomaly_score is not None and anomaly_score > 10:
        context_bits.append(f"anomaly score {anomaly_score}/100")
    if confidence is not None:
        context_bits.append(f"confidence {confidence:.0%}" if isinstance(confidence, float) else f"confidence {confidence}")
    if risk_level and risk_level not in ("none", "low"):
        context_bits.append(f"predicted risk: {risk_level}")
    if context_bits:
        lines.append(" | ".join(context_bits) + ".")

    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Investigation hints
# ---------------------------------------------------------------------------

def generate_investigation_hints(
    service_name: str,
    severity: str,
    anomaly_ctx: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Generate 3-5 actionable, signal-specific investigation hints.

    Each hint tells the operator WHERE to look and WHAT to verify.
    No executable commands. No generic filler.
    """
    hints: List[str] = []
    seen_types = set()

    if anomaly_ctx:
        evidence_raw = anomaly_ctx.get("evidence_summary") or ""
        signals = _parse_evidence_signals(evidence_raw)

        # Add signal-specific hints (pick first hint per signal type)
        for sig in signals:
            stype = sig["type"]
            if stype in seen_types or stype == "other":
                continue
            seen_types.add(stype)
            bank = _SIGNAL_HINTS.get(stype, [])
            for hint in bank:
                if hint not in hints:
                    hints.append(hint)
                    break

        # If we have detail, add a signal-specific second hint
        for sig in signals:
            stype = sig["type"]
            if stype == "other":
                continue
            bank = _SIGNAL_HINTS.get(stype, [])
            for hint in bank:
                if hint not in hints and len(hints) < 4:
                    hints.append(hint)
                    break

        # Prediction-based hint
        pred_summary = (anomaly_ctx.get("prediction_summary") or "").strip()
        risk_level = anomaly_ctx.get("predicted_risk_level") or ""
        if risk_level not in ("none", "low", "") and pred_summary:
            hints.append(f"Prediction: {pred_summary} -- prepare mitigation if the trend continues.")

    # Fallback: ensure at least 2 hints
    if len(hints) < 2:
        hints.append(f"Review recent deployment and configuration changes for {service_name}.")
    if len(hints) < 2:
        hints.append(f"Check the {service_name} dashboard for correlated metric shifts.")

    # Critical severity addendum
    if severity == "critical" and len(hints) < 5:
        hints.append("Critical severity -- confirm customer-facing impact and consider engaging on-call.")

    return hints[:5]


# ---------------------------------------------------------------------------
# Postmortem generation
# ---------------------------------------------------------------------------

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
    dur_str = _format_duration(duration_seconds) if duration_seconds else "unknown"

    sections = []

    # -- What Happened --
    sections.append("## What Happened\n")
    if anomaly_ctx:
        explanation = (anomaly_ctx.get("explanation_summary") or "").strip()
        evidence_raw = anomaly_ctx.get("evidence_summary") or ""
        signals = _parse_evidence_signals(evidence_raw)

        if explanation:
            sections.append(explanation + "\n")
        elif signals:
            signal_desc = ", ".join(
                (f"{s['raw']} ({s['detail']})" if s["detail"] else s["raw"]) for s in signals
            )
            sections.append(f"This incident was triggered by: {signal_desc}.\n")
        else:
            sections.append(f"An anomaly was detected for {service_name} that triggered this incident.\n")
    else:
        sections.append(f"An incident was opened for {service_name} based on alert signals.\n")

    sections.append(f"**Service:** {service_name}  ")
    sections.append(f"**Severity:** {severity}  ")
    sections.append(f"**Duration:** {dur_str}  ")
    sections.append(f"**Started:** {started_at}  ")
    sections.append(f"**Resolved:** {resolved_at}\n")

    # -- Key Signals --
    if anomaly_ctx:
        evidence_raw = anomaly_ctx.get("evidence_summary") or ""
        signals = _parse_evidence_signals(evidence_raw)
        anomaly_score = anomaly_ctx.get("anomaly_score")
        confidence = anomaly_ctx.get("confidence")

        if signals or anomaly_score is not None:
            sections.append("## Key Signals\n")
            for sig in signals:
                if sig["detail"]:
                    sections.append(f"- **{sig['raw']}** -- {sig['detail']}")
                else:
                    sections.append(f"- **{sig['raw']}**")
            if anomaly_score is not None:
                sections.append(f"- Anomaly score: {anomaly_score}/100")
            if confidence is not None:
                conf_str = f"{confidence:.0%}" if isinstance(confidence, float) else str(confidence)
                sections.append(f"- Detection confidence: {conf_str}")
            sections.append("")

    # -- Timeline Summary --
    if timeline_events and len(timeline_events) > 0:
        sections.append("## Timeline\n")
        for evt in timeline_events[:10]:
            ts = evt.get("created_at", "")
            desc = evt.get("description") or evt.get("event_type", "")
            if ts:
                # Shorten ISO timestamp to readable format
                short_ts = ts[:19].replace("T", " ") if "T" in ts else ts
                sections.append(f"- **{short_ts}** -- {desc}")
            else:
                sections.append(f"- {desc}")
        sections.append("")

    # -- Follow-up --
    sections.append("## Recommended Follow-up\n")
    sections.append("- Verify the root cause has been fully addressed.")
    sections.append("- Review monitoring coverage for the contributing signal categories.")
    sections.append("- Document any manual actions taken during investigation.")

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
