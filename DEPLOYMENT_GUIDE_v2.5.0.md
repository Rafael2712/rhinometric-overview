# Rhinometric v2.5.0 - Production Deployment Guide

## 📋 OVERVIEW

This guide covers deploying **Rhinometric v2.5.0 PRODUCTION** to AWS Lightsail (54.197.192.198).

**Key Changes from v2.1.0:**
- ✅ License Management UI (web interface)
- ✅ Rhinometric Console v3 (Backend + Frontend)
- ✅ Jaeger distributed tracing (replaces Tempo)
- ✅ AI Anomaly Detection engine
- ✅ Optimized for 2GB RAM (16 containers vs 60+ in full stack)

---

## 🎯 DEPLOYMENT PLAN

### **Phase 1: Local Staging Test (CURRENT)**
Test stack locally on Windows/WSL before touching production.

### **Phase 2: Production Preparation**
Backup current server, prepare environment.

### **Phase 3: Migration**
Deploy to production with rollback plan.

---

## 📦 WHAT'S IN v2.5.0 PRODUCTION STACK

### **Core Services (16 containers)**

| Service | Port | Resources | Purpose |
|---------|------|-----------|---------|
| **license-server-v2** | 5000 | 512MB | License API (FastAPI) |
| **license-ui** | 8093 | 256MB | License management web UI |
| **postgres** | 5432 | 512MB | Main database (PostgreSQL 15) |
| **redis** | 6379 | 256MB | Cache & sessions |
| **prometheus** | 9090 | 768MB | Metrics collection |
| **loki** | 3100 | 512MB | Log aggregation |
| **jaeger** | 16686, 14317, 14318 | 384MB | Distributed tracing |
| **grafana** | 3000 | 512MB | Dashboards & visualization |
| **otel-collector** | 4317, 4318 | 256MB | OpenTelemetry pipeline |
| **rhinometric-ai-anomaly** | 8085, 9091 | 512MB | ML anomaly detection |
| **alertmanager** | 9093 | 256MB | Alert routing |
| **node-exporter** | 9100 | 128MB | Host metrics |
| **postgres-exporter** | 9187 | 128MB | Database metrics |
| **promtail** | - | 128MB | Log collector |
| **rhinometric-console-backend** | 8105 | 384MB | Console API Gateway |
| **rhinometric-console-frontend** | 3002 | 256MB | Console Vue.js UI |

**TOTAL ESTIMATED RAM:** ~5.5GB  
**PRODUCTION TARGET:** 2GB (will need optimization or RAM upgrade)

---

## ⚙️ PHASE 1: LOCAL STAGING SETUP

### **Step 1: Prepare Environment File**

```bash
cd c:\Users\canel\mi-proyecto\infrastructure\mi-proyecto
cp .env.v2.5.0-production .env
```

**Edit `.env` and configure:**
```bash
# Required changes
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
SMTP_PASSWORD=<your-zoho-password>
GRAFANA_PASSWORD=<admin-password>
ADMIN_PASSWORD=<console-admin-password>
SECRET_KEY=$(openssl rand -base64 32)
```

### **Step 2: Launch Stack Locally**

```bash
# Option A: WSL2/Docker Desktop (Windows)
docker compose -f docker-compose-v2.5.0-PRODUCTION.yml up -d

# Option B: Linux/Mac
docker compose -f docker-compose-v2.5.0-PRODUCTION.yml up -d
```

### **Step 3: Verify Services**

```bash
# Check all containers running
docker compose -f docker-compose-v2.5.0-PRODUCTION.yml ps

# Check health status
docker compose -f docker-compose-v2.5.0-PRODUCTION.yml ps | grep healthy

# View logs
docker compose -f docker-compose-v2.5.0-PRODUCTION.yml logs -f --tail=50
```

### **Step 4: Access UIs**

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin / (from .env) |
| **License UI** | http://localhost:8093 | - |
| **Console Frontend** | http://localhost:3002 | admin / (from .env) |
| **Jaeger UI** | http://localhost:16686 | - |
| **Prometheus** | http://localhost:9090 | - |
| **License API** | http://localhost:5000/docs | - |
| **Console API** | http://localhost:8105/docs | - |

### **Step 5: Functional Tests**

```bash
# 1. Test License Creation (Trial)
curl -X POST http://localhost:5000/api/licenses/trial \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test Customer",
    "customer_email": "test@example.com",
    "license_type": "trial",
    "days": 15
  }'

# 2. Test License API Health
curl http://localhost:5000/api/health

# 3. Test Console API Health
curl http://localhost:8105/health

# 4. Check Prometheus Targets
curl http://localhost:9090/api/v1/targets

# 5. Check Jaeger Services
curl http://localhost:16686/api/services
```

