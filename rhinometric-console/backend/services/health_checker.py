"""
Background Health Checker for External Services - Hardened Edition.

Runs as an asyncio background task inside the FastAPI process.
Every POLL_INTERVAL seconds it:
  1. Queries all enabled services whose last_check_at + check_interval has passed.
  2. Runs the appropriate test (HTTP or PostgreSQL) in a thread pool.
  3. Updates status, latency, message in the DB.
  4. Inserts a row into external_service_checks (Phase 3 - History).
  5. Updates Prometheus gauges/counters/histograms (Phase 4+6 - Metrics).
  6. Detects incidents (UP->DOWN transitions) and tracks consecutive failures.
  7. Checks SSL certificate expiry for HTTPS endpoints.
  8. Computes composite health score per service.

Hardened for 15-second check intervals at scale:
  - Configurable thread pool (HEALTH_CHECK_MAX_WORKERS env, default 20)
  - Per-check asyncio.wait_for() timeout isolation
  - Cycle overrun detection with structured logging
  - Deterministic jitter/stagger to prevent thundering herd
  - Shared httpx.Client connection pool for HTTP checks

No extra dependencies (APScheduler, Celery) required.
"""

import asyncio
import hashlib
import logging
import os
import ssl
import socket
import time as _time_mod
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Tuple

from database import SessionLocal
from models.external_service import ExternalService, ServiceType, ServiceStatus, MonitoringMode, TelemetryStatus
from models.external_service_check import ExternalServiceCheck
from services.connector_service import test_http_connection, test_postgresql_connection
from metrics import (
    external_service_up,
    external_service_latency_ms,
    external_service_checks_total,
    external_service_latency_histogram,
    external_service_incidents_total,
    external_service_consecutive_failures,
    external_service_last_success_timestamp,
    external_service_last_check_timestamp,
    external_service_ssl_expiry_days,
    external_service_health_score,
)

from services.retention_cleanup import run_cleanup as _run_retention_cleanup, get_retention_days
from services.state_repository import ensure_schema as _ensure_state_schema, load_all_states as _load_all_states, persist_state as _persist_state

from models.service_assertion import ServiceAssertion
from models.assertion_result import AssertionResult
from services.assertion_evaluator import evaluate_assertions, needs_body_capture

logger = logging.getLogger("rhinometric.health_checker")

# ── Configuration ───────────────────────────────────────────────

# Retention cleanup state - runs once per day
_last_cleanup_epoch: float = 0.0
_CLEANUP_INTERVAL = 86400  # 24 hours in seconds

# How often the scheduler loop wakes up (seconds)
POLL_INTERVAL = 15

# Default check interval for services (seconds) — centralized constant
DEFAULT_CHECK_INTERVAL = 15

# Telemetry stale threshold (minutes with no data)
STALE_MINUTES = 10

# Thread pool for blocking I/O (HTTP requests, PG connections)
# Configurable via HEALTH_CHECK_MAX_WORKERS env var; default 20
_MAX_WORKERS = int(os.environ.get("HEALTH_CHECK_MAX_WORKERS", "20"))
_executor = ThreadPoolExecutor(max_workers=_MAX_WORKERS, thread_name_prefix="health-check")

# Asyncio semaphore gates concurrent check dispatch so tasks only
# start their timeout countdown after acquiring a worker slot.
# This prevents queue-induced timeouts when services >> workers.
_concurrency_gate: Optional[asyncio.Semaphore] = None  # initialized in event loop

# Per-check timeout guard (seconds). If a single check (including DB write)
# takes longer than this, the task is cancelled. This prevents one slow
# service from blocking the entire cycle.
# Set tight (8s) for 300-endpoint scale. Per-service HTTP/PG
# timeout is capped to (_PER_CHECK_TIMEOUT - 1) so transport times out first.
_PER_CHECK_TIMEOUT = int(os.environ.get("HEALTH_CHECK_TASK_TIMEOUT", "8"))

# Control flag
_running = False
_task: Optional[asyncio.Task] = None

# ── In-memory state tracking ────────────────────────────────────

