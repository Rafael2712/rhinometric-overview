#!/bin/bash
# ============================================================================
# Rhinometric v2.1.0 - Quick Start Installer
# ============================================================================
# Description: One-command installer for Linux/macOS
# Checks prerequisites, creates .env, deploys full observability stack
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
RHINOMETRIC_VERSION="2.1.0"
COMPOSE_FILE="docker-compose-v2.1.0.yml"
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"
MIN_DOCKER_VERSION="20.10.0"
MIN_DOCKER_COMPOSE_VERSION="2.0.0"

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ${BOLD}Rhinometric v${RHINOMETRIC_VERSION} - Observability Platform${NC}           ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${BOLD}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_error() {
    echo -e "${RED}❌ ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARNING:${NC} $1"
}

version_gt() {
    test "$(printf '%s\n' "$@" | sort -V | head -n 1)" != "$1"
}

# ============================================================================
# Prerequisite Checks
# ============================================================================

check_docker() {
    print_step "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    
    DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -n 1)
    print_success "Docker ${DOCKER_VERSION} found"
    
    if version_gt "$MIN_DOCKER_VERSION" "$DOCKER_VERSION"; then
        print_warning "Docker version ${DOCKER_VERSION} is below recommended ${MIN_DOCKER_VERSION}"
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        echo "Please start Docker Desktop and try again"
        exit 1
    fi
    
    print_success "Docker daemon is running"
}

check_docker_compose() {
    print_step "Checking Docker Compose..."
    
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose v2 is not available"
        echo "Please update Docker Desktop to get Compose v2"
        exit 1
    fi
    
    COMPOSE_VERSION=$(docker compose version --short)
    print_success "Docker Compose ${COMPOSE_VERSION} found"
}

