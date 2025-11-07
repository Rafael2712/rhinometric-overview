#!/bin/bash
# ============================================
# Rhinometric v2.5.0 - Instalador Oficial Linux
# Soporta: Ubuntu 20.04+, Debian 11+, CentOS 8+, RHEL 8+
# © 2025 Rhinometric. All rights reserved.
# ============================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
VERSION="2.5.0"
REPO_URL="https://github.com/Rafael2712/mi-proyecto"
INSTALL_DIR="/opt/rhinometric"
DATA_DIR="/var/lib/rhinometric"
LOG_FILE="/var/log/rhinometric-install.log"

# Función de log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Banner
clear
echo -e "${BLUE}"
cat << "EOF"
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        🦏 RHINOMETRIC INSTALLER v2.5.0                   ║
    ║        Observability Platform - Enterprise Edition       ║
    ║        © 2025 Rhinometric. All rights reserved.          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

# Iniciar log
mkdir -p "$(dirname "$LOG_FILE")"
log "Starting Rhinometric v$VERSION installation..."

# Verificar root
if [ "$EUID" -ne 0 ]; then
    error "Este instalador debe ejecutarse como root"
    error "Ejecuta: sudo $0"
    exit 1
fi

# Detectar OS
log "Detectando sistema operativo..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
    log "Detectado: $PRETTY_NAME"
else
    error "No se pudo detectar el sistema operativo"
    exit 1
fi

# Verificar arquitectura
ARCH=$(uname -m)
if [ "$ARCH" != "x86_64" ] && [ "$ARCH" != "aarch64" ]; then
    error "Arquitectura no soportada: $ARCH"
    error "Rhinometric requiere x86_64 o aarch64"
    exit 1
fi
log "Arquitectura: $ARCH ✓"

# Verificar requisitos
log "Verificando requisitos del sistema..."

# RAM: 8GB mínimo
TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM" -lt 7 ]; then
    error "RAM insuficiente: ${TOTAL_RAM}GB (mínimo 8GB)"
    exit 1
fi
log "RAM: ${TOTAL_RAM}GB ✓"

# Disco: 50GB mínimo
FREE_DISK=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$FREE_DISK" -lt 50 ]; then
    error "Espacio en disco insuficiente: ${FREE_DISK}GB (mínimo 50GB)"
    exit 1
fi
log "Disco libre: ${FREE_DISK}GB ✓"

# Verificar Docker
log "Verificando Docker..."
if ! command -v docker &> /dev/null; then
    warning "Docker no encontrado. Instalando..."
    
    case "$OS" in
        ubuntu|debian)
            apt-get update -qq
            apt-get install -y ca-certificates curl gnupg lsb-release
            mkdir -p /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$OS/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            apt-get update -qq
            apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        centos|rhel|rocky|almalinux)
            yum install -y yum-utils
            yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            systemctl start docker
            systemctl enable docker
            ;;
        *)
            error "Distribución no soportada para instalación automática de Docker"
            error "Instala Docker manualmente: https://docs.docker.com/engine/install/"
            exit 1
            ;;
    esac
    
    log "Docker instalado ✓"
else
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    log "Docker $DOCKER_VERSION encontrado ✓"
fi

# Verificar Docker corriendo
if ! docker info &> /dev/null; then
    log "Iniciando Docker..."
    systemctl start docker
    sleep 3
    if ! docker info &> /dev/null; then
        error "Docker no pudo iniciarse"
        error "Verifica: sudo systemctl status docker"
        exit 1
    fi
fi

# Verificar Docker Compose
log "Verificando Docker Compose..."
if ! docker compose version &> /dev/null; then
    error "Docker Compose no encontrado"
    error "Instala Docker Compose v2.20+: https://docs.docker.com/compose/install/"
    exit 1
fi
COMPOSE_VERSION=$(docker compose version --short)
log "Docker Compose $COMPOSE_VERSION encontrado ✓"