# Previous status per service_id  (used to detect UP->DOWN transitions)
_previous_status: Dict[int, str] = {}

# Consecutive failure count per service_id
_consecutive_failures: Dict[int, int] = {}

# Rolling window of recent checks for health score calculation
# Key: service_id, Value: list of (timestamp, success_bool, latency_ms)
_recent_checks: Dict[int, list] = {}
HEALTH_WINDOW_SIZE = 60  # keep last 60 checks (~15min at 15s interval)

# SSL cert cache: {url: (expiry_days, last_checked_epoch)}
_ssl_cache: Dict[str, Tuple[float, float]] = {}
SSL_CHECK_INTERVAL = 3600  # Re-check SSL every hour

# Assertion cache: service_id -> list of enabled assertions (sorted by order)
_assertion_cache: Dict[int, list] = {}
_assertion_cache_ts: float = 0.0
_ASSERTION_CACHE_TTL: float = 60.0  # Refresh every 60 seconds


# ── Stale metric label cleanup ──────────────────────────────────
# Tracks (service_name, service_type, group_name) tuples that have been emitted.
# On each scheduler iteration, label sets for deleted/disabled services are removed.
_known_metric_labels: set = set()


def _refresh_assertion_cache():
    """Reload enabled assertions from DB, grouped by service_id."""
    global _assertion_cache, _assertion_cache_ts
    db = SessionLocal()
    try:
        rows = (
            db.query(ServiceAssertion)
            .filter(ServiceAssertion.enabled == True)
            .order_by(ServiceAssertion.service_id, ServiceAssertion.order)
            .all()
        )
        new_cache: Dict[int, list] = {}
        for a in rows:
            new_cache.setdefault(a.service_id, []).append(a)
            db.expunge(a)
        _assertion_cache = new_cache
        _assertion_cache_ts = _time_mod.time()
        logger.debug("[Assertions] Cache refreshed: %d assertions for %d services", len(rows), len(new_cache))
    except Exception as exc:
        logger.warning("[Assertions] Cache refresh failed: %s", exc)
    finally:
        db.close()


def _cleanup_stale_metrics(active_services):
    """
    Remove prometheus_client label sets for services no longer in the DB.

    This is called each scheduler iteration with the current list of enabled
    services. Any previously-tracked label tuple not in the active set is
    removed from all external_service_* metrics, preventing stale data
    from being exposed on /metrics.
    """
    global _known_metric_labels

    # Build active label tuples from current DB services
    active_labels = set()
    for svc in active_services:
        svc_type = svc.service_type.value if hasattr(svc.service_type, 'value') else str(svc.service_type)
        group = svc.group_name or "default"
        active_labels.add((svc.name, svc_type, group))

    # Find orphaned label sets (previously known but no longer active)
    orphaned = _known_metric_labels - active_labels
    if orphaned:
        logger.info(f"[MetricCleanup] Removing stale metrics for {len(orphaned)} deleted service(s): "
                     f"{[o[0] for o in orphaned]}")

        for svc_name, svc_type, group_name in orphaned:
            for metric_obj in [
                external_service_up,
                external_service_latency_ms,
                external_service_consecutive_failures,
                external_service_last_success_timestamp,
                external_service_last_check_timestamp,
                external_service_ssl_expiry_days,
                external_service_health_score,
            ]:
                try:
                    metric_obj.remove(svc_name, svc_type, group_name)
                except KeyError:
                    pass  # Label combo never existed for this metric
                except Exception as e:
                    logger.debug(f"[MetricCleanup] Could not remove {metric_obj._name} "
                                 f"for {svc_name}: {e}")

            # Counter with result label (success/failure)
            for result_val in ["success", "failure"]:
                try:
                    external_service_checks_total.remove(svc_name, svc_type, group_name, result_val)
                except KeyError:
                    pass
                except Exception as e:
                    logger.debug(f"[MetricCleanup] Could not remove checks_total "
                                 f"for {svc_name}/{result_val}: {e}")

            # Histogram
            try:
                external_service_latency_histogram.remove(svc_name, svc_type, group_name)
            except KeyError:
                pass
            except Exception as e:
                logger.debug(f"[MetricCleanup] Could not remove histogram for {svc_name}: {e}")

            # Incidents counter
            try:
                external_service_incidents_total.remove(svc_name, svc_type, group_name)
            except KeyError:
                pass
            except Exception as e:
                logger.debug(f"[MetricCleanup] Could not remove incidents for {svc_name}: {e}")

        logger.info(f"[MetricCleanup] Cleanup complete — removed labels for: "
                     f"{[o[0] for o in orphaned]}")

    # Update tracked set to current active
    _known_metric_labels = active_labels



