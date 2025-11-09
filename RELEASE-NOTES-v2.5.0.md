# Rhinometric v2.5.0 - Release Notes

**Release Date:** 2024-12-XX  
**Status:** Production Ready + Demo Appliance  
**GitHub:** https://github.com/Rafael2712/mi-proyecto/releases/tag/v2.5.0

---

## ��� Overview

Rhinometric v2.5.0 introduces **production-hardened deployment** with TLS, comprehensive monitoring, operational automation, and a **self-contained OVA demo appliance** for instant evaluation.

### Key Highlights

- ✅ **Production Deployment** (`deploy/prod/`) - Traefik TLS, resource limits, automatic provisioning
- ✅ **Demo Appliance** (`deploy/demo/`) - Self-contained stack with auto-seeding for immediate data visibility
- ✅ **Dashboard Builder UI** - Create Grafana dashboards without YAML/PromQL (React + Node.js API)
- ✅ **OVA Packaging** - Packer-based VirtualBox/VMware appliance for zero-config demos
- ✅ **Operational Scripts** - Smoke tests, backups, updates, support bundles

---

## ��� What's New

### 1. Production Deployment (`deploy/prod/`)

Complete production-ready stack with 15 services:

**Infrastructure:**
- **Traefik 2.10** - Reverse proxy with Let's Encrypt TLS, HSTS headers
- **HAProxy** (optional) - Load balancing for HA setups
- **PostgreSQL 15** + **Redis 7** - Persistent storage and caching
- **Nginx** - Static assets and reverse proxy

**Monitoring & Observability:**
- **Prometheus 2.48** - Metrics (15d retention, 10GB limit)
- **Grafana 10.2** - Dashboards with auto-provisioning
- **Loki 2.9** - Log aggregation (30d retention)
- **Tempo 2.3** - Distributed tracing
- **Alertmanager 0.26** - Email alerts with HTML templates
- **Exporters** - node-exporter, cAdvisor, blackbox-exporter

**Rhinometric Services:**
- **AI Anomaly Detection** - ML-based anomaly detection
- **Report Generator** - PDF/Excel report generation
- **Dashboard Builder** - No-code dashboard creation

**Configuration Files (14):**
```
deploy/prod/
├── docker-compose-prod.yml      # 15 services, resource limits, healthchecks
├── .env.prod.example            # Template con variables requeridas
├── traefik/                     # TLS, security headers (HSTS, CSP, XFO)
├── prometheus/                  # 15d retention, 8 scrape jobs, alerting rules
├── grafana/provisioning/        # Datasources + dashboards auto-import
├── alertmanager/                # SMTP config, HTML email templates
├── scripts/                     # smoke-test.sh, backup.sh, healthcheck.sh, deploy.sh
├── README.md                    # Quick start y troubleshooting
└── README-OPERATIONS.md         # Operational procedures
```

**Operational Features:**
- **Smoke Tests** - 8-check validation (containers, endpoints, datasources, metrics)
- **Automated Backups** - Volume backup con SHA256 checksums, 7-day retention
- **Health Checks** - All services with liveness/readiness probes
- **Deploy Script** - Zero-downtime deployment workflow

---

### 2. Demo Appliance (`deploy/demo/`)

Self-contained demo environment optimized for VirtualBox OVA packaging:

**Key Differences vs Production:**
- **Reduced Retention** - Prometheus 3d, Loki 7d, Tempo 3d
- **Demo Credentials** - admin/rhinometric_demo (hardcoded)
- **Auto-Seeding** - `anomaly-seed.sh` generates metrics every 90s
- **Self-Signed TLS** - Quick setup without cert management
- **No Resource Limits** - Adapts to available hardware

