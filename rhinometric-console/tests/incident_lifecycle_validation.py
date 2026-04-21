"""
INCIDENT VALIDATION — SERVICE_DOWN >120s
Verifies: incident created after 120s sustained downtime, auto-resolved on recovery.

Strategy: seed the noise-filter's in-memory _first_failure_at dict
with (now - 130s) to simulate 130s of sustained downtime BEFORE
firing the evaluation, eliminating the need to actually wait 2 minutes.
"""
import sys, uuid, hashlib, time
sys.path.insert(0, '/app')

import psycopg2
from datetime import datetime, timezone, timedelta

DB_RAW = "postgresql://rhinometric:0gm1S4NgXiuOojRDbKjgX31C@postgres:5432/rhinometric"
TS     = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
SVC_NAME = f"INC_TEST_{TS}"

def rconn():
    return psycopg2.connect(DB_RAW)

def qone(sql, params=()):
    c = rconn(); cur = c.cursor()
    cur.execute(sql, params); r = cur.fetchone(); c.close(); return r

def qall(sql, params=()):
    c = rconn(); cur = c.cursor()
    cur.execute(sql, params); r = cur.fetchall(); c.close(); return r

def execute(sql, params=()):
    c = rconn(); cur = c.cursor()
    cur.execute(sql, params); c.commit(); c.close()

