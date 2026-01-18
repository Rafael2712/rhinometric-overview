#!/bin/bash
# ============================================================================
# RHINOMETRIC v2.5.0 CORE - ON-PREMISE INSTALLER
# ============================================================================
# Automated installation script for customer on-premise deployment
# Verifies requirements, creates directories, generates configs, and deploys
# ============================================================================

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REQUIRED_DOCKER_VERSION="20.10"
REQUIRED_COMPOSE_VERSION="2.0"
MIN_CPU_CORES=8
MIN_RAM_GB=16
MIN_DISK_GB=150
DATA_BASE_PATH="${HOME}/rhinometric_data_v2.2"
BACKUP_PATH="${HOME}/rhinometric_backups"
COMPOSE_FILE="docker-compose-v2.5.0-core.yml"
ENV_FILE=".env"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

print_header() {
    echo -e "${BLUE}"
    echo "============================================================================"
    echo "$1"
    echo "============================================================================"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

check_root() {
    if [ "$EUID" -eq 0 ]; then 
        print_error "Do not run this script as root or with sudo"
        print_info "Run as regular user with Docker permissions: ./install-core.sh"
        exit 1
    fi
}

check_docker() {
    print_info "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        print_info "Install Docker: https://docs.docker.com/engine/install/"
        exit 1
    fi
    
    DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "0.0.0")
    print_success "Docker version: $DOCKER_VERSION"
    
    # Check if user can run Docker without sudo
    if ! docker ps &> /dev/null; then
        print_error "Cannot run Docker commands (permission denied)"
        print_info "Add user to docker group: sudo usermod -aG docker $USER"
        print_info "Then logout and login again"
        exit 1
    fi
    
    print_success "Docker is accessible"
}

check_docker_compose() {
    print_info "Checking Docker Compose installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Try docker compose (plugin) first
    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version --short)
        COMPOSE_CMD="docker compose"
        print_success "Docker Compose (plugin) version: $COMPOSE_VERSION"
    # Fallback to docker-compose (standalone)
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose version --short)
        COMPOSE_CMD="docker-compose"
        print_success "Docker Compose (standalone) version: $COMPOSE_VERSION"
    else
        print_error "Docker Compose is not available"
        print_info "Install: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

