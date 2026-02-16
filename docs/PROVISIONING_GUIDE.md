# Rhinometric — Provisioning Guide

## Overview

This document describes how to provision a new Rhinometric SaaS single-tenant instance
for a customer using the automated `provision-customer.sh` script.

**Architecture:** Each customer gets a dedicated VM cloned from the master snapshot.
The provisioning script configures all services for the specific customer.

**Platform version:** v2.5.1-hardened  
**Script version:** provision-customer.sh v2.5.1

---

## Prerequisites

1. **Clone the VM snapshot** → new Hetzner server
2. **SSH into the new VM** as root
3. **Verify Docker is running:** `docker ps` should show no containers (fresh clone)
4. **Verify files exist:**
   ```
   /opt/rhinometric/provision-customer.sh        # Provisioning script
   /opt/rhinometric/templates/                    # Template files
   /opt/rhinometric/config/customer.env.template  # Customer config template
   ```

---

## Step-by-Step Provisioning

### 1. Prepare Customer Configuration

```bash
# Copy the template
cp /opt/rhinometric/templates/customer.env.template /opt/rhinometric/config/customer.env

# Edit with customer data
nano /opt/rhinometric/config/customer.env
```

**Required fields** (script will fail if any are empty):

| Field | Description | Example |
|-------|-------------|---------|
| `CUSTOMER_NAME` | Company name (quote if spaces) | `"ACME Corp"` |
| `CUSTOMER_ID` | Unique identifier | `acme-001` |
| `CUSTOMER_DOMAIN` | Console domain | `console.acme-corp.com` |
| `CUSTOMER_PUBLIC_IP` | VM public IP | `10.0.0.100` |
| `CUSTOMER_SMTP_HOST` | SMTP server | `smtp.zoho.eu` |
| `CUSTOMER_SMTP_PORT` | SMTP port | `587` |
| `CUSTOMER_SMTP_USER` | SMTP username | `alerts@acme.com` |
| `CUSTOMER_SMTP_PASSWORD` | SMTP password | `secretpass` |
| `CUSTOMER_SMTP_FROM` | Sender email | `noreply@acme.com` |
| `CUSTOMER_ALERT_EMAIL` | Alert recipient | `ops@acme.com` |

**Optional fields:**

| Field | Default | Description |
|-------|---------|-------------|
| `CUSTOMER_TIMEZONE` | `Europe/Madrid` | Timezone |
| `CUSTOMER_LICENSE_TIER` | `essentials` | `essentials`, `growth`, or `enterprise` |
| `CUSTOMER_SLACK_WEBHOOK` | *(empty)* | Slack incoming webhook URL |
| `CUSTOMER_SLACK_CHANNEL_*` | `#monitoring-*` | Slack channel names |
| `CUSTOMER_SSL_ENABLED` | `false` | Enable HTTPS |
| `CUSTOMER_WEBSITE_URL` | *(empty)* | URL to monitor with blackbox-exporter |
| `CUSTOMER_WEBSITE_MONITORING` | `false` | Enable website monitoring metrics |
| `CUSTOMER_ADMIN_PASSWORD` | *(auto-generated)* | Console admin password |

### 2. Run Provisioning (Dry-Run First)

```bash
cd /opt/rhinometric

# Dry-run: generates configs without deploying
./provision-customer.sh cliente-acme --dry-run

# Review generated files:
#   .env.new
#   nginx/nginx.conf.new
#   alertmanager/alertmanager.yml.new
#   rhinometric-ai-anomaly/config.yaml.new
#   docker-compose-v2.5.1-cliente-acme.yml
```

### 3. Run Full Provisioning

```bash
./provision-customer.sh cliente-acme
```

The script will:
1. **Validate** customer.env (all required fields present)
2. **Generate** unique passwords (Postgres, Redis, Grafana, SecretKey, Admin)
3. **Process** templates → final config files
4. **Create** tenant record at `/opt/rhinometric/tenants/cliente-acme/`
5. **Activate** configs (move `.new` → live, update compose symlink)
6. **Deploy** stack (`docker-compose down` + `docker-compose up -d --force-recreate`)
7. **Healthcheck** (nginx, backend, Grafana — up to 6 retries)
8. **Generate** provision report at `/opt/rhinometric/audits/PROVISION_*.md`

### 4. Post-Provisioning

1. **Configure DNS:** Point `CUSTOMER_DOMAIN` → `CUSTOMER_PUBLIC_IP`
2. **Test access:** `http://<IP>/` → Console login
3. **Review credentials:** `cat /opt/rhinometric/tenants/<TENANT_ID>/credentials.env`
4. **Verify Grafana:** `http://<IP>/grafana/`
5. **Test alerts:** Trigger a test alert to verify email/Slack delivery

