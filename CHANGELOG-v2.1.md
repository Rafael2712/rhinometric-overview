# ═══════════════════════════════════════════════════════════════════════════
#  RHINOMETRIC v2.1.0 ENTERPRISE - CHANGELOG
# ═══════════════════════════════════════════════════════════════════════════

## Version 2.1.0 - Enterprise Edition (October 2025)

### 🎯 Major Features

#### ✅ GUI-Based API Connectivity
- **API Proxy** (Node.js + Express) - Universal connector for external APIs
- Pre-configured APIs: CoinDesk (Bitcoin), GitHub Status, OpenWeather
- Redis caching with configurable TTL
- Prometheus metrics exposition
- Automatic URL encoding and error handling
- REST API for dynamic registration

#### ✅ Production-Grade Telemetry
- **OpenTelemetry Collector** replaces telemetrygen
- OTLP gRPC/HTTP receivers (ports 4319, 4320)
- Jaeger protocol support (ports 14250, 14268)
- Span enrichment with resource attributes
- Metrics generation from traces
- Export to Tempo and Prometheus

#### ✅ FastAPI License Server
- Complete rewrite from Flask to FastAPI
- Async/await architecture with asyncpg
- REST API: `/api/health`, `/api/licenses`, `/api/external-apis`
- Automatic OpenAPI documentation
- Prometheus metrics with fastapi-instrumentator
- Production-ready with uvicorn workers

#### ✅ One-Command Installation
- **Universal installer** (`install-v2.1.sh`) for macOS/Linux/WSL2
- Automatic OS detection
- Dependency verification
- Data directory setup
- Environment configuration
- Service deployment
- Health validation

#### ✅ Enhanced Observability Stack
- **Prometheus v2.1.yml** - 17 scrape jobs, 15s interval, external API integration
- **Loki v2.1.yml** - 7-day retention, optimized ingestion limits
- **Tempo v2.1.yml** - Metrics generator, service graphs, span metrics
- **Promtail v2.1.yml** - Docker service discovery, JSON log parsing

### 🔧 Technical Improvements

#### Resource Optimization
- **CPU**: 3.5 vCPUs (down from 4.9, -30%)
- **Memory**: 6 GB RAM (down from 8.8 GB, -32%)
- **Services**: 16 total (3 new: API Proxy, OTEL Collector, License Server v2)
- **Healthchecks**: 16/16 (100%, up from 75%)

#### Configuration Enhancements
- All services use bind mounts to `~/rhinometric_data_v2.1/`
- Fixed Docker image versions (no `latest` tags)
- Optimized resource limits per service
- Custom network `rhinometric_network_v21` (172.21.0.0/16)
- Enhanced healthcheck intervals and timeouts

#### Multi-Platform Support
- **macOS**: Data dir in `~/Library/Application Support/Rhinometric`
- **Linux**: Data dir in `~/rhinometric_data_v2.1`
- **WSL2**: Compatible with Docker Engine (no Desktop required)
- Portable shell scripts with `#!/usr/bin/env bash`

### 📊 Pre-Loaded Dashboards (Ready in v2.2.0)

Eight enterprise-grade Grafana dashboards planned:
1. System Overview - CPU, RAM, Disk, Network
2. Database Health - PostgreSQL metrics
3. Container Metrics - Docker stats via cAdvisor
4. API Monitoring - External API health
5. Logs Explorer - Aggregated logs with filters
6. Distributed Tracing - Service graph, latency
7. License Management - Active licenses, expiration
8. Alerting Dashboard - Active alerts, history

### 🐛 Bug Fixes

#### Resolved Issues from v2.0.0
- ✅ **json_exporter error 400** - Replaced with API Proxy
- ✅ **Empty dashboards** - Enhanced with proper datasource variables
- ✅ **No telemetry** - OpenTelemetry Collector with sample spans
- ✅ **No logs in Loki** - Fixed Promtail Docker socket access
- ✅ **License server crashes** - FastAPI with async support
- ✅ **macOS incompatibility** - Universal installer with OS detection
- ✅ **High CPU usage** - Optimized scrape intervals and resource limits
- ✅ **Missing healthchecks** - 100% coverage (16/16)

### 📦 New Files

#### Core Configuration
- `docker-compose-v2.1.0.yml` - Complete 16-service stack
- `config/prometheus-v2.1.yml` - Enhanced monitoring config
- `config/loki-v2.1.yml` - Log aggregation config
- `config/tempo-v2.1.yml` - Distributed tracing config
- `config/promtail-v2.1.yml` - Log collection config
- `config/otel-collector-config.yml` - Telemetry collector config
- `config/alertmanager.yml` - Alert routing config
- `config/blackbox.yml` - Endpoint probing config

