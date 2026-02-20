# Changelog - v2.6.0-alerts

## [v2.6.0-alerts] - 2026-02-20

### New Features

#### 1. Platform vs Client Services Split

Monitored services are now classified into two categories:

- **Platform Services**: Internal infrastructure (Prometheus, Grafana, Loki, Alertmanager, Jaeger, Redis, PostgreSQL, etc.)
- **Client Services**: Customer-facing endpoints and monitored websites

**Dashboard Changes:**
- Home KPI card shows: "Client: X  Platform: Y  Total: Z"
- Services page has filter buttons: All / Platform / Client
- Each service displays a category badge (Shield for platform, Globe for client)
- Four stat cards: Total, Platform (with health), Client (with health), Down

**API Changes:**
- `GET /api/kpis`  Returns `client_services_count`, `platform_services_count`, `total_services_count`
- `GET /api/kpis/services`  Each service includes a `category` field
- `GET /api/kpis/services/{filter_type}`  New filtered endpoint (all/platform/client)

---

#### 2. Notification Settings (Slack & Email)

Admin/Owner users can configure alert notification channels directly from the Settings page.

**Slack Configuration:**
- Webhook URL and Channel configuration
- Test button to verify connectivity
- Auto-updates Alertmanager configuration

**Email / SMTP Configuration:**
- Host, Port, Username, Password, From address, TLS toggle
- Password stored securely (masked in API responses)
- Test button sends a verification email
- Auto-updates Alertmanager SMTP global config

**API Changes:**
- `GET /api/settings/notifications`  Retrieve current notification config
- `PUT /api/settings/notifications`  Save config + update Alertmanager
- `POST /api/settings/notifications/slack-test`  Send test Slack message
- `POST /api/settings/notifications/email-test`  Send test email

---

### Files Modified

| Component | File | Description |
|---|---|---|
| Backend | `routers/kpis.py` | Service classification + filtered endpoints |
| Backend | `routers/settings.py` | Notification CRUD + Alertmanager wiring |
| Frontend | `pages/Home.tsx` | KPI subtitle driven by backend |
| Frontend | `pages/Services.tsx` | Filter UI + category badges + split stats |
| Frontend | `pages/Settings.tsx` | Slack + Email panels with test buttons |

### Infrastructure

- Docker image tag: `v2.5.2-alerts`
- All endpoints smoke-tested
- Alertmanager auto-reloaded on settings change