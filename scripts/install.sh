#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
#  RHINOMETRIC v2.1.0 - ONE-COMMAND INSTALLER (Linux/macOS)
# ═══════════════════════════════════════════════════════════════════════════
set -e

echo "════════════════════════════════════════════════════════════════════════"
echo " 🦏 RHINOMETRIC v2.1.0 - Enterprise Observability Platform"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# ───────────────────────────────────────────────────────────────────────────
# 1. VALIDATE PREREQUISITES
# ───────────────────────────────────────────────────────────────────────────
echo "📋 [1/5] Validando prerequisitos..."

if ! command -v docker &> /dev/null; then
    echo "❌ ERROR: Docker no está instalado"
    echo "   Instala Docker Desktop desde: https://docker.com/get-started"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "❌ ERROR: Docker Compose no está disponible"
    echo "   Actualiza Docker a versión 24.0+ que incluye Compose v2"
    exit 1
fi

DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+' | head -1)
echo "   ✅ Docker ${DOCKER_VERSION} detectado"

# ───────────────────────────────────────────────────────────────────────────
# 2. SETUP ENVIRONMENT
# ───────────────────────────────────────────────────────────────────────────
echo ""
echo "⚙️  [2/5] Configurando entorno..."

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "   ✅ Archivo .env creado desde .env.example"
        echo "   ⚠️  IMPORTANTE: Edita .env y configura tus credenciales"
        echo ""
        read -p "   Presiona Enter para continuar con valores por defecto o Ctrl+C para editar primero..."
    else
        echo "   ❌ ERROR: No se encontró .env.example"
        exit 1
    fi
else
    echo "   ✅ Archivo .env existente (no se sobrescribe)"
fi

# ───────────────────────────────────────────────────────────────────────────
# 3. CREATE DATA DIRECTORIES
# ───────────────────────────────────────────────────────────────────────────
echo ""
echo "📁 [3/5] Creando directorios de datos..."

DATA_DIR="${HOME}/rhinometric_data_v2.1"
mkdir -p "${DATA_DIR}"/{grafana,prometheus,loki,tempo,postgres,redis,license-server}

echo "   ✅ Directorios creados en: ${DATA_DIR}"

# ───────────────────────────────────────────────────────────────────────────
# 4. START SERVICES
# ───────────────────────────────────────────────────────────────────────────
echo ""
echo "🚀 [4/5] Iniciando servicios Docker..."

cd deploy
docker compose -f docker-compose.yml up -d

echo "   ✅ Contenedores iniciados"

# ───────────────────────────────────────────────────────────────────────────
# 5. VERIFY INSTALLATION
# ───────────────────────────────────────────────────────────────────────────
echo ""
echo "🔍 [5/5] Verificando instalación..."
sleep 10

RUNNING_CONTAINERS=$(docker ps --format '{{.Names}}' | grep rhinometric | wc -l)
echo "   ✅ Contenedores activos: ${RUNNING_CONTAINERS}"

# ───────────────────────────────────────────────────────────────────────────
# SUCCESS
# ───────────────────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo " ✅ INSTALACIÓN COMPLETADA"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "📍 ACCESOS:"
echo "   • Grafana:        http://localhost:3000"
echo "   • Prometheus:     http://localhost:9090"
echo "   • Loki:           http://localhost:3100"
echo "   • License Server: http://localhost:5000"
echo "   • License UI:     http://localhost:8092"
echo ""
echo "🔐 CREDENCIALES GRAFANA:"
echo "   Usuario:    $(grep GF_SECURITY_ADMIN_USER .env | cut -d'=' -f2 || echo 'admin')"
echo "   Contraseña: $(grep GF_SECURITY_ADMIN_PASSWORD .env | cut -d'=' -f2 || echo 'Ver archivo .env')"
echo ""
echo "📚 DOCUMENTACIÓN: https://github.com/Rafael2712/rhinometric-overview"
echo "💬 SOPORTE: rafael.canelon@rhinometric.com"
echo ""
echo "════════════════════════════════════════════════════════════════════════"
