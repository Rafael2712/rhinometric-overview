#!/bin/bash

# Script de validación de dashboards Rhinometric Trial
# Este script verifica que todos los dashboards tengan data

echo "========================================="
echo "VALIDACIÓN DASHBOARDS RHINOMETRIC TRIAL"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. License Management Dashboard
echo -e "${YELLOW}1. License Management Dashboard${NC}"
LICENSE_COUNT=$(wsl -d Ubuntu docker exec rhinometric-postgres psql -U postgres -d rhinometric -t -c "SELECT COUNT(*) FROM licenses;" 2>/dev/null | tr -d ' ')
if [ "$LICENSE_COUNT" -gt 0 ]; then
    echo -e "   ${GREEN}✓${NC} Licencias encontradas: $LICENSE_COUNT"
else
    echo -e "   ${RED}✗${NC} No se encontraron licencias en la BD"
fi

# 2. Rhinometric - Overview (Prometheus)
echo -e "${YELLOW}2. Rhinometric - Overview${NC}"
PROM_TARGETS=$(curl -s http://localhost:9090/api/v1/targets | python3 -c "import sys, json; data=json.load(sys.stdin); print(len([t for t in data['data']['activeTargets'] if t['health']=='up']))" 2>/dev/null)
if [ "$PROM_TARGETS" -gt 0 ]; then
    echo -e "   ${GREEN}✓${NC} Targets activos: $PROM_TARGETS"
else
    echo -e "   ${RED}✗${NC} No hay targets activos en Prometheus"
fi

# 3. Docker Containers (cAdvisor)
echo -e "${YELLOW}3. Docker Containers Dashboard${NC}"
CADVISOR_METRICS=$(curl -s http://localhost:8080/metrics | grep -c "container_cpu_usage_seconds_total" 2>/dev/null)
if [ "$CADVISOR_METRICS" -gt 0 ]; then
    echo -e "   ${GREEN}✓${NC} Métricas de contenedores: $CADVISOR_METRICS"
else
    echo -e "   ${RED}✗${NC} cAdvisor no está exportando métricas"
fi

# 4. System Monitoring (Node Exporter)
echo -e "${YELLOW}4. System Monitoring Dashboard${NC}"
NODE_METRICS=$(curl -s http://localhost:9100/metrics | grep -c "node_cpu_seconds_total" 2>/dev/null)
if [ "$NODE_METRICS" -gt 0 ]; then
    echo -e "   ${GREEN}✓${NC} Métricas de sistema disponibles"
else
    echo -e "   ${RED}✗${NC} Node Exporter no está funcionando"
fi

# 5. Logs Explorer (Loki)
echo -e "${YELLOW}5. Logs Explorer Dashboard${NC}"
LOKI_READY=$(curl -s http://localhost:3100/ready 2>/dev/null)
if [ "$LOKI_READY" == "ready" ]; then
    # Query para verificar si hay logs
    LOGS_COUNT=$(curl -s -G --data-urlencode 'query={job="docker_logs"}' http://localhost:3100/loki/api/v1/query | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('data', {}).get('result', [])))" 2>/dev/null)
    if [ "$LOGS_COUNT" -gt 0 ]; then
        echo -e "   ${GREEN}✓${NC} Logs encontrados en Loki"
    else
        echo -e "   ${YELLOW}!${NC} Loki ready pero sin logs aún (esperando ingesta)"
    fi
else
    echo -e "   ${RED}✗${NC} Loki no está listo"
fi

# 6. License Status
echo -e "${YELLOW}6. License Status Dashboard${NC}"
LICENSE_SERVER_STATUS=$(curl -s http://localhost:5000/status 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['status'])" 2>/dev/null)
if [ "$LICENSE_SERVER_STATUS" == "healthy" ]; then
    echo -e "   ${GREEN}✓${NC} License Server: $LICENSE_SERVER_STATUS"
else
    echo -e "   ${RED}✗${NC} License Server no está healthy"
fi

# 7. Distributed Tracing (Tempo)
echo -e "${YELLOW}7. Distributed Tracing Dashboard${NC}"
TEMPO_READY=$(curl -s http://localhost:3200/ready 2>/dev/null)
TEMPO_STATUS=$(curl -s http://localhost:3200/status 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null)

if [ -n "$TEMPO_READY" ]; then
    # Verificar si hay trazas
    TRACES_COUNT=$(curl -s "http://localhost:3200/api/search?limit=5" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('traces', [])))" 2>/dev/null)
    if [ "$TRACES_COUNT" -gt 0 ]; then
        echo -e "   ${GREEN}✓${NC} Trazas encontradas: $TRACES_COUNT"
    else
        echo -e "   ${YELLOW}!${NC} Tempo ready pero sin trazas aún (esperando telemetrygen)"
    fi
else
    echo -e "   ${RED}✗${NC} Tempo no está respondiendo"
fi

echo ""
echo "========================================="
echo "VALIDACIÓN COMPLETA"
echo "========================================="
echo ""

# Alertmanager
echo -e "${YELLOW}BONUS: Alertmanager Status${NC}"
ALERTS_COUNT=$(curl -s http://localhost:9093/api/v2/alerts | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [ "$ALERTS_COUNT" -ge 0 ]; then
    echo -e "   ${GREEN}✓${NC} Alertmanager funcionando (Alertas activas: $ALERTS_COUNT)"
else
    echo -e "   ${RED}✗${NC} Alertmanager no está respondiendo"
fi

# Prometheus Rules
RULES_COUNT=$(curl -s http://localhost:9090/api/v1/rules | python3 -c "import sys, json; data=json.load(sys.stdin); print(sum(len(g['rules']) for g in data['data']['groups']))" 2>/dev/null)
if [ "$RULES_COUNT" -gt 0 ]; then
    echo -e "   ${GREEN}✓${NC} Reglas de alertas cargadas: $RULES_COUNT"
else
    echo -e "   ${RED}✗${NC} No se cargaron reglas de alertas"
fi

echo ""
