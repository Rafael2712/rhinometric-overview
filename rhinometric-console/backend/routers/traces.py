import re
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import httpx
from datetime import datetime, timedelta

from config import settings
from routers.auth import get_current_user
from models.user import User as UserModel

router = APIRouter()

# ---------------------------------------------------------------------------
# Internal-platform service blocklist  (mirrors the Logs filter)
# ---------------------------------------------------------------------------
INTERNAL_SERVICES: set[str] = {
    "rhinometric-console-backend",
    "rhinometric-console-frontend",
    "rhinometric-nginx",
    "rhinometric-grafana",
    "rhinometric-loki",
    "rhinometric-jaeger",
    "rhinometric-alertmanager",
    "rhinometric-prometheus",
    "console-backend",
    "console-frontend",
    "grafana",
    "loki",
    "jaeger",
    "jaeger-all-in-one",
    "jaeger-query",
    "jaeger-collector",
    "alertmanager",
    "prometheus",
    "node-exporter",
    "cadvisor",
    "ai-anomaly",
    "ai_anomaly",
}

INTERNAL_PATTERN = re.compile(
    r"^(rhinometric[-_]|console[-_]|grafana|loki|jaeger|alertmanager|prometheus|cadvisor|node.exporter|ai[-_]anomaly)",
    re.IGNORECASE,
)


def _is_internal_service(name: str) -> bool:
    if not name:
        return True
    if name.lower() in INTERNAL_SERVICES:
        return True
    if INTERNAL_PATTERN.search(name):
        return True
    return False


def parse_lookback(lookback: str) -> timedelta:
    """Convert lookback string (e.g., '1h', '30m') to timedelta"""
    if not lookback:
        return timedelta(hours=1)
    unit = lookback[-1]
    try:
        value = int(lookback[:-1])
    except ValueError:
        return timedelta(hours=1)
    if unit == "m":
        return timedelta(minutes=value)
    elif unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)
    return timedelta(hours=1)


@router.get("")
async def get_traces(
    limit: int = Query(50, description="Maximum number of traces"),
    lookback: str = Query("1h", description="Time range to look back"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    minDuration: Optional[str] = Query(None, description="Minimum duration filter"),
    start: Optional[int] = Query(None, description="Absolute start time in microseconds"),
    end: Optional[int] = Query(None, description="Absolute end time in microseconds"),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Proxy traces from Jaeger, excluding internal platform services.

    Supports two time modes:
      1. Relative: ?lookback=1h  (default)
      2. Absolute: ?start=<µs>&end=<µs>  (overrides lookback when both provided)
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # --- Determine time window ---
            if start is not None and end is not None:
                # Absolute timestamps provided by frontend
                start_us = start
                end_us = end
            else:
                # Relative lookback (existing behaviour)
                lookback_delta = parse_lookback(lookback)
                end_time = datetime.now()
                start_time = end_time - lookback_delta
                start_us = int(start_time.timestamp() * 1_000_000)
                end_us = int(end_time.timestamp() * 1_000_000)

            params: dict = {
                "start": start_us,
                "end": end_us,
                "limit": limit,
            }
            if minDuration:
                try:
                    duration_ms = int(minDuration.replace("ms", ""))
                    params["minDuration"] = f"{duration_ms * 1000}us"
                except Exception:
                    pass

            # ----- Specific service requested -----
            if service and service != "all":
                if _is_internal_service(service):
                    return {"traces": [], "total": 0}
                params["service"] = service
                jaeger_url = f"{settings.JAEGER_URL}/api/traces"
                try:
                    response = await client.get(jaeger_url, params=params)
                except httpx.ConnectError:
                    return {"traces": [], "error": "Jaeger unreachable"}
                if response.status_code != 200:
                    return {"traces": [], "error": f"Jaeger returned status {response.status_code}"}
                jaeger_data = response.json()
                traces = jaeger_data.get("data", [])
                return {"traces": traces, "total": len(traces)}

            # ----- All services (excluding internal) -----
            services_url = f"{settings.JAEGER_URL}/api/services"
            try:
                services_response = await client.get(services_url)
            except httpx.ConnectError:
                return {"traces": [], "error": "Jaeger unreachable"}

            if services_response.status_code != 200:
                return {"traces": [], "error": "Could not fetch services list"}

            available = services_response.json().get("data", [])
            customer_services = [s for s in available if not _is_internal_service(s)]

            if not customer_services:
                return {"traces": [], "total": 0}

            all_traces: list = []
            for svc in customer_services:
                svc_params = {**params, "service": svc}
                try:
                    resp = await client.get(f"{settings.JAEGER_URL}/api/traces", params=svc_params)
                    if resp.status_code == 200:
                        all_traces.extend(resp.json().get("data", []))
                except Exception:
                    continue

            all_traces.sort(
                key=lambda t: t.get("spans", [{}])[0].get("startTime", 0),
                reverse=True,
            )
            all_traces = all_traces[:limit]
            return {"traces": all_traces, "total": len(all_traces)}

    except httpx.TimeoutException:
        return {"traces": [], "error": "Jaeger request timeout"}
    except httpx.RequestError as e:
        return {"traces": [], "error": f"Jaeger not available: {str(e)}"}
    except Exception as e:
        return {"traces": [], "error": f"Internal error: {str(e)}"}


@router.get("/services")
async def get_services(current_user: UserModel = Depends(get_current_user)):
    """
    Return only customer-facing services from Jaeger (internal platform excluded).
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            services_url = f"{settings.JAEGER_URL}/api/services"
            try:
                response = await client.get(services_url)
            except httpx.ConnectError:
                return {"services": [], "error": "Jaeger unreachable"}

            if response.status_code != 200:
                return {"services": [], "error": f"Jaeger returned status {response.status_code}"}

            data = response.json()
            all_services = data.get("data", [])
            customer_services = [s for s in all_services if not _is_internal_service(s)]

            return {"services": customer_services, "total": len(customer_services)}
    except Exception as e:
        return {"services": [], "error": f"Internal error: {str(e)}"}
