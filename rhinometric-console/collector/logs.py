"""
Rhinometric Collector — Log Capture & File Ingestion

Two log sources merged into one pipeline:

1. **Internal buffer** — A custom logging.Handler captures the collector's
   own log output (startup messages, cycle results, errors).  These are
   real operational events, not synthetic data.

2. **File tailing** (Task 21) — Reads new lines from external log files
   listed in LOG_SOURCES (e.g. /var/log/app.log).  Uses offset-based
   tailing with rotation/truncation detection.

Both sources are merged by `collect_logs()` and shipped in one payload.
"""

import os
import logging
import threading
from typing import Dict, List, Optional

from config import CollectorConfig

logger = logging.getLogger("rhyno.collector.logs")

# ═══════════════════════════════════════════════════════════════
#  Part 1 — Internal log buffer (unchanged from v1.1.0)
# ═══════════════════════════════════════════════════════════════

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


_buffer_handler: Optional[_BufferHandler] = None


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


def _drain_internal_logs(cfg: CollectorConfig) -> List[Dict]:
    """Drain buffered internal log records and return them in backend format."""
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
    return entries


# ═══════════════════════════════════════════════════════════════
#  Part 2 — File-based log tailing  (Task 21 — NEW)
# ═══════════════════════════════════════════════════════════════

def detect_level(line: str) -> str:
    """
    Detect log level from a raw line by keyword matching.

    Scans for common level keywords (case-insensitive).
    Returns: "error", "warning", "info" (default).
    """
    upper = line.upper()
    for keyword in ("ERROR", "FATAL", "CRITICAL", "EXCEPTION", "PANIC"):
        if keyword in upper:
            return "error"
    for keyword in ("WARN", "WARNING"):
        if keyword in upper:
            return "warning"
    if "DEBUG" in upper:
        return "debug"
    return "info"


class FileTailer:
    """
    Offset-based file tailer with rotation and truncation detection.

    Tracks:
      - offset: byte position of last read
      - inode:  file identity (detects log rotation / replacement)

    Safety:
      - Missing files are silently skipped (logged once per cycle)
      - Truncated files reset offset to 0
      - Reads are capped at `max_lines` per cycle to avoid memory spikes
      - Uses readline() loop (not iterator) to keep fh.tell() working
    """

    def __init__(self, path: str, max_lines: int = 50):
        self.path = path
        self.max_lines = max_lines
        self._offset: int = 0
        self._inode: Optional[int] = None

    def read_new_lines(self) -> List[str]:
        """
        Read new lines appended since the last call.

        Returns a list of stripped non-empty lines (up to max_lines).
        Updates internal offset for next call.
        """
        try:
            stat = os.stat(self.path)
        except FileNotFoundError:
            logger.info(f"file:{self.path} → file not found, skipping")
            return []
        except OSError as exc:
            logger.warning(f"file:{self.path} → stat error: {exc}")
            return []

        current_inode = getattr(stat, "st_ino", 0)

        # Rotation detection: inode changed → new file
        if self._inode is not None and current_inode != 0 and current_inode != self._inode:
            logger.info(f"file:{self.path} → inode changed (rotation detected), resetting offset")
            self._offset = 0

        # Truncation detection: file shrunk
        if stat.st_size < self._offset:
            logger.info(f"file:{self.path} → file truncated ({stat.st_size} < {self._offset}), resetting offset")
            self._offset = 0

        self._inode = current_inode

        # Nothing new to read
        if stat.st_size == self._offset:
            return []

        lines: List[str] = []
        try:
            with open(self.path, "r", encoding="utf-8", errors="replace") as fh:
                fh.seek(self._offset)
                while len(lines) < self.max_lines:
                    raw = fh.readline()
                    if not raw:          # EOF
                        break
                    line = raw.rstrip("\n\r")
                    if line:
                        lines.append(line)
                self._offset = fh.tell()
        except OSError as exc:
            logger.warning(f"file:{self.path} → read error: {exc}")

        return lines


# ── Module-level tailer registry ─────────────────────────────────
_tailers: Dict[str, FileTailer] = {}


def _get_tailer(path: str, max_lines: int) -> FileTailer:
    """Get or create a FileTailer for the given path."""
    if path not in _tailers:
        _tailers[path] = FileTailer(path, max_lines=max_lines)
    return _tailers[path]


def collect_file_logs(cfg: CollectorConfig) -> List[Dict]:
    """
    Read new lines from all configured LOG_SOURCES and return them
    in backend log format.

    Each entry: { "message": str, "level": str, "labels": dict }
    """
    if not cfg.log_sources:
        return []

    entries: List[Dict] = []

    for file_path in cfg.log_sources:
        tailer = _get_tailer(file_path, cfg.log_max_lines)
        new_lines = tailer.read_new_lines()

        for line in new_lines:
            level = detect_level(line)
            entries.append({
                "message": line,
                "level": level,
                "labels": {
                    "service_key": cfg.service_key,
                    "source": "file",
                    "file_path": file_path,
                    "environment": cfg.environment,
                },
            })

    if entries:
        logger.debug(f"Collected {len(entries)} file log entries from {len(cfg.log_sources)} source(s)")

    return entries


# ═══════════════════════════════════════════════════════════════
#  Part 3 — Merged collector  (updated for Task 21)
# ═══════════════════════════════════════════════════════════════

def collect_logs(cfg: CollectorConfig) -> List[Dict]:
    """
    Drain all log sources and return a merged list:
      - Internal collector logs (from _BufferHandler)
      - File-based logs (from LOG_SOURCES)

    Backward compatible: if LOG_SOURCES is empty, only internal
    logs are returned (identical to v1.1.0 behavior).
    """
    internal = _drain_internal_logs(cfg)
    file_logs = collect_file_logs(cfg)

    merged = internal + file_logs

    if merged:
        logger.debug(f"Total log entries: {len(merged)} (internal={len(internal)}, file={len(file_logs)})")

    return merged
