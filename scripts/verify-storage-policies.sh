#!/bin/bash
#
# RHINOMETRIC STORAGE POLICY VERIFICATION
# Verifica que todas las políticas de almacenamiento estén correctamente aplicadas
#
# Uso:
#   ./scripts/verify-storage-policies.sh
#

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contadores
PASSED=0
FAILED=0
WARNINGS=0

echo "=========================================="
echo " RHINOMETRIC STORAGE POLICY VERIFICATION"
echo "=========================================="
echo ""

# Función para verificar
check() {
    local name="$1"
    local command="$2"
    local expected="$3"
    
    echo -n "Verificando ${name}... "
    
    if eval "${command}" | grep -q "${expected}"; then
        echo -e "${GREEN}✓ OK${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Expected: ${expected}"
        echo "  Got: $(eval ${command})"
        ((FAILED++))
        return 1
    fi
}

check_warning() {
    local name="$1"
    local command="$2"
    local expected="$3"
    
    echo -n "Verificando ${name}... "
    
    if eval "${command}" | grep -q "${expected}"; then
        echo -e "${GREEN}✓ OK${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠ WARNING${NC}"
        echo "  Expected: ${expected}"
        ((WARNINGS++))
        return 1
    fi
}

echo "1. DOCKER LOG ROTATION"
echo "----------------------------------------"
if [ -f /etc/docker/daemon.json ]; then
    check "Docker daemon.json exists" "cat /etc/docker/daemon.json" "max-size"
    check "Log max-size configured" "cat /etc/docker/daemon.json" "50m"
    check "Log max-file configured" "cat /etc/docker/daemon.json" "max-file"
else
    echo -e "${RED}✗ /etc/docker/daemon.json no encontrado${NC}"
    ((FAILED++))
fi
echo ""

echo "2. PROMETHEUS RETENTION"
echo "----------------------------------------"
if docker ps --format '{{.Names}}' | grep -q "rhinometric-prometheus"; then
    check "Prometheus está corriendo" "docker ps --format '{{.Names}}'" "rhinometric-prometheus"
    check "Prometheus retention.time configurado" "docker inspect rhinometric-prometheus" "storage.tsdb.retention.time"
    check "Prometheus retention.size configurado" "docker inspect rhinometric-prometheus" "storage.tsdb.retention.size"
    
    # Extraer valores actuales
    PROM_TIME=$(docker inspect rhinometric-prometheus 2>/dev/null | grep -oP '(?<=storage.tsdb.retention.time=)[^"]+' | head -1 || echo "NOT_FOUND")
    PROM_SIZE=$(docker inspect rhinometric-prometheus 2>/dev/null | grep -oP '(?<=storage.tsdb.retention.size=)[^"]+' | head -1 || echo "NOT_FOUND")
    
    echo "  Configurado: time=${PROM_TIME}, size=${PROM_SIZE}"
else
    echo -e "${RED}✗ Prometheus no está corriendo${NC}"
    ((FAILED++))
fi
echo ""

echo "3. LOKI RETENTION"
echo "----------------------------------------"
if docker ps --format '{{.Names}}' | grep -q "rhinometric-loki"; then
    check "Loki está corriendo" "docker ps --format '{{.Names}}'" "rhinometric-loki"
    
    if [ -f config/loki-config.yml ]; then
        check "Loki retention_period configurado" "cat config/loki-config.yml" "retention_period"
        check "Loki compactor habilitado" "cat config/loki-config.yml" "retention_enabled: true"
        
        # Extraer valor actual
        LOKI_RETENTION=$(grep "retention_period:" config/loki-config.yml | grep -oP '\d+h' | head -1 || echo "NOT_FOUND")
        echo "  Configurado: retention=${LOKI_RETENTION}"
        
        # Verificar schema_config compatible con retención
        if grep -q "schema_config:" config/loki-config.yml; then
            if grep -A5 "schema_config:" config/loki-config.yml | grep -q "boltdb-shipper"; then
                echo -e "  ${GREEN}✓${NC} schema_config usa boltdb-shipper (compatible con retención)"
                ((PASSED++))
            else
                echo -e "  ${YELLOW}⚠${NC} schema_config podría no soportar retención (verificar)"
                ((WARNINGS++))
            fi
        fi
    else
        echo -e "${RED}✗ config/loki-config.yml no encontrado${NC}"
        ((FAILED++))
    fi
