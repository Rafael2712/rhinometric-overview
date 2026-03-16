"""
Service Summary Aggregation Service

Aggregates health data from BOTH external monitored services
and internal platform services to produce a unified health overview.

Used by: GET /api/services/summary
"""

import logging
from typing import Dict, Any

import httpx
from sqlalchemy.orm import Session

from config import settings
from models.external_service import ExternalService, ServiceStatus

logger = logging.getLogger("rhinometric.service_summary")

# Platform jobs that represent internal infrastructure services.
# Mirrors the canonical set from kpis.py — do NOT duplicate logic,
# just reference the same classification.
PLATFORM_JOBS = {
    "prometheus", "grafana", "loki", "jaeger", "alertmanager",
    "otel-collector", "console-backend", "license-server-v2",
    "ai-anomaly", "postgres", "redis", "promtail",
}

INFRA_JOBS = {
    "node-exporter", "cadvisor", "blackbox-exporter",
}

INTERNAL_PROBE_JOBS = {
    "blackbox-http",
}

ALL_INTERNAL_JOBS = PLATFORM_JOBS | INFRA_JOBS | INTERNAL_PROBE_JOBS


async def _fetch_prometheus_up_targets() -> Dict[str, Any]:
    """
    Query Prometheus `up` metric to get all scrape targets and their status.
    Returns dict with 'internal' and 'prom_external' counts.
    Timeout: 5 seconds max.
    """
    internal_up = 0
    internal_down = 0
    prom_external_up = 0
    prom_external_down = 0

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.PROMETHEUS_URL}/api/v1/query",
                params={"query": "up"},
            )
            data = resp.json()

            if data.get("status") == "success":
                for result in data.get("data", {}).get("result", []):
                    job = result.get("metric", {}).get("job", "unknown")
                    is_up = result.get("value", [None, "0"])[1] == "1"

                    if job in ALL_INTERNAL_JOBS:
                        if is_up:
                            internal_up += 1
                        else:
                            internal_down += 1
                    else:
                        # Prometheus-scraped external targets
                        if is_up:
                            prom_external_up += 1
                        else:
                            prom_external_down += 1

    except Exception as e:
        logger.warning(f"Prometheus query failed: {e}")

    return {
        "internal_up": internal_up,
        "internal_down": internal_down,
        "prom_external_up": prom_external_up,
        "prom_external_down": prom_external_down,
    }


def _fetch_external_services_from_db(db: Session) -> Dict[str, int]:
    """
    Query PostgreSQL for registered external service statuses.
    Only counts enabled services.
    """
    try:
        enabled = db.query(ExternalService).filter(
            ExternalService.enabled == True
        ).all()

        up = sum(1 for s in enabled if s.status == ServiceStatus.UP)
        down = sum(1 for s in enabled if s.status == ServiceStatus.DOWN)
        degraded = sum(1 for s in enabled if s.status == ServiceStatus.DEGRADED)
        unknown = sum(
            1 for s in enabled
            if s.status in (ServiceStatus.UNKNOWN, ServiceStatus.ERROR)
        )

        return {
            "total": len(enabled),
            "up": up,
            "down": down,
            "degraded": degraded,
            "unknown": unknown,
        }
    except Exception as e:
        logger.warning(f"External services DB query failed: {e}")
        return {"total": 0, "up": 0, "down": 0, "degraded": 0, "unknown": 0}


def _calculate_overall_status(
    healthy: int,
    degraded: int,
    down: int,
    total: int,
    has_latency_anomalies: bool = False,
) -> str:
    """
    Determine the global platform health status.

    Rules (in priority order):
      1. >10% of services DOWN  → CRITICAL
      2. ANY service DOWN       → DEGRADED
      3. Latency anomalies exist → DEGRADED
      4. Everything healthy      → OPERATIONAL
    """
    if total == 0:
        return "OPERATIONAL"

    down_pct = down / total

    if down_pct > 0.10:
        return "CRITICAL"

    if down > 0:
        return "DEGRADED"

    if has_latency_anomalies:
        return "DEGRADED"

    return "OPERATIONAL"


async def _check_latency_anomalies() -> bool:
    """
    Quick check against the AI anomaly service for active latency-related
    anomaly groups.  Returns True only when significant anomalies exist.

    Filters:
      - status must be "active"
      - metric must contain "latency"
      - severity must be "high" or "critical" (ignore low/medium noise)

    Timeout: 3 seconds — this is a best-effort enrichment.
    """
    SIGNIFICANT_SEVERITIES = {"high", "critical"}
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                f"{settings.AI_ANOMALY_URL}/anomalies",
                params={"limit": 50},
            )
            if resp.status_code == 200:
                data = resp.json()
                anomalies = data.get("anomalies", [])
                for a in anomalies:
                    metric = a.get("metric_name", "") or a.get("metric", "")
                    status = a.get("status", "")
                    severity = (a.get("severity", "") or "").lower()
                    if (
                        status == "active"
                        and "latency" in metric.lower()
                        and severity in SIGNIFICANT_SEVERITIES
                    ):
                        return True
    except Exception as e:
        logger.debug(f"Latency anomaly check skipped: {e}")

    return False


async def get_services_summary(db: Session) -> Dict[str, Any]:
    """
    Main aggregation function.

    Combines:
      - Internal platform services (from Prometheus `up` metric)
      - External monitored services (from PostgreSQL external_services table)

    Returns a flat summary dict ready for JSON response.
    """

    # --- Parallel-ish data collection ---
    prom_data = await _fetch_prometheus_up_targets()
    ext_data = _fetch_external_services_from_db(db)
    has_latency = await _check_latency_anomalies()

    # --- Internal (platform) services ---
    internal_total = prom_data["internal_up"] + prom_data["internal_down"]
    internal_healthy = prom_data["internal_up"]
    internal_down = prom_data["internal_down"]

    # --- External services (DB-registered + Prometheus-scraped external) ---
    # DB-registered externals
    ext_healthy = ext_data["up"]
    ext_degraded = ext_data["degraded"]
    ext_down = ext_data["down"]
    ext_total = ext_data["total"]

    # Prometheus-scraped external targets (not in DB)
    prom_ext_up = prom_data["prom_external_up"]
    prom_ext_down = prom_data["prom_external_down"]

    # Combined external counts
    all_ext_total = ext_total + prom_ext_up + prom_ext_down
    all_ext_healthy = ext_healthy + prom_ext_up
    all_ext_degraded = ext_degraded
    all_ext_down = ext_down + prom_ext_down

    # --- Grand totals ---
    total_services = internal_total + all_ext_total
    total_healthy = internal_healthy + all_ext_healthy
    total_degraded = all_ext_degraded  # internal services are only up/down
    total_down = internal_down + all_ext_down

    overall_status = _calculate_overall_status(
        healthy=total_healthy,
        degraded=total_degraded,
        down=total_down,
        total=total_services,
        has_latency_anomalies=has_latency,
    )

    return {
        "total_services": total_services,
        "external_services": all_ext_total,
        "internal_services": internal_total,
        "healthy": total_healthy,
        "degraded": total_degraded,
        "down": total_down,
        "overall_status": overall_status,
    }
