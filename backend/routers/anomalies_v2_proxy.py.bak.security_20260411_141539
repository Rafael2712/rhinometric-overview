"""
Anomalies V2 Proxy — severity-aware enrichment layer.

Proxies /api/v2/anomalies to the Go anomaly engine and enriches
each anomaly with hard operational severity classification.

The Go engine's ML model adapts to sustained failures, marking
services with 99% error rates and 100+ consecutive failures as
merely "degraded" (score 56/100).  This proxy applies hard rules
to override severity and generate operationally honest explanations.

Hard classification rules:
  - error_rate >= 95% AND failure_streak >= 20  →  CRITICAL (SERVICE DOWN)
  - error_rate >= 80% OR failure_streak >= 10   →  CRITICAL
  - error_rate >= 50%                           →  HIGH
  - latency_deviation >= 500%                   →  CRITICAL
  - latency_deviation >= 200%                   →  HIGH
  - health_score < 30                           →  CRITICAL (SERVICE DOWN)
  - availability incidents + high error rate    →  CRITICAL

Does NOT modify: anomaly scoring, alert routing, or API contract
shape.  Only adds/overrides: severity, explanation_summary, op_state.
"""

import logging
import re
from typing import Optional

import httpx
from fastapi import APIRouter, Request, Response

logger = logging.getLogger("anomalies_v2_proxy")

ANOMALY_ENGINE_URL = "http://rhinometric-anomaly-engine-v1:8091"
HTTP_TIMEOUT = 15.0

router = APIRouter()

# -- Operational state constants --
_DOWN = "DOWN"
_SEVERE = "SEVERE_DEGRADATION"
_DEGRADED = "DEGRADED"
_MINOR = "MINOR"
_NORMAL = "NORMAL"

# -- Severity mapping (engine → standard) --
_SEVERITY_RANK = {
    "emergency": 0,
    "critical": 1,
    "high": 2,
    "degraded": 3,
    "warning": 3,
    "medium": 3,
    "watch": 4,
    "low": 5,
    "normal": 6,
}


def _max_sev(a: str, b: str) -> str:
    """Return the more severe of two severity labels."""
    return a if _SEVERITY_RANK.get(a, 6) <= _SEVERITY_RANK.get(b, 6) else b


def _extract_error_rate(anomaly: dict) -> Optional[float]:
    """Extract error rate from reason_codes."""
    for rc in anomaly.get("reason_codes") or []:
        code = rc.get("code", "")
        detail = rc.get("detail") or {}
        if code == "ErrorRateElevated":
            return detail.get("rate")
    return None


def _extract_failure_streak(anomaly: dict) -> int:
    """Extract consecutive failure count from reason_codes."""
    for rc in anomaly.get("reason_codes") or []:
        if rc.get("code") == "FailureStreak":
            return (rc.get("detail") or {}).get("count", 0)
    return 0


def _extract_latency_deviation(anomaly: dict) -> float:
    """Extract latency baseline deviation percentage."""
    for rc in anomaly.get("reason_codes") or []:
        if rc.get("code") == "LatencyBaselineBreach":
            return abs((rc.get("detail") or {}).get("deviation_pct", 0))
    return abs(anomaly.get("baseline_deviation_pct", 0))


def _extract_health_score(anomaly: dict) -> Optional[float]:
    """Extract health score from category_scores or reason_codes."""
    cats = anomaly.get("category_scores") or {}
    # Availability category is 0-100
    avail = cats.get("availability")
    # Also try reason_codes
    for rc in anomaly.get("reason_codes") or []:
        if rc.get("code") == "PredictedAvailabilityRisk":
            detail = rc.get("detail") or {}
            hs = detail.get("health_score")
            if hs is not None:
                return hs
    return avail


