"""
Root Cause Assistant — Phase 2.7

Deterministic, explainable root-cause analysis for incidents.
Analyses a ±5-minute window around the incident start:
  1. Metrics (latency, error rate, availability from external_service_checks)
  2. Alert events linked to the entity
  3. Anomaly detection signals (from AI service)
  4. Log error signals (from Loki)

Each signal contributes points; the entity with the highest score
becomes the candidate root cause.

Read-only — never mutates any data.
"""

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

import httpx
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from config import settings
from models.incident import Incident
from models.alert_event import AlertEvent
from models.external_service import ExternalService
from models.external_service_check import ExternalServiceCheck

logger = logging.getLogger("rhinometric.root_cause")

# ── Scoring weights ──────────────────────────────────────────────
SCORE_METRIC_SPIKE = 3
SCORE_ANOMALY      = 2
SCORE_ALERT        = 2
SCORE_LOG_ERRORS   = 2

# ── Analysis window ──────────────────────────────────────────────
WINDOW_MINUTES = 5
BASELINE_MINUTES = 30

# ── Spike threshold ──────────────────────────────────────────────
SPIKE_FACTOR = 2.0  # 2× increase from baseline → spike


# ─────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────

async def analyze_incident_root_cause(
    incident_id: str,
    db: Session,
) -> Dict[str, Any]:
    """Analyse an incident and return a structured root-cause hypothesis."""

    import uuid as _uuid
    try:
        inc_uuid = _uuid.UUID(incident_id)
    except ValueError:
        return _no_data_response(incident_id, "Invalid incident ID")

    incident = db.query(Incident).filter(Incident.id == inc_uuid).first()
    if not incident:
        return _no_data_response(incident_id, "Incident not found")

    started_at = incident.started_at
    if started_at and started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)

    window_start = started_at - timedelta(minutes=WINDOW_MINUTES)
    window_end   = started_at + timedelta(minutes=WINDOW_MINUTES)
    baseline_start = started_at - timedelta(minutes=BASELINE_MINUTES)
    baseline_end   = started_at - timedelta(minutes=WINDOW_MINUTES)

    entity_name = incident.entity_name
    entity_type = incident.entity_type

    # ── 1. Gather metric signals ─────────────────────────────────
    metric_signals = _gather_metric_signals(
        db, entity_name, window_start, window_end,
        baseline_start, baseline_end,
    )

    # ── 2. Gather alert event signals ────────────────────────────
    alert_signals = _gather_alert_signals(
        db, entity_name, entity_type, window_start, window_end,
    )

    # ── 3. Gather anomaly signals (async — AI service) ───────────
    anomaly_signals = await _gather_anomaly_signals(
        entity_name, window_start, window_end,
    )

    # ── 4. Gather log error signals (async — Loki) ───────────────
    log_signals = await _gather_log_signals(
        entity_name, window_start, window_end,
    )

    # ── 5. Score and rank ────────────────────────────────────────
    evidence: List[Dict[str, Any]] = []
    total_score = 0

    # Metric spikes
    for sig in metric_signals:
        total_score += SCORE_METRIC_SPIKE
        evidence.append({
            "type": "metric_spike",
            "metric": sig["metric"],
            "value": sig["value"],
            "baseline": sig["baseline"],
            "factor": sig["factor"],
            "timestamp": sig.get("timestamp"),
        })

    # Alerts
    for sig in alert_signals:
        total_score += SCORE_ALERT
        evidence.append({
            "type": "alert",
            "alert_name": sig["alert_name"],
            "severity": sig["severity"],
            "metric_name": sig.get("metric_name"),
            "started_at": sig["started_at"],
        })

    # Anomalies
    for sig in anomaly_signals:
        total_score += SCORE_ANOMALY
        evidence.append({
            "type": "anomaly",
            "metric": sig.get("metric_name", "unknown"),
            "score": sig.get("anomaly_score", 0),
            "timestamp": sig.get("timestamp"),
        })

    # Log errors
    if log_signals.get("error_count", 0) > 0:
        total_score += SCORE_LOG_ERRORS
        evidence.append({
            "type": "log_errors",
            "error_count": log_signals["error_count"],
            "sample_messages": log_signals.get("samples", []),
        })

    # ── 6. Determine confidence ──────────────────────────────────
    if total_score >= 7:
        confidence = "high"
    elif total_score >= 4:
        confidence = "medium"
    elif total_score >= 1:
        confidence = "low"
    else:
        confidence = "none"

    # ── 7. Determine primary signal ──────────────────────────────
    primary_signal = _determine_primary_signal(metric_signals, alert_signals, anomaly_signals, log_signals)

    # ── 8. Build response ────────────────────────────────────────
    if total_score == 0:
        return _no_data_response(
            incident_id,
            "No correlated signals found in the analysis window",
        )

    return {
        "incident_id": incident_id,
        "entity_name": entity_name,
        "entity_type": entity_type,
        "analysis_window": {
            "start": window_start.isoformat(),
            "end": window_end.isoformat(),
        },
        "likely_root_cause": {
            "entity": entity_name,
            "metric": primary_signal.get("metric", "unknown"),
            "confidence": confidence,
            "description": _build_description(entity_name, primary_signal, confidence),
        },
        "score": total_score,
        "evidence": evidence,
        "signal_counts": {
            "metric_spikes": len(metric_signals),
            "alerts": len(alert_signals),
            "anomalies": len(anomaly_signals),
            "log_errors": log_signals.get("error_count", 0),
        },
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────────────────────────────
# Signal Gatherers
# ─────────────────────────────────────────────────────────────────

def _gather_metric_signals(
    db: Session,
    entity_name: str,
    window_start: datetime,
    window_end: datetime,
    baseline_start: datetime,
    baseline_end: datetime,
) -> List[Dict[str, Any]]:
    """Compare incident-window metrics vs 30-min baseline."""
    signals = []

    # Find the service
    service = db.query(ExternalService).filter(
        ExternalService.name == entity_name
    ).first()
    if not service:
        return signals

    sid = service.id

    # Incident-window checks
    window_checks = db.query(ExternalServiceCheck).filter(
        ExternalServiceCheck.service_id == sid,
        ExternalServiceCheck.checked_at >= window_start,
        ExternalServiceCheck.checked_at <= window_end,
    ).all()

    # Baseline checks
    baseline_checks = db.query(ExternalServiceCheck).filter(
        ExternalServiceCheck.service_id == sid,
        ExternalServiceCheck.checked_at >= baseline_start,
        ExternalServiceCheck.checked_at <= baseline_end,
    ).all()

    if not window_checks or not baseline_checks:
        return signals

    # ── Latency comparison ───────────────────────────────────────
    w_latencies = [c.response_time_ms for c in window_checks if c.response_time_ms and c.response_time_ms > 0]
    b_latencies = [c.response_time_ms for c in baseline_checks if c.response_time_ms and c.response_time_ms > 0]

    if w_latencies and b_latencies:
        w_avg = sum(w_latencies) / len(w_latencies)
        b_avg = sum(b_latencies) / len(b_latencies)

        # P95
        w_sorted = sorted(w_latencies)
        b_sorted = sorted(b_latencies)
        w_p95 = w_sorted[int(len(w_sorted) * 0.95)] if len(w_sorted) >= 2 else w_avg
        b_p95 = b_sorted[int(len(b_sorted) * 0.95)] if len(b_sorted) >= 2 else b_avg

        if b_avg > 0:
            avg_factor = w_avg / b_avg
            if avg_factor >= SPIKE_FACTOR:
                signals.append({
                    "metric": "avg_latency",
                    "value": f"{w_avg:.1f}ms",
                    "baseline": f"{b_avg:.1f}ms",
                    "factor": round(avg_factor, 1),
                })

        if b_p95 > 0:
            p95_factor = w_p95 / b_p95
            if p95_factor >= SPIKE_FACTOR:
                signals.append({
                    "metric": "p95_latency",
                    "value": f"{w_p95:.1f}ms",
                    "baseline": f"{b_p95:.1f}ms",
                    "factor": round(p95_factor, 1),
                })

    # ── Error rate comparison ────────────────────────────────────
    w_errors = sum(1 for c in window_checks if c.status and c.status.lower() in ("down", "error", "degraded"))
    b_errors = sum(1 for c in baseline_checks if c.status and c.status.lower() in ("down", "error", "degraded"))
    w_err_rate = (w_errors / len(window_checks) * 100) if window_checks else 0
    b_err_rate = (b_errors / len(baseline_checks) * 100) if baseline_checks else 0

    if w_err_rate > 0 and (b_err_rate == 0 or (b_err_rate > 0 and w_err_rate / b_err_rate >= SPIKE_FACTOR)):
        signals.append({
            "metric": "error_rate",
            "value": f"{w_err_rate:.1f}%",
            "baseline": f"{b_err_rate:.1f}%",
            "factor": round(w_err_rate / max(b_err_rate, 0.1), 1),
        })

    # ── Availability drop ────────────────────────────────────────
    w_up = sum(1 for c in window_checks if c.status and c.status.lower() == "up")
    b_up = sum(1 for c in baseline_checks if c.status and c.status.lower() == "up")
    w_avail = (w_up / len(window_checks) * 100) if window_checks else 100
    b_avail = (b_up / len(baseline_checks) * 100) if baseline_checks else 100

    if b_avail > 0 and w_avail < b_avail and (b_avail - w_avail) >= 20:
        signals.append({
            "metric": "availability",
            "value": f"{w_avail:.1f}%",
            "baseline": f"{b_avail:.1f}%",
            "factor": round(b_avail / max(w_avail, 0.1), 1),
        })

    return signals


def _gather_alert_signals(
    db: Session,
    entity_name: str,
    entity_type: str,
    window_start: datetime,
    window_end: datetime,
) -> List[Dict[str, Any]]:
    """Find alert events for the entity within the analysis window."""
    alerts = db.query(AlertEvent).filter(
        AlertEvent.entity_name == entity_name,
        AlertEvent.started_at >= window_start,
        AlertEvent.started_at <= window_end,
    ).order_by(AlertEvent.started_at.asc()).limit(20).all()

    return [
        {
            "alert_name": a.alert_name,
            "severity": a.severity,
            "metric_name": a.metric_name,
            "started_at": a.started_at.isoformat() if a.started_at else None,
        }
        for a in alerts
    ]


async def _gather_anomaly_signals(
    entity_name: str,
    window_start: datetime,
    window_end: datetime,
) -> List[Dict[str, Any]]:
    """Query the AI anomaly service for anomalies in the window."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.AI_ANOMALY_URL}/anomalies",
                params={"limit": 100},
            )
            if resp.status_code != 200:
                return []

            data = resp.json()
            anomalies = data.get("anomalies", [])

            matched = []
            for a in anomalies:
                a_entity = a.get("entity_name", "")
                a_ts_str = a.get("detected_at") or a.get("timestamp")
                if not a_ts_str or a_entity != entity_name:
                    continue

                try:
                    a_ts = datetime.fromisoformat(a_ts_str.replace("Z", "+00:00"))
                    if a_ts.tzinfo is None:
                        a_ts = a_ts.replace(tzinfo=timezone.utc)
                except (ValueError, AttributeError):
                    continue

                if window_start <= a_ts <= window_end:
                    matched.append({
                        "metric_name": a.get("metric_name", a.get("config_name", "unknown")),
                        "anomaly_score": a.get("anomaly_score", a.get("severity_score", 0)),
                        "timestamp": a_ts.isoformat(),
                    })

            return matched[:10]

    except Exception as e:
        logger.warning(f"Failed to fetch anomalies: {e}")
        return []


async def _gather_log_signals(
    entity_name: str,
    window_start: datetime,
    window_end: datetime,
) -> Dict[str, Any]:
    """Query Loki for error logs in the window."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Search container logs for error patterns
            query = f'{{job="docker_logs"}} |= "{entity_name}" |~ "(?i)(error|timeout|connection refused|database unavailable|exception|fatal)"'

            start_ns = str(int(window_start.timestamp() * 1e9))
            end_ns = str(int(window_end.timestamp() * 1e9))

            resp = await client.get(
                f"{settings.LOKI_URL}/loki/api/v1/query_range",
                params={
                    "query": query,
                    "start": start_ns,
                    "end": end_ns,
                    "limit": 50,
                },
            )

            if resp.status_code != 200:
                # Try fallback query with console-backend job
                query2 = f'{{job="console-backend"}} |= "{entity_name}" |~ "(?i)(error|timeout|exception|fail)"'
                resp = await client.get(
                    f"{settings.LOKI_URL}/loki/api/v1/query_range",
                    params={
                        "query": query2,
                        "start": start_ns,
                        "end": end_ns,
                        "limit": 50,
                    },
                )
                if resp.status_code != 200:
                    return {"error_count": 0, "samples": []}

            data = resp.json()
            streams = data.get("data", {}).get("result", [])

            total_errors = 0
            samples = []
            for stream in streams:
                values = stream.get("values", [])
                total_errors += len(values)
                for ts, line in values[:3]:
                    samples.append(line[:200])

            return {
                "error_count": total_errors,
                "samples": samples[:5],
            }

    except Exception as e:
        logger.warning(f"Failed to query Loki: {e}")
        return {"error_count": 0, "samples": []}


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _determine_primary_signal(
    metrics: List[Dict],
    alerts: List[Dict],
    anomalies: List[Dict],
    log_signals: Dict,
) -> Dict[str, Any]:
    """Determine the most significant signal."""
    # Prioritize: metric spikes > alerts > anomalies > logs
    if metrics:
        best = max(metrics, key=lambda m: m.get("factor", 0))
        return {"metric": best["metric"], "type": "metric_spike", "detail": best}
    if alerts:
        return {"metric": alerts[0].get("metric_name", "alert"), "type": "alert", "detail": alerts[0]}
    if anomalies:
        best = max(anomalies, key=lambda a: a.get("anomaly_score", 0))
        return {"metric": best.get("metric_name", "anomaly"), "type": "anomaly", "detail": best}
    if log_signals.get("error_count", 0) > 0:
        return {"metric": "log_errors", "type": "log_errors", "detail": log_signals}
    return {"metric": "unknown", "type": "none", "detail": {}}


def _build_description(entity_name: str, primary: Dict, confidence: str) -> str:
    """Build a human-readable root cause description."""
    metric = primary.get("metric", "unknown")
    sig_type = primary.get("type", "none")

    if sig_type == "metric_spike":
        detail = primary.get("detail", {})
        factor = detail.get("factor", 0)
        return f"{entity_name} experienced a {factor}x {metric} spike during the incident window"

    if sig_type == "alert":
        detail = primary.get("detail", {})
        alert_name = detail.get("alert_name", "Unknown")
        return f"Alert '{alert_name}' fired for {entity_name} correlating with the incident"

    if sig_type == "anomaly":
        detail = primary.get("detail", {})
        score = detail.get("anomaly_score", 0)
        return f"Anomaly detected on {entity_name} ({metric}) with score {score}"

    if sig_type == "log_errors":
        detail = primary.get("detail", {})
        count = detail.get("error_count", 0)
        return f"{count} error log entries found for {entity_name} during the incident window"

    return f"Insufficient data to determine root cause for {entity_name}"


def _no_data_response(incident_id: str, message: str) -> Dict[str, Any]:
    """Return a structured response when no analysis is possible."""
    return {
        "incident_id": incident_id,
        "likely_root_cause": {
            "entity": None,
            "metric": None,
            "confidence": "none",
            "description": message,
        },
        "score": 0,
        "evidence": [],
        "signal_counts": {
            "metric_spikes": 0,
            "alerts": 0,
            "anomalies": 0,
            "log_errors": 0,
        },
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }
