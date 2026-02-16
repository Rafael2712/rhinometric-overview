#!/bin/bash

# ============================================
# RHINOMETRIC TRIAL - INSTALADOR SIMPLIFICADO
# Versión Trial 6 Meses (180 días)
# Compatible: macOS, Linux
# ============================================

set -e

# Colores para terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  🦏 RHINOMETRIC TRIAL - INSTALADOR"
echo "  Plataforma de Observabilidad"
echo "  Versión: Trial 6 Meses (180 días)"
echo "════════════════════════════════════════════════════════════"
echo ""

# 1. VERIFICAR DOCKER
echo -e "${BLUE}[1/7]${NC} Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado${NC}"
    echo "   Instalar desde: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker no está corriendo${NC}"
    echo "   Por favor inicia Docker Desktop"
    exit 1
fi
echo -e "${GREEN}✅ Docker detectado y corriendo${NC}"

# 2. VERIFICAR DOCKER COMPOSE
echo -e "${BLUE}[2/7]${NC} Verificando Docker Compose..."
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo -e "${RED}❌ Docker Compose no está instalado${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose detectado${NC}"

# 3. VERIFICAR ARCHIVOS
echo -e "${BLUE}[3/7]${NC} Verificando archivos..."
REQUIRED_FILES=(
    "config/prometheus-saas.yml"
    "config/loki-saas.yml"
    "config/tempo-saas.yml"
    "config/alertmanager-saas.yml"
    "config/nginx-trial.conf"
    "docker-compose-trial.yml"
)

MISSING=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}   ❌ Falta: $file${NC}"
        MISSING=1
    fi
done

if [ $MISSING -eq 1 ]; then
    echo -e "${RED}❌ Archivos faltantes detectados${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Todos los archivos presentes${NC}"

# 4. CREAR DIRECTORIOS
echo -e "${BLUE}[4/7]${NC} Creando directorios..."
mkdir -p certs licenses init-db data/postgres data/grafana data/prometheus data/loki data/tempo 2>/dev/null || true
echo -e "${GREEN}✅ Directorios creados${NC}"

# 5. GENERAR .env
echo -e "${BLUE}[5/7]${NC} Configurando variables de entorno..."
if [ ! -f .env ]; then
    # Compatible con macOS y Linux
    POSTGRES_PASS=$(LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 25)
    GRAFANA_PASS=$(LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 16)
    JWT_SEC=$(LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 32)
    
    cat > .env << EOF
# Rhinometric Trial Configuration - Generado $(date +%Y-%m-%d)
POSTGRES_PASSWORD=${POSTGRES_PASS}
GRAFANA_PASSWORD=${GRAFANA_PASS}
JWT_SECRET=${JWT_SEC}
GRAFANA_URL=http://localhost:3000
DASHBOARD_PORT=8080
EOF
    echo -e "${GREEN}✅ Archivo .env generado${NC}"
else
    echo -e "${GREEN}✅ Archivo .env existente (no modificado)${NC}"
fi

# Leer password de Grafana
GRAFANA_PWD=$(grep GRAFANA_PASSWORD .env | cut -d'=' -f2)

# 6. GENERAR LICENCIA TRIAL
echo -e "${BLUE}[6/7]${NC} Generando licencia trial..."
echo -n "   Nombre del cliente [Trial-Demo]: "
read CLIENT_NAME
CLIENT_NAME=${CLIENT_NAME:-Trial-Demo}

# Crear licencia simple
LICENSE_FILE="licenses/trial_${CLIENT_NAME// /_}.lic"
cat > "$LICENSE_FILE" << EOF
RHINOMETRIC TRIAL LICENSE
=========================
Cliente: ${CLIENT_NAME}
Tipo: Trial
Duración: 180 días (6 meses)
Generado: $(date +%Y-%m-%d)
Expira: $(date -v+180d +%Y-%m-%d 2>/dev/null || date -d '+180 days' +%Y-%m-%d 2>/dev/null || echo "2025-04-15")

Características:
- Grafana, Prometheus, Loki, Tempo
- Retención: 7 días
- Máximo 5 usuarios
- Soporte básico

NOTA: Esta es una versión de prueba
EOF

echo -e "${GREEN}✅ Licencia generada: $LICENSE_FILE${NC}"

# 7. INICIAR SERVICIOS
echo -e "${BLUE}[7/7]${NC} ¿Iniciar Rhinometric ahora? [S/n]: "
read START_NOW
START_NOW=${START_NOW:-S}

if [[ "$START_NOW" =~ ^[Ss]$ ]]; then
    echo ""
    echo -e "${YELLOW}🚀 Iniciando contenedores...${NC}"
    echo "   (Esto puede tardar 2-3 minutos en la primera ejecución)"
    echo ""
    
    # Detener versión anterior si existe
    $COMPOSE_CMD -f docker-compose-trial.yml down 2>/dev/null || true
    
    # Iniciar servicios
    $COMPOSE_CMD -f docker-compose-trial.yml up -d --build
    
    echo ""
    echo -e "${YELLOW}⏳ Esperando que los servicios estén listos (30 segundos)...${NC}"
    sleep 30
    
    # Mostrar estado
    echo ""
    echo -e "${BLUE}🔍 Estado de servicios:${NC}"
    $COMPOSE_CMD -f docker-compose-trial.yml ps
    
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo -e "${GREEN}  ✅ RHINOMETRIC TRIAL INICIADO${NC}"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "📊 ACCESO A SERVICIOS:"
    echo ""
    echo "  🎨 Grafana Dashboard:"
    echo "     → http://localhost:3000"
    echo "     Usuario:  admin"
    echo "     Password: ${GRAFANA_PWD}"
    echo ""
    echo "  📈 Prometheus:        → http://localhost:9090"
    echo "  📝 Loki (Logs):       → http://localhost:3100"
    echo "  🔍 Tempo (Traces):    → http://localhost:3200"
    echo "  🚨 Alertmanager:      → http://localhost:9093"
    echo "  🔑 License Dashboard: → http://localhost:8080"
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "📚 COMANDOS ÚTILES:"
    echo ""
    echo "  Ver logs:       $COMPOSE_CMD -f docker-compose-trial.yml logs -f"
    echo "  Ver estado:     $COMPOSE_CMD -f docker-compose-trial.yml ps"
    echo "  Reiniciar:      $COMPOSE_CMD -f docker-compose-trial.yml restart"
    echo "  Detener:        $COMPOSE_CMD -f docker-compose-trial.yml stop"
    echo "  Eliminar todo:  $COMPOSE_CMD -f docker-compose-trial.yml down -v"
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo ""
else
    echo ""
    echo -e "${GREEN}✅ Configuración completada${NC}"
    echo ""
    echo "Para iniciar Rhinometric:"
    echo "  $COMPOSE_CMD -f docker-compose-trial.yml up -d"
    echo ""
fi

echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
echo "   - Versión TRIAL válida por 180 días"
echo "   - NO usar en producción"
echo "   - Los puertos usados son: 3000, 3100, 3200, 8080, 9090, 9093"
echo ""
