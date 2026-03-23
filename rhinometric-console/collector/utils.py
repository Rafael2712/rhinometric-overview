"""
Rhinometric Collector — Utilities

Shared helpers: ID generation, time, logging setup, masking.
"""

import time
import uuid
import logging
import sys

__version__ = "1.2.0"


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging for the collector agent."""
    root = logging.getLogger("rhyno.collector")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        ))
        root.addHandler(handler)


def mask_token(token: str) -> str:
    """Mask a sensitive token for safe logging: show first 4 and last 4 chars."""
    if not token or len(token) < 12:
        return "***"
    return f"{token[:4]}…{token[-4:]}"


def mask_url(url: str) -> str:
    """Show URL but mask any embedded credentials."""
    if "@" in url:
        before_at = url.split("@")[0]
        after_at = url.split("@", 1)[1]
        scheme = before_at.split("//")[0] + "//" if "//" in before_at else ""
        return f"{scheme}***@{after_at}"
    return url


def generate_trace_id() -> str:
    """32-char hex trace ID (128-bit)."""
    return uuid.uuid4().hex


def generate_span_id() -> str:
    """16-char hex span ID (64-bit)."""
    return uuid.uuid4().hex[:16]


def now_us() -> int:
    """Current time in microseconds since epoch."""
    return int(time.time() * 1_000_000)


def now_iso() -> str:
    """Current time as ISO-8601 UTC string."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
