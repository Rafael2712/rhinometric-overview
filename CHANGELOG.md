# Changelog - Rhinometric Platform

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

- **2.5.1** (2026-02-09) - Infrastructure stabilization & SSL preparation
- **2.5.0** (2025-11-10) - Initial production release
- **2.4.x** - Beta releases
- **2.3.x** - Alpha releases

---

**Maintained by**: Rafael Canelón  
**Repository**: [github.com/Rafael2712/mi-proyecto](https://github.com/Rafael2712/mi-proyecto)  
**Documentation**: [github.com/Rafael2712/rhinometric-overview](https://github.com/Rafael2712/rhinometric-overview)