---

## Directory Structure

### Templates (read-only, do not modify on customer VMs)
```
/opt/rhinometric/templates/
├── customer.env.template              # Customer config template
├── env.template                       # Docker .env template
├── nginx.conf.template               # Nginx reverse proxy template
├── alertmanager.yml.template         # Alertmanager template
├── ai-anomaly-config.yaml.template   # AI anomaly detector template
├── website-monitoring.block          # Website monitoring metrics block
└── website-monitoring-disabled.block # Disabled website monitoring placeholder
```

### Tenant Record (per customer)
```
/opt/rhinometric/tenants/<TENANT_ID>/
├── customer.env                    # Customer config (source of truth)
├── credentials.env                 # Auto-generated passwords (chmod 600)
├── metadata.json                   # Tenant metadata (JSON)
├── env.snapshot                    # Generated .env copy
├── nginx.conf.snapshot             # Generated nginx.conf copy
├── alertmanager.yml.snapshot       # Generated alertmanager.yml copy
├── ai-anomaly-config.yaml.snapshot # Generated AI config copy
├── docker-compose.yml.snapshot     # Generated compose copy
└── backup_pre_provision/           # Pre-provision config backups
    ├── .env.bak
    ├── nginx.conf.bak
    ├── alertmanager.yml.bak
    └── ai-anomaly-config.yaml.bak
```

---

## What Gets Modified

The script modifies **only** these files on the target VM:

| File | What Changes |
|------|-------------|
| `.env` | Unique passwords (Postgres, Redis, Grafana, SecretKey) + SMTP credentials |
| `nginx/nginx.conf` | `server_name` → customer domain |
| `alertmanager/alertmanager.yml` | SMTP config, Slack webhook, alert email recipients |
| `rhinometric-ai-anomaly/config.yaml` | CORS origins, website monitoring URLs |
| `docker-compose.yml` | Symlink → `docker-compose-v2.5.1-<TENANT_ID>.yml` |
| `docker-compose-v2.5.1-<TENANT_ID>.yml` | CORS_ORIGINS, GF_SERVER_ROOT_URL, GF_SERVER_DOMAIN, GRAFANA_URL, SECRET_KEY, SMTP |

The script **never** modifies:
- `audits/FASE1_*.md`
- `docs/SAAS_SINGLE_TENANT_BASELINE.md`
- Source code (`rhinometric-console/`, `license-server-v2/`, etc.)
- Prometheus/Loki/Grafana provisioning configs
- Docker images (uses pre-built images from snapshot)

---

## Security Notes

- All passwords are generated using `openssl rand -base64 32`
- `credentials.env` is created with `chmod 600` (root-only readable)
- Original configs are backed up before replacement
- SECRET_KEY is unique per tenant (48 chars)
- ADMIN_PASSWORD is auto-generated (16 chars) unless customer provides one

---

## Re-Provisioning

To re-provision an existing tenant (e.g., after changing SMTP settings):

1. Edit `/opt/rhinometric/config/customer.env`
2. Run `./provision-customer.sh <TENANT_ID>`
3. The script will detect the existing tenant directory and back up previous config

> **Warning:** Re-provisioning generates NEW passwords. The old credentials become invalid.
> Save the new credentials from the provision report.

---

## Troubleshooting

### Script fails at "Required field empty"
→ Edit `customer.env` and fill all required fields

### Healthchecks fail
→ Check container logs: `docker-compose logs --tail=50 <service>`
→ Common causes: port conflicts, DNS not configured, build errors

### "Template missing" error
→ Ensure `/opt/rhinometric/templates/` directory has all template files
→ Re-run the template generator if needed

### Containers crash-loop
→ Check `.env` for valid passwords (no special characters that break YAML)
→ Verify `docker-compose-v2.5.1-<TENANT_ID>.yml` is valid: `docker-compose config`

---

## License Tiers

| Tier | Max Hosts | Data Retention | AI Anomaly | Website Monitoring |
|------|-----------|----------------|------------|-------------------|
| **essentials** | 1–20 | 7 days (168h) | Basic | Optional |
| **growth** | 21–70 | 30 days (720h) | Full | Included |
| **enterprise** | 71+ | 90 days (2160h) | Full + Custom | Included |

> Note: License tier enforcement will be implemented in Fase 2.C

---

*Last updated: 2026-02-13 — provision-customer.sh v2.5.1*
