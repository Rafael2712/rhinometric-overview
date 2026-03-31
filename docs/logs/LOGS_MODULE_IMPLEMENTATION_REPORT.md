# Logs Module — Implementation Report

> **Version:** v2.7.0-logs  
> **Date:** 2025-07-14  
> **Scope:** Backend rewrite + Frontend UX restructure  
> **Branch:** `feature/use-direct-grafana-links`

---

## 1. Context and Objective

The Logs module in the Rhinometric Console allows operators and administrators to explore log streams
ingested from customer services via the OpenTelemetry Collector. Logs are stored in **Loki** and
served through a FastAPI backend that proxies and enriches Loki queries.

Prior to this work, the module had the following limitations:

- **Customer service logs were hidden** — an overly broad regex filter excluded any service matching
  `rhinometric-*`, which inadvertently blocked legitimate customer services whose names contained
  the prefix (e.g., `rhinometric-web-produccion`).
- **No structured parsing** — log entries were displayed as raw text with no field extraction.
- **No server-side filtering** — all filtering was either absent or delegated entirely to Loki's
  LogQL, with no post-enrichment filtering capability.
- **Minimal frontend UX** — the previous UI was a basic list without level indicators, detail
  panels, keyboard navigation, or export functionality.

The objective was to transform the Logs module into a **production-ready, commercially demonstrable**
log explorer with structured parsing, multi-dimensional filtering, and professional UX.

---

## 2. Diagnosis

### 2.1 Root Cause: Missing Customer Logs

The original `INTERNAL_PATTERN` regex in `logs.py` was:

```python
INTERNAL_PATTERN = re.compile(r"^rhinometric[-_]", re.IGNORECASE)
```

This matched **any** service starting with `rhinometric-`, including legitimate customer services
such as `rhinometric-web-produccion`. The fix was to narrow the regex to an explicit list of
known infrastructure components.

### 2.2 Loki Empty Query Timeout

When the frontend sent `{} | ...` (empty selector), Loki attempted a full scan and timed out.
The fix was to inject `job=~".+"` as a positive matcher when the selector body is empty, ensuring
Loki always has a bounded query scope.

### 2.3 Frontend Architecture

The previous frontend used `@heroicons/react` (not installed in the project), had inconsistent
auth patterns, and lacked structured data display. It needed a full rewrite to be consistent
with other pages (Traces, Anomalies) that use `lucide-react`, `useAuthStore`, and direct `fetch`.

---

## 3. Backend Changes

**File:** `rhinometric-console/backend/routers/logs.py`  
**Lines:** 134 → 419 (complete rewrite)

### 3.1 Internal Exclusion — Blocklist Approach

Replaced the single broad regex with a two-tier exclusion system:

| Component | Purpose |
|-----------|---------|
| `INTERNAL_JOBS` | Set of exact job names to exclude (e.g., `console-backend`, `grafana`, `loki`) |
| `INTERNAL_PATTERN` | Compiled regex for compound names (e.g., `rhinometric-console-*`, `rhinometric-nginx-*`) |
| `_LOKI_INTERNAL_RE` | LogQL-compatible regex string injected into Loki queries |
| `_LOKI_SHORT_EXCLUSION` | Compact exclusion for enriched endpoint (Python handles the rest) |

The function `_is_internal_stream()` checks `job`, `service_name`, `service`, and `container`
labels against both the set and the regex.

### 3.2 Log Parsing Engine

Five regex patterns extract structured fields from raw log text:

| Regex | Source Type | Fields Extracted |
|-------|-------------|-----------------|
| `_LEVEL_PREFIX_RE` | all | `level` |
| `_ACCESS_LOG_RE` | `access_log` | `client_ip`, `method`, `path`, `full_path`, `status_code`, `response_bytes`, `access_time` |
| `_APACHE_ERROR_RE` | `error_log` | `module`, `error_message`, `client_ip` |
| `_CYCLE_RE` | `collector_cycle` | `cycle_num`, `duration_ms`, `ok_count`, `total_signals` |
| `_SIGNAL_RE` | `collector_signal` | `signal`, `status_code`, `duration_ms` |

