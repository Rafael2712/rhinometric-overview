#!/bin/bash
# ============================================
# Rhinometric v2.5.0 - Instalador Oficial macOS
# Soporta: macOS 11 (Big Sur) y superiores
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
INSTALL_DIR="/Applications/Rhinometric"
DATA_DIR="$HOME/Library/Application Support/Rhinometric"
LOG_FILE="$HOME/Library/Logs/rhinometric-install.log"

# Funciones
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
    ║        Observability Platform - macOS Edition            ║
    ║        © 2025 Rhinometric. All rights reserved.          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

# Iniciar log
mkdir -p "$(dirname "$LOG_FILE")"
log "Starting Rhinometric v$VERSION installation on macOS..."

# Verificar macOS version
log "Checking macOS version..."
MACOS_VERSION=$(sw_vers -productVersion)
MACOS_MAJOR=$(echo $MACOS_VERSION | cut -d. -f1)
if [ "$MACOS_MAJOR" -lt 11 ]; then
    error "macOS version not supported: $MACOS_VERSION"
    error "Rhinometric requires macOS 11 (Big Sur) or later"
    exit 1
fi
log "macOS $MACOS_VERSION detected ✓"

# Verificar arquitectura
ARCH=$(uname -m)
log "Architecture: $ARCH"
if [ "$ARCH" != "x86_64" ] && [ "$ARCH" != "arm64" ]; then
    error "Architecture not supported: $ARCH"
    exit 1
fi

# Verificar Homebrew
log "Checking Homebrew..."
if ! command -v brew &> /dev/null; then
    warning "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add to PATH
    if [ "$ARCH" = "arm64" ]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    
    log "Homebrew installed ✓"
else
    BREW_VERSION=$(brew --version | head -1)
    log "Homebrew found: $BREW_VERSION ✓"
fi

# Verificar Docker Desktop
log "Checking Docker Desktop..."
if ! command -v docker &> /dev/null; then
    warning "Docker Desktop not found. Installing..."
    brew install --cask docker
    
    log "Opening Docker Desktop..."
    open -a Docker
    
    log "⏳ Waiting for Docker to start (this may take 30-60 seconds)..."
    for i in {1..60}; do
        if docker info &> /dev/null; then
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""
    
    if ! docker info &> /dev/null; then
        error "Docker failed to start"
        error "Please start Docker Desktop manually and run this script again"
        exit 1
    fi
    
    log "Docker Desktop installed and started ✓"
else
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    log "Docker $DOCKER_VERSION found ✓"
    
    # Verificar si Docker está corriendo
    if ! docker info &> /dev/null; then
        log "Starting Docker Desktop..."
        open -a Docker
        
        log "⏳ Waiting for Docker to start..."
        for i in {1..60}; do
            if docker info &> /dev/null; then
                break
            fi
            echo -n "."
            sleep 1
        done
        echo ""
        
        if ! docker info &> /dev/null; then
            error "Docker failed to start"
            error "Please start Docker Desktop manually and run this script again"
            exit 1
        fi
    fi
fi

# Verificar Docker Compose
log "Checking Docker Compose..."
if ! docker compose version &> /dev/null; then
    error "Docker Compose not found"
    error "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi
COMPOSE_VERSION=$(docker compose version --short)
log "Docker Compose $COMPOSE_VERSION found ✓"

# Verificar Git
log "Checking Git..."
if ! command -v git &> /dev/null; then
    warning "Git not found. Installing..."
    brew install git
    log "Git installed ✓"
fi

# Verificar requisitos del sistema
log "Checking system requirements..."

# RAM: 8GB mínimo
TOTAL_RAM=$(sysctl hw.memsize | awk '{print int($2/1024/1024/1024)}')
if [ "$TOTAL_RAM" -lt 8 ]; then
    error "Insufficient RAM: ${TOTAL_RAM}GB (minimum 8GB required)"
    exit 1
fi
log "RAM: ${TOTAL_RAM}GB ✓"

# Disco: 50GB mínimo
FREE_DISK=$(df -g / | awk 'NR==2 {print $4}')
if [ "$FREE_DISK" -lt 50 ]; then
    error "Insufficient disk space: ${FREE_DISK}GB (minimum 50GB required)"
    exit 1
fi
log "Free disk space: ${FREE_DISK}GB ✓"

# Crear directorios
log "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$DATA_DIR"/{postgres,grafana,prometheus,loki,tempo,licenses,backups}
log "Directories created ✓"

# Descargar configuración
log "Downloading Rhinometric from GitHub..."
cd "$INSTALL_DIR"

if [ -d ".git" ]; then
    log "Existing repository found, updating..."
    git fetch origin main --quiet
    git reset --hard origin/main --quiet
else
    log "Cloning repository..."
    git clone --depth 1 --branch main "$REPO_URL.git" . --quiet 2>&1 | tee -a "$LOG_FILE"
fi

cd infrastructure/mi-proyecto
log "Files downloaded ✓"

# Generar .env con valores seguros
log "Generating secure configuration..."
POSTGRES_PWD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
REDIS_PWD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
JWT_SECRET=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-40)

cat > .env << ENVEOF
# Rhinometric v$VERSION - Generated Configuration
# Generated: $(date)