else
    echo -e "${RED}✗ Loki no está corriendo${NC}"
    ((FAILED++))
fi
echo ""

echo "4. JAEGER TTL"
echo "----------------------------------------"
if docker ps --format '{{.Names}}' | grep -q "rhinometric-jaeger"; then
    check "Jaeger está corriendo" "docker ps --format '{{.Names}}'" "rhinometric-jaeger"
    check "Jaeger BADGER_TTL configurado" "docker exec rhinometric-jaeger env" "BADGER_TTL"
    check "Jaeger BADGER_EPHEMERAL=false" "docker exec rhinometric-jaeger env" "BADGER_EPHEMERAL=false"
    
    # Extraer valores actuales
    JAEGER_TTL=$(docker exec rhinometric-jaeger env 2>/dev/null | grep "BADGER_TTL=" | cut -d'=' -f2 || echo "NOT_FOUND")
    JAEGER_EPH=$(docker exec rhinometric-jaeger env 2>/dev/null | grep "BADGER_EPHEMERAL=" | cut -d'=' -f2 || echo "NOT_FOUND")
    
    echo "  Configurado: TTL=${JAEGER_TTL}, EPHEMERAL=${JAEGER_EPH}"
else
    echo -e "${RED}✗ Jaeger no está corriendo${NC}"
    ((FAILED++))
fi
echo ""

echo "5. DISK GUARDIAN"
echo "----------------------------------------"
if [ -f /usr/local/bin/disk-guardian ]; then
    check "Disk Guardian instalado" "ls -l /usr/local/bin/disk-guardian" "disk-guardian"
    check "Disk Guardian ejecutable" "ls -l /usr/local/bin/disk-guardian" "rwxr-xr-x"
    
    if crontab -l 2>/dev/null | grep -q "disk-guardian"; then
        echo -e "${GREEN}✓ Disk Guardian en crontab${NC}"
        ((PASSED++))
        
        CRON_LINE=$(crontab -l 2>/dev/null | grep "disk-guardian" | head -1)
        echo "  Configurado: ${CRON_LINE}"
    else
        echo -e "${YELLOW}⚠ Disk Guardian NO está en crontab${NC}"
        ((WARNINGS++))
    fi
    
    # Verificar última ejecución
    if [ -f /var/log/disk-guardian.log ]; then
        LAST_RUN=$(tail -1 /var/log/disk-guardian.log)
        echo "  Última ejecución: ${LAST_RUN}"
    else
        echo -e "  ${YELLOW}⚠${NC} Log /var/log/disk-guardian.log no encontrado"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}✗ Disk Guardian no instalado en /usr/local/bin/${NC}"
    ((FAILED++))
fi
echo ""

