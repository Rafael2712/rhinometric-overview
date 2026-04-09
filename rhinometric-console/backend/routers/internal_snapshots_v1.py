"""
Internal signal assembler endpoint for the Anomaly Engine V1.

GET /internal/anomaly-signal-snapshots-v1

Assembles 18 signals per service from 4 data sources:
  - PostgreSQL (sync SQLAlchemy): service metadata, incidents, baselines, latency trend
  - Prometheus (httpx): health_score, ssl_expiry_days, is_up
  - Loki (httpx): log_error_count_1h, log_warn_count_1h, log_error_burst_ratio
  - Jaeger (httpx): trace_p95_latency_ms, trace_error_rate, trace_bottleneck_score, trace_slow_operations

V1.3: Added latency_trend_slope, latency_trend_r2, log_error_burst_ratio
V1.4: Added trace-based signals (Jaeger integration)

Target: < 500ms total assembly time.
"""

import time
import logging
from typing import List, Dict, Optional
from collections import defaultdict

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ──
PROMETHEUS_URL = "http://prometheus:9090"
LOKI_URL = "http://loki:3100"
JAEGER_URL = "http://jaeger:16686"
HTTP_TIMEOUT = 5.0

# Internal infrastructure services — excluded from Jaeger trace queries.
# NOTE: "rhinometric" alone is too broad (catches rhinometric-web).
#        Use specific prefixes for actual infra components.
_INTERNAL_PREFIXES = (
    "rhinometric-console", "rhinometric-ai", "rhinometric-anomaly",
    "console-", "grafana", "loki", "jaeger",
    "alertmanager", "prometheus", "node-exporter", "cadvisor",
)


def _prom_query_by_id(client: httpx.Client, query: str) -> Dict[int, float]:
    """Execute a PromQL instant query, keyed by service_id label."""
    try:
        resp = client.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query},
            timeout=HTTP_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                result = {}
                for r in data.get("data", {}).get("result", []):
                    sid = r["metric"].get("service_id")
                    if sid is not None:
                        result[int(sid)] = float(r["value"][1])
                return result
    except Exception as e:
        logger.warning(f"Prometheus query failed: {query[:80]}... → {e}")
    return {}


def _loki_count(client: httpx.Client, query: str) -> Dict[str, int]:
    """Execute a LogQL count query."""
    try:
        resp = client.get(
            f"{LOKI_URL}/loki/api/v1/query",
            params={"query": query},
            timeout=HTTP_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                return {
                    r["metric"].get("service_name", r["metric"].get("service_key", "unknown")):
                        int(float(r["value"][1]))
                    for r in data.get("data", {}).get("result", [])
                }
    except Exception as e:
        logger.warning(f"Loki query failed: {query[:80]}... → {e}")
    return {}


def _compute_latency_trend(points: List[float]) -> dict:
    """
    Compute linear regression slope and R-squared from a list of latency values.
    Same approach as ai_analyzer._analyze_trend().
    Returns {"slope": float, "r2": float} or defaults on failure.
    """
    n = len(points)
    if n < 5:
        return {"slope": 0.0, "r2": 0.0}
    try:
        x_vals = list(range(n))
        sum_x = sum(x_vals)
        sum_y = sum(points)
        sum_xy = sum(x * y for x, y in zip(x_vals, points))
        sum_x2 = sum(x * x for x in x_vals)
        mean_y = sum_y / n

        denom = n * sum_x2 - sum_x * sum_x
        if denom == 0:
            return {"slope": 0.0, "r2": 0.0}

        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n

        ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(x_vals, points))
        ss_tot = sum((y - mean_y) ** 2 for y in points)

        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        r2 = max(0.0, min(1.0, r2))

        return {"slope": round(slope, 4), "r2": round(r2, 4)}
    except Exception as e:
        logger.warning(f"Trend computation failed: {e}")
        return {"slope": 0.0, "r2": 0.0}


def _extract_service_id_from_trace(trace: dict) -> Optional[int]:
    """Extract rhinometric.service_id from any span tag in a trace."""
    for span in trace.get("spans", []):
        for tag in span.get("tags", []):
            if tag.get("key") == "rhinometric.service_id":
                try:
                    return int(tag["value"])
                except (ValueError, TypeError):
                    continue
    return None