def sep(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")

# ─── ORM Session ────────────────────────────────────────────────
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine("postgresql+psycopg2://rhinometric:0gm1S4NgXiuOojRDbKjgX31C@postgres:5432/rhinometric")
Session = sessionmaker(bind=engine)
db = Session()

now = datetime.now(timezone.utc)

# ─── SETUP ───────────────────────────────────────────────────────
sep("SETUP — Create INC_TEST service")

execute("""
    INSERT INTO external_services
        (name, service_type, environment, enabled, status, config, created_at, updated_at, group_name,
         monitoring_mode, timeout_seconds, check_interval_seconds,
         synthetic_enabled, metrics_enabled, logs_enabled, traces_enabled, telemetry_attached,
         telemetry_status)
    VALUES (%s, 'HTTP', 'staging', true, 'DOWN', '{}', %s, %s, 'E2E',
            'SYNTHETIC_ONLY', 10, 15, true, false, false, false, false, 'NOT_CONFIGURED')
""", (SVC_NAME, now, now))

svc_row = qone("SELECT id, name, status FROM external_services WHERE name=%s", (SVC_NAME,))
SVC_ID = svc_row[0]
print(f"[SETUP] service id={SVC_ID} name={svc_row[1]} status={svc_row[2]}")

# Insert 3 consecutive down checks
for i in range(3):
    checked = now - timedelta(seconds=30*(3-i))
    execute("""
        INSERT INTO external_service_checks
            (service_id, status, checked_at, response_time_ms, status_code,
             assertions_total, assertions_passed, assertions_failed)
        VALUES (%s, 'down', %s, NULL, NULL, 0, 0, 0)
    """, (SVC_ID, checked))
print(f"[SETUP] 3 consecutive down checks inserted")

RULE_UUID = str(uuid.uuid4())
execute("""
    INSERT INTO alert_rules (id, name, service_id, rule_type, severity, threshold,
                             consecutive_failures, enabled, created_at, updated_at, sustained_checks)
    VALUES (%s, %s, %s, 'SERVICE_DOWN', 'critical', 1, 3, true, %s, %s, 3)
""", (RULE_UUID, f"INC_RULE_{TS}", SVC_ID, now, now))
print(f"[SETUP] rule id={RULE_UUID}")

# ─── SEED NOISE FILTER: simulate 130s of downtime ────────────────
sep("SEED NOISE FILTER — simulate 130s sustained downtime")

from services.alert_noise_filter import _first_failure_at, _lock, INCIDENT_MIN_DOWN_SECONDS
simulated_first_failure = time.time() - 130  # 130s ago
with _lock:
    _first_failure_at[SVC_NAME] = simulated_first_failure

down_duration = time.time() - _first_failure_at[SVC_NAME]
print(f"[SEED] INCIDENT_MIN_DOWN_SECONDS={INCIDENT_MIN_DOWN_SECONDS}")
print(f"[SEED] Simulated first_failure_at = now - 130s")
print(f"[SEED] Effective down_duration = {down_duration:.1f}s (must be > {INCIDENT_MIN_DOWN_SECONDS}s)")
print(f"[SEED] Noise filter threshold MET: {down_duration >= INCIDENT_MIN_DOWN_SECONDS}")

# ─── FIRE EVALUATION ─────────────────────────────────────────────
sep("STEP 1 — Fire _evaluate_service_down")

from models.alert_rule import AlertRule
from routers.alert_rules import _evaluate_service_down

rule_obj = db.query(AlertRule).filter(AlertRule.id == RULE_UUID).first()
try:
    fired = _evaluate_service_down(db, rule_obj)
    db.commit()
    print(f"[FIRE] _evaluate_service_down fired={fired}")
except Exception as e:
    db.rollback()
    print(f"[FIRE] ERROR: {e}")
    import traceback; traceback.print_exc()
    fired = 0

# ─── VERIFY ALERT_EVENT ──────────────────────────────────────────
sep("STEP 2 — Verify AlertEvent (firing, critical)")

alert_name_str = f"policy:SERVICE_DOWN:{SVC_NAME}"
fp_seed = f"{alert_name_str}|{SVC_NAME}|SERVICE_DOWN"
fingerprint = hashlib.sha256(fp_seed.encode()).hexdigest()[:16]
print(f"[VERIFY] fingerprint={fingerprint}")

ev = qone("""
    SELECT id, alert_name, status, severity, started_at, ended_at, resolved_at,
           incident_id, escalation_count, entity_name, source
    FROM alert_events WHERE fingerprint=%s AND status='firing'
    ORDER BY started_at DESC LIMIT 1
""", (fingerprint,))

if ev:
    EVENT_ID   = ev[0]
    INCIDENT_ID = ev[7]
    print(f"[VERIFY] AlertEvent:")
    print(f"  id            = {ev[0]}")
    print(f"  alert_name    = {ev[1]}")
    print(f"  status        = {ev[2]}")
    print(f"  severity      = {ev[3]}")
    print(f"  started_at    = {ev[4]}")
    print(f"  ended_at      = {ev[5]}")
    print(f"  resolved_at   = {ev[6]}")
    print(f"  incident_id   = {ev[7]}")
    print(f"  escalation    = {ev[8]}")
    print(f"  entity_name   = {ev[9]}")
    ALERT_STATUS_OK   = ev[2] == 'firing'
    SEVERITY_OK       = ev[3] == 'critical'
    INCIDENT_ID_OK    = ev[7] is not None
else:
    EVENT_ID = INCIDENT_ID = None
    ALERT_STATUS_OK = SEVERITY_OK = INCIDENT_ID_OK = False
    print(f"[VERIFY] FAIL — no firing event for fingerprint {fingerprint}")

print(f"\n  AlertEvent status=firing  : {'YES' if ALERT_STATUS_OK else 'NO'}")
print(f"  AlertEvent severity=crit  : {'YES' if SEVERITY_OK else 'NO'}")
print(f"  incident_id NOT NULL      : {'YES' if INCIDENT_ID_OK else 'NO'}")

# ─── VERIFY INCIDENT ─────────────────────────────────────────────
sep("STEP 3 — Verify Incident created")

if INCIDENT_ID:
    inc = qone("""
        SELECT id, title, status, severity, created_at, resolved_at, entity_name
        FROM incidents WHERE id=%s
    """, (INCIDENT_ID,))
    if inc:
        print(f"[INCIDENT] Incident found:")
        print(f"  id           = {inc[0]}")
        print(f"  title        = {inc[1]}")
        print(f"  status       = {inc[2]}")
        print(f"  severity     = {inc[3]}")
        print(f"  created_at   = {inc[4]}")
        print(f"  resolved_at  = {inc[5]}")
        print(f"  entity_name  = {inc[6]}")
        INCIDENT_CREATED = inc[2] in ('open', 'investigating', 'resolved')
    else:
        print(f"[INCIDENT] FAIL — incident id={INCIDENT_ID} not found in incidents table")
        INCIDENT_CREATED = False
else:
    print(f"[INCIDENT] FAIL — no incident_id on alert event")
    INCIDENT_CREATED = False

print(f"\n  Incident CREATED          : {'YES' if INCIDENT_CREATED else 'NO'}")

# ─── RESOLVE SERVICE ─────────────────────────────────────────────
sep("STEP 4 — Restore service to UP, run resolution")

execute("UPDATE external_services SET status='UP' WHERE name=%s", (SVC_NAME,))
print(f"[RESOLVE] service status → UP")

# Also clear the noise filter recovery buffer so resolution proceeds
try:
    from services.alert_noise_filter import on_recovery
    on_recovery(SVC_NAME)
    print(f"[RESOLVE] noise filter recovery buffer cleared for {SVC_NAME}")
except Exception as e:
    print(f"[RESOLVE] on_recovery warning: {e}")

from routers.alert_rules import _resolve_recovered_services
try:
    db.expire_all()
    _resolve_recovered_services(db)
    db.commit()
    print(f"[RESOLVE] _resolve_recovered_services completed")
except Exception as e:
    db.rollback()
    print(f"[RESOLVE] ERROR: {e}")
    import traceback; traceback.print_exc()

# ─── VERIFY RESOLUTION ───────────────────────────────────────────
sep("STEP 5 — Verify resolution")

ev_r = qone("""
    SELECT id, status, ended_at, resolved_at, incident_id
    FROM alert_events WHERE fingerprint=%s ORDER BY started_at DESC LIMIT 1
""", (fingerprint,))

print(f"[VERIFY] AlertEvent after resolve:")
print(f"  id          = {ev_r[0] if ev_r else 'N/A'}")
print(f"  status      = {ev_r[1] if ev_r else 'N/A'}")
print(f"  ended_at    = {ev_r[2] if ev_r else 'N/A'}")
print(f"  resolved_at = {ev_r[3] if ev_r else 'N/A'}")

ALERT_RESOLVED    = ev_r and ev_r[1] == 'resolved'
ENDED_AT_SET      = ev_r and ev_r[2] is not None

if INCIDENT_ID:
    inc_r = qone("SELECT id, status, resolved_at FROM incidents WHERE id=%s", (INCIDENT_ID,))
    print(f"\n[VERIFY] Incident after resolve:")
    print(f"  status      = {inc_r[1] if inc_r else 'N/A'}")
    print(f"  resolved_at = {inc_r[2] if inc_r else 'N/A'}")
    INCIDENT_RESOLVED  = inc_r and inc_r[1] == 'resolved'
    INC_RESOLVED_AT    = inc_r and inc_r[2] is not None
else:
    INCIDENT_RESOLVED = INC_RESOLVED_AT = False

# ─── CROSS-CHECK: HISTORY ────────────────────────────────────────
sep("STEP 6 — Cross-check: Alert History and DB consistency")

cutoff = now - timedelta(hours=24)
hist = qone("""
    SELECT id, status, started_at, ended_at FROM alert_events
    WHERE fingerprint=%s AND status='resolved'
    AND COALESCE(ended_at, resolved_at, started_at) >= %s
""", (fingerprint, cutoff))
IN_HISTORY = hist is not None

no_active = qone("SELECT id FROM alert_events WHERE fingerprint=%s AND status='firing'", (fingerprint,))
NO_ACTIVE  = no_active is None

print(f"[CROSS-CHECK] No active firing alert: {'YES' if NO_ACTIVE else 'NO  <-- FAIL'}")
print(f"[CROSS-CHECK] Appears in Alert History: {'YES' if IN_HISTORY else 'NO  <-- FAIL'}")

if INCIDENT_ID:
    inc_done = qone("SELECT status FROM incidents WHERE id=%s", (INCIDENT_ID,))
    print(f"[CROSS-CHECK] Incident status in DB: {inc_done[0] if inc_done else 'N/A'}")

# ─── CLEANUP ─────────────────────────────────────────────────────
sep("CLEANUP")
execute("DELETE FROM alert_events WHERE fingerprint=%s", (fingerprint,))
execute("DELETE FROM external_service_checks WHERE service_id=%s", (SVC_ID,))
execute("DELETE FROM alert_rules WHERE id=%s", (RULE_UUID,))
execute("DELETE FROM external_services WHERE name=%s", (SVC_NAME,))
print("[CLEANUP] done")
db.close()

# ─── FINAL REPORT ────────────────────────────────────────────────
sep("INCIDENT VALIDATION — FINAL REPORT")

rows = [
    ("Incident CREATED after >120s downtime",   INCIDENT_CREATED),
    ("AlertEvent status=firing",                 ALERT_STATUS_OK),
    ("AlertEvent severity=critical",             SEVERITY_OK),
    ("incident_id NOT NULL on AlertEvent",       INCIDENT_ID_OK),
    ("AlertEvent resolved after recovery",       ALERT_RESOLVED),
    ("ended_at populated",                       ENDED_AT_SET),
    ("Incident auto-resolved",                   INCIDENT_RESOLVED),
    ("Alert History contains event",             IN_HISTORY),
    ("No active alert after recovery",           NO_ACTIVE),
]

all_pass = True
for desc, val in rows:
    icon = "YES" if val else "NO "
    print(f"  [{icon}] {desc}")
    if not val:
        all_pass = False

print()
verdict = "PASS — Incident lifecycle fully validated" if all_pass else "FAIL — see items above"
print(f"  VERDICT: {verdict}")