# ── SSL Certificate Checker ─────────────────────────────────────

def _check_ssl_expiry(url: str) -> Optional[float]:
    """Check days until SSL certificate expires for an HTTPS URL."""
    try:
        if not url.startswith("https://"):
            return None

        # Parse hostname from URL
        hostname = url.split("://")[1].split("/")[0].split(":")[0]
        port = 443

        # Check if port is specified
        host_parts = url.split("://")[1].split("/")[0]
        if ":" in host_parts:
            parts = host_parts.rsplit(":", 1)
            hostname = parts[0]
            try:
                port = int(parts[1])
            except ValueError:
                port = 443

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Also try with verification for expiry
        verify_ctx = ssl.create_default_context()

        with socket.create_connection((hostname, port), timeout=5) as sock:
            with verify_ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                if cert and "notAfter" in cert:
                    expiry_str = cert["notAfter"]
                    # Format: 'Mar  9 12:00:00 2027 GMT'
                    expiry_dt = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")
                    expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    days_left = (expiry_dt - now).total_seconds() / 86400
                    return round(days_left, 1)
        return None
    except Exception as e:
        logger.debug(f"[SSL] Could not check cert for {url}: {e}")
        # Try without verification - just get expiry
        try:
            hostname = url.split("://")[1].split("/")[0].split(":")[0]
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            with socket.create_connection((hostname, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Binary DER cert
                    der_cert = ssock.getpeercert(binary_form=True)
                    if der_cert:
                        # Decode using ssl
                        pem_cert = ssl.DER_cert_to_PEM_cert(der_cert)
                        # Can't easily parse without cryptography lib
                        # Return None gracefully
                        pass
            return None
        except Exception:
            return None


def _get_ssl_expiry_cached(url: str, service_name: str, group_name: str = "default") -> Optional[float]:
    """Get SSL expiry days with caching (re-check every SSL_CHECK_INTERVAL)."""
    now_epoch = datetime.now(timezone.utc).timestamp()

    if url in _ssl_cache:
        cached_days, last_checked = _ssl_cache[url]
        if now_epoch - last_checked < SSL_CHECK_INTERVAL:
            return cached_days

    days = _check_ssl_expiry(url)
    if days is not None:
        _ssl_cache[url] = (days, now_epoch)
        try:
            external_service_ssl_expiry_days.labels(service_name=service_name, group_name=group_name).set(days)
        except Exception:
            pass
        logger.info(f"[SSL] {service_name}: certificate expires in {days:.0f} days")
    return days


# ── Health Score Calculator ──────────────────────────────────────

def _compute_health_score(service_id: int, service_name: str, service_type: str, group_name: str = "default") -> float:
    """
    Compute a 0-100 health score based on:
      - Uptime ratio (50% weight): % of recent checks that succeeded
      - Latency score (30% weight): lower avg latency = higher score
      - Stability score (20% weight): fewer consecutive failures = higher score
    """
    checks = _recent_checks.get(service_id, [])
    if not checks:
        return 50.0  # Unknown = neutral

    # Uptime ratio (0-1)
    successes = sum(1 for _, ok, _ in checks if ok)
    uptime_ratio = successes / len(checks)

    # Avg latency score (0-1): 0ms=1.0, 1000ms=0.5, 5000ms+=0.0
    latencies = [lat for _, _, lat in checks if lat and lat > 0]
    if latencies:
        avg_lat = sum(latencies) / len(latencies)
        if avg_lat <= 100:
            latency_score = 1.0
        elif avg_lat <= 500:
            latency_score = 1.0 - (avg_lat - 100) / 800  # 100->1.0, 500->0.5
        elif avg_lat <= 2000:
            latency_score = 0.5 - (avg_lat - 500) / 3000  # 500->0.5, 2000->0.0
        else:
            latency_score = 0.0
    else:
        latency_score = 0.5

    # Stability score (0-1): 0 consecutive failures=1.0, 5+=0.0
    consec = _consecutive_failures.get(service_id, 0)
    stability_score = max(0.0, 1.0 - (consec / 5.0))

    # Weighted combination
    score = (uptime_ratio * 50) + (latency_score * 30) + (stability_score * 20)
    score = round(min(100.0, max(0.0, score)), 1)

    try:
        external_service_health_score.labels(
            service_name=service_name, service_type=service_type, group_name=group_name
        ).set(score)
    except Exception:
        pass

    return score


# ── Jitter / Stagger ────────────────────────────────────────────

def _compute_stagger_offset(service_id: int, interval: int) -> float:
    """
    Return a deterministic phase offset in [0, interval) seconds for this
    service.  The offset is stable across restarts (derived from
    service_id) so services keep their assigned slot.

    This spreads due-times evenly across the interval window,
    preventing all services from becoming due at the same instant.
    """
    # Use a hash of the service_id to get a stable float in [0, 1)
    h = hashlib.md5(str(service_id).encode()).hexdigest()
    frac = int(h[:8], 16) / 0xFFFFFFFF  # 0.0 .. 1.0
    return frac * interval


# ── Core Check Logic ─────────────────────────────────────────────

def _check_service(svc_id: int, svc_type: str, config: dict, timeout: int, capture_body: bool = False) -> dict:
    """Run a single service check (blocking - runs in thread pool)."""
    try:
        if svc_type == "http":
            return test_http_connection(
                url=config.get("url", ""),
                method=config.get("method", "GET"),
                health_path=config.get("health_path", ""),
                headers=config.get("headers"),
                auth_type=config.get("auth_type"),
                auth_value=config.get("auth_value"),
                timeout_seconds=timeout,
                service_name=config.get("name", f"svc-{svc_id}"),
                capture_body=capture_body,
            )
        elif svc_type == "postgresql":
            return test_postgresql_connection(
                host=config.get("host", "localhost"),
                port=int(config.get("port", 5432)),
                database_name=config.get("database_name", "postgres"),
                username=config.get("username", "postgres"),
                password=config.get("password", ""),
                ssl_mode=config.get("ssl_mode", "prefer"),
                timeout_seconds=timeout,
            )
        else:
            return {"success": False, "status": "error", "message": f"Unknown type: {svc_type}",
                    "response_time_ms": 0, "status_code": None}
    except Exception as e:
        return {"success": False, "status": "error", "message": str(e)[:300],
                "response_time_ms": 0, "status_code": None}


async def _check_one(svc_id: int, svc_name: str, svc_type: str, config: dict, timeout: int, group_name: str = "default"):
    """Run a check in the thread pool, update DB, insert history, evaluate assertions, update metrics."""
    # -- Determine if body capture is needed for assertions --
    assertions = _assertion_cache.get(svc_id, [])
    capture_body = bool(assertions) and svc_type == "http" and needs_body_capture(assertions)

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        _executor, _check_service, svc_id, svc_type, config, timeout, capture_body,
    )

    now = datetime.now(timezone.utc)
    now_epoch = now.timestamp()
    check_status = result.get("status", "error")
    is_success = result.get("success", False)
    latency = result.get("response_time_ms", 0) or 0

    # -- Evaluate assertions (skip when service is DOWN/error) --
    assertion_eval_results = []
    a_total = a_passed = a_failed = 0
    first_fail_name = None
    first_fail_msg = None

    if assertions and check_status not in ("down", "error"):
        response_body = result.get("response_body")
        try:
            assertion_eval_results = evaluate_assertions(assertions, result, response_body)
            a_total = len(assertion_eval_results)
            a_passed = sum(1 for r in assertion_eval_results if r["passed"])
            a_failed = a_total - a_passed
            for r in assertion_eval_results:
                if not r["passed"]:
                    first_fail_name = r["assertion_name"]
                    first_fail_msg = r.get("error_message") or (
                        f"expected {r['expected_value']}, got {r['actual_value']}"
                    )
                    break
            if a_failed:
                logger.info("[Assertions] %s: %d/%d failed (first: %s)", svc_name, a_failed, a_total, first_fail_name)
        except Exception as _ae:
            logger.warning("[Assertions] Evaluation error for %s: %s", svc_name, _ae)

    # ── Incident Detection (UP->DOWN transition) ──
    prev = _previous_status.get(svc_id)
    if prev in ("up", "degraded") and check_status == "down":
        try:
            external_service_incidents_total.labels(
                service_name=svc_name, service_type=svc_type, group_name=group_name
            ).inc()
        except Exception:
            pass
        logger.warning(f"[INCIDENT] {svc_name} ({svc_type}): {prev} -> DOWN")
    _previous_status[svc_id] = check_status

    # ── Consecutive Failures ──
    if not is_success:
        _consecutive_failures[svc_id] = _consecutive_failures.get(svc_id, 0) + 1
    else:
        _consecutive_failures[svc_id] = 0

    consec = _consecutive_failures[svc_id]
    try:
        external_service_consecutive_failures.labels(
            service_name=svc_name, service_type=svc_type, group_name=group_name
        ).set(consec)
    except Exception:
        pass

    # ── Rolling window for health score ──
    if svc_id not in _recent_checks:
        _recent_checks[svc_id] = []
    _recent_checks[svc_id].append((now_epoch, is_success, latency))
    if len(_recent_checks[svc_id]) > HEALTH_WINDOW_SIZE:
        _recent_checks[svc_id] = _recent_checks[svc_id][-HEALTH_WINDOW_SIZE:]

    # ── Update DB ──
    db = SessionLocal()
    try:
        svc = db.query(ExternalService).filter(ExternalService.id == svc_id).first()
        if svc:
            svc.status = check_status
            svc.status_message = result.get("message", "")[:500]
            svc.last_response_time_ms = result.get("response_time_ms")
            svc.last_status_code = result.get("status_code")
            svc.last_check_at = now

            # Phase 3: Insert check history record
            check_record = ExternalServiceCheck(
                service_id=svc_id,
                status=check_status,
                response_time_ms=result.get("response_time_ms"),
                status_code=result.get("status_code"),
                message=result.get("message", "")[:500],
                checked_at=now,
                # Phase 2: assertion summary
                assertions_total=a_total,
                assertions_passed=a_passed,
                assertions_failed=a_failed,
                first_failed_assertion=(first_fail_name or "")[:255] or None,
                first_failed_message=(first_fail_msg or "")[:500] or None,
            )
            db.add(check_record)

            # Phase 2: persist FAILED assertion results
            if a_failed and assertion_eval_results:
                db.flush()  # materialise check_record.id
                for _ar in assertion_eval_results:
                    if not _ar["passed"]:
                        db.add(AssertionResult(
                            check_id=check_record.id,
                            assertion_id=_ar["assertion_id"],
                            service_id=svc_id,
                            assertion_type=_ar["assertion_type"],
                            assertion_name=_ar.get("assertion_name"),
                            expected_value=_ar["expected_value"],
                            actual_value=_ar.get("actual_value"),
                            error_message=_ar.get("error_message"),
                            evaluated_at=now,
                        ))

            db.commit()
            logger.info(f"[HealthCheck] {svc_name} ({svc_type}) -> {check_status} ({latency:.0f}ms) [score={_compute_health_score(svc_id, svc_name, svc_type, group_name):.0f}]")

            # Persist health checker state to DB (survives restarts)
            try:
                _persist_state(
                    svc_id,
                    status=check_status,
                    consecutive_failures=consec,
                    is_success=is_success,
                )
            except Exception as pe:
                logger.warning(f"[HealthCheck] State persist failed for svc_id={svc_id}: {pe}")

    except Exception as e:
        db.rollback()
        logger.error(f"[HealthCheck] DB update failed for svc_id={svc_id}: {e}")
    finally:
        db.close()

    # ── Phase 4+6: Update all Prometheus metrics (outside DB session) ──
    try:
        is_up = 1 if check_status == "up" else 0
        external_service_up.labels(service_name=svc_name, service_type=svc_type, group_name=group_name).set(is_up)
        external_service_latency_ms.labels(service_name=svc_name, service_type=svc_type, group_name=group_name).set(latency)

        # Histogram for percentiles (in seconds)
        external_service_latency_histogram.labels(
            service_name=svc_name, service_type=svc_type, group_name=group_name
        ).observe(latency / 1000.0)

        check_result = "success" if is_success else "failure"
        external_service_checks_total.labels(
            service_name=svc_name, service_type=svc_type, group_name=group_name, result=check_result
        ).inc()

        # Last check timestamp
        external_service_last_check_timestamp.labels(
            service_name=svc_name, service_type=svc_type, group_name=group_name
        ).set(now_epoch)

        # Last success timestamp
        if is_success:
            external_service_last_success_timestamp.labels(
                service_name=svc_name, service_type=svc_type, group_name=group_name
            ).set(now_epoch)

    except Exception as e:
        logger.warning(f"[HealthCheck] Prometheus metric update error: {e}")

    # ── SSL Certificate check (HTTPS only, cached) ──
    if svc_type == "http":
        url = config.get("url", "")
        if url.startswith("https://"):
            try:
                await loop.run_in_executor(_executor, _get_ssl_expiry_cached, url, svc_name, group_name)
            except Exception as e:
                logger.debug(f"[SSL] Error checking {svc_name}: {e}")



# ── Telemetry stale detection ───────────────────────────────────

def _check_stale_telemetry():
    """Mark services as STALE if no telemetry received in STALE_MINUTES."""
    try:
        db = SessionLocal()
        now = datetime.now(timezone.utc)
        threshold = now - timedelta(minutes=STALE_MINUTES)

        stale_candidates = (
            db.query(ExternalService)
            .filter(
                ExternalService.monitoring_mode == MonitoringMode.TELEMETRY_ENABLED,
                ExternalService.telemetry_status == TelemetryStatus.RECEIVING_DATA,
                ExternalService.last_telemetry_at != None,
                ExternalService.last_telemetry_at < threshold,
            )
            .all()
        )

        for svc in stale_candidates:
            svc.telemetry_status = TelemetryStatus.STALE
            logger.info(f"[Stale] Service '{svc.name}' (id={svc.id}) marked STALE — last data at {svc.last_telemetry_at}")

        if stale_candidates:
            db.commit()
            logger.info(f"[Stale] Marked {len(stale_candidates)} service(s) as STALE")

        db.close()
    except Exception as e:
        logger.warning(f"[Stale] Detection error: {e}")

async def _run_guarded(svc_name: str, coro):
    """Acquire concurrency slot, then run check with timeout guard.

    The semaphore prevents tasks from starting their timeout countdown
    while waiting in queue — only tasks with a worker slot begin the clock.
    This is critical at scale: with 300 services and 20 workers, tasks
    15-300 would otherwise timeout before even starting.
    """
    async with _concurrency_gate:
        return await asyncio.wait_for(coro, timeout=_PER_CHECK_TIMEOUT)


async def _scheduler_loop():
    """Main loop: poll DB, dispatch checks for due services with hardened execution."""
    global _running, _concurrency_gate
    _concurrency_gate = asyncio.Semaphore(_MAX_WORKERS)
    logger.info(
        f"[HealthCheck] Scheduler started (poll every {POLL_INTERVAL}s, "
        f"max_workers={_MAX_WORKERS}, per_check_timeout={_PER_CHECK_TIMEOUT}s, "
        f"default_interval={DEFAULT_CHECK_INTERVAL}s)"
    )

    while _running:
        cycle_start = _time_mod.monotonic()
        due_count = 0

        # Refresh assertion cache if stale
        if _time_mod.time() - _assertion_cache_ts >= _ASSERTION_CACHE_TTL:
            try:
                _refresh_assertion_cache()
            except Exception as _acerr:
                logger.warning("[HealthCheck] Assertion cache refresh error: %s", _acerr)

        try:
            db = SessionLocal()
            now = datetime.now(timezone.utc)

            # Get all enabled services
            services = db.query(ExternalService).filter(ExternalService.enabled == True).all()

            # ── Cleanup stale metric labels for deleted services ──
            try:
                _cleanup_stale_metrics(services)
            except Exception as _cleanup_metrics_err:
                logger.warning("[HealthCheck] Metric cleanup error: %s", _cleanup_metrics_err)

            due = []
            for svc in services:
                interval = svc.check_interval_seconds or DEFAULT_CHECK_INTERVAL
                # Apply deterministic stagger offset based on service ID
                stagger = _compute_stagger_offset(svc.id, interval)
                if svc.last_check_at is None:
                    due.append(svc)
                else:
                    # next_check = last_check + interval + stagger_offset
                    # The stagger offset is applied once at the first scheduling;
                    # after that the service is checked at regular intervals.
                    # We use a simpler model: check is due when
                    # now >= last_check_at + interval
                    # but stagger the *initial* due time by offsetting
                    # last_check_at forward on first-ever cycle.
                    next_check = svc.last_check_at + timedelta(seconds=interval)
                    if now >= next_check:
                        due.append(svc)

            db.close()
            due_count = len(due)

            if due:
                logger.info(f"[HealthCheck] {due_count} service(s) due for check")
                tasks = []
                for svc in due:
                    svc_type_str = svc.service_type.value if hasattr(svc.service_type, 'value') else str(svc.service_type)
                    coro = _check_one(
                        svc.id,
                        svc.name,
                        svc_type_str,
                        dict(svc.config) if svc.config else {},
                        min(svc.timeout_seconds or 10, _PER_CHECK_TIMEOUT - 1),
                        group_name=svc.group_name or "default",
                    )
                    # Semaphore-gated: fair slot acquisition before timeout clock starts.
                    tasks.append(_run_guarded(svc.name, coro))

                # Execute all checks concurrently; return_exceptions=True
                # ensures one failure doesn't cancel the rest.
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Log any per-check timeout or unexpected errors
                for i, res in enumerate(results):
                    if isinstance(res, asyncio.TimeoutError):
                        svc = due[i]
                        logger.error(
                            f"[HealthCheck] TIMEOUT: {svc.name} exceeded per-check limit "
                            f"of {_PER_CHECK_TIMEOUT}s — skipped this cycle"
                        )
                    elif isinstance(res, Exception):
                        svc = due[i]
                        logger.error(
                            f"[HealthCheck] ERROR: {svc.name} raised {type(res).__name__}: {res}"
                        )

            # ── Alert rule evaluation against recent check data ──
            try:
                from routers.alert_rules import evaluate_alert_rules as _eval_rules
                _alert_db = SessionLocal()
                _eval_rules(_alert_db)
                _alert_db.close()
            except Exception as _alert_err:
                logger.error(f"[HealthCheck] Alert rule evaluation error: {_alert_err}")

        except Exception as e:
            logger.error(f"[HealthCheck] Scheduler loop error: {e}")

        # ── Cycle overrun detection ──
        cycle_duration = _time_mod.monotonic() - cycle_start
        if due_count > 0:
            if cycle_duration > POLL_INTERVAL:
                logger.warning(
                    f"[HealthCheck] CYCLE OVERRUN: {cycle_duration:.2f}s > {POLL_INTERVAL}s target "
                    f"(due={due_count}, workers={_MAX_WORKERS})"
                )
            else:
                logger.info(
                    f"[HealthCheck] Cycle complete: {cycle_duration:.2f}s "
                    f"(due={due_count}, budget={POLL_INTERVAL}s)"
                )

        # -- Daily retention cleanup (non-blocking) --
        try:
            global _last_cleanup_epoch
            _now_epoch = _time_mod.time()
            if _now_epoch - _last_cleanup_epoch >= _CLEANUP_INTERVAL:
                _last_cleanup_epoch = _now_epoch
                loop = asyncio.get_event_loop()
                logger.info("[HealthCheck] Running daily retention cleanup...")
                deleted, dur = await loop.run_in_executor(_executor, _run_retention_cleanup)
                if deleted > 0:
                    logger.info("[HealthCheck] Retention cleanup: removed %d old checks in %ss", deleted, dur)
        except Exception as _cleanup_err:
            logger.warning("[HealthCheck] Retention cleanup error: %s", _cleanup_err)

        # -- Telemetry stale detection --
        try:
            _check_stale_telemetry()
        except Exception as _stale_err:
            logger.warning("[HealthCheck] Stale detection error: %s", _stale_err)

        # Sleep for remaining budget (skip if overrun)
        remaining = POLL_INTERVAL - (_time_mod.monotonic() - cycle_start)
        if remaining > 0:
            await asyncio.sleep(remaining)
        else:
            # Cycle took longer than POLL_INTERVAL — start next immediately
            logger.debug("[HealthCheck] Skipping sleep — cycle overrun, starting next cycle immediately")
            await asyncio.sleep(0)  # yield to event loop

    logger.info("[HealthCheck] Scheduler stopped")


def _restore_state_from_db():
    """
    Restore in-memory health checker state from PostgreSQL.
    Called once on startup before the scheduler loop begins.
    Ensures consecutive_failures, previous_status survive restarts.
    """
    try:
        _ensure_state_schema()
    except Exception as e:
        logger.error("[HealthCheck] State schema migration failed: %s", e)
        return

    states = _load_all_states()
    restored = 0
    for s in states:
        svc_id = s["id"]
        _previous_status[svc_id] = s["status"]
        _consecutive_failures[svc_id] = s["consecutive_failures"]
        restored += 1
    logger.info("[HealthCheck] Restored persistent state for %d services", restored)


async def _apply_initial_stagger():
    """
    One-time stagger application on startup: for every enabled service
    that already has a last_check_at, nudge it by the service's stagger
    offset so that services spread out naturally from the next cycle.

    This runs once after state restore and before the scheduler loop
    begins processing.
    """
    try:
        db = SessionLocal()
        now = datetime.now(timezone.utc)
        services = db.query(ExternalService).filter(ExternalService.enabled == True).all()
        staggered = 0
        for svc in services:
            interval = svc.check_interval_seconds or DEFAULT_CHECK_INTERVAL
            offset = _compute_stagger_offset(svc.id, interval)
            if svc.last_check_at is not None:
                # Set last_check_at so that (last_check_at + interval + offset) distributes
                # due times across the interval window.  We set:
                # last_check_at = now - interval + offset
                # This means the service becomes due at now + offset.
                svc.last_check_at = now - timedelta(seconds=interval) + timedelta(seconds=offset)
                staggered += 1
        db.commit()
        db.close()
        if staggered:
            logger.info(f"[HealthCheck] Applied stagger offsets to {staggered} service(s)")
    except Exception as e:
        logger.warning(f"[HealthCheck] Stagger application error: {e}")


async def start_scheduler():
    """Start the background health-check scheduler."""
    global _running, _task
    if _running:
        return

    # Restore persisted state before starting the loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, _restore_state_from_db)

    # Apply stagger offsets so services spread across the interval
    await _apply_initial_stagger()

    _running = True
    _task = asyncio.create_task(_scheduler_loop())
    logger.info("[HealthCheck] Background scheduler launched")


async def stop_scheduler():
    """Stop the background health-check scheduler gracefully."""
    global _running, _task
    _running = False
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None
    _executor.shutdown(wait=False)
    logger.info("[HealthCheck] Background scheduler shut down")
