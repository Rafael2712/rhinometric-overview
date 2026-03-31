import re
import time
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
import httpx
from datetime import datetime
from config import settings
from routers.auth import get_current_user
from models.user import User as UserModel
from database import get_db
from models.external_service import ExternalService

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Service type taxonomy
# ---------------------------------------------------------------------------
SERVICE_TYPE_VALUES = {"http_api", "web_app", "database_postgres", "collector", "unknown"}

# Map DB catalog_type -> our taxonomy
_CATALOG_TYPE_MAP: Dict[str, str] = {
    "WEB_APP": "web_app",
    "REST_API": "http_api",
    "EXTERNAL_SERVICE": "http_api",
    "DATABASE": "database_postgres",
}

# Map DB service_type (enum) -> our taxonomy (fallback)
_DB_SERVICE_TYPE_MAP: Dict[str, str] = {
    "HTTP": "http_api",
    "POSTGRESQL": "database_postgres",
}

# Heuristic patterns for job names when DB lookup fails
_JOB_HEURISTICS: List[tuple] = [
    (re.compile(r"collector", re.IGNORECASE), "collector"),
    (re.compile(r"postgres|pg[-_]", re.IGNORECASE), "database_postgres"),
    (re.compile(r"web[-_]|frontend|www|site", re.IGNORECASE), "web_app"),
    (re.compile(r"api[-_]|backend|rest[-_]|http[-_]", re.IGNORECASE), "http_api"),
]

# Cache: service_key -> service_type (refreshed periodically)
_service_type_cache: Dict[str, str] = {}
_cache_ts: float = 0.0
_CACHE_TTL: float = 300.0  # 5 minutes


def _refresh_service_type_cache() -> None:
    """Load service_key -> service_type mapping from external_services table."""
    global _service_type_cache, _cache_ts
    try:
        db = next(get_db())
        try:
            rows = (
                db.query(
                    ExternalService.telemetry_service_key,
                    ExternalService.catalog_type,
                    ExternalService.service_type,
                )
                .filter(
                    ExternalService.telemetry_service_key.isnot(None),
                    ExternalService.telemetry_service_key != "",
                )
                .all()
            )
            new_cache: Dict[str, str] = {}
            for skey, cat_type, svc_type in rows:
                # Priority: catalog_type > service_type > unknown
                resolved = "unknown"
                if cat_type and cat_type in _CATALOG_TYPE_MAP:
                    resolved = _CATALOG_TYPE_MAP[cat_type]
                elif svc_type and svc_type.value in _DB_SERVICE_TYPE_MAP:
                    resolved = _DB_SERVICE_TYPE_MAP[svc_type.value]
                new_cache[skey] = resolved
            _service_type_cache = new_cache
            _cache_ts = time.time()
            logger.debug("service_type cache refreshed: %d entries", len(new_cache))
        finally:
            db.close()
    except Exception as e:
        logger.warning("Failed to refresh service_type cache: %s", e)


def _get_service_type_cache() -> Dict[str, str]:
    """Return the cached mapping, refreshing if stale."""
    global _cache_ts
    if time.time() - _cache_ts > _CACHE_TTL:
        _refresh_service_type_cache()
    return _service_type_cache


def _classify_service_type(stream_labels: dict) -> str:
    """Derive service_type from stream labels using DB cache + heuristics."""
    cache = _get_service_type_cache()

    # 1. Try service_key lookup in DB cache
    service_key = stream_labels.get("service_key", "")
    if service_key and service_key in cache:
        return cache[service_key]

    # 2. Try job as service_key
    job = stream_labels.get("job", "")
    if job and job in cache:
        return cache[job]

    # 3. Heuristic patterns on job name
    for pattern, stype in _JOB_HEURISTICS:
        if pattern.search(job):
            return stype

    # 4. Check service_name for hints
    service_name = stream_labels.get("service_name", "")
    for pattern, stype in _JOB_HEURISTICS:
        if service_name and pattern.search(service_name):
            return stype

    return "unknown"


# ---------------------------------------------------------------------------
# Internal-platform service blocklist
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

INTERNAL_PATTERN = re.compile(
    r"^(rhinometric[-_](console|nginx|postgres|loki|jaeger|victoria|grafana|alertmanager|prometheus|cadvisor|node|redis|blackbox|otel|promtail|license|ai)|console[-_]|grafana|loki|jaeger|alertmanager|prometheus|cadvisor|node.exporter|ai[-_]anomaly)",
    re.IGNORECASE,
)