Level normalization maps vendor-specific severity strings (e.g., `WARNING`, `crit`, `emerg`)
to a canonical set: `debug | info | warn | error | fatal`.

### 3.3 API Endpoints

#### `GET /api/logs` — Raw Loki Proxy
- Injects full internal exclusion into LogQL query
- Python-side double-filter via `_is_internal_stream()`
- Returns original Loki JSON payload structure
- Timeout: 30s with proper 503/504 error mapping

#### `GET /api/logs/enriched` — Parsed + Filtered
- Accepts server-side filters: `level`, `source_type`, `service`, `method`, `status_code`, `path_contains`, `search`
- `search` is pushed into LogQL as `|~ "(?i)..."` for pre-filtering at Loki level
- `service` rewrites the selector to `{job="<service>"}`
- `status_code` supports exact match (`404`) and range match (`4xx`, `5xx`)
- Over-fetches by 4x when filters active, then trims to `limit`
- Returns enriched entries + available filter options (levels, source_types, services, methods, status_codes)

#### `GET /api/logs/fields` — Schema Documentation
- Static endpoint returning all stream labels and parsed fields with descriptions
- Documents when each field is present (e.g., `"when": "source_type=access_log"`)

### 3.4 Loki Query Safety

The `_inject_internal_exclusion()` function:
- Detects empty selectors (`{}`) and inserts `job=~".+"` as a positive matcher
- Appends `job!~"<exclusion_regex>"` to filter out internal streams at the Loki level
- Uses `short=True` mode for enriched endpoint (shorter regex, Python does the rest)

---

## 4. Frontend Changes

**File:** `rhinometric-console/frontend/src/pages/Logs.tsx`  
**Lines:** 592 → 846 (complete rewrite)

### 4.1 Architecture

| Component | Responsibility |
|-----------|---------------|
| `FilterBar` | Search input, time range, limit selector, 6 advanced filters (service, level, source_type, method, status_code, path), refresh, clear |
| `LogRow` | Single log entry rendering with level badge, timestamp, source type tag, HTTP inline info (method + status + path), message excerpt |
| `DetailPanel` | Three-tab detail view: Parsed Fields, Raw Message (with copy), Stream Labels |
| `StatsBar` | Live statistics: total entries, before/after filter count, active filter badges |
| `EmptyState` | Three states: no-data, filtered-empty (with clear button), error |
| `LogsPage` | Main page component with state management, data fetching, keyboard navigation, CSV/JSON export |

### 4.2 Features

- **7 filter dimensions** — search, service, level, source_type, method, status_code, path
- **9 time range options** — 15min to 7 days
- **5 limit options** — 100, 200, 500, 1000, 2000
- **Keyboard navigation** — Arrow keys to navigate rows, Enter to toggle detail panel, Escape to close
- **Data export** — CSV and JSON download with timestamped filenames
- **Auto-refresh** — via React Query with configurable stale time
- **Level badges** — Color-coded with icons (Bug, Info, AlertTriangle, XCircle, Flame)
- **HTTP inline display** — Method badge + status code (color-coded) + path shown directly in log row
- **Active filter counter** — Badge on filter toggle button showing count of active filters
- **Responsive grid** — 2/3/6 column filter layout adapting to screen size

### 4.3 Consistency with Platform

- Uses `lucide-react` icons (same as Traces, Anomalies, Dashboard pages)
- Uses `useAuthStore` from `../lib/auth/store` (same auth pattern as all pages)
- Uses direct `fetch` with Bearer token (not Axios — consistent with Traces.tsx)
- Named export `LogsPage` matching `App.tsx` import pattern
- Tailwind CSS with platform design tokens (`bg-surface-light`, `btn-primary`, etc.)

---

## 5. Supported Fields (Enriched Endpoint)

### Stream Labels (from Loki)

