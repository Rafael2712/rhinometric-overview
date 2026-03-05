# Rhinometric Ansible Installer — Documentation

## Overview

The Ansible installer replaces the legacy Bash installer (v3.0.0–v3.0.4) with a
professional, idempotent, and maintainable automation stack. It deploys the full
Rhinometric on-prem platform (21 Docker services) with license activation, health
validation, and automatic debug bundle generation on failure.

### Key Design Principles

| Principle | Implementation |
|---|---|
| **Idempotent** | `.env` uses `force: false`; rsync excludes state files; config patches are declarative |
| **No secrets in logs** | `no_log: true` on credential generation and license activation tasks |
| **Docker inspect, not curl** | Container health is checked via `docker inspect`, never `curl` inside containers |
| **Nginx front-door only** | HTTP validation uses port 80 through Nginx — no direct container ports exposed |
| **Rescue → Debug bundle** | Any critical failure automatically collects diagnostics before aborting |
| **Offline-capable** | License request bundle generated for air-gapped environments |

---

## Architecture

```
ansible/
├── ansible.cfg                          # Global config (pipelining, yaml callback)
├── inventories/
│   ├── staging.ini                      # Staging host (edit TARGET_IP)
│   └── prod.ini                         # Production with Vault references
├── group_vars/
│   └── all.yml                          # ~100 defaults (version, paths, services, etc.)
├── playbooks/
│   ├── deploy.yml                       # Full deploy: Docker → Deploy → License → Validate
│   ├── validate.yml                     # Standalone health check
│   └── uninstall.yml                    # Clean removal (safe by default)
└── roles/
    ├── docker/                          # Install/verify Docker + Compose v2
    ├── rhinometric_deploy/              # Tarball, .env, config patches, volumes, compose up
    ├── rhinometric_license/             # Fingerprint + online/offline activation
    ├── rhinometric_validate/            # Container health + HTTP endpoint checks
    └── rhinometric_debugbundle/         # Diagnostic tar.gz collection
```

---

## Quick Start

### Prerequisites

- **Control node**: Python 3.8+, Ansible 2.14+ (`pip install ansible`)
- **Target server**: Ubuntu 20.04+/Debian 11+, SSH access, sudo/root
- **Tarball**: `rhinometric-v3.0.4.tar.gz` in `dist/` directory

### 1. Configure Inventory

Edit `inventories/staging.ini`:

```ini
[rhinometric]
89.167.22.228 ansible_user=root

[rhinometric:vars]
rhinometric_version=3.0.4
rhinometric_tarball_path_local=../../dist/rhinometric-v3.0.4.tar.gz
```

### 2. Deploy

```bash
# From the ansible/ directory:
ansible-playbook -i inventories/staging.ini playbooks/deploy.yml
```

### 3. Deploy with Online License Activation

```bash
ansible-playbook -i inventories/staging.ini playbooks/deploy.yml \
  -e rhinometric_activation_code=XXXX-XXXX-XXXX
```

### 4. Validate an Existing Deployment

```bash
ansible-playbook -i inventories/staging.ini playbooks/validate.yml
```

### 5. Uninstall

```bash
# Safe uninstall (preserves data)
ansible-playbook -i inventories/staging.ini playbooks/uninstall.yml

# Full removal including data
ansible-playbook -i inventories/staging.ini playbooks/uninstall.yml \
  -e remove_data=true

# Nuclear option (also removes Docker)
ansible-playbook -i inventories/staging.ini playbooks/uninstall.yml \
  -e remove_data=true -e remove_docker=true -e remove_images=true
```

---

## Roles Reference

### `docker`

Ensures Docker Engine and Compose v2 are installed.

| Task | Description |
|---|---|
| Check Docker | `docker --version` |
| Install Docker | `get.docker.com` script (if missing) |
| Verify Compose v2 | `docker compose version` — **fails** if not available |

### `rhinometric_deploy`

The largest role — handles the complete deployment in 6 phases:

