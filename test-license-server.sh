#!/bin/bash
# 🦏 RHINOMETRIC LICENSE SERVER - TEST SCRIPT
# Script de prueba para verificar el servidor de licencias

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║        🦏 RHINOMETRIC LICENSE SERVER TEST                ║"
echo "║        Testing License Generation & Validation           ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

LICENSE_SERVER="http://localhost:5000"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check${NC}"
response=$(curl -s -w "\n%{http_code}" "$LICENSE_SERVER/health")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✅ Health check OK${NC}"
    echo "$body" | jq '.'
else
    echo -e "${RED}❌ Health check FAILED (HTTP $http_code)${NC}"
    exit 1
fi

echo ""
echo "─────────────────────────────────────────────────────────────"
echo ""

# Test 2: Generar licencia trial
echo -e "${YELLOW}Test 2: Generar Licencia Trial${NC}"
response=$(curl -s -w "\n%{http_code}" -X POST "$LICENSE_SERVER/api/license/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test_Customer_Demo",
    "license_type": "trial",
    "days": 180
  }')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "201" ]; then
    echo -e "${GREEN}✅ Licencia generada correctamente${NC}"
    echo "$body" | jq '.'
    
    # Guardar license_key para validación
    LICENSE_KEY=$(echo "$body" | jq -r '.license_key')
else
    echo -e "${RED}❌ Error generando licencia (HTTP $http_code)${NC}"
    echo "$body"
    exit 1
fi

echo ""
echo "─────────────────────────────────────────────────────────────"
echo ""

# Test 3: Validar licencia
echo -e "${YELLOW}Test 3: Validar Licencia${NC}"
response=$(curl -s -w "\n%{http_code}" -X POST "$LICENSE_SERVER/api/license/validate" \
  -H "Content-Type: application/json" \
  -d "{
    \"license_key\": \"$LICENSE_KEY\"
  }")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "200" ]; then
    valid=$(echo "$body" | jq -r '.valid')
    if [ "$valid" == "true" ]; then
        echo -e "${GREEN}✅ Licencia válida${NC}"
        echo "$body" | jq '.'
    else
        echo -e "${RED}❌ Licencia inválida${NC}"
        echo "$body" | jq '.'
        exit 1
    fi
else
    echo -e "${RED}❌ Error validando licencia (HTTP $http_code)${NC}"
    echo "$body"
    exit 1
fi

echo ""
echo "─────────────────────────────────────────────────────────────"
echo ""

# Test 4: Obtener estado de licencia
echo -e "${YELLOW}Test 4: Estado de Licencia${NC}"
response=$(curl -s -w "\n%{http_code}" "$LICENSE_SERVER/api/license/status/Test_Customer_Demo")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✅ Estado obtenido correctamente${NC}"
    echo "$body" | jq '.'
else
    echo -e "${RED}❌ Error obteniendo estado (HTTP $http_code)${NC}"
    echo "$body"
    exit 1
fi

echo ""
echo "─────────────────────────────────────────────────────────────"
echo ""

# Test 5: Listar todas las licencias
echo -e "${YELLOW}Test 5: Listar Licencias${NC}"
response=$(curl -s -w "\n%{http_code}" "$LICENSE_SERVER/api/license/list")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✅ Lista obtenida correctamente${NC}"
    echo "$body" | jq '.'
else
    echo -e "${RED}❌ Error listando licencias (HTTP $http_code)${NC}"
    echo "$body"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "${GREEN}🎉 TODOS LOS TESTS PASARON EXITOSAMENTE${NC}"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📧 Soporte: soporte@rhinometric.com"
echo "💼 Ventas: ventas@rhinometric.com"
echo ""
