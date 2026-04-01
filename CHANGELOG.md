# Changelog - Rhinometric Platform

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---



## [v2.7.2] Platform Stability & Collector Packaging — 2026-04-01

### Fixed — Auth Hydration (`store.ts`, `App.tsx`, `main.tsx`)
- **Zustand v5 persist hydration race** — After inactivity, returning to the app caused spurious 401 bursts on all protected endpoints. Root cause: Zustand v5 `persist` middleware rehydrates asynchronously; `ProtectedRoute` read `isAuthenticated=false` before localStorage was restored, triggering redirect to `/login` and fetch calls with `null` token.
- **Hydration gate** — Added `useHasHydrated()` hook using `persist.onFinishHydration()`. `App()` now blocks all route rendering until auth store is fully hydrated.
- **React Query retry filter** — `QueryClient` now skips retry on HTTP 401/403 errors, preventing error multiplication during auth failures.

### Changed — Logs UX (`Logs.tsx`)
- **Filter layout** — Reorganized from flat 7-column grid into two tiers: Quick filters (service type, service, severity) and Advanced filters (event type, HTTP status, HTTP method, path).
- **Severity dropdown** — Now uses canonical `SEVERITY_OPTIONS` constant (fatal, error, warn, info, debug, unknown) instead of only showing levels present in current data.
- **`LEVEL_CONFIG`** — Added `unknown` entry with gray styling for unrecognized severity levels.
- **Time ranges** — Reduced from 9 to 5 options (15min, 1h, 6h, 24h, 7d). Default changed from 3h to 1h.
- **Limit options** — Reduced from `[100, 200, 500, 1000, 2000]` to `[50, 100, 250]`. Default changed from 500 to 100.

### Changed — Collector v1.1.0 (`collector/`)
- **Production packaging** — Complete rewrite of collector for customer delivery with fail-fast config validation, startup banner with masked tokens, preflight connectivity check, per-cycle signal-level results, and Docker image metadata (labels + healthcheck).
- **Config system** — ENV override precedence, `.env.example` with all variables documented, `config.yaml.example` for file-based config.
- **Signal control** — `ENABLE_METRICS`, `ENABLE_LOGS`, `ENABLE_TRACES` flags with per-signal reporting in cycle output.
- **Dockerfile** — Multi-stage build with healthcheck, proper labels, non-root user.
- **README** — Complete documentation with Quick Start, Troubleshooting, Architecture, docker-compose examples.

### Risk
- Auth fix: minimal — 3 files, additive only, no hook reordering
- Logs UX: frontend-only constants/layout, no backend changes
- Collector: self-contained package, no platform code affected

---

## [v2.7.1-logs] Logs Module — service_type Classification - 2026-03-31

### Added — Backend (`logs.py`, 540 lines)
- **`service_type` classification** — Each log entry now includes a `service_type` field derived from DB lookup (cached 5 min TTL) + heuristic regex fallback.
- **Taxonomy**: `http_api`, `web_app`, `database_postgres`, `collector`, `unknown`.
- **DB cache**: Reads `external_services.catalog_type` and `service_type` columns; maps WEB_APP→web_app, REST_API→http_api, POSTGRESQL→database_postgres.
- **Heuristic fallback**: Compiled regex patterns on `job`/`service_name` labels when DB has no match.
- **`/api/logs/enriched`** filters now include `service_types` array.
- **`/api/logs/fields`** returns `enriched_fields.service_type` schema documentation.

### Added — Frontend (`Logs.tsx`, 872 lines)
- **service_type badge** in LogRow — color-coded pill (cyan=HTTP API, green=Web App, purple=PostgreSQL, orange=Collector).
- **"Tipo Servicio" FieldCard** in detail panel parsed tab.
- Constants: `SERVICE_TYPE_LABELS`, `SERVICE_TYPE_COLORS` for consistent UI rendering.

### Risk
- Zero breaking changes. Read-only DB access. Logs module only. No other modules touched.
## [v2.7.0-logs] Logs Module — Diagnosis, Parsing, Filters and UX Restructure - 2025-07-14

### Fixed
- **Customer service logs invisible** — Overly broad `INTERNAL_PATTERN` regex (`^rhinometric[-_]`) was excluding legitimate customer services (e.g., `rhinometric-web-produccion`). Narrowed to explicit infrastructure component list.
- **Loki empty query timeout** — Empty selector `{}` caused full-scan timeout. Added `job=~".+"` positive matcher when selector body is empty.

### Added — Backend (`logs.py`, 419 lines — complete rewrite)
- **Log parsing engine** — 5 regex patterns extracting structured fields from raw log text: access_log, error_log, collector_cycle, collector_signal, application.
- **Level normalization** — Maps vendor-specific severities (WARNING, crit, emerg, etc.) to canonical set: debug|info|warn|error|fatal.
- **`GET /api/logs/enriched`** — New endpoint with server-side filters: `level`, `source_type`, `service`, `method`, `status_code` (exact + range 4xx/5xx), `path_contains`, `search`.
- **`GET /api/logs/fields`** — Schema documentation endpoint returning all stream labels and parsed fields with descriptions and conditions.
- **Smart query rewriting** — Service filter rewrites LogQL selector; free-text search pushed to Loki with `|~ "(?i)..."`.
- **Two-tier exclusion** — Python-side `_is_internal_stream()` checks job/service/container labels against set + regex; Loki-side `job!~"..."` for pre-filtering.