# Crear directorios
log "Creando directorios..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$DATA_DIR"/{postgres,grafana,prometheus,loki,tempo,licenses,backups}
chmod 755 "$INSTALL_DIR"
chmod 755 "$DATA_DIR"
log "Directorios creados ✓"

# Descargar configuración
log "Descargando Rhinometric desde GitHub..."
cd "$INSTALL_DIR"

if [ -d ".git" ]; then
    log "Repositorio existente, actualizando..."
    git fetch origin main --quiet
    git reset --hard origin/main --quiet
else
    log "Clonando repositorio..."
    git clone --depth 1 --branch main "$REPO_URL.git" . --quiet 2>&1 | tee -a "$LOG_FILE"
fi

# Ir al directorio correcto
cd infrastructure/mi-proyecto
log "Archivos descargados ✓"

# Generar .env con valores seguros
log "Generando configuración segura..."
POSTGRES_PWD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
REDIS_PWD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
JWT_SECRET=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-40)

cat > .env << ENVEOF
# Rhinometric v$VERSION - Generated Configuration
# Generated: $(date)

# SMTP Configuration (COMPLETAR DESPUÉS)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=licenses@rhinometric.io

# Database (AUTO-GENERATED)
POSTGRES_PASSWORD=$POSTGRES_PWD
REDIS_PASSWORD=$REDIS_PWD
JWT_SECRET=$JWT_SECRET

# License
LICENSE_DURATION_DAYS=180

# Grafana
GF_SECURITY_ADMIN_PASSWORD=admin

# Retention Policies
PROMETHEUS_RETENTION_DAYS=15d
PROMETHEUS_RETENTION_SIZE=10GB
LOKI_RETENTION_DAYS=168h
TEMPO_RETENTION_DAYS=72h
ENVEOF

chmod 600 .env
log "Configuración generada ✓"
log "⚠️  Passwords guardados en: $INSTALL_DIR/infrastructure/mi-proyecto/.env"

# Construir imágenes
log "Construyendo imágenes Docker..."
log "⏳ Esto puede tomar 5-10 minutos dependiendo de tu conexión..."
docker compose -f docker-compose.yml -f docker-compose.override.yml build 2>&1 | tee -a "$LOG_FILE" | grep -E "(Building|Successfully|ERROR)" || true

# Iniciar servicios
log "Iniciando servicios Rhinometric..."
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d 2>&1 | tee -a "$LOG_FILE"

# Esperar servicios
log "⏳ Esperando que los servicios estén listos (60 segundos)..."
for i in {1..6}; do
    echo -n "."
    sleep 10
done
echo ""

# Verificar servicios
log "Verificando salud de servicios..."
FAILED=0
SERVICES=(
    "3000:Grafana"
    "9090:Prometheus"
    "3100:Loki"
    "3200:Tempo"
    "8090:License Server"
    "8001:Dashboard Builder"
    "5432:PostgreSQL"
    "6379:Redis"
)

for service in "${SERVICES[@]}"; do
    PORT="${service%%:*}"
    NAME="${service##*:}"
    
    if timeout 5 bash -c "cat < /dev/null > /dev/tcp/localhost/$PORT" 2>/dev/null; then
        log "$NAME (puerto $PORT) ✓"
    else
        warning "$NAME (puerto $PORT) no responde"
        FAILED=$((FAILED + 1))
    fi
done

# Crear script de uninstall
cat > "$INSTALL_DIR/uninstall.sh" << 'UNINSTALL'
#!/bin/bash
set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}"
echo "═══════════════════════════════════════════════════════════"
echo "  🗑️  RHINOMETRIC UNINSTALLER"
echo "═══════════════════════════════════════════════════════════"
echo -e "${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Ejecuta como root: sudo $0"
    exit 1
fi

