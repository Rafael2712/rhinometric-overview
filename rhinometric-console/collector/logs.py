"""
Rhinometric Collector — Real Log Capture

Captures the collector agent's own internal log output and sends it
as structured telemetry logs.  This is NOT fake data — every entry
represents a real event that occurred inside the collector process.

Architecture:
  A custom logging.Handler buffers log records produced by the
  collector.  Each collection cycle drains the buffer and ships the
  entries to the backend.
"""

import logging
import threading
from typing import Dict, List

from config import CollectorConfig

logger = logging.getLogger("rhyno.collector.logs")

# ── In-memory ring buffer handler ────────────────────────────────

_MAX_BUFFER = 200  # cap to avoid unbounded growth between cycles


class _BufferHandler(logging.Handler):
    """Thread-safe handler that stores records for later draining."""

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self._records: List[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        with self._lock:
            if len(self._records) < _MAX_BUFFER:
                self._records.append(record)

    def drain(self) -> List[logging.LogRecord]:
        with self._lock:
            records = list(self._records)
            self._records.clear()
            return records


_buffer_handler: _BufferHandler | None = None


def install_log_capture() -> None:
    """Attach the buffer handler to the collector root logger."""
    global _buffer_handler
    if _buffer_handler is not None:
        return
    _buffer_handler = _BufferHandler()
    _buffer_handler.setLevel(logging.DEBUG)
    root = logging.getLogger("rhyno.collector")
    root.addHandler(_buffer_handler)
    logger.debug("Log capture buffer installed")


def _level_str(record: logging.LogRecord) -> str:
    lvl = record.levelname.lower()
    mapping = {"warning": "warn", "critical": "fatal"}
    return mapping.get(lvl, lvl)


def collect_logs(cfg: CollectorConfig) -> List[Dict]:
    """
    Drain buffered log records and return them in backend format.

    Each log: { "message": str, "level": str, "labels": dict }
    """
    if _buffer_handler is None:
        return []

    records = _buffer_handler.drain()
    if not records:
        return []

    entries: List[Dict] = []
    for rec in records:
        entries.append({
            "message": rec.getMessage(),
            "level": _level_str(rec),
            "labels": {
                "service_key": cfg.service_key,
                "source": "collector",
                "module": rec.name.split(".")[-1] if "." in rec.name else rec.name,
                "environment": cfg.environment,
            },
        })

    logger.debug(f"Drained {len(entries)} log entries for shipment")
    return entries
