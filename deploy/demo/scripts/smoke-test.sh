#!/bin/bash
# smoke-test.sh - Enhanced con validaciÃ³n AI metrics >0 en 5 min
# Rhinometric v2.5.0

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}âœ“${NC} $1"
    else
        echo -e "${RED}âœ—${NC} $1"
        ((ERRORS++))
    fi
}

echo -e "\n${GREEN}í´ Rhinometric Demo - Enhanced Smoke Test${NC}"
echo "=================================="

# [1/9] Docker containers
echo -e "\n${YELLOW}[1/9]${NC} Verificando contenedores..."
UNHEALTHY=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep -c "unhealthy" || true)
[ "$UNHEALTHY" -eq 0 ]
check "Todos los contenedores healthy"

# [2/9] HTTP Endpoints
echo -e "\n${YELLOW}[2/9]${NC} Verificando endpoints HTTP..."
for SERVICE in "Grafana:3000" "Prometheus:9090" "Loki:3100" "AI:8085" "Builder:8001"; do
    NAME="${SERVICE%%:*}"
    PORT="${SERVICE##*:}"
    curl -sf "http://localhost:$PORT" -o /dev/null
    check "$NAME :$PORT"
done

# [3/9] Prometheus Targets
echo -e "\n${YELLOW}[3/9]${NC} Verificando Prometheus targets..."
TARGETS_DOWN=$(curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | select(.health!="up") | .scrapePool' | wc -l)
[ "$TARGETS_DOWN" -eq 0 ]
check "Todos los targets UP ($TARGETS_DOWN DOWN)"

# [4/9] Grafana Datasources
echo -e "\n${YELLOW}[4/9]${NC} Verificando datasources Grafana..."
curl -s -u admin:rhinometric_demo http://localhost:3000/api/datasources/uid/prometheus | jq -e '.uid == "prometheus"' > /dev/null
check "Datasource Prometheus (UID: prometheus)"

# [5/9] AI Metrics - ENHANCED: Wait for detections >0
echo -e "\n${YELLOW}[5/9]${NC} Verificando mÃ©tricas AI (espera max 5 min para detecciones >0)..."

# Check metrics exist
curl -s http://localhost:8085/metrics | grep -q "rhinometric_anomaly"
check "MÃ©tricas AI presentes"

# NEW: Wait for actual detections
MAX_WAIT=300  # 5 minutos
WAIT_INTERVAL=10
ELAPSED=0
DETECTIONS=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    DETECTIONS=$(curl -s http://localhost:8085/metrics 2>/dev/null | grep "^rhinometric_anomaly_detections_total" | awk '{print $2}' | head -1 || echo "0")
    
    if (( $(echo "$DETECTIONS > 0" | bc -l 2>/dev/null || echo 0) )); then
        break
    fi
    
    echo -e "  ${YELLOW}â³${NC} Esperando detecciones... (${ELAPSED}s / ${MAX_WAIT}s)"
    sleep $WAIT_INTERVAL
    ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

[ "$(echo "$DETECTIONS > 0" | bc -l)" -eq 1 ]
check "AI Anomaly Detections >0 (actual: $DETECTIONS) en ${ELAPSED}s"

# [6/9] Disk Space
echo -e "\n${YELLOW}[6/9]${NC} Verificando espacio en disco..."
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
[ "$DISK_USAGE" -lt 80 ]
check "Disco <80% (actual: ${DISK_USAGE}%)"

# [7/9] Docker Volumes
echo -e "\n${YELLOW}[7/9]${NC} Verificando volÃºmenes..."
VOLUMES=$(docker volume ls --filter "name=demo_" --format "{{.Name}}" | wc -l)
[ "$VOLUMES" -gt 0 ]
check "VolÃºmenes creados (total: $VOLUMES)"

# [8/9] Network
echo -e "\n${YELLOW}[8/9]${NC} Verificando red..."
docker network inspect demo_rhinometric > /dev/null 2>&1
check "Red rhinometric activa"

# [9/9] Anomaly Seed Process
echo -e "\n${YELLOW}[9/9]${NC} Verificando anomaly-seed..."
if ps aux | grep -q "[a]nomaly-seed.sh"; then
    check "Proceso anomaly-seed.sh activo"
else
    echo -e "${YELLOW}âš ${NC}  anomaly-seed.sh no detectado (puede estar detenido)"
    echo "   Para iniciarlo: nohup bash /opt/rhinometric/deploy/demo/scripts/anomaly-seed.sh > /tmp/seed.log 2>&1 &"
fi

# Summary
echo -e "\n=================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}âœ“ Smoke test PASSED${NC} - Stack funcional"
    echo -e "${GREEN}í¾‰ DEMO READY${NC}"
    exit 0
else
    echo -e "${RED}âœ— Smoke test FAILED${NC} - $ERRORS error(es)"
    exit 1
fi
