"""
Internal signal assembler endpoint for the Anomaly Engine V1.

GET /internal/anomaly-signal-snapshots-v1

Assembles 11 signals per service from 3 data sources:
  - PostgreSQL (sync SQLAlchemy): service metadata, incidents, baselines (computed from checks)
  - Prometheus (httpx): health_score, ssl_expiry_days, is_up
  - Loki (httpx): log_error_count_1h, log_warn_count_1h

Target: < 500ms total assembly time.
"""

import time
import logging
from typing import List, Dict

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
HTTP_TIMEOUT = 5.0


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
                COALESCE(check_interval_seconds, 60) as check_interval_seconds,
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
            'sum by (service_name) (count_over_time({job="rhinometric"} | json | level="error" [1h]))',
        )
        loki_results["log_warns"] = _loki_count(
            client,
            'sum by (service_name) (count_over_time({job="rhinometric"} | json | level="warn" [1h]))',
        )

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