echo "6. PROMETHEUS DISK ALERTS"
echo "----------------------------------------"
if docker ps --format '{{.Names}}' | grep -q "rhinometric-prometheus"; then
    if [ -f config/rules/disk-alerts.yml ]; then
        check "Archivo disk-alerts.yml existe" "cat config/rules/disk-alerts.yml" "DiskUsageWarning"
        
        # Verificar en Prometheus API
        if curl -s http://localhost:9090/api/v1/rules 2>/dev/null | grep -q "disk"; then
            echo -e "${GREEN}✓ Alertas cargadas en Prometheus${NC}"
            ((PASSED++))
            
            ALERT_COUNT=$(curl -s http://localhost:9090/api/v1/rules 2>/dev/null | grep -o "DiskUsage" | wc -l || echo "0")
            echo "  Alertas de disco detectadas: ${ALERT_COUNT}"
        else
            echo -e "${YELLOW}⚠ No se pudieron verificar alertas en Prometheus API${NC}"
            ((WARNINGS++))
        fi
    else
        echo -e "${RED}✗ config/rules/disk-alerts.yml no encontrado${NC}"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠ Prometheus no está corriendo, no se pueden verificar alertas${NC}"
    ((WARNINGS++))
fi
echo ""

echo "7. CONSUMO ACTUAL DE DISCO"
echo "----------------------------------------"
CURRENT_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
CURRENT_USAGE_NUM=${CURRENT_USAGE}

echo "Uso actual del disco: ${CURRENT_USAGE}%"

if [ "${CURRENT_USAGE_NUM}" -lt 70 ]; then
    echo -e "${GREEN}✓ Uso normal (< 70%)${NC}"
    ((PASSED++))
elif [ "${CURRENT_USAGE_NUM}" -lt 85 ]; then
    echo -e "${YELLOW}⚠ Warning (70-85%)${NC}"
    ((WARNINGS++))
else
    echo -e "${RED}✗ Critical (> 85%)${NC}"
    ((FAILED++))
fi

# Tamaños componentes
echo ""
echo "Tamaños de componentes principales:"
if [ -d /var/lib/docker/volumes ]; then
    LOKI_SIZE=$(docker exec rhinometric-loki du -sh /loki 2>/dev/null | awk '{print $1}' || echo "N/A")
    PROM_SIZE=$(docker exec rhinometric-prometheus du -sh /prometheus 2>/dev/null | awk '{print $1}' || echo "N/A")
    JAEGER_SIZE=$(docker exec rhinometric-jaeger du -sh /badger 2>/dev/null | awk '{print $1}' || echo "N/A")
    
    echo "  - Loki: ${LOKI_SIZE}"
    echo "  - Prometheus: ${PROM_SIZE}"
    echo "  - Jaeger: ${JAEGER_SIZE}"
fi
echo ""

echo "8. TIER CONFIGURATION"
echo "----------------------------------------"
if [ -f .env ]; then
    if grep -q "RHINO_LICENSE_TIER=" .env; then
        CURRENT_TIER=$(grep "RHINO_LICENSE_TIER=" .env | cut -d'=' -f2 | tr -d ' ')
        echo "Tier actual: ${CURRENT_TIER}"
        
        case "${CURRENT_TIER}" in
            essentials)
                echo "  Esperado: Prometheus 30d, Loki 7d, Jaeger 3d"
                ;;
            growth)
                echo "  Esperado: Prometheus 30d, Loki 5d, Jaeger 2d"
                ;;
            enterprise)
                echo "  Esperado: Prometheus 15d, Loki 3d, Jaeger 1d"
                ;;
            *)
                echo -e "${YELLOW}⚠ Tier desconocido: ${CURRENT_TIER}${NC}"
                ((WARNINGS++))
                ;;
        esac
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠ RHINO_LICENSE_TIER no configurado en .env${NC}"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠ Archivo .env no encontrado${NC}"
    ((WARNINGS++))
fi
echo ""

echo "=========================================="
echo " RESUMEN"
echo "=========================================="
echo ""
echo -e "${GREEN}✓ Passed: ${PASSED}${NC}"
if [ ${WARNINGS} -gt 0 ]; then
    echo -e "${YELLOW}⚠ Warnings: ${WARNINGS}${NC}"
fi
if [ ${FAILED} -gt 0 ]; then
    echo -e "${RED}✗ Failed: ${FAILED}${NC}"
fi
echo ""

# Exit code
if [ ${FAILED} -gt 0 ]; then
    echo "❌ VERIFICACIÓN FALLIDA: Corregir errores críticos"
    exit 1
elif [ ${WARNINGS} -gt 0 ]; then
    echo "⚠️  VERIFICACIÓN PARCIAL: Revisar warnings"
    exit 0
else
    echo "✅ VERIFICACIÓN EXITOSA: Todas las políticas aplicadas correctamente"
    exit 0
fi