### **Step 6: Monitor Resources**

```bash
# Check RAM usage per container
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}"

# Check total RAM consumption
docker stats --no-stream --format "{{.MemUsage}}" | awk '{sum+=$1} END {print sum " MB total"}'
```

---

## 🚨 EXPECTED ISSUES & SOLUTIONS

### **Issue 1: Out of Memory (likely on 2GB server)**

**Symptom:** Containers crash, OOMKilled errors

**Solutions:**
1. **Upgrade AWS Lightsail plan** to 4GB RAM instance ($20/month → $40/month)
2. **Disable AI Anomaly** (saves ~512MB)
3. **Reduce Prometheus retention:** Change `--storage.tsdb.retention.time=30d` to `7d`
4. **Reduce container memory limits** in docker-compose

### **Issue 2: Missing Configuration Files**

**Symptom:** `Error: config file not found`

**Check these files exist:**
```bash
./config/prometheus-v2.2.yml
./config/loki-config.yml
./config/otel-collector-config.yml
./config/promtail-config.yml
./config/rules/
./alertmanager/alertmanager.yml
./grafana/provisioning/
./init-db/
./rhinometric-ai-anomaly/config.yaml
```

### **Issue 3: Port Conflicts**

**Symptom:** `Error: port already in use`

**Solution:**
```bash
# Check what's using ports
netstat -ano | findstr :3000  # Windows
lsof -i :3000                 # Linux/Mac

# Stop conflicting services or change ports in docker-compose
```

---

## 📊 PHASE 2: PRODUCTION PREPARATION

### **Step 1: Backup Current Production**

SSH to server and backup everything:

```bash
ssh -i lightsail-license-server.pem ubuntu@54.197.192.198

# Create backup directory
mkdir -p ~/backups/pre-v2.5.0-$(date +%Y%m%d)
cd ~/backups/pre-v2.5.0-$(date +%Y%m%d)

# Backup database
docker exec rhinometric-postgres pg_dump -U postgres rhinometric_dev > rhinometric_db_backup.sql

# Backup volumes
sudo tar -czf license_server_volumes.tar.gz ~/license-server/
sudo tar -czf rhinometric_data.tar.gz ~/rhinometric_data/

# Backup docker-compose
cp ~/license-server/docker-compose.yml docker-compose-OLD.yml
cp ~/license-server/.env .env.OLD

# Verify backups
ls -lh
```

### **Step 2: Check Server Resources**

```bash
# Check available disk space (need at least 10GB free)
df -h

# Check current RAM usage
free -h

# Check current containers
docker ps

# Check Docker version
docker --version
docker compose version
```

### **Step 3: Prepare Production Environment**

```bash
# Create new data directory (v2.5 uses different path)
mkdir -p ~/rhinometric_data_v2.5/{license-server,postgres,redis,loki,jaeger,grafana,prometheus,ai-anomaly,console-backend,alertmanager}

# Set permissions
sudo chown -R 1000:1000 ~/rhinometric_data_v2.5/loki
sudo chown -R 472:472 ~/rhinometric_data_v2.5/grafana
```

---

## 🚀 PHASE 3: PRODUCTION MIGRATION

### **Step 1: Upload Code to Server**

From your local machine:

```bash
# Option A: SCP entire project
scp -i lightsail-license-server.pem -r \
  c:/Users/canel/mi-proyecto/infrastructure/mi-proyecto \
  ubuntu@54.197.192.198:~/rhinometric-v2.5.0/

# Option B: Git clone (if you push to GitHub first)
ssh ubuntu@54.197.192.198
git clone https://github.com/Rafael2712/mi-proyecto.git ~/rhinometric-v2.5.0
cd ~/rhinometric-v2.5.0/infrastructure/mi-proyecto
```

### **Step 2: Configure Production .env**

```bash
cd ~/rhinometric-v2.5.0/infrastructure/mi-proyecto
cp .env.v2.5.0-production .env

# Edit with your production secrets
nano .env

# CRITICAL: Update these values
# - POSTGRES_PASSWORD (strong password)
# - REDIS_PASSWORD (strong password)
# - SMTP_PASSWORD (Zoho SMTP password)
# - GRAFANA_PASSWORD (admin password)
# - ADMIN_PASSWORD (console admin password)
# - SECRET_KEY (generate with: openssl rand -base64 32)
```

