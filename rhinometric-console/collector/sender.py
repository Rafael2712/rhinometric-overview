"""
Rhinometric Collector — HTTP Sender

Central module for all telemetry HTTP submissions.
Handles retries, timeouts, and structured error reporting.
"""

import time
import logging
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import CollectorConfig

logger = logging.getLogger("rhyno.collector.sender")

# ── Session factory ────────────────────────────────────────────────

_session: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    """Lazy-init a requests.Session with retry/backoff."""
    global _session
    if _session is None:
        _session = requests.Session()
        retry = Retry(
            total=1,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)
    return _session


# ── Generic POST ───────────────────────────────────────────────────

def send_telemetry(
    cfg: CollectorConfig,
    signal: str,
    payload: Dict[str, Any],
    timeout: float = 10.0,
) -> bool:
    """
    POST a telemetry payload to the backend.

    Args:
        cfg:     Collector configuration
        signal:  One of "metrics", "logs", "traces"
        payload: JSON-serializable body
        timeout: HTTP timeout in seconds

    Returns:
        True on success (2xx), False otherwise.
    """
    url = f"{cfg.api_url}/telemetry/{signal}"
    headers = {
        "Content-Type": "application/json",
        "X-Service-Key": cfg.service_key,
        "X-Telemetry-Token": cfg.telemetry_token,
    }

    t0 = time.monotonic()
    try:
        resp = _get_session().post(url, json=payload, headers=headers, timeout=(3, timeout))
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        if resp.status_code < 300:
            logger.info(f"[{signal}] {resp.status_code} — {elapsed_ms}ms")
            return True
        else:
            logger.warning(f"[{signal}] HTTP {resp.status_code} — {resp.text[:200]}")
            return False

    except requests.exceptions.ConnectionError as exc:
        logger.error(f"[{signal}] connection error: {exc}")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"[{signal}] request timed out after {timeout}s")
        return False
    except Exception as exc:
        logger.error(f"[{signal}] unexpected error: {exc}")
        return False


# ── Typed wrappers ─────────────────────────────────────────────────

def send_metrics(cfg: CollectorConfig, metrics: List[Dict]) -> bool:
    return send_telemetry(cfg, "metrics", {"metrics": metrics})


def send_logs(cfg: CollectorConfig, logs: List[Dict]) -> bool:
    return send_telemetry(cfg, "logs", {"logs": logs})


def send_traces(cfg: CollectorConfig, spans: List[Dict]) -> bool:
    return send_telemetry(cfg, "traces", {"spans": spans})
