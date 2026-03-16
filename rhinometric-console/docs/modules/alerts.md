# Module: Alert Rules & Alerts

**Version:** 2.7.0  
**Classification:** Internal  
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

Define conditions that trigger alerts and manage the resulting alert lifecycle. Alert rules evaluate anomaly events and metric conditions to produce actionable alerts routed through the notification pipeline.

## What It Does

### Alert Rules
- Users define rules specifying: target service(s), metric(s), condition type, threshold, evaluation window, severity, and notification channel(s).
- Condition types supported:
  - **Threshold**: Metric value exceeds or drops below a static value.
  - **Anomaly-based**: Triggered when the AI anomaly detector flags a group above a configured severity.
  - **Absence**: No data received for a metric within the evaluation window.
- Rules are evaluated against incoming anomaly events and Prometheus/Alertmanager alert payloads.
- Each rule maps to one or more notification channels (Slack, Email).

### Alerts
- An alert is created when a rule condition is met.
- Alert states: `firing` → `acknowledged` → `resolved`.
- Alerts carry metadata: source rule, triggering metric values, severity, affected service, timestamps.
- Resolution occurs via:
  - **Manual**: User acknowledges/resolves in the UI.
  - **Automatic**: Resolve timeout expires after no new anomaly data (configurable per rule).
- Cooldown period prevents re-firing during sustained anomaly events.

## What It Does Not Do

- Does not support complex multi-condition rules (AND/OR logic between metrics).
- Does not support alert escalation chains.
- Does not correlate across multiple services in a single rule.
- Does not support maintenance windows / muting schedules.

## Data Model — Rules

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `name` | String | Rule display name |
| `service_id` | UUID | Target service (nullable for global rules) |
| `condition_type` | Enum | threshold, anomaly, absence |
| `metric` | String | Metric name |
| `threshold_value` | Float | Threshold for comparison |
| `operator` | Enum | gt, lt, gte, lte, eq |
| `evaluation_window` | Integer | Seconds to evaluate |
| `severity` | Enum | Low, Medium, High, Critical |
| `notification_channels` | Array | Channel IDs to notify |
| `cooldown_seconds` | Integer | Cooldown between notifications |
| `resolve_timeout` | Integer | Seconds before auto-resolve |
| `is_active` | Boolean | Whether rule is enabled |

## Data Model — Alerts

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `rule_id` | UUID | FK to alert rules |
| `service_id` | UUID | Affected service |
| `status` | Enum | firing, acknowledged, resolved |
| `severity` | Enum | Inherited from rule |
| `metric_value` | Float | Triggering value |
| `fired_at` | DateTime | When the alert fired |
| `acknowledged_at` | DateTime | When acknowledged |
| `resolved_at` | DateTime | When resolved |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/alert-rules/` | List all rules |
| POST | `/api/alert-rules/` | Create a rule |
| PUT | `/api/alert-rules/{id}` | Update a rule |
| DELETE | `/api/alert-rules/{id}` | Delete a rule |
| GET | `/api/alerts/` | List alerts with filters |
| GET | `/api/alerts/{id}` | Alert detail |
| POST | `/api/alerts/{id}/acknowledge` | Acknowledge an alert |
| POST | `/api/alerts/{id}/resolve` | Manually resolve |
| GET | `/api/alerts/history` | Historical alert log |

## Dependencies

- **AI Anomaly Detector**: Produces anomaly events consumed by anomaly-type rules.
- **Alertmanager**: Receives Prometheus-side alerts for threshold rules.
- **Notification Pipeline**: Sends Slack/Email for triggered alerts.
- **PostgreSQL**: Stores rules and alert records.

## Frontend

- **Routes:** `/alert-rules`, `/alerts`, `/alerts/history`
- **Key Features:** Rule builder form, active alerts dashboard with severity filtering, alert history with search and CSV export.

## Known Limitations

1. No multi-condition rule logic (single condition per rule).
2. No escalation — all channels fire simultaneously.
3. No maintenance window/muting capability.
4. Alert history retention has no automatic purge policy.

---

*Rhinometric Team — info@rhinometric.com*
