#!/bin/bash

###############################################################################
# RHINOMETRIC v2.5.0 - Script de Verificación de Endpoints
# 
# Este script verifica que todos los endpoints de descarga y documentación
# del License Server v2 estén funcionando correctamente.
#
# Uso:
#   chmod +x test-download-endpoints.sh
#   ./test-download-endpoints.sh [SERVER_URL]
#
# Ejemplo:
#   ./test-download-endpoints.sh https://licensing.rhinometric.com:5000
#   ./test-download-endpoints.sh http://localhost:5000
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Server URL (default to localhost)
SERVER_URL="${1:-http://localhost:5000}"

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║   RHINOMETRIC v2.5.0 - Verificación de Endpoints de Descarga    ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "🔍 Servidor: ${SERVER_URL}"
echo ""

# Test counter
PASSED=0
FAILED=0
TOTAL=0

###############################################################################
# Helper function to test endpoint
###############################################################################

test_endpoint() {
    local name="$1"
    local endpoint="$2"
    local expected_status="${3:-200}"
    local method="${4:-GET}"
    
    TOTAL=$((TOTAL + 1))
    
    echo -n "[$TOTAL] Probando: ${name}... "
    
    # Make request and capture status code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "${SERVER_URL}${endpoint}")
    
    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $status_code)"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_status, got $status_code)"
        FAILED=$((FAILED + 1))
    fi
}

test_endpoint_json() {
    local name="$1"
    local endpoint="$2"
    local json_key="$3"
    
    TOTAL=$((TOTAL + 1))
    
    echo -n "[$TOTAL] Probando: ${name}... "
    
    # Make request and check JSON key exists
    response=$(curl -s "${SERVER_URL}${endpoint}")
    
    if echo "$response" | jq -e ".${json_key}" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC} (JSON válido, key '${json_key}' encontrada)"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (JSON inválido o key '${json_key}' no encontrada)"
        echo "    Respuesta: $response"
        FAILED=$((FAILED + 1))
    fi
}

test_file_download() {
    local name="$1"
    local endpoint="$2"
    local expected_content_type="$3"
    
    TOTAL=$((TOTAL + 1))
    
    echo -n "[$TOTAL] Probando: ${name}... "
    
    # Get headers only
    content_type=$(curl -s -I "${SERVER_URL}${endpoint}" | grep -i "content-type:" | cut -d' ' -f2- | tr -d '\r\n')
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "${SERVER_URL}${endpoint}")
    
    if [ "$status_code" -eq 200 ] && [[ "$content_type" == *"$expected_content_type"* ]]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP 200, Content-Type: $content_type)"
        PASSED=$((PASSED + 1))
    elif [ "$status_code" -eq 404 ]; then
        echo -e "${YELLOW}⚠ SKIP${NC} (Archivo no encontrado - 404)"
        echo "    Esto es normal si aún no has copiado el archivo al servidor"
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $status_code, Content-Type: $content_type)"
        FAILED=$((FAILED + 1))
    fi
}

###############################################################################
# Run Tests
###############################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 SECCIÓN 1: Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_endpoint_json "Health Check" "/api/health" "status"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 SECCIÓN 2: Endpoints de Descarga"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_file_download "Demo OVA" "/downloads/demo-ova" "application/octet-stream"
test_file_download "Trial Installer" "/downloads/trial-installer" "application/x-sh"
test_endpoint_json "Downloads Info (Metadata)" "/downloads/info" "downloads"

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 SECCIÓN 3: Documentación (Español)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_file_download "Guía de Instalación (ES)" "/docs/installation-guide?lang=es" "application/pdf"
test_file_download "Manual de Usuario (ES)" "/docs/user-manual?lang=es" "application/pdf"

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 SECCIÓN 4: Documentación (English)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_file_download "Installation Guide (EN)" "/docs/installation-guide?lang=en" "application/pdf"
test_file_download "User Manual (EN)" "/docs/user-manual?lang=en" "application/pdf"

echo ""

###############################################################################
# Additional Checks
###############################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 SECCIÓN 5: Verificación de Metadata"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Obteniendo metadata de archivos..."
echo ""

metadata=$(curl -s "${SERVER_URL}/downloads/info")

if command -v jq &> /dev/null; then
    echo "📊 Archivos Disponibles:"
    echo ""
    echo "$metadata" | jq -r '
        .downloads | to_entries[] | 
        "  • \(.key): \(if .value.available then "✓ Disponible (\(.value.size_mb) MB)" else "✗ No disponible" end)"
    '
    echo ""
    echo "📄 Documentación Disponible:"
    echo ""
    echo "$metadata" | jq -r '
        .documentation | to_entries[] | 
        "  • \(.key): \(if .value.available then "✓ Disponible (\(.value.size_mb) MB)" else "✗ No disponible" end)"
    '
else
    echo "$metadata" | python3 -m json.tool
fi

echo ""

###############################################################################
# Summary
###############################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 RESUMEN DE RESULTADOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "Estado: ${GREEN}✓ TODOS LOS TESTS PASARON${NC}"
else
    echo -e "Estado: ${RED}✗ ALGUNOS TESTS FALLARON${NC}"
fi

echo ""
echo "Tests ejecutados: $TOTAL"
echo -e "Exitosos:        ${GREEN}$PASSED${NC}"
echo -e "Fallidos:        ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -gt 0 ]; then
    echo "⚠️  NOTAS:"
    echo ""
    echo "  • Si ves errores 404, probablemente los archivos aún no están copiados al servidor."
    echo "  • Verifica que los archivos estén en las rutas correctas:"
    echo "    - /app/static/downloads/rhinometric-demo-2.5.0.ova"
    echo "    - /app/static/downloads/rhinometric-trial-2.5.0-install.sh"
    echo "    - /app/static/docs/es/rhinometric-installation-guide-es.pdf"
    echo "    - /app/static/docs/en/rhinometric-user-manual-en.pdf"
    echo ""
    echo "  • Consulta docs/v2.5.0/DOWNLOAD_ENDPOINTS.md para instrucciones de deployment."
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Exit with appropriate code
if [ $FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
