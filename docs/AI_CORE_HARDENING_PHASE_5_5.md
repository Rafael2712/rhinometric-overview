# AI Core Hardening Phase 5.5

## Scope

Surgical hardening for:
- AI lifecycle isolation
- incident auto-resolution safety
- AI endpoint contract validation for frontend routes

No feature redesign, no lifecycle redesign, no notification policy changes.

## Fixes Applied

### 1) AI advisory-only enforcement

- Disabled `POST /api/alerts/internal/ai-resolve` state mutation path.
- Route now requires admin role and returns `410 Gone`.
- Removed all lifecycle mutation behavior from this endpoint.

Files:
- `backend/routers/alerts.py`

### 2) Incident active-status safety

- Introduced `ACTIVE_ALERT_STATUSES` and used it in incident resolution checks.
- Active statuses now include: `firing`, `acknowledged`, `silenced`, `escalated`, `active`.
- Incident auto-resolution no longer closes when linked alerts are still operationally active.

Files:
- `backend/routers/incidents.py`

### 3) AI decision endpoint contract completion

- Added alert AI decision routes:
  - `GET /api/alerts/{alert_id}/ai-decision`
  - `POST /api/alerts/{alert_id}/ai-decision`
- Added incident AI decision routes:
  - `GET /api/incidents/{incident_id}/ai-decision`
  - `POST /api/incidents/{incident_id}/ai-decision`
- Added anomaly AI decision routes:
  - `GET /api/anomalies/db/{anomaly_id}/ai-decision`
  - `POST /api/anomalies/db/{anomaly_id}/ai-decision`
- Mounted anomalies router in backend app to guarantee `/api/anomalies/...` availability.

Files:
- `backend/routers/alerts.py`
- `backend/routers/incidents.py`
- `backend/routers/anomalies.py`
- `backend/main.py`

## Storage Changes

- Added `ai_decision` storage fields:
  - `alert_events.ai_decision` (JSONB via startup ALTER)
  - `incidents.ai_decision` (JSONB model + startup ALTER)

Files:
- `backend/models/alert_event.py`
- `backend/models/incident.py`
- `backend/main.py`

## Validation Evidence

- Syntax/import validation passed:
  - `python3 -m py_compile main.py routers/alerts.py routers/incidents.py routers/anomalies.py models/alert_event.py models/incident.py`
- Endpoint contract presence and auth dependencies verified in code:
  - routes present in `alerts.py`, `incidents.py`, `anomalies.py`
  - mounted routers confirmed in `main.py`
- Active status logic verified in code:
  - `check_incident_resolution()` now uses `ACTIVE_ALERT_STATUSES`

## Safety Statements

- AI is advisory-only for lifecycle control path previously exposed by `internal/ai-resolve`.
- Core lifecycle protection improved for incident auto-resolution edge cases.

## Repo / Branch

- Work performed in `rhinometric-console` repository.
- Final consolidation target: `main`.
- Commit hash: `24434e7`