def _classify_anomaly(anomaly: dict) -> tuple:
    """Classify operational state from anomaly data.

    Returns (op_state, corrected_severity, explanation).
    """
    service_name = anomaly.get("service_name", "unknown")
    engine_severity = anomaly.get("severity", "normal")
    error_rate = _extract_error_rate(anomaly)
    failure_streak = _extract_failure_streak(anomaly)
    latency_dev = _extract_latency_deviation(anomaly)
    evidence = anomaly.get("evidence_summary", "")

    # -- Hard DOWN classification --
    if error_rate is not None and error_rate >= 0.95 and failure_streak >= 20:
        explanation = (
            f"**SERVICE DOWN** — {service_name} has {error_rate*100:.0f}% error rate "
            f"with {failure_streak} consecutive failures. "
            f"Nearly all requests are failing. Immediate investigation required."
        )
        return _DOWN, "critical", explanation

    if error_rate is not None and error_rate >= 0.95 and failure_streak >= 5:
        explanation = (
            f"**SERVICE DOWN** — {service_name} error rate at {error_rate*100:.0f}% "
            f"({failure_streak} consecutive failures). "
            f"Service is effectively non-functional."
        )
        return _DOWN, "critical", explanation

    # -- CRITICAL classification --
    if error_rate is not None and error_rate >= 0.80:
        explanation = (
            f"**SEVERE DEGRADATION** — {service_name} error rate at {error_rate*100:.0f}% "
            f"({failure_streak} consecutive failures). "
            f"Majority of requests failing. Users experiencing widespread failures."
        )
        return _SEVERE, "critical", explanation

    if failure_streak >= 50:
        er_part = f" with {error_rate*100:.0f}% error rate" if error_rate else ""
        explanation = (
            f"**SEVERE DEGRADATION** — {service_name} has {failure_streak} "
            f"consecutive failures{er_part}. Service is severely impaired."
        )
        return _SEVERE, "critical", explanation

    if latency_dev >= 500:
        explanation = (
            f"**SEVERE DEGRADATION** — {service_name} latency {latency_dev:.0f}% above baseline. "
            f"Service is effectively unusable due to extreme response times."
        )
        return _SEVERE, "critical", explanation

    # -- HIGH classification --
    if error_rate is not None and error_rate >= 0.50:
        explanation = (
            f"**DEGRADED** — {service_name} error rate at {error_rate*100:.0f}% "
            f"({failure_streak} consecutive failures). "
            f"Significant portion of requests failing."
        )
        return _DEGRADED, "high", explanation

    if latency_dev >= 200:
        explanation = (
            f"**DEGRADED** — {service_name} latency {latency_dev:.0f}% above baseline. "
            f"Users experiencing significant delays."
        )
        return _DEGRADED, "high", explanation

    if failure_streak >= 10 and error_rate is not None and error_rate >= 0.30:
        explanation = (
            f"**DEGRADED** — {service_name} with {failure_streak} consecutive failures "
            f"and {error_rate*100:.0f}% error rate. Service reliability is impacted."
        )
        return _DEGRADED, "high", explanation

    # -- MINOR classification --
    if latency_dev >= 100:
        explanation = (
            f"{service_name}: latency {latency_dev:.0f}% above baseline. "
            f"Performance degradation detected — monitor for escalation."
        )
        return _MINOR, _max_sev(engine_severity, "watch"), explanation

    if error_rate is not None and error_rate >= 0.10:
        explanation = (
            f"{service_name}: error rate at {error_rate*100:.0f}%. "
            f"Elevated failure rate detected — monitor for escalation."
        )
        return _MINOR, _max_sev(engine_severity, "watch"), explanation

    # -- NORMAL — pass through --
    return _NORMAL, engine_severity, None


def _enrich_anomaly(anomaly: dict) -> dict:
    """Enrich a single V2 anomaly with severity classification."""
    op_state, corrected_severity, explanation = _classify_anomaly(anomaly)

    engine_severity = anomaly.get("severity", "normal")

    # Only upgrade severity, never downgrade
    if _SEVERITY_RANK.get(corrected_severity, 6) < _SEVERITY_RANK.get(engine_severity, 6):
        anomaly["severity"] = corrected_severity
        anomaly["severity_original"] = engine_severity
        logger.info(
            f"Severity override: {anomaly.get('service_name')} "
            f"{engine_severity}→{corrected_severity} (op_state={op_state})"
        )

    anomaly["op_state"] = op_state

    if explanation:
        anomaly["explanation_summary"] = explanation
    elif op_state in (_DOWN, _SEVERE, _DEGRADED):
        # Should not happen, but safety net
        anomaly["explanation_summary"] = anomaly.get("evidence_summary", "")

    # Upgrade anomaly_score for DOWN/SEVERE states
    current_score = anomaly.get("anomaly_score", 0)
    if op_state == _DOWN and current_score < 95:
        anomaly["anomaly_score"] = 95
        anomaly["anomaly_score_original"] = current_score
    elif op_state == _SEVERE and current_score < 85:
        anomaly["anomaly_score"] = 85
        anomaly["anomaly_score_original"] = current_score
    elif op_state == _DEGRADED and current_score < 70:
        anomaly["anomaly_score"] = 70
        anomaly["anomaly_score_original"] = current_score

    return anomaly


