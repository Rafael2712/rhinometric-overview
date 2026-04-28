import re
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import httpx
from datetime import datetime
from config import settings
from routers.auth import get_current_user
from models.user import User as UserModel

router = APIRouter()

# ---------------------------------------------------------------------------
# Internal-platform service blocklist
# Any Loki stream whose "job" label matches one of these exact names
# or whose "job" label matches the INTERNAL_PATTERN regex is silently
# stripped from the response before it reaches the customer UI.
# ---------------------------------------------------------------------------
INTERNAL_JOBS: set[str] = {
    "console-backend",
    "docker_logs",
    "rhinometric-audit",
    "varlogs",
    "grafana",
    "loki",
    "jaeger",
    "alertmanager",
    "prometheus",
    "node-exporter",
    "cadvisor",
    "ai-anomaly",
    "ai_anomaly",
}

# Catch any future container whose name starts with "rhinometric-"
INTERNAL_PATTERN = re.compile(
    r"^(rhinometric[-_]|console[-_]|grafana|loki|jaeger|alertmanager|prometheus|cadvisor|node.exporter|ai[-_]anomaly)",
    re.IGNORECASE,
)

# Loki-level exclusion regex — used to inject job!~"..." into the
# LogQL stream selector BEFORE Loki applies its limit.  This ensures
# the "limit" parameter counts only customer-visible entries.
_LOKI_INTERNAL_RE = (
    "console-backend|docker_logs|rhinometric-audit|varlogs"
    "|grafana|loki|jaeger|alertmanager|prometheus"
    "|node-exporter|cadvisor|ai-anomaly|ai_anomaly"
    "|rhinometric[-_].*|console[-_].*"
)


def _inject_internal_exclusion(query: str) -> str:
    """Add ``job!~"<internal>"`` to the LogQL stream selector.

    Without this, Loki applies the *limit* to ALL streams (including
    high-volume internal ones).  The post-query ``_is_internal_stream``
    filter then removes them, potentially leaving zero results even
    though customer logs exist.
    """
    idx = query.find("}")
    if idx == -1:
        return query                       # not a valid selector
    # Determine separator – empty selector "{}" vs non-empty "{job=~…}"
    before = query[1:idx].strip()
    sep = ", " if before else ""
    return query[:idx] + sep + f'job!~"{_LOKI_INTERNAL_RE}"' + query[idx:]


def _is_internal_stream(stream_labels: dict) -> bool:
    """Return True if the stream belongs to internal platform telemetry."""
    job = stream_labels.get("job", "")
    service = stream_labels.get("service_name", "") or stream_labels.get("service", "")
    container = stream_labels.get("container", "")

    for val in (job, service, container):
        if not val:
            continue
        if val.lower() in INTERNAL_JOBS:
            return True
        if INTERNAL_PATTERN.search(val):
            return True
    return False


@router.get("")
async def get_logs(
    query: str = Query(..., description="LogQL query"),
    limit: int = Query(100, description="Maximum number of log lines"),
    start: str = Query(..., description="Start time in nanoseconds"),
    end: str = Query(..., description="End time in nanoseconds"),
    direction: str = Query("backward", description="Query direction: forward or backward"),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Proxy logs from Loki, filtering out internal platform streams.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "query": _inject_internal_exclusion(query),
                "limit": limit,
                "start": start,
                "end": end,
                "direction": direction,
            }

            loki_url = f"{settings.LOKI_URL}/loki/api/v1/query_range"
            response = await client.get(loki_url, params=params)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Loki returned error: {response.text}",
                )

            payload = response.json()

            # ---- Filter out internal platform streams ----
            result_list = payload.get("data", {}).get("result", [])
            filtered = [
                entry for entry in result_list
                if not _is_internal_stream(entry.get("stream", {}))
            ]
            payload.setdefault("data", {})["result"] = filtered

            return payload

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Loki request timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Cannot connect to Loki: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
