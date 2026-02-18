# Rhinometric Console v2.6 ??? Installation, License Generator & Usability Design Document

> **Date**: 2026-02-18  
> **Author**: DevOps/SRE Team (automated planning session)  
> **Status**: DRAFT ??? Ready for implementation  
> **Based on**: Live audit of `rhinometric-prod` (89.167.22.228), Hetzner Helsinki

---

## Table of Contents

1. [Part 1 ??? Installation Smoke Test: Clean Hetzner VM](#part-1--installation-smoke-test-clean-hetzner-vm)
2. [Part 2 ??? Minimal Install Scripts & Documentation](#part-2--minimal-install-scripts--documentation)
3. [Part 3 ??? Minimal Rust License Generator (rhino-lic-gen) ??? Design Only](#part-3--minimal-rust-license-generator-rhino-lic-gen--design-only)
4. [Part 4 ??? First-Time Admin Usability Checklist](#part-4--first-time-admin-usability-checklist)

---

# PART 1 ??? Installation Smoke Test: Clean Hetzner VM

## 1.1 Test Objective

Simulate a **brand-new customer** receiving Rhinometric v2.6 and installing it on a fresh Hetzner cloud VM. The customer has:

- A fresh VM (no Docker, no prior config).
- SSH access as `root` (or non-root with sudo).
- A `rhinometric-release-v2.6.0.tar.gz` package (or Git tag).
- A signed `license.key` file provided by Rhinometric sales.

## 1.2 Canonical Test VM Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Cloud provider** | Hetzner Cloud | Region: Helsinki (eu-central or eu-north) |
| **VM type** | CPX31 or CX32 | 4 vCPUs, 8 GB RAM (minimum) |
| **Recommended** | CPX41 or CX42 | 8 vCPUs, 16 GB RAM (matches production) |
| **OS Image** | Ubuntu 22.04 LTS | Mandatory ??? scripts tested on this |
| **Disk** | ??? 160 GB SSD | Prometheus/VM retention needs ~80 GB headroom |
| **Public IPv4** | Yes | Auto-assigned by Hetzner |
| **Hostname** | `rhinometric-test` | Set via Hetzner panel |
| **Firewall (Hetzner)** | Allow inbound: 22/tcp, 80/tcp, 443/tcp | All other ports internal only |

### Required Open Ports (on the VM firewall / Hetzner FW)

| Port | Protocol | Service | Exposure |
|------|----------|---------|----------|
| **22** | TCP | SSH | Admin only |
| **80** | TCP | Nginx ??? Frontend, Grafana, API | Public |
| **443** | TCP | Nginx (HTTPS, when enabled) | Public (future) |

> **All other ports** (9090, 3000, 8428, 3100, 9093, 8085, 5000, 16686, etc.) are internal to the Docker bridge network (`172.25.0.0/16`) and **must NOT be exposed** to the internet. The current `docker-compose.yml` already binds VictoriaMetrics (`8428`) and Blackbox Exporter (`9115`) to `127.0.0.1` only, which is correct.

## 1.3 Step-by-Step Installation Flow

### Phase A ??? VM Preparation (5 min)

| # | Step | Command / Action | Pass Criteria |
|---|------|-----------------|---------------|
| A1 | SSH into the new VM | `ssh root@<VM_IP>` | Shell prompt appears |
| A2 | Update packages | `apt update && apt upgrade -y` | No errors |
| A3 | Set hostname | `hostnamectl set-hostname rhinometric-test` | `hostname` returns `rhinometric-test` |
| A4 | Set timezone | `timedatectl set-timezone Europe/Madrid` | (or customer TZ) |
| A5 | Verify OS version | `cat /etc/os-release` | `VERSION_ID="22.04"` |
| A6 | Verify resources | `nproc` ??? 4, `free -g` ??? 7 GB, `df -h /` ??? 150 GB | All pass |

### Phase B ??? Install Docker (3 min)

| # | Step | Command | Pass Criteria |
|---|------|---------|---------------|
| B1 | Install prerequisites | `apt install -y ca-certificates curl gnupg lsb-release` | No errors |
| B2 | Add Docker GPG key | `install -m 0755 -d /etc/apt/keyrings && curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc && chmod a+r /etc/apt/keyrings/docker.asc` | File exists |
| B3 | Add Docker repo | `echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list` | ??? |
| B4 | Install Docker Engine | `apt update && apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin` | No errors |
| B5 | Verify Docker | `docker --version` | `Docker version 28.x.x` or higher |
| B6 | Verify Compose | `docker compose version` | `Docker Compose version v2.x.x` |
| B7 | Enable Docker at boot | `systemctl enable docker` | ??? |

### Phase C ??? Deploy Rhinometric (10 min)

| # | Step | Command / Action | Pass Criteria |
|---|------|-----------------|---------------|
| C1 | Create install directory | `mkdir -p /opt/rhinometric` | Dir exists |
| C2 | Upload release package | `scp rhinometric-release-v2.6.0.tar.gz root@<VM_IP>:/opt/` | File transferred |
| C3 | Extract | `cd /opt && tar xzf rhinometric-release-v2.6.0.tar.gz -C /opt/rhinometric --strip-components=1` | Files in `/opt/rhinometric/` |
| C4 | Verify key files exist | `ls /opt/rhinometric/{docker-compose.yml,.env.template,start-rhinometric.sh,config/customer.env.template}` | All present |
| C5 | Create `.env` from template | `cp /opt/rhinometric/.env.template /opt/rhinometric/.env` | File exists |
| C6 | **Edit `.env`** ??? set passwords | Edit `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `GRAFANA_PASSWORD`, `SECRET_KEY`, `ADMIN_PASSWORD` | Strong random values (???20 chars) |
| C7 | Create `customer.env` | `cp /opt/rhinometric/config/customer.env.template /opt/rhinometric/config/customer.env` | File exists |
| C8 | **Edit `customer.env`** | Set `CUSTOMER_NAME`, `CUSTOMER_ID`, `CUSTOMER_DOMAIN`, `CUSTOMER_PUBLIC_IP`, `CUSTOMER_TIMEZONE`, SMTP vars | All mandatory fields filled |
| C9 | Create data directories | `mkdir -p ~/rhinometric_data_v2.5/{license-server/logs,postgres,redis,loki,jaeger,ai-anomaly/{models,data},console-backend/{logs,data},alertmanager}` | All dirs exist |
| C10 | Set `HOME` in `.env` | Ensure `HOME=/root` (or the user's home) is in `.env` | Present |

### Phase D ??? Install License (3 min)

| # | Step | Command / Action | Pass Criteria |
|---|------|-----------------|---------------|
| D1 | Upload `license.key` | `scp license.key root@<VM_IP>:/opt/rhinometric/license.key` | File exists |
| D2 | Upload `rhino-lic` binary | `scp rhino-lic root@<VM_IP>:/usr/local/bin/rhino-lic && chmod +x /usr/local/bin/rhino-lic` | Binary executable |
| D3 | Get machine fingerprint | `rhino-lic fingerprint` | Returns `sha256:<64hex>` |
| D4 | **Verify fingerprint matches license** | Compare output of D3 with `jq .payload.fingerprint /opt/rhinometric/license.key` | Must match, or request new license |
| D5 | Validate license | `rhino-lic validate /opt/rhinometric/license.key` | Exit code `0`, JSON with `"status": "valid"` |

> **CRITICAL**: If D4 fails (fingerprint mismatch), a new license must be issued by Rhinometric for this specific VM. This is the #1 cause of installation failures.

### Phase E ??? Build & Start Stack (10???15 min first time)

| # | Step | Command / Action | Pass Criteria |
|---|------|-----------------|---------------|
| E1 | Build images | `cd /opt/rhinometric && docker compose build` | All images built without error |
| E2 | Pull external images | `docker compose pull` | All images pulled |
| E3 | Start stack via launcher | `bash start-rhinometric.sh` | "License is VALID" + "stack started successfully" |
| E4 | Verify all containers | `docker ps --filter name=rhinometric --format 'table {{.Names}}\t{{.Status}}'` | ???18 containers running, majority `(healthy)` |
| E5 | Wait for health convergence | Wait ~3 min, repeat E4 | All containers `(healthy)` or `Up` |

### Phase F ??? Health Check (2 min)

| # | Step | Command / Action | Pass Criteria |
|---|------|-----------------|---------------|
| F1 | Nginx / Frontend alive | `curl -s -o /dev/null -w '%{http_code}' http://localhost/` | `200` or `302` |
| F2 | Backend API alive | `curl -s http://localhost/api/health` | JSON with health info |
| F3 | Grafana alive | `curl -s -o /dev/null -w '%{http_code}' http://localhost/grafana/api/health` | `200` |
| F4 | Prometheus alive | `docker exec rhinometric-prometheus wget -qO- http://localhost:9090/-/healthy` | `Prometheus Server is Healthy.` |
| F5 | VictoriaMetrics alive | `curl -s http://127.0.0.1:8428/health` | `OK` (only works from localhost) |
| F6 | Loki alive | `docker exec rhinometric-loki wget -qO- http://localhost:3100/ready` | `ready` |
| F7 | AI Anomaly alive | `docker exec rhinometric-ai-anomaly curl -sf http://localhost:8085/health` | JSON health |
| F8 | License Server alive | `docker exec rhinometric-license-server-v2 curl -sf http://localhost:5000/api/health` | JSON health |
| F9 | Alertmanager alive | `docker exec rhinometric-alertmanager wget -qO- http://localhost:9093/-/healthy` | healthy |

### Phase G ??? First Login & Sanity (5 min)

| # | Step | Action | Pass Criteria |
|---|------|--------|---------------|
| G1 | Open browser | Navigate to `http://<VM_IP>/` | Login page loads |
| G2 | Login with admin | Username: `admin`, Password: (from `.env` `ADMIN_PASSWORD`) | Dashboard/Home loads |
| G3 | Home dashboard | Check "Monitored Services" count | Shows `1` (self-monitoring only) |
| G4 | License page | Navigate to License page | Shows: valid, enterprise/trial, correct max_hosts, days remaining, modules |
| G5 | Alerts page | Navigate to Alerts | Loads without errors (may be empty) |
| G6 | Anomalies page | Navigate to AI Anomalies | Loads without errors (may show "No anomalies detected") |
| G7 | Grafana embedded | Click "View in Grafana" (as admin) | Opens Grafana Explore with VictoriaMetrics datasource |
| G8 | Test Grafana direct | Navigate to `http://<VM_IP>/grafana/` | Grafana UI loads |

## 1.4 Known Failure Points & Pre-Check Mitigations

| # | Failure Point | Symptom | Mitigation |
|---|--------------|---------|------------|
| F-1 | **Fingerprint mismatch** | `rhino-lic validate` exits with code 3 | Always run `rhino-lic fingerprint` BEFORE requesting a license. Include fingerprint in the license request form |
| F-2 | **Docker Compose v1 vs v2** | `docker-compose` not found or YAML errors | Script must check for `docker compose` (plugin) not `docker-compose` (standalone). Our `start-rhinometric.sh` currently uses `docker-compose` ??? needs migration to `docker compose` |
| F-3 | **Port 80 already in use** | Nginx container fails to bind | Pre-check: `ss -tlnp | grep :80` and abort if occupied |
| F-4 | **Insufficient disk for image builds** | Build fails mid-way | Pre-check: require ???20 GB free in `/var/lib/docker` |
| F-5 | **Missing `.env` variables** | Containers crash-loop with empty passwords | The `install-rhinometric.sh` script should validate all required vars are non-empty before `docker compose up` |
| F-6 | **`~/rhinometric_data_v2.5/` not created** | Volume mount failures | Script must create ALL data directories before starting |
| F-7 | **DNS not resolving customer domain** | Grafana `GF_SERVER_ROOT_URL` wrong | For installation test, use the raw IP; document that DNS is optional for initial setup |
| F-8 | **SMTP credentials wrong** | Alerts page works but no notifications go out | Non-blocking ??? stack still starts; test email delivery separately |
| F-9 | **`rhino-lic` binary not in PATH** | `start-rhinometric.sh` fails at step 1 | Pre-check in script; provide clear error message |
| F-10 | **`jq` not installed** | Some health check scripts fail | Add `jq` to prerequisites |
| F-11 | **`GF_SERVER_ROOT_URL` hardcoded to production IP** | Grafana deep links broken on new VM | **Must be parameterized** from `.env` or `customer.env` ??? currently hardcoded to `http://89.167.22.228/grafana` in compose file |
| F-12 | **`CORS_ORIGINS` hardcoded** | Frontend API calls blocked | **Must be parameterized** ??? currently hardcoded to production IP in compose file |

---

# PART 2 ??? Minimal Install Scripts & Documentation

## 2.1 Scripts to Create/Maintain

### 2.1.1 `scripts/install-prerequisites.sh`

**Purpose**: Install Docker Engine + Compose plugin + system utilities on a clean Ubuntu 22.04 VM.

**Steps performed**:
1. Validate OS is Ubuntu 22.04 (warn if different, continue).
2. Validate CPU ??? 4 cores, RAM ??? 8 GB, Disk ??? 80 GB free.
3. Install system packages: `ca-certificates curl gnupg lsb-release jq openssl`.
4. Add Docker official GPG key and APT repository.
5. `apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin`.
6. Enable and start Docker: `systemctl enable --now docker`.
7. Verify: `docker --version`, `docker compose version`.
8. Print summary with green/red pass/fail.

**Input variables**: None (auto-detects everything).

**Idempotency**: Safe to re-run ??? uses `apt install` (idempotent), skips Docker GPG add if already present.

**OS assumptions**: Ubuntu 22.04 LTS (Hetzner default image). Should warn and continue on 24.04.

```bash
# Usage:
sudo bash scripts/install-prerequisites.sh
```

### 2.1.2 `scripts/install-rhinometric.sh` (rewrite of existing)

**Purpose**: Set up the Rhinometric stack directory, generate secrets, create data volumes, build/pull images, and optionally start the stack.

**Steps performed**:
1. Validate Docker is installed (`docker compose version`).
2. Create `/opt/rhinometric/` if not exists.
3. If `.env` does not exist ??? copy `.env.template` ??? auto-generate random passwords for `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `GRAFANA_PASSWORD`, `SECRET_KEY`.
4. Prompt for or accept `ADMIN_PASSWORD` (env var or interactive).
5. If `config/customer.env` does not exist ??? copy `config/customer.env.template` ??? print warning that it must be edited.
6. Parameterize `GF_SERVER_ROOT_URL` and `CORS_ORIGINS`:
   - Detect public IP via `curl -s https://ifconfig.me` or accept `RHINOMETRIC_PUBLIC_IP` env var.
   - Substitute into `.env`: `PUBLIC_IP=<detected>`.
7. Create all data directories under `$HOME/rhinometric_data_v2.5/`:
   ```
   license-server/logs, postgres, redis, loki, jaeger,
   ai-anomaly/models, ai-anomaly/data,
   console-backend/logs, console-backend/data, alertmanager
   ```
8. Pull external images: `docker compose pull`.
9. Build custom images: `docker compose build`.
10. Print summary of readiness.

**Input variables**:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `INSTALL_DIR` | No | `/opt/rhinometric` | Installation root |
| `RHINOMETRIC_PUBLIC_IP` | No | auto-detected | VM public IP for Grafana/CORS |
| `ADMIN_PASSWORD` | Yes | (interactive prompt) | Console admin password |
| `SKIP_BUILD` | No | `false` | Set to `true` to skip image build |

**Idempotency**: Safe to re-run ??? does not overwrite `.env` if exists, does not recreate data dirs, `docker compose pull` and `build` are idempotent.

```bash
# Usage:
sudo bash scripts/install-rhinometric.sh
# Or non-interactive:
sudo ADMIN_PASSWORD=mysecret RHINOMETRIC_PUBLIC_IP=1.2.3.4 bash scripts/install-rhinometric.sh
```

### 2.1.3 `scripts/health-check.sh` (rewrite of existing `quick-health-check.sh`)

**Purpose**: Verify all critical Rhinometric services are alive and responding, suitable for post-install validation and cron monitoring.

**Steps performed**:
1. Check Docker containers running with name `rhinometric*`:
   - Count total, count healthy, list unhealthy.
2. Test endpoints (via `docker exec` or `curl localhost`):

   | Service | Check Method | Expected |
   |---------|-------------|----------|
   | Nginx (frontend) | `curl -s http://localhost/` | HTTP 200 or 302 |
   | Backend API | `curl -s http://localhost/api/health` | JSON response |
   | Grafana | `curl -s http://localhost/grafana/api/health` | HTTP 200 |
   | Prometheus | `docker exec ... wget localhost:9090/-/healthy` | "Healthy" |
   | VictoriaMetrics | `curl -s http://127.0.0.1:8428/health` | "OK" |
   | Loki | `docker exec ... wget localhost:3100/ready` | "ready" |
   | AI Anomaly | `docker exec ... curl localhost:8085/health` | JSON |
   | License Server | `docker exec ... curl localhost:5000/api/health` | JSON |
   | Alertmanager | `docker exec ... wget localhost:9093/-/healthy` | "healthy" |
   | Jaeger | `docker exec ... wget localhost:16686` | HTTP 200 |

3. Test license validity: `rhino-lic validate /opt/rhinometric/license.key --skip-fingerprint` (exit code 0).
4. Print summary: `PASSED X/Y` with colored output.
5. Exit code: `0` if all pass, `1` if any fail.

**Input variables**: None.

**Idempotency**: Read-only ??? always safe to run.

```bash
# Usage:
sudo bash scripts/health-check.sh
# Or from cron:
# */5 * * * * /opt/rhinometric/scripts/health-check.sh >> /var/log/rhinometric-health.log 2>&1
```

## 2.2 Required Changes to Existing Files

### 2.2.1 Parameterize `docker-compose.yml` (CRITICAL)

Currently hardcoded values that **break installation on a new VM**:

| Location | Current Value | Must Change To |
|----------|--------------|----------------|
| `grafana.environment.GF_SERVER_ROOT_URL` | `http://89.167.22.228/grafana` | `http://${PUBLIC_IP:-localhost}/grafana` |
| `rhinometric-console-backend.environment.CORS_ORIGINS` | Hardcoded list with `89.167.22.228` | `'["http://localhost:3002","http://${PUBLIC_IP:-localhost}","http://${PUBLIC_IP:-localhost}:80"]'` |
| `rhinometric-console-backend.environment.FRONTEND_URL` | `https://console.rhinometric.com` | `http://${PUBLIC_IP:-localhost}` |
| `grafana.environment.GF_SERVER_DOMAIN` | `app.rhinometric.com` | `${CUSTOMER_DOMAIN:-localhost}` |

**Recommendation**: Add a `PUBLIC_IP` variable to `.env.template` and reference it with `${PUBLIC_IP}` in compose. This is the **single most important change** for installation portability.

### 2.2.2 Compose command: `docker-compose` ??? `docker compose`

The `start-rhinometric.sh` script uses `docker-compose -f ...` (legacy standalone binary). Modern Docker installs provide only the `docker compose` plugin. Update:

```bash
# Old:
docker-compose -f "${COMPOSE_FILE}" up -d --no-build ${SCALE_OVERRIDES}
# New:
docker compose -f "${COMPOSE_FILE}" up -d --no-build ${SCALE_OVERRIDES}
```

### 2.2.3 `.env.template` (NEW FILE to create)

A sanitized version of the current `.env` with **empty values and comments**:

```env
# === RHINOMETRIC v2.6.0 ??? Environment Template ===
# Copy to .env and fill in all values before starting.
# Generated passwords should be ???20 random characters.

# === Public Access ===
PUBLIC_IP=           # VM public IP (e.g. 89.167.22.228)

# === Database ===
POSTGRES_USER=rhinometric
POSTGRES_PASSWORD=   # REQUIRED: Generate with `openssl rand -base64 24`
POSTGRES_DB=rhinometric

# === Cache ===
REDIS_PASSWORD=      # REQUIRED: Generate with `openssl rand -base64 24`

# === Grafana Admin ===
GRAFANA_USER=admin
GRAFANA_PASSWORD=    # REQUIRED: Generate with `openssl rand -base64 24`

# === Console Backend Security ===
SECRET_KEY=          # REQUIRED: Generate with `openssl rand -base64 48`
ADMIN_USERNAME=admin
ADMIN_PASSWORD=      # REQUIRED: Customer-defined admin password

# === Paths ===
HOME=/root

# === AlertManager Notifications ===
SLACK_WEBHOOK_URL=   # Optional: Slack incoming webhook URL
SMTP_PASSWORD=       # Optional: SMTP password for email alerts
SMTP_HOST=           # Optional: e.g. smtp.zoho.eu
SMTP_PORT=587        # Optional: SMTP TLS port
SMTP_USER=           # Optional: SMTP username/email
```

### 2.2.4 `config/customer.env.template` (NEW FILE to create)

```env
# === RHINOMETRIC v2.6.0 ??? Customer Configuration Template ===
# Copy to customer.env and fill in per-customer values.

CUSTOMER_NAME="Acme Corp"            # REQUIRED: Customer display name
CUSTOMER_ID=acme-001                 # REQUIRED: Unique customer identifier
CUSTOMER_DOMAIN=console.acme.com     # Optional: Custom domain (or use IP)
CUSTOMER_PUBLIC_IP=                   # REQUIRED: Same as PUBLIC_IP in .env
CUSTOMER_TIMEZONE=Europe/Madrid       # REQUIRED: TZ database name
CUSTOMER_DEFAULT_LANGUAGE=es          # Optional: en, es
CUSTOMER_LICENSE_TIER=enterprise      # Informational only; real tier is in license.key

# SMTP for customer notifications
CUSTOMER_SMTP_HOST=                   # Optional
CUSTOMER_SMTP_PORT=587                # Optional
CUSTOMER_SMTP_USER=                   # Optional
CUSTOMER_SMTP_PASSWORD=               # Optional
CUSTOMER_SMTP_FROM=                   # Optional
CUSTOMER_ALERT_EMAIL=                 # Optional: Where to send alert emails

# Slack notifications
CUSTOMER_SLACK_WEBHOOK=               # Optional
CUSTOMER_SLACK_CHANNEL_ALERTS=        # Optional: e.g. #alerts
CUSTOMER_SLACK_CHANNEL_CRITICAL=      # Optional: e.g. #critical

# SSL / HTTPS
CUSTOMER_SSL_ENABLED=false            # Set true when certs are provisioned

# Website monitoring
CUSTOMER_WEBSITE_URL=                 # Optional: Customer website to monitor
CUSTOMER_WEBSITE_MONITORING=false     # Enable blackbox probe

CUSTOMER_ADMIN_PASSWORD=              # Optional: Override admin password
```

## 2.3 Documentation Structure

### `docs/INSTALLATION_SMOKE_TESTS.md`

```
# Rhinometric v2.6 ??? Installation Smoke Tests

## 1. Prerequisites
   - Hardware: 4+ vCPUs, 8+ GB RAM, 160+ GB disk
   - OS: Ubuntu 22.04 LTS
   - Network: Ports 22, 80 open inbound
   - Files needed: release tarball, license.key, rhino-lic binary

## 2. Prepare Hetzner VM
   - Create VM in Hetzner Cloud console (CPX31 or CPX41)
   - Set hostname, timezone
   - Run `scripts/install-prerequisites.sh`

## 3. Install Rhinometric
   - Extract release bundle
   - Run `scripts/install-rhinometric.sh`
   - Review generated `.env` and `customer.env`

## 4. Configure License
   - Upload license.key to /opt/rhinometric/license.key
   - Upload rhino-lic to /usr/local/bin/rhino-lic
   - Verify fingerprint matches: `rhino-lic fingerprint`
   - Validate: `rhino-lic validate /opt/rhinometric/license.key`

## 5. Start & Run Health Checks
   - `bash start-rhinometric.sh`
   - `bash scripts/health-check.sh`

## 6. First Login & Sanity Checks
   - Open http://<IP>/ ??? Login ??? Check License page, Home, Alerts, Anomalies

## 7. Common Errors
   - Table of F-1 through F-12 failure points with resolutions
```

## 2.4 Release Bundle Contents

The `rhinometric-release-v2.6.0.tar.gz` should contain **exactly**:

```
rhinometric-release-v2.6.0/
????????? docker-compose.yml                  # Main compose (parameterized)
????????? .env.template                        # Environment template
????????? start-rhinometric.sh                # License-gated launcher
????????? scripts/
???   ????????? install-prerequisites.sh        # Docker + system deps
???   ????????? install-rhinometric.sh          # Setup + build + prep
???   ????????? health-check.sh                # Post-install validation
????????? config/
???   ????????? customer.env.template           # Per-customer config template
???   ????????? prometheus-v2.2.yml             # Prometheus config
???   ????????? loki-config.yml                 # Loki config
???   ????????? otel-collector-config.yml       # OTEL collector config
???   ????????? promtail-config.yml             # Promtail config
???   ????????? rules/                          # Prometheus alert rules
????????? nginx/
???   ????????? nginx.conf                      # Reverse proxy config
???   ????????? .htpasswd                       # Basic auth (if needed)
????????? alertmanager/
???   ????????? alertmanager.yml                # Alertmanager config
???   ????????? templates/                      # Slack + Email templates
????????? grafana/
???   ????????? provisioning/                   # Datasources + dashboards
????????? blackbox/
???   ????????? blackbox.yml                    # Blackbox exporter config
????????? init-db/                            # PostgreSQL init scripts
????????? rhinometric-ai-anomaly/             # AI anomaly service (source + Dockerfile)
????????? rhinometric-console/
???   ????????? backend/                        # FastAPI backend (source + Dockerfile)
???   ????????? frontend/                       # React frontend (source + Dockerfile)
????????? license-server-v2/                  # License server (source + Dockerfile)
????????? bin/
???   ????????? rhino-lic                       # Pre-compiled license validator (Linux x86_64)
????????? docs/
???   ????????? INSTALLATION_SMOKE_TESTS.md
???   ????????? ADMIN_QUICK_GUIDE.md
???   ????????? LICENSE_VALIDATION_FLOW.md
???   ????????? PERFORMANCE_LOAD_TESTS.md
????????? CHANGELOG.md
????????? README.md
```

---

# PART 3 ??? License Generator: `rhino-lic-gen.sh` (IMPLEMENTED)

> **Status**: ??? Implemented and smoke-tested on 2026-02-18.
> Script location: `scripts/rhino-lic-gen.sh` (v1.0.0).

## 3.1 Background: `rhino-lic issue` Already Exists

The Rust binary `rhino-lic` (v0.1.0, at `/usr/local/bin/rhino-lic`) already has an `issue` subcommand that:

- Accepts all license fields as CLI arguments.
- Signs with an Ed25519 private key.
- Outputs a signed JSON license file.

The wrapper `scripts/rhino-lic-gen.sh` adds **SKU-based defaults** on top of `rhino-lic issue`, so issuing a license for any product tier is a single command.

## 3.2 Product SKUs (Locked In)

### Self-Hosted / On-Prem (customer provides infrastructure)

| SKU Slug | Plan Field | Max Hosts | Default Validity | Purpose |
|----------|-----------|-----------|-----------------|---------|
| `community-trial-1-host-3m` | `community_trial` | 1 | 90 days | Free trial for very small teams, single host only |
| `community-annual-1-host` | `community` | 1 | 365 days | Very small SaaS or side projects with a single critical host |
| `starter-selfhosted-5-hosts` | `starter_onprem` | 5 | 365 days | Small SaaS / agencies with app + DB + extra services |

### Managed / Single-Tenant SaaS VM (prepared, not yet actively sold)

| SKU Slug | Plan Field | Max Hosts | Default Validity | Purpose |
|----------|-----------|-----------|-----------------|---------|
| `starter-saas-20-hosts` | `starter_saas` | 20 | 365 days | Small SaaS deployments, managed by Rhinometric |
| `professional-saas-50-hosts` | `professional_saas` | 50 | 365 days | Mid-size SaaS deployments |
| `enterprise-saas-100-hosts` | `enterprise_saas` | 100 | 365 days | Large enterprise SaaS deployments |

> **Note**: Prices are NOT encoded in the license. Only `plan`, `max_hosts`, validity, and `features` are in the signed payload. Pricing is handled in commercial documents, not in code.

### Default Features (all SKUs)

All SKUs receive the same feature set by default:

```
monitoring, alerting, anomaly-detection, license-server
```

This matches the existing production license schema. Features can be overridden per invocation with `--features`.

## 3.3 `rhino-lic-gen.sh` ??? CLI Reference

### Location

```
scripts/rhino-lic-gen.sh      # INTERNAL TOOL ??? Not for customer distribution
```

### Required Arguments

| Argument | Description | Example |
|----------|------------|---------|
| `--sku` | SKU identifier (see table above) | `community-trial-1-host-3m` |
| `--tenant-id` | Unique tenant identifier | `"acme-001"` |
| `--customer` | Customer display name | `"Acme Corp"` |
| `--fingerprint` | Target machine fingerprint (`sha256:<64hex>`) | `"sha256:f4f8f231..."` |
| `--privkey` | Path to Ed25519 private key (NEVER stored in repo) | `/secure/keys/license.key` |
| `--out` | Output path for the signed license file | `/tmp/acme-license.key` |

### Optional Arguments

| Argument | Description | Default |
|----------|------------|---------|
| `--expires-in-days` | Override default validity period | From SKU (90 or 365) |
| `--plan` | Override plan name | From SKU mapping |
| `--features` | Comma-separated feature list | `monitoring,alerting,anomaly-detection,license-server` |
| `--help` | Show usage help | ??? |

### How It Works Internally

1. Parse CLI arguments; validate all required fields are present.
2. Validate fingerprint format (`sha256:<64 hex chars>`).
3. Resolve `--sku` ??? `(plan, max_hosts, expires_in_days)` via a `case` statement.
4. Apply overrides (`--expires-in-days`, `--plan`, `--features`) if provided.
5. Compute `expires_at` = now + days, in RFC 3339 format (using GNU `date`).
6. Call `rhino-lic issue` with all resolved parameters.
7. Verify output file was created.
8. Print a summary with SKU, plan, max_hosts, expires_at, output path.

### Example Commands

```bash
# 1) Community trial ??? 1 host, 3 months:
bash scripts/rhino-lic-gen.sh \
  --sku community-trial-1-host-3m \
  --tenant-id "demo-001" \
  --customer "Demo Customer" \
  --fingerprint "sha256:f4f8f23133d1d94aba54e69938c77e6dcb094d7c5a9fcdd5732a62bec4bec13a" \
  --privkey /opt/rhinometric/rust-licenses/keys/license.key \
  --out /tmp/demo-license.key

# 2) Starter self-hosted ??? 5 hosts, 1 year:
bash scripts/rhino-lic-gen.sh \
  --sku starter-selfhosted-5-hosts \
  --tenant-id "customer-001" \
  --customer "Customer Name" \
  --fingerprint "sha256:f4f8f23133d1d94aba54e69938c77e6dcb094d7c5a9fcdd5732a62bec4bec13a" \
  --privkey /opt/rhinometric/rust-licenses/keys/license.key \
  --out /tmp/customer-001-license.key

# 3) Enterprise SaaS ??? 100 hosts, 1 year:
bash scripts/rhino-lic-gen.sh \
  --sku enterprise-saas-100-hosts \
  --tenant-id "bigcorp-001" \
  --customer "BigCorp Inc." \
  --fingerprint "sha256:f4f8f23133d1d94aba54e69938c77e6dcb094d7c5a9fcdd5732a62bec4bec13a" \
  --privkey /opt/rhinometric/rust-licenses/keys/license.key \
  --out /tmp/bigcorp-license.key

# 4) Short-lived test license (3 days, for expiration testing):
bash scripts/rhino-lic-gen.sh \
  --sku enterprise-saas-100-hosts \
  --tenant-id "test-expiry" \
  --customer "Expiration Test" \
  --fingerprint "sha256:f4f8f23133d1d94aba54e69938c77e6dcb094d7c5a9fcdd5732a62bec4bec13a" \
  --privkey /opt/rhinometric/rust-licenses/keys/license.key \
  --expires-in-days 3 \
  --out /tmp/test-3day.key
```

### Example Output

```
============================================================
 Rhinometric License Generator v1.0.0
============================================================

??? SKU             : community-trial-1-host-3m
??? Tenant ID       : demo-001
??? Customer        : Demo Customer
??? Plan            : community_trial
??? Max hosts       : 1
??? Validity        : 90 days
??? Expires at      : 2026-05-19T17:29:10Z
??? Features        : monitoring,alerting,anomaly-detection,license-server
??? Fingerprint     : sha256:f4f8f23133d1...
??? Output          : /tmp/demo-license.key

??? Calling rhino-lic issue ...

License issued successfully:
  File    : /tmp/demo-license.key
  Tenant  : demo-001
  ...

============================================================
 ??? License generated successfully
============================================================

  SKU          : community-trial-1-host-3m
  Plan         : community_trial
  Max hosts    : 1
  Expires      : 2026-05-19T17:29:10Z (90 days)
  Output file  : /tmp/demo-license.key (609 bytes)

  Validate with:
    rhino-lic validate /tmp/demo-license.key --pubkey <pubkey-path>

  Deploy to target VM:
    scp /tmp/demo-license.key root@<VM_IP>:/opt/rhinometric/license.key
```

## 3.4 Security Constraints

| Constraint | Implementation |
|-----------|----------------|
| **Private key never in repo** | Script requires `--privkey` path at runtime. No default path. No env-var fallback. |
| **Private key never logged** | Script passes the path to `rhino-lic issue`; the Rust binary reads the key internally. |
| **`.gitignore` protects keys** | Repo `.gitignore` should include: `*.key`, `!license.key.example`, `keys/` |
| **Internal-use only** | Script header states: "INTERNAL TOOL ??? Not for customer distribution" |
| **Key storage** | Keys must be stored in an encrypted vault (1Password, Bitwarden, AWS Secrets Manager). Never under the repo. |
| **No YAML / extra deps** | Script uses only Bash + `date` + `stat`. No `yq`, no `jq`, no Python required. |

## 3.5 Field Mapping: Generator ??? License JSON ??? Validator

| Generator Input | License JSON Field | Validator Check |
|----------------|-------------------|-----------------|
| `--sku` (resolved) ??? `--plan` | `payload.plan` | Returned in validation result |
| `--sku` (resolved) ??? `--max-hosts` | `payload.max_hosts` | Compared against Prometheus host count in backend |
| `--tenant-id` | `payload.tenant_id` | Part of signed payload (informational) |
| `--customer` | `payload.customer` | Part of signed payload (informational) |
| computed `--expires-at` | `payload.expires_at` | `issued_at <= now <= expires_at` |
| `--fingerprint` | `payload.fingerprint` | Compared against `sha256(machine-id + MAC)` |
| `--features` | `payload.features` | Returned in result; frontend shows as module chips |
| (auto: `Utc::now()`) | `payload.issued_at` | `now >= issued_at` |
| (auto: `1`) | `payload.version` | Future schema versioning |
| Ed25519 sign(canonical_json) | `signature` | Ed25519 verify with embedded public key |

## 3.6 Validation Test Matrix

| Test Case | Command Variation | Expected Exit Code | Expected Status |
|-----------|------------------|-------------------|-----------------|
| Valid license, correct fingerprint | Generate with correct `--fingerprint` | `0` | `valid` |
| Expired license | `--expires-in-days 0` or past date | `2` | `expired` / `date out of range` |
| Wrong fingerprint | Generate with fingerprint from a different VM | `3` on different machine | `fingerprint_mismatch` |
| Corrupted signature | Manually edit `signature` field in JSON | `1` | `invalid_signature` |
| Malformed JSON | Truncate the license file | `4` | `parse_error` |
| max_hosts exceeded | `--sku community-trial-1-host-3m` (max=1) + 2+ node-exporters | `0` (validator passes) | `valid` but backend shows `hosts_used > max_hosts` |

> **Note**: `max_hosts` enforcement happens in the **backend Python code** (`routers/license.py`), NOT in `rhino-lic`. The Rust validator only checks signature, dates, and fingerprint.

## 3.7 Smoke Test Results (2026-02-18)

All 6 SKUs were generated and validated successfully on the production VM:

| SKU | Plan | Max Hosts | Expires | Validated |
|-----|------|-----------|---------|-----------|
| `community-trial-1-host-3m` | `community_trial` | 1 | +90 days | ??? valid |
| `community-annual-1-host` | `community` | 1 | +365 days | ??? valid |
| `starter-selfhosted-5-hosts` | `starter_onprem` | 5 | +365 days | ??? valid |
| `starter-saas-20-hosts` | `starter_saas` | 20 | +365 days | ??? valid |
| `professional-saas-50-hosts` | `professional_saas` | 50 | +365 days | ??? valid |
| `enterprise-saas-100-hosts` | `enterprise_saas` | 100 | +365 days | ??? valid |

## 3.8 Integration with Installation / Sales Flow

```
?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
???  SALES / ONBOARDING FLOW                                    ???
???                                                             ???
???  1. Customer provisions a Hetzner VM                        ???
???  2. Customer runs install-prerequisites.sh + install.sh     ???
???  3. Customer sends us their machine fingerprint:            ???
???       ssh root@<VM> "rhino-lic fingerprint"                 ???
???       ??? sha256:abcdef1234567890...                          ???
???                                                             ???
???  4. We (internal) generate a license:                       ???
???       bash scripts/rhino-lic-gen.sh \                       ???
???         --sku starter-selfhosted-5-hosts \                  ???
???         --tenant-id "customer-001" \                        ???
???         --customer "Customer Name" \                        ???
???         --fingerprint "sha256:abcdef..." \                  ???
???         --privkey /secure/keys/license.key \                ???
???         --out customer-001-license.key                      ???
???                                                             ???
???  5. We deliver the license file to the customer:            ???
???       scp customer-001-license.key \                        ???
???         root@<VM>:/opt/rhinometric/license.key              ???
???                                                             ???
???  6. Customer starts the stack:                              ???
???       bash start-rhinometric.sh                             ???
???       ??? "License is VALID" ??? stack comes up                 ???
???                                                             ???
???  7. Customer opens http://<VM_IP>/ ??? Login ??? Done           ???
?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
```

---

# PART 4 ??? First-Time Admin Usability Checklist

## 4.1 License Page Verification

| # | Check | Expected Result | Status |
|---|-------|----------------|--------|
| U-1 | License page loads without errors | No spinners stuck, no blank page | ??? |
| U-2 | Edition shown correctly | Matches `plan` in license.key (e.g. "Enterprise") | ??? |
| U-3 | Max hosts shown | Numeric, matches license (e.g. 100) | ??? |
| U-4 | Hosts used shown | Numeric, matches Prometheus count (e.g. 1 for self-monitoring) | ??? |
| U-5 | Days remaining shown | Correct calculation, e.g. "682 days" | ??? |
| U-6 | Modules shown as chips | "monitoring", "alerting", "anomaly-detection" etc. | ??? |
| U-7 | Technical section (ADMIN only) | License ID, Install ID, raw JSON, validator type visible only for ADMIN/OWNER | ??? |
| U-8 | Technical section hidden for VIEWER | Login as VIEWER role ??? no technical section | ??? |
| U-9 | **Expired license**: show clear red banner | Swap in an expired license.key ??? "License Expired" with red styling, degraded mode | ??? |
| U-10 | **Invalid license**: show clear error | Use corrupted license ??? "Invalid License" with specific reason | ??? |
| U-11 | **Missing license**: show clear error | Remove license.key ??? "No License Found" with instructions | ??? |
| U-12 | **About to expire** (???30 days): warning banner | Use a license expiring in 15 days ??? yellow warning shown | ??? |

## 4.2 Home Dashboard Verification

| # | Check | Expected Result | Status |
|---|-------|----------------|--------|
| U-13 | Home page loads | Dashboard renders within 3 seconds | ??? |
| U-14 | "Monitored Services" count is accurate | Shows `1` for a fresh install (self-monitoring only) ??? **NOT hardcoded "12 services"** | ??? |
| U-15 | Container status widget | Shows ~20 containers, all green/healthy | ??? |
| U-16 | No stale/demo data visible | No "ACME Corp" or "demo" labels from development | ??? |

## 4.3 AI Anomalies & Alerts Page Verification

| # | Check | Expected Result | Status |
|---|-------|----------------|--------|
| U-17 | Alerts page loads | Shows loading state ??? then empty state ("No active alerts") or real alerts | ??? |
| U-18 | Anomalies page loads | Shows loading state ??? then "No anomalies detected" or real anomalies | ??? |
| U-19 | "View in Grafana" (admin) | Button visible for ADMIN/OWNER, links to Grafana Explore with **VictoriaMetrics** datasource | ??? |
| U-20 | "View in Grafana" (viewer) | Button **NOT visible** for VIEWER/OPERATOR roles | ??? |
| U-21 | Traces button disabled | "Jaeger Traces" button shows "Coming Soon" tooltip, not clickable | ??? |
| U-22 | Degraded mode (expired license) | Pages load but show a degraded banner; do **NOT** crash with unhandled exception | ??? |

## 4.4 General Navigation & First-Run Experience

| # | Check | Expected Result | Status |
|---|-------|----------------|--------|
| U-23 | Login page copy | Logo, "Rhinometric Console" branding, no "React App" or default titles | ??? |
| U-24 | Password change prompt | First login does NOT force password change (currently) ??? **consider adding for v2.7** | ??? |
| U-25 | Sidebar navigation | All menu items (Home, Alerts, Anomalies, License, Settings) present and functional | ??? |
| U-26 | Grafana accessible at `/grafana/` | Loads Grafana UI, VictoriaMetrics datasource pre-configured | ??? |
| U-27 | Grafana anonymous access | Non-logged-in users can view dashboards (as configured with `GF_AUTH_ANONYMOUS_ENABLED=true`) | ??? |
| U-28 | Mobile / responsive | Console is usable on tablet-sized screens (not broken layout) | ??? |

## 4.5 Friction Points to Improve Before "Production Ready"

| # | Friction Point | Severity | Recommendation |
|---|---------------|----------|----------------|
| FP-1 | **Hardcoded IPs in docker-compose.yml** (`GF_SERVER_ROOT_URL`, `CORS_ORIGINS`) | ???? Critical | Parameterize with `${PUBLIC_IP}` ??? a new customer CANNOT use the platform without manually editing compose | 
| FP-2 | **No `.env.template` or `customer.env.template`** in repo | ???? Critical | Customer has no idea what variables to set; create documented templates |
| FP-3 | **`start-rhinometric.sh` uses `docker-compose` (legacy)** | ???? Medium | Modern Docker only has `docker compose` plugin; script fails on fresh installs |
| FP-4 | **No first-login password change flow** | ???? Medium | Admin password is in plaintext in `.env`; should prompt for change on first console login |
| FP-5 | **License page shows "core" module by default** when backend doesn't send modules | ???? Medium | Frontend falls back to `['core']` ??? should show actual features from license.key or say "Checking..." |
| FP-6 | **Grafana branding says "v2.5.0"** in footer (`GF_BRANDING_FOOTER`) | ???? Low | Update to v2.6.0 |
| FP-7 | **Health check scripts are outdated** ??? reference Tempo (removed) and ports that are no longer exposed | ???? Medium | Rewrite `health-check.sh` as specified in Part 2 |
| FP-8 | **No HTTPS out of the box** | ???? Medium | Port 443 is commented out in compose; provide a `scripts/setup-ssl.sh` using Let's Encrypt/certbot for one-command TLS |
| FP-9 | **`GF_AUTH_ANONYMOUS_ENABLED=true`** ??? security concern | ???? Medium | Customers with public-facing VMs may not want anonymous Grafana access; make configurable via `.env` |
| FP-10 | **VictoriaMetrics shows `(unhealthy)`** on current production | ???? Medium | Health check uses `wget --spider` but VM returns non-standard response; fix healthcheck command in compose |
| FP-11 | **No uninstall / cleanup script** | ???? Low | Provide `scripts/uninstall-rhinometric.sh` for clean removal (stop containers, remove images, optionally remove data) |
| FP-12 | **ADMIN_PASSWORD visible in `.env`** ??? no rotation mechanism | ???? Low | After first login, admin should change password via UI; `.env` value becomes stale but still works if re-deployed |

---

# Appendix A ??? Quick Reference Card

## Installer Cheat Sheet (for Francia)

```bash
# === FRESH VM SETUP (run as root) ===

# 1. Install Docker
bash scripts/install-prerequisites.sh

# 2. Extract Rhinometric
cd /opt
tar xzf rhinometric-release-v2.6.0.tar.gz -C /opt/rhinometric --strip-components=1
cd /opt/rhinometric

# 3. Setup environment
bash scripts/install-rhinometric.sh

# 4. Install license
cp /path/to/license.key /opt/rhinometric/license.key
cp /path/to/rhino-lic /usr/local/bin/rhino-lic
chmod +x /usr/local/bin/rhino-lic

# 5. Verify license
rhino-lic fingerprint
rhino-lic validate /opt/rhinometric/license.key

# 6. Start
bash start-rhinometric.sh

# 7. Health check
bash scripts/health-check.sh

# 8. Open browser ??? http://<VM_IP>/
#    Login: admin / <password from .env>
```

## License Generation Cheat Sheet (internal)

```bash
# Get target VM fingerprint:
ssh root@<TARGET_VM> "rhino-lic fingerprint"
# ??? sha256:f4f8f23133d1d94aba54e69938c77e6dcb094d7c5a9fcdd5732a62bec4bec13a

# Generate community trial (1 host, 3 months):
bash scripts/rhino-lic-gen.sh \
  --sku community-trial-1-host-3m \
  --tenant-id "demo-001" \
  --customer "Demo Customer" \
  --fingerprint "sha256:<from above>" \
  --privkey /secure/keys/license.key \
  --out demo-001-license.key

# Generate starter self-hosted (5 hosts, 1 year):
bash scripts/rhino-lic-gen.sh \
  --sku starter-selfhosted-5-hosts \
  --tenant-id "customer-001" \
  --customer "Customer Name" \
  --fingerprint "sha256:<from above>" \
  --privkey /secure/keys/license.key \
  --out customer-001-license.key

# Generate enterprise SaaS (100 hosts, 1 year):
bash scripts/rhino-lic-gen.sh \
  --sku enterprise-saas-100-hosts \
  --tenant-id "bigcorp-001" \
  --customer "BigCorp Inc." \
  --fingerprint "sha256:<from above>" \
  --privkey /secure/keys/license.key \
  --out bigcorp-001-license.key

# Short-lived test license (3 days, for expiration testing):
bash scripts/rhino-lic-gen.sh \
  --sku enterprise-saas-100-hosts \
  --tenant-id "test-expiry" \
  --customer "Expiration Test" \
  --fingerprint "sha256:<from above>" \
  --privkey /secure/keys/license.key \
  --expires-in-days 3 \
  --out test-3day.key

# Validate a generated license:
rhino-lic validate customer-001-license.key --pubkey /path/to/license.pub

# Deliver to customer:
scp customer-001-license.key root@<TARGET_VM>:/opt/rhinometric/license.key
```

---

# Appendix B ??? Implementation Priority

| Priority | Task | Effort | Blocks |
|----------|------|--------|--------|
| **P0** | ~~Parameterize `docker-compose.yml` (FP-1)~~ | 30 min | ??? Done 2026-02-18 |
| **P0** | ~~Create `.env.template` + `customer.env.template` (FP-2)~~ | 20 min | ??? Done 2026-02-18 |
| **P0** | ~~Fix `start-rhinometric.sh` compose detection (FP-3)~~ | 5 min | ??? Done 2026-02-18 |
| **P0** | ~~Fix VictoriaMetrics healthcheck (FP-10)~~ | 15 min | ??? Done 2026-02-18 |
| **P0** | ~~Write `scripts/rhino-lic-gen.sh` + SKU mapping~~ | 2 hr | ??? Done 2026-02-18, all 6 SKUs tested |
| **P1** | Write `scripts/install-prerequisites.sh` | 1 hr | Repeatable installation |
| **P1** | Rewrite `scripts/install-rhinometric.sh` | 2 hr | Repeatable installation |
| **P1** | Rewrite `scripts/health-check.sh` | 1 hr | Post-install validation |
| **P2** | Write `docs/INSTALLATION_SMOKE_TESTS.md` | 1 hr | Francia can test independently |
| **P2** | Update Grafana branding to v2.6.0 (FP-6) | 5 min | Cosmetic |
| **P3** | HTTPS setup script (FP-8) | 2 hr | Security for public-facing installs |
| **P3** | First-login password change (FP-4) | 4 hr | Security improvement |

---

> **Next action**: Provision a **clean Hetzner test VM** and run Part 1 installation checklist manually. Then implement P1 scripts (`install-prerequisites.sh`, `install-rhinometric.sh`, `health-check.sh`).

