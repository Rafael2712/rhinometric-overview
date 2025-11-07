# 🚀 Rhinometric v2.5.0 - Production Operations Guide

Complete operations runbook for production deployment and maintenance.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Deployment](#initial-deployment)
3. [Daily Operations](#daily-operations)
4. [Monitoring](#monitoring)
5. [Backup & Restore](#backup--restore)
6. [Troubleshooting](#troubleshooting)
7. [Rollback Procedures](#rollback-procedures)
8. [Security](#security)
9. [Performance Tuning](#performance-tuning)

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+, RHEL 8+, or Debian 11+)
- **CPU**: 8 cores minimum (16 recommended)
- **RAM**: 16GB minimum (32GB recommended)
- **Disk**: 100GB minimum (SSD recommended)
- **Docker**: 24.0+ with Docker Compose v2
- **Ports**: 80, 443 (external); internal network for services

### Required Software

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### DNS Configuration

Point your domain to the server IP:
```
A     yourdomain.com        -> 1.2.3.4
CNAME *.yourdomain.com       -> yourdomain.com
```

---

## Initial Deployment

### 1. Prepare Environment

```bash
# Clone repository
cd /opt
git clone https://github.com/yourorg/rhinometric.git
cd rhinometric/deploy/prod

# Copy environment template
cp .env.prod.example .env.prod
```

### 2. Configure Environment

Edit `.env.prod` and set all `CHANGEME` values:

```bash
# Critical settings to configure:
DOMAIN=yourdomain.com
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=<strong-password>
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
DASHBUILDER_JWT_SECRET=<random-64-char-string>
REPORTGEN_JWT_SECRET=<random-64-char-string>
AI_JWT_SECRET=<random-64-char-string>
LICENSE_JWT_SECRET=<random-64-char-string>
SMTP_HOST=smtp.yourprovider.com
SMTP_USER=your-email@domain.com
SMTP_PASSWORD=<smtp-password>
TRAEFIK_ACME_EMAIL=admin@yourdomain.com
```

**Generate strong secrets:**
```bash
# JWT secrets (64 characters)
openssl rand -hex 32

# Passwords (32 characters)
openssl rand -base64 32
```

### 3. Configure Docker Logging

```bash
# Copy daemon.json
sudo cp logging/daemon.json /etc/docker/daemon.json

# Restart Docker
sudo systemctl restart docker
```

### 4. Deploy Services

```bash
# Pull all images
docker compose --env-file .env.prod -f docker-compose-prod.yml pull

# Start services
docker compose --env-file .env.prod -f docker-compose-prod.yml up -d

# Check status
docker compose --env-file .env.prod -f docker-compose-prod.yml ps
```

### 5. Run Smoke Tests

```bash
# Wait 2 minutes for services to start
sleep 120

# Run smoke tests
bash scripts/smoke-test.sh
```

If all tests pass, your deployment is successful! ✅

---

## Daily Operations

### Start Services

```bash
cd /opt/rhinometric/deploy/prod
docker compose --env-file .env.prod -f docker-compose-prod.yml up -d
```

### Stop Services

```bash
# Graceful stop (waits 10s per service)
docker compose --env-file .env.prod -f docker-compose-prod.yml down

# Force stop
docker compose --env-file .env.prod -f docker-compose-prod.yml down -t 0
```

### Restart Single Service

```bash
# Restart Grafana
docker compose --env-file .env.prod -f docker-compose-prod.yml restart grafana

# Restart with fresh config
docker compose --env-file .env.prod -f docker-compose-prod.yml up -d --force-recreate grafana
```

### View Logs

```bash
# All services (follow mode)
docker compose --env-file .env.prod -f docker-compose-prod.yml logs -f

# Specific service
docker compose logs -f grafana

# Last 100 lines
docker compose logs --tail=100 dashboard-builder

# Logs from last hour
docker compose logs --since 1h prometheus
```

### Check Service Health

```bash
# All services status
docker compose ps

# Health checks
docker ps --filter "health=unhealthy"

# Resource usage
docker stats --no-stream

# Disk usage
docker system df -v
```

---

## Monitoring

### Access URLs

- **Grafana**: `https://yourdomain.com`
- **Prometheus**: Internal only (`http://prometheus:9090`)
- **Alertmanager**: Internal only (`http://alertmanager:9093`)

### Default Credentials

- **Grafana**: Username from `GRAFANA_ADMIN_USER` / Password from `GRAFANA_ADMIN_PASSWORD`

### Key Dashboards

1. **Rhinometric System Health** (Auto-provisioned)
   - Services status
   - Resource usage (CPU, RAM, Disk)
   - Retention policies
   - Compaction activity

2. **Prometheus Stats** (Create manually)
   - Metrics: `prometheus_tsdb_storage_blocks_bytes`, `prometheus_tsdb_head_samples`

3. **API Performance**
   - Metrics: `http_requests_total`, `http_request_duration_seconds`

### Alerts

Alerts are sent via email to configured addresses:
- **Critical**: `ALERT_EMAIL_CRITICAL` (immediate action required)
- **Warning**: `ALERT_EMAIL_OPS` (investigate soon)
- **Default**: `ALERT_EMAIL_DEFAULT` (informational)

### Key Metrics to Watch

```promql
# Services up/down
up{job="dashboard-builder"}

# API request rate
rate(http_requests_total[5m])

# API error rate
rate(http_requests_total{status=~"5.."}[5m])

# Disk usage
100 - (node_filesystem_avail_bytes / node_filesystem_size_bytes * 100)

# Memory usage
100 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100)

# Prometheus storage
prometheus_tsdb_storage_blocks_bytes / 10737418240 * 100
```

---

## Backup & Restore

### Automated Backups

```bash
# Run manual backup
bash scripts/backup.sh

# Setup cron for daily backups at 2 AM
crontab -e
# Add: 0 2 * * * /opt/rhinometric/deploy/prod/scripts/backup.sh
```

### Backup Location

Backups are stored in `$BACKUP_DIR` (default: `/var/backups/rhinometric/`):
```
rhinometric_backup_20240615_020000.tar.gz
rhinometric_backup_20240615_020000.tar.gz.sha256
```

### Restore from Backup

```bash
# Stop services
cd /opt/rhinometric/deploy/prod
docker compose --env-file .env.prod -f docker-compose-prod.yml down

# Extract backup
cd /var/backups/rhinometric
tar xzf rhinometric_backup_20240615_020000.tar.gz
cd rhinometric_backup_20240615_020000

# Verify checksum
sha256sum -c ../rhinometric_backup_20240615_020000.tar.gz.sha256

# Restore volumes
for volume in volumes/*.tar.gz; do
    volume_name=$(basename "$volume" .tar.gz)
    echo "Restoring $volume_name..."
    
    # Remove existing volume
    docker volume rm "$volume_name" 2>/dev/null || true
    
    # Create new volume
    docker volume create "$volume_name"
    
    # Extract data
    docker run --rm \
        -v "$volume_name":/data \
        -v "$(pwd)/volumes":/backup \
        alpine sh -c "cd /data && tar xzf /backup/${volume_name}.tar.gz"
done

# Restore configs
cp -r configs/* /opt/rhinometric/deploy/prod/

# Start services
cd /opt/rhinometric/deploy/prod
docker compose --env-file .env.prod -f docker-compose-prod.yml up -d

# Verify
bash scripts/smoke-test.sh
```

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
docker compose logs grafana
```

**Common issues:**
- Database connection: Check `DATABASE_URL`, ensure postgres is running
- Port conflict: `netstat -tulpn | grep <port>`
- Memory limit: Check `docker stats`, increase `mem_limit` in compose file
- Wrong credentials: Verify `.env.prod` values

### High Memory Usage

```bash
# Check per-container usage
docker stats --no-stream

# Identify top consumers
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}" | sort -k2 -h

# Increase limits in docker-compose-prod.yml
# grafana:
#   mem_limit: 2g  # was 1g
```

### Disk Space Issues

```bash
# Check disk usage
df -h

# Check Docker disk usage
docker system df -v

# Clean old images
docker image prune -a

# Clean volumes (CAUTION: removes unused volumes)
docker volume prune

# Clean old logs
find /var/log -name "*.log" -mtime +30 -delete
```

### Prometheus Storage Full

```bash
# Check current usage
docker exec prometheus du -sh /prometheus

# Reduce retention
# Edit .env.prod:
PROM_RETENTION_TIME=10d  # was 15d
PROM_RETENTION_SIZE=8GB  # was 10GB

# Restart Prometheus
docker compose restart prometheus
```

### Grafana Cannot Connect to Datasources

```bash
# Check datasource config
docker exec grafana cat /etc/grafana/provisioning/datasources/datasources.yml

# Verify network connectivity
docker exec grafana ping -c 3 prometheus
docker exec grafana curl -s http://prometheus:9090/-/healthy

# Re-provision datasources
docker compose restart grafana
```

### Alerts Not Sending

```bash
# Check Alertmanager logs
docker compose logs alertmanager

# Verify SMTP settings in .env.prod
echo $SMTP_HOST $SMTP_PORT $SMTP_USER

# Test alert manually
curl -X POST http://localhost:9093/api/v2/alerts -H "Content-Type: application/json" -d '[{
  "labels": {"alertname": "TestAlert", "severity": "warning"},
  "annotations": {"summary": "Test alert"}
}]'

# Check Alertmanager UI (internal only)
docker exec -it alertmanager wget -O- http://localhost:9093/
```

### API Returns 500 Errors

```bash
# Check API logs
docker compose logs dashboard-builder

# Common causes:
# - Database unavailable: Check postgres logs
# - Invalid JWT: Verify JWT_SECRET in .env.prod matches API secret
# - Missing dependencies: Check API container health

# Restart API
docker compose restart dashboard-builder
```

---

## Rollback Procedures

### Rollback to Previous Version

```bash
# Stop current deployment
docker compose --env-file .env.prod -f docker-compose-prod.yml down

# Checkout previous version
git fetch --tags
git checkout v2.4.0  # or specific commit

# Deploy old version
cd deploy/prod
docker compose --env-file .env.prod -f docker-compose-prod.yml up -d

# Verify
bash scripts/smoke-test.sh
```

### Rollback Database

```bash
# If schema changed, restore from backup
# See "Restore from Backup" section above

# If data corrupted, restore only postgres volume:
docker compose down
docker volume rm postgres_data
docker volume create postgres_data

# Extract from backup
docker run --rm \
    -v postgres_data:/data \
    -v /var/backups/rhinometric/rhinometric_backup_20240615_020000/volumes:/backup \
    alpine tar xzf /backup/postgres_data.tar.gz -C /data

docker compose up -d
```

---

## Security

### Update Secrets

```bash
# Generate new JWT secret
NEW_SECRET=$(openssl rand -hex 32)

# Update .env.prod
sed -i "s/DASHBUILDER_JWT_SECRET=.*/DASHBUILDER_JWT_SECRET=$NEW_SECRET/" .env.prod

# Restart affected service
docker compose restart dashboard-builder
```

### SSL/TLS Certificate Renewal

Let's Encrypt certificates auto-renew via Traefik. Check expiry:

```bash
# Check certificate
docker exec traefik cat /letsencrypt/acme.json | jq '.letsencrypt.Certificates[0].domain'

# Force renewal (if needed)
docker exec traefik touch /letsencrypt/acme.json
docker compose restart traefik
```

### Security Audit

```bash
# Check for exposed ports
netstat -tulpn | grep LISTEN

# Verify only 80/443 exposed
ss -tulpn | grep -E ':(80|443)\s'

# Check Docker security
docker scan rhinometric/dashboard-builder:2.5.0

# Update all images
docker compose pull
docker compose up -d
```

---

## Performance Tuning

### Prometheus

```bash
# Increase memory if scraping many targets
# docker-compose-prod.yml:
prometheus:
  mem_limit: 4g  # was 2g
  cpus: 3.0      # was 2.0
```

### Grafana

```bash
# Enable caching in .env.prod
GF_CACHING_ENABLED=true
GF_CACHE_TYPE=redis
GF_CACHE_CONNSTR=addr=redis:6379,password=${REDIS_PASSWORD},db=1
```

### PostgreSQL

```bash
# Tune postgres (in docker-compose-prod.yml)
postgres:
  environment:
    - POSTGRES_SHARED_BUFFERS=512MB
    - POSTGRES_EFFECTIVE_CACHE_SIZE=2GB
    - POSTGRES_MAX_CONNECTIONS=200
```

### API Workers

```bash
# Increase API concurrency in .env.prod
API_WORKERS=4  # was 2

# Restart APIs
docker compose restart dashboard-builder ai-anomaly report-generator
```

---

## Contact & Support

- **Documentation**: `/docs` in repository
- **Issues**: GitHub Issues
- **Email**: ops@yourcompany.com
- **Version**: Rhinometric v2.5.0
- **Last Updated**: 2024-06-15

---

## Quick Reference

### Essential Commands

```bash
# Start
docker compose --env-file .env.prod -f docker-compose-prod.yml up -d

# Stop
docker compose --env-file .env.prod -f docker-compose-prod.yml down

# Logs
docker compose logs -f <service>

# Backup
bash scripts/backup.sh

# Test
bash scripts/smoke-test.sh

# Status
docker compose ps
docker stats
```

### Service Ports (Internal)

| Service              | Port  |
|---------------------|-------|
| Grafana             | 3000  |
| Prometheus          | 9090  |
| Alertmanager        | 9093  |
| Loki                | 3100  |
| Tempo               | 3200  |
| PostgreSQL          | 5432  |
| Redis               | 6379  |
| Dashboard Builder   | 8001  |
| AI Anomaly          | 8085  |
| Report Generator    | 8086  |
| License Server      | 8090  |
| Node Exporter       | 9100  |
| cAdvisor            | 8080  |
| Blackbox Exporter   | 9115  |

---

**Remember**: Always run smoke tests after any change! 🧪