#### Phase 1: System Validation
- Checks OS family (Debian/RedHat), CPU count, RAM, disk space
- All checks are **warnings only** (won't block deployment)

#### Phase 2: Tarball Copy & Extract
- Copies tarball from control node via `ansible.builtin.copy`
- Extracts with `--strip-components=1`
- rsync-like approach: **excludes** `.env`, `install-info.txt`, `fingerprint.txt`, `license.key`

#### Phase 3: .env Generation
- Uses Jinja2 template (`env.j2`) with `force: false` → never overwrites existing
- Generates random passwords via `lookup('password', '/dev/null length=24')`
- All credential tasks use `no_log: true`

#### Phase 4: Config Patches
Fixes known issues discovered during Bash installer era:

| Patch | What it fixes |
|---|---|
| Prometheus target | `localhost:9090` → `rhinometric-prometheus:9090` |
| AI Anomaly healthcheck | `curl` → Python `urllib` (no curl in container) |
| Loadtest targets mount | Missing `loadtest_targets.json` volume mount |
| Compose version field | Removes deprecated `version:` top-level key |

#### Phase 5: Volume Preparation
Creates data directories with correct ownership:

| Volume | UID:GID | Service |
|---|---|---|
| jaeger | 10001:0 | Jaeger OTLP collector |
| postgresql | 999:999 | PostgreSQL |
| redis | 999:999 | Redis |
| alertmanager | 65534:65534 | Alertmanager |
| loki | root:root | Loki |
| ai-anomaly, console, license | 777 (world-write) | Various |

#### Phase 6: Compose Up
- `docker compose pull` → `docker compose build` → `docker compose up -d`
- Waits configurable seconds before health checks
- Counts running containers vs expected

### `rhinometric_license`

Two activation modes:

#### Mode A: Online Activation
1. Detects machine fingerprint via `rhino-lic fingerprint`
2. POSTs `{fingerprint, activation_code}` to activation endpoint
3. Saves returned `license.key`
4. Restarts backend + license-server

```bash
ansible-playbook -i inventories/staging.ini playbooks/deploy.yml \
  -e rhinometric_activation_code=XXXX-XXXX-XXXX
```

#### Mode B: Offline Bundle (Air-Gapped)
1. Detects machine fingerprint
2. Generates `license-request.json` with machine metadata
3. Prints manual instructions for email exchange
4. After receiving `license.key`, user copies it and restarts services

### `rhinometric_validate`

Three-phase health check:

#### Phase 1: Docker Container Health
- Inspects each container via `docker inspect`
- Classifies by criticality: **critical** / **important** / **optional**
- Retries for unhealthy critical services (configurable retries/delay)

#### Phase 2: HTTP Endpoint Validation
- Tests endpoints through Nginx port 80 **only**
- Default endpoints:

| Endpoint | Path | Critical |
|---|---|---|
| Frontend | `/` | Yes |
| Backend API | `/api/health` | Yes |
| Grafana | `/grafana/api/health` | Yes |
| Prometheus | `/prometheus/-/healthy` | No |

#### Phase 3: Summary Report
Produces a formatted report with overall status:
- **HEALTHY**: All critical + important services OK
- **DEGRADED**: Critical OK, some important services down
- **CRITICAL_FAILURE**: Critical services down → triggers debug bundle

### `rhinometric_debugbundle`

Collects diagnostic information into a tar.gz:

| File | Contents |
|---|---|
| `system-info.txt` | OS, kernel, CPU, RAM, disk, Docker version |
| `compose-ps.txt` | `docker compose ps -a` output |
| `log-<service>.txt` | Last 500 lines per service |
| `inspect-<service>.json` | Detailed inspect of failed containers |
| `dmesg-oom.txt` | Kernel OOM kill events |
| `docker-networks.txt` | Network configuration |
| `docker-volumes.txt` | Volume/disk usage |
| `env-sanitized.txt` | `.env` with secrets redacted |
| `docker-compose.yml` | Compose definition |

---

## Variables Reference

### Core Variables (`group_vars/all.yml`)

| Variable | Default | Description |
|---|---|---|
| `rhinometric_version` | `3.0.4` | Release version |
| `rhinometric_install_dir` | `/opt/rhinometric` | Installation directory |
| `rhinometric_data_dir` | `/opt/rhinometric/data` | Persistent data |
| `rhinometric_tarball_path_local` | `../../dist/rhinometric-v{{ version }}.tar.gz` | Local tarball path |

### System Requirements (warnings only)

| Variable | Default |
|---|---|
| `rhinometric_min_cpu` | `4` |
| `rhinometric_min_ram_gb` | `8` |
| `rhinometric_min_disk_gb` | `20` |

### Health Check Tuning

| Variable | Default | Description |
|---|---|---|
| `rhinometric_validate_retries` | `40` | Max retries per service |
| `rhinometric_validate_delay` | `10` | Seconds between retries |
| `rhinometric_validate_compose_up_wait` | `30` | Initial settle time |
| `rhinometric_validate_infra_wait_retries` | `12` | Retries for infra services |

### License

| Variable | Default | Description |
|---|---|---|
| `rhinometric_enable_online_activation` | `true` | Enable online mode |
| `rhinometric_activation_url` | `https://license.rhinometric.com/api/activate` | Activation endpoint |
| `rhinometric_activation_code` | `""` | Activation code (pass via `-e`) |

### Service Classification

```yaml
rhinometric_critical_services:
  - rhinometric-postgres
  - rhinometric-redis
  - rhinometric-console-backend
  - rhinometric-console-frontend
  - rhinometric-nginx
  - rhinometric-grafana

rhinometric_important_services:
  - license-server-v2
  - rhinometric-prometheus
  - rhinometric-loki
  - rhinometric-otel-collector
  - rhinometric-alertmanager
  - rhinometric-cadvisor
  - rhinometric-jaeger

rhinometric_optional_services:
  - rhinometric-victoria-metrics
  - rhinometric-ai-anomaly
```

---

## Deployment Flow

```
deploy.yml
│
├── pre_tasks: Banner + gather facts
│
├── role: docker
│   ├── Check Docker installed
│   ├── Install via get.docker.com (if missing)
│   └── Verify Compose v2
│
├── role: rhinometric_deploy
│   ├── Phase 1: System validation (CPU/RAM/disk — warnings only)
│   ├── Phase 2: Copy + extract tarball
│   ├── Phase 3: Generate .env (idempotent, force: false)
│   ├── Phase 4: Config patches (prometheus, AI HC, loadtest, version)
│   ├── Phase 5: Volume prep (correct UIDs)
│   └── Phase 6: compose pull → build → up -d
│
├── block: rhinometric_license
│   ├── Detect fingerprint
│   ├── Online: POST activation → save license.key → restart
│   └── Offline: Generate license-request.json → print instructions
│   └── rescue: Warning (non-blocking)
│
├── block: rhinometric_validate
│   ├── Phase 1: Docker inspect health (critical/important/optional)
│   ├── Phase 2: HTTP through Nginx :80
│   └── Phase 3: Summary report
│   └── rescue: rhinometric_debugbundle → fail
│
└── post_tasks: Success banner with URL + credentials location
```

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---|---|
| `docker compose` not found | Ansible installs it, but check: `docker compose version` |
| Port 80 already in use | Stop conflicting service: `ss -tlnp \| grep :80` |
| Container keeps restarting | Check logs: `docker compose logs <service> --tail=100` |
| Disk full | Check with `df -h`; prune images: `docker image prune -af` |
| License activation fails | Use offline flow; check firewall for HTTPS outbound |

### Manual Debug Bundle

```bash
ansible-playbook -i inventories/staging.ini playbooks/validate.yml
# If validation fails, debug bundle is auto-generated
# Download it:
scp root@<IP>:/tmp/rhinometric-debug-*.tar.gz .
```

### Re-run After Fixing Issues

The installer is fully idempotent:

```bash
# Re-run deploy — won't regenerate .env or overwrite state
ansible-playbook -i inventories/staging.ini playbooks/deploy.yml
```

### Skip Specific Phases

```bash
# Skip license activation
ansible-playbook -i inventories/staging.ini playbooks/deploy.yml --skip-tags license

# Skip health validation
ansible-playbook -i inventories/staging.ini playbooks/deploy.yml --skip-tags validate

# Only run Docker installation
ansible-playbook -i inventories/staging.ini playbooks/deploy.yml --tags docker
```

---

## Security Notes

1. **Credentials**: Generated randomly per deployment; never logged (`no_log: true`)
2. **Activation code**: Pass via `-e` flag, never stored in inventory files
3. **Production inventory**: Use Ansible Vault for sensitive variables:
   ```bash
   ansible-vault encrypt_string 'XXXX-XXXX-XXXX' --name rhinometric_activation_code
   ```
4. **SSH**: Use key-based auth; avoid password in inventory
5. **Debug bundles**: `.env` is sanitized (secrets replaced with `***REDACTED***`)

---

## Migration from Bash Installer

If upgrading from the legacy Bash installer (v3.0.0–v3.0.4):

1. The Ansible installer detects existing `.env` and **preserves it** (`force: false`)
2. Existing `fingerprint.txt` and `license.key` are preserved (rsync exclusion)
3. Config patches are idempotent — safe to re-apply
4. Volume permissions are corrected on every run

```bash
# Safe upgrade from existing Bash installation:
ansible-playbook -i inventories/staging.ini playbooks/deploy.yml
```

---

## Version History

| Version | Date | Notes |
|---|---|---|
| 1.0.0 | 2025-01 | Initial Ansible installer replacing Bash v3.0.4 |
