#!/usr/bin/env python3
"""
Rhinometric Collector v1 — Main Entry Point

Production-ready telemetry agent that collects real system metrics,
captures its own logs, and generates real traces for each cycle.

Usage:
    python main.py                          # env-var config
    RHYNO_CONFIG_FILE=config.yaml python main.py  # YAML config
"""

import sys
import time
import signal as sig
import logging

from config import load_config, CollectorConfig
from utils import setup_logging
from sender import send_metrics, send_logs, send_traces
from metrics import collect_metrics
from logs import install_log_capture, collect_logs
from traces import CycleTracer

logger = logging.getLogger("rhyno.collector.main")

# ── Graceful shutdown ──────────────────────────────────────────────

_running = True


def _shutdown(signum, frame):
    global _running
    logger.info(f"Received signal {signum} — shutting down")
    _running = False


sig.signal(sig.SIGINT, _shutdown)
sig.signal(sig.SIGTERM, _shutdown)


# ── Main loop ──────────────────────────────────────────────────────

def run(cfg: CollectorConfig) -> None:
    cycle = 0
    logger.info(
        f"Collector started — "
        f"api={cfg.api_url}  key={cfg.service_key}  "
        f"interval={cfg.collect_interval}s  "
        f"metrics={'on' if cfg.enable_metrics else 'off'}  "
        f"logs={'on' if cfg.enable_logs else 'off'}  "
        f"traces={'on' if cfg.enable_traces else 'off'}"
    )

    while _running:
        cycle += 1
        tracer = CycleTracer(cfg, cycle)
        t0 = time.monotonic()
        signals_ok = 0
        signals_total = 0

        # ── Metrics ────────────────────────────────────────────
        if cfg.enable_metrics:
            signals_total += 1
            with tracer.child("send_metrics") as span:
                try:
                    samples = collect_metrics(cfg)
                    ok = send_metrics(cfg, samples)
                    if ok:
                        signals_ok += 1
                    else:
                        span.set_error("HTTP error")
                except Exception as exc:
                    span.set_error(str(exc))
                    logger.error(f"Metrics collection failed: {exc}")

        # ── Logs ───────────────────────────────────────────────
        if cfg.enable_logs:
            signals_total += 1
            with tracer.child("send_logs") as span:
                try:
                    entries = collect_logs(cfg)
                    if entries:
                        ok = send_logs(cfg, entries)
                        if ok:
                            signals_ok += 1
                        else:
                            span.set_error("HTTP error")
                    else:
                        # No buffered logs this cycle — still OK
                        signals_ok += 1
                        span.attributes["note"] = "no_buffered_logs"
                except Exception as exc:
                    span.set_error(str(exc))
                    logger.error(f"Log collection failed: {exc}")

        # ── Traces ─────────────────────────────────────────────
        if cfg.enable_traces:
            signals_total += 1
            cycle_spans = tracer.finish()
            try:
                ok = send_traces(cfg, cycle_spans)
                if ok:
                    signals_ok += 1
            except Exception as exc:
                logger.error(f"Trace send failed: {exc}")

        elapsed = round((time.monotonic() - t0) * 1000)
        logger.info(
            f"Cycle {cycle} complete — "
            f"{signals_ok}/{signals_total} signals OK — "
            f"{elapsed}ms"
        )

        # ── Sleep (interruptible) ──────────────────────────────
        deadline = time.monotonic() + cfg.collect_interval
        while _running and time.monotonic() < deadline:
            time.sleep(0.5)

    logger.info("Collector stopped")


# ── Entry point ────────────────────────────────────────────────────

def main() -> None:
    setup_logging("INFO")
    install_log_capture()
    cfg = load_config()
    run(cfg)


if __name__ == "__main__":
    main()
