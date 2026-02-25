# Rhinometric On-Premise — Quick Start Guide

> **Version:** 2.6.0 · **Last updated:** 2026-02-25

---

## Prerequisites

| Requirement     | Minimum            | Recommended         |
|-----------------|--------------------|---------------------|
| OS              | Ubuntu 22.04/24.04 | Ubuntu 24.04 LTS    |
| CPU             | 2 cores            | 4+ cores            |
| RAM             | 8 GB               | 16+ GB              |
| Disk            | 50 GB free         | 150+ GB free        |
| Docker          | 24+                | 28+                 |
| Docker Compose  | v2.20+             | v2.24+              |
| Ports           | 80, 3000, 3100, 5432, 6379, 8105, 9090, 9093, 16686 |

**No Docker?** Install with one command:
```bash
curl -fsSL https://get.docker.com | sh
```

---

## 1. Install (One Command)

```bash
# Interactive install (prompts for edition + domain)
sudo bash scripts/install-rhinometric.sh

# OR non-interactive install
sudo bash scripts/install-rhinometric.sh --non-interactive --edition trial

# Dry-run first (validates system, no changes)
sudo bash scripts/install-rhinometric.sh --dry-run
```

### Installer Options

| Flag                | Description                                  |
|---------------------|----------------------------------------------|
| `--edition TYPE`    | `trial` (30 days) or `annual`                |
| `--install-dir DIR` | Install directory (default: `/opt/rhinometric`) |
| `--license-file F`  | Pre-apply a license file during install      |
| `--non-interactive` | Skip all prompts (requires `--edition`)      |
| `--dry-run`         | Validate only, no changes                    |
| `--skip-build`      | Skip Docker image builds                     |
| `--domain DOMAIN`   | Public domain or IP                          |
| `--admin-email E`   | Admin email for alerts                       |

---

## 2. Generate Hardware Fingerprint

After installation, generate the hardware ID needed for licensing:

```bash
rhinoctl fingerprint
```

Output:
```
  HWID: A1B2C3D4E5F6G7H8

  Send this HWID to: licenses@rhinometric.com
```

---

## 3. Apply License

Once you receive your license file:

```bash
rhinoctl apply-license /path/to/license.lic
```

> **Trial installs** work for 30 days without a license file.

---

## 4. Verify Installation

```bash
# Platform status
rhinoctl status

# Endpoint health checks
rhinoctl health
```

Expected output:
```
  ✓ Console Backend     200
  ✓ Prometheus          200
  ✓ Loki Ready          200
  ✓ Alertmanager        200
  ✓ Grafana             200
  ✓ Frontend            200

  All 6 endpoints healthy
```

---

## 5. Access the Platform

| Service         | URL                       | Default Credentials      |
|-----------------|---------------------------|--------------------------|
| Console         | `http://<IP>`             | See `CREDENTIALS.txt`    |
| Grafana         | `http://<IP>:3000`        | See `CREDENTIALS.txt`    |
| Prometheus      | `http://<IP>:9090`        | No auth                  |
| Alertmanager    | `http://<IP>:9093`        | No auth                  |
| Jaeger (traces) | `http://<IP>:16686`       | No auth                  |

Credentials were saved during installation:
```bash
cat /opt/rhinometric/CREDENTIALS.txt
```

> ⚠️ Save credentials to a password manager and delete the file.

---

## Management Commands

```bash
rhinoctl start              # Start platform
rhinoctl stop               # Stop platform
rhinoctl restart            # Restart all services
rhinoctl status             # Show status summary
rhinoctl health             # Check endpoint health
rhinoctl logs               # Follow all logs
rhinoctl logs grafana 50    # Last 50 lines of grafana
rhinoctl backup             # Full backup (tar.gz)
rhinoctl update             # Pull + rebuild + restart
rhinoctl version            # Show version
```

---

## Troubleshooting

### Container not starting

```bash
# Check specific service logs
rhinoctl logs <service-name> 200

# List all containers with status
cd /opt/rhinometric && docker compose ps
```

### Port conflict

```bash
# Find what's using a port
ss -tlnp | grep :<PORT>
```

### Re-run installer (idempotent)

The installer detects existing installations and offers:
- **Update** — keep `.env` and data, update configs
- **Fresh** — backup existing, clean install

```bash
sudo bash scripts/install-rhinometric.sh
```

### Reset credentials

```bash
cd /opt/rhinometric
# Edit .env with new passwords
nano .env
# Restart to apply
rhinoctl restart
```

---

## Architecture Overview

The platform runs **20 containers** orchestrated via Docker Compose:

```
┌─────────────────────────────────────────────────┐
│                    NGINX (80)                    │
│           Reverse proxy / TLS termination        │
├──────────────┬──────────────┬───────────────────┤
│  Console     │  Console     │  AI Anomaly       │
│  Frontend    │  Backend     │  Detection        │
│  (React)     │  (Node.js)   │  (Python)         │
├──────────────┴──────────────┴───────────────────┤
│                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │PostgreSQL│ │  Redis   │ │ License Server   │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │Prometheus│ │  Loki    │ │  Jaeger  │        │
│  │  (9090)  │ │  (3100)  │ │ (16686)  │        │
│  └──────────┘ └──────────┘ └──────────┘        │
│                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Grafana  │ │Alertmgr  │ │VictoriaMetrics   │ │
│  │  (3000)  │ │  (9093)  │ │(long-term store) │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│                                                   │
│  Exporters: node, cadvisor, blackbox, postgres,  │
│             redis, promtail, otel-collector       │
└─────────────────────────────────────────────────┘
```

---

## Data Directories

All persistent data is stored at `~/rhinometric_data_v2.5/`:

```
rhinometric_data_v2.5/
├── postgres/           # Database
├── redis/              # Cache
├── loki/               # Log storage
├── jaeger/             # Trace storage
├── alertmanager/       # Alert state
├── ai-anomaly/         # ML models + data
│   ├── models/
│   └── data/
├── console-backend/    # App logs + data
│   ├── logs/
│   └── data/
└── license-server/     # License logs
    └── logs/
```

---

## Support

- **Email:** support@rhinometric.com
- **License requests:** licenses@rhinometric.com
- **Documentation:** https://docs.rhinometric.com