echo -e "${YELLOW}ADVERTENCIA:${NC} Esto eliminará:"
echo "  • Todos los contenedores"
echo "  • Todas las imágenes Docker"
echo "  • Todos los datos en /var/lib/rhinometric"
echo "  • Archivos en /opt/rhinometric"
echo ""
read -p "¿Continuar? Escribe 'YES': " confirm

if [ "$confirm" != "YES" ]; then
    echo "Cancelado."
    exit 0
fi

echo -e "${GREEN}[1/4]${NC} Deteniendo servicios..."
cd /opt/rhinometric/infrastructure/mi-proyecto
docker compose down -v 2>/dev/null || true

echo -e "${GREEN}[2/4]${NC} Eliminando imágenes..."
docker images | grep rhinometric | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true

echo -e "${GREEN}[3/4]${NC} Eliminando datos..."
rm -rf /var/lib/rhinometric

echo -e "${GREEN}[4/4]${NC} Eliminando instalación..."
rm -rf /opt/rhinometric

echo ""
echo -e "${GREEN}✅ Rhinometric desinstalado completamente${NC}"
UNINSTALL

chmod +x "$INSTALL_DIR/uninstall.sh"

# Resumen
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}║              ✅ INSTALACIÓN COMPLETADA                     ║${NC}"
else
    echo -e "${YELLOW}║         ⚠️  INSTALACIÓN CON ADVERTENCIAS ($FAILED servicios)    ║${NC}"
fi
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

SERVER_IP=$(hostname -I | awk '{print $1}')

log "Rhinometric v$VERSION instalado en: $INSTALL_DIR"
log "Datos en: $DATA_DIR"
echo ""
echo -e "${BLUE}📊 ACCESO A LA PLATAFORMA:${NC}"
echo "  • Grafana:          http://$SERVER_IP:3000"
echo "  • Prometheus:       http://$SERVER_IP:9090"
echo "  • License Server:   http://$SERVER_IP:8090"
echo "  • Dashboard Builder: http://$SERVER_IP:8001"
echo ""
echo -e "${BLUE}🔐 CREDENCIALES INICIALES:${NC}"
echo "  • Usuario: ${GREEN}admin${NC}"
echo "  • Contraseña: ${GREEN}admin${NC} ${YELLOW}(⚠️  CAMBIAR EN PRIMER LOGIN)${NC}"
echo ""
echo -e "${BLUE}📧 CONFIGURAR SMTP (OPCIONAL):${NC}"
echo "  Edita: ${GREEN}$INSTALL_DIR/infrastructure/mi-proyecto/.env${NC}"
echo "  Variables: SMTP_USER, SMTP_PASSWORD"
echo "  Luego: ${GREEN}cd $INSTALL_DIR/infrastructure/mi-proyecto && docker compose restart rhinometric-license-server-v2${NC}"
echo ""
echo -e "${BLUE}📚 PRÓXIMOS PASOS:${NC}"
echo "  1. Accede a Grafana en tu navegador"
echo "  2. Genera una licencia en License Server"
echo "  3. Lee la documentación: https://github.com/Rafael2712/mi-proyecto/wiki"
echo ""
echo -e "${BLUE}🛠️  COMANDOS ÚTILES:${NC}"
echo "  • Ver logs:     ${GREEN}cd $INSTALL_DIR/infrastructure/mi-proyecto && docker compose logs -f${NC}"
echo "  • Reiniciar:    ${GREEN}docker compose restart${NC}"
echo "  • Detener:      ${GREEN}docker compose down${NC}"
echo "  • Ver estado:   ${GREEN}docker compose ps${NC}"
echo "  • Desinstalar:  ${GREEN}sudo $INSTALL_DIR/uninstall.sh${NC}"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $FAILED servicio(s) no respondieron${NC}"
    echo "   Verifica: cd $INSTALL_DIR/infrastructure/mi-proyecto && docker compose logs"
    echo ""
fi

log "✅ Instalación completada. Log guardado en: $LOG_FILE"
log "¡Disfruta Rhinometric! 🦏"

exit 0