def _compute_trace_signals(traces: list) -> dict:
    """Compute trace anomaly signals from a list of Jaeger traces."""
    trace_durations_ms = []
    total_spans = 0
    error_spans = 0
    bottleneck_scores = []
    slow_ops = 0

    for trace in traces:
        spans = trace.get("spans", [])
        if not spans:
            continue

        span_starts = []
        span_ends = []
        max_span_duration = 0
        # V1.4b: track child (non-root) durations for bottleneck normalization
        span_id_set = {s["spanID"] for s in spans}
        child_durations_us = []

        for span in spans:
            dur = span.get("duration", 0)  # microseconds
            st = span.get("startTime", 0)
            span_starts.append(st)
            span_ends.append(st + dur)
            total_spans += 1

            if dur > max_span_duration:
                max_span_duration = dur

            # V1.4b: classify root vs child span for bottleneck
            refs = span.get("references", [])
            is_child = any(
                r.get("refType") == "CHILD_OF" and r.get("spanID") in span_id_set
                for r in refs
            )
            if is_child:
                child_durations_us.append(dur)

            # Check for error span
            is_error = False
            for tag in span.get("tags", []):
                if tag.get("key") == "otel.status_code" and tag.get("value") not in ("OK", "UNSET", 0):
                    is_error = True
                    break
                if tag.get("key") == "http.status_code" and isinstance(tag.get("value"), (int, float)) and tag["value"] >= 400:
                    is_error = True
                    break
                if tag.get("key") == "error" and tag.get("value") in (True, "true"):
                    is_error = True
                    break
            if is_error:
                error_spans += 1

        if span_starts and span_ends:
            trace_duration_us = max(span_ends) - min(span_starts)
            trace_duration_ms = trace_duration_us / 1000.0
            trace_durations_ms.append(trace_duration_ms)

            # V1.4b: bottleneck = non-root child dominance × complexity factor
            # Root span trivially wraps all children so we exclude it.
            # Complexity factor dampens simple traces (≤5 children = normal).
            if trace_duration_us > 0 and child_durations_us:
                child_dominance = max(child_durations_us) / trace_duration_us
                complexity = min(1.0, len(child_durations_us) / 5.0)
                bottleneck_scores.append(round(child_dominance * complexity, 4))
            elif trace_duration_us > 0:
                # Single-span trace (root only) → no bottleneck
                bottleneck_scores.append(0.0)

            # Slow operations: trace duration > 2000ms threshold
            if trace_duration_ms > 2000:
                slow_ops += 1

    # P95 latency
    p95_latency = 0.0
    if trace_durations_ms:
        sorted_durations = sorted(trace_durations_ms)
        idx = int(len(sorted_durations) * 0.95)
        idx = min(idx, len(sorted_durations) - 1)
        p95_latency = round(sorted_durations[idx], 2)

    # Error rate
    error_rate = round(error_spans / total_spans, 4) if total_spans > 0 else 0.0

    # Avg bottleneck score
    avg_bottleneck = 0.0
    if bottleneck_scores:
        avg_bottleneck = round(sum(bottleneck_scores) / len(bottleneck_scores), 4)

    return {
        "trace_p95_latency_ms": p95_latency,
        "trace_error_rate": error_rate,
        "trace_bottleneck_score": avg_bottleneck,
        "trace_slow_operations": slow_ops,
    }


