#!/usr/bin/env bash

# ═══════════════════════════════════════════════════════════════════════════
#  RHINOMETRIC v2.1.0 ENTERPRISE - UNIVERSAL INSTALLER
# ═══════════════════════════════════════════════════════════════════════════
#
#  One-command installation for macOS, Linux, and Windows (WSL2)
#
#  Usage:
#    ./install-v2.1.sh
#
#  Features:
#  ✓ Automatic OS detection
#  ✓ Dependency verification
#  ✓ Data directory setup
#  ✓ Environment configuration
#  ✓ Service deployment
#  ✓ Health validation
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

# ═══════════════════════════════════════════════════════════════════════════
#  COLORS & FORMATTING
# ═══════════════════════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${CYAN}"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# ═══════════════════════════════════════════════════════════════════════════
#  ENVIRONMENT DETECTION
# ═══════════════════════════════════════════════════════════════════════════

detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        print_info "Detected: macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if grep -qi microsoft /proc/version 2>/dev/null; then
            OS="wsl2"
            print_info "Detected: Windows WSL2 (Ubuntu)"
        else
            OS="linux"
            print_info "Detected: Linux"
        fi
    else
        OS="unknown"
        print_error "Unsupported OS: $OSTYPE"
        exit 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
#  DEPENDENCY CHECKS
# ═══════════════════════════════════════════════════════════════════════════

check_dependencies() {
    print_header "Checking Dependencies"
    
    local missing=0
    
    # Check Docker
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
        print_success "Docker found: $DOCKER_VERSION"
    else
        print_error "Docker not found"
        missing=$((missing + 1))
    fi
    
    # Check Docker Compose
    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version --short)
        print_success "Docker Compose found: $COMPOSE_VERSION"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | sed 's/,//')
        print_success "Docker Compose found: $COMPOSE_VERSION"
    else
        print_error "Docker Compose not found"
        missing=$((missing + 1))
    fi
    
    # Check Docker daemon
    if docker info &> /dev/null; then
        print_success "Docker daemon is running"
    else
        print_error "Docker daemon is not running"
        print_info "Please start Docker and try again"
        exit 1
    fi
    
    if [ $missing -gt 0 ]; then
        print_error "Missing $missing required dependencies"
        print_info "Please install missing dependencies and try again"
        exit 1
    fi
    
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
#  DATA DIRECTORY SETUP
# ═══════════════════════════════════════════════════════════════════════════

setup_data_directory() {
    print_header "Setting Up Data Directory"
    
    # Determine data directory based on OS
    case $OS in
        macos)
            DATA_DIR="$HOME/Library/Application Support/Rhinometric/v2.1"
            ;;
        wsl2|linux)
            DATA_DIR="$HOME/rhinometric_data_v2.1"
            ;;
    esac
    
    print_info "Data directory: $DATA_DIR"
    
    # Create directories
    mkdir -p "$DATA_DIR"/{prometheus,grafana,loki,tempo,postgres,redis,alertmanager}
    mkdir -p "$DATA_DIR"/{license-server/logs,api-proxy/{cache,config},nginx/logs}
    
    # Set permissions
    chmod -R 755 "$DATA_DIR"
    
    print_success "Data directory created"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
#  ENVIRONMENT CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

