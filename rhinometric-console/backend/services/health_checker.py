"""
Background Health Checker for External Services.

Runs as an asyncio background task inside the FastAPI process.
Every POLL_INTERVAL seconds it:
  1. Queries all enabled services whose last_check_at + check_interval has passed.
  2. Runs the appropriate test (HTTP or PostgreSQL) in a thread pool.
  3. Updates status, latency, message in the DB.

No extra dependencies (APScheduler, Celery) required.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from database import SessionLocal
from models.external_service import ExternalService, ServiceType, ServiceStatus
from services.connector_service import test_http_connection, test_postgresql_connection

logger = logging.getLogger("rhinometric.health_checker")

# How often the scheduler loop wakes up (seconds)
POLL_INTERVAL = 15

# Thread pool for blocking I/O (HTTP requests, PG connections)
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="health-check")

# Control flag
_running = False
_task: Optional[asyncio.Task] = None


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


async def _check_one(svc_id: int, svc_type: str, config: dict, timeout: int):
    """Run a check in the thread pool and update the DB."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(_executor, _check_service, svc_id, svc_type, config, timeout)

    # Update DB
    db = SessionLocal()
    try:
        svc = db.query(ExternalService).filter(ExternalService.id == svc_id).first()
        if svc:
            svc.status = result.get("status", "error")
            svc.status_message = result.get("message", "")[:500]
            svc.last_response_time_ms = result.get("response_time_ms")
            svc.last_status_code = result.get("status_code")
            svc.last_check_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"[HealthCheck] {svc.name} ({svc_type}) -> {result['status']} ({result.get('response_time_ms',0):.0f}ms)")
    except Exception as e:
        db.rollback()
        logger.error(f"[HealthCheck] DB update failed for svc_id={svc_id}: {e}")
    finally:
        db.close()


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
                        svc.service_type.value if hasattr(svc.service_type, 'value') else str(svc.service_type),
                        dict(svc.config) if svc.config else {},
                        svc.timeout_seconds or 10,
                    ))
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"[HealthCheck] Scheduler loop error: {e}")

        await asyncio.sleep(POLL_INTERVAL)

    logger.info("[HealthCheck] Scheduler stopped")


async def start_scheduler():
    """Start the background health-check scheduler."""
    global _running, _task
    if _running:
        return
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