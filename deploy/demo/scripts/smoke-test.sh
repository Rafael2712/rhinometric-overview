#!/bin/bash
# smoke-test.sh - Validación completa del stack demo

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        ((ERRORS++))
    fi
}

echo "�� Rhinometric Demo - Smoke Test"
echo "=================================="

# 1. Containers Health
echo -e "\n${YELLOW}[1/8]${NC} Verificando contenedores..."
docker ps --filter "name=rhinometric-" --format "{{.Names}} {{.Status}}" | grep -q "healthy"
check "Todos los contenedores healthy"

# 2. HTTP Endpoints
echo -e "\n${YELLOW}[2/8]${NC} Verificando endpoints HTTP..."
curl -sf http://localhost:3000/api/health > /dev/null
check "Grafana :3000"

curl -sf http://localhost:9090/-/healthy > /dev/null
check "Prometheus :9090"

curl -sf http://localhost:3100/ready > /dev/null
check "Loki :3100"

curl -sf http://localhost:8085/health > /dev/null
check "AI Anomaly :8085"

# 3. Prometheus Targets
echo -e "\n${YELLOW}[3/8]${NC} Verificando Prometheus targets..."
TARGETS=$(curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | select(.health!="up") | .scrapePool')
if [ -z "$TARGETS" ]; then
    check "Todos los targets UP"
else
    echo -e "${RED}✗${NC} Targets DOWN: $TARGETS"
    ((ERRORS++))
fi

# 4. Grafana Datasources
echo -e "\n${YELLOW}[4/8]${NC} Verificando datasources Grafana..."
DS_CHECK=$(curl -s -u admin:rhinometric_demo http://localhost:3000/api/datasources/uid/prometheus | jq -r '.name')
if [ "$DS_CHECK" == "Prometheus" ]; then
    check "Datasource Prometheus (UID: prometheus)"
else
    echo -e "${RED}✗${NC} Datasource Prometheus no encontrado"
    ((ERRORS++))
fi

# 5. AI Metrics
echo -e "\n${YELLOW}[5/8]${NC} Verificando métricas AI..."
curl -s http://localhost:8085/metrics | grep -q "rhinometric_anomaly"
check "Métricas AI presentes"

# 6. Disk Space
echo -e "\n${YELLOW}[6/8]${NC} Verificando espacio en disco..."
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    check "Disco <80% (actual: ${DISK_USAGE}%)"
else
    echo -e "${RED}✗${NC} Disco al ${DISK_USAGE}% (>80%)"
    ((ERRORS++))
fi

# 7. Volumes
echo -e "\n${YELLOW}[7/8]${NC} Verificando volúmenes..."
docker volume ls | grep -q "demo_grafana-data"
check "Volúmenes creados"

# 8. Network
echo -e "\n${YELLOW}[8/8]${NC} Verificando red..."
docker network inspect demo_rhinometric > /dev/null 2>&1
check "Red rhinometric activa"

echo ""
echo "=================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Smoke test PASSED${NC} - Stack funcional"
    exit 0
else
    echo -e "${RED}✗ Smoke test FAILED${NC} - $ERRORS errores encontrados"
    exit 1
fi
