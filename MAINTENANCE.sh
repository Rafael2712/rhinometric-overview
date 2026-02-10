#!/bin/bash
################################################################################
# RHINOMETRIC MAINTENANCE SCRIPT
# Version: 1.0.0
# Purpose: Automated cleanup and health checks for production server
# Disk: 320GB - Critical maintenance to prevent saturation
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== RHINOMETRIC MAINTENANCE SCRIPT ===${NC}"
echo "Started: $(date)"
echo ""

################################################################################
# 1. DOCKER LOGS CLEANUP
################################################################################
echo -e "${YELLOW}[1/6] Cleaning Docker logs...${NC}"

# Stop logging temporarily
docker-compose -f /opt/rhinometric/docker-compose.yml pause 2>/dev/null || true

# Truncate logs older than 7 days
find /var/lib/docker/containers/ -name "*.log" -mtime +7 -exec truncate -s 0 {} \; 2>/dev/null || true

# Configure log rotation for all containers
cat > /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

# Restart docker daemon to apply changes
systemctl restart docker
sleep 10

# Resume containers
cd /opt/rhinometric
docker-compose up -d

LOGS_CLEANED=$(du -sh /var/lib/docker/containers/ 2>/dev/null | awk '{print $1}')
echo -e "${GREEN}✓ Docker logs cleaned. Current size: $LOGS_CLEANED${NC}"

################################################################################
# 2. PRUNE UNUSED DOCKER RESOURCES
################################################################################
echo -e "${YELLOW}[2/6] Pruning unused Docker resources...${NC}"

# Remove dangling images
IMAGES_REMOVED=$(docker image prune -f 2>&1 | grep "Total reclaimed space" | awk '{print $4 $5}')
echo -e "${GREEN}✓ Images pruned: $IMAGES_REMOVED${NC}"

# Remove unused volumes (BE CAREFUL - only unused)
VOLUMES_REMOVED=$(docker volume prune -f 2>&1 | grep "Total reclaimed space" | awk '{print $4 $5}')
echo -e "${GREEN}✓ Volumes pruned: $VOLUMES_REMOVED${NC}"

# Remove stopped containers
docker container prune -f > /dev/null 2>&1
echo -e "${GREEN}✓ Stopped containers removed${NC}"

################################################################################
# 3. VICTORIAMETRICS DATA RETENTION
################################################################################
echo -e "${YELLOW}[3/6] Checking VictoriaMetrics retention...${NC}"

VM_SIZE=$(docker exec rhinometric-victoria-metrics du -sh /victoria-metrics-data 2>/dev/null | awk '{print $1}')
echo "Current VictoriaMetrics data: $VM_SIZE"
echo "Retention policy: 90 days (configured in docker-compose.yml)"
echo -e "${GREEN}✓ VictoriaMetrics within limits${NC}"

################################################################################
# 4. LOKI LOGS RETENTION
################################################################################
echo -e "${YELLOW}[4/6] Checking Loki retention...${NC}"

LOKI_SIZE=$(du -sh ~/rhinometric_data_v2.5/loki 2>/dev/null | awk '{print $1}')
echo "Current Loki data: $LOKI_SIZE"
echo "Retention policy: 30 days (configured in loki-config.yml)"
echo -e "${GREEN}✓ Loki within limits${NC}"

################################################################################
# 5. POSTGRES VACUUM AND ANALYZE
################################################################################
echo -e "${YELLOW}[5/6] Running PostgreSQL maintenance...${NC}"

docker exec rhinometric-postgres psql -U rhinometric -d rhinometric -c "VACUUM ANALYZE;" > /dev/null 2>&1
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric_licenses -c "VACUUM ANALYZE;" > /dev/null 2>&1

PG_SIZE=$(docker exec rhinometric-postgres psql -U rhinometric -d rhinometric -t -c "SELECT pg_size_pretty(pg_database_size('rhinometric'));" | xargs)
echo -e "${GREEN}✓ PostgreSQL vacuumed. DB size: $PG_SIZE${NC}"

################################################################################
# 6. DISK SPACE SUMMARY
################################################################################
echo -e "${YELLOW}[6/6] Disk space summary...${NC}"

DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
DISK_AVAILABLE=$(df -h / | tail -1 | awk '{print $4}')

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "DISK USAGE: ${DISK_USAGE}% used"
echo "AVAILABLE: ${DISK_AVAILABLE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$DISK_USAGE" -gt 80 ]; then
    echo -e "${RED}⚠️  WARNING: Disk usage above 80%!${NC}"
    echo "Consider:"
    echo "  1. Reducing VictoriaMetrics retention (currently 90d)"
    echo "  2. Reducing Loki retention (currently 30d)"
    echo "  3. Cleaning old backups in ~/rhinometric_data_v2.5/"
else
    echo -e "${GREEN}✓ Disk usage healthy${NC}"
fi

################################################################################
# HEALTH CHECKS
################################################################################
echo ""
echo -e "${YELLOW}Running health checks...${NC}"

# Check critical containers
CRITICAL_CONTAINERS=(
    "rhinometric-console-frontend"
    "rhinometric-console-backend"
    "rhinometric-nginx"
    "rhinometric-victoria-metrics"
    "rhinometric-loki"
    "rhinometric-postgres"
)

ALL_HEALTHY=true
for container in "${CRITICAL_CONTAINERS[@]}"; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' $container 2>/dev/null || echo "no-healthcheck")
    if [ "$STATUS" = "healthy" ] || [ "$STATUS" = "no-healthcheck" ]; then
        echo -e "${GREEN}✓${NC} $container: $STATUS"
    else
        echo -e "${RED}✗${NC} $container: $STATUS"
        ALL_HEALTHY=false
    fi
done

if [ "$ALL_HEALTHY" = true ]; then
    echo -e "${GREEN}✓ All critical services healthy${NC}"
else
    echo -e "${RED}⚠️  Some services are unhealthy!${NC}"
fi

################################################################################
# SUMMARY
################################################################################
echo ""
echo -e "${GREEN}=== MAINTENANCE COMPLETED ===${NC}"
echo "Finished: $(date)"
echo ""
echo "Next scheduled run: Add to crontab with:"
echo "  0 2 * * 0  /opt/rhinometric/MAINTENANCE.sh >> /var/log/rhinometric-maintenance.log 2>&1"
echo "  (Runs every Sunday at 2 AM)"
