# Logs Module & Auth Stability — Technical Notes

**Last updated:** 2026-04-01
**Scope:** Internal reference for development team

---

## 1. Auth Hydration Fix (401 bug)

### Problem
After ~70 minutes of inactivity, returning to the app triggered bursts of HTTP 401 errors on all protected endpoints. The session was still valid (JWT has 24h TTL), but the app behaved as if the user was logged out. After manual re-login, everything worked again.

### Root Cause
**Zustand v5 `persist` middleware** rehydrates state from localStorage **asynchronously**. On page load (or return from inactive tab), the React component tree rendered before the auth store finished restoring `token` and `isAuthenticated` from localStorage.

This caused:
1. `ProtectedRoute` read `isAuthenticated === false` → redirect to `/login`
2. Page components' `useQuery` hooks fired with `token === null` → HTTP 401
3. React Query default retry (×3) amplified the 401 burst
4. User experienced "redirect dance" between `/login` and protected routes

### Fix (3 files, ~30 lines added)

| File | Change |
|------|--------|
| `frontend/src/lib/auth/store.ts` | Added `useHasHydrated()` hook using `persist.onFinishHydration()` |
| `frontend/src/App.tsx` | Added hydration gate — blocks all route rendering until store is hydrated |
| `frontend/src/main.tsx` | React Query retry filter: skip retry on HTTP 401/403 |

### How it works
- `useHasHydrated()` returns `false` until Zustand's persist middleware calls `onFinishHydration`
- `App()` renders a minimal loading state ("Cargando sesión…") while `hasHydrated === false`
- No routes mount → no `ProtectedRoute` check → no fetch calls with null token
- Once hydrated, full app renders with correct auth state from localStorage

### Limitations
- If the JWT is genuinely expired (>24h), the user still needs to re-login. This is expected behavior.
- There is no automatic token refresh mechanism. This could be a future improvement.
- The fix does NOT add a global 401 → logout handler. This would be a separate enhancement.

---

## 2. Logs Module UX Improvements

### Changes (frontend only — `Logs.tsx`)

| Area | Before | After |
|------|--------|-------|
| Time ranges | 9 options (5min–30d) | 5 options (15min, 1h, 6h, 24h, 7d) |
| Limit options | [100, 200, 500, 1000, 2000] | [50, 100, 250] |
| Default time | 3 hours | 1 hour |
| Default limit | 500 | 100 |
| Filter layout | Flat 7-column grid | Quick (3-col) + Advanced (4-col) tiers |
| Severity dropdown | Dynamic only (shows what's in data) | Canonical 6 levels always shown |
| Unknown severity | Not handled | Added with gray styling |

### Filter Tiers

**Quick filters** (always visible, `bg-surface-light/30`):
- Tipo servicio (service_type)
- Servicio (service name)
- Severidad (log level)

**Advanced filters** (`bg-surface-light/20`):
- Tipo evento (source_type)
- HTTP Status
- Método HTTP
- Path

### Backend
No backend changes were needed. All filter parameters were already supported by `GET /api/logs/enriched`.

---

## 3. Collector v1.1.0

### Scope
Production-ready repackaging of the telemetry collector for customer delivery.

### Key Features
- Fail-fast on missing required ENV vars with clear error box
- Startup banner with version, masked token, hostname, interval
- Preflight API connectivity check
- Per-cycle signal-level results (metrics/logs/traces counts + OK/FAIL + duration)
- Docker image with HEALTHCHECK, labels, non-root user
- Complete `.env.example` and `README.md`

### Files Modified
- `collector/main.py` — Startup logic, cycle reporting
- `collector/config.py` — ENV override system, validation
- `collector/sender.py` — HTTP client with retry
- `collector/metrics.py`, `logs.py`, `traces.py` — Signal collectors
- `collector/utils.py` — Utilities
- `collector/Dockerfile` — Multi-stage build
- `collector/.env.example` — All variables documented
- `collector/README.md` — Full documentation

---

## 4. Future Considerations

| Area | Status | Priority |
|------|--------|----------|
| Automatic token refresh | Not implemented | Medium |
| Global 401 → logout handler | Not implemented | Low |
| Logs backend performance (large time ranges) | Working but could be optimized | Low |
| Severity filter backend-side validation | Not needed currently | Low |
| Collector v1.2.0 (graceful shutdown, retry backoff) | Not started | Medium |

---

*This document is for internal use only. Do not include in public documentation.*
