#!/usr/bin/env bash
set -euo pipefail

# RHINOMETRIC v2.5.0 - Dashboard Builder Test Script
# Propósito: Probar creación de dashboards vía backend y verificar en Grafana

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }

PASSED=0
FAILED=0

# Configuración
BUILDER_API="${BUILDER_API:-http://localhost:8001}"
GRAFANA_API="${GRAFANA_API:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-rhinometric2024}"
TIMEOUT=10

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  RHINOMETRIC Dashboard Builder - Test Script"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 1. Verificar Backend Dashboard Builder
echo "[1/6] Verificando Dashboard Builder Backend..."
if curl -sf --max-time "$TIMEOUT" "${BUILDER_API}/health" > /dev/null 2>&1; then
    log_success "Dashboard Builder responde en ${BUILDER_API}"
    ((PASSED++))
else
    log_error "Dashboard Builder NO responde en ${BUILDER_API}"
    ((FAILED++))
fi

# 2. Verificar Grafana
echo "[2/6] Verificando Grafana API..."
if curl -sf --max-time "$TIMEOUT" -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" "${GRAFANA_API}/api/health" > /dev/null 2>&1; then
    log_success "Grafana API responde en ${GRAFANA_API}"
    ((PASSED++))
else
    log_error "Grafana API NO responde en ${GRAFANA_API}"
    ((FAILED++))
fi

# 3. Crear dashboard de prueba vía Dashboard Builder
echo "[3/6] Creando dashboard de prueba vía Dashboard Builder..."
DASHBOARD_NAME="Test Dashboard $(date +%s)"
CREATE_RESPONSE=$(curl -sf --max-time "$TIMEOUT" -X POST "${BUILDER_API}/api/dashboards" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"${DASHBOARD_NAME}\",
        \"metrics\": [
            {\"name\": \"CPU Usage\", \"query\": \"rate(node_cpu_seconds_total[5m])\"},
            {\"name\": \"Memory Usage\", \"query\": \"node_memory_MemAvailable_bytes\"}
        ],
        \"datasource_uid\": \"prometheus\"
    }" 2>&1) || true

if echo "$CREATE_RESPONSE" | grep -q "uid"; then
    DASHBOARD_UID=$(echo "$CREATE_RESPONSE" | grep -o '"uid":"[^"]*"' | cut -d'"' -f4)
    log_success "Dashboard creado con UID: ${DASHBOARD_UID}"
    ((PASSED++))
else
    log_error "No se pudo crear dashboard: ${CREATE_RESPONSE}"
    ((FAILED++))
    DASHBOARD_UID=""
fi

# 4. Verificar dashboard en Grafana
if [ -n "$DASHBOARD_UID" ]; then
    echo "[4/6] Verificando dashboard en Grafana..."
    sleep 2  # Esperar a que se sincronice
    
    GRAFANA_RESPONSE=$(curl -sf --max-time "$TIMEOUT" -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
        "${GRAFANA_API}/api/dashboards/uid/${DASHBOARD_UID}" 2>&1) || true
    
    if echo "$GRAFANA_RESPONSE" | grep -q "dashboard"; then
        log_success "Dashboard ${DASHBOARD_UID} existe en Grafana"
        ((PASSED++))
    else
        log_error "Dashboard ${DASHBOARD_UID} NO existe en Grafana"
        ((FAILED++))
    fi
else
    log_warning "Saltando verificación de Grafana (no se creó dashboard)"
    echo "[4/6] SKIPPED"
fi

# 5. Verificar datasource UID en dashboard
if [ -n "$DASHBOARD_UID" ] && [ -n "$GRAFANA_RESPONSE" ]; then
    echo "[5/6] Verificando datasource UID en dashboard..."
    
    if echo "$GRAFANA_RESPONSE" | grep -q '"uid":"prometheus"'; then
        log_success "Dashboard usa datasource UID 'prometheus'"
        ((PASSED++))
    else
        log_error "Dashboard NO usa datasource UID 'prometheus'"
        ((FAILED++))
    fi
else
    log_warning "Saltando verificación de datasource (dashboard no disponible)"
    echo "[5/6] SKIPPED"
fi

# 6. Limpiar dashboard de prueba
if [ -n "$DASHBOARD_UID" ]; then
    echo "[6/6] Limpiando dashboard de prueba..."
    
    DELETE_RESPONSE=$(curl -sf --max-time "$TIMEOUT" -X DELETE \
        -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
        "${GRAFANA_API}/api/dashboards/uid/${DASHBOARD_UID}" 2>&1) || true
    
    if echo "$DELETE_RESPONSE" | grep -q "deleted"; then
        log_success "Dashboard ${DASHBOARD_UID} eliminado correctamente"
        ((PASSED++))
    else
        log_warning "No se pudo eliminar dashboard ${DASHBOARD_UID}"
    fi
else
    log_warning "Saltando limpieza (no se creó dashboard)"
    echo "[6/6] SKIPPED"
fi

# Resumen final
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  RESUMEN DE TEST DASHBOARD BUILDER"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}PASSED:${NC}    $PASSED checks"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}FAILED:${NC}    $FAILED checks"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    log_success "TEST DASHBOARD BUILDER PASSED"
    exit 0
else
    log_error "TEST DASHBOARD BUILDER FAILED"
    exit 1
fi
