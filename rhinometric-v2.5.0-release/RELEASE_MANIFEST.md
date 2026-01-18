# Rhinometric v2.5.0 - Release Manifest

**Build Date**: 2025-12-30  
**Release Type**: MVP Production Ready  
**Platform**: Linux x86_64 (Ubuntu 22.04 LTS)

---

## 📦 Package Contents

### Core Files

| File | Size | Description |
|------|------|-------------|
| `docker-compose-v2.5.0-core.yml` | ~15 KB | Stack definition (17 services) |
| `.env.example` | 500 B | Environment variables template |
| `README.md` | 3 KB | Quick start guide |

### Scripts

| File | Purpose |
|------|---------|
| `scripts/install-rhinometric.sh` | Automated installer with validation |

### Documentation

| File | Content |
|------|---------|
| `docs/INSTALLATION_GUIDE.md` | Complete installation & troubleshooting guide |
| `docs/AWS_AMI_BACKUP_INFO.txt` | AWS backup reference (for internal use) |

### Grafana Dashboards

| Dashboard | File | Metrics |
|-----------|------|---------|
| **05 - Docker Containers** | `05-docker-containers.json` | CPU, RAM, Network, Disk I/O per container |
| **06 - System Monitoring** | `06-system-monitoring.json` | Host CPU, RAM, Disk, Load Average |
| **07 - License Status** | `07-license-status.json` | Active licenses, expiry dates |
| **08 - Stack Health** | `08-stack-health.json` | All 17 services healthchecks |

### Configuration

| File | Service | Notes |
|------|---------|-------|
| `config/prometheus-v2.2.yml` | Prometheus | Scrape configs for all targets |
| `config/alertmanager.yml` | Alertmanager | Alert routing rules |

---

## 🚀 Services Included

### Application Stack (17 containers)

**Data Layer**:
- `postgres:15.10` - PostgreSQL database (licenses, users)
- `redis:7.2` - Redis cache (sessions, temp data)

**Observability Core**:
- `prom/prometheus:v2.53.0` - Metrics collection & storage
- `grafana/grafana:10.4.0` - Dashboards & visualization
- `grafana/loki:3.0.0` - Log aggregation
- `jaegertracing/all-in-one:1.57.0` - Distributed tracing
- `prom/alertmanager:v0.27.0` - Alert management

**Exporters & Collectors**:
- `prom/node-exporter:v1.7.0` - Host metrics
- `gcr.io/cadvisor/cadvisor:v0.49.1` - Container metrics
- `grafana/promtail:3.0.0` - Log shipper
- `otel/opentelemetry-collector:0.96.0` - Telemetry collection

**Rhinometric Application**:
- `rhinometric-console-frontend:latest` - React UI (Nginx)
- `rhinometric-console-backend:latest` - FastAPI Gateway
- `rhinometric-license-server-v2:latest` - License validator
- `rhinometric-ai-anomaly:latest` - ML anomaly detector

**Infrastructure**:
- `nginx:1.25-alpine` - Reverse proxy
- `alpine:latest` - Backup service

---

## ✅ Validation Tests Completed

| Test | Status | Details |
|------|--------|---------|
| **Reinicio Completo** | ✅ PASS | Recovery time: 43s, all services healthy |
| **Stress Test (3x load)** | ✅ PASS | Peak RAM: 47%, no OOM kills |
| **Network Isolation** | ✅ PASS | Platform operational without internet |
| **Security Baseline** | ✅ PASS | All passwords secured, .env configured |

---

## 🔧 Tested Configurations

### Hardware Profile

| Spec | Tested Value | Min Required | Status |
|------|--------------|--------------|--------|
| vCPU | 2 cores | 4 cores | ⚠️ Works but not recommended |
| RAM | 4 GB | 8 GB | ⚠️ Works with tuning |
| Disk | 29 GB used | 150 GB | ✅ Room for growth |
| Network | 100 Mbps | 100 Mbps | ✅ Sufficient |

**Recommendation**: Use 4+ vCPU and 8+ GB RAM for production.

### OS Tested

- ✅ Ubuntu 22.04 LTS (AWS EC2 t3.medium)
- ✅ Docker 24.0.7
- ✅ Docker Compose v2.29.7

---

## 🐛 Known Issues

1. **Anomalías HTTP en Grafana Explore**:
   - **Issue**: Métricas `http_latency_p95/p99` no aparecen como nombres directos
   - **Workaround**: Usar query completa: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`
   - **Impact**: Low (dashboards funcionan correctamente)

2. **Frontend URL Reset**:
   - **Issue**: Después de `docker compose down/up`, frontend puede revertir a localhost URLs
   - **Workaround**: Rebuild frontend: `docker compose build --no-cache rhinometric-console-frontend`
   - **Impact**: Low (solo en demos)

---

## 📊 Performance Baseline

Based on AWS EC2 t3.medium testing:

| Metric | Value |
|--------|-------|
| **Memory Usage (idle)** | 1.2 GB / 3.8 GB (31%) |
| **Memory Usage (peak)** | 1.8 GB / 3.8 GB (47%) |
| **Prometheus Metrics** | 1425+ time series |
| **Prometheus Targets** | 11 active endpoints |
| **Grafana Dashboards** | 7 pre-configured |
| **Container Startup Time** | ~60 seconds (cold start) |
| **Platform Recovery Time** | 43 seconds (warm restart) |

---

## 🔐 Security Notes

- All default passwords are replaced during installation
- Credentials stored in `/opt/rhinometric/CREDENCIALES.txt` (chmod 600)
- PostgreSQL, Redis, Grafana use secure passwords
- Services without auth (Prometheus, Alertmanager) - recommend firewall

**Recommendation**: Deploy behind reverse proxy with TLS for internet exposure.

---

## 📝 Release Notes v2.5.0

### New Features
- ✅ Automated installer with system validation
- ✅ AI-powered anomaly detection with ML models
- ✅ Distributed tracing with Jaeger integration
- ✅ License management system
- ✅ 7 pre-configured production dashboards

### Improvements
- ✅ cAdvisor metrics fixed for systemd environments
- ✅ Dashboard queries optimized for Docker containers
- ✅ Secure credential generation built-in
- ✅ Healthchecks on all 17 services

### Breaking Changes
- Docker Compose v2 required (v1 deprecated)
- Minimum RAM increased to 8 GB (was 4 GB)

---

## 📋 Installation Checklist

Before installation:
- [ ] Ubuntu 22.04 LTS installed
- [ ] Docker 24.0+ installed
- [ ] 8+ GB RAM available
- [ ] 150+ GB disk space
- [ ] Ports 3000-3002, 5000, 5432, 6379, 8085, 8105, 9090-9093, 3100, 16686 free
- [ ] Root/sudo access

Post-installation:
- [ ] All 17 containers show as `healthy`
- [ ] Grafana accessible on port 3000
- [ ] Console accessible on port 3002
- [ ] Credentials saved in password manager
- [ ] Backup scheduled

---

**Build Hash**: `sha256:24cab359e2f8a1c7d36690c9df94fff6db8b5f2`  
**Git Tag**: `v2.5.0-mvp-20251230`  
**Validated By**: MVP Testing Team  
**Support Until**: 2026-12-30
