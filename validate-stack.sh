#!/bin/bash
# ==============================================================================
# RHINOMETRIC TRIAL v2.0.0 - QUICK VALIDATION SCRIPT
# ==============================================================================
# Script rápido para validar que los 16 servicios estén operativos
# ==============================================================================

set -euo pipefail

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================"
echo "RHINOMETRIC TRIAL v2.0.0 - VALIDATION"
echo -e "========================================${NC}"
echo ""

# Contador de servicios
TOTAL=16
HEALTHY=0
UNHEALTHY=0

# Array de servicios esperados
SERVICES=(
    "rhinometric-license-server"
    "rhinometric-postgres"
    "rhinometric-redis"
    "rhinometric-prometheus"
    "rhinometric-loki"
    "rhinometric-tempo"
    "rhinometric-telemetrygen"
    "rhinometric-grafana"
    "rhinometric-alertmanager"
    "rhinometric-node-exporter"
    "rhinometric-cadvisor"
    "rhinometric-blackbox-exporter"
    "rhinometric-postgres-exporter"
    "rhinometric-license-dashboard"
    "rhinometric-nginx"
    "rhinometric-promtail"
)

echo -e "${BLUE}Verificando estado de contenedores...${NC}"
echo ""

# Verificar cada servicio
for service in "${SERVICES[@]}"; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "missing")
    
    if [ "$STATUS" = "healthy" ]; then
        echo -e "  ${GREEN}✓${NC} $service: ${GREEN}HEALTHY${NC}"
        ((HEALTHY++))
    elif [ "$STATUS" = "missing" ]; then
        echo -e "  ${RED}✗${NC} $service: ${RED}MISSING${NC}"
        ((UNHEALTHY++))
    elif [ "$STATUS" = "starting" ]; then
        echo -e "  ${YELLOW}◐${NC} $service: ${YELLOW}STARTING${NC}"
        ((UNHEALTHY++))
    else
        echo -e "  ${RED}✗${NC} $service: ${RED}$STATUS${NC}"
        ((UNHEALTHY++))
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "Resultado: ${GREEN}$HEALTHY${NC}/${TOTAL} contenedores healthy"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar endpoints HTTP
echo -e "${BLUE}Verificando endpoints HTTP...${NC}"
echo ""

ENDPOINTS=(
    "Grafana:3000:/api/health"
    "Prometheus:9090:/-/healthy"
    "Loki:3100:/ready"
    "Tempo:3200:/ready"
    "Alertmanager:9093:/-/healthy"
    "License-Server:5000:/health"
    "License-Dashboard:8080:/health"
)

for endpoint_info in "${ENDPOINTS[@]}"; do
    IFS=':' read -r name port path <<< "$endpoint_info"
    
    if curl -sf "http://localhost:$port$path" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $name (localhost:$port$path)"
    else
        echo -e "  ${RED}✗${NC} $name (localhost:$port$path)"
    fi
done

echo ""

# Verificar modo oscuro de Grafana
echo -e "${BLUE}Verificando configuración de Grafana...${NC}"
GRAFANA_THEME=$(docker exec rhinometric-grafana env 2>/dev/null | grep GF_USERS_DEFAULT_THEME | cut -d= -f2 || echo "unknown")
if [ "$GRAFANA_THEME" = "dark" ]; then
    echo -e "  ${GREEN}✓${NC} Modo oscuro: ${GREEN}HABILITADO${NC}"
else
    echo -e "  ${RED}✗${NC} Modo oscuro: ${RED}$GRAFANA_THEME${NC}"
fi

echo ""

# Verificar persistencia de datos
echo -e "${BLUE}Verificando persistencia de datos...${NC}"
DATA_DIR="${HOME}/rhinometric_data"

if [ -d "$DATA_DIR" ]; then
    TOTAL_SIZE=$(du -sh "$DATA_DIR" 2>/dev/null | cut -f1 || echo "N/A")
    echo -e "  ${GREEN}✓${NC} Directorio de datos: $DATA_DIR"
    echo -e "  ${GREEN}✓${NC} Tamaño total: $TOTAL_SIZE"
    echo ""
    echo "  Desglose por servicio:"
    du -sh "$DATA_DIR"/* 2>/dev/null | while read -r size dir; do
        echo "    • $(basename "$dir"): $size"
    done
else
    echo -e "  ${RED}✗${NC} Directorio de datos no encontrado: $DATA_DIR"
fi

echo ""
echo -e "${BLUE}========================================${NC}"

if [ $HEALTHY -eq $TOTAL ]; then
    echo -e "${GREEN}✅ TODOS LOS SERVICIOS OPERATIVOS${NC}"
else
    echo -e "${YELLOW}⚠️  $UNHEALTHY SERVICIOS REQUIEREN ATENCIÓN${NC}"
fi

echo -e "${BLUE}========================================${NC}"
echo ""

# Mostrar accesos
echo -e "${BLUE}Acceso a interfaces web:${NC}"
echo "  • Grafana:            http://localhost:3000"
echo "  • Prometheus:         http://localhost:9090"
echo "  • Alertmanager:       http://localhost:9093"
echo "  • License Dashboard:  http://localhost:8080"
echo ""

exit 0