check_ports() {
    print_step "Checking port availability..."
    
    REQUIRED_PORTS=(3000 5000 5432 6379 8090 8091 8092 9090 9093)
    PORTS_IN_USE=()
    
    for PORT in "${REQUIRED_PORTS[@]}"; do
        if lsof -Pi :$PORT -sTCP:LISTEN -t &> /dev/null || netstat -an | grep -q ":$PORT.*LISTEN" 2>/dev/null; then
            PORTS_IN_USE+=($PORT)
        fi
    done
    
    if [ ${#PORTS_IN_USE[@]} -gt 0 ]; then
        print_warning "The following ports are already in use: ${PORTS_IN_USE[*]}"
        echo "These services may fail to start. Continue anyway? (y/N)"
        read -r CONTINUE
        if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "All required ports are available"
    fi
}

check_disk_space() {
    print_step "Checking disk space..."
    
    AVAILABLE_GB=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    
    if [ "$AVAILABLE_GB" -lt 5 ]; then
        print_warning "Less than 5GB available. Rhinometric requires ~3-5GB for images."
        echo "Continue anyway? (y/N)"
        read -r CONTINUE
        if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "${AVAILABLE_GB}GB available"
    fi
}

# ============================================================================
# Environment Configuration
# ============================================================================

setup_environment() {
    print_step "Setting up environment configuration..."
    
    if [ -f "$ENV_FILE" ]; then
        print_warning ".env file already exists"
        echo "Overwrite with new configuration? (y/N)"
        read -r OVERWRITE
        if [[ ! $OVERWRITE =~ ^[Yy]$ ]]; then
            print_success "Using existing .env file"
            return
        fi
        cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        print_success "Backed up existing .env file"
    fi
    
    if [ ! -f "$ENV_EXAMPLE" ]; then
        print_error ".env.example not found"
        exit 1
    fi
    
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    
    # Generate secure passwords
    POSTGRES_PASS=$(openssl rand -base64 16 | tr -d '/+=' | head -c 20)
    REDIS_PASS=$(openssl rand -base64 16 | tr -d '/+=' | head -c 20)
    GRAFANA_PASS=$(openssl rand -base64 16 | tr -d '/+=' | head -c 20)
    
    # Update .env with generated passwords
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${POSTGRES_PASS}/" "$ENV_FILE"
        sed -i '' "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=${REDIS_PASS}/" "$ENV_FILE"
        sed -i '' "s/GRAFANA_PASSWORD=.*/GRAFANA_PASSWORD=${GRAFANA_PASS}/" "$ENV_FILE"
    else
        # Linux
        sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${POSTGRES_PASS}/" "$ENV_FILE"
        sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=${REDIS_PASS}/" "$ENV_FILE"
        sed -i "s/GRAFANA_PASSWORD=.*/GRAFANA_PASSWORD=${GRAFANA_PASS}/" "$ENV_FILE"
    fi
    
    print_success "Environment configured with secure passwords"
    
    # Save credentials to file
    CREDS_FILE="credentials.txt"
    cat > "$CREDS_FILE" << EOF
# ============================================================================
# Rhinometric v${RHINOMETRIC_VERSION} - Generated Credentials
# ============================================================================
# IMPORTANT: Store this file securely and delete after saving elsewhere
# Generated: $(date)
# ============================================================================

GRAFANA (http://localhost:3000):
  Username: admin
  Password: ${GRAFANA_PASS}

POSTGRES (localhost:5432):
  Database: rhinometric_trial
  Username: rhinometric
  Password: ${POSTGRES_PASS}

REDIS (localhost:6379):
  Password: ${REDIS_PASS}

# ============================================================================
# Other Services (no authentication required):
# ============================================================================
# Prometheus: http://localhost:9090
# License Server API: http://localhost:5000/api/docs
# API Connector UI: http://localhost:8091
# License Management UI: http://localhost:8092
# Alertmanager: http://localhost:9093
# ============================================================================
EOF

    chmod 600 "$CREDS_FILE"
    print_success "Credentials saved to ${CREDS_FILE} (permissions: 600)"
}

# ============================================================================
# Deployment
# ============================================================================

deploy_stack() {
    print_step "Deploying Rhinometric stack..."
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "docker-compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    echo "Pulling Docker images (this may take 5-10 minutes on first run)..."
    docker compose -f "$COMPOSE_FILE" pull
    
    echo "Starting services..."
    docker compose -f "$COMPOSE_FILE" up -d
    
    print_success "All services started"
}

wait_for_services() {
    print_step "Waiting for services to become healthy..."
    
    echo "This may take 30-60 seconds..."
    sleep 15
    
    MAX_ATTEMPTS=30
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        HEALTHY_COUNT=$(docker compose -f "$COMPOSE_FILE" ps --format json 2>/dev/null | jq -r '.[] | select(.Health == "healthy") | .Name' 2>/dev/null | wc -l || echo "0")
        TOTAL_COUNT=$(docker compose -f "$COMPOSE_FILE" ps --format json 2>/dev/null | jq -r '.[].Name' 2>/dev/null | wc -l || echo "0")
        
        if [ "$TOTAL_COUNT" -eq 0 ]; then
            # Fallback if jq not available
            HEALTHY_COUNT=$(docker compose -f "$COMPOSE_FILE" ps | grep -c "healthy" || echo "0")
            TOTAL_COUNT=$(docker compose -f "$COMPOSE_FILE" ps | grep -c "Up" || echo "0")
        fi
        
        echo -ne "\rHealthy containers: ${HEALTHY_COUNT}/${TOTAL_COUNT}  "
        
        if [ "$HEALTHY_COUNT" -ge 10 ]; then
            echo ""
            print_success "Core services are healthy"
            return
        fi
        
        sleep 2
        ATTEMPT=$((ATTEMPT + 1))
    done
    
    echo ""
    print_warning "Some services may still be starting. Check with: docker compose -f $COMPOSE_FILE ps"
}

# ============================================================================
# Post-Install
# ============================================================================

print_access_info() {
    print_header
    
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}  ${BOLD}Installation Complete!${NC}                                      ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BOLD}🌐 Access URLs:${NC}"
    echo ""
    echo -e "  ${BLUE}Grafana:${NC}              http://localhost:3000"
    echo -e "  ${BLUE}Prometheus:${NC}           http://localhost:9090"
    echo -e "  ${BLUE}License Server:${NC}       http://localhost:5000/api/docs"
    echo -e "  ${BLUE}API Connector UI:${NC}     http://localhost:8091"
    echo -e "  ${BLUE}License Management:${NC}   http://localhost:8092"
    echo ""
    echo -e "${BOLD}🔐 Credentials:${NC}"
    echo ""
    echo -e "  Saved in: ${YELLOW}credentials.txt${NC}"
    echo -e "  Grafana username: ${YELLOW}admin${NC}"
    echo ""
    echo -e "${BOLD}📋 Quick Commands:${NC}"
    echo ""
    echo -e "  View logs:        ${YELLOW}docker compose -f $COMPOSE_FILE logs -f${NC}"
    echo -e "  Check status:     ${YELLOW}docker compose -f $COMPOSE_FILE ps${NC}"
    echo -e "  Stop services:    ${YELLOW}docker compose -f $COMPOSE_FILE down${NC}"
    echo -e "  Restart:          ${YELLOW}docker compose -f $COMPOSE_FILE restart${NC}"
    echo ""
    echo -e "${BOLD}📚 Documentation:${NC}"
    echo ""
    echo -e "  README.md - Full documentation"
    echo -e "  CONFIGURAR_EMAIL_ZOHO.md - Email configuration guide"
    echo ""
    echo -e "${YELLOW}⚠️  Remember to:${NC}"
    echo -e "  1. Store credentials.txt securely"
    echo -e "  2. Change Grafana password on first login"
    echo -e "  3. Configure SMTP in .env for email functionality"
    echo ""
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    print_header
    
    # Prerequisites
    check_docker
    check_docker_compose
    check_ports
    check_disk_space
    
    echo ""
    
    # Configuration
    setup_environment
    
    echo ""
    
    # Deployment
    deploy_stack
    wait_for_services
    
    echo ""
    
    # Success
    print_access_info
}

# Run main function
main