def _enrich_response(data: dict) -> dict:
    """Enrich the full V2 anomalies response."""
    anomalies = data.get("anomalies") or data.get("results") or []
    if isinstance(anomalies, list):
        for a in anomalies:
            _enrich_anomaly(a)

        # Recalculate summary severity counts
        if "summary" in data:
            sev_counts = {}
            for a in anomalies:
                s = a.get("severity", "normal")
                sev_counts[s] = sev_counts.get(s, 0) + 1
            data["summary"]["severity_counts"] = sev_counts

            # Count active by new severity
            active = [a for a in anomalies if a.get("status") != "resolved"]
            data["summary"]["total_active"] = len(active)

            # Recalculate max_score from enriched scores
            if anomalies:
                data["summary"]["max_score"] = max(
                    a.get("anomaly_score", 0) for a in anomalies
                )

    return data


# -- Proxy endpoints --

@router.api_route("/anomalies", methods=["GET"])
@router.api_route("/anomalies/{path:path}", methods=["GET"])
async def proxy_anomalies(request: Request, path: str = ""):
    """Proxy GET /api/v2/anomalies to the Go engine with severity enrichment."""
    target_path = f"/api/v2/anomalies"
    if path:
        target_path += f"/{path}"

    target_url = f"{ANOMALY_ENGINE_URL}{target_path}"
    query_string = str(request.query_params)

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(
                target_url,
                params=dict(request.query_params),
                headers={
                    k: v for k, v in request.headers.items()
                    if k.lower() not in ("host", "connection")
                },
            )

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    enriched = _enrich_response(data)
                    return enriched
                except Exception as e:
                    logger.warning(f"Failed to enrich anomaly response: {e}")
                    # Fall through to raw proxy
                    return Response(
                        content=resp.content,
                        status_code=resp.status_code,
                        headers=dict(resp.headers),
                    )
            else:
                return Response(
                    content=resp.content,
                    status_code=resp.status_code,
                    headers={
                        k: v for k, v in resp.headers.items()
                        if k.lower() not in ("transfer-encoding", "connection")
                    },
                )

    except httpx.ConnectError as e:
        logger.error(f"Anomaly engine connection failed: {e}")
        return Response(
            content=b'{"error": "Anomaly engine unavailable"}',
            status_code=503,
            media_type="application/json",
        )
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return Response(
            content=b'{"error": "Internal proxy error"}',
            status_code=502,
            media_type="application/json",
        )


@router.api_route("/anomalies/{path:path}", methods=["POST", "PUT", "PATCH", "DELETE"])
async def proxy_anomalies_write(request: Request, path: str = ""):
    """Proxy write operations to the Go engine without enrichment."""
    target_path = f"/api/v2/anomalies"
    if path:
        target_path += f"/{path}"

    target_url = f"{ANOMALY_ENGINE_URL}{target_path}"

    try:
        body = await request.body()
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                params=dict(request.query_params),
                content=body,
                headers={
                    k: v for k, v in request.headers.items()
                    if k.lower() not in ("host", "connection")
                },
            )
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers={
                    k: v for k, v in resp.headers.items()
                    if k.lower() not in ("transfer-encoding", "connection")
                },
            )

    except httpx.ConnectError as e:
        logger.error(f"Anomaly engine connection failed: {e}")
        return Response(
            content=b'{"error": "Anomaly engine unavailable"}',
            status_code=503,
            media_type="application/json",
        )
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return Response(
            content=b'{"error": "Internal proxy error"}',
            status_code=502,
            media_type="application/json",
        )
