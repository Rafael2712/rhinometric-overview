# Notification Channels — Technical Reference

> **Module:** `backend/routers/settings.py` + `backend/services/alertmanager_template.py`  
> **Version:** 2.5.1  
> **Last updated:** 2026-03-03

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [API Endpoints](#api-endpoints)
3. [Data Model](#data-model)
4. [Slack Configuration](#slack-configuration)
5. [Email Configuration (Zoho API)](#email-configuration-zoho-api)
6. [Alertmanager Integration](#alertmanager-integration)
7. [Alert Deep-Links](#alert-deep-links)
8. [Deployment Checklist](#deployment-checklist)
9. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    Rhinometric Console                        │
│  ┌──────────┐    ┌──────────────┐    ┌────────────────────┐  │
│  │ Frontend  │───▶│ Settings API │───▶│ notification_      │  │
│  │ Settings  │    │ (FastAPI)    │    │ channels.json      │  │
│  │ Page      │◀───│              │    │ (chmod 600)        │  │
│  └──────────┘    └──────┬───────┘    └────────────────────┘  │
│                         │                                     │
│                         ▼                                     │
│              ┌─────────────────────┐                          │
│              │ alertmanager_       │                          │
│              │ template.py         │                          │
│              │ (config renderer)   │                          │
│              └──────────┬──────────┘                          │
│                         │                                     │
│                         ▼                                     │
│              ┌─────────────────────┐                          │
│              │ alertmanager.yml    │                          │
│              │ (generated config)  │                          │
│              └─────────────────────┘                          │
└──────────────────────────────────────────────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
     ┌───────────┐ ┌───────────┐ ┌───────────────┐
     │  Slack    │ │  Email    │ │  Alertmanager  │
     │  Webhook  │ │  (Zoho    │ │  (routes,      │
     │  API      │ │   API)    │ │   receivers)   │
     └───────────┘ └───────────┘ └───────────────┘
```

### Key Design Decisions

- **Secrets storage:** `notification_channels.json` with `chmod 600`, never committed to git.
- **Alertmanager config generation:** Deterministic YAML rendering via Python template (no regex edits).
- **Email delivery:** Uses **Zoho Mail API** (HTTPS 443) instead of SMTP, because Hetzner blocks outbound ports 587/465.
- **Webhook URL masking:** GET endpoint returns redacted URLs (`https://hooks.slack.com/s...pwcdQc`). POST preserves real URL if masked value is received.
- **Alert deep-links:** Both Slack buttons and email buttons link to metric-specific dashboards (Console viewer or Grafana direct).

---

## API Endpoints

All endpoints require `Authorization: Bearer <token>` header.  
Base path: `/api/settings`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | Any role | Get system settings (AI alerting toggle) |
| `PUT` | `/ai-alerts` | Admin | Enable/disable AI anomaly alerting |
| `GET` | `/notification-channels` | Admin | Get notification channel config (secrets redacted) |
| `POST` | `/notification-channels` | Admin | Save channels + regenerate alertmanager.yml |
| `POST` | `/notification-channels/test/slack` | Admin | Send test message to configured Slack channel |
| `POST` | `/notification-channels/test/email` | Admin | Send test email to configured recipients |
| `GET` | `/system-info` | Any role | System info (version, containers, uptime) |
| `GET` | `/email/status` | Admin | Email delivery status (Zoho API health) |
| `POST` | `/alertmanager-webhook/email` | None (internal) | Alertmanager webhook → forwards alerts as emails via Zoho API |

### Authentication

```bash
# Login (form-urlencoded, NOT JSON):
curl -X POST https://console-staging.rhinometric.com/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=YOUR_PASSWORD"

# Response:
# {"access_token": "eyJhbG...", "token_type": "bearer"}
```

---

## Data Model

### notification_channels.json

```json
{
  "slack": {
    "enabled": true,
    "webhook_url": "https://hooks.slack.com/services/T.../B.../xxx",
    "channel": "#your-channel"
  },
  "email": {
    "enabled": true,
    "smtp_host": "smtp.zoho.eu",
    "smtp_port": 587,
    "smtp_username": "user@yourdomain.com",
    "smtp_password": "",
    "smtp_require_tls": true,
    "from_email": "user@yourdomain.com",
    "to_emails": ["recipient@yourdomain.com"]
  },
  "zoho_api": {
    "client_id": "1000.XXXXX",
    "client_secret": "xxxxx",
    "refresh_token": "1000.xxxxx",
    "account_id": "74279XXXXX",
    "from_address": "user@yourdomain.com"
  }
}
```

**File location inside container:** `/app/data/notification_channels.json`  
**File location on host (volume mount):** `/home/rafa/rhinometric_data_v2.5/console-backend/data/notification_channels.json`

---

## Slack Configuration

### Prerequisites

1. Create a Slack App at https://api.slack.com/apps
2. Enable **Incoming Webhooks**
3. Add a webhook to the desired channel
4. Copy the webhook URL

### Configuration Fields

| Field | Example | Description |
|-------|---------|-------------|
| `enabled` | `true` | Enable/disable Slack notifications |
| `webhook_url` | `https://hooks.slack.com/services/T.../B.../xxx` | Incoming Webhook URL |
| `channel` | `#nuevo-canal` | Target Slack channel (must match webhook) |

### What Gets Sent

When an AI anomaly is detected with `severity: critical`:

- **Title:** 🔴 [CRITICAL] AI Anomaly: node_cpu_usage
- **Body:** Metric details, deviation %, current/baseline values
- **Buttons:**
  - **"Ver Dashboard en Consola"** → Opens the relevant dashboard inside the Console app
  - **"Ver en Grafana"** → Opens the specific Grafana panel for that metric

### Testing

```bash
curl -X POST https://console-staging.rhinometric.com/api/settings/notification-channels/test/slack \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

---

## Email Configuration (Zoho API)

### Why Zoho API Instead of SMTP?

Hetzner Cloud VMs **block outbound SMTP ports** (25, 465, 587) by default. The platform uses Zoho Mail's REST API over HTTPS (port 443) as a reliable alternative.

### Zoho API Setup

1. Go to https://api-console.zoho.eu/
2. Create a **Self Client** application
3. Generate a refresh token with scope: `ZohoMail.messages.CREATE`
4. Note the `client_id`, `client_secret`, and `refresh_token`
5. Get your `account_id` from Zoho Mail admin

### Configuration Fields

| Field | Example | Description |
|-------|---------|-------------|
| `email.enabled` | `true` | Enable/disable email notifications |
| `email.from_email` | `user@domain.com` | Sender address (must be verified in Zoho) |
| `email.to_emails` | `["admin@domain.com"]` | Recipient list |
| `zoho_api.client_id` | `1000.XXXXX` | Zoho API Client ID |
| `zoho_api.client_secret` | `xxxxx` | Zoho API Client Secret |
| `zoho_api.refresh_token` | `1000.xxxxx` | OAuth2 Refresh Token |
| `zoho_api.account_id` | `74279XXXXX` | Zoho Mail Account ID |
| `zoho_api.from_address` | `user@domain.com` | Must match `email.from_email` |

### Email Content

Emails are HTML-formatted with:
- Red/orange header based on severity
- Metric details (name, severity, component, service, values)
- Two action buttons:
  - **"Ver Dashboard en Consola"** → Opens the corresponding Console dashboard viewer
  - **"Ver en Grafana"** → Opens the specific Grafana panel

### Testing

```bash
curl -X POST https://console-staging.rhinometric.com/api/settings/notification-channels/test/email \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

---

## Alertmanager Integration

### Config Generation Flow

1. Admin saves notification channels via UI or API
2. `settings.py` calls `alertmanager_template.py → render_alertmanager_config()`
3. A complete `alertmanager.yml` is generated deterministically
4. File is written to `/etc/alertmanager/alertmanager.yml`
5. Alertmanager is reloaded via `/-/reload` HTTP endpoint

### Generated Receivers

| Receiver | Purpose | Channels |
|----------|---------|----------|
| `ai-anomaly-alerts` | AI-detected critical anomalies | Slack + Email (via webhook) |
| `team-notifications` | General alerts | Slack + Email |
| `critical-alerts` | Prometheus critical alerts | Slack + Email |
| `warning-alerts` | Prometheus warnings | Slack |
| `info-alerts` | Informational alerts | Slack |
| `blackhole` | Suppressed alerts | None |

### Slack Templates

Located at: `/opt/rhinometric/alertmanager/templates/ai_anomaly_slack.tmpl`

The template uses Go template syntax with metric-conditional deep-links.

---

## Alert Deep-Links

### Metric → Dashboard Mapping

| Metric | Console Dashboard | Grafana Panel |
|--------|------------------|---------------|
| `node_cpu_usage` | `/dashboards/rhinometric-system-overview/view` | System Overview → Panel 1 (CPU) |
| `node_memory_usage` | `/dashboards/rhinometric-system-overview/view` | System Overview → Panel 2 (Memory) |
| `node_disk_usage` | `/dashboards/rhinometric-system-overview/view` | System Overview → Panel 3 (Disk) |
| `node_disk_io` | `/dashboards/rhinometric-system-overview/view` | System Overview → Panel 3 (Disk) |
| `node_network_receive` | `/dashboards/rhinometric-system-overview/view` | System Overview → Panel 6 (Network) |
| `node_network_transmit` | `/dashboards/rhinometric-system-overview/view` | System Overview → Panel 6 (Network) |
| All other metrics | `/dashboards/ai-anomaly-service/view` | AI Anomaly Service dashboard |

### Implementation

- **Slack buttons:** Go templates in `alertmanager_template.py` → `actions[].url`
- **Email buttons:** Python dict mapping in `settings.py` → `alertmanager_email_webhook()`
- **Slack message text:** Go template conditionals in `ai_anomaly_slack.tmpl`

---

## Deployment Checklist

### New Installation

- [ ] Configure `notification_channels.json` with Slack webhook URL and channel
- [ ] Configure Zoho API credentials (`zoho_api` section)
- [ ] Set `email.enabled: true` and `slack.enabled: true`
- [ ] Verify from Settings page in Console UI
- [ ] Test Slack with "Test Slack" button
- [ ] Test Email with "Test Email" button
- [ ] Verify alertmanager.yml was generated correctly
- [ ] Confirm AI Alerting toggle is ON in Settings

### After Container Restart

- [ ] Verify `notification_channels.json` persists (volume mounted)
- [ ] Check backend logs: `docker logs rhinometric-console-backend`
- [ ] Confirm alertmanager loaded config: `docker logs rhinometric-alertmanager`

### Key Files

| File | Location (Host) | Location (Container) |
|------|-----------------|---------------------|
| Channels config | `/home/rafa/rhinometric_data_v2.5/console-backend/data/notification_channels.json` | `/app/data/notification_channels.json` |
| Settings API | `backend/routers/settings.py` | `/app/routers/settings.py` |
| Template renderer | `backend/services/alertmanager_template.py` | `/app/services/alertmanager_template.py` |
| Email service | `backend/services/email_service.py` | `/app/services/email_service.py` |
| Alertmanager config | `/opt/rhinometric/alertmanager/alertmanager.yml` | `/etc/alertmanager/alertmanager.yml` |
| Slack template | `/opt/rhinometric/alertmanager/templates/ai_anomaly_slack.tmpl` | `/etc/alertmanager/templates/ai_anomaly_slack.tmpl` |

---

## Troubleshooting

### Slack messages not arriving

1. Check webhook URL is valid: `curl -X POST -H "Content-Type: application/json" -d '{"text":"test"}' YOUR_WEBHOOK_URL`
2. Verify channel name matches webhook configuration
3. Check alertmanager logs: `docker logs rhinometric-alertmanager`
4. Ensure AI Alerting is enabled in Settings

### Emails not arriving

1. Check backend logs: `docker logs rhinometric-console-backend | grep -i email`
2. Verify Zoho API credentials are correct (test with Test Email button)
3. Check `from_address` matches a verified Zoho email
4. Verify `zoho_api` section exists in `notification_channels.json`
5. Common error: `missing 1 required positional argument: 'from_email'` → ensure `from_address` is set in zoho_api config

### Webhook URL gets overwritten

The GET endpoint returns a **redacted** URL (e.g., `https://hooks.slack.com/s...pwcdQc`). The backend detects masked URLs (containing `...`) and preserves the real URL from disk. If the URL appears wrong:

1. Read the real URL directly: `cat /home/rafa/rhinometric_data_v2.5/console-backend/data/notification_channels.json`
2. Never copy the redacted URL from the API response to save back

### Alertmanager config not updating

1. Settings API auto-regenerates on save → check response for errors
2. Manual regeneration: Save notification channels again from UI
3. Verify file: `cat /opt/rhinometric/alertmanager/alertmanager.yml`
4. Reload manually: `docker exec rhinometric-alertmanager wget -qO- http://localhost:9093/-/reload`
