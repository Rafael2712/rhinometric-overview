"""
Alert Noise Filter — Production-grade noise reduction for synthetic monitoring.

Reduces alert and incident volume while preserving real failure detection.

Features:
  1. Transient failure filter — minimum consecutive failures before alerting
  2. Per-service alert cooldown — prevent repeated alerts for same service
  3. Alert deduplication — skip if same fingerprint already firing
  4. Incident creation gating — require critical severity + sustained downtime
  5. Recovery buffer — require multiple failures to reopen after recovery
  6. Severity escalation — auto-escalate based on failure streak length

All thresholds configurable via environment variables.
"""

import logging
import os
import time
import threading
from datetime import datetime, timezone
from typing import Dict, Tuple

logger = logging.getLogger("rhinometric.alert_noise_filter")

# ── Configuration ───────────────────────────────────────────────
# All tunable via environment variables; defaults optimised for
# 250-300 HTTP endpoints checked every 15 seconds.
# ────────────────────────────────────────────────────────────────

# Minimum consecutive failures before allowing an alert
MIN_FAILURE_STREAK = int(os.environ.get("ALERT_MIN_FAILURE_STREAK", "3"))

# Cooldown: seconds after firing an alert before another is allowed
# for the same service
ALERT_COOLDOWN_SECONDS = int(os.environ.get("ALERT_COOLDOWN_SECONDS", "120"))

# Minimum sustained downtime (seconds) before creating an incident
INCIDENT_MIN_DOWN_SECONDS = int(os.environ.get("INCIDENT_MIN_DOWN_SECONDS", "120"))

# After recovery, require this many consecutive failures before re-opening
RECOVERY_REOPEN_STREAK = int(os.environ.get("ALERT_RECOVERY_REOPEN_STREAK", "2"))

# Severity escalation thresholds (consecutive failure counts)
SEVERITY_WARNING_STREAK = int(os.environ.get("SEVERITY_WARNING_STREAK", "3"))
SEVERITY_CRITICAL_STREAK = int(os.environ.get("SEVERITY_CRITICAL_STREAK", "6"))


# ── In-memory state ─────────────────────────────────────────────
_lock = threading.Lock()

# Epoch of last alert fired per entity_name
_last_alert_time: Dict[str, float] = {}

# Whether a service recently recovered (needs extra failures to reopen)
_recently_recovered: Dict[str, bool] = {}

# Epoch of first observed failure per entity_name (for incident timing)
_first_failure_at: Dict[str, float] = {}

# entity_name -> service_id cache (refreshed periodically)
_name_to_id: Dict[str, int] = {}
_name_cache_ts: float = 0.0
_NAME_CACHE_TTL = 300  # seconds

# Suppression counters (for monitoring / diagnostics)
_suppressed: Dict[str, int] = {}
_allowed_count: int = 0


# ── Service name -> ID mapping ─────────────────────────────────

def _refresh_name_cache() -> None:
    """Refresh the entity_name -> service_id mapping from DB."""
    global _name_cache_ts
    now = time.time()
    if now - _name_cache_ts < _NAME_CACHE_TTL:
        return
    try:
        from database import SessionLocal
        from models.external_service import ExternalService
        db = SessionLocal()
        rows = db.query(ExternalService.id, ExternalService.name).all()
        db.close()
        _name_to_id.clear()
        for r in rows:
            _name_to_id[r.name.lower()] = r.id
        _name_cache_ts = now
    except Exception as e:
        logger.debug("[NoiseFilter] Name cache refresh error: %s", e)


def _get_failure_streak(entity_name: str) -> int:
    """Read consecutive failure count from the health checker's in-memory state."""
    _refresh_name_cache()
    try:
        from services.health_checker import _consecutive_failures
        svc_id = _name_to_id.get(entity_name.lower())
        if svc_id is not None:
            return _consecutive_failures.get(svc_id, 0)
    except Exception as e:
        logger.debug("[NoiseFilter] Cannot read failure streak for %s: %s",
                     entity_name, e)
    return 0


# ── Core API ────────────────────────────────────────────────────

