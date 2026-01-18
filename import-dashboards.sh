#!/bin/bash

# Script para importar dashboards de Grafana automáticamente
# Requiere: GRAFANA_API_TOKEN configurado

set -e

GRAFANA_URL="http://localhost:80"
DASHBOARDS_DIR="./grafana-dashboards"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 RHINOMETRIC Dashboard Import Script${NC}"
echo ""

# Verificar si existe el token
if [ -z "$GRAFANA_API_TOKEN" ]; then
    echo -e "${RED}❌ ERROR: GRAFANA_API_TOKEN no está configurado${NC}"
    echo ""
    echo "Por favor, sigue las instrucciones en HOW_TO_GET_GRAFANA_TOKEN.md"
    echo "y luego ejecuta:"
    echo ""
    echo "export GRAFANA_API_TOKEN=\"tu-token-aqui\""
    echo "./import-dashboards.sh"
    exit 1
fi

# Verificar si Grafana está corriendo
echo -e "${YELLOW}📡 Verificando conexión a Grafana...${NC}"
if ! curl -s -f "$GRAFANA_URL/api/health" > /dev/null; then
    echo -e "${RED}❌ ERROR: No se puede conectar a Grafana en $GRAFANA_URL${NC}"
    echo ""
    echo "Verifica que Grafana esté corriendo:"
    echo "docker ps | grep grafana"
    exit 1
fi
echo -e "${GREEN}✅ Grafana está corriendo${NC}"
echo ""

# Función para importar un dashboard
import_dashboard() {
    local file=$1
    local name=$(basename "$file" .json)
    
    echo -e "${YELLOW}📊 Importando: $name${NC}"
    
    response=$(curl -s -X POST \
        -H "Authorization: Bearer $GRAFANA_API_TOKEN" \
        -H "Content-Type: application/json" \
        -d @"$file" \
        "$GRAFANA_URL/api/dashboards/db")
    
    if echo "$response" | grep -q '"status":"success"'; then
        uid=$(echo "$response" | grep -o '"uid":"[^"]*"' | cut -d'"' -f4)
        url=$(echo "$response" | grep -o '"url":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✅ Dashboard importado: $name${NC}"
        echo -e "   UID: $uid"
        echo -e "   URL: $GRAFANA_URL$url"
    else
        echo -e "${RED}❌ Error importando: $name${NC}"
        echo "$response" | grep -o '"message":"[^"]*"' | cut -d'"' -f4
    fi
    echo ""
}

# Verificar si existe el directorio de dashboards
if [ ! -d "$DASHBOARDS_DIR" ]; then
    echo -e "${RED}❌ ERROR: Directorio $DASHBOARDS_DIR no existe${NC}"
    exit 1
fi

# Importar todos los dashboards
echo -e "${GREEN}📂 Importando dashboards desde: $DASHBOARDS_DIR${NC}"
echo ""

dashboard_count=0
for dashboard in "$DASHBOARDS_DIR"/*.json; do
    if [ -f "$dashboard" ]; then
        import_dashboard "$dashboard"
        ((dashboard_count++))
    fi
done

if [ $dashboard_count -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No se encontraron dashboards en $DASHBOARDS_DIR${NC}"
else
    echo -e "${GREEN}✅ $dashboard_count dashboard(s) importado(s) exitosamente${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Proceso completado!${NC}"
echo ""
echo "Accede a tus dashboards en: $GRAFANA_URL/dashboards"
