#!/bin/bash

# ════════════════════════════════════════════════════════════════════════════
# RHINOMETRIC TRIAL - SCRIPT DE VALIDACIÓN
# Verifica que el paquete esté completo antes de distribuir
# ════════════════════════════════════════════════════════════════════════════

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Validando paquete Rhinometric Trial..."
echo ""

ERRORS=0
WARNINGS=0

# Archivos principales
echo "📁 Verificando archivos principales..."

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $1"
    else
        echo -e "${RED}❌${NC} $1 - FALTA"
        ERRORS=$((ERRORS + 1))
    fi
}

check_file "README.md"
check_file "start-trial.sh"
check_file "docker-compose.yml"
check_file ".env.example"

# Configs
echo ""
echo "⚙️  Verificando configuraciones..."
check_file "config/prometheus.yml"
check_file "config/loki.yml"
check_file "config/tempo.yml"
check_file "config/alertmanager.yml"
check_file "config/nginx.conf"

# Licensing
echo ""
echo "🔐 Verificando sistema de licencias..."
check_file "licensing/Dockerfile"
check_file "licensing/license_server.py"

# Dashboard
echo ""
echo "📊 Verificando dashboard..."
check_file "dashboard/Dockerfile"
check_file "dashboard/app.py"
check_file "dashboard/templates/index.html"

# Grafana
echo ""
echo "📈 Verificando Grafana provisioning..."
check_file "grafana/provisioning/datasources/datasources.yml"
check_file "grafana/provisioning/dashboards/dashboard-provider.yml"

# Init DB
echo ""
echo "🗄️  Verificando init-db..."
check_file "init-db/01-init.sql"

# Permisos ejecutables
echo ""
echo "🔑 Verificando permisos..."
if [ -x "start-trial.sh" ]; then
    echo -e "${GREEN}✅${NC} start-trial.sh es ejecutable"
else
    echo -e "${YELLOW}⚠️${NC}  start-trial.sh NO es ejecutable"
    echo "   Ejecuta: chmod +x start-trial.sh"
    WARNINGS=$((WARNINGS + 1))
fi

# Docker Compose válido
echo ""
echo "🐳 Validando docker-compose.yml..."
if docker compose -f docker-compose.yml config --quiet 2>&1 | grep -q "error"; then
    echo -e "${RED}❌${NC} docker-compose.yml tiene errores de sintaxis"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅${NC} docker-compose.yml es válido"
fi

# Archivos que NO deben existir
echo ""
echo "🚫 Verificando que archivos sensibles NO estén..."
if [ -f ".env" ]; then
    echo -e "${RED}❌${NC} .env existe - DEBE ELIMINARSE"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅${NC} .env no existe (correcto)"
fi

if [ -f "credentials.txt" ]; then
    echo -e "${RED}❌${NC} credentials.txt existe - DEBE ELIMINARSE"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅${NC} credentials.txt no existe (correcto)"
fi

if [ -d "data" ]; then
    echo -e "${YELLOW}⚠️${NC}  directorio data/ existe - debería eliminarse"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅${NC} directorio data/ no existe (correcto)"
fi

# Resumen
echo ""
echo "════════════════════════════════════════════════════════════"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ VALIDACIÓN EXITOSA${NC}"
    echo "   El paquete está listo para distribuir"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}   Advertencias: $WARNINGS${NC}"
    fi
    exit 0
else
    echo -e "${RED}❌ VALIDACIÓN FALLIDA${NC}"
    echo "   Errores encontrados: $ERRORS"
    echo "   Advertencias: $WARNINGS"
    echo ""
    echo "   Corrige los errores antes de distribuir"
    exit 1
fi
