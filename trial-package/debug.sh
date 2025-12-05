#!/bin/bash

# ════════════════════════════════════════════════════════════════════
# RHINOMETRIC TRIAL - Script de Diagnóstico Rápido
# ════════════════════════════════════════════════════════════════════

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  🔍 RHINOMETRIC - DIAGNÓSTICO DEL SISTEMA"
echo "════════════════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════════
# 1. VERIFICAR DOCKER
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}[1/7]${NC} Verificando Docker..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker no está corriendo${NC}"
    echo -e "${YELLOW}   → Inicia Docker Desktop${NC}"
    exit 1
fi

DOCKER_VERSION=$(docker --version)
echo -e "${GREEN}✅ Docker: ${DOCKER_VERSION}${NC}"

# ═══════════════════════════════════════════════════════════════════
# 2. VERIFICAR DOCKER COMPOSE
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}[2/7]${NC} Verificando Docker Compose..."

if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose no está disponible${NC}"
    exit 1
fi

COMPOSE_VERSION=$(docker compose version)
echo -e "${GREEN}✅ Compose: ${COMPOSE_VERSION}${NC}"

# ═══════════════════════════════════════════════════════════════════
# 3. VERIFICAR ARCHIVOS ESENCIALES
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}[3/7]${NC} Verificando archivos..."

MISSING_FILES=0

if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Falta: docker-compose.yml${NC}"
    MISSING_FILES=$((MISSING_FILES + 1))
fi

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠  Falta: .env (se puede generar)${NC}"
fi

if [ ! -d "config" ]; then
    echo -e "${RED}❌ Falta: directorio config/${NC}"
    MISSING_FILES=$((MISSING_FILES + 1))
fi

if [ $MISSING_FILES -gt 0 ]; then
    echo -e "${RED}❌ Faltan $MISSING_FILES archivos esenciales${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Archivos esenciales presentes${NC}"

# ═══════════════════════════════════════════════════════════════════
# 4. VALIDAR SINTAXIS DE docker-compose.yml
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}[4/7]${NC} Validando sintaxis de docker-compose.yml..."

if docker compose config > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Sintaxis válida${NC}"
else
    echo -e "${RED}❌ Error de sintaxis en docker-compose.yml${NC}"
    echo ""
    echo "Errores detectados:"
    docker compose config 2>&1 | grep -i "error" || true
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════
# 5. VERIFICAR ESTADO DE SERVICIOS
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}[5/7]${NC} Verificando estado de servicios..."

RUNNING_SERVICES=$(docker compose ps --services --filter "status=running" 2>/dev/null | wc -l)
TOTAL_SERVICES=$(docker compose ps --services 2>/dev/null | wc -l)

echo -e "   Servicios corriendo: ${RUNNING_SERVICES}/${TOTAL_SERVICES}"

if [ "$RUNNING_SERVICES" -eq 0 ]; then
    echo -e "${YELLOW}⚠  Ningún servicio está corriendo${NC}"
else
    echo -e "${GREEN}✅ Hay servicios corriendo${NC}"
    echo ""
    docker compose ps
fi

# ═══════════════════════════════════════════════════════════════════
# 6. VERIFICAR CONTENEDORES COLGADOS
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}[6/7]${NC} Verificando contenedores colgados..."

STUCK_CONTAINERS=$(docker ps -a --filter "status=created" --filter "status=restarting" --format "{{.Names}}" | grep rhinometric || true)

if [ -z "$STUCK_CONTAINERS" ]; then
    echo -e "${GREEN}✅ No hay contenedores colgados${NC}"
else
    echo -e "${YELLOW}⚠  Contenedores colgados:${NC}"
    echo "$STUCK_CONTAINERS"
    echo ""
    echo -e "${YELLOW}   Limpiando...${NC}"
    docker compose down --remove-orphans
    echo -e "${GREEN}✅ Limpieza completada${NC}"
fi

# ═══════════════════════════════════════════════════════════════════
# 7. VERIFICAR PUERTOS OCUPADOS
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}[7/7]${NC} Verificando puertos ocupados..."

PORTS_TO_CHECK=(3000 9090 3100 3200 9093 8080 80)
PORTS_IN_USE=0

for PORT in "${PORTS_TO_CHECK[@]}"; do
    if lsof -i ":$PORT" &> /dev/null; then
        PROCESS=$(lsof -i ":$PORT" | tail -n 1 | awk '{print $1}')
        echo -e "${YELLOW}⚠  Puerto $PORT ocupado por: $PROCESS${NC}"
        PORTS_IN_USE=$((PORTS_IN_USE + 1))
    fi
done

if [ $PORTS_IN_USE -eq 0 ]; then
    echo -e "${GREEN}✅ Todos los puertos están libres${NC}"
else
    echo -e "${YELLOW}⚠  Hay $PORTS_IN_USE puertos ocupados${NC}"
fi

# ═══════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  📊 RESUMEN DEL DIAGNÓSTICO"
echo "════════════════════════════════════════════════════════════════"
echo ""

if [ "$RUNNING_SERVICES" -gt 0 ]; then
    echo -e "${GREEN}✅ ESTADO: RHINOMETRIC ESTÁ CORRIENDO${NC}"
    echo ""
    echo "Accede a:"
    echo -e "  🎨 Grafana: ${BLUE}http://localhost:3000${NC}"
    echo -e "  📊 Dashboard Licencias: ${BLUE}http://localhost:8080${NC}"
    echo -e "  📈 Prometheus: ${BLUE}http://localhost:9090${NC}"
    echo ""
    echo "Credenciales:"
    echo -e "  $(cat credentials.txt 2>/dev/null || echo 'Ver archivo credentials.txt')"
else
    echo -e "${YELLOW}⚠  ESTADO: RHINOMETRIC NO ESTÁ CORRIENDO${NC}"
    echo ""
    echo "Siguiente paso:"
    echo -e "  ${GREEN}1.${NC} Si hay puertos ocupados, libéralos"
    echo -e "  ${GREEN}2.${NC} Ejecuta: ${BLUE}./start-trial.sh${NC}"
    echo -e "  ${GREEN}3.${NC} Si falla, ejecuta: ${BLUE}docker compose logs${NC}"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════════
# COMANDOS ÚTILES
# ═══════════════════════════════════════════════════════════════════

echo "Comandos útiles:"
echo ""
echo "  Ver logs en tiempo real:"
echo -e "    ${BLUE}docker compose logs -f${NC}"
echo ""
echo "  Ver logs de un servicio específico:"
echo -e "    ${BLUE}docker compose logs -f grafana${NC}"
echo ""
echo "  Reiniciar servicios:"
echo -e "    ${BLUE}docker compose restart${NC}"
echo ""
echo "  Detener servicios:"
echo -e "    ${BLUE}docker compose down${NC}"
echo ""
echo "  Ver uso de recursos:"
echo -e "    ${BLUE}docker stats${NC}"
echo ""
