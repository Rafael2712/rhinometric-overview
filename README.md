> **[English]** | [Español](README_ES.md)

# Rhinometric

**Service-Centric Observability Platform**

[![Version](https://img.shields.io/badge/version-2.7.0-blue.svg)]()
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)]()

---

## What is Rhinometric?

Rhinometric is a **service-centric observability platform** that organizes all operational data — metrics, logs, and AI-driven anomaly detection — around **monitored services** as the primary entity. It is designed for infrastructure and DevOps teams that need to monitor services, detect issues before they cause outages, and manage incidents with full lifecycle support.

Unlike traditional monitoring tools that rely exclusively on static thresholds, Rhinometric adds an AI anomaly detection layer that automatically identifies abnormal behavior across all monitored services — without requiring manual rule configuration for every metric.

The platform's commercial model is based on the number of **monitored services**, with three license tiers offering progressively more capabilities.

---

## Core Capabilities

### Service Monitoring
Register and monitor services with periodic health checks. View real-time status, historical availability, and detailed metrics through integrated Grafana dashboards. Services are the central entity around which all platform modules are organized.

### AI Anomaly Detection
A dedicated anomaly detection engine analyzes metric time-series data and identifies statistical anomalies using IsolationForest, LOF, and MAD-based models. Related deviations are grouped by service and time window. A 30% MAD threshold guard filters noise to reduce false positives.

### AI Insights
Natural-language summaries explain detected anomalies in plain terms — describing what changed, by how much, and potential impact — so operators can understand issues without manual metric analysis.

### Alert Rules & Alerting
Define alert rules based on thresholds, anomaly severity, or metric absence. Alerts fire when conditions are met and follow a lifecycle (firing → acknowledged → resolved) with configurable notification channels.

### Incident Management
Full lifecycle incident management with state machine (open → acknowledged → investigating → resolved → closed), timeline, comments, tags, linked alerts, and assigned owners.

### Root Cause Analysis
When incidents are created from anomaly alerts, the platform traverses the service dependency graph to identify and rank the most likely origin of the failure.

### Service Map
Live dependency graph showing service interconnections, health status, and anomaly propagation paths.

### SLO/SLA Tracking
Define Service Level Objectives with error-budget tracking and alert on budget exhaustion before SLA breaches occur.

### Correlation Engine
Cross-signal analysis linking metrics and logs (and optionally traces, when available) to anomaly events for context enrichment.

### Notification Pipeline
Slack and email notifications with configurable channels, cooldown periods, resolve timeouts, and severity-appropriate templates.

### Centralized Logs
Log aggregation via Loki/Promtail integrated into anomaly and incident views.

### Distributed Tracing (Available)
Jaeger/OpenTelemetry tracing infrastructure is deployed and ready. Trace data collection requires applications to be instrumented with OpenTelemetry SDKs. For most deployments, metrics and logs provide the primary observability signals.

### Role-Based Access Control
Four-role permission system (Owner, Admin, Operator, Viewer) enforced at both API and UI levels.

### Licensing
Service-based license tiers: Community, Professional, Enterprise. Each tier defines the maximum number of monitored services and available features.

---

## Architecture Overview

Rhinometric runs as a containerized stack of 21 Docker services:

```
┌─────────────────────────────────────────────────────┐
│                      NGINX                          │
│              (Reverse Proxy + SSL)                  │
├───────────────────────┬─────────────────────────────┤
│     Frontend          │         Backend API         │
│  React 18 + Vite      │      FastAPI (Python)       │
├───────────────────────┴─────────────────────────────┤
│                  Data Layer                          │
│  PostgreSQL │ Redis │ VictoriaMetrics │ Prometheus   │
├─────────────────────────────────────────────────────┤
│             Observability & Intelligence            │
│  Loki │ Grafana │ Alertmanager │ Promtail           │
│  Anomaly Detection Engine │ License Server          │
├─────────────────────────────────────────────────────┤
│          Available Capabilities                     │
│  Jaeger │ OTel Collector (tracing)                  │
├─────────────────────────────────────────────────────┤
│               Infrastructure Exporters              │
│  Node Exporter │ cAdvisor │ Postgres Exporter       │
│  Redis Exporter │ Blackbox Exporter                 │
└─────────────────────────────────────────────────────┘
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, TanStack Query, Zustand |
| Backend | Python 3.11, FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL 16, Redis 7 |
| Metrics | Prometheus, VictoriaMetrics |
| Logs | Loki, Promtail |
| Visualization | Grafana |
| Anomaly Detection | IsolationForest, LOF, MAD — dedicated detection engine |
| Alerting | Alertmanager, custom notification pipeline |
| Tracing (available) | Jaeger, OpenTelemetry Collector |
| Proxy | Nginx |
| Deployment | Docker Compose |

---

## Deployment Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 16 GB | 32 GB |
| Storage | 100 GB SSD | 250 GB SSD |
| OS | Ubuntu 22.04+ / Rocky Linux 8+ | Ubuntu 24.04 |
| Docker | 24.0+ | Latest stable |
| Docker Compose | v2.20+ | Latest stable |

---

## License Tiers

| Feature | Community | Professional | Enterprise |
|---------|:---------:|:------------:|:----------:|
| Monitored Services | Up to 10 | Up to 50 | Unlimited |
| Health Dashboards | ✓ | ✓ | ✓ |
| AI Anomaly Detection | — | ✓ | ✓ |
| AI Insights | — | ✓ | ✓ |
| Alert Rules | Basic | Full | Full |
| Incident Management | — | ✓ | ✓ |
| Root Cause Analysis | — | — | ✓ |
| Service Map | — | ✓ | ✓ |
| SLO/SLA | — | — | ✓ |
| Correlation Engine | — | ✓ | ✓ |
| RBAC | 2 roles | 3 roles | 4 roles |
| Notification Channels | Email | Email + Slack | All |
| Support | Community | Email | Priority |

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](ARCHITECTURE.md) | Detailed architecture with data flow diagrams |
| [Modules](MODULES.md) | Feature matrix and module descriptions |
| [Release Notes](RELEASE_NOTES.md) | Version history and changes |
| [Roadmap](ROADMAP.md) | Public roadmap and upcoming features |

---

## Contact

**Rhinometric Team**
Website: [rhinometric.com](https://rhinometric.com)
Email: info@rhinometric.com

---

*Copyright 2024–2026 Rhinometric. All rights reserved.*
