# Module: Notifications

**Version:** 2.7.0  
**Classification:** Internal  
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

Deliver alert and incident notifications to operations teams via configurable channels. Currently supports Slack and Email with per-rule channel assignment.

## What It Does

### Channels
- **Slack**: Sends formatted messages to configured Slack webhooks. Messages include severity badge, service name, metric values, and direct Grafana/platform links.
- **Email**: Sends HTML-formatted emails via SMTP. Templates include alert summary, severity indicator, metric snapshot, and action links.

### Pipeline Behavior
- Notifications are triggered by the Alert Rules engine when a rule condition fires.
- Each alert rule specifies which notification channel(s) to use.
- **Cooldown**: After sending a notification for a rule, a configurable cooldown period prevents re-sending for the same rule/service combination. This eliminates duplicate notifications during sustained anomaly events.
- **Resolve Timeout**: When no new anomaly data is received for a configurable period, the alert auto-resolves and a resolution notification is sent.
- **Incident Notifications**: State transitions on incidents (created, acknowledged, resolved, closed) trigger channel-appropriate notifications.

### Templates
- Alert firing: Service name, severity, triggering metric, current value, threshold, Grafana link, platform link.
- Alert resolved: Same data plus resolution reason and duration.
- Incident update: Incident title, new state, assigned user, comment summary.

## What It Does Not Do

- Does not support Microsoft Teams, PagerDuty, OpsGenie, or SMS.
- Does not support custom notification templates (templates are hardcoded).
- Does not support escalation chains or on-call schedules.
- Does not support notification grouping/batching (each alert sends immediately).
- Does not support user-level notification preferences.

## Data Model

### Notification Channel

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `name` | String | Channel display name |
| `type` | Enum | slack, email |
| `config` | JSON | Channel-specific config (webhook URL, SMTP settings, recipients) |
| `is_active` | Boolean | Whether channel is enabled |
| `created_at` | DateTime | Creation timestamp |

### Notification Log

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `channel_id` | UUID | FK to notification channel |
| `alert_id` | UUID | FK to alert that triggered it |
| `status` | Enum | sent, failed, throttled |
| `sent_at` | DateTime | Delivery timestamp |
| `error_message` | String | Error details if failed |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/notifications/channels` | List notification channels |
| POST | `/api/notifications/channels` | Create a channel |
| PUT | `/api/notifications/channels/{id}` | Update channel config |
| DELETE | `/api/notifications/channels/{id}` | Remove a channel |
| POST | `/api/notifications/channels/{id}/test` | Send a test notification |
| GET | `/api/notifications/log` | Notification delivery log |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SMTP_HOST` | — | Email server hostname |
| `SMTP_PORT` | `587` | Email server port |
| `SMTP_USER` | — | SMTP authentication user |
| `SMTP_PASSWORD` | — | SMTP authentication password |
| `SMTP_FROM` | `info@rhinometric.com` | Sender address |
| `NOTIFICATION_COOLDOWN` | `300` | Default cooldown in seconds |
| `RESOLVE_TIMEOUT` | `600` | Default resolve timeout in seconds |

## Dependencies

- **Alert Rules Engine**: Triggers notifications when rules fire.
- **Incident Module**: Triggers notifications on state transitions.
- **PostgreSQL**: Stores channel configurations and delivery logs.
- **External Services**: Slack API (webhooks), SMTP server.

## Frontend

- **Route:** `/notifications`
- **Key Features:** Channel management (add/edit/test/delete), delivery log viewer with status filtering.

## Known Limitations

1. Only Slack and Email channels supported.
2. No custom template editing.
3. No escalation chains.
4. No notification batching/digest mode.
5. No per-user notification preferences.
6. Failed notifications are logged but not automatically retried.

---

*Rhinometric Team — info@rhinometric.com*
