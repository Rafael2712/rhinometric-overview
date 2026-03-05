# Installer Bash v3.0.4 — Post-Mortem & Freeze Notice

> **Status**: FROZEN / DEPRECATED  
> **Decision date**: 2026-03-05  
> **Last commit**: `ab639d6` on branch `feature/use-direct-grafana-links`  
> **Superseded by**: Ansible installer (in progress)

---

## 1. Executive Summary

The Bash installer (`install-rhinometric.sh`) was developed as a single-script, on-prem production installer for the Rhinometric observability stack. After four iterative releases (v3.0.0 → v3.0.4), the installer reaches the point where it can:

- Validate system prerequisites (OS, CPU, RAM, disk, Docker)
- Detect machine fingerprint and manage license validation
- Copy configs, build/pull images, start the 21-service Docker Compose stack
- Run a multi-phase health check with auto-fix and rollback capabilities
- Generate a debug bundle on failure

**However**, the installer cannot guarantee full functional correctness of the running platform. The final test on a fresh Ubuntu 24.04 VM showed the stack starting ("INSTALLATION COMPLETED") but with UI-level failures (KPI fetch errors, dashboard loading failures). These are integration/config issues beyond what a shell script can reasonably detect and fix.

**Decision**: Stop iterating on the Bash installer. Freeze v3.0.4 as historical reference and move to an Ansible-based installer that offers idempotency, role-based structure, and testability.

### Why stop?

| Factor | Bash installer | Ansible installer |
|--------|---------------|-------------------|
| Idempotency | Manual (fragile) | Built-in |
| Testability | None (run the whole thing) | Molecule / check mode |
| Config templating | sed/python hacks through SSH | Jinja2 templates |
| Error handling | Explicit per-command | Handlers + rescue blocks |
| Debugging | Shell tracing, manual | Verbose mode, callbacks |
| Maintainability | Single 1000+ line script | Roles, tasks, vars |

---

## 2. Timeline: v3.0.2 → v3.0.4

### v3.0.2 (commit `5dd918c`)

First version with auto-fix and debug bundle capabilities. Issues discovered during real fresh install on Ubuntu 24.04:

- `/etc/os-release` sourced with `. /etc/os-release`, which crashed because `VERSION` was declared `readonly` in the script
- `df` on non-existent `INSTALL_DIR` returned empty, breaking disk check
- Health check curled `localhost:3002` and `localhost:3000` directly — but those ports are NOT published to the host (only port 80/nginx is)
- VictoriaMetrics stuck in restart loop (root cause found in v3.0.3)
- Rollback (`docker compose down -v`) destroyed all evidence before debug bundle could be collected

### v3.0.3 (commit `3fbe01a`)

Addressed most v3.0.2 issues:

- Safe `/etc/os-release` parsing (grep instead of source)
- Disk check walks to existing parent directory
- Dynamic port detection via `docker compose port`
- Full stack health check with Phase 1 (infra) → Phase 2 (all services) → Phase 3 (HTTP)
- Debug bundle generated BEFORE rollback

**New bug introduced**: `docker compose port` returns the literal string `"invalid IP:0"` for services without host-published ports. The installer checked `-n` (non-empty) which passed, constructing garbage URLs:

```
$ docker compose port grafana 3000
invalid IP:0

$ docker compose port prometheus 9090
invalid IP:0

# Installer then did:
# endpoints+=("Grafana|http://invalid IP:0/api/health")
# → curl "http://invalid IP:0/api/health" → failure → false critical error
```

### v3.0.4 (commit `ab639d6`) — FINAL

Four targeted fixes plus UX improvements:

**(A) VictoriaMetrics promscrape config**

VictoriaMetrics was configured with `-promscrape.config=/etc/prometheus/prometheus.yml` which contained:

```yaml
# config/prometheus-v2.2.yml, line 20 (BEFORE fix)
- targets: ['localhost:9090']
```

Inside the VM container, `localhost:9090` doesn't resolve to Prometheus. Also, `file_sd_configs` referenced `/etc/prometheus/loadtest_targets.json` which didn't exist.

Fix: `localhost:9090` → `rhinometric-prometheus:9090`, created empty `loadtest_targets.json` (`[]`), added volume mount.

