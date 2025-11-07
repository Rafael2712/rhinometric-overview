# 🚀 Rhinometric v2.5.0 - Production Deployment

Production-ready deployment configuration for Rhinometric monitoring platform.

## 📦 What's Included

This production deployment includes:

- ✅ **24 Services**: Grafana, Prometheus, Alertmanager, Loki, Tempo, PostgreSQL, Redis, 4 FastAPI services, and exporters
- ✅ **TLS/HTTPS**: Traefik reverse proxy with automatic Let's Encrypt certificates
- ✅ **Security**: JWT authentication, CORS restrictions, disabled /docs in production, secret management
- ✅ **Monitoring**: Service health checks, resource limits, retention policies, alerts via email
- ✅ **High Availability**: Restart policies, healthchecks, persistent volumes, backup procedures
- ✅ **Observability**: Metrics, logs, traces fully integrated with Grafana
- ✅ **Automation**: Smoke tests, automated backups, log rotation
- ✅ **Documentation**: Complete operations runbook

---

## 🏗️ Architecture

```
Internet (80/443)
     ↓
 [Traefik] → TLS termination, routing
     ↓
┌────────────────────────────────────┐
│   Rhinometric Internal Network     │
│                                    │
│  [Grafana] ← [Prometheus]          │
│      ↓          ↓                  │
│  [Loki]    [Alertmanager]          │
│      ↓          ↓                  │
│  [Tempo]   [Node Exporter]         │
│                ↓                   │
│  [PostgreSQL] [cAdvisor]           │
│      ↓                             │
│  [Redis]   [Blackbox]              │
│                                    │
│  [Dashboard Builder API] :8001     │
│  [AI Anomaly Detection]  :8085     │
│  [Report Generator]      :8086     │
│  [License Server]        :8090     │
└────────────────────────────────────┘
```

---

## ⚡ Quick Start

### 1. Prerequisites

- Linux server (Ubuntu 20.04+, RHEL 8+, Debian 11+)
- 8 CPU cores / 16GB RAM / 100GB SSD minimum
- Docker 24.0+ with Compose v2
- Domain with DNS pointing to server

### 2. Deploy

```bash
# Clone and navigate
cd /opt
git clone https://github.com/yourorg/rhinometric.git
cd rhinometric/deploy/prod

# Configure environment
cp .env.prod.example .env.prod
nano .env.prod  # Set DOMAIN, passwords, JWT secrets, SMTP settings

# Configure Docker logging
sudo cp logging/daemon.json /etc/docker/daemon.json
sudo systemctl restart docker

# Deploy all services
docker compose --env-file .env.prod -f docker-compose-prod.yml up -d

# Wait for services to start (2 minutes)
sleep 120

# Run smoke tests
bash scripts/smoke-test.sh
```

If all tests pass ✅, access Grafana at `https://yourdomain.com`

---

## 📁 Directory Structure

```
deploy/prod/
├── .env.prod.example           # Environment template (copy to .env.prod)
├── docker-compose-prod.yml     # Main orchestration file
├── README.md                   # This file
├── README-OPERATIONS.md        # Complete operations guide
│
├── traefik/
│   └── traefik.yml            # Reverse proxy + TLS config
│
├── prometheus/
│   ├── prometheus.yml         # Scrape configs for all services
│   └── alerts/
│       └── rhinometric.yml    # Alert rules (disk, memory, CPU, services)
│
├── alertmanager/
│   └── alertmanager.yml       # Email routing (critical/warning/ops)
│
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yml   # Prometheus, Loki, Tempo, PostgreSQL
│       └── dashboards/
│           └── dashboards.yml    # Auto-import dashboards
│
├── logging/
│   └── daemon.json            # Docker log rotation config
│
└── scripts/
    ├── smoke-test.sh          # Automated health checks
    └── backup.sh              # Daily backup script
```

---

## 🔐 Security Features

### Authentication & Authorization
- JWT tokens for all API endpoints
- Grafana: No anonymous access, no signups
- CORS restricted to configured origins
- `/docs` endpoints disabled in production

### TLS/HTTPS
- Automatic Let's Encrypt certificates via Traefik
- HTTP → HTTPS redirect
- Secure cookies, HSTS, CSP headers

### Secrets Management
- All secrets in `.env.prod` (not committed)
- 4 separate JWT secrets for services
- Strong password generation documented
- PostgreSQL/Redis authentication required

### Network Isolation
- Internal network for service-to-service communication
- Only ports 80/443 exposed to internet
- Traefik as single entry point

---

## 📊 Monitoring & Alerts

### Built-in Dashboards

1. **Rhinometric System Health** (Auto-provisioned)
   - Services status (24 services monitored)
   - Resource usage: CPU, RAM, Disk
   - Retention policies: Prometheus 15d/10GB, Loki 7d/5GB, Tempo 3d/2GB
   - Compaction activity

### Alert Types

| Severity | Trigger | Recipients | Example |
|----------|---------|-----------|---------|
| **Critical** | Service down >2min, Disk >90%, Memory >95% | `ALERT_EMAIL_CRITICAL` | PostgreSQL down |
| **Warning** | Disk >80%, Memory >85%, High latency | `ALERT_EMAIL_OPS` | Prometheus storage at 85% |

Alerts sent via email with professional HTML templates.

### Key Metrics

