# Rhinometric Platform — Functional Overview

**Version:** 2.7.0
**Date:** March 2026
**Classification:** Internal — Confidential
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## 1. Executive Summary

Rhinometric is a **service-centric observability platform**. Unlike traditional monitoring tools that focus on infrastructure metrics or host-level data, Rhinometric organizes all telemetry — metrics, logs, and anomaly signals — around **monitored services** as the primary entity.

The platform provides a complete operational intelligence pipeline:

**Services → Health Checks → Anomaly Detection → Alerts → Incidents → Root Cause Analysis → Service Map → SLO Tracking**

Every module feeds into this pipeline, creating a unified operational picture from raw metrics to business-level SLA compliance. The commercial model is based on the number of **monitored services**, not hosts or infrastructure nodes.

---

## 2. Platform Modules

### 2.1 Service Monitoring

**Purpose:** Central registry of all monitored services with automated health checking. Services are the primary entity around which the entire platform is organized.

**What it does:**
- Maintains an inventory of external services (APIs, databases, websites)
- Performs periodic HTTP/TCP/PostgreSQL health checks
- Calculates health scores (0–100) based on availability, latency, and error rates
- Classifies services into groups: `apis`, `databases`, `websites`, `storage`
- Supports multiple environments: `production`, `staging`, `development`

**What it does NOT do:**
- Auto-discovery of services (services must be manually registered)
- APM-level code instrumentation
- Custom protocol checks beyond HTTP/TCP/PostgreSQL

**Inputs:** Service definitions (URL, type, check interval, expected response)
**Outputs:** Health scores, availability percentages, latency metrics, status (up/down/degraded)

**Dependencies:** PostgreSQL (service definitions), Prometheus (metrics export), Health Checker service

**Limitations:**
- Currently optimized for 10–30 services; UI needs redesign for 100+ services
- No bulk import/export of service definitions

---

### 2.2 AI Anomaly Detection

**Purpose:** Automatic detection of statistical anomalies across all monitored metrics using machine learning models.

**What it does:**
- Runs a detection cycle every 5 minutes (configurable)
- Analyzes infrastructure metrics (CPU, memory, disk, network) and service metrics (latency, health, availability)
- Uses multiple detection models: **Isolation Forest**, **Local Outlier Factor (LOF)**, and **Statistical (MAD-based modified Z-score)**
- Groups anomalies by fingerprint (metric + entity) with occurrence history
- Calculates deviation percentage, confidence scores, and severity levels
- Supports lifecycle management: `active` → `acknowledged` → `resolved`
- Applies a 30% minimum deviation guard to prevent trivially small anomalies from tight distributions