def _fetch_jaeger_trace_signals(
    client: httpx.Client, snapshot_service_ids: List[int]
) -> Dict[int, dict]:
    """
    Batch-fetch trace signals from Jaeger, mapped by rhinometric.service_id tag.
    Returns {service_id: {trace_p95_latency_ms, trace_error_rate,
                          trace_bottleneck_score, trace_slow_operations}}.

    Strategy:
      1. GET /api/services  → discover Jaeger service names   (1 call)
      2. Filter out internal infrastructure services
      3. GET /api/traces per non-internal Jaeger service       (N calls)
      4. Extract rhinometric.service_id tag → group traces by service_id
      5. Compute signals only for IDs present in snapshot_service_ids

    Fails safely: returns empty dict on any error.
    """
    result: Dict[int, dict] = {}

    if not snapshot_service_ids:
        return result

    snapshot_id_set = set(snapshot_service_ids)

    try:
        # Step 1: Discover Jaeger services
        svc_resp = client.get(
            f"{JAEGER_URL}/api/services", timeout=HTTP_TIMEOUT
        )
        if svc_resp.status_code != 200:
            logger.warning(f"Jaeger /api/services returned {svc_resp.status_code}")
            return result
        jaeger_services = svc_resp.json().get("data", [])
    except Exception as e:
        logger.warning(f"Jaeger services fetch failed: {e}")
        return result

    # Step 2: Filter out internal infrastructure
    customer_jaeger_svcs = [
        s for s in jaeger_services
        if not any(s.lower().startswith(p) for p in _INTERNAL_PREFIXES)
    ]

    if not customer_jaeger_svcs:
        logger.warning(
            f"Trace mapping: 0 non-internal Jaeger services "
            f"(total Jaeger: {len(jaeger_services)})"
        )
        return result

    # Step 3: Fetch traces for all customer Jaeger services,
    #         group by rhinometric.service_id tag
    end_us = int(time.time() * 1_000_000)
    start_us = end_us - 3600 * 1_000_000

    traces_by_sid: Dict[int, list] = defaultdict(list)

    for jaeger_svc in customer_jaeger_svcs:
        try:
            resp = client.get(
                f"{JAEGER_URL}/api/traces",
                params={
                    "service": jaeger_svc,
                    "start": str(start_us),
                    "end": str(end_us),
                    "limit": "100",
                },
                timeout=HTTP_TIMEOUT,
            )
            if resp.status_code != 200:
                continue

            for trace in resp.json().get("data", []):
                sid = _extract_service_id_from_trace(trace)
                if sid is not None and sid in snapshot_id_set:
                    traces_by_sid[sid].append(trace)
        except Exception as e:
            logger.warning(f"Jaeger trace fetch failed for {jaeger_svc}: {e}")
            continue

    # Step 4: Compute signals per service_id
    for sid, traces in traces_by_sid.items():
        result[sid] = _compute_trace_signals(traces)

    # Mandatory logging
    mapped = len(result)
    total = len(snapshot_service_ids)
    if total > 0 and mapped == 0:
        logger.warning(
            "Trace mapping failed — no services matched Jaeger traces. "
            f"Snapshot IDs: {snapshot_service_ids}, "
            f"Jaeger services queried: {customer_jaeger_svcs}"
        )
    else:
        logger.info(
            f"Trace mapping: {mapped}/{total} services mapped "
            f"from {len(customer_jaeger_svcs)} Jaeger services"
        )

    return result