_LOKI_INTERNAL_RE = (
    "console-backend|docker_logs|rhinometric-audit|varlogs"
    "|grafana|loki|jaeger|alertmanager|prometheus"
    "|node-exporter|cadvisor|ai-anomaly|ai_anomaly"
    "|rhinometric[-_](console|nginx|postgres|loki|jaeger|victoria|grafana|alertmanager|prometheus|cadvisor|node|redis|blackbox|otel|promtail|license|ai)[-_].*|console[-_].*"
)

# ---------------------------------------------------------------------------
# Log message parsing — extract structured fields from raw text
# ---------------------------------------------------------------------------

_LEVEL_PREFIX_RE = re.compile(r"^\[(?P<level>DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL)\]\s*", re.IGNORECASE)

_ACCESS_LOG_RE = re.compile(
    r"(?P<client_ip>\d+\.\d+\.\d+\.\d+)\s+\S+\s+\S+\s+"
    r"\[(?P<access_time>[^\]]+)\]\s+"
    r'"(?P<method>GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(?P<path>\S+)\s+HTTP/\d\.\d"\s+'
    r"(?P<status_code>\d{3})\s+(?P<bytes>\S+)"
)

_APACHE_ERROR_RE = re.compile(
    r"\[(?P<error_time>[^\]]+)\]\s+"
    r"\[(?P<module>[^:]+):(?P<apache_level>\w+)\]\s+"
    r"\[pid\s+\d+:tid\s+\d+\]\s+"
    r"(?:\[client\s+(?P<client_ip>[^\]]+)\]\s+)?"
    r"(?P<error_message>.*)"
)

_CYCLE_RE = re.compile(
    r"Cycle\s+(?P<cycle_num>\d+)\s+.+?(?P<ok_count>\d+)/(?P<total>\d+)\s+OK.*?(?P<duration_ms>\d+)ms"
)

_SIGNAL_RE = re.compile(
    r"\[(?P<signal>metrics|logs|traces)\]\s+.+?\s+(?P<http_status>\d{3})\s+.*?(?P<duration_ms>\d+)ms"
)


def _parse_log_fields(message: str) -> Dict[str, Any]:
    """Extract structured fields from a raw log message."""
    fields: Dict[str, Any] = {}

    m = _LEVEL_PREFIX_RE.match(message)
    if m:
        raw_level = m.group("level").upper()
        if raw_level == "WARNING":
            raw_level = "WARN"
        fields["level"] = raw_level
        body = message[m.end():]
    else:
        body = message
        fields["level"] = "INFO"

    m = _ACCESS_LOG_RE.search(body)
    if m:
        fields["source_type"] = "access_log"
        fields["client_ip"] = m.group("client_ip")
        fields["method"] = m.group("method")
        fields["path"] = m.group("path").split("?")[0]
        fields["full_path"] = m.group("path")
        fields["status_code"] = int(m.group("status_code"))
        fields["response_bytes"] = m.group("bytes")
        fields["access_time"] = m.group("access_time")
        sc = fields["status_code"]
        if sc >= 500:
            fields["level"] = "ERROR"
        elif sc >= 400:
            fields["level"] = "WARN"
        return fields

    m = _APACHE_ERROR_RE.search(body)
    if m:
        fields["source_type"] = "error_log"
        fields["module"] = m.group("module")
        fields["error_message"] = m.group("error_message")
        if m.group("client_ip"):
            fields["client_ip"] = m.group("client_ip").split(":")[0]
        apache_level = m.group("apache_level").lower()
        if apache_level in ("error", "crit", "alert", "emerg"):
            fields["level"] = "ERROR"
        elif apache_level in ("warn", "warning"):
            fields["level"] = "WARN"
        return fields

    m = _CYCLE_RE.search(body)
    if m:
        fields["source_type"] = "collector_cycle"
        fields["cycle_num"] = int(m.group("cycle_num"))
        fields["duration_ms"] = int(m.group("duration_ms"))
        fields["ok_count"] = int(m.group("ok_count"))
        fields["total_signals"] = int(m.group("total"))
        return fields

    m = _SIGNAL_RE.search(body)
    if m:
        fields["source_type"] = "collector_signal"
        fields["signal"] = m.group("signal")
        fields["status_code"] = int(m.group("http_status"))
        fields["duration_ms"] = int(m.group("duration_ms"))
        return fields

    fields["source_type"] = "application"
    return fields


def _normalize_level(raw: str) -> str:
    low = raw.lower().strip()
    if low in ("debug", "trace"):
        return "debug"
    if low in ("info", "notice", "information"):
        return "info"
    if low in ("warn", "warning"):
        return "warn"
    if low in ("error", "err", "critical", "crit", "alert", "emerg"):
        return "error"
    if low in ("fatal", "panic"):
        return "fatal"
    return "info"