| Field | Description | Always Present |
|-------|-------------|---------------|
| `job` | Service key identifier | Yes |
| `service` | Service name | Yes |
| `service_key` | Unique service+environment key | Yes |
| `service_name` | Human-readable service name | Yes |
| `environment` | Deployment environment | Yes |
| `source` | Ingestion source | Yes |

### Parsed Fields (extracted by backend)

| Field | Description | When Present |
|-------|-------------|-------------|
| `level` | Normalized severity: debug\|info\|warn\|error\|fatal | Always |
| `source_type` | Log classification | Always |
| `method` | HTTP method (GET, POST, etc.) | access_log |
| `path` | Request path without query string | access_log |
| `full_path` | Full request path with query | access_log |
| `status_code` | HTTP status code | access_log, collector_signal |
| `client_ip` | Client IP address | access_log, error_log |
| `response_bytes` | Response size | access_log |
| `module` | Apache module name | error_log |
| `error_message` | Error detail text | error_log |
| `signal` | Telemetry signal type (metrics/logs/traces) | collector_signal |
| `duration_ms` | Duration in milliseconds | collector_cycle, collector_signal |
| `cycle_num` | Collector cycle number | collector_cycle |

---

## 6. Validation

All endpoints were validated against live data from customer services:

| Test | Endpoint | Result |
|------|----------|--------|
| Enriched logs (default) | `GET /api/logs/enriched?query={}&limit=50&start=...&end=...` | ✅ Returns parsed entries with fields |
| Service filter | `GET /api/logs/enriched?...&service=rhinometric-web-produccion` | ✅ Only entries from that service |
| Level filter | `GET /api/logs/enriched?...&level=error` | ✅ Only error-level entries |
| Status code range | `GET /api/logs/enriched?...&status_code=4xx` | ✅ Only 4xx status codes |
| Free text search | `GET /api/logs/enriched?...&search=favicon` | ✅ Message body filtered |
| Fields schema | `GET /api/logs/fields` | ✅ Complete schema returned |
| Raw proxy | `GET /api/logs?query={}&limit=20&start=...&end=...` | ✅ Loki payload with internal streams excluded |
| Frontend build | `npm run build` | ✅ Built successfully, deployed as index-CFhg_YA7.js |
| Frontend render | Browser test | ✅ FilterBar, LogRow, DetailPanel, StatsBar all render |

---

## 7. Known Risks and Technical Debt

| Item | Severity | Description |
|------|----------|-------------|
| Over-fetch multiplier | Low | Enriched endpoint fetches 4x limit when filters active. Could be optimized with LogQL push-down for level/method. |
| No pagination | Medium | Current implementation loads all results in one request. For very high volumes, cursor-based pagination should be added. |
| Regex maintenance | Low | Adding new infrastructure services requires updating `INTERNAL_JOBS`, `INTERNAL_PATTERN`, and `_LOKI_INTERNAL_RE` in three places. Could be unified. |
| No WebSocket streaming | Low | Real-time tail mode not implemented. Would need Loki's tail endpoint + WebSocket bridge. |
| Filter options from limited data | Low | Available filter options (levels, services, etc.) are derived from the current result set, not from a global label scan. |

---

## 8. Modified Files

| File | Change Type | Lines |
|------|------------|-------|
| `rhinometric-console/backend/routers/logs.py` | Complete rewrite | 419 |
| `rhinometric-console/frontend/src/pages/Logs.tsx` | Complete rewrite | 846 |

**Not modified in this scope** (other changes exist in the working tree but belong to separate work items):
- `alertmanager/alertmanager.yml`
- `rhinometric-console/backend/routers/telemetry_ingest.py`
- `rhinometric-console/collector/*`

---

## 9. Executive Summary

The Logs module was transformed from a basic Loki proxy with visibility bugs into a
**production-grade log explorer** suitable for commercial demonstrations. The backend now
parses 5 log formats, applies server-side filtering across 7 dimensions, and correctly
isolates customer service logs from internal platform noise. The frontend provides a
professional, keyboard-navigable interface with structured log display, multi-tab detail
panels, and data export capabilities. All changes are validated against live customer data
and the module is ready for the next phase of development (pagination, real-time tail, saved queries).