# SMTP Configuration (COMPLETE AFTER INSTALLATION)
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
log "Configuration generated ✓"
log "⚠️  Passwords saved in: $INSTALL_DIR/infrastructure/mi-proyecto/.env"

# Construir imágenes
log "Building Docker images..."
log "⏳ This may take 5-10 minutes depending on your connection..."
docker compose -f docker-compose.yml -f docker-compose.override.yml build 2>&1 | tee -a "$LOG_FILE" | grep -E "(Building|Successfully|ERROR)" || true

# Iniciar servicios
log "Starting Rhinometric services..."
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d 2>&1 | tee -a "$LOG_FILE"

# Esperar servicios
log "⏳ Waiting for services to be ready (60 seconds)..."
for i in {1..6}; do
    echo -n "."
    sleep 10
done
echo ""

# Verificar servicios
log "Verifying service health..."
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
    
    if nc -z localhost $PORT 2>/dev/null; then
        log "$NAME (port $PORT) ✓"
    else
        warning "$NAME (port $PORT) not responding"
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

echo -e "${YELLOW}WARNING:${NC} This will remove:"
echo "  • All containers"
echo "  • All Docker images"
echo "  • All data in ~/Library/Application Support/Rhinometric"
echo "  • Files in /Applications/Rhinometric"
echo ""
read -p "Continue? Type 'YES': " confirm

if [ "$confirm" != "YES" ]; then
    echo "Cancelled."
    exit 0
fi

echo -e "${GREEN}[1/4]${NC} Stopping services..."
cd "/Applications/Rhinometric/infrastructure/mi-proyecto"
docker compose down -v 2>/dev/null || true

echo -e "${GREEN}[2/4]${NC} Removing images..."
docker images | grep rhinometric | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true

echo -e "${GREEN}[3/4]${NC} Removing data..."
rm -rf "$HOME/Library/Application Support/Rhinometric"

echo -e "${GREEN}[4/4]${NC} Removing installation..."
rm -rf "/Applications/Rhinometric"

echo ""
echo -e "${GREEN}✅ Rhinometric has been completely uninstalled${NC}"
UNINSTALL

chmod +x "$INSTALL_DIR/uninstall.sh"

# Crear alias para fácil acceso
SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "alias rhinometric=" "$SHELL_RC"; then
        echo "" >> "$SHELL_RC"
        echo "# Rhinometric aliases" >> "$SHELL_RC"
        echo "alias rhinometric='cd /Applications/Rhinometric/infrastructure/mi-proyecto && docker compose'" >> "$SHELL_RC"
        log "Added 'rhinometric' alias to $SHELL_RC"
    fi
fi

# Resumen
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}║              ✅ INSTALLATION COMPLETED                     ║${NC}"
else
    echo -e "${YELLOW}║         ⚠️  INSTALLATION WITH WARNINGS ($FAILED services)    ║${NC}"
fi
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

log "Rhinometric v$VERSION installed in: $INSTALL_DIR"
log "Data in: $DATA_DIR"
echo ""
echo -e "${BLUE}📊 ACCESS TO PLATFORM:${NC}"
echo "  • Grafana:          http://localhost:3000"
echo "  • Prometheus:       http://localhost:9090"
echo "  • License Server:   http://localhost:8090"
echo "  • Dashboard Builder: http://localhost:8001"
echo ""
echo -e "${BLUE}🔐 INITIAL CREDENTIALS:${NC}"
echo "  • Username: ${GREEN}admin${NC}"
echo "  • Password: ${GREEN}admin${NC} ${YELLOW}(⚠️  CHANGE ON FIRST LOGIN)${NC}"
echo ""
echo -e "${BLUE}📧 CONFIGURE SMTP (OPTIONAL):${NC}"
echo "  Edit: ${GREEN}$INSTALL_DIR/infrastructure/mi-proyecto/.env${NC}"
echo "  Variables: SMTP_USER, SMTP_PASSWORD"
echo "  Then: ${GREEN}rhinometric restart rhinometric-license-server-v2${NC}"
echo ""
echo -e "${BLUE}📚 NEXT STEPS:${NC}"
echo "  1. Access Grafana in your browser"
echo "  2. Generate a license in License Server"
echo "  3. Read documentation: https://github.com/Rafael2712/mi-proyecto/wiki"
echo ""
echo -e "${BLUE}🛠️  USEFUL COMMANDS:${NC}"
echo "  • View logs:     ${GREEN}rhinometric logs -f${NC}"
echo "  • Restart:       ${GREEN}rhinometric restart${NC}"
echo "  • Stop:          ${GREEN}rhinometric down${NC}"
echo "  • View status:   ${GREEN}rhinometric ps${NC}"
echo "  • Uninstall:     ${GREEN}$INSTALL_DIR/uninstall.sh${NC}"
echo ""
echo "  ${YELLOW}Note:${NC} Restart your terminal to use the 'rhinometric' alias"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $FAILED service(s) did not respond${NC}"
    echo "   Check logs: rhinometric logs"
    echo ""
fi

log "Installation completed. Log saved in: $LOG_FILE"
log "Enjoy Rhinometric! 🦏"

exit 0