**What it does NOT do:**
- Does not use deep learning (LSTM is not currently deployed)
- Does not perform root cause analysis (that's a separate module)
- Does not generate predictions or forecasts

**Inputs:** Prometheus/VictoriaMetrics time-series data, service health metrics
**Outputs:** Anomaly groups with fingerprints, severity, deviation %, occurrence history

**Dependencies:** Anomaly detection engine (dedicated container), VictoriaMetrics, Backend API

**Limitations:**
- Detection models require a minimum of data points (configurable window, default 28 samples)
- The anomaly detection engine runs as a dedicated container; source code is not distributed with the deployment

---

### 2.3 AI Insights

**Purpose:** Natural-language analysis of anomaly groups providing expert-level interpretation.

**What it does:**
- Provides contextual analysis for each anomaly detection
- Generates human-readable explanations of what the anomaly means
- Calculates expected ranges and deviation context
- Presents trend information alongside raw numbers

**What it does NOT do:**
- Does not use LLM/GPT models
- Does not provide remediation suggestions (planned for future)
- Analysis is deterministic, not generative

**Inputs:** Anomaly groups, metric metadata, historical baselines

**Outputs:** Analysis strings with current value, expected range, deviation context

**Dependencies:** AI Anomaly Detection module

---

### 2.4 Alert Rules Management

**Purpose:** Define and manage alerting rules for proactive notification.

**What it does:**
- CRUD interface for alert rules
- Supports Prometheus-style PromQL expressions
- Configurable severity levels: `critical`, `warning`, `info`
- Duration thresholds (how long a condition must persist before firing)
- Labels and annotations for contextual information
- Rules are synced to Alertmanager for evaluation

**What it does NOT do:**
- Does not support complex boolean logic across multiple rules (single expression per rule)
- Does not provide a visual rule builder (PromQL text input only)

**Inputs:** PromQL expression, severity, duration, labels
**Outputs:** Alert rule definitions stored in PostgreSQL and synced to Alertmanager

**Dependencies:** Alertmanager, Prometheus

---

### 2.5 Alerts & Alert History

**Purpose:** Real-time active alert display and historical alert tracking.

**What it does:**
- Shows all currently firing alerts from Alertmanager
- Provides alert history with firing/resolved transitions
- Alert acknowledgement workflow
- Severity-based filtering and sorting
- Alert correlation with anomaly fingerprints
- Historical alert search with time range filtering

**What it does NOT do:**
- Does not aggregate alerts across multiple Alertmanager instances
- Does not support alert silencing from the UI (must use Alertmanager directly)

**Inputs:** Alertmanager API, alert webhook events
**Outputs:** Active alert list, alert history records with timestamps

**Dependencies:** Alertmanager, PostgreSQL (alert history)

---

### 2.6 Incident Management

**Purpose:** Structured incident lifecycle from detection to resolution.

**What it does:**
- Automatic incident creation from alert webhooks (find-or-create pattern with race condition protection)
- Incident lifecycle: `open` → `acknowledged` → `investigating` → `resolved` → `closed`
- Severity classification: `critical`, `high`, `medium`, `low`
- Incident timeline with automatic event logging
- User comments on incidents
- Tag system for categorization
- Deduplication via `incident_key` (prevents duplicate incidents for the same alert)

**What it does NOT do:**
- Does not support on-call rotation or escalation policies
- Does not integrate with PagerDuty or OpsGenie (planned)
- No automated runbook execution

**Inputs:** Alert webhooks, user actions
**Outputs:** Incident records with timeline, comments, tags, status transitions

**Dependencies:** Alertmanager webhook, PostgreSQL

---

### 2.7 Root Cause Analysis Engine

**Purpose:** Automated analysis of correlated signals to suggest probable root causes.

**What it does:**
- Analyzes infrastructure metrics, service health, and anomaly data
- Identifies temporal correlations between events
- Generates root cause hypotheses with confidence levels
- Provides timeline of contributing factors
- Uses correlation engine data to enrich analysis

**What it does NOT do:**
- Does not guarantee accuracy (hypotheses are probabilistic)
- Does not execute remediation actions
- Not a substitute for human investigation

**Inputs:** Anomaly fingerprint, correlated metrics, alert history

**Outputs:** Root cause hypotheses, contributing factors, confidence scores

**Dependencies:** Correlation Engine, AI Anomaly Detection, Alert History

---

### 2.8 Service Map (Topology)

**Purpose:** Visual representation of service dependencies and their current state.

**What it does:**
- Displays service-to-service dependencies as a directed graph
- Shows real-time health status on each node
- Supports manual dependency definition
- Infrastructure and service nodes differentiated visually
- Click-through to service details

**What it does NOT do:**
- Does not auto-discover dependencies from traces (manual definition only)
- Does not show traffic flow or request volumes
- Does not support multiple topology views

**Inputs:** Service dependency definitions, real-time health data

**Outputs:** Interactive topology graph with health overlay

**Dependencies:** Service Monitoring, PostgreSQL (dependency definitions)

---

### 2.9 SLO/SLA Tracking

**Purpose:** Define and track Service Level Objectives and Agreements.

**What it does:**
- Define SLOs with target percentages (e.g., 99.9% availability)
- Track compliance over configurable windows (7d, 30d, 90d)
- Calculate remaining error budget
- Burn rate alerts when error budget is being consumed too fast
- Historical SLO compliance tracking

**What it does NOT do:**
- Does not integrate with external SLA contract management tools
- Does not support composite SLOs (single metric per SLO)
- No automatic SLO suggestion based on historical data

**Inputs:** SLO definition (metric, target, window), real-time metrics
**Outputs:** Compliance percentage, error budget remaining, burn rate

**Dependencies:** Prometheus/VictoriaMetrics, Service Monitoring

---

### 2.10 Notifications (Slack & Email)

**Purpose:** Multi-channel alert notification delivery.

**What it does:**
- Slack integration via webhook URLs
- Email integration via Zoho SMTP
- Per-alert-type notification templates (AI anomaly alerts, standard alerts)
- Email cooldown system: prevents duplicate emails for the same (metric, severity) within configurable time windows
- Deep links in notifications: direct links to Console anomaly views and Grafana dashboards
- Dynamic template rendering with metric-specific Grafana dashboard routing

**What it does NOT do:**
- Does not support PagerDuty, OpsGenie, Teams, or SMS (planned)
- Does not support per-user notification preferences
- No notification scheduling or quiet hours

**Inputs:** Alert webhook events from Alertmanager
**Outputs:** Formatted Slack messages, HTML emails with deep links

**Dependencies:** Alertmanager, Zoho SMTP, Slack webhook URL

**Limitations:**
- `resolve_timeout` set to 10m to prevent alert auto-expire before next detection cycle
- Cooldown is global (not per-recipient)

---

### 2.11 Correlation Engine

**Purpose:** Find relationships between anomalies and metrics across the platform.

**What it does:**
- Given an anomaly fingerprint, finds temporally correlated metrics
- Uses Pearson correlation on time-series data from VictoriaMetrics
- Ranks related anomalies by severity, status, and deviation
- Provides correlation timeline visualization
- Rich Related Anomalies panel with contextual ranking

**What it does NOT do:**
- Does not establish causal relationships (correlation only)
- Does not correlate across multiple time granularities simultaneously

**Inputs:** Anomaly fingerprint, time range
**Outputs:** Correlated metrics list, related anomaly groups, correlation scores

**Dependencies:** VictoriaMetrics, AI Anomaly Detection

---

### 2.12 Logs

**Purpose:** Centralized log querying and exploration.

**What it does:**
- LogQL query interface to Loki
- Time-range filtering
- Log stream browsing
- Label-based filtering
- Integration with Grafana log panels

**What it does NOT do:**
- Does not provide log-based alerting from the Console UI (use Grafana/Alertmanager)
- No log analytics or automatic pattern detection
- No log-to-trace correlation from the Console UI

**Inputs:** LogQL queries
**Outputs:** Log entries with timestamps, labels, and content

**Dependencies:** Loki, Promtail

---

### 2.13 Traces (Available Capability)

**Purpose:** Distributed trace exploration.

**Current State:** Traces are an **available capability** within the platform, not a primary pillar. The infrastructure (Jaeger + OTel Collector) is deployed and functional, but trace data collection requires applications to be instrumented with OpenTelemetry SDKs. Currently, only the Rhinometric backend itself emits traces. For most deployments, metrics and logs provide the primary observability signals.

**What it does:**
- Search traces by service, operation, duration, and time range
- View trace detail with span waterfall
- Jaeger backend integration

**What it does NOT do:**
- No automatic trace-to-log correlation
- No trace-to-metric correlation
- No service dependency inference from traces

**Inputs:** Trace search parameters
**Outputs:** Trace list, span detail view

**Dependencies:** Jaeger, OpenTelemetry Collector

---

### 2.14 RBAC (Role-Based Access Control)

**Purpose:** User management with role-based permissions.

**What it does:**
- Four roles: `OWNER`, `ADMIN`, `OPERATOR`, `VIEWER`
- User CRUD operations
- Password management with forced change on first login
- JWT-based authentication with 24-hour token expiry
- Session persistence via Zustand + localStorage
- 401 detection with automatic redirect to login

**What it does NOT do:**
- No LDAP/Active Directory integration (planned)
- No SSO/SAML/OAuth (planned)
- No fine-grained resource-level permissions (role-based only)

**Inputs:** User credentials
**Outputs:** JWT token, user profile with roles

**Dependencies:** PostgreSQL (user records)

---

### 2.15 Licensing

**Purpose:** Platform license management and validation.

**What it does:**
- License server (Python/FastAPI) with PostgreSQL backend
- License key validation (format: `RHINO-XXXX-XXXX-XXXX-XXXX`)
- Tier support: `starter`, `professional`, `enterprise`
- Feature gating based on tier
- **Service-based model:** Each tier defines the maximum number of monitored services (e.g., Community = 10, Professional = 50, Enterprise = unlimited)
- License UI for activation and status display
- Grace period handling for expired licenses

**Current State:** The license server is functional and deployed. License validation is integrated into the backend. Tiers currently control feature access and service count limits. The compiled Rust-based license validator with tamper resistance is planned for pre-production but not yet implemented.

**What it does NOT do:**
- No online activation (offline key-based only)
- No usage metering
- No floating/concurrent license models

**Inputs:** License key
**Outputs:** License status, tier, expiry date, enabled features, service count limit

**Dependencies:** License Server, PostgreSQL, Redis

---

## 3. Functional Data Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                  │
│  Infrastructure (node_exporter, cAdvisor, postgres_exporter)         │
│  Services (health_checker → HTTP/TCP/PG checks)                      │
│  Logs (Promtail → container logs)                                    │
│  Traces (OpenTelemetry SDK → optional, requires instrumentation)     │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      COLLECTION & STORAGE                            │
│  Prometheus ──► VictoriaMetrics (long-term metrics)                  │
│  Loki (logs)    Jaeger (traces, when available)    PostgreSQL (state)│
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      ANALYSIS ENGINES                                │
│  Anomaly Detection Engine ──► anomaly groups + fingerprints          │
│  Correlation Engine ──► related metrics + anomalies                  │
│  Root Cause Engine ──► hypotheses + contributing factors              │
│  Health Checker ──► service scores + availability                    │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      ALERTING PIPELINE                               │
│  Alertmanager ──► route + group ──► webhook ──► Backend              │
│  Backend ──► incident creation + email cooldown                      │
│  Backend ──► Slack webhook + Email (Zoho SMTP)                       │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      CONSOLE UI                                      │
│  Home Dashboard ── Services ── Anomalies ── Alerts ── Incidents      │
│  Service Map ── SLO/SLA ── Logs ── Traces ── Settings                │
│  AI Insights ── Correlation ── Root Cause ── Alert Rules             │
│  Users (RBAC) ── License ── Dashboards (Grafana embed)               │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Module Interaction Matrix

| Module | Feeds Into | Receives From |
|--------|-----------|---------------|
| Service Monitoring | Anomaly Detection, SLO, Service Map | Health Checker |
| AI Anomaly Detection | Alerts, Correlation, Root Cause | Prometheus, VictoriaMetrics |
| Alert Rules | Alertmanager | User-defined rules |
| Alerts | Incidents, Alert History, Notifications | Alertmanager |
| Incidents | — | Alerts (webhook) |
| Correlation | Root Cause, AI Insights | Anomaly Detection, VictoriaMetrics |
| Root Cause | — | Correlation, Anomaly Detection, Alerts |
| Service Map | — | Service Monitoring, Dependencies |
| SLO/SLA | — | Service Monitoring, Prometheus |
| Notifications | — | Alertmanager webhook |
| Logs | — | Loki (Promtail) |
| Traces (available) | — | Jaeger (OTel Collector, when instrumented) |

---

## 5. Known Limitations (Current State)

1. **Service scaling:** UI optimized for <30 services; needs redesign for 100+ services
2. **Trace coverage:** Only backend self-traces; full coverage requires application instrumentation with OpenTelemetry SDKs
3. **License enforcement:** Key-based validation with service-count limits works; compiled Rust validator in development
4. **Installer:** Docker Compose based; Ansible-based enterprise installer not yet built
5. **External integrations:** Only Slack and Email; PagerDuty, Teams, OpsGenie planned
6. **No SSO/LDAP:** Authentication is local JWT only
7. **Single-node deployment:** No horizontal scaling or HA clustering
8. **Dashboard builder:** Relies on Grafana embed; native builder not yet implemented

---

*Document generated by Rhinometric Team — info@rhinometric.com*
*Last updated: March 2026*
