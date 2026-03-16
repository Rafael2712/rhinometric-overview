# Rhinometric — Public Roadmap

**Version:** 2.7.0
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Current Status

Rhinometric 2.7.0 is the latest release, delivering a service-centric observability platform with AI-powered anomaly detection, incident management, root cause analysis, and operational intelligence across 21 containerized services.

---

## Planned for v2.8.0 (Q2 2026)

### Platform Stability
- **Configurable Home Dashboard**: User-selectable widgets with role-based layout persistence.
- **Scalable Service Monitoring**: Pagination, search, and bulk operations for 100–200 monitored services.
- **Database Migrations**: Alembic-managed schema versioning for safe upgrades.

### Distribution
- **Ansible Installer**: Automated enterprise deployment with pre-flight validation, OS compatibility checks, and rollback capability.
- **Compiled License Validator**: Rust-based binary with service-based validation and tamper resistance (replaces Python implementation).

### Quality
- **Test Suite**: Unit tests (80% coverage target), integration tests, E2E tests for critical user flows.
- **Load Testing**: Validated operation with 100+ services, 1000+ metric streams, 50+ anomaly groups, 10+ concurrent users.

### Documentation
- **Documentation Site**: Versioned, searchable documentation portal with multi-language support (EN/ES).

---

## Planned for v2.9.0 (Q3 2026)

### Security
- **Audit Trail**: Complete log of all administrative operations.
- **API Key Authentication**: Programmatic access for automation and integrations.
- **Secret Management**: Encrypted vault integration for credentials and keys.

### Platform Expansion
- **Microsoft Teams Notifications**: Native Teams channel support.
- **PagerDuty Integration**: Alert routing to PagerDuty services.

---

## Planned for v3.0.0 (Q4 2026)

### Enterprise Features
- **SSO/LDAP/SAML**: External identity provider integration.
- **Native Dashboard Builder**: Drag-and-drop dashboard creation without Grafana dependency.
- **Multi-Tenant Architecture**: Tenant isolation with per-tenant branding, cross-tenant admin views.
- **Advanced Notification Channels**: OpsGenie, SMS (Twilio), custom webhooks.

### AI Enhancements
- **Predictive Analytics**: Trend-based forecasting for capacity planning.
- **Custom Model Tuning**: Per-service anomaly detection parameters.
- **False Positive Feedback Loop**: Learning from user-marked false positives to improve accuracy.

---

## Completed (v2.7.0)

| Feature | Status |
|---------|--------|
| AI Anomaly Detection with MAD Guard | ✅ Delivered |
| AI Insights (Natural Language) | ✅ Delivered |
| Alert Rules Engine | ✅ Delivered |
| Alert Lifecycle & History | ✅ Delivered |
| Incident Management (Timeline/Comments/Tags) | ✅ Delivered |
| Root Cause Analysis | ✅ Delivered |
| Service Map | ✅ Delivered |
| SLO/SLA with Error Budget | ✅ Delivered |
| Correlation Engine (Metrics/Logs) | ✅ Delivered |
| Notification Pipeline (Slack/Email) | ✅ Delivered |
| RBAC (4 Roles) | ✅ Delivered |
| Service-Based License Tiers | ✅ Delivered |
| Grafana Deep Links | ✅ Delivered |
| 21-Container Docker Stack | ✅ Delivered |
| Distributed Tracing Infrastructure (Available) | ✅ Deployed |

---

## How We Prioritize

Items are prioritized using a P0–P2 framework:

- **P0 (Must Have)**: Required for commercial viability and customer deployment.
- **P1 (Should Have)**: Significantly improves product value and operational readiness.
- **P2 (Nice to Have)**: Enhances competitive positioning and customer experience.

---

*Copyright 2024–2026 Rhinometric. All rights reserved.*