**(B) AI Anomaly healthcheck**

The Docker Compose healthcheck used `curl` but the container image (`python:3.11-slim`) doesn't include curl:

```yaml
# docker-compose.yml (BEFORE fix)
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8085/health"]
```

```
# Container log:
OCI runtime exec failed: exec failed: unable to start container process:
exec: "curl": executable file not found in $PATH
```

Fix: Changed to `CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8085/health', timeout=5)"`.

**(C) Endpoint validation — "invalid IP:0" root cause**

`docker compose port <service> <port>` returns `"invalid IP:0"` for services without host port mappings. This is a non-empty string, so the v3.0.3 `-n` check passed.

Fix: Added `is_valid_hostport()` regex validator (`^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$`). Only Nginx port 80 is validated via host curl. Internal services tested through Nginx proxy routes (`/`, `/api/health`, `/grafana/api/health`).

**(D) License/fingerprint UX**

- Fingerprint saved to `/opt/rhinometric/fingerprint.txt`
- `print_license_apply_guide()` with step-by-step instructions
- `--wait-for-license` flag (pauses up to 5 min for license.key placement)
- Credentials file includes license application guide

---

## 3. Final Test Result (v3.0.4)

**Server**: Fresh Ubuntu 24.04 VM  
**Installer output**: `✓ INSTALLATION COMPLETED`  
**Container status**: All 21 services running, most healthy  

**Functional result**: UI loads but shows runtime errors:

- "Failed to fetch KPIs" — backend cannot retrieve metrics from Prometheus/VictoriaMetrics
- "Failed to load dashboards" — Grafana datasource provisioning incomplete
- Various console API 500 errors related to uninitialized data

These are **integration-level issues** (datasource URLs, API initialization sequences, seed data) that a Bash installer cannot reasonably detect or fix. The staging environment (configured manually over time) works correctly, confirming the platform itself is functional.

---

## 4. What Remains Unsolved

| Issue | Category | Why not fixed in Bash |
|-------|----------|----------------------|
| Grafana datasource provisioning (correct URLs for Prometheus/Loki) | Config templating | Requires Jinja2-style templating with env vars |
| Console backend initial data seeding | Initialization order | Needs orchestrated wait → seed → verify cycle |
| Service dependency ordering beyond Docker healthchecks | Orchestration | Compose `depends_on` with `condition: service_healthy` is insufficient for app-level readiness |
| End-to-end functional verification (not just HTTP 200) | Testing | Would require headless browser or deep API integration testing |
| Secrets rotation / renewal | Security | Needs vault integration or at minimum a renewal script |

---

## 5. Next Steps: Ansible Installer

The Ansible installer will:

1. Use roles for each service group (infra, observability, app, reverse-proxy)
2. Template all config files with Jinja2 (datasource URLs, passwords, IPs)
3. Include Molecule tests for each role
4. Support `--check` mode for dry runs
5. Handle fingerprint/license flow as a dedicated task
6. Include a verification playbook (`verify.yml`) that tests real API responses

---

## 6. File Inventory (v3.0.4 artifacts)

| File | Lines | Description |
|------|-------|-------------|
| `dist/install-rhinometric.sh` | 1,047 | Main installer script |
| `dist/build-release.sh` | ~80 | Tarball builder |
| `config/prometheus-v2.2.yml` | ~25 | Promscrape config (patched) |
| `config/loadtest_targets.json` | 1 | Empty file_sd_configs target |
| `docker-compose.yml` | ~650 | Compose file (AI anomaly HC + VM mount patched) |
| `prometheus/prometheus.yml` | ~25 | Prometheus config (patched) |

---

## 7. Reproduction Notes

To reproduce the v3.0.4 install on a fresh Ubuntu 24.04 VM:

```bash
# Transfer tarball
scp rhinometric-v3.0.4.tar.gz root@<SERVER>:/tmp/

# On server
tar -xzf /tmp/rhinometric-v3.0.4.tar.gz
cd rhinometric-v3.0.4
sudo bash install-rhinometric.sh
```

The installer will complete successfully but the platform will show UI-level errors as documented above.

---

*Document created: 2026-03-05 | Author: Release Engineering*
