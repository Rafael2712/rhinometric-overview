#  Rhinometric - Installation Guide

**Version:** 2.5.1 | **Platform:** On-Premise (Docker Compose)

---

## Prerequisites

### **Operating System**
- Ubuntu 22.04+ LTS
- Rocky Linux 8+
- Debian 11+
- macOS (Docker Desktop) - **not recommended for production**
- Windows (WSL2 + Docker Desktop) - **not recommended for production**

### **Hardware**
- **Minimum:** 4 vCPU, 8 GB RAM, 50 GB disk
- **Recommended:** 8 vCPU, 16 GB RAM, 200 GB SSD

### **Software**
- Docker >= 24.0
- Docker Compose >= 2.20
- curl, tar, git (optional)

---

## Quick Install (Ubuntu/Debian)

\\\ash
# 1. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker \
newgrp docker

# 2. Download Rhinometric
curl -L https://github.com/Rafael2712/rhinometric-overview/releases/download/v2.5.1/rhinometric-v2.5.1.tar.gz -o rhinometric.tar.gz
tar -xzf rhinometric.tar.gz
cd rhinometric

# 3. Start platform
docker-compose up -d

# 4. Verify installation
docker ps | grep rhinometric
curl http://localhost:3002
\\\

---

## Post-Installation

### **1. Access Console**
- URL: http://your-server-ip:3002
- Default login: \dmin\ / \dmin\
- **Change password immediately** after first login

### **2. Verify Services**
\\\ash
# Check all containers running
docker ps --filter "name=rhinometric" --format "table {{.Names}}\t{{.Status}}"

# Expected output:
# rhinometric-console-frontend   Up 2 minutes
# rhinometric-console-backend    Up 2 minutes
# rhinometric-prometheus         Up 2 minutes
# rhinometric-grafana            Up 2 minutes
# rhinometric-loki               Up 2 minutes
# rhinometric-jaeger             Up 2 minutes
# rhinometric-ai-anomaly         Up 2 minutes
# rhinometric-alertmanager       Up 2 minutes
# rhinometric-postgres           Up 2 minutes
# rhinometric-redis              Up 2 minutes
\\\

### **3. Check Prometheus Targets**
\\\ash
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job, health}'

# All targets should show "health": "up"
\\\

### **4. Verify Logs Flow**
\\\ash
# Query Loki for recent logs
curl -G http://localhost:3100/loki/api/v1/query \
  --data-urlencode 'query={job="varlogs"}' \
  --data-urlencode 'limit=5' | jq
\\\

### **5. Test AI Anomaly Engine**
\\\ash
docker logs rhinometric-ai-anomaly --tail 50

# Should see:
# [INFO] Fetched 1234 metrics from Prometheus
# [INFO] Detected 3 anomalies (severity: low=2, medium=1)
\\\

---

## Configuration

### **Environment Variables** (\.env\ file)
\\\ash
# Retention settings
PROMETHEUS_RETENTION=15d
LOKI_RETENTION=7d

# Resource limits
PROMETHEUS_MEMORY=2g
LOKI_MEMORY=1g

# Security
GRAFANA_ADMIN_PASSWORD=change_me
POSTGRES_PASSWORD=change_me
REDIS_PASSWORD=change_me
\\\

### **Firewall Rules**
\\\ash
# Ubuntu/Debian
sudo ufw allow 3002/tcp  # Console
sudo ufw allow 3000/tcp  # Grafana
sudo ufw allow 9090/tcp  # Prometheus (optional)

# Rocky Linux
sudo firewall-cmd --add-port=3002/tcp --permanent
sudo firewall-cmd --add-port=3000/tcp --permanent
sudo firewall-cmd --reload
\\\

---

## Troubleshooting

### **Console shows "API Error"**
\\\ash
# Check backend logs
docker logs rhinometric-console-backend --tail 100

# Restart backend
docker restart rhinometric-console-backend
\\\

### **No metrics in dashboards**
\\\ash
# Verify Prometheus scraping
curl http://localhost:9090/api/v1/targets

# Check if node-exporter is running
docker ps | grep node-exporter
\\\

### **Logs not appearing**
\\\ash
# Check Promtail
docker logs rhinometric-promtail --tail 50

# Verify Loki is accessible
docker exec rhinometric-promtail curl http://loki:3100/ready
\\\

---

## Upgrading

\\\ash
# 1. Backup data
docker-compose down
tar -czf rhinometric-backup-.tar.gz volumes/

# 2. Download new version
curl -L https://github.com/Rafael2712/rhinometric-overview/releases/download/v2.6.0/rhinometric-v2.6.0.tar.gz -o rhinometric-v2.6.0.tar.gz
tar -xzf rhinometric-v2.6.0.tar.gz
cd rhinometric-v2.6.0

# 3. Copy old .env
cp ../rhinometric/.env .

# 4. Start new version
docker-compose up -d
\\\

---

## Uninstallation

\\\ash
# Stop and remove all containers
docker-compose down -v

# Remove images (optional)
docker rmi 

# Remove data volumes (optional)
sudo rm -rf volumes/
\\\

---

## Next Steps

- **User Guide:** [USER_GUIDE.md](./USER_GUIDE.md)
- **Architecture:** [ARCHITECTURE.md](./ARCHITECTURE.md)
- **FAQ:** [FAQ.md](./FAQ.md)

** 2025 Rhinometric**
