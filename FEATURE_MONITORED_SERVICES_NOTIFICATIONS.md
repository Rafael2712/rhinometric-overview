# Feature: Monitored Services Split & Notification Settings

**Version:** v2.6.0-alerts  
**Date:** 2026-02-20  
**Branch:** `feature/monitored-services-and-notifications`

---

## Overview

This release introduces two major features to the Rhinometric monitoring console:

1. **Platform vs Client Services Classification**  Services are now split into platform (internal infrastructure) and client (customer-facing) categories across the dashboard and services page.
2. **Notification Settings UI**  Admin users can configure Slack and Email/SMTP alert delivery directly from the Settings page, with automatic Alertmanager integration.

---

## Feature 1: Platform vs Client Services

### Concept

Every monitored service is automatically classified:

| Category | Description | Examples |
|---|---|---|
| **Platform** | Internal infrastructure services | Prometheus, Grafana, Loki, Alertmanager, Jaeger, Redis, PostgreSQL, Console Backend, AI Anomaly, Node Exporter, cAdvisor |
| **Client** | Customer-facing monitored endpoints | External websites, client APIs, SaaS health checks |

Classification is based on the Prometheus scrape job name. Known infrastructure jobs are tagged as "platform"; everything else defaults to "client".

### Dashboard (Home Page)

The "Monitored Services" KPI card now shows:
- **Main value**: Client service count (what matters most to the customer)
- **Subtitle**: `Client: 1  Platform: 11  Total: 12`

This gives operators an instant view of client vs infrastructure health.

### Services Page

| Element | Description |
|---|---|
| **Filter Buttons** | Toggle between All, Platform, and Client views |
| **Stat Cards** | Total Services, Platform (with healthy count), Client (with healthy count), Down |
| **Category Column** | Each row shows a badge: Shield icon for platform, Globe icon for client |
| **Empty State** | Friendly message when no services match the filter |

### API Endpoints

```
GET /api/kpis
  -> monitored_hosts.client_services_count
  -> monitored_hosts.platform_services_count
  -> monitored_hosts.total_services_count

GET /api/kpis/services
  -> services[].category = "platform" | "client"
  -> platform_services, platform_up, client_services, client_up

GET /api/kpis/services/{filter_type}
  filter_type: "all" | "platform" | "client"
  -> Filtered list with same response structure
```

---

## Feature 2: Notification Settings

### Concept

Administrators can configure Slack and Email alert delivery from the UI. When settings are saved, the system automatically updates Alertmanager's configuration and triggers a reload.

### Slack Configuration

| Field | Description |
|---|---|
| **Webhook URL** | Slack Incoming Webhook URL |
| **Channel** | Target Slack channel (e.g., `#alerts`) |
| **Test Button** | Sends a test message to verify the webhook works |

### Email / SMTP Configuration

| Field | Description |
|---|---|
| **SMTP Host** | Mail server hostname |
| **SMTP Port** | Mail server port (default: 587) |
| **Username** | SMTP authentication username |
| **Password** | SMTP authentication password (masked in API) |
| **From Address** | Sender email address |
| **Use TLS** | Enable/disable TLS encryption |
| **Test Button** | Sends a test email to verify SMTP works |

### Alertmanager Integration

When notification settings are saved via the API:
1. The `alertmanager.yml` global section is updated with the new SMTP and Slack values
2. Alertmanager is reloaded via `POST /-/reload`
3. All existing alert routes immediately use the new configuration

### API Endpoints

```
GET  /api/settings/notifications      -> Current config (password masked)
PUT  /api/settings/notifications      -> Save + update Alertmanager
POST /api/settings/notifications/slack-test  -> Test Slack webhook
POST /api/settings/notifications/email-test  -> Test SMTP delivery
```

### Security

- SMTP password is never returned in API responses; only a `smtp_password_set: bool` flag indicates if one is stored
- Settings endpoints require OWNER or ADMIN role
- Test endpoints validate connectivity without exposing credentials

---

## Architecture

```
Browser (React)
    |
    v
Settings.tsx  <-->  PUT /api/settings/notifications
                         |
                         v
                    settings.py (FastAPI)
                         |
                    +----+----+
                    |         |
                    v         v
               PostgreSQL   alertmanager.yml
              (settings)     (global config)
                              |
                              v
                         Alertmanager
                         /-/reload
```

---

## Testing

All endpoints were smoke-tested with the following results:

| Test | Result |
|---|---|
| KPIs with split counts | Client: 1, Platform: 11, Total: 12 |
| Services (all) | 20 services with category field |
| Services (platform filter) | 19 platform services |
| Services (client filter) | 1 client service |
| Notification settings GET | Returns defaults (empty config) |
| General settings | AI alerts toggle preserved |