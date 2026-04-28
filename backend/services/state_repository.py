"""
Persistent state repository for the External Services health checker.

Stores and restores per-service operational state (consecutive failures,
last success/failure timestamps) in the external_services table.

This ensures monitoring state survives backend container restarts.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from database import SessionLocal

logger = logging.getLogger("rhinometric.state_repository")


# ── Schema Migration ─────────────────────────────────────────────

_MIGRATION_COLUMNS = [
    ("consecutive_failures", "INTEGER NOT NULL DEFAULT 0"),
    ("last_success_at", "TIMESTAMPTZ"),
    ("last_failure_at", "TIMESTAMPTZ"),
    ("state_updated_at", "TIMESTAMPTZ"),
]


def ensure_schema():
    """
    Ensure the state columns exist on external_services.
    Uses ADD COLUMN IF NOT EXISTS for idempotent migration.
    Safe to call on every startup.
    """
    db = SessionLocal()
    try:
        for col_name, col_def in _MIGRATION_COLUMNS:
            db.execute(text(
                f"ALTER TABLE external_services "
                f"ADD COLUMN IF NOT EXISTS {col_name} {col_def};"
            ))
        db.commit()
        logger.info("[StateRepo] Schema migration complete — state columns verified")
    except Exception as e:
        db.rollback()
        logger.error("[StateRepo] Schema migration failed: %s", e)
        raise
    finally:
        db.close()


# ── Load All State ───────────────────────────────────────────────

def load_all_states() -> List[Dict[str, Any]]:
    """
    Load persisted state for all services.
    Returns list of dicts with keys:
        id, name, service_type, status, consecutive_failures,
        last_success_at, last_failure_at, state_updated_at
    """
    db = SessionLocal()
    try:
        rows = db.execute(text(
            "SELECT id, name, "
            "       COALESCE(status::text, 'unknown') AS status, "
            "       COALESCE(consecutive_failures, 0) AS consecutive_failures, "
            "       last_success_at, "
            "       last_failure_at, "
            "       state_updated_at "
            "FROM external_services "
            "WHERE enabled = true"
        )).fetchall()

        result = []
        for r in rows:
            result.append({
                "id": r[0],
                "name": r[1],
                "status": r[2],
                "consecutive_failures": r[3],
                "last_success_at": r[4],
                "last_failure_at": r[5],
                "state_updated_at": r[6],
            })
        return result
    except Exception as e:
        logger.error("[StateRepo] Failed to load states: %s", e)
        return []
    finally:
        db.close()


# ── Persist State for One Service ────────────────────────────────

def persist_state(
    service_id: int,
    *,
    status: str,
    consecutive_failures: int,
    is_success: bool,
):
    """
    Atomically update the persisted state columns for a single service.
    Called after each health check completes.
    """
    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        params = {
            "svc_id": service_id,
            "consec": consecutive_failures,
            "state_ts": now,
        }

        if is_success:
            db.execute(text(
                "UPDATE external_services SET "
                "  consecutive_failures = :consec, "
                "  last_success_at = :state_ts, "
                "  state_updated_at = :state_ts "
                "WHERE id = :svc_id"
            ), params)
        else:
            db.execute(text(
                "UPDATE external_services SET "
                "  consecutive_failures = :consec, "
                "  last_failure_at = :state_ts, "
                "  state_updated_at = :state_ts "
                "WHERE id = :svc_id"
            ), params)

        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("[StateRepo] Failed to persist state for svc_id=%d: %s", service_id, e)
    finally:
        db.close()


# ── Clear State for Deleted Service ──────────────────────────────

def clear_in_memory_state(service_id: int):
    """
    Remove in-memory tracking for a deleted service.
    Called from the delete endpoint.
    DB columns are removed automatically when the row is deleted.
    """
    # Import here to avoid circular imports
    from services.health_checker import (
        _previous_status, _consecutive_failures, _recent_checks
    )
    _previous_status.pop(service_id, None)
    _consecutive_failures.pop(service_id, None)
    _recent_checks.pop(service_id, None)
    logger.info("[StateRepo] Cleared in-memory state for deleted service_id=%d", service_id)
