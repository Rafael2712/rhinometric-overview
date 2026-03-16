# Rhinometric — Release Notes

**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Version 2.7.0 — March 2026

### Highlights

Version 2.7.0 represents a major platform expansion from monitoring into full service-centric observability and incident management. This release introduces AI-powered anomaly analysis, a complete incident management lifecycle, root cause analysis, SLO tracking, and a notification pipeline — transforming Rhinometric into an operational intelligence platform organized around monitored services.

### New Modules

| Module | Description |
|--------|-------------|
| **AI Insights** | Natural-language anomaly summaries with confidence and severity scoring |
| **Root Cause Analysis** | Automated dependency-graph traversal to identify failure origin |
| **Service Map** | Live topology visualization with health status overlay |
| **SLO/SLA Management** | Error-budget tracking with proactive breach alerting |
| **Correlation Engine** | Cross-signal linking of metrics and logs for context enrichment |
| **Incident Management** | Full lifecycle with timeline, comments, tags, and state machine |
| **Alert History** | Persistent searchable log of all alerts with CSV export |
| **Alert Rules** | Configurable conditions with threshold, anomaly, and absence types |
| **Notification Pipeline** | Slack and email delivery with cooldown and deduplication |
| **RBAC** | Four-role permission system enforced at API and UI levels |

### Improvements

- **Grafana Deep Links**: Direct dashboard URLs with time-range context for CPU, memory, latency, HTTP errors, and saturation panels.
- **AI Anomaly Detection**: 30% MAD threshold guard reduces false positives by filtering statistically insignificant anomaly groups.
- **Frontend Error Handling**: Graceful 401 handling with login redirect instead of broken UI states.
- **Notification Templates**: Rich templates with severity badges, metric snapshots, and action links.
- **Backend API**: Standardized JSON error responses across all 20 routers.

### Bug Fixes

- Fixed duplicate email notifications during simultaneous anomaly group resolution within the same cooldown window.
- Fixed race condition between incident creation and alert resolution causing conflicting notifications.
- Fixed cooldown timer reset logic that allowed premature re-notification on long-running incidents.
- Fixed 401 error on AI Anomalies page when authentication token expires mid-session.
- Fixed incorrect time-range calculation in Grafana deep link URLs.

### Infrastructure

- 21 Docker containers running in production configuration.
- Anomaly detection engine deployed as dedicated containerized service.
- License Server v2 operational with service-based tier validation.
- Observability stack: Prometheus, VictoriaMetrics, Loki, Grafana, Alertmanager, with optional distributed tracing via Jaeger/OTel Collector.

---

## Version 2.5.0 — November 2024

### Highlights

First public-facing release with product documentation and branding. Introduced AI anomaly detection, long-term metric storage, and the core observability stack.

### New Features

- AI Anomaly Detection v1 (IsolationForest-based).
- VictoriaMetrics integration for long-term metric retention.
- Loki log aggregation with Promtail agents.
- Distributed tracing infrastructure deployed (Jaeger + OTel Collector) — available for instrumented applications.
- Rhinometric brand identity applied to frontend.
- Public product documentation.

### Changes

- Frontend migrated from Create React App to Vite.
- Authentication changed from session-based to JWT.
- Prometheus reconfigured as 30-day short-term buffer with VictoriaMetrics as long-term store.

---

## Version 2.1.0 — September 2024

### Highlights

Initial platform release with core service monitoring capabilities.

### Features

- Service monitoring with Prometheus metric collection.
- Basic alerting via Alertmanager with email notification.
- Grafana dashboards for infrastructure and service metrics.
- React 18 + TypeScript frontend.
- PostgreSQL database for platform state.
- Redis caching layer.
- Docker Compose deployment with 15 services.
- Nginx reverse proxy with SSL termination.

---

*Copyright 2024–2026 Rhinometric. All rights reserved.*