**Configuration Files (20):**
```
deploy/demo/
├── docker-compose-demo.yml      # 15 services, demo config
├── .env.demo                    # Demo credentials
├── grafana/provisioning/
│   ├── datasources/             # Prometheus (UID: prometheus), Loki, Tempo
│   └── dashboards/
│       └── json/                # 3 pre-built dashboards (AI, System, App)
├── prometheus/prometheus.yml    # 8 scrape jobs including AI metrics
├── alertmanager/                # HTML email template (demo SMTP)
├── loki/config.yml              # 7d retention
├── tempo/tempo.yml              # OTLP receivers (HTTP/gRPC)
├── traefik/                     # Self-signed TLS, redirects
├── blackbox/blackbox.yml        # HTTP/TCP/ICMP probes
├── scripts/
│   ├── anomaly-seed.sh          # Auto-seeding (CPU, latency, memory, errors, disk)
│   ├── smoke-test.sh            # 8-check validation
│   ├── backup.sh                # Volume backup + checksums
│   ├── update.sh                # Safe update workflow
│   ├── support-bundle.sh        # Diagnostic bundle collection
│   └── first-boot.sh            # OVA first-boot initialization
└── README.md                    # Quick start, operations, troubleshooting
```

**Auto-Seeding Feature:**
- Continuous POST to AI Anomaly API every 90s
- Metrics: `node_cpu_usage`, `api_latency`, `memory_pressure`, `error_rate`, `disk_io_wait`
- Ensures dashboards show data immediately (no "No data" placeholders)

---

### 3. Dashboard Builder (`tools/dashboard-builder/`)

**UI sin YAML** para crear dashboards de Grafana visualmente.

**Backend API (Node.js/Express) - Port 8001:**
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /templates` - Lista de templates disponibles (AI Anomaly, System, App Performance)
- `POST /create` - Crea dashboard en Grafana vía API

**Frontend UI (React standalone) - Port 3001:**
- Wizard: Select template → Custom title → Create
- React via CDN (no build step, standalone HTML)
- Direct integration with backend API
- Responsive design with success/error alerts

**Templates Incluidos:**
1. **AI Anomaly Detection** - Detections/24h, active count, trained models, real-time graph
2. **System Overview** - CPU, memory, disk, network from node-exporter
3. **App Performance** - Req/sec, error rate, latency, percentiles (p50/p95/p99)

**Integration:**
- Incluido en `docker-compose-demo.yml` con env vars preconfiguradas
- Acceso vía Traefik: `https://demo.rhinometric.local/builder`

---

### 4. OVA Build System (`packer/`)

Packer template para generar OVA de VirtualBox/VMware con Ubuntu 22.04.

**Características:**
- **Base Image:** Ubuntu 22.04.3 LTS Server
- **Resources:** 4 vCPU, 8GB RAM, 60-80GB disk (thin provisioned)
- **Builders:** VirtualBox + VMware
- **Provisioners:**
  - Docker 24+ y Docker Compose v2 installation
  - UFW firewall configured (22, 80, 443, 3000, 8001, 9090)
  - Deploy/demo files copied to `/opt/rhinometric`
  - First-boot systemd service for auto-start
- **Export:** OVA format, target size <4.5GB

**Build Command:**
```bash
cd packer
packer build ubuntu2204-rhinometric.json
# Output: output-virtualbox-iso/rhinometric-demo.ova
```

**First Boot Behavior:**
1. Generate self-signed certs if missing
2. `docker compose up -d` all 15 services
3. Start `anomaly-seed.sh` in background
4. Display access info (Grafana URL, credentials)

**VM Specs:**
- **CPU:** 4 cores
- **RAM:** 8GB
- **Disk:** 80GB thin (actual size ~10GB after build)
- **Network:** Bridged adapter (DHCP)
- **OS:** Ubuntu 22.04.3 LTS
- **User:** rhinouser / rhinometric (sudo enabled)

---

### 5. Dashboards & Grafana Provisioning

**3 Pre-built Dashboards (JSON):**

#### AI Anomaly Detection (`rhinometric-ai-anomaly`)
- **Panels:**
  - Anomalías Detectadas (24h) - `increase(rhinometric_anomaly_detections_total[24h])`
  - Anomalías Activas - `rhinometric_anomaly_active_count`
  - Modelos Entrenados - `rhinometric_anomaly_models_trained`
  - Detecciones en Tiempo Real - `rate(rhinometric_anomaly_detections_total[5m])`