@router.get("/internal/anomaly-signal-snapshots-v1")
def get_signal_snapshots(db: Session = Depends(get_db)):
    """
    Assemble signal snapshots for all active external services.
    Called by the Rust anomaly engine every 60 seconds.
    """
    start = time.monotonic()
    warnings: List[str] = []

    # ── Step 1: Get active services from PostgreSQL ──
    try:
        rows = db.execute(text("""
            SELECT
                id,
                name,
                COALESCE(service_type::text, 'http') as service_type,
                COALESCE(group_name, 'Default') as group_name,
                COALESCE(environment, 'production') as environment,
                COALESCE(check_interval_seconds, 15) as check_interval_seconds,
                COALESCE(consecutive_failures, 0) as consecutive_failures,
                COALESCE(last_response_time_ms, 0) as last_response_time_ms,
                status::text as status
            FROM external_services
            WHERE enabled = true
            ORDER BY id
        """)).fetchall()

        services = [dict(r._mapping) for r in rows]
    except Exception as e:
        logger.error(f"Failed to fetch services: {e}")
        return {
            "snapshots": [],
            "assembled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "assembly_duration_ms": 0,
            "warnings": [f"Database error: {str(e)}"],
        }

    if not services:
        return {
            "snapshots": [],
            "assembled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "assembly_duration_ms": 0,
            "warnings": ["No active services found"],
        }

    # ── Step 2: PostgreSQL baseline + checks + incidents ──
    try:
        baseline_rows = db.execute(text("""
            SELECT
                service_id,
                AVG(response_time_ms) as avg_ms,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_ms,
                COUNT(*) as check_count,
                EXTRACT(EPOCH FROM (NOW() - MIN(checked_at))) / 3600.0 as age_hours
            FROM external_service_checks
            WHERE checked_at > NOW() - INTERVAL '24 hours'
              AND response_time_ms IS NOT NULL
              AND response_time_ms > 0
            GROUP BY service_id
        """)).fetchall()
        baselines_map = {
            r.service_id: {
                "baseline_ms": float(r.avg_ms or 0),
                "p95_ms": float(r.p95_ms or 0),
                "age_hours": float(r.age_hours or 0),
            }
            for r in baseline_rows
        }
    except Exception as e:
        warnings.append(f"baselines query failed: {e}")
        baselines_map = {}

    try:
        checks_rows = db.execute(text("""
            SELECT
                service_id,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status_code >= 400 OR status = 'error') as errors
            FROM external_service_checks
            WHERE checked_at > NOW() - INTERVAL '1 hour'
            GROUP BY service_id
        """)).fetchall()
        checks_1h_map = {
            r.service_id: {"total": int(r.total), "errors": int(r.errors)}
            for r in checks_rows
        }
    except Exception as e:
        warnings.append(f"checks_1h query failed: {e}")
        checks_1h_map = {}

    try:
        incident_rows = db.execute(text("""
            SELECT entity_name, COUNT(*) as cnt
            FROM incidents
            WHERE created_at > NOW() - INTERVAL '24 hours'
            GROUP BY entity_name
        """)).fetchall()
        incidents_map = {r.entity_name: int(r.cnt) for r in incident_rows}
    except Exception as e:
        warnings.append(f"incidents query failed: {e}")
        incidents_map = {}

    # ── Step 2b: Latency trend data (V1.3) ──
    # Fetch last ~50 latency points per service (last 1h) in a single batched query
    latency_trend_map: Dict[int, dict] = {}
    try:
        trend_rows = db.execute(text("""
            SELECT service_id, response_time_ms
            FROM external_service_checks
            WHERE checked_at > NOW() - INTERVAL '1 hour'
              AND response_time_ms IS NOT NULL
              AND response_time_ms > 0
            ORDER BY service_id, checked_at ASC
        """)).fetchall()

        service_latencies: Dict[int, List[float]] = defaultdict(list)
        for row in trend_rows:
            service_latencies[row.service_id].append(float(row.response_time_ms))

        for sid, points in service_latencies.items():
            latency_trend_map[sid] = _compute_latency_trend(points)
    except Exception as e:
        warnings.append(f"latency trend query failed: {e}")

    # ── Step 3: Prometheus + Loki queries (sync httpx) ──
    prom_results: Dict[str, Dict[int, float]] = {}
    loki_results: Dict[str, Dict[str, int]] = {}

    with httpx.Client() as client:
        prom_results["health_score"] = _prom_query_by_id(
            client, "rhinometric_service_health_score"
        )
        prom_results["ssl_expiry_days"] = _prom_query_by_id(
            client, "rhinometric_service_ssl_expiry_days"
        )
        prom_results["is_up"] = _prom_query_by_id(
            client, "rhinometric_service_up"
        )

        loki_results["log_errors"] = _loki_count(
            client,
            'sum by (service_name) (count_over_time({service_name=~".+", level=~"error|ERROR"}[1h]))',
        )
        loki_results["log_warns"] = _loki_count(
            client,
            'sum by (service_name) (count_over_time({service_name=~".+", level=~"warn|WARNING"}[1h]))',
        )

        # V1.3: Batched 5-minute error count for burst detection
        loki_results["log_errors_5m"] = _loki_count(
            client,
            'sum by (service_name) (count_over_time({service_name=~".+", level=~"error|ERROR"}[5m]))',
        )

        # V1.4: Jaeger trace signals (batch by service_id, fail-safe)
        snapshot_service_ids = [svc["id"] for svc in services]
        jaeger_signals = _fetch_jaeger_trace_signals(client, snapshot_service_ids)

    # ── Step 4: Assemble snapshots ──
    now_ms = int(time.time() * 1000)
    snapshots = []

    for svc in services:
        sid = svc["id"]
        svc_name = svc["name"]
        baseline_data = baselines_map.get(sid, {})
        checks_data = checks_1h_map.get(sid, {})

        signals_available = []

        # Prometheus signals
        health = prom_results.get("health_score", {}).get(sid)
        ssl_days = prom_results.get("ssl_expiry_days", {}).get(sid)
        is_up_val = prom_results.get("is_up", {}).get(sid)

        if is_up_val is not None:
            is_up = is_up_val >= 1.0
            signals_available.append("is_up")
        else:
            is_up = svc["status"] not in ("down", "error", "critical")

        if health is not None:
            signals_available.append("health_score")
        else:
            health = 100.0

        if ssl_days is not None:
            signals_available.append("ssl_expiry_days")
        else:
            ssl_days = 365.0

        # Latency
        latency_current = float(svc["last_response_time_ms"] or 0)
        if latency_current > 0:
            signals_available.append("latency_current_ms")

        # Baselines
        baseline_ms = baseline_data.get("baseline_ms", 0)
        p95_ms = baseline_data.get("p95_ms", 0)
        age_hours = baseline_data.get("age_hours", 0)
        if baseline_ms > 0:
            signals_available.append("latency_baseline_ms")

        # Checks
        checks_total = checks_data.get("total", 0)
        checks_errors = checks_data.get("errors", 0)
        error_rate = checks_errors / checks_total if checks_total > 0 else 0.0

        # Loki
        log_errors = loki_results.get("log_errors", {}).get(svc_name, 0)
        log_warns = loki_results.get("log_warns", {}).get(svc_name, 0)
        if log_errors > 0 or log_warns > 0:
            signals_available.append("log_counts")

        # Incidents
        incidents_24h = incidents_map.get(svc_name, 0)

        # V1.3: Latency trend
        trend_data = latency_trend_map.get(sid, {"slope": 0.0, "r2": 0.0})
        latency_trend_slope = trend_data["slope"]
        latency_trend_r2 = trend_data["r2"]
        if latency_trend_r2 > 0.3:
            signals_available.append("latency_trend")

        # V1.3: Log error burst ratio
        log_errors_5m = loki_results.get("log_errors_5m", {}).get(svc_name, 0)
        if log_errors > 0:
            expected_5m = log_errors / 12.0
            log_error_burst_ratio = round(log_errors_5m / expected_5m, 2) if expected_5m > 0 else 0.0
        else:
            log_error_burst_ratio = 0.0
        if log_error_burst_ratio > 1.5:
            signals_available.append("log_error_burst")

        # V1.4: Trace signals (keyed by service_id)
        trace_data = jaeger_signals.get(sid, {})
        trace_p95 = trace_data.get("trace_p95_latency_ms", 0.0)
        trace_err_rate = trace_data.get("trace_error_rate", 0.0)
        trace_bottleneck = trace_data.get("trace_bottleneck_score", 0.0)
        trace_slow_ops = trace_data.get("trace_slow_operations", 0)
        if trace_p95 > 0 or trace_err_rate > 0 or trace_bottleneck > 0 or trace_slow_ops > 0:
            signals_available.append("jaeger_traces")

        snapshot = {
            "service_name": svc_name,
            "service_id": sid,
            "service_type": svc["service_type"],
            "group_name": svc["group_name"],
            "environment": svc["environment"],
            "timestamp_ms": now_ms,
            "check_interval_seconds": svc["check_interval_seconds"],
            "latency_current_ms": latency_current,
            "latency_baseline_ms": baseline_ms,
            "latency_p95_ms": p95_ms,
            "is_up": is_up,
            "health_score": health,
            "consecutive_failures": svc["consecutive_failures"],
            "incidents_24h": incidents_24h,
            "error_rate_1h": round(error_rate, 4),
            "log_error_count_1h": log_errors,
            "log_warn_count_1h": log_warns,
            "ssl_expiry_days": ssl_days,
            "baseline_age_hours": round(age_hours, 2),
            "checks_in_last_1h": checks_total,
            "signals_available": signals_available,
            # V1.3 signals
            "latency_trend_slope": latency_trend_slope,
            "latency_trend_r2": latency_trend_r2,
            "log_error_burst_ratio": log_error_burst_ratio,
            # V1.4 trace signals
            "trace_p95_latency_ms": trace_p95,
            "trace_error_rate": trace_err_rate,
            "trace_bottleneck_score": trace_bottleneck,
            "trace_slow_operations": trace_slow_ops,
        }
        snapshots.append(snapshot)

    elapsed_ms = round((time.monotonic() - start) * 1000, 1)

    logger.info(
        f"Signal assembly: {len(snapshots)} services, "
        f"{elapsed_ms}ms, {len(warnings)} warnings"
    )

    return {
        "snapshots": snapshots,
        "assembled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "assembly_duration_ms": elapsed_ms,
        "warnings": warnings,
    }
