# Rhinometric On-Premise Quick Start Guide

Deploy Rhinometric on your own infrastructure in minutes.

## Prerequisites

| Requirement | Minimum |
|------------|---------|
| OS | Ubuntu 22.04+ / Debian 12+ |
| CPU | 4 cores |
| RAM | 8 GB |
| Disk | 50 GB SSD |
| Docker | 24.0+ with Compose v2 |
| Network | Outbound HTTPS (for Slack webhooks + SMTP) |

## Step 1: Clone and Configure

```bash
git clone https://github.com/Rafael2712/mi-proyecto.git /opt/rhinometric
cd /opt/rhinometric
cp .env.example .env  # Edit with your passwords
```

## Step 2: Start the Stack

```bash
docker compose up -d
```

Wait ~2 minutes for all 21 services to become healthy:

```bash
docker compose ps
```

## Step 3: Access the Console

Open your browser: `http://<YOUR_SERVER_IP>`

Default credentials:
- **Username:** `admin`
- **Password:** (set in `.env` as `RHINO_ADMIN_PASSWORD`)

## Step 4: Activate License

1. Navigate to **License** in the sidebar
2. Enter your license key
3. Click **Activate**

## Step 5: Configure Slack & Email Notifications

> **This step is required for alert notifications to work.**

1. Navigate to **Settings** in the sidebar
2. In **Notification Channels**:
   - **Slack**: Toggle on, paste your Slack webhook URL, click "Test"
   - **Email**: Toggle on, enter SMTP credentials, click "Test"
3. Click **"Save Notification Channels"**
4. Toggle **"Enable AI Alerting"** to ON

See [NOTIFICATIONS_SETUP.md](./NOTIFICATIONS_SETUP.md) for detailed instructions and troubleshooting.

## Step 6: Verify Everything Works

| Check | How |
|-------|-----|
| Dashboard loads | Visit Home page — cards show service count and anomalies |
| AI Detection runs | Visit AI Anomalies — should show detections after ~10 min |
| Slack works | Send test from Settings |
| Email works | Send test from Settings |
| Grafana dashboards | Visit Dashboards page |
| Logs flowing | Visit Logs page — should show recent entries |
| Traces | Visit Traces page — should show traces after first requests |

## Architecture Overview

```
Browser → Nginx (80/443) → Console Frontend (React)
                         → Console Backend (FastAPI) → PostgreSQL
                                                     → Prometheus / VictoriaMetrics
                                                     → AI Anomaly Engine → Alertmanager → Slack / Email
                                                     → Grafana
                                                     → Loki (logs)
                                                     → Jaeger (traces)
```

## Data Persistence

All data is stored in `~/rhinometric_data_v2.5/`:
- `console-backend/data/` — Settings, notification config
- `ai-anomaly/data/` — AI models, baselines, notification state
- `postgres/` — Users, roles, alert acknowledgements
- `prometheus/` — Metrics time-series data
- `grafana/` — Dashboard definitions
- `jaeger/` — Distributed trace data

## Updating

```bash
cd /opt/rhinometric
git pull origin main
docker compose build
docker compose up -d
```

## Support

- Documentation: See `docs/` folder
- Notifications: See [NOTIFICATIONS_SETUP.md](./NOTIFICATIONS_SETUP.md)
