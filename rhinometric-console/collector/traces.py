"""
Rhinometric Collector — Real Trace Generation

Produces real traces for the collector's own operations:
  - Each collection cycle is a parent span.
  - Each signal send (metrics/logs/traces) is a child span with
    actual measured duration.

Trace and span IDs are cryptographically random (UUID-based).
Durations are measured with time.monotonic() — not invented.
"""

import time
import logging
from typing import Dict, List, Optional

from config import CollectorConfig
from utils import generate_trace_id, generate_span_id, now_us

logger = logging.getLogger("rhyno.collector.traces")


class SpanBuilder:
    """Lightweight span builder that measures real wall-clock duration."""

    def __init__(
        self,
        operation_name: str,
        service_name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict] = None,
    ):
        self.trace_id = trace_id or generate_trace_id()
        self.span_id = generate_span_id()
        self.parent_span_id = parent_span_id
        self.operation_name = operation_name
        self.service_name = service_name
        self.attributes = attributes or {}
        self.start_time_us = now_us()
        self._t0 = time.monotonic()
        self.status = "ok"

    def set_error(self, msg: str = "") -> None:
        self.status = "error"
        if msg:
            self.attributes["error.message"] = msg

    def finish(self) -> Dict:
        """Return the span dict in backend-expected format."""
        elapsed_us = int((time.monotonic() - self._t0) * 1_000_000)
        span: Dict = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "operation_name": self.operation_name,
            "service_name": self.service_name,
            "start_time": self.start_time_us,
            "duration": max(elapsed_us, 1),
            "status": self.status,
            "attributes": self.attributes,
        }
        if self.parent_span_id:
            span["parent_span_id"] = self.parent_span_id
        return span


class CycleTracer:
    """
    Manages traces for one collection cycle.

    Usage:
        tracer = CycleTracer(cfg, cycle)
        with tracer.child("send_metrics") as span:
            ... do work ...
            if failed: span.set_error("reason")
        spans = tracer.finish()
    """

    def __init__(self, cfg: CollectorConfig, cycle: int):
        self.cfg = cfg
        svc_name = cfg.service_key or "rhyno-collector"
        self.trace_id = generate_trace_id()
        self._parent = SpanBuilder(
            operation_name="collector.cycle",
            service_name=svc_name,
            trace_id=self.trace_id,
            attributes={
                "collector.cycle": str(cycle),
                "service_key": cfg.service_key,
                "environment": cfg.environment,
            },
        )
        self._children: List[Dict] = []

    def child(self, operation: str, **attrs: str) -> "_ChildCtx":
        return _ChildCtx(self, operation, attrs)

    def _add_child(self, span_dict: Dict) -> None:
        self._children.append(span_dict)

    def finish(self) -> List[Dict]:
        """Close the parent span and return all spans."""
        parent_dict = self._parent.finish()
        return [parent_dict] + self._children


class _ChildCtx:
    """Context manager for a child span."""

    def __init__(self, tracer: CycleTracer, operation: str, attrs: Dict):
        self._tracer = tracer
        svc_name = tracer.cfg.service_key or "rhyno-collector"
        self._span = SpanBuilder(
            operation_name=f"collector.{operation}",
            service_name=svc_name,
            trace_id=tracer.trace_id,
            parent_span_id=tracer._parent.span_id,
            attributes=attrs,
        )

    def __enter__(self) -> SpanBuilder:
        return self._span

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self._span.set_error(str(exc_val))
        self._tracer._add_child(self._span.finish())
        return None  # do not suppress exceptions
