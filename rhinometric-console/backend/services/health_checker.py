"""
Background Health Checker for External Services - Intelligence Edition.

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

No extra dependencies (APScheduler, Celery) required.
"""

import asyncio
import logging
import ssl
import socket
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

logger = logging.getLogger("rhinometric.health_checker")

# Retention cleanup state - runs once per day
_last_cleanup_epoch: float = 0.0
_CLEANUP_INTERVAL = 86400  # 24 hours in seconds

# How often the scheduler loop wakes up (seconds)
POLL_INTERVAL = 15

# Telemetry stale threshold (minutes with no data)
STALE_MINUTES = 10

# Thread pool for blocking I/O (HTTP requests, PG connections)
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="health-check")

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


def _get_ssl_expiry_cached(url: str, service_name: str) -> Optional[float]:
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
            external_service_ssl_expiry_days.labels(service_name=service_name).set(days)
        except Exception:
            pass
        logger.info(f"[SSL] {service_name}: certificate expires in {days:.0f} days")
    return days


# ── Health Score Calculator ──────────────────────────────────────

def _compute_health_score(service_id: int, service_name: str, service_type: str) -> float:
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
            service_name=service_name, service_type=service_type
        ).set(score)
    except Exception:
        pass

    return score


# ── Core Check Logic ─────────────────────────────────────────────

def _check_service(svc_id: int, svc_type: str, config: dict, timeout: int) -> dict:
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


async def _check_one(svc_id: int, svc_name: str, svc_type: str, config: dict, timeout: int):
    """Run a check in the thread pool, update DB, insert history, update all metrics."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(_executor, _check_service, svc_id, svc_type, config, timeout)

    now = datetime.now(timezone.utc)
    now_epoch = now.timestamp()
    check_status = result.get("status", "error")
    is_success = result.get("success", False)
    latency = result.get("response_time_ms", 0) or 0

    # ── Incident Detection (UP->DOWN transition) ──
    prev = _previous_status.get(svc_id)
    if prev in ("up", "degraded") and check_status == "down":
        try:
            external_service_incidents_total.labels(
                service_name=svc_name, service_type=svc_type
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
            service_name=svc_name, service_type=svc_type
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
            )
            db.add(check_record)

            db.commit()
            logger.info(f"[HealthCheck] {svc_name} ({svc_type}) -> {check_status} ({latency:.0f}ms) [score={_compute_health_score(svc_id, svc_name, svc_type):.0f}]")

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
        external_service_up.labels(service_name=svc_name, service_type=svc_type).set(is_up)
        external_service_latency_ms.labels(service_name=svc_name, service_type=svc_type).set(latency)

        # Histogram for percentiles (in seconds)
        external_service_latency_histogram.labels(
            service_name=svc_name, service_type=svc_type
        ).observe(latency / 1000.0)

        check_result = "success" if is_success else "failure"
        external_service_checks_total.labels(
            service_name=svc_name, service_type=svc_type, result=check_result
        ).inc()

        # Last check timestamp
        external_service_last_check_timestamp.labels(
            service_name=svc_name, service_type=svc_type
        ).set(now_epoch)

        # Last success timestamp
        if is_success:
            external_service_last_success_timestamp.labels(
                service_name=svc_name, service_type=svc_type
            ).set(now_epoch)

    except Exception as e:
        logger.warning(f"[HealthCheck] Prometheus metric update error: {e}")

    # ── SSL Certificate check (HTTPS only, cached) ──
    if svc_type == "http":
        url = config.get("url", "")
        if url.startswith("https://"):
            try:
                await loop.run_in_executor(_executor, _get_ssl_expiry_cached, url, svc_name)
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

async def _scheduler_loop():
    """Main loop: poll DB, dispatch checks for due services."""
    global _running
    logger.info(f"[HealthCheck] Scheduler started (poll every {POLL_INTERVAL}s)")

    while _running:
        try:
            db = SessionLocal()
            now = datetime.now(timezone.utc)

            # Get all enabled services
            services = db.query(ExternalService).filter(ExternalService.enabled == True).all()

            due = []
            for svc in services:
                interval = svc.check_interval_seconds or 60
                if svc.last_check_at is None:
                    due.append(svc)
                else:
                    next_check = svc.last_check_at + timedelta(seconds=interval)
                    if now >= next_check:
                        due.append(svc)

            db.close()

            if due:
                logger.info(f"[HealthCheck] {len(due)} service(s) due for check")
                tasks = []
                for svc in due:
                    tasks.append(_check_one(
                        svc.id,
                        svc.name,
                        svc.service_type.value if hasattr(svc.service_type, 'value') else str(svc.service_type),
                        dict(svc.config) if svc.config else {},
                        svc.timeout_seconds or 10,
                    ))
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"[HealthCheck] Scheduler loop error: {e}")

        # -- Daily retention cleanup (non-blocking) --
        try:
            import time as _time_mod
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

        await asyncio.sleep(POLL_INTERVAL)

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


async def start_scheduler():
    """Start the background health-check scheduler."""
    global _running, _task
    if _running:
        return

    # Restore persisted state before starting the loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, _restore_state_from_db)

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