### Changed — Frontend (`Logs.tsx`, 846 lines — complete rewrite)
- **FilterBar** — Search input, time range (15min–7 days), limit selector (100–2000), 6 advanced filters with responsive 2/3/6-column grid.
- **LogRow** — Structured display with level badges (color-coded icons), timestamp, source type tag, HTTP inline info (method + status code + path).
- **DetailPanel** — Three-tab detail view: Parsed Fields, Raw Message (with copy), Stream Labels.
- **StatsBar** — Live statistics with total/filtered counts and active filter badges.
- **EmptyState** — Three states (no-data, filtered-empty with clear button, error).
- **Keyboard navigation** — Arrow keys, Enter to toggle detail, Escape to close.
- **Data export** — CSV and JSON download with timestamped filenames.
- Switched from `@heroicons/react` (not installed) to `lucide-react` (consistent with platform).
- Auth via `useAuthStore` + direct `fetch` with Bearer token (consistent with Traces.tsx).

### Documentation
- Added `docs/logs/LOGS_MODULE_IMPLEMENTATION_REPORT.md` — Complete 9-section implementation report.

### Build
- Frontend bundle: `index-CFhg_YA7.js` (1.29 MB)
- Backend deployed to container: 419 lines, 3 endpoints

---


## [v2.6.0] Performance validation for 100 hosts - 2026-02-17

### Added
- Synthetic load test framework for node-exporter targets (up to 100 hosts).
- Scripts: 
un_host_load_test.sh, stop_host_load_test.sh, sim_node_exporter.py.
- Prometheus ile_sd_configs integration for dynamic target injection.

### Tested
- Progressive stress tests: 20 → 50 → 70 → 100 simulated hosts.
- Verified license host counter (get_monitored_hosts_count()) matches Prometheus metrics at every tier.
- All 101 Prometheus targets UP with zero scrape failures at maximum capacity.

### Documentation
- docs/PERFORMANCE_LOAD_TESTS.md — Full capacity report with per-tier results, summary table, architecture diagram, cheat-sheet, and final conclusion.
- Documented capacity results and recommended limits for Enterprise edition (100 hosts).

---

## [2.5.2-alerts] - 2026-02-16

### Fixed
- **Datasource incorrecto en Grafana Explore** - Todos los enlaces usaban datasource uid prometheus en lugar de victoriametrics. Corregido en externalLinks.ts, Anomalies.tsx, Alerts.tsx.
- **MetricMap keys no coincidian con backend** - Motor de correlacion devuelve cpu_usage, memory_usage, etc. pero frontend solo tenia variantes node_*. Anadidas claves duales.
- **Cache del navegador servia bundle obsoleto** - Mitigado con constante CORRELATION_VIEW_BUILD y atributo data-build.

### Changed
- Seccion Grafana en modal Anomalias gated por isAdmin() (solo ADMIN/OWNER).
- Boton Metricas deshabilitado cuando metric_name es vacio o contiene unknown.

### Disabled
- Boton Jaeger Traces en CorrelationView y Anomalies (Proximamente).
- Boton Logs en modal Anomalias (Proximamente).

### Build
- Bundle: index-ksGfZoKC.js / Imagen: rhinometric-console-frontend:v2.5.2-alerts

### Documentation
- Anadido docs/AI_ANOMALIES_CORRELATION_MODULE.md - Documentacion completa del modulo de anomalias y correlacion.

### Added - Notification Templates (AI Anomaly)
- **Plantilla Slack dedicada** (`ai_anomaly_slack.tmpl`) - Titulo con emoji de severidad, descripcion en lenguaje humano, bloque de contexto, troubleshooting inline y botones de accion (Consola + Grafana).
- **Plantilla Email HTML dedicada** (`ai_anomaly_email.tmpl`) - Header con color por severidad, badges, seccion descriptiva, tabla de contexto, botones de accion, guia rapida de troubleshooting, links a documentacion y footer profesional.
- **Ruta dedicada en Alertmanager** - Nuevo route `match: component: ai-anomaly` con receiver `ai-anomaly-alerts` (Slack + Email), posicionado antes de las rutas de severidad genericas.
- **Regla MediumAnomalyDetected** - Nueva regla para anomalias de severidad `medium` con `for: 10m`.
- **Catalogo de troubleshooting** - 10 tipos de metrica con pasos especificos: node_cpu_usage, node_memory_usage, node_disk_usage, node_disk_io, node_network_receive, node_network_transmit, rhinometric_website_availability, rhinometric_website_response_time, rhinometric_website_ssl_expiry, rhinometric_website_dns_time.