### **Step 3: Stop Old Stack**

```bash
cd ~/license-server
docker compose down

# Verify all stopped
docker ps
```

### **Step 4: Deploy v2.5.0**

```bash
cd ~/rhinometric-v2.5.0/infrastructure/mi-proyecto

# Pull images first (faster startup)
docker compose -f docker-compose-v2.5.0-PRODUCTION.yml pull

# Build custom images
docker compose -f docker-compose-v2.5.0-PRODUCTION.yml build

# Launch stack
docker compose -f docker-compose-v2.5.0-PRODUCTION.yml up -d

# Watch startup logs
docker compose -f docker-compose-v2.5.0-PRODUCTION.yml logs -f
```

### **Step 5: Verify Deployment**

```bash
# Check all containers running
docker compose -f docker-compose-v2.5.0-PRODUCTION.yml ps

# Wait for healthy status (may take 2-3 minutes)
watch -n 2 'docker compose -f docker-compose-v2.5.0-PRODUCTION.yml ps'

# Test endpoints
curl http://localhost:5000/api/health      # License API
curl http://localhost:8105/health          # Console API
curl http://localhost:3000/api/health      # Grafana
curl http://localhost:16686                # Jaeger UI

# Check logs for errors
docker compose -f docker-compose-v2.5.0-PRODUCTION.yml logs | grep -i error
```

### **Step 6: Test License Creation**

```bash
# Create test trial license
curl -X POST http://54.197.192.198:5000/api/licenses/trial \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Production Test",
    "customer_email": "rafael.canelon@rhinometric.com",
    "license_type": "trial",
    "days": 15
  }'

# Check email received (should arrive within 1 minute)
```

---

## 🔄 ROLLBACK PLAN

If v2.5.0 fails, revert to old stack:

```bash
# Stop v2.5.0
cd ~/rhinometric-v2.5.0/infrastructure/mi-proyecto
docker compose -f docker-compose-v2.5.0-PRODUCTION.yml down

# Restore old stack
cd ~/license-server
docker compose up -d

# Verify working
curl http://localhost:5000/api/health
docker compose ps
```

---

## 📈 POST-DEPLOYMENT

### **Monitor for 24 hours:**

```bash
# Check RAM usage
docker stats --no-stream

# Check container health
docker compose -f docker-compose-v2.5.0-PRODUCTION.yml ps

# Check for OOM kills
dmesg | grep -i oom

# Watch logs for errors
docker compose -f docker-compose-v2.5.0-PRODUCTION.yml logs -f | grep -i error
```

### **Configure Firewall:**

```bash
# If using Lightsail firewall, open these ports:
# - 3000 (Grafana)
# - 3002 (Console UI)
# - 5000 (License API)
# - 8093 (License UI)
# - 16686 (Jaeger UI - optional, can be internal only)
```

---

## 🎯 SUCCESS CRITERIA

- [ ] All 16 containers show `healthy` status
- [ ] Grafana accessible at http://54.197.192.198:3000
- [ ] Console UI accessible at http://54.197.192.198:3002
- [ ] License UI accessible at http://54.197.192.198:8093
- [ ] License creation works (trial + annual)
- [ ] Email delivery working (SMTP Zoho)
- [ ] Jaeger shows traces from services
- [ ] Prometheus collecting metrics
- [ ] RAM usage stays under 80%
- [ ] No OOMKilled containers

---

## 🆘 TROUBLESHOOTING

### **Container won't start**
```bash
# Check logs for specific container
docker logs rhinometric-license-server-v2

# Check healthcheck
docker inspect rhinometric-license-server-v2 | grep -A 10 Health
```

### **Database connection errors**
```bash
# Check PostgreSQL logs
docker logs rhinometric-postgres

# Test database connection
docker exec -it rhinometric-postgres psql -U rhinometric -d rhinometric -c "SELECT 1;"
```

### **SMTP not working**
```bash
# Check License Server logs
docker logs rhinometric-license-server-v2 | grep -i smtp

# Verify .env SMTP settings
cat .env | grep SMTP
```

---

## 📝 NEXT STEPS AFTER PRODUCTION

1. **Create Manual de Usuario v2.5.0** (document new UIs)
2. **Create Manual Técnico v2.5.0**
3. **Update rhinometric.com** with v2.5.0 info
4. **Configure Cloudflare** for SSL/domain routing
5. **Set up automated backups** (cron job)
6. **Create v2.5.0 Release Notes**

---

**Document Version:** 1.0  
**Last Updated:** December 18, 2024  
**Author:** Rhinometric Team