def should_create_alert(entity_name: str, fingerprint: str,
                        db=None) -> Tuple[bool, str]:
    """
    Decide whether an alert event should be created.

    Checks (in order):
      1. Recovery buffer — recently recovered services need extra failures
      2. Transient failure filter — minimum consecutive failures
      3. Alert cooldown — per-service time window
      4. Alert deduplication — no duplicate firing events

    Returns (should_create, reason_string).
    """
    global _allowed_count
    now_ts = time.time()

    with _lock:
        streak = _get_failure_streak(entity_name)

        # 1. Recovery buffer
        if _recently_recovered.get(entity_name, False):
            if streak < RECOVERY_REOPEN_STREAK:
                reason = (f"recovery_buffer: {streak}/{RECOVERY_REOPEN_STREAK} "
                          f"failures needed after recovery")
                _suppressed["recovery_buffer"] = _suppressed.get("recovery_buffer", 0) + 1
                return False, reason
            else:
                _recently_recovered[entity_name] = False
                logger.info("[NoiseFilter] %s: recovery buffer cleared "
                            "after %d consecutive failures", entity_name, streak)

        # 2. Transient failure filter
        if streak < MIN_FAILURE_STREAK:
            reason = f"transient_filter: streak={streak}/{MIN_FAILURE_STREAK}"
            _suppressed["transient_filter"] = _suppressed.get("transient_filter", 0) + 1
            return False, reason

        # 3. Alert cooldown
        last_alert = _last_alert_time.get(entity_name, 0)
        if (now_ts - last_alert) < ALERT_COOLDOWN_SECONDS:
            remaining = int(ALERT_COOLDOWN_SECONDS - (now_ts - last_alert))
            reason = f"cooldown: {remaining}s remaining for {entity_name}"
            _suppressed["cooldown"] = _suppressed.get("cooldown", 0) + 1
            return False, reason

        # 4. Alert deduplication
        if db and fingerprint:
            try:
                from models.alert_event import AlertEvent
                existing = db.query(AlertEvent).filter(
                    AlertEvent.fingerprint == fingerprint,
                    AlertEvent.status == "firing",
                ).first()
                if existing:
                    reason = f"dedup: firing event exists (fp={fingerprint[:8]})"
                    _suppressed["dedup"] = _suppressed.get("dedup", 0) + 1
                    return False, reason
            except Exception as e:
                logger.warning("[NoiseFilter] Dedup check failed: %s", e)

        # All checks passed — record and allow
        _last_alert_time[entity_name] = now_ts
        if entity_name not in _first_failure_at:
            _first_failure_at[entity_name] = now_ts
        _allowed_count += 1
        return True, f"allowed: streak={streak}"


def should_create_incident(entity_name: str, severity: str) -> Tuple[bool, str]:
    """
    Decide whether an incident should be created for this alert.

    Rules:
      - severity must be "critical"
      - downtime must exceed INCIDENT_MIN_DOWN_SECONDS

    Returns (should_create, reason_string).
    """
    now_ts = time.time()

    with _lock:
        first_failure = _first_failure_at.get(entity_name)
        if not first_failure:
            _first_failure_at[entity_name] = now_ts
            first_failure = now_ts

        down_duration = now_ts - first_failure

        # Only critical alerts create incidents
        if severity != "critical":
            return False, (f"incident_gate: severity={severity} (need critical), "
                           f"down {down_duration:.0f}s")

        # Critical: require sustained downtime
        if down_duration < INCIDENT_MIN_DOWN_SECONDS:
            return False, (f"incident_gate: critical but down {down_duration:.0f}s "
                           f"< {INCIDENT_MIN_DOWN_SECONDS}s threshold")

        return True, (f"incident_allowed: severity={severity}, "
                       f"down {down_duration:.0f}s >= {INCIDENT_MIN_DOWN_SECONDS}s")


def escalate_severity(entity_name: str, original_severity: str) -> str:
    """
    Auto-escalate severity based on consecutive failure streak.

      < WARNING_STREAK  : keep original
      WARNING_STREAK-   : "warning"
      >= CRITICAL_STREAK: "critical"
    """
    streak = _get_failure_streak(entity_name)
    if streak >= SEVERITY_CRITICAL_STREAK:
        if original_severity != "critical":
            logger.info("[NoiseFilter] %s: severity escalated %s -> critical "
                        "(streak=%d)", entity_name, original_severity, streak)
        return "critical"
    elif streak >= SEVERITY_WARNING_STREAK:
        return "warning"
    return original_severity


def on_recovery(entity_name: str) -> None:
    """
    Called when a service recovers (resolved alert received).
    Sets the recovery buffer so the service needs RECOVERY_REOPEN_STREAK
    consecutive failures before alerts reopen.
    """
    with _lock:
        _recently_recovered[entity_name] = True
        _first_failure_at.pop(entity_name, None)
    logger.info("[NoiseFilter] %s recovered — buffer active "
                "(need %d failures to reopen)", entity_name, RECOVERY_REOPEN_STREAK)


def get_filter_stats() -> dict:
    """Return current filter state for the diagnostics endpoint."""
    now = time.time()
    with _lock:
        cooldown_active = {
            k: int(ALERT_COOLDOWN_SECONDS - (now - v))
            for k, v in _last_alert_time.items()
            if now - v < ALERT_COOLDOWN_SECONDS
        }
        return {
            "config": {
                "min_failure_streak": MIN_FAILURE_STREAK,
                "alert_cooldown_seconds": ALERT_COOLDOWN_SECONDS,
                "incident_min_down_seconds": INCIDENT_MIN_DOWN_SECONDS,
                "recovery_reopen_streak": RECOVERY_REOPEN_STREAK,
                "severity_warning_streak": SEVERITY_WARNING_STREAK,
                "severity_critical_streak": SEVERITY_CRITICAL_STREAK,
            },
            "counters": {
                "alerts_allowed": _allowed_count,
                "alerts_suppressed": dict(_suppressed),
                "total_suppressed": sum(_suppressed.values()),
            },
            "state": {
                "cooldown_active": cooldown_active,
                "services_in_recovery_buffer": [
                    k for k, v in _recently_recovered.items() if v
                ],
                "services_with_active_failures": list(_first_failure_at.keys()),
            },
        }