# ---------------------------------------------------------------------------
# Loki query helpers
# ---------------------------------------------------------------------------

_LOKI_SHORT_EXCLUSION = "console-backend|docker_logs|rhinometric-audit|varlogs"


def _inject_internal_exclusion(query: str, short: bool = False) -> str:
    """Inject internal-job exclusion into a LogQL query.
    
    short=True uses a compact regex (for enriched endpoint where
    Python-side _is_internal_stream handles the rest).
    Loki requires at least one positive matcher, so we add job=~".+"
    when the query has no existing matchers.
    """
    idx = query.find("}")
    if idx == -1:
        return query
    before = query[1:idx].strip()
    regex = _LOKI_SHORT_EXCLUSION if short else _LOKI_INTERNAL_RE
    if not before:
        # Empty selector: need positive matcher first
        return '{job=~".+", job!~"' + regex + '"}' + query[idx+1:]
    return query[:idx] + ', job!~"' + regex + '"' + query[idx:]


def _is_internal_stream(stream_labels: dict) -> bool:
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


def _enrich_log_entry(ts: str, message: str, stream_labels: dict) -> Dict[str, Any]:
    parsed = _parse_log_fields(message)
    normalized_level = _normalize_level(parsed.get("level", "info"))
    return {
        "timestamp": ts,
        "message": message,
        "level": normalized_level,
        "source_type": parsed.get("source_type", "application"),
        "service_type": _classify_service_type(stream_labels),
        "fields": parsed,
        "stream": stream_labels,
    }


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@router.get("")
async def get_logs(
    query: str = Query(..., description="LogQL query"),
    limit: int = Query(200, description="Maximum number of log lines"),
    start: str = Query(..., description="Start time in nanoseconds"),
    end: str = Query(..., description="End time in nanoseconds"),
    direction: str = Query("backward", description="Query direction: forward or backward"),
    current_user: UserModel = Depends(get_current_user),
):
    """Proxy logs from Loki, filtering out internal platform streams."""
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
                raise HTTPException(status_code=response.status_code, detail=f"Loki error: {response.text}")
            payload = response.json()
            result_list = payload.get("data", {}).get("result", [])
            filtered = [e for e in result_list if not _is_internal_stream(e.get("stream", {}))]
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