setup_environment() {
    print_header "Configuring Environment"
    
    if [ ! -f .env ]; then
        print_info "Creating .env file"
        cat > .env <<EOF
# Rhinometric v2.1.0 Enterprise Configuration
POSTGRES_PASSWORD=rhinometric
REDIS_PASSWORD=rhinometric
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
HOME=$HOME
EOF
        print_success ".env file created"
    else
        print_warning ".env file already exists, skipping"
    fi
    
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
#  DOCKER COMPOSE DEPLOYMENT
# ═══════════════════════════════════════════════════════════════════════════

deploy_services() {
    print_header "Deploying Rhinometric v2.1.0"
    
    print_info "Pulling Docker images..."
    docker compose -f docker-compose-v2.1.0.yml pull
    
    print_info "Starting services..."
    docker compose -f docker-compose-v2.1.0.yml up -d
    
    print_success "Services started"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
#  HEALTH VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

wait_for_health() {
    print_header "Waiting for Services"
    
    local services=(
        "rhinometric-postgres:5432"
        "rhinometric-redis:6379"
        "rhinometric-license-server-v2:5000"
        "rhinometric-api-proxy:8090"
        "rhinometric-prometheus:9090"
        "rhinometric-loki:3100"
        "rhinometric-tempo:3200"
        "rhinometric-grafana:3000"
    )
    
    local max_wait=300
    local elapsed=0
    
    print_info "Waiting up to 5 minutes for all services to be healthy..."
    
    while [ $elapsed -lt $max_wait ]; do
        local healthy=0
        
        for service in "${services[@]}"; do
            local container=$(echo $service | cut -d: -f1)
            if docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null | grep -q healthy; then
                healthy=$((healthy + 1))
            fi
        done
        
        if [ $healthy -eq ${#services[@]} ]; then
            print_success "All services are healthy!"
            return 0
        fi
        
        echo -ne "\r${BLUE}ℹ${NC} Services healthy: $healthy/${#services[@]} (${elapsed}s elapsed)"
        sleep 5
        elapsed=$((elapsed + 5))
    done
    
    echo ""
    print_warning "Timeout waiting for all services (5 minutes)"
    print_info "Some services may still be starting. Check with: docker compose -f docker-compose-v2.1.0.yml ps"
}

# ═══════════════════════════════════════════════════════════════════════════
#  VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

validate_installation() {
    print_header "Validating Installation"
    
    local failed=0
    
    # Check Grafana
    if curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
        print_success "Grafana is accessible"
    else
        print_error "Grafana is not accessible"
        failed=$((failed + 1))
    fi
    
    # Check Prometheus
    if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
        print_success "Prometheus is accessible"
    else
        print_error "Prometheus is not accessible"
        failed=$((failed + 1))
    fi
    
    # Check License Server
    if curl -sf http://localhost:5000/api/health > /dev/null 2>&1; then
        print_success "License Server is accessible"
    else
        print_error "License Server is not accessible"
        failed=$((failed + 1))
    fi
    
    # Check API Proxy
    if curl -sf http://localhost:8090/health > /dev/null 2>&1; then
        print_success "API Proxy is accessible"
    else
        print_error "API Proxy is not accessible"
        failed=$((failed + 1))
    fi
    
    echo ""
    
    if [ $failed -eq 0 ]; then
        print_success "All validation checks passed!"
        return 0
    else
        print_warning "$failed validation checks failed"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
#  FINAL REPORT
# ═══════════════════════════════════════════════════════════════════════════

print_final_report() {
    print_header "Installation Complete!"
    
    echo -e "${GREEN}Rhinometric v2.1.0 Enterprise is now running!${NC}"
    echo ""
    echo "Access URLs:"
    echo -e "  ${CYAN}Grafana:${NC}         http://localhost:3000 (admin/admin)"
    echo -e "  ${CYAN}Prometheus:${NC}      http://localhost:9090"
    echo -e "  ${CYAN}License Server:${NC}  http://localhost:5000/api/docs"
    echo -e "  ${CYAN}API Proxy:${NC}       http://localhost:8090/health"
    echo -e "  ${CYAN}Loki:${NC}            http://localhost:3100"
    echo -e "  ${CYAN}Tempo:${NC}           http://localhost:3200"
    echo ""
    echo "Commands:"
    echo -e "  ${CYAN}Status:${NC}          docker compose -f docker-compose-v2.1.0.yml ps"
    echo -e "  ${CYAN}Logs:${NC}            docker compose -f docker-compose-v2.1.0.yml logs -f"
    echo -e "  ${CYAN}Stop:${NC}            docker compose -f docker-compose-v2.1.0.yml down"
    echo -e "  ${CYAN}Restart:${NC}         docker compose -f docker-compose-v2.1.0.yml restart"
    echo ""
    echo "Data directory: $DATA_DIR"
    echo ""
    print_info "For troubleshooting, check logs with: docker compose -f docker-compose-v2.1.0.yml logs -f [service-name]"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

main() {
    clear
    
    print_header "RHINOMETRIC v2.1.0 ENTERPRISE - UNIVERSAL INSTALLER"
    
    echo -e "${CYAN}This installer will:${NC}"
    echo "  1. Detect your operating system"
    echo "  2. Verify dependencies (Docker, Docker Compose)"
    echo "  3. Create data directories"
    echo "  4. Configure environment"
    echo "  5. Deploy all services"
    echo "  6. Validate installation"
    echo ""
    
    read -p "Press ENTER to continue or Ctrl+C to cancel..."
    echo ""
    
    detect_os
    check_dependencies
    setup_data_directory
    setup_environment
    deploy_services
    wait_for_health
    validate_installation
    print_final_report
}

main "$@"
