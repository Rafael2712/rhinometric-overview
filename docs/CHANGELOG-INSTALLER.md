# Changelog — Rhinometric On-Prem Installer

All notable changes to the Bash-based installer are documented in this file.

> **Notice**: The Bash installer is **frozen at v3.0.4**. No further development planned.  
> Successor: Ansible-based installer (separate repository/playbook).

---

## [3.0.4] — 2026-03-05 (FROZEN)

**Status**: Frozen / deprecated in favor of Ansible installer.

### Fixed
- **VictoriaMetrics unhealthy**: promscrape config changed `localhost:9090` → `rhinometric-prometheus:9090`; created `config/loadtest_targets.json` (empty `[]`); added volume mount to `victoria-metrics` service.
- **AI Anomaly healthcheck**: replaced `CMD curl` with `CMD python -c "import urllib.request; ..."` since `python:3.11-slim` has no `curl` binary. Increased retries to 5, start_period to 45s.
- **Endpoint validation "invalid IP:0" bug**: `docker compose port` returns literal `"invalid IP:0"` for unpublished ports. Added `is_valid_hostport()` regex validator. Rewrote `verify_http_endpoints()` to only check Nginx published port and test internal services through proxy routes (`/`, `/api/health`, `/grafana/api/health`).
- **Rollback evidence preservation**: debug bundle now generated BEFORE any rollback action.

### Added
- `patch_configs_post_copy()` — applies config corrections after file copy to ensure tarball-shipped configs are always fixed.
- `is_valid_hostport()` — regex helper to validate `IP:PORT` strings from Docker.
- `print_license_apply_guide()` — step-by-step post-install license instructions.
- `--wait-for-license` CLI flag — pauses installer up to 5 min for license.key placement.
- Fingerprint persisted to `/opt/rhinometric/fingerprint.txt`.
- Credentials file includes license application guide.

### Known Issues (not resolved — by design)
- UI shows "Failed to fetch KPIs" / "Failed to load dashboards" after fresh install due to datasource provisioning gaps.
- Service initialization order beyond Docker `depends_on` healthchecks is not covered.
- No end-to-end functional verification (only HTTP status code checks).

---

## [3.0.3] — 2026-03-05

### Fixed
- `/etc/os-release` crash: replaced `. /etc/os-release` (source) with safe `grep` parsing (the script declares `readonly VERSION` which conflicted).
- Disk check crash on non-existent `INSTALL_DIR`: walks to existing parent directory.
- Removed obsolete `version: '3.8'` from docker-compose.yml (deprecated in Compose v2).
- Health check: full multi-phase approach (Phase 1: infra, Phase 2: all services via `docker inspect`, Phase 3: HTTP endpoints).

### Added
- Dynamic port detection via `docker compose port`.
- Auto-fix engine with up to 2 retry cycles.
- Comprehensive debug bundle with system info, container logs, dmesg OOM checks.
- Per-service diagnosis for unhealthy containers (OOM, permissions, disk).
- `--no-traces` flag to skip Jaeger.
- `--rollback-on-failure` flag (opt-in).
- Failure report with structured diagnosis.

### Introduced Bug
- `docker compose port` returns `"invalid IP:0"` for unpublished services — not caught by `-n` check → false critical failures. Fixed in v3.0.4.

---

## [3.0.2] — 2026-03-04

### Fixed
- False "INSTALLATION COMPLETED" when stack was actually unhealthy: added proper exit code tracking.
- Missing build context directories: installer now verifies all `context:` paths before `docker compose build`.

### Added
- Jaeger `/badger` permission fix (chown 10001:0).
- Full stack health check (all 21 services).
- Auto-fixer for common permission and directory issues.
- Rollback with `docker compose down -v` on failure.
- Debug bundle generation.

### Known Issues
- Rollback destroyed evidence before debug bundle (fixed in v3.0.3).
- Health check used hardcoded `localhost:3002`/`localhost:3000` which are not published to host (fixed in v3.0.3).

---

## [3.0.1] — 2026-03-04

### Fixed
- Installer reported success even when `docker compose up` failed (exit code was not checked).
- Build context directories not included in tarball.

---

## [3.0.0] — 2026-03-04

### Added
- Initial production installer (804 lines).
- System validation (OS, CPU, RAM, disk, Docker, ports).
- Machine fingerprint detection via `rhino-lic`.
- Ed25519 license validation with detailed status reporting.
- Secure credential generation (PostgreSQL, Redis, Grafana, Admin).
- Environment file generation with all service configs.
- Docker Compose stack startup with image pull retry.
- Basic health check (curl to console and Grafana).
- Credentials saved to `/opt/rhinometric/install-info.txt`.
- Interactive license path input with auto-detection.

---

*Maintained by: Release Engineering | Frozen: 2026-03-05*
