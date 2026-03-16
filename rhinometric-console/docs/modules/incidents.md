# Module: Incident Management

**Version:** 2.7.0  
**Classification:** Internal  
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

Manage the full lifecycle of incidents from detection through resolution, providing a collaborative workspace for investigation with timeline, comments, and tagging.

## What It Does

- Incidents are created from fired alerts (manual or automatic escalation).
- Each incident follows a state machine: `open` → `acknowledged` → `investigating` → `resolved` → `closed`.
- **Timeline**: Every state transition and significant event is logged as an immutable timeline entry.
- **Comments**: Users can add internal comments to document investigation progress.
- **System Comments**: Automated entries log when alerts attach, resolve, or when anomaly data changes.
- **Tags**: Free-form tags for categorization (e.g., `network`, `database`, `deployment`).
- **Linked Alerts**: Multiple alerts can be attached to a single incident.
- **Linked Anomalies**: Anomaly groups that triggered the incident are referenced.
- **Assigned Owner**: Incidents can be assigned to a specific user.
- **Severity Tracking**: Severity can be adjusted during investigation.
- **Resolution Summary**: A mandatory field when closing an incident.

## What It Does Not Do

- Does not support SLA breach tracking per incident (see SLO/SLA module).
- Does not integrate with external incident management tools (PagerDuty, ServiceNow).
- Does not support post-mortem templates.
- Does not have runbook attachment capability.

## State Machine

```
┌──────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────┐     ┌────────┐
│ Open │ ──▶ │ Acknowledged │ ──▶ │ Investigating │ ──▶ │ Resolved │ ──▶ │ Closed │
└──────┘     └──────────────┘     └───────────────┘     └──────────┘     └────────┘
                                         │                    │
                                         └─── can reopen ─────┘
```

## Data Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `title` | String | Incident title |
| `description` | Text | Initial description |
| `status` | Enum | open, acknowledged, investigating, resolved, closed |
| `severity` | Enum | Low, Medium, High, Critical |
| `assigned_to` | UUID | FK to users (nullable) |
| `tags` | Array[String] | Classification labels |
| `alert_ids` | Array[UUID] | Linked alert references |
| `anomaly_group_ids` | Array[UUID] | Linked anomaly groups |
| `resolution_summary` | Text | Required on close |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last modification |
| `resolved_at` | DateTime | Resolution timestamp |
| `closed_at` | DateTime | Closure timestamp |

### Timeline Entry

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `incident_id` | UUID | Parent incident |
| `entry_type` | Enum | state_change, comment, system, alert_linked |
| `content` | Text | Description or comment body |
| `author_id` | UUID | User who created the entry |
| `created_at` | DateTime | Entry timestamp |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/incidents/` | List incidents with filters |
| POST | `/api/incidents/` | Create an incident |
| GET | `/api/incidents/{id}` | Incident detail with timeline |
| PUT | `/api/incidents/{id}` | Update incident fields |
| POST | `/api/incidents/{id}/transition` | Change state |
| POST | `/api/incidents/{id}/comments` | Add a comment |
| GET | `/api/incidents/{id}/timeline` | Get timeline entries |
| POST | `/api/incidents/{id}/tags` | Add tags |
| DELETE | `/api/incidents/{id}/tags/{tag}` | Remove a tag |

## Dependencies

- **Alert System**: Incidents are created from alerts.
- **AI Anomaly Detector**: Anomaly groups linked to incidents.
- **Root Cause Analysis**: Triggered when an incident is created from anomaly alerts.
- **Notification Pipeline**: Incident state changes can trigger notifications.
- **PostgreSQL**: Stores incidents, timeline entries, comments.

## Frontend

- **Route:** `/incidents`, `/incidents/{id}`
- **Key Features:** Incident list with status/severity filters, detail page with full timeline, comment input, tag management, state transition buttons.

## Known Limitations

1. No external incident tool integration.
2. No post-mortem template system.
3. No SLA timer per incident.
4. No runbook or playbook attachment.
5. No bulk incident operations.

---

*Rhinometric Team — info@rhinometric.com*