@router.get("/enriched")
async def get_logs_enriched(
    query: str = Query(..., description="LogQL query"),
    limit: int = Query(500, description="Maximum number of log lines"),
    start: str = Query(..., description="Start time in nanoseconds"),
    end: str = Query(..., description="End time in nanoseconds"),
    direction: str = Query("backward", description="Query direction"),
    level: Optional[str] = Query(None, description="Filter by level: debug|info|warn|error|fatal"),
    source_type: Optional[str] = Query(None, description="Filter by source_type"),
    service: Optional[str] = Query(None, description="Filter by service_key or job label"),
    method: Optional[str] = Query(None, description="Filter by HTTP method (GET, POST, etc.)"),
    status_code: Optional[str] = Query(None, description="Filter by HTTP status code or range (e.g. 404, 4xx, 5xx)"),
    path_contains: Optional[str] = Query(None, description="Filter by path substring"),
    search: Optional[str] = Query(None, description="Free text search in message body"),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Fetch logs from Loki, parse and enrich each entry with structured fields.
    All filters are applied server-side after enrichment.
    """
    try:
        base_query = query
        if service:
            base_query = f'{{job="{service}"}}'
            pipe_match = re.search(r"\}\s*(.*)", query)
            if pipe_match and pipe_match.group(1).strip():
                base_query += " " + pipe_match.group(1).strip()

        # Inject text search into LogQL for efficiency (pre-filter at Loki level)
        if search:
            safe = re.sub(r'[\\"`]', '', search)
            base_query += f' |~ "(?i){safe}"'

        enriched_query = _inject_internal_exclusion(base_query, short=True)

        async with httpx.AsyncClient(timeout=30.0) as client:
            has_filters = any([level, source_type, method, status_code, path_contains])
            fetch_limit = limit * 4 if has_filters else limit

            params = {
                "query": enriched_query,
                "limit": min(fetch_limit, 5000),
                "start": start,
                "end": end,
                "direction": direction,
            }

            loki_url = f"{settings.LOKI_URL}/loki/api/v1/query_range"
            response = await client.get(loki_url, params=params)

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Loki error: {response.text}")

            payload = response.json()

        result_list = payload.get("data", {}).get("result", [])
        all_entries: List[Dict[str, Any]] = []

        for stream_data in result_list:
            stream_labels = stream_data.get("stream", {})
            if _is_internal_stream(stream_labels):
                continue
            for ts, message in stream_data.get("values", []):
                entry = _enrich_log_entry(ts, message, stream_labels)
                all_entries.append(entry)

        total_before_filters = len(all_entries)

        # --- Server-side filters ---
        if level:
            norm = _normalize_level(level)
            all_entries = [e for e in all_entries if e["level"] == norm]

        if source_type:
            all_entries = [e for e in all_entries if e["source_type"] == source_type]

        if method:
            method_upper = method.upper()
            all_entries = [e for e in all_entries if e["fields"].get("method", "").upper() == method_upper]

        if status_code:
            sc_str = status_code.strip().lower()
            if sc_str.endswith("xx"):
                # Range filter: 4xx, 5xx, 2xx, 3xx
                prefix = sc_str[0]
                all_entries = [e for e in all_entries if str(e["fields"].get("status_code", "")).startswith(prefix)]
            else:
                try:
                    sc_int = int(sc_str)
                    all_entries = [e for e in all_entries if e["fields"].get("status_code") == sc_int]
                except ValueError:
                    pass

        if path_contains:
            path_lower = path_contains.lower()
            all_entries = [e for e in all_entries if path_lower in (e["fields"].get("path", "") or "").lower() or path_lower in (e["fields"].get("full_path", "") or "").lower()]

        # Sort and limit
        reverse = direction == "backward"
        all_entries.sort(key=lambda e: e["timestamp"], reverse=reverse)
        all_entries = all_entries[:limit]

        # Build available filter options from ALL data (before limit)
        all_levels = sorted({e["level"] for e in all_entries})
        all_source_types = sorted({e["source_type"] for e in all_entries})
        all_services = sorted({
            e["stream"].get("service_key") or e["stream"].get("job", "")
            for e in all_entries
        })
        all_methods = sorted({e["fields"].get("method", "") for e in all_entries if e["fields"].get("method")})
        all_status_codes = sorted({str(e["fields"].get("status_code", "")) for e in all_entries if e["fields"].get("status_code")})
        all_service_types = sorted({e.get("service_type", "unknown") for e in all_entries})

        return {
            "status": "success",
            "data": {
                "entries": all_entries,
                "total": len(all_entries),
                "total_before_filters": total_before_filters,
                "filters": {
                    "levels": all_levels,
                    "source_types": all_source_types,
                    "services": all_services,
                    "service_types": all_service_types,
                    "methods": all_methods,
                    "status_codes": all_status_codes,
                },
            },
        }

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Loki request timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Cannot connect to Loki: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/fields")
async def get_log_fields(
    current_user: UserModel = Depends(get_current_user),
):
    return {
        "status": "success",
        "data": {
            "stream_labels": {
                "job": {"description": "Service key identifier", "always_present": True},
                "service": {"description": "Service name", "always_present": True},
                "service_key": {"description": "Unique service+environment key", "always_present": True},
                "service_name": {"description": "Human-readable service name", "always_present": True},
                "environment": {"description": "Deployment environment", "always_present": True},
                "source": {"description": "Ingestion source", "always_present": True},
            },
            "enriched_fields": {
                "service_type": {
                    "description": "Service classification: http_api|web_app|database_postgres|collector|unknown",
                    "always_present": True,
                    "values": ["http_api", "web_app", "database_postgres", "collector", "unknown"],
                },
            },
            "parsed_fields": {
                "level": {"description": "Normalized severity: debug|info|warn|error|fatal", "always_present": True},
                "source_type": {"description": "Log classification", "always_present": True},
                "method": {"description": "HTTP method", "when": "source_type=access_log"},
                "path": {"description": "Request path without query", "when": "source_type=access_log"},
                "full_path": {"description": "Full request path", "when": "source_type=access_log"},
                "status_code": {"description": "HTTP status code", "when": "source_type=access_log|collector_signal"},
                "client_ip": {"description": "Client IP address", "when": "source_type=access_log|error_log"},
                "response_bytes": {"description": "Response size", "when": "source_type=access_log"},
                "module": {"description": "Apache module name", "when": "source_type=error_log"},
                "error_message": {"description": "Error detail", "when": "source_type=error_log"},
                "signal": {"description": "Telemetry signal type", "when": "source_type=collector_signal"},
                "duration_ms": {"description": "Duration in ms", "when": "source_type=collector_cycle|collector_signal"},
                "cycle_num": {"description": "Collector cycle number", "when": "source_type=collector_cycle"},
            },
        },
    }
