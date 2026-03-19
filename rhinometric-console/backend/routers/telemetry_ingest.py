"""
Telemetry Ingestion Router — Task 10

Endpoints:
  POST /api/telemetry/metrics
  POST /api/telemetry/logs
  POST /api/telemetry/traces

Authentication: telemetry_service_key + telemetry_token headers.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import logging
import httpx
import secrets

from database import get_db
from models.external_service import (
    ExternalService, MonitoringMode, TelemetryStatus,
)

logger = logging.getLogger("rhinometric.telemetry_ingest")

router = APIRouter()

# ── Rate-limit state (basic in-memory) ──────────────────────────
_rate_limit: Dict[str, List[float]] = {}
RATE_LIMIT_WINDOW = 60   # seconds
RATE_LIMIT_MAX = 120      # requests per window per service key


def _check_rate_limit(service_key: str):
    """Basic sliding-window rate limiter."""
    import time
    now = time.time()
    window = _rate_limit.setdefault(service_key, [])
    # Prune old entries
    _rate_limit[service_key] = [t for t in window if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit[service_key]) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    _rate_limit[service_key].append(now)


# ── Schemas ─────────────────────────────────────────────────────

class MetricSample(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Metric name (e.g. http_requests_total)")
    value: float = Field(..., description="Metric value")
    labels: Optional[Dict[str, str]] = Field(default_factory=dict, description="Label key-value pairs")
    timestamp: Optional[int] = Field(None, description="Unix timestamp in milliseconds (optional)")

class MetricsPayload(BaseModel):
    metrics: List[MetricSample] = Field(..., min_length=1, max_length=1000)

class LogEntry(BaseModel):
    message: str = Field(..., min_length=1, max_length=65536)
    level: str = Field(default="info", pattern="^(debug|info|warn|error|fatal)$")
    labels: Optional[Dict[str, str]] = Field(default_factory=dict)
    timestamp: Optional[str] = Field(None, description="ISO-8601 timestamp (optional)")

class LogsPayload(BaseModel):
    logs: List[LogEntry] = Field(..., min_length=1, max_length=500)

class SpanData(BaseModel):
    trace_id: str = Field(..., min_length=1, max_length=64)
    span_id: str = Field(..., min_length=1, max_length=32)
    parent_span_id: Optional[str] = Field(None, max_length=32)
    operation_name: str = Field(..., min_length=1, max_length=255)
    service_name: str = Field(..., min_length=1, max_length=255)
    start_time: int = Field(..., description="Start time in microseconds since epoch")
    duration: int = Field(..., description="Duration in microseconds")
    status: str = Field(default="ok", pattern="^(ok|error|unset)$")
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict)

class TracesPayload(BaseModel):
    spans: List[SpanData] = Field(..., min_length=1, max_length=500)


# ── Service resolution & auth ───────────────────────────────────

def _resolve_service(
    service_key: str,
    token: str,
    signal: str,
    db: Session,
) -> ExternalService:
    """Resolve and authenticate a service from key+token.

    Also handles auto-attachment and status transitions.
    """
    if not service_key or not token:
        raise HTTPException(status_code=401, detail="Missing telemetry_service_key or telemetry_token.")

    _check_rate_limit(service_key)

    svc = (
        db.query(ExternalService)
        .filter(ExternalService.telemetry_service_key == service_key)
        .first()
    )
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found for the given service key.")

    if svc.monitoring_mode != MonitoringMode.TELEMETRY_ENABLED:
        raise HTTPException(status_code=403, detail="Telemetry is not enabled for this service.")

    if svc.telemetry_token != token:
        raise HTTPException(status_code=401, detail="Invalid telemetry token.")

    # Check signal permission
    signal_map = {
        "metrics": svc.metrics_enabled,
        "logs": svc.logs_enabled,
        "traces": svc.traces_enabled,
    }
    if not signal_map.get(signal, False):
        raise HTTPException(
            status_code=403,
            detail=f"Signal '{signal}' is not enabled for this service.",
        )

    # ── Attachment logic (Part 4) ──────────────────────────────
    now = datetime.now(timezone.utc)
    changed = False

    if not svc.telemetry_attached:
        svc.telemetry_attached = True
        svc.telemetry_source_type = "collector"
        svc.telemetry_status = TelemetryStatus.CONNECTED
        changed = True
        logger.info(f"Telemetry attached for service {svc.name} (id={svc.id})")

    if svc.telemetry_status == TelemetryStatus.CONNECTED:
        svc.telemetry_status = TelemetryStatus.RECEIVING_DATA
        changed = True

    svc.last_telemetry_at = now
    if changed:
        db.flush()

    return svc


# ── Backend forwarding helpers ──────────────────────────────────

VICTORIA_METRICS_URL = "http://rhinometric-victoria-metrics:8428"
LOKI_URL = "http://rhinometric-loki:3100"
JAEGER_OTLP_URL = "http://rhinometric-jaeger:4318"


async def _forward_metrics(svc: ExternalService, payload: MetricsPayload):
    """Convert to Prometheus text format and push to Victoria Metrics."""
    import time
    lines = []
    for m in payload.metrics:
        label_str = ""
        labels = dict(m.labels or {})
        labels["service"] = svc.name
        labels["service_key"] = svc.telemetry_service_key or ""
        labels["environment"] = svc.environment or "unknown"
        if labels:
            parts = [f'{k}="{v}"' for k, v in labels.items()]
            label_str = "{" + ",".join(parts) + "}"
        ts = m.timestamp or int(time.time() * 1000)
        lines.append(f"{m.name}{label_str} {m.value} {ts}")

    body = "\n".join(lines)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{VICTORIA_METRICS_URL}/api/v1/import/prometheus",
                content=body,
                headers={"Content-Type": "text/plain"},
            )
            if resp.status_code >= 400:
                logger.warning(f"Victoria Metrics push failed: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"Victoria Metrics push error: {e}")


async def _forward_logs(svc: ExternalService, payload: LogsPayload):
    """Push logs to Loki via the push API."""
    import time
    entries = []
    for log in payload.logs:
        ts_ns = str(int(time.time() * 1e9))
        if log.timestamp:
            try:
                from datetime import datetime as dt
                parsed = dt.fromisoformat(log.timestamp.replace("Z", "+00:00"))
                ts_ns = str(int(parsed.timestamp() * 1e9))
            except Exception:
                pass
        entries.append([ts_ns, f"[{log.level.upper()}] {log.message}"])

    labels = {
        "service": svc.name,
        "service_key": svc.telemetry_service_key or "",
        "environment": svc.environment or "unknown",
        "source": "telemetry_ingest",
    }
    loki_payload = {
        "streams": [{
            "stream": labels,
            "values": entries,
        }]
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{LOKI_URL}/loki/api/v1/push",
                json=loki_payload,
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code >= 400:
                logger.warning(f"Loki push failed: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"Loki push error: {e}")


async def _forward_traces(svc: ExternalService, payload: TracesPayload):
    """Convert to OTLP JSON and push to Jaeger's OTLP HTTP endpoint."""
    resource_spans = []
    scope_spans_map: Dict[str, list] = {}

    for span in payload.spans:
        svc_name = span.service_name
        if svc_name not in scope_spans_map:
            scope_spans_map[svc_name] = []

        attrs = []
        for k, v in (span.attributes or {}).items():
            attrs.append({"key": k, "value": {"stringValue": str(v)}})
        # Add service metadata
        attrs.append({"key": "rhinometric.service_key", "value": {"stringValue": svc.telemetry_service_key or ""}})
        attrs.append({"key": "rhinometric.environment", "value": {"stringValue": svc.environment or "unknown"}})

        otlp_span = {
            "traceId": span.trace_id,
            "spanId": span.span_id,
            "name": span.operation_name,
            "kind": 1,  # SPAN_KIND_INTERNAL
            "startTimeUnixNano": str(span.start_time * 1000),  # us -> ns
            "endTimeUnixNano": str((span.start_time + span.duration) * 1000),
            "attributes": attrs,
            "status": {"code": 1 if span.status == "ok" else 2},
        }
        if span.parent_span_id:
            otlp_span["parentSpanId"] = span.parent_span_id

        scope_spans_map[svc_name].append(otlp_span)

    for svc_name, spans_list in scope_spans_map.items():
        resource_spans.append({
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": svc_name}},
                    {"key": "rhinometric.service_id", "value": {"intValue": svc.id}},
                ]
            },
            "scopeSpans": [{
                "scope": {"name": "rhinometric.telemetry_ingest"},
                "spans": spans_list,
            }],
        })

    otlp_payload = {"resourceSpans": resource_spans}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{JAEGER_OTLP_URL}/v1/traces",
                json=otlp_payload,
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code >= 400:
                logger.warning(f"Jaeger push failed: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"Jaeger push error: {e}")


# ── Endpoints ───────────────────────────────────────────────────

@router.post("/metrics", status_code=202)
async def ingest_metrics(
    payload: MetricsPayload,
    request: Request,
    db: Session = Depends(get_db),
):
    """Ingest metrics from an external service."""
    service_key = request.headers.get("X-Service-Key", "")
    token = request.headers.get("X-Telemetry-Token", "")

    svc = _resolve_service(service_key, token, "metrics", db)
    logger.info(f"Ingesting {len(payload.metrics)} metrics for service {svc.name}")

    await _forward_metrics(svc, payload)

    return {
        "status": "accepted",
        "service": svc.name,
        "signal": "metrics",
        "count": len(payload.metrics),
    }


@router.post("/logs", status_code=202)
async def ingest_logs(
    payload: LogsPayload,
    request: Request,
    db: Session = Depends(get_db),
):
    """Ingest logs from an external service."""
    service_key = request.headers.get("X-Service-Key", "")
    token = request.headers.get("X-Telemetry-Token", "")

    svc = _resolve_service(service_key, token, "logs", db)
    logger.info(f"Ingesting {len(payload.logs)} logs for service {svc.name}")

    await _forward_logs(svc, payload)

    return {
        "status": "accepted",
        "service": svc.name,
        "signal": "logs",
        "count": len(payload.logs),
    }


@router.post("/traces", status_code=202)
async def ingest_traces(
    payload: TracesPayload,
    request: Request,
    db: Session = Depends(get_db),
):
    """Ingest traces from an external service."""
    service_key = request.headers.get("X-Service-Key", "")
    token = request.headers.get("X-Telemetry-Token", "")

    svc = _resolve_service(service_key, token, "traces", db)
    logger.info(f"Ingesting {len(payload.spans)} spans for service {svc.name}")

    await _forward_traces(svc, payload)

    return {
        "status": "accepted",
        "service": svc.name,
        "signal": "traces",
        "count": len(payload.spans),
    }


# ── Token generation helper ─────────────────────────────────────

def generate_telemetry_token() -> str:
    """Generate a cryptographically secure telemetry token."""
    return f"rtk_{secrets.token_urlsafe(48)}"