#### System Overview (`rhinometric-system-overview`)
- **Panels:**
  - CPU Usage - `100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
  - Memory Usage - `100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))`
  - Disk Usage - `100 - ((node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100)`
  - Network Traffic - `irate(node_network_*_bytes_total[5m])`

#### App Performance (`rhinometric-app-performance`)
- **Panels:**
  - Requests/sec - `sum(rate(http_requests_total[5m]))`
  - Error Rate - `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100`
  - Avg Latency - `avg(http_request_duration_seconds)`
  - Percentiles - `histogram_quantile(0.50|0.95|0.99, rate(http_request_duration_seconds_bucket[5m]))`

**Auto-Provisioning:**
- Datasources: Prometheus (UID: prometheus, default), Loki, Tempo, Alertmanager
- Dashboards: Auto-import from `/etc/grafana/provisioning/dashboards/json`
- All dashboards editable after creation

---

## ��� Configuration & Setup

### Production Deployment

```bash
# 1. Clone repository
git clone https://github.com/Rafael2712/mi-proyecto.git
cd mi-proyecto/deploy/prod

# 2. Configure environment
cp .env.prod.example .env.prod
nano .env.prod
# Set: DOMAIN, SMTP_*, JWT_SECRET, passwords

# 3. Deploy
bash scripts/deploy.sh

# 4. Verify
bash scripts/smoke-test.sh
```

**Required Environment Variables:**
- `DOMAIN` - Your domain (e.g., rhinometric.example.com)
- `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` - Email alerts
- `JWT_SECRET` - JWT signing key (generate with `openssl rand -hex 32`)
- `POSTGRES_PASSWORD` - PostgreSQL password
- `GRAFANA_ADMIN_PASSWORD` - Grafana admin password

---

### Demo Appliance (Local Development)

```bash
# 1. Clone repository
git clone https://github.com/Rafael2712/mi-proyecto.git
cd mi-proyecto/deploy/demo

# 2. Generate certs
cd traefik/certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/C=US/ST=Demo/L=Demo/O=Rhinometric/CN=rhinometric-demo.local"
cd ../..

# 3. Start stack
docker compose -f docker-compose-demo.yml up -d

# 4. Auto-seed data (optional, recommended)
bash scripts/anomaly-seed.sh > /tmp/seed.log 2>&1 &

# 5. Verify
bash scripts/smoke-test.sh
```

**Access:**
- Grafana: http://localhost:3000 (admin / rhinometric_demo)
- Dashboard Builder: http://localhost:3001
- Prometheus: http://localhost:9090
- AI Anomaly API: http://localhost:8085

---

### OVA Import & Usage

```bash
# 1. Download OVA from releases
wget https://github.com/Rafael2712/mi-proyecto/releases/download/v2.5.0/rhinometric-demo-v2.5.0.ova

# 2. Import to VirtualBox
VBoxManage import rhinometric-demo-v2.5.0.ova

# 3. Start VM
VBoxManage startvm "Rhinometric Demo Appliance"

# 4. Wait for first-boot (~3-5 min)
# VM will display access info on console

# 5. Access from host
https://<VM_IP>:3000  (Grafana)
http://<VM_IP>:3001   (Dashboard Builder)
```

**VM Credentials:**
- **SSH:** rhinouser / rhinometric
- **Grafana:** admin / rhinometric_demo

---

## ��� Metrics & Monitoring

### Prometheus Targets (8 jobs)

1. `prometheus` - Prometheus self-monitoring
2. `grafana` - Grafana metrics
3. `node-exporter` - System metrics (CPU, RAM, disk)
4. `cadvisor` - Docker container metrics
5. `blackbox` - Endpoint probes
6. `rhinometric-ai-anomaly` - AI service metrics
7. `rhinometric-report-generator` - Report service metrics
8. `rhinometric-dashboard-builder` - Dashboard Builder API metrics

### Key Metrics

**AI Anomaly Detection:**
- `rhinometric_anomaly_detections_total` - Total anomalies detected (counter)
- `rhinometric_anomaly_active_count` - Active anomalies (gauge)
- `rhinometric_anomaly_models_trained` - Number of trained models (gauge)

**Dashboard Builder:**
- `dashboard_builder_requests_total` - Total API requests (labels: method, route, status)
- `dashboard_builder_request_duration_seconds` - Request duration histogram

### Alerting Rules

**Configured in `deploy/prod/prometheus/alerts.yml`:**
- `InstanceDown` - Service unreachable for >2 minutes
- `HighCpuUsage` - CPU >80% for >5 minutes
- `HighMemoryUsage` - Memory >90% for >5 minutes
- `DiskSpaceWarning` - Disk >80% used
- `HighErrorRate` - HTTP 5xx errors >5% for >2 minutes

---

## ��� Testing & Validation

### E2E Test Plan

Comprehensive test suite covering:
1. **Demo Stack** - Initialization, smoke test, Grafana access, AI data, Dashboard Builder, operational scripts (7 tests)
2. **Production Stack** - Config validation, smoke test, alerts, backup & restore (4 tests)
3. **OVA Build** - Packer validation, OVA build, VM import, smoke test, acceptance criteria (5 tests)

**Total: 16 tests** - See `docs/testing/E2E-TEST-PLAN.md` for details

**Quick Smoke Test:**
```bash
cd deploy/demo
bash scripts/smoke-test.sh

# Output:
# ✓ Todos los contenedores healthy
# ✓ Grafana :3000
# ✓ Prometheus :9090
# ✓ Todos los targets UP
# ✓ Datasource Prometheus (UID: prometheus)
# ✓ Métricas AI presentes
# ✓ Disco <80%
# ✓ Volúmenes creados
# ✓ Red rhinometric activa
# ✓ Smoke test PASSED
```

---

## ��� Documentation

### New Documentation

- **`deploy/prod/README.md`** - Production deployment guide
- **`deploy/prod/README-OPERATIONS.md`** - Operational procedures (backup, monitoring, troubleshooting)
- **`deploy/demo/README.md`** - Demo appliance guide
- **`docs/ova/OVA-README.md`** - OVA user manual (245 lines)
- **`docs/ova/BUILD-OVA.md`** - OVA build process (380 lines)
- **`docs/testing/E2E-TEST-PLAN.md`** - Comprehensive E2E test plan (600+ lines)
- **`tools/dashboard-builder/README.md`** - Dashboard Builder documentation

### Updated Documentation

- **`README.md`** - Updated with v2.5.0 features and links
- **API Documentation** - Updated with Dashboard Builder endpoints

---

## ��� Migration Guide

### From v2.1.0 to v2.5.0

**Breaking Changes:**
- None - Fully backward compatible

**New Features Available:**
1. Dashboard Builder UI (:3001) - Optional, can be disabled if not needed
2. OVA packaging - For demo/evaluation purposes only
3. Enhanced operational scripts - Existing scripts still work

**Migration Steps:**
```bash
# 1. Backup existing data
docker compose exec postgres pg_dump -U postgres > backup.sql

# 2. Pull latest changes
git pull origin main

# 3. Review new environment variables
diff .env.prod .env.prod.example

# 4. Deploy with zero downtime
bash deploy/prod/scripts/deploy.sh
```

---

## ��� Security

### Improvements in v2.5.0

1. **TLS Enforcement** - Traefik auto-redirect HTTP → HTTPS, HSTS headers
2. **Security Headers** - CSP, X-Frame-Options, X-Content-Type-Options
3. **JWT Secrets** - Environment-based (no hardcoded keys)
4. **Password Management** - All passwords via .env (template provided)
5. **Resource Limits** - CPU/memory limits prevent DoS
6. **Health Checks** - Liveness/readiness probes for all services
7. **Firewall Rules** - UFW configured in OVA (only required ports open)

### Security Notes

**Production:**
- Use Let's Encrypt for TLS certificates (configured in Traefik)
- Rotate JWT secrets regularly
- Enable fail2ban for SSH brute-force protection
- Configure database backups to encrypted storage
- Use strong passwords (minimum 16 characters)

**Demo/OVA:**
- Self-signed certificates (NOT for production)
- Hardcoded credentials (admin/rhinometric_demo) - Change after import
- No firewall by default (configure UFW after import)

---

## ��� Known Issues & Limitations

### Demo Appliance

1. **"No data" in AI dashboard** - Requires `anomaly-seed.sh` running for 2+ minutes
2. **VM import size** - OVA is ~4GB, requires ~10GB disk after import
3. **Network config** - Bridged adapter may require manual IP configuration on some hypervisors

### Production

1. **Traefik TLS** - Requires DNS pointing to server for Let's Encrypt validation
2. **SMTP alerts** - Requires valid SMTP credentials, test with `docker stop rhinometric-grafana`
3. **High availability** - Current setup is single-node, HA requires HAProxy + multi-node setup

### Dashboard Builder

1. **Limited templates** - Only 3 templates available (AI, System, App), more to be added
2. **No PromQL validation** - Custom queries not validated before creation
3. **CORS** - Frontend requires backend on same domain or CORS configured

---

## ��️ Troubleshooting

### Common Issues

#### "No data" en dashboards
```bash
# Verificar Prometheus targets
curl http://localhost:9090/api/v1/targets

# Iniciar auto-seeding
cd deploy/demo
bash scripts/anomaly-seed.sh > /tmp/seed.log 2>&1 &

# Esperar 2 min y refrescar dashboard
```

#### Containers unhealthy
```bash
# Ver logs del servicio
docker logs rhinometric-grafana-demo

# Reiniciar servicio
docker restart rhinometric-grafana-demo

# Ejecutar smoke test
bash scripts/smoke-test.sh
```

#### Grafana datasource error
```bash
# Verificar UID
curl -s -u admin:rhinometric_demo \
  http://localhost:3000/api/datasources/uid/prometheus | jq '.'

# Re-provision
docker restart rhinometric-grafana-demo
```

#### Dashboard Builder CORS error
```bash
# Verificar backend
curl http://localhost:8001/health

# Verificar frontend
curl http://localhost:3001

# Revisar logs
docker logs rhinometric-dashboard-builder-demo
```

---

## ��� Changelog Summary

### Added

- Production deployment stack (`deploy/prod/`) with 14 files
- Demo appliance stack (`deploy/demo/`) with 20 files
- Dashboard Builder UI and API (`tools/dashboard-builder/`)
- 3 pre-built Grafana dashboards (AI Anomaly, System, App Performance)
- Packer OVA build template for VirtualBox/VMware
- Operational scripts (smoke-test, backup, update, support-bundle)
- Comprehensive documentation (6 new docs, 1,800+ lines)
- E2E test plan with 16 tests

### Changed

- Prometheus retention: 3d (demo) vs 15d (prod)
- Loki retention: 7d (demo) vs 30d (prod)
- Grafana datasource UIDs: standardized to "prometheus" for auto-provisioning
- Docker Compose: v2 syntax with healthchecks and resource limits

### Fixed

- Grafana provisioning: datasources now auto-import on first boot
- Prometheus targets: all services properly labeled for scraping
- Alertmanager: HTML email templates properly rendered
- Traefik: TLS redirect and security headers working

---

## ��� Credits

**Developed by:** Rafael2712  
**Repository:** https://github.com/Rafael2712/mi-proyecto  
**License:** [Specify License]  
**Documentation:** See `/docs` folder for comprehensive guides

---

## ��� Support

- **Issues:** https://github.com/Rafael2712/mi-proyecto/issues
- **Discussions:** https://github.com/Rafael2712/mi-proyecto/discussions
- **Email:** [Specify support email if available]

---

## ��� Roadmap v2.6.0

- [ ] High Availability (HA) support with HAProxy + multi-node
- [ ] Additional Dashboard Builder templates (Kubernetes, MySQL, Redis)
- [ ] Custom PromQL query builder in Dashboard Builder UI
- [ ] Automated OVA build in CI/CD pipeline
- [ ] Ansible playbooks for production deployment
- [ ] Grafana Cloud integration (optional)
- [ ] Multi-tenancy support

---

**Thank you for using Rhinometric v2.5.0!** ���

For feedback, issues, or contributions, visit our [GitHub repository](https://github.com/Rafael2712/mi-proyecto).

---

**Release Notes Generated:** $(date +%Y-%m-%d)  
**Version:** 2.5.0  
**Build:** production-ready + demo-appliance

---

## ��� BRANDING & UX

### Identidad Corporativa

Rhinometric v2.5.0 implementa branding consistente en todos los componentes:

**Elementos Visuales:**
- Logo corporativo con gradientes azul petróleo (#1e5a7d) y azul acento (#2d8ab8)
- Tipografía: Inter (sistema), Courier New (código)
- Tema dark con acentos corporativos en alertas y estados

**Landing Page:**
- Página de bienvenida moderna con glassmorphism
- Credenciales demo visibles para acceso rápido
- Links directos a servicios principales
- Responsive design (móvil/tablet/desktop)

**Grafana Customization:**
- Título de instancia: "Rhinometric Enterprise"
- Estructura de carpetas con prefijo "RHINOMETRIC /"
- CSS personalizado con colores corporativos
- Footer branded en todos los dashboards
- Headers HTTP con X-Powered-By corporativo

**Consola VM (MOTD):**
- Banner ASCII "RHINOMETRIC ENTERPRISE" al login SSH
- Información dinámica de IP y servicios
- Comandos útiles pre-listados
- Documentación embebida en prompt

**Emails de Alertas:**
- Template HTML profesional con logo
- Badges de severidad con colores corporativos
- Footer: "Rhinometric Enterprise v2.5.0"
- Firma automática en todos los emails

**Traefik Middleware:**
- Headers de seguridad branded
- Páginas de error 502/503/504 personalizadas
- Routing consistente (/grafana, /builder, /prometheus)

**Nginx Landing Server:**
- Sirve landing page + docs estáticos
- Error pages branded (502.html, 404.html)
- Health endpoint: `/health`
- Gzip habilitado para performance

### Variables de Configuración

Todas configurables vía `.env.demo`:

```bash
RHINO_BRAND_NAME=Rhinometric Enterprise
RHINO_VERSION=v2.5.0
RHINO_DOMAIN=localhost
RHINO_TAGLINE=Observabilidad On-Premise con IA Local
GF_INSTANCE_NAME=${RHINO_BRAND_NAME}
SMTP_FROM_NAME=Rhinometric Enterprise
```

**Sin IPs hardcodeadas:** Todo usa `${RHINO_DOMAIN}` o IP dinámica vía `hostname -I`.

### Archivos de Branding

```
deploy/demo/branding/
├── html/
│   ├── index.html (214 líneas - landing page)
│   └── error.html (56 líneas - error pages)
├── css/
│   └── rhinometric-theme.css
└── logos/
    └── (placeholder para SVG)

deploy/demo/grafana/
├── grafana.ini (branding config)
└── provisioning/branding/
    └── rhinometric-theme.css

deploy/demo/alertmanager/
└── email-template.html (100 líneas HTML)

packer/
└── 99-rhinometric-motd (banner ASCII)
```

### Testing de Branding

```bash
# 1. Verificar landing page
curl http://localhost | grep "RHINOMETRIC"

# 2. Verificar headers Grafana
curl -I http://localhost:3000 | grep "X-Powered-By"

# 3. Verificar MOTD (en VM)
ssh rhinouser@<IP>  # Debe mostrar banner

# 4. Verificar email template
cat deploy/demo/alertmanager/email-template.html | grep "Rhinometric"
```

