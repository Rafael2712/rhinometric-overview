# Rhinometric — Modules

**Version:** 2.7.0  
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Module Overview

Rhinometric is organized into 15 functional modules. The table below summarizes each module's purpose, availability by license tier, and current maturity.

| Module | Purpose | Community | Professional | Enterprise | Maturity |
|--------|---------|:---------:|:------------:|:----------:|:--------:|
| Service Monitoring | Health checks and availability tracking | ✓ | ✓ | ✓ | Stable |
| AI Anomaly Detection | Automatic anomaly identification | — | ✓ | ✓ | Stable |
| AI Insights | Natural-language anomaly summaries | — | ✓ | ✓ | Stable |
| Alert Rules | Configurable alert conditions | Basic | Full | Full | Stable |
| Alerts | Alert lifecycle management | ✓ | ✓ | ✓ | Stable |
| Alert History | Historical alert log and export | ✓ | ✓ | ✓ | Stable |
| Incident Management | Full lifecycle incident tracking | — | ✓ | ✓ | Stable |
| Root Cause Analysis | Automated failure origin identification | — | — | ✓ | Beta |
| Service Map | Dependency topology visualization | — | ✓ | ✓ | Stable |
| SLO/SLA | Error budget and compliance tracking | — | — | ✓ | Stable |
| Correlation Engine | Cross-signal context enrichment | — | ✓ | ✓ | Beta |
| Notifications | Slack and Email delivery pipeline | Email | All | All | Stable |
| Logs & Traces | Centralized log and trace access | ✓ | ✓ | ✓ | Stable |
| RBAC | Role-based access control | 2 roles | 3 roles | 4 roles | Stable |
| Licensing | License validation and tier enforcement | ✓ | ✓ | ✓ | Stable |

---

## Module Details

### Service Monitoring
Register endpoints with URL, protocol, and check interval. Rhinometric uses Blackbox Exporter to perform periodic health probes, storing results in Prometheus/VictoriaMetrics. The dashboard shows real-time status, availability percentages over configurable windows, and links to Grafana metric panels.

**Key capabilities:**
- HTTP/HTTPS/TCP health probes
- Availability calculation (1h, 24h, 7d, 30d)
- Service grouping with tags
- Grafana deep links for metric drill-down

---

### AI Anomaly Detection
A containerized IsolationForest model analyzes metric time-series from VictoriaMetrics at regular intervals. Data points scoring above the anomaly threshold are grouped by service and time window. A 30% MAD (Median Absolute Deviation) guard filters noise by discarding groups with insufficient statistical significance.

**Key capabilities:**
- Automatic anomaly detection without manual thresholds
- Severity scoring (Low, Medium, High, Critical)
- Anomaly grouping by service and time
- Noise filtering with MAD threshold guard

---

### AI Insights
Generates human-readable summaries for detected anomaly groups, explaining what changed, by how much, and potential operational impact. Summaries include confidence scores and severity justification.

**Key capabilities:**
- Natural-language anomaly explanations
- Confidence scoring
- Severity context

---

### Alert Rules & Alerts
Users define rules with conditions (threshold, anomaly-based, absence), target services, evaluation windows, and notification channels. When conditions are met, alerts are created with a lifecycle: firing → acknowledged → resolved. Cooldown periods prevent duplicate notifications; resolve timeouts enable automatic resolution.

**Key capabilities:**
- Threshold, anomaly, and absence conditions
- Per-rule notification channel assignment
- Cooldown and resolve timeout
- Alert lifecycle management

---

### Incident Management
Full-lifecycle incident tracking from detection to closure. State machine: open → acknowledged → investigating → resolved → closed. Each incident has a timeline with state changes, user comments, and system events. Tags, linked alerts, assigned owners, and mandatory resolution summaries support structured investigation.

**Key capabilities:**
- 5-state incident lifecycle
- Timeline with user and system comments
- Tag-based categorization
- Linked alerts and anomaly groups

---

### Root Cause Analysis
When an incident is created from anomaly alerts, the platform traverses the service dependency graph (from Service Map) and identifies upstream/downstream services with concurrent anomalies. Candidates are ranked by temporal precedence, dependency depth, severity, and propagation pattern.

**Key capabilities:**
- Dependency graph traversal
- Temporal and severity-based ranking
- Confidence scoring
- Automatic triggering on incident creation

---

### Service Map
Interactive dependency graph showing services as nodes and their relationships as directed edges. Node colors reflect health status (green/yellow/red), and active anomalies are visually highlighted. Selecting a node shows detail including current anomalies, alerts, and Grafana links.

**Key capabilities:**
- Interactive topology visualization
- Real-time health status overlay
- Anomaly propagation highlighting

---

### SLO/SLA Tracking
Define objectives per service with target metrics (availability, latency, error rate), target values, and rolling evaluation windows. The engine calculates current compliance and error-budget consumption. Alerts fire when budget drops below configured thresholds.

**Key capabilities:**
- Error budget tracking with burn rate
- Multiple objective types (availability, latency, error rate)
- Budget exhaustion alerting
- SLA metadata support

---

### Correlation Engine
Links metrics, logs, and traces around an anomaly event. Queries VictoriaMetrics for co-occurring metric deviations, Loki for error-level log entries, and Jaeger for high-latency or error traces within the trigger time window. Results enrich anomaly and incident views.

**Key capabilities:**
- Cross-signal correlation (metrics + logs + traces)
- Temporal proximity ranking
- Anomaly and incident enrichment

---

### Notifications
Alert-triggered notifications delivered via Slack webhooks and SMTP email. Templates include severity badges, metric values, service names, and platform/Grafana links. Cooldown periods prevent notification storms during sustained events.

**Key capabilities:**
- Slack and Email channels
- Per-rule channel assignment
- Cooldown and deduplication
- Resolution notifications

---

### Logs & Traces
Centralized collection and access to log and trace data. Promtail agents ship container logs to Loki; OpenTelemetry-instrumented services export traces to Jaeger via the OTel Collector. Data accessible through Grafana Explore and the Correlation Engine.

**Key capabilities:**
- Container log aggregation
- Distributed tracing
- Integration with Grafana data sources

---

### RBAC
Four-role permission system enforced at API (FastAPI middleware) and UI (React route guards) levels. SuperAdmin manages users and licenses. Admin manages monitoring features. Operator handles alerts and incidents. Viewer has read-only access the platform.

| Role | Users | Services | Alerts | Incidents | Settings |
|------|:-----:|:--------:|:------:|:---------:|:--------:|
| SuperAdmin | Manage | Manage | Full | Full | Full |
| Admin | View | Manage | Full | Full | Limited |
| Operator | View | View | Create | Manage | — |
| Viewer | — | View | View | View | — |

---

### Licensing
Hardware-fingerprinted license validation with three tiers. The License Server validates keys on startup and periodically. Feature availability is controlled by the active tier. The License UI provides a standalone interface for key entry and status display.

---

## Module Interaction Map

```
Services ──▶ AI Anomaly ──▶ AI Insights
                │
                ├──▶ Alert Rules ──▶ Alerts ──▶ Notifications
                │                       │
                │                       ▼
                │              Incident Management ──▶ Root Cause
                │
                ├──▶ Correlation Engine
                │         │
                │         ├── Logs (Loki)
                │         └── Traces (Jaeger)
                │
                └──▶ Service Map
                          │
                          └──▶ Root Cause

SLO/SLA ◀── Services + Alert Rules
RBAC ──▶ All modules (permission enforcement)
Licensing ──▶ All modules (feature gating)
```

---

*Copyright 2024–2026 Rhinometric. All rights reserved.*
