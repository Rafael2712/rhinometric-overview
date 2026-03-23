"""
Rhinometric Collector — Real System Metrics

Collects actual host metrics via psutil:
  - CPU usage (percent, core count)
  - Memory usage (percent, used bytes, total bytes)
  - Disk usage (percent)
  - Network I/O (bytes sent/received)
  - Process uptime (seconds)
"""

import time
import logging
from typing import Dict, List

import psutil

from config import CollectorConfig

logger = logging.getLogger("rhyno.collector.metrics")

# Track collector start time for uptime
_start_time = time.monotonic()


def collect_metrics(cfg: CollectorConfig) -> List[Dict]:
    """
    Gather real system metrics and return them in the backend-expected format.

    Each metric: { "name": str, "value": float, "labels": dict }
    """
    labels: Dict[str, str] = {
        "service_key": cfg.service_key,
        "host": cfg.hostname,
        "environment": cfg.environment,
    }

    samples: List[Dict] = []

    # ── CPU ──────────────────────────────────────────────────
    try:
        cpu_pct = psutil.cpu_percent(interval=0.5)
        samples.append({
            "name": "system_cpu_usage_percent",
            "value": round(cpu_pct, 2),
            "labels": {**labels, "unit": "percent"},
        })
        cpu_count = psutil.cpu_count(logical=True) or 1
        samples.append({
            "name": "system_cpu_count",
            "value": float(cpu_count),
            "labels": {**labels, "unit": "cores"},
        })
    except Exception as exc:
        logger.warning(f"Failed to collect CPU metrics: {exc}")

    # ── Memory ───────────────────────────────────────────────
    try:
        mem = psutil.virtual_memory()
        samples.append({
            "name": "system_memory_usage_percent",
            "value": round(mem.percent, 2),
            "labels": {**labels, "unit": "percent"},
        })
        samples.append({
            "name": "system_memory_used_bytes",
            "value": float(mem.used),
            "labels": {**labels, "unit": "bytes"},
        })
        samples.append({
            "name": "system_memory_total_bytes",
            "value": float(mem.total),
            "labels": {**labels, "unit": "bytes"},
        })
    except Exception as exc:
        logger.warning(f"Failed to collect memory metrics: {exc}")

    # ── Disk ─────────────────────────────────────────────────
    try:
        disk = psutil.disk_usage("/")
        samples.append({
            "name": "system_disk_usage_percent",
            "value": round(disk.percent, 2),
            "labels": {**labels, "mount": "/", "unit": "percent"},
        })
    except Exception as exc:
        logger.warning(f"Failed to collect disk metrics: {exc}")

    # ── Network I/O ──────────────────────────────────────────
    try:
        net = psutil.net_io_counters()
        samples.append({
            "name": "system_net_bytes_sent",
            "value": float(net.bytes_sent),
            "labels": {**labels, "unit": "bytes"},
        })
        samples.append({
            "name": "system_net_bytes_recv",
            "value": float(net.bytes_recv),
            "labels": {**labels, "unit": "bytes"},
        })
    except Exception as exc:
        logger.warning(f"Failed to collect network metrics: {exc}")

    # ── Process uptime ───────────────────────────────────────
    uptime_s = round(time.monotonic() - _start_time, 1)
    samples.append({
        "name": "collector_uptime_seconds",
        "value": uptime_s,
        "labels": {**labels, "unit": "seconds"},
    })

    logger.debug(f"Collected {len(samples)} metric samples")
    return samples
