#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
#  RHINOMETRIC v2.2.0 - INSTALLATION SCRIPT
# ═══════════════════════════════════════════════════════════════════════════
#
#  Este script instala RHINOMETRIC v2.2.0 Enterprise Edition
#  Sin conflictos con la versión v2.1.0 existente
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        RHINOMETRIC v2.2.0 - ENTERPRISE EDITION               ║
║                                                               ║
║   Plataforma de Observabilidad con:                          ║
║   ✓ 4 Dashboards Enterprise Pre-cargados                     ║
║   ✓ VeriVerde: Monitoreo de Sostenibilidad                   ║
║   ✓ Backup Automático                                        ║
║   ✓ IA: Detección de Anomalías                               ║
║   ✓ Reportes Ejecutivos PDF                                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Verificar Docker
echo -e "${YELLOW}[1/8] Verificando Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker no está corriendo${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker OK${NC}"

# Verificar Docker Compose
echo -e "${YELLOW}[2/8] Verificando Docker Compose...${NC}"
if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose no está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker Compose OK${NC}"

# Crear directorios de datos
echo -e "${YELLOW}[3/8] Creando directorios de datos...${NC}"
mkdir -p $HOME/rhinometric_data_v2.2/{prometheus,loki,tempo,grafana,postgres,redis,alertmanager,license-server/logs,nginx/logs}
mkdir -p $HOME/rhinometric_backups

echo -e "${GREEN}✅ Directorios creados en:${NC}"
echo "   📁 $HOME/rhinometric_data_v2.2/"
echo "   📁 $HOME/rhinometric_backups/"

# Verificar puertos disponibles
echo -e "${YELLOW}[4/8] Verificando puertos disponibles...${NC}"

check_port() {
    local port=$1
    if netstat -an 2>/dev/null | grep -q ":$port.*LISTEN" || lsof -i:$port &>/dev/null; then
        echo -e "${RED}❌ Puerto $port ya está en uso${NC}"
        return 1
    fi
    return 0
}

PORTS=(3000 5000 8092 9090 9200 8085)
PORTS_OK=true

for port in "${PORTS[@]}"; do
    if ! check_port $port; then
        PORTS_OK=false
        echo -e "${YELLOW}   ⚠️  Puerto $port en uso (puede causar conflictos)${NC}"
    fi
done

if [ "$PORTS_OK" = false ]; then
    echo ""
    echo -e "${YELLOW}ADVERTENCIA: Algunos puertos están en uso.${NC}"
    echo -e "${YELLOW}Si tienes v2.1.0 corriendo, detenla primero con:${NC}"
    echo -e "${BLUE}   cd ~/mi-proyecto/infrastructure/mi-proyecto/rhinometric-trial-v2.1.0-universal${NC}"
    echo -e "${BLUE}   docker compose down${NC}"
    echo ""
    read -p "¿Continuar de todas formas? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Construir imágenes
echo -e "${YELLOW}[5/8] Construyendo imágenes Docker...${NC}"
echo "   (Esto puede tomar 2-3 minutos)"

docker build -t rhinometric-veriverde:v2.2.0 ./rhinometric-veriverde -q
echo -e "${GREEN}   ✅ VeriVerde${NC}"

docker build -t rhinometric-ai-anomaly:v2.2.0 ./rhinometric-ai-anomaly -q
echo -e "${GREEN}   ✅ AI Anomaly${NC}"

docker build -t rhinometric-backup:v2.2.0 ./rhinometric-backup -q
echo -e "${GREEN}   ✅ Backup Service${NC}"

docker build -t rhinometric-report:v2.2.0 ./rhinometric-report -q
echo -e "${GREEN}   ✅ Report Service${NC}"

# Crear archivo .env si no existe
echo -e "${YELLOW}[6/8] Configurando variables de entorno...${NC}"
if [ ! -f .env.v2.2.0 ]; then
    cat > .env.v2.2.0 << 'ENVFILE'
# RHINOMETRIC v2.2.0 Configuration
# ═══════════════════════════════════════════════════════════════

# Database
POSTGRES_PASSWORD=rhinometric_v22_secure
REDIS_PASSWORD=redis_v22_secure

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=rhinometric_v22

# SMTP (para reportes)
SMTP_PASSWORD=271211Rc$
REPORT_RECIPIENTS=rafael.canelon@rhinometric.com

# VeriVerde (Sostenibilidad)
RENEWABLE_PERCENT=35
CO2_FACTOR=0.233

# Reportes
REPORT_SCHEDULE=weekly
ENVFILE
    echo -e "${GREEN}✅ Archivo .env.v2.2.0 creado${NC}"
else
    echo -e "${BLUE}ℹ️  Usando .env.v2.2.0 existente${NC}"
fi

# Iniciar servicios
echo -e "${YELLOW}[7/8] Iniciando RHINOMETRIC v2.2.0...${NC}"
docker compose -f docker-compose-v2.2.0.yml --env-file .env.v2.2.0 up -d

# Esperar a que los servicios estén listos
echo -e "${YELLOW}[8/8] Esperando a que los servicios estén listos...${NC}"
echo "   (Esto puede tomar 30-60 segundos)"

sleep 5

# Verificar servicios
echo ""
echo -e "${GREEN}✅ RHINOMETRIC v2.2.0 instalado correctamente!${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${BLUE}📊 ACCESO A LOS SERVICIOS${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}1. Grafana (Dashboards)${NC}"
echo "   URL: http://localhost:3000"
echo "   Usuario: admin"
echo "   Password: rhinometric_v22"
echo ""
echo -e "${GREEN}2. Prometheus (Métricas)${NC}"
echo "   URL: http://localhost:9090"
echo ""
echo -e "${GREEN}3. License Management UI${NC}"
echo "   URL: http://localhost:8092"
echo ""
echo -e "${GREEN}4. VeriVerde (Sostenibilidad)${NC}"
echo "   Métricas: http://localhost:9200/metrics"
echo "   Health: http://localhost:9200/health"
echo ""
echo -e "${GREEN}5. AI Anomaly Detector${NC}"
echo "   API: http://localhost:8085/anomalies"
echo "   Health: http://localhost:8085/health"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${BLUE}🎨 DASHBOARDS DISPONIBLES EN GRAFANA${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "   1. Executive Overview - Vista para directivos"
echo "   2. Infrastructure & Containers - Monitoreo técnico"
echo "   3. Applications & APIs - Rendimiento de apps"
echo "   4. VeriVerde Insights - Sostenibilidad ESG"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${BLUE}🛠️  COMANDOS ÚTILES${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Ver estado de servicios:"
echo "   docker compose -f docker-compose-v2.2.0.yml ps"
echo ""
echo "Ver logs:"
echo "   docker compose -f docker-compose-v2.2.0.yml logs -f"
echo ""
echo "Crear backup:"
echo "   ./scripts/rmetricctl backup"
echo ""
echo "Detener servicios:"
echo "   docker compose -f docker-compose-v2.2.0.yml down"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${YELLOW}⚠️  NOTAS IMPORTANTES${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "• Los datos se guardan en: $HOME/rhinometric_data_v2.2/"
echo "• Los backups se guardan en: $HOME/rhinometric_backups/"
echo "• Esta instalación NO interfiere con v2.1.0"
echo "• Para reportes automáticos, configura SMTP_PASSWORD en .env.v2.2.0"
echo ""
echo -e "${GREEN}🎉 Disfruta de RHINOMETRIC v2.2.0 Enterprise Edition!${NC}"
echo ""
