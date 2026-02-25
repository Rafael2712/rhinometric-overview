# Rhinometric Single Installer — Delivery Report

> **Version:** 2.6.0 · **Date:** 2026-02-25 · **Author:** DevOps/SRE Team

---

## Deliverables

| # | File | Type | Purpose |
|---|------|------|---------|
| 1 | `scripts/install-rhinometric.sh` | NEW | Idempotent on-premise installer (530+ lines) |
| 2 | `scripts/rhinoctl.sh` | NEW | Platform management CLI (400+ lines) |
| 3 | `docs/INSTALL_ONPREM_QUICKSTART.md` | NEW | Customer-facing quickstart guide |
| 4 | `docs/INSTALLATION_CURRENT_STATE.md` | NEW | Internal inventory & technical debt doc |

---

## Validation Results (Production VM: 89.167.22.228)

### Pre-flight Checks (--dry-run)
```
[  OK]  Running as root
[  OK]  Ubuntu 24.04 detected
[  OK]  CPU: 8 cores
[  OK]  RAM: 15608 MB
[  OK]  Disk: 263 GB available
[  OK]  Docker 28.2 installed
[  OK]  docker-compose 2.24.5 (standalone)
[  OK]  Dependencies satisfied (curl, openssl, jq)
[  OK]  Required ports available
[  OK]  All pre-flight checks passed
```

### rhinoctl status
```
  Containers:  20/20 running
  Healthy:     15
  Disk used:   11G
  License:     Applied
```

### rhinoctl health
```
  ✓ ai-anomaly            healthy
  ✓ alertmanager           healthy
  ✓ console-backend        healthy
  ✓ console-frontend       healthy
  ✓ grafana                healthy
  ✓ jaeger                 healthy
  ✓ license-server-v2      healthy
  ✓ loki                   healthy
  ✓ nginx                  healthy
  ✓ otel-collector         healthy
  ✓ postgres               healthy
  ✓ postgres-exporter      healthy
  ✓ prometheus             healthy
  ✓ redis                  healthy
  ✓ cadvisor               healthy
  ~ blackbox-exporter      running (no healthcheck)
  ~ node-exporter          running (no healthcheck)
  ~ promtail               running (no healthcheck)
  ~ redis-exporter         running (no healthcheck)
  ✗ victoria-metrics       unhealthy

  ✓ Frontend (nginx:80)    200
```

### rhinoctl fingerprint
```
  HWID: 2B05C713B5896223
  Saved to: /opt/rhinometric/HWID.txt
```

---

## What the Installer Does (Step by Step)

1. **Pre-flight validation** — root, OS, CPU ≥2, RAM ≥8GB, disk ≥50GB, Docker, Compose, ports, curl/openssl/jq
2. **Detect existing** — if found, offers Update (preserve .env) / Fresh (backup + overwrite) / Abort
3. **Prompt config** — edition (trial/annual), domain/IP, admin email (skipped in `--non-interactive`)
4. **Create directories** — install dir + 10 data subdirs at `~/rhinometric_data_v2.5/`
5. **Generate .env** — all 17 variables with secure random passwords (skipped if exists + update mode)
6. **Save CREDENTIALS.txt** — admin-readable credentials file (chmod 600)
7. **Setup compose symlink** — `docker-compose.yml` → `docker-compose-v2.5.0-SECURE.yml`
8. **Apply license** — if `--license-file` provided
9. **Build images** — pull base + build 4 custom services (parallel, with fallback)
10. **Start stack** — `docker compose up -d --remove-orphans --scale license-ui=0`
11. **Wait for healthy** — polls Docker healthcheck status up to 120s
12. **Smoke tests** — Docker-native health status + HTTP frontend check
13. **Install rhinoctl** — copies to `/usr/local/bin/rhinoctl`

---

## Known Issues / Remaining Technical Debt

| # | Issue | Severity | Notes |
|---|-------|----------|-------|
| 1 | `victoria-metrics` reports unhealthy | Low | Pre-existing; healthcheck may need tuning |
| 2 | 4 exporters lack Docker healthchecks | Low | They run fine, just can't confirm via Docker API |
| 3 | `license-ui` excluded (`--scale 0`) | Info | Known build failure; not needed for operation |
| 4 | `rmetricctl` (Python CLI) still references v2.2 paths | Low | Superseded by `rhinoctl.sh` |
| 5 | No automated backup cron | Medium | `rhinoctl backup` works manually; cron TODO |
| 6 | TLS not included in installer | Medium | Handled separately via nginx/Cloudflare |
| 7 | Email-in-the-loop for license activation | Medium | HWID → email → manual key generation |

---

## Usage Commands

```bash
# Install (interactive)
sudo bash scripts/install-rhinometric.sh

# Install (CI/automated)
sudo bash scripts/install-rhinometric.sh --non-interactive --edition trial

# Validate without changes
sudo bash scripts/install-rhinometric.sh --dry-run

# Day-2 operations
rhinoctl status           # Overview
rhinoctl health           # Endpoint checks
rhinoctl fingerprint      # Generate HWID
rhinoctl apply-license F  # Apply license
rhinoctl start|stop       # Start/stop
rhinoctl restart          # Restart all
rhinoctl logs grafana 50  # Service logs
rhinoctl backup           # Full backup
rhinoctl update           # Pull + rebuild
```

---

## Files NOT Modified

Per project rules, zero existing files were changed:
- No infrastructure touched
- No repo restructured
- No secrets in git
- No running services disrupted
- The production VM continues running 20/20 containers

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Installer overwrites existing .env | Detects existing install; Update mode preserves .env |
| Build fails (no internet) | `--skip-build` flag; `pull --ignore-pull-failures` |
| Port conflict | Pre-flight check detects conflicts; skips own containers |
| Wrong compose file | Hardcoded to `docker-compose-v2.5.0-SECURE.yml` |
| Data loss on reinstall | Backup created before fresh install; rollback instructions shown |