check_system_resources() {
    print_info "Checking system resources..."
    
    # CPU cores
    CPU_CORES=$(nproc)
    if [ "$CPU_CORES" -lt "$MIN_CPU_CORES" ]; then
        print_warning "CPU cores: $CPU_CORES (minimum recommended: $MIN_CPU_CORES)"
        print_info "Stack may run slowly on this hardware"
    else
        print_success "CPU cores: $CPU_CORES (✓ meets minimum)"
    fi
    
    # RAM (in GB)
    TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
    if [ "$TOTAL_RAM_GB" -lt "$MIN_RAM_GB" ]; then
        print_error "RAM: ${TOTAL_RAM_GB}GB (minimum required: ${MIN_RAM_GB}GB)"
        print_info "Rhinometric v2.5.0 Core requires at least ${MIN_RAM_GB}GB RAM"
        exit 1
    else
        print_success "RAM: ${TOTAL_RAM_GB}GB (✓ meets minimum)"
    fi
    
    # Disk space (in GB)
    AVAILABLE_DISK_GB=$(df -BG "$HOME" | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$AVAILABLE_DISK_GB" -lt "$MIN_DISK_GB" ]; then
        print_error "Disk space: ${AVAILABLE_DISK_GB}GB available (minimum required: ${MIN_DISK_GB}GB)"
        exit 1
    else
        print_success "Disk space: ${AVAILABLE_DISK_GB}GB available (✓ meets minimum)"
    fi
}

check_required_files() {
    print_info "Checking required files..."
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Compose file not found: $COMPOSE_FILE"
        print_info "Ensure you're running this script from the Rhinometric installation directory"
        exit 1
    fi
    print_success "Compose file found: $COMPOSE_FILE"
}

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

generate_random_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

generate_secret_key() {
    openssl rand -base64 48 | tr -d "=+/" | cut -c1-48
}

create_env_file() {
    print_info "Creating environment file..."
    
    if [ -f "$ENV_FILE" ]; then
        print_warning "Environment file already exists: $ENV_FILE"
        read -p "Overwrite? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Keeping existing $ENV_FILE"
            return
        fi
        mv "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        print_info "Backed up existing $ENV_FILE"
    fi
    
    # Generate secure random passwords
    POSTGRES_PASS=$(generate_random_password)
    REDIS_PASS=$(generate_random_password)
    GRAFANA_PASS=$(generate_random_password)
    ADMIN_PASS=$(generate_random_password)
    SECRET_KEY=$(generate_secret_key)
    
    cat > "$ENV_FILE" << EOF
# ============================================================================
# RHINOMETRIC v2.5.0 CORE - ENVIRONMENT CONFIGURATION
# ============================================================================
# Generated: $(date)
# IMPORTANT: Keep this file secure - contains sensitive credentials
# ============================================================================

# PostgreSQL
POSTGRES_PASSWORD=${POSTGRES_PASS}

# Redis
REDIS_PASSWORD=${REDIS_PASS}

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=${GRAFANA_PASS}

# Console Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=${ADMIN_PASS}

# Backend Security
SECRET_KEY=${SECRET_KEY}

# SMTP Configuration (update with your SMTP server)
SMTP_HOST=smtp.zoho.eu
SMTP_PORT=587
SMTP_USER=rafael.canelon@rhinometric.com
SMTP_PASSWORD=CHANGEME
SMTP_FROM=rafael.canelon@rhinometric.com

# Alertmanager
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SMTP_PASS=\${SMTP_PASSWORD}

# Timezone
TZ=Europe/Madrid
EOF

    chmod 600 "$ENV_FILE"
    print_success "Environment file created: $ENV_FILE"
    
    # Display credentials
    echo ""
    print_header "GENERATED CREDENTIALS (save these securely)"
    echo -e "${YELLOW}Grafana:${NC}"
    echo "  URL: http://localhost:3000"
    echo "  User: admin"
    echo "  Password: ${GRAFANA_PASS}"
    echo ""
    echo -e "${YELLOW}Rhinometric Console (UI Principal):${NC}"
    echo "  URL: http://localhost:3002"
    echo "  User: admin"
    echo "  Password: ${ADMIN_PASS}"
    echo ""
    echo -e "${YELLOW}PostgreSQL:${NC}"
    echo "  User: rhinometric"
    echo "  Password: ${POSTGRES_PASS}"
    echo ""
    echo -e "${YELLOW}Redis:${NC}"
    echo "  Password: ${REDIS_PASS}"
    echo ""
    print_warning "Credentials saved to: $ENV_FILE (chmod 600)"
    echo ""
}

# ============================================================================
# DIRECTORY STRUCTURE
# ============================================================================

create_data_directories() {
    print_info "Creating data directories..."
    
    # Main data directories
    mkdir -p "${DATA_BASE_PATH}"/{postgres,redis,loki,jaeger,prometheus,grafana,ai-anomaly/{models,data},reports,temp,alertmanager,nginx/logs,license-server/logs,console-backend/logs}
    
    # Backup directory
    mkdir -p "${BACKUP_PATH}"
    
    # Set permissions
    chmod -R 755 "${DATA_BASE_PATH}"
    chmod -R 755 "${BACKUP_PATH}"
    
    # Grafana needs specific permissions
    if [ -d "${DATA_BASE_PATH}/grafana" ]; then
        chmod 777 "${DATA_BASE_PATH}/grafana"
    fi
    
    # Loki needs write access
    if [ -d "${DATA_BASE_PATH}/loki" ]; then
        chmod 777 "${DATA_BASE_PATH}/loki"
    fi
    
    print_success "Data directories created at: ${DATA_BASE_PATH}"
    print_success "Backup directory created at: ${BACKUP_PATH}"
}

# ============================================================================
# DOCKER DEPLOYMENT
# ============================================================================

pull_docker_images() {
    print_info "Pulling Docker images (this may take several minutes)..."
    
    if $COMPOSE_CMD -f "$COMPOSE_FILE" pull; then
        print_success "Docker images pulled successfully"
    else
        print_error "Failed to pull Docker images"
        exit 1
    fi
}

start_stack() {
    print_info "Starting Rhinometric stack..."
    
    if $COMPOSE_CMD -f "$COMPOSE_FILE" up -d; then
        print_success "Stack started successfully"
    else
        print_error "Failed to start stack"
        print_info "Check logs: $COMPOSE_CMD -f $COMPOSE_FILE logs"
        exit 1
    fi
}

# ============================================================================
# HEALTH VALIDATION
# ============================================================================

wait_for_services() {
    print_info "Waiting for services to become healthy (this may take 2-3 minutes)..."
    
    local max_wait=300  # 5 minutes
    local elapsed=0
    local check_interval=10
    
    while [ $elapsed -lt $max_wait ]; do
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
        
        # Count healthy services
        local healthy=$($COMPOSE_CMD -f "$COMPOSE_FILE" ps --format json 2>/dev/null | grep -o '"Health":"healthy"' | wc -l)
        
        echo -ne "\rHealthy services: $healthy/17 (${elapsed}s elapsed)   "
        
        # Check if all critical services are up
        if [ "$healthy" -ge 15 ]; then
            echo ""
            print_success "Most services are healthy"
            return 0
        fi
    done
    
    echo ""
    print_warning "Timeout waiting for all services (some may still be starting)"
    return 1
}

validate_endpoints() {
    print_info "Validating service endpoints..."
    
    local failed=0
    
    # Core services validation
    services=(
        "postgres:docker exec rhinometric-postgres pg_isready -U rhinometric"
        "redis:docker exec rhinometric-redis redis-cli --raw incr ping"
        "prometheus:curl -sf http://localhost:9090/-/healthy"
        "grafana:curl -sf http://localhost:3000/api/health"
        "loki:curl -sf http://localhost:3100/ready"
        "jaeger:curl -sf http://localhost:16686"
        "console-frontend:curl -sf http://localhost:3002"
        "console-backend:curl -sf http://localhost:8105/health"
        "nginx:curl -sf http://localhost/health"
    )
    
    for service in "${services[@]}"; do
        name="${service%%:*}"
        cmd="${service#*:}"
        
        if eval "$cmd" &> /dev/null; then
            print_success "$name: healthy"
        else
            print_error "$name: not responding"
            ((failed++))
        fi
    done
    
    return $failed
}

# ============================================================================
# MAIN INSTALLATION FLOW
# ============================================================================

main() {
    clear
    print_header "RHINOMETRIC v2.5.0 CORE - ON-PREMISE INSTALLER"
    
    echo ""
    print_info "This installer will deploy 17 core services:"
    echo "  • Databases: PostgreSQL, Redis"
    echo "  • Observability: Prometheus, Loki, Jaeger, Grafana, Alertmanager"
    echo "  • Console: Backend API + Frontend UI (puerto 3002)"
    echo "  • AI: Anomaly Detection"
    echo "  • Infrastructure: Nginx, Backup, Exporters"
    echo ""
    read -p "Continue with installation? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_info "Installation cancelled"
        exit 0
    fi
    
    # Pre-flight checks
    print_header "STEP 1/7: PRE-FLIGHT CHECKS"
    check_root
    check_docker
    check_docker_compose
    check_system_resources
    check_required_files
    
    # Environment setup
    echo ""
    print_header "STEP 2/7: ENVIRONMENT SETUP"
    create_env_file
    
    # Create directories
    echo ""
    print_header "STEP 3/7: DIRECTORY STRUCTURE"
    create_data_directories
    
    # Pull images
    echo ""
    print_header "STEP 4/7: PULL DOCKER IMAGES"
    pull_docker_images
    
    # Start stack
    echo ""
    print_header "STEP 5/7: START RHINOMETRIC STACK"
    start_stack
    
    # Wait for services
    echo ""
    print_header "STEP 6/7: WAIT FOR SERVICES"
    wait_for_services || true
    
    # Validate
    echo ""
    print_header "STEP 7/7: VALIDATE ENDPOINTS"
    if validate_endpoints; then
        echo ""
        print_header "✓ INSTALLATION COMPLETE"
        print_success "Rhinometric v2.5.0 Core is now running!"
        echo ""
        echo -e "${GREEN}Access the platform:${NC}"
        echo "  🌟 Rhinometric Console (UI Principal): http://localhost:3002"
        echo "  📊 Grafana Dashboards: http://localhost:3000"
        echo "  🔍 Jaeger Tracing: http://localhost:16686"
        echo "  📈 Prometheus Metrics: http://localhost:9090"
        echo ""
        echo -e "${YELLOW}Credentials: see $ENV_FILE${NC}"
        echo ""
    else
        print_warning "Some services need more time to initialize"
        print_info "Check status: $COMPOSE_CMD -f $COMPOSE_FILE ps"
    fi
}

# Run main installation
main "$@"
