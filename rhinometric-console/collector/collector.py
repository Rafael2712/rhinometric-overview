#!/usr/bin/env python3
"""
Rhinometric Minimal Telemetry Collector

Sends synthetic metrics, logs, and traces to the Rhinometric
telemetry ingestion endpoints every INTERVAL seconds.

Required env vars:
  SERVICE_KEY       — the telemetry_service_key assigned to your service
  TELEMETRY_TOKEN   — the rtk_* token generated on service creation

Optional env vars:
  BASE_URL          — API base URL (default: http://localhost:80/api)
  INTERVAL          — seconds between collection cycles (default: 10)
"""

import os
import sys
import time
import json
import random
import string
import logging
import requests
from datetime import datetime, timezone

# ── Configuration ────────────────────────────────────────────

SERVICE_KEY      = os.environ.get("SERVICE_KEY", "")
TELEMETRY_TOKEN  = os.environ.get("TELEMETRY_TOKEN", "")
BASE_URL         = os.environ.get("BASE_URL", "http://localhost:80/api").rstrip("/")
INTERVAL         = int(os.environ.get("INTERVAL", "10"))

# ── Logging ──────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("collector")

# ── Helpers ──────────────────────────────────────────────────

HEADERS = {
    "Content-Type": "application/json",
    "X-Service-Key": SERVICE_KEY,
    "X-Telemetry-Token": TELEMETRY_TOKEN,
}

def rand_hex(n: int) -> str:
    return "".join(random.choices(string.hexdigits[:16], k=n))

def now_epoch_us() -> int:
    return int(time.time() * 1_000_000)

# ── Senders ──────────────────────────────────────────────────

def send_metrics(cycle: int) -> bool:
    """Send a small batch of realistic metrics."""
    payload = {
        "metrics": [
            {
                "name": "collector_heartbeat",
                "value": 1,
                "labels": {"service": "collector", "cycle": str(cycle)},
            },
            {
                "name": "http_requests_total",
                "value": random.randint(50, 500),
                "labels": {"method": "GET", "path": "/api/health", "status": "200"},
            },
            {
                "name": "http_request_duration_ms",
                "value": round(random.uniform(5, 250), 2),
                "labels": {"method": "GET", "path": "/api/health"},
            },
            {
                "name": "system_cpu_usage_percent",
                "value": round(random.uniform(10, 85), 1),
                "labels": {"host": "collector"},
            },
            {
                "name": "system_memory_used_mb",
                "value": round(random.uniform(128, 1024), 0),
                "labels": {"host": "collector"},
            },
        ]
    }
    try:
        r = requests.post(f"{BASE_URL}/telemetry/metrics", json=payload, headers=HEADERS, timeout=10)
        if r.status_code == 202:
            log.info("  [metrics]  202 — %d metrics sent", len(payload["metrics"]))
            return True
        else:
            log.warning("  [metrics]  %d — %s", r.status_code, r.text[:200])
            return False
    except Exception as e:
        log.error("  [metrics]  error: %s", e)
        return False


def send_logs(cycle: int) -> bool:
    """Send a small batch of realistic log entries."""
    levels = ["info", "info", "info", "warn", "error"]
    messages = [
        ("info",  "Collector heartbeat — cycle {cycle}"),
        ("info",  "Health check passed — response 200 in {ms}ms"),
        ("warn",  "Slow response detected — {ms}ms exceeds threshold"),
        ("error", "Connection timeout to upstream service after {ms}ms"),
        ("info",  "Request processed successfully — {method} {path}"),
    ]
    selected = random.sample(messages, k=min(3, len(messages)))
    logs = []
    for level, tmpl in selected:
        msg = tmpl.format(
            cycle=cycle,
            ms=random.randint(5, 3000),
            method=random.choice(["GET", "POST", "PUT"]),
            path=random.choice(["/api/users", "/api/orders", "/api/health"]),
        )
        logs.append({
            "message": msg,
            "level": level,
            "labels": {"source": "collector", "cycle": str(cycle)},
        })

    payload = {"logs": logs}
    try:
        r = requests.post(f"{BASE_URL}/telemetry/logs", json=payload, headers=HEADERS, timeout=10)
        if r.status_code == 202:
            log.info("  [logs]     202 — %d log entries sent", len(logs))
            return True
        else:
            log.warning("  [logs]     %d — %s", r.status_code, r.text[:200])
            return False
    except Exception as e:
        log.error("  [logs]     error: %s", e)
        return False


def send_traces(cycle: int) -> bool:
    """Send a realistic multi-span trace."""
    trace_id = rand_hex(32)
    root_span = rand_hex(16)
    child_span = rand_hex(16)
    start = now_epoch_us()
    child_dur = random.randint(2000, 15000)
    root_dur  = child_dur + random.randint(1000, 5000)

    payload = {
        "spans": [
            {
                "trace_id": trace_id,
                "span_id": root_span,
                "operation_name": "HTTP GET /api/health",
                "service_name": "collector",
                "start_time": start,
                "duration": root_dur,
                "status": "ok",
                "attributes": {
                    "http.method": "GET",
                    "http.url": "/api/health",
                    "http.status_code": "200",
                    "cycle": str(cycle),
                },
            },
            {
                "trace_id": trace_id,
                "span_id": child_span,
                "parent_span_id": root_span,
                "operation_name": "DB SELECT health_check",
                "service_name": "collector",
                "start_time": start + random.randint(500, 2000),
                "duration": child_dur,
                "status": "ok",
                "attributes": {
                    "db.system": "postgresql",
                    "db.statement": "SELECT 1",
                },
            },
        ]
    }
    try:
        r = requests.post(f"{BASE_URL}/telemetry/traces", json=payload, headers=HEADERS, timeout=10)
        if r.status_code == 202:
            log.info("  [traces]   202 — %d spans sent (trace=%s…)", len(payload["spans"]), trace_id[:12])
            return True
        else:
            log.warning("  [traces]   %d — %s", r.status_code, r.text[:200])
            return False
    except Exception as e:
        log.error("  [traces]   error: %s", e)
        return False


# ── Main Loop ────────────────────────────────────────────────

def main():
    if not SERVICE_KEY or not TELEMETRY_TOKEN:
        log.error("SERVICE_KEY and TELEMETRY_TOKEN must be set.")
        sys.exit(1)

    log.info("=" * 60)
    log.info("Rhinometric Minimal Collector started")
    log.info("  BASE_URL : %s", BASE_URL)
    log.info("  KEY      : %s", SERVICE_KEY)
    log.info("  TOKEN    : %s…%s", TELEMETRY_TOKEN[:8], TELEMETRY_TOKEN[-4:])
    log.info("  INTERVAL : %ds", INTERVAL)
    log.info("=" * 60)

    cycle = 0
    while True:
        cycle += 1
        log.info("── cycle %d ──", cycle)

        m = send_metrics(cycle)
        l = send_logs(cycle)
        t = send_traces(cycle)

        if m and l and t:
            log.info("  ✓ all signals sent successfully")
        else:
            log.warning("  ⚠ some signals failed")

        log.info("  sleeping %ds…", INTERVAL)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