### Documentation
- Anadido `docs/ALERTING_NOTIFICATIONS_AI_ANOMALY.md` - Documentacion completa de notificaciones AI Anomaly (flujo, plantillas, catalogo, RBAC, verificacion).


---
## [2.5.1] - 2026-02-09

### 🎯 Infrastructure Stabilization & Security Hardening

This release focuses on production readiness, SSL preparation, and critical bug fixes for the console login system.

### Added
- **Cloudflare SSL Configuration**: Nginx now includes Real IP detection for Cloudflare proxy
  - 15 Cloudflare IP ranges configured for `set_real_ip_from`
  - `CF-Connecting-IP` header support
  - Custom log format with Cloudflare Ray ID
  - X-Forwarded-Proto header pass-through for HTTPS detection
- **Enhanced Security Headers**:
  - Content Security Policy with WebSocket support
  - X-Frame-Options, X-XSS-Protection, X-Content-Type-Options
  - Referrer-Policy and Permissions-Policy headers
- **Domain Configuration**: `server_name` set to `console.rhinometric.com`
- **CORS Configuration**: Added public IP to allowed origins for cross-origin requests

### Changed
- **Memory Optimization**:
  - `rhinometric-loki`: Increased from 512M to **1024M** (2x improvement)
  - `rhinometric-promtail`: Increased from 128M to **256M** (2x improvement)
- **Nginx Routing Architecture**:
  - `/` → Rhinometric Console (Login & Dashboard)
  - `/api/` → Console Backend API
  - `/grafana/` → Grafana Dashboards
  - Removed direct Grafana root routing
- **Rate Limiting**:
  - General: 20 req/s with burst of 40
  - API: 50 req/s with burst of 100
  - Auth endpoints: More aggressive rate limiting for brute-force protection

### Fixed
- **Critical Login Bug**: Resolved authentication failure in console
  - **Root Cause**: Invalid bcrypt password hash in database
  - **Solution**: Regenerated correct hash for `admin` user
  - **Impact**: Login now works with credentials `admin/admin`
- **CORS Blocking**: Frontend requests were being rejected
  - Added `http://89.167.22.228` to CORS_ORIGINS
  - Backend now accepts requests from public IP
- **Nginx Configuration**: Fixed proxy pass to console frontend
  - Corrected service names and port mappings
  - Verified Docker network connectivity

### Security
- **Password Hash**: Replaced corrupted bcrypt hash with valid one
- **Login Protection**: Rate limiting on `/api/auth/*` endpoints (5 req/min)
- **Disk Cleanup**: Removed obsolete backup directory (`/root/rhino-backup-final`) to free 2.0M

### Infrastructure
- **Docker Compose**: All changes applied to `docker-compose-v2.5.0-SECURE.yml`
- **Containers Restarted**:
  - `rhinometric-loki` (Up 24 hours, healthy)
  - `rhinometric-promtail` (Up 2 days)
  - `rhinometric-grafana` (Up 37 seconds after restart)
  - `rhinometric-console-backend` (Up 17 seconds, healthy)
  - `rhinometric-nginx` (Up 10 seconds)

### Verified
- ✅ Login accessible at `http://console.rhinometric.com/login`
- ✅ Grafana accessible at `http://console.rhinometric.com/grafana/`
- ✅ API responding at `http://console.rhinometric.com/api/`
- ✅ 21 Prometheus targets UP
- ✅ JWT authentication working correctly
- ✅ Disk usage: 6% (272G available)

### Migration Notes
- **Default Credentials**: `admin` / `admin` (MUST be changed on first login)
- **SSL Ready**: Platform is prepared for Cloudflare SSL activation
  - Set Cloudflare to "Full" or "Full (Strict)" mode
  - Enable "Always Use HTTPS"
- **DNS Configuration**: Ensure `console.rhinometric.com` points to server IP

---

## [2.5.0] - 2025-11-10

### Initial Production Release
- Multi-component observability platform
- Grafana, Prometheus, Loki, Jaeger integration
- AI-powered anomaly detection
- License management system
- Docker Compose deployment

---

## Version History

- **2.7.2** (2026-04-01) - Platform stability (auth hydration fix) + Logs UX + Collector v1.1.0
- **2.7.1-logs** (2026-03-31) - Logs service_type classification
- **2.7.0-logs** (2026-03-15) - Logs module complete rewrite
- **2.6.0** (2026-02-17) - Performance validation for 100 hosts
- **2.5.2-alerts** (2026-02-16) - Alerting & notifications
- **2.5.1** (2026-02-09) - Infrastructure stabilization & SSL preparation
- **2.5.0** (2025-11-10) - Initial production release

---

**Maintained by**: Rafael Canelón  
**Repository**: [github.com/Rafael2712/mi-proyecto](https://github.com/Rafael2712/mi-proyecto)  
**Documentation**: [github.com/Rafael2712/rhinometric-overview](https://github.com/Rafael2712/rhinometric-overview)
