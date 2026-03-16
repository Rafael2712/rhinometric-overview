# Rhinometric Console — Private Repository

**Version:** 2.7.0
**Maintained by:** Rhinometric Team
**Contact:** info@rhinometric.com

---

## Overview

This is the private monorepo for the **Rhinometric Console** — the central management interface of the Rhinometric Observability Platform. It contains the full-stack application (backend + frontend), configuration for all infrastructure services, and deployment tooling.

Rhinometric is a **service-centric observability platform**. Every module — anomalies, alerts, incidents, SLOs, root cause analysis — is organized around **monitored services** as the primary entity. The platform combines automated anomaly detection, structured incident management, and operational intelligence to help teams detect and resolve issues before they impact users.

## Repository Structure

```
rhinometric-console/
├── backend/                  # FastAPI backend (Python 3.11)
│   ├── routers/              # API route handlers
│   ├── services/             # Business logic & engines
│   ├── models/               # SQLAlchemy ORM models
│   ├── config.py             # Application configuration
│   ├── database.py           # Database connection
│   └── main.py               # Application entrypoint
├── frontend/                 # React frontend (TypeScript + Vite)
│   ├── src/pages/            # Page components
│   ├── src/components/       # Shared components
│   └── src/lib/              # Auth, API, utilities
├── alertmanager/             # Alertmanager config & templates
├── nginx/                    # Reverse proxy configuration
├── dist/                     # Installer scripts
├── docs/                     # Technical & functional documentation
│   ├── modules/              # Per-module documentation
│   ├── FUNCTIONAL_PLATFORM_OVERVIEW.md
│   ├── TECHNICAL_PLATFORM_OVERVIEW.md
│   └── PREPRODUCTION_ROADMAP.md
├── docker-compose.yml        # Full platform orchestration
└── CHANGELOG.md              # Release history
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | FastAPI (Python 3.11) | API Gateway, business logic |
| Frontend | React 18 + TypeScript + Vite | Console UI |
| Database | PostgreSQL 16 | Persistent storage |
| Cache | Redis 7 | Session cache, rate limiting |
| Metrics | Prometheus + VictoriaMetrics | Time-series storage |
| Logs | Loki + Promtail | Log aggregation |
| Dashboards | Grafana 10 | Visualization |
| Alerts | Alertmanager 0.27 | Alert routing & grouping |
| Proxy | Nginx | Reverse proxy, TLS termination |
| Anomaly Detection | Dedicated detection engine | IsolationForest, LOF, Statistical (MAD) |
| Tracing (available) | Jaeger + OpenTelemetry | Distributed tracing (requires app instrumentation) |

## Quick Start (Development)

```bash
# Clone
git clone git@github.com:Rafael2712/mi-proyecto.git
cd mi-proyecto

# Copy environment
cp .env.example .env
# Edit .env with your credentials (database, SMTP, JWT secret, default admin password)

# Start all services
docker compose up -d

# Access
# Console:     http://localhost (credentials configured in .env)
# Grafana:     http://localhost/grafana/
# Backend API: http://localhost/api/
```

## Documentation

| Document | Description |
|----------|-------------|
| [Functional Overview](docs/FUNCTIONAL_PLATFORM_OVERVIEW.md) | Complete functional description of every module |
| [Technical Overview](docs/TECHNICAL_PLATFORM_OVERVIEW.md) | Architecture, services, data flows, endpoints |
| [Pre-production Roadmap](docs/PREPRODUCTION_ROADMAP.md) | Pending items before market release |
| [Changelog](CHANGELOG.md) | Version history and release notes |
| [Module Docs](docs/modules/) | Per-module functional + technical docs |

## Branching Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable production-ready code |
| `staging` | Pre-release validation |
| `feature/*` | Feature development |
| `fix/*` | Bug fixes |
| `docs/*` | Documentation updates |

## Deployment

The platform is deployed via Docker Compose on a single node. See `docker-compose.yml` for the full service definition (21 containers).

```bash
# Production deployment
docker compose up -d

# Rebuild specific service
docker compose build --no-cache rhinometric-console-backend
docker compose up -d rhinometric-console-backend

# View logs
docker logs rhinometric-console-backend --tail 100 -f
```

## API Endpoints

The backend exposes all APIs under `/api/`. Key routes:

| Route | Description |
|-------|-------------|
| `/api/auth/login` | Authentication (JWT) |
| `/api/auth/me` | Current user profile |
| `/api/anomalies` | AI anomaly groups & detections |
| `/api/alerts` | Current active alerts |
| `/api/alert-rules` | Alert rule management |
| `/api/alert-history` | Historical alert records |
| `/api/incidents` | Incident lifecycle management |
| `/api/external-services` | Service inventory & monitoring |
| `/api/correlation/{anomaly_group_id}` | Anomaly correlation engine |
| `/api/service-map` | Service topology & dependencies |
| `/api/slo` | SLO/SLA definitions & compliance |
| `/api/logs` | Log query interface |
| `/api/traces` | Trace search & detail |
| `/api/users` | User management (RBAC) |
| `/api/settings` | Platform configuration |
| `/api/license` | License status & validation |
| `/api/system/health` | System health & metrics |

## License

Proprietary — Rhinometric. All rights reserved.

---

*Rhinometric Console — Service-Centric Observability Platform*
*info@rhinometric.com — https://rhinometric.com*