- **API Performance**: `http_requests_total`, `http_request_duration_seconds`
- **System Resources**: `node_cpu_seconds_total`, `node_memory_MemAvailable_bytes`, `node_filesystem_avail_bytes`
- **Services Health**: `up{job="<service>"}`, `probe_success`
- **Data Retention**: `prometheus_tsdb_storage_blocks_bytes`, `loki_ingester_bytes_received_total`

---

## 💾 Backup & Recovery

### Automated Backups

```bash
# Setup daily backups at 2 AM
crontab -e
# Add: 0 2 * * * /opt/rhinometric/deploy/prod/scripts/backup.sh
```

Backups include:
- All Docker volumes (prometheus, grafana, loki, tempo, postgres, redis, ai_models, reports)
- Configuration files (docker-compose, .env, prometheus, alertmanager, grafana)
- Metadata with checksums

Retention: 30 days (configurable via `BACKUP_RETENTION_DAYS`)

### Restore

See detailed restore procedures in [`README-OPERATIONS.md`](./README-OPERATIONS.md#backup--restore)

---

## 🛠️ Operations

### Daily Commands

```bash
# Start all services
docker compose --env-file .env.prod -f docker-compose-prod.yml up -d

# Stop all services
docker compose --env-file .env.prod -f docker-compose-prod.yml down

# View logs (follow mode)
docker compose logs -f

# Check status
docker compose ps

# Run health checks
bash scripts/smoke-test.sh

# Manual backup
bash scripts/backup.sh
```

### Service Management

```bash
# Restart single service
docker compose restart grafana

# Update service config
nano .env.prod  # Change variables
docker compose up -d --force-recreate grafana

# Scale API workers (edit .env.prod)
API_WORKERS=4  # was 2
docker compose restart dashboard-builder
```

### Resource Limits

Configured in `docker-compose-prod.yml`:

| Service | Memory | CPU |
|---------|--------|-----|
| Grafana | 1GB | 1.0 |
| Prometheus | 2GB | 2.0 |
| Loki | 1GB | 1.0 |
| APIs | 512MB each | 0.5 each |
| PostgreSQL | 512MB | 1.0 |
| Redis | 256MB | 0.3 |

Adjust in compose file if needed.

---

## 🧪 Testing

### Smoke Tests

The `smoke-test.sh` script validates:

✅ Health endpoints (8 services)  
✅ Metrics endpoints (6 services)  
✅ Grafana datasources  
✅ Dashboard creation  
✅ Alertmanager alerts  

Run after every deployment:
```bash
bash scripts/smoke-test.sh
```

Exit code 0 = success, 1 = failure with detailed errors.

---

## 📈 Retention Policies

### Prometheus
- **Time**: 15 days
- **Size**: 10GB
- **Compaction**: Every 10 minutes

### Loki
- **Retention**: 7 days
- **Max Size**: 5GB
- **Chunk Size**: 1MB

### Tempo
- **Retention**: 3 days
- **Max Size**: 2GB

### Docker Logs
- **Max Size**: 50MB per container
- **Max Files**: 5 files
- **Total per container**: 250MB

---

## 🔧 Troubleshooting

Common issues and solutions:

### Service Won't Start
```bash
# Check logs
docker compose logs <service>

# Common causes:
# - Port conflict: netstat -tulpn | grep <port>
# - Wrong credentials: Verify .env.prod
# - Memory limit: Increase mem_limit in compose file
```

### Alerts Not Sending
```bash
# Verify SMTP settings
echo $SMTP_HOST $SMTP_PORT $SMTP_USER

# Test Alertmanager
docker compose logs alertmanager
```

### Disk Space Full
```bash
# Check usage
docker system df -v

# Clean old images
docker image prune -a

# Reduce retention (edit .env.prod)
PROM_RETENTION_TIME=10d  # was 15d
docker compose restart prometheus
```

Full troubleshooting guide: [`README-OPERATIONS.md`](./README-OPERATIONS.md#troubleshooting)

---

## 📚 Documentation

- **[README-OPERATIONS.md](./README-OPERATIONS.md)**: Complete operations guide (prerequisites, deployment, monitoring, backup/restore, troubleshooting, rollback, security, performance tuning)
- **[.env.prod.example](./.env.prod.example)**: All environment variables with descriptions
- **[../../docs/](../../docs/)**: API documentation, architecture diagrams

---

## 🚀 Deployment Checklist

Before going to production:

- [ ] Server meets minimum requirements (8 cores, 16GB RAM, 100GB disk)
- [ ] Docker and Docker Compose installed
- [ ] DNS configured (A record pointing to server)
- [ ] `.env.prod` created with all secrets set (no CHANGEME values)
- [ ] `daemon.json` copied to `/etc/docker/daemon.json` and Docker restarted
- [ ] Services deployed: `docker compose up -d`
- [ ] Smoke tests passed: `bash scripts/smoke-test.sh`
- [ ] Grafana accessible at `https://yourdomain.com`
- [ ] Test alert sent and received via email
- [ ] Backup cron job configured: `0 2 * * * /path/to/backup.sh`
- [ ] Operations team trained on [`README-OPERATIONS.md`](./README-OPERATIONS.md)

---

## 📞 Support

- **Issues**: GitHub Issues
- **Email**: ops@yourcompany.com
- **Documentation**: `/docs` in repository
- **Version**: v2.5.0
- **Release Date**: June 2024

---

## 📝 License

See [LICENSE](../../LICENSE) file in repository root.

---

**Ready for production!** 🎉

For detailed operations procedures, see [README-OPERATIONS.md](./README-OPERATIONS.md)