#### Application Code
- `api-proxy/server.js` - Node.js API proxy (300+ lines)
- `api-proxy/package.json` - Dependencies
- `api-proxy/Dockerfile` - Container build
- `license-server-v2/main.py` - FastAPI application (250+ lines)
- `license-server-v2/requirements.txt` - Python dependencies
- `license-server-v2/Dockerfile` - Container build
- `init-db/init.sql` - PostgreSQL schema and sample data

#### Scripts & Tools
- `install-v2.1.sh` - Universal installer (400+ lines)
- `validate-v2.1.sh` - System validation script
- `create-package-v2.1.sh` - Package creator with checksums

#### Documentation
- `README-v2.1.md` - Complete user guide
- `CHANGELOG-v2.1.md` - This file
- `INSTALL-GUIDE-v2.1.txt` - Installation instructions (auto-generated)

### 🔄 Breaking Changes

#### Removed Services
- `telemetrygen` - Replaced by OpenTelemetry Collector
- `json_exporter` - Replaced by API Proxy
- `license-server` (Flask) - Replaced by `license-server-v2` (FastAPI)

#### Port Changes
- OTLP gRPC: `4317` → `4319` (to avoid conflicts)
- OTLP HTTP: `4318` → `4320` (to avoid conflicts)
- API Proxy: New service on port `8090`

#### Configuration Changes
- Prometheus config: `prometheus-saas.yml` → `prometheus-v2.1.yml`
- Loki config: Default → `loki-v2.1.yml`
- Tempo config: Default → `tempo-v2.1.yml`
- Promtail config: Default → `promtail-v2.1.yml`
- Data directory: `~/rhinometric_data/` → `~/rhinometric_data_v2.1/`

### 📈 Performance Metrics

#### Startup Time
- Cold start: ~90 seconds (16 services)
- Warm start: ~30 seconds (with cached images)

#### Resource Usage (Measured)
- Idle: 2.8 vCPUs, 5.2 GB RAM
- Under load: 3.5 vCPUs, 6.0 GB RAM
- Disk usage: ~15 GB (with 7-day retention)

#### Healthcheck Coverage
- v2.0.0: 12/16 services (75%)
- v2.1.0: 16/16 services (100%)

### 🔐 Security

#### Default Credentials
- PostgreSQL: `rhinometric` / `rhinometric`
- Redis: `rhinometric`
- Grafana: `admin` / `admin`

**⚠️ WARNING**: Change all passwords in `.env` before production deployment!

#### Network Security
- Custom bridge network: `172.21.0.0/16`
- Only essential ports exposed to host
- Internal service communication on private network

### 📊 Compatibility Matrix

| Platform | Docker Version | Status |
|----------|----------------|--------|
| macOS 13+ (Intel) | 20.10+ | ✅ Tested |
| macOS 13+ (M1/M2) | 20.10+ | ✅ Tested |
| Ubuntu 22.04 | 20.10+ | ✅ Tested |
| Ubuntu 24.04 | 20.10+ | ✅ Tested |
| Debian 11+ | 20.10+ | ✅ Compatible |
| Windows WSL2 (Ubuntu) | 20.10+ | ✅ Tested |
| Windows Docker Desktop | 4.0+ | ✅ Compatible |

### 🛣️ Roadmap to v2.2.0

#### Planned Features
- [ ] React/Svelte GUI for API connector
- [ ] Enhanced Grafana dashboards (8 total)
- [ ] Alert rules for common scenarios
- [ ] SSL/TLS support with Let's Encrypt
- [ ] Backup/restore scripts
- [ ] High availability mode (3+ replicas)
- [ ] Kubernetes deployment option

### 📝 Migration Guide (v2.0.0 → v2.1.0)

#### Step 1: Backup v2.0.0 Data

```bash
cd ~/mi-proyecto/infrastructure/mi-proyecto
docker compose -f docker-compose-rebuilt.yml down
tar -czf ~/rhinometric_v2.0.0_backup.tar.gz ~/rhinometric_data/
```

#### Step 2: Install v2.1.0

```bash
# Extract v2.1.0 package
tar -xzf rhinometric-trial-v2.1.0-universal.tar.gz
cd rhinometric-trial-v2.1.0-universal

# Run installer
./install-v2.1.sh
```

#### Step 3: Migrate Data (Optional)

```bash
# Copy Grafana dashboards
cp -r ~/rhinometric_data/grafana/* ~/rhinometric_data_v2.1/grafana/

# Copy PostgreSQL data
cp -r ~/rhinometric_data/postgres/* ~/rhinometric_data_v2.1/postgres/

# Restart services
docker compose -f docker-compose-v2.1.0.yml restart
```

### 🙏 Acknowledgments

- Grafana Labs - Grafana, Loki, Tempo, Promtail
- Prometheus - Monitoring and alerting
- OpenTelemetry - Observability standards
- Docker - Containerization platform
- FastAPI - Modern Python web framework

### 📄 License

Rhinometric v2.1.0 Enterprise Edition - Trial License

---

**For questions or support, check the documentation or run `./validate-v2.1.sh`**
