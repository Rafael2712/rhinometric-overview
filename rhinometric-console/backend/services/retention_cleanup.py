"""
Data Retention & Cleanup for external_service_checks.

Provides batched deletion of check history older than a configurable
retention window.  Designed to run once per day inside the existing
health-checker scheduler without blocking check cycles.

Environment variable:
    EXTERNAL_SERVICE_CHECK_RETENTION_DAYS  (default 90, min 7, max 365)
"""

import logging
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Tuple

from sqlalchemy import text

from database import SessionLocal

logger = logging.getLogger("rhinometric.retention_cleanup")

# -- Configuration -------------------------------------------------------

_DEFAULT_RETENTION_DAYS = 90
_MIN_RETENTION_DAYS = 7
_MAX_RETENTION_DAYS = 365
_BATCH_SIZE = 5000          # rows deleted per batch to avoid long locks
_BATCH_SLEEP_SECS = 0.1    # short pause between batches to yield I/O


def get_retention_days() -> int:
    """Read and validate EXTERNAL_SERVICE_CHECK_RETENTION_DAYS from env."""
    raw = os.environ.get("EXTERNAL_SERVICE_CHECK_RETENTION_DAYS", str(_DEFAULT_RETENTION_DAYS))
    try:
        days = int(raw)
    except (ValueError, TypeError):
        logger.warning(
            "[retention] Invalid EXTERNAL_SERVICE_CHECK_RETENTION_DAYS='%s', "
            "using default %d", raw, _DEFAULT_RETENTION_DAYS
        )
        return _DEFAULT_RETENTION_DAYS

    if days < _MIN_RETENTION_DAYS:
        logger.warning(
            "[retention] EXTERNAL_SERVICE_CHECK_RETENTION_DAYS=%d below minimum, "
            "clamping to %d", days, _MIN_RETENTION_DAYS
        )
        return _MIN_RETENTION_DAYS
    if days > _MAX_RETENTION_DAYS:
        logger.warning(
            "[retention] EXTERNAL_SERVICE_CHECK_RETENTION_DAYS=%d above maximum, "
            "clamping to %d", days, _MAX_RETENTION_DAYS
        )
        return _MAX_RETENTION_DAYS

    return days


# -- Batched Cleanup ------------------------------------------------------

def run_cleanup(retention_days=None):
    """
    Delete external_service_checks rows older than *retention_days*.

    Uses batched DELETE with LIMIT to avoid locking the table for
    extended periods.

    Returns:
        (total_deleted, duration_seconds)
    """
    if retention_days is None:
        retention_days = get_retention_days()

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    total_deleted = 0
    t0 = time.monotonic()

    db = SessionLocal()
    try:
        while True:
            # ctid sub-select is the portable Postgres pattern for batched DELETE
            result = db.execute(
                text(
                    "DELETE FROM external_service_checks "
                    "WHERE ctid IN ("
                    "  SELECT ctid FROM external_service_checks "
                    "  WHERE checked_at < :cutoff "
                    "  ORDER BY checked_at "
                    "  LIMIT :batch"
                    ")"
                ),
                {"cutoff": cutoff, "batch": _BATCH_SIZE},
            )
            db.commit()

            deleted = result.rowcount
            if deleted == 0:
                break

            total_deleted += deleted
            logger.debug(
                "[retention] batch deleted %d rows (total so far: %d)",
                deleted, total_deleted,
            )

            # yield I/O between batches
            if deleted == _BATCH_SIZE:
                time.sleep(_BATCH_SLEEP_SECS)

        # ── Phase 3: cleanup assertion_results (same retention) ──
        ar_deleted = 0
        try:
            while True:
                ar_result = db.execute(
                    text(
                        "DELETE FROM assertion_results "
                        "WHERE ctid IN ("
                        "  SELECT ctid FROM assertion_results "
                        "  WHERE evaluated_at < :cutoff "
                        "  ORDER BY evaluated_at "
                        "  LIMIT :batch"
                        ")"
                    ),
                    {"cutoff": cutoff, "batch": _BATCH_SIZE},
                )
                db.commit()
                ar_batch = ar_result.rowcount
                if ar_batch == 0:
                    break
                ar_deleted += ar_batch
                if ar_batch == _BATCH_SIZE:
                    time.sleep(_BATCH_SLEEP_SECS)
        except Exception as ar_e:
            db.rollback()
            logger.error("[retention] assertion_results cleanup error: %s", ar_e)

    except Exception as e:
        db.rollback()
        logger.error("[retention] cleanup error: %s", e, exc_info=True)
    finally:
        db.close()

    duration = round(time.monotonic() - t0, 2)
    logger.info(
        "[cleanup] external_service_checks retention=%d days deleted=%d duration=%ss",
        retention_days, total_deleted, duration,
    )
    if ar_deleted:
        logger.info(
            "[cleanup] assertion_results retention=%d days deleted=%d",
            retention_days, ar_deleted,
        )
    return total_deleted, duration


# -- Storage Info (for /api/system/storage) --------------------------------

def get_storage_info():
    """Return row count, estimated size, and retention config."""
    retention_days = get_retention_days()
    db = SessionLocal()
    try:
        row = db.execute(text("SELECT count(*) FROM external_service_checks")).fetchone()
        row_count = row[0] if row else 0

        size_row = db.execute(
            text("SELECT pg_total_relation_size('external_service_checks')")
        ).fetchone()
        size_bytes = size_row[0] if size_row else 0

        # human readable
        if size_bytes >= 1_073_741_824:
            size_hr = "{:.2f} GB".format(size_bytes / 1_073_741_824)
        elif size_bytes >= 1_048_576:
            size_hr = "{:.1f} MB".format(size_bytes / 1_048_576)
        else:
            size_hr = "{:.0f} KB".format(size_bytes / 1024)

        oldest_row = db.execute(
            text("SELECT min(checked_at) FROM external_service_checks")
        ).fetchone()
        oldest = oldest_row[0].isoformat() if oldest_row and oldest_row[0] else None

        newest_row = db.execute(
            text("SELECT max(checked_at) FROM external_service_checks")
        ).fetchone()
        newest = newest_row[0].isoformat() if newest_row and newest_row[0] else None

        return {
            "table": "external_service_checks",
            "row_count": row_count,
            "size_bytes": size_bytes,
            "size_human": size_hr,
            "oldest_check": oldest,
            "newest_check": newest,
            "retention_days": retention_days,
            "retention_env_var": "EXTERNAL_SERVICE_CHECK_RETENTION_DAYS",
        }
    except Exception as e:
        logger.error("[retention] storage info error: %s", e)
        return {"error": str(e)}
    finally:
        db.close()
