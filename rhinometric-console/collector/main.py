#!/usr/bin/env python3
"""
Rhinometric Collector v1.2 — Main Entry Point

Production-ready telemetry agent that collects real system metrics,
captures its own logs, tails external log files, and generates real
traces for each cycle.

Usage:
    python main.py                                # env-var config
    RHYNO_CONFIG_FILE=config.yaml python main.py  # YAML config
    docker run --env-file .env rhinometric-collector
"""

import sys
import time
import signal as sig
import logging

from config import load_config, CollectorConfig
from utils import setup_logging, mask_token, mask_url, __version__
from sender import send_metrics, send_logs, send_traces, preflight_check
from metrics import collect_metrics
from logs import install_log_capture, collect_logs
from traces import CycleTracer

logger = logging.getLogger("rhyno.collector.main")

# ── Graceful shutdown ───────────────────────────────────────────

_running = True


def _shutdown(signum, frame):
    global _running
    logger.info(f"Received signal {signum} — shutting down gracefully…")
    _running = False


sig.signal(sig.SIGINT, _shutdown)
sig.signal(sig.SIGTERM, _shutdown)


# ── Startup banner ──────────────────────────────────────────────

def _print_banner(cfg: CollectorConfig) -> None:
    """Print a clear startup summary with masked sensitive values."""
    signals = []
    if cfg.enable_metrics:
        signals.append("metrics")
    if cfg.enable_logs:
        signals.append("logs")
    if cfg.enable_traces:
        signals.append("traces")

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║          Rhinometric Collector v" + __version__.ljust(26) + "║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  API URL      : {mask_url(cfg.api_url):<40s}║")
    print(f"║  Service Key  : {cfg.service_key:<40s}║")
    print(f"║  Token        : {mask_token(cfg.telemetry_token):<40s}║")
    print(f"║  Hostname     : {cfg.hostname:<40s}║")
    print(f"║  Environment  : {cfg.environment:<40s}║")
    print(f"║  Interval     : {str(cfg.collect_interval) + 's':<40s}║")
    print(f"║  Signals      : {', '.join(signals):<40s}║")
    print(f"║  Log Level    : {cfg.log_level.upper():<40s}║")

    # Task 21: Show file log sources in banner
    if cfg.log_sources:
        print(f"║  Log Sources  : {str(len(cfg.log_sources)) + ' file(s)':<40s}║")
        for src in cfg.log_sources:
            display = src if len(src) <= 38 else "…" + src[-(38-1):]
            print(f"║    → {display:<52s}║")
    else:
        print(f"║  Log Sources  : {'internal only':<40s}║")

    print("╚══════════════════════════════════════════════════════════╝")
    print()


# ── Main loop ───────────────────────────────────────────────────

def run(cfg: CollectorConfig) -> None:
    cycle = 0

    _print_banner(cfg)

    # Preflight connectivity check
    logger.info("Running preflight connectivity check…")
    if preflight_check(cfg):
        logger.info(f"✓ API reachable at {mask_url(cfg.api_url)}")
    else:
        logger.warning(
            f"✗ Cannot reach API at {mask_url(cfg.api_url)} — "
            f"collector will retry each cycle"
        )

    logger.info("Collector running. Press Ctrl+C to stop.")

    while _running:
        cycle += 1
        tracer = CycleTracer(cfg, cycle)
        t0 = time.monotonic()
        signals_ok = 0
        signals_fail = 0
        signals_total = 0
        signal_results: list[str] = []

        # ── Metrics ──────────────────────────────────────────
        if cfg.enable_metrics:
            signals_total += 1
            with tracer.child("send_metrics") as span:
                try:
                    samples = collect_metrics(cfg)
                    ok = send_metrics(cfg, samples)
                    if ok:
                        signals_ok += 1
                        signal_results.append("metrics:✓")
                    else:
                        signals_fail += 1
                        signal_results.append("metrics:✗")
                        span.set_error("HTTP error")
                except Exception as exc:
                    signals_fail += 1
                    signal_results.append("metrics:✗")
                    span.set_error(str(exc))
                    logger.error(f"Metrics collection failed: {exc}")

        # ── Logs (internal + file sources) ───────────────────
        if cfg.enable_logs:
            signals_total += 1
            with tracer.child("send_logs") as span:
                try:
                    entries = collect_logs(cfg)
                    if entries:
                        ok = send_logs(cfg, entries)
                        if ok:
                            signals_ok += 1
                            signal_results.append(f"logs:✓({len(entries)})")
                        else:
                            signals_fail += 1
                            signal_results.append("logs:✗")
                            span.set_error("HTTP error")
                    else:
                        # No buffered logs this cycle — still OK
                        signals_ok += 1
                        signal_results.append("logs:✓(0)")
                        span.attributes["note"] = "no_buffered_logs"
                except Exception as exc:
                    signals_fail += 1
                    signal_results.append("logs:✗")
                    span.set_error(str(exc))
                    logger.error(f"Log collection failed: {exc}")

        # ── Traces ───────────────────────────────────────────
        if cfg.enable_traces:
            signals_total += 1
            cycle_spans = tracer.finish()
            try:
                ok = send_traces(cfg, cycle_spans)
                if ok:
                    signals_ok += 1
                    signal_results.append(f"traces:✓({len(cycle_spans)})")
                else:
                    signals_fail += 1
                    signal_results.append("traces:✗")
            except Exception as exc:
                signals_fail += 1
                signal_results.append("traces:✗")
                logger.error(f"Trace send failed: {exc}")

        elapsed = round((time.monotonic() - t0) * 1000)
        status_icon = "✓" if signals_fail == 0 else "⚠" if signals_ok > 0 else "✗"
        logger.info(
            f"Cycle {cycle} {status_icon} — "
            f"{signals_ok}/{signals_total} OK — "
            f"[{' | '.join(signal_results)}] — "
            f"{elapsed}ms"
        )

        # ── Sleep (interruptible) ────────────────────────────
        deadline = time.monotonic() + cfg.collect_interval
        while _running and time.monotonic() < deadline:
            time.sleep(0.5)

    logger.info("Collector stopped cleanly.")


# ── Entry point ─────────────────────────────────────────────────

def main() -> None:
    # Pre-load config to get log_level before setting up logging
    import os
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    setup_logging(log_level)
    install_log_capture()
    cfg = load_config()
    # Re-apply with final config log level
    setup_logging(cfg.log_level)
    run(cfg)


if __name__ == "__main__":
    main()
