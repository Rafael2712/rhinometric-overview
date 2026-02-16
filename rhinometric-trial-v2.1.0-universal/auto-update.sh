#!/usr/bin/env bash

# ═══════════════════════════════════════════════════════════════════════════
#  RHINOMETRIC AUTO-UPDATE SYSTEM v2.1.0
# ═══════════════════════════════════════════════════════════════════════════
#
#  Automatic update system with:
#  - Version detection
#  - Automatic backup
#  - Zero-downtime updates (when possible)
#  - Automatic rollback on failure
#  - Health validation
#
#  Usage:
#    ./auto-update.sh [--check-only] [--force] [--version=X.Y.Z]
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

# ═══════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

CURRENT_VERSION="2.1.0"
UPDATE_CHECK_URL="${UPDATE_CHECK_URL:-https://updates.rhinometric.com/latest}"
BACKUP_DIR="${HOME}/rhinometric_backups"
DATA_DIR="${HOME}/rhinometric_data_v2.1"
COMPOSE_FILE="docker-compose-v2.1.0.yml"

CHECK_ONLY=false
FORCE_UPDATE=false
TARGET_VERSION=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ═══════════════════════════════════════════════════════════════════════════
#  FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

print_header() {
    echo -e "${CYAN}"
    echo "═══════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════════════════"
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
#  VERSION CHECKING
# ═══════════════════════════════════════════════════════════════════════════

check_for_updates() {
    print_info "Checking for updates..."
    
    # Try to fetch latest version from update server
    if command -v curl &> /dev/null; then
        LATEST_VERSION=$(curl -s -f "$UPDATE_CHECK_URL" 2>/dev/null || echo "")
    elif command -v wget &> /dev/null; then
        LATEST_VERSION=$(wget -q -O- "$UPDATE_CHECK_URL" 2>/dev/null || echo "")
    else
        print_warning "No curl or wget available, skipping online check"
        LATEST_VERSION=""
    fi
    
    # Fallback: check local VERSION file or git tags
    if [ -z "$LATEST_VERSION" ]; then
        if [ -f "VERSION" ]; then
            LATEST_VERSION=$(cat VERSION)
        else
            LATEST_VERSION="$CURRENT_VERSION"
        fi
    fi
    
    echo "Current version: $CURRENT_VERSION"
    echo "Latest version:  $LATEST_VERSION"
    
    if [ "$LATEST_VERSION" == "$CURRENT_VERSION" ]; then
        print_success "You are running the latest version!"
        return 1
    elif version_gt "$LATEST_VERSION" "$CURRENT_VERSION"; then
        print_info "Update available: $CURRENT_VERSION → $LATEST_VERSION"
        return 0
    else
        print_info "Running development version ($CURRENT_VERSION)"
        return 1
    fi
}

version_gt() {
    # Compare versions (simple semantic versioning)
    test "$(printf '%s\n' "$@" | sort -V | head -n 1)" != "$1"
}

# ═══════════════════════════════════════════════════════════════════════════
#  BACKUP SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

create_backup() {
    print_header "CREATING BACKUP"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_NAME="rhinometric_v${CURRENT_VERSION}_${TIMESTAMP}"
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
    
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$BACKUP_PATH"
    
    # Backup configuration files
    print_info "Backing up configuration..."
    if [ -d "config" ]; then
        cp -r config "${BACKUP_PATH}/"
        print_success "Configuration backed up"
    fi
    
    # Backup data directories
    print_info "Backing up data..."
    if [ -d "$DATA_DIR" ]; then
        # Only backup critical data (not logs/temp files)
        for service in grafana prometheus postgres redis; do
            if [ -d "${DATA_DIR}/${service}" ]; then
                print_info "  Backing up $service data..."
                rsync -a --exclude='*.log' --exclude='tmp' \
                    "${DATA_DIR}/${service}/" "${BACKUP_PATH}/data/${service}/" 2>/dev/null || \
                cp -r "${DATA_DIR}/${service}" "${BACKUP_PATH}/data/" 2>/dev/null || true
            fi
        done
        print_success "Data backed up"
    fi
    
    # Backup docker-compose file
    if [ -f "$COMPOSE_FILE" ]; then
        cp "$COMPOSE_FILE" "${BACKUP_PATH}/"
        print_success "Docker Compose file backed up"
    fi
    
    # Backup .env file
    if [ -f ".env" ]; then
        cp ".env" "${BACKUP_PATH}/"
        print_success "Environment file backed up"
    fi
    
    # Create backup metadata
    cat > "${BACKUP_PATH}/backup_info.txt" << EOF
Backup Information
==================
Date: $(date)
Version: $CURRENT_VERSION
Host: $(hostname)
User: $(whoami)
Path: $(pwd)
EOF
    
    print_success "Backup created: $BACKUP_PATH"
    echo "$BACKUP_PATH" > /tmp/rhinometric_last_backup
}

restore_backup() {
    BACKUP_PATH=$1
    
    print_header "RESTORING BACKUP"
    print_warning "Restoring from: $BACKUP_PATH"
    
    if [ ! -d "$BACKUP_PATH" ]; then
        print_error "Backup not found: $BACKUP_PATH"
        exit 1
    fi
    
    # Stop services
    print_info "Stopping services..."
    docker compose -f "$COMPOSE_FILE" down || true
    
    # Restore configuration
    if [ -d "${BACKUP_PATH}/config" ]; then
        print_info "Restoring configuration..."
        cp -r "${BACKUP_PATH}/config/"* config/ 2>/dev/null || true
        print_success "Configuration restored"
    fi
    
    # Restore data
    if [ -d "${BACKUP_PATH}/data" ]; then
        print_info "Restoring data..."
        for service in grafana prometheus postgres redis; do
            if [ -d "${BACKUP_PATH}/data/${service}" ]; then
                print_info "  Restoring $service data..."
                rsync -a "${BACKUP_PATH}/data/${service}/" "${DATA_DIR}/${service}/" 2>/dev/null || \
                cp -r "${BACKUP_PATH}/data/${service}"/* "${DATA_DIR}/${service}/" 2>/dev/null || true
            fi
        done
        print_success "Data restored"
    fi
    
    # Restore docker-compose
    if [ -f "${BACKUP_PATH}/$COMPOSE_FILE" ]; then
        cp "${BACKUP_PATH}/$COMPOSE_FILE" "$COMPOSE_FILE"
        print_success "Docker Compose file restored"
    fi
    
    # Restore .env
    if [ -f "${BACKUP_PATH}/.env" ]; then
        cp "${BACKUP_PATH}/.env" ".env"
        print_success "Environment file restored"
    fi
    
    print_success "Backup restored successfully"
}

# ═══════════════════════════════════════════════════════════════════════════
#  UPDATE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

perform_update() {
    TARGET=$1
    
    print_header "PERFORMING UPDATE: $CURRENT_VERSION → $TARGET"
    
    # Create backup before update
    create_backup
    BACKUP_PATH=$(cat /tmp/rhinometric_last_backup)
    
    # Pull new images
    print_info "Pulling new Docker images..."
    if docker compose -f "$COMPOSE_FILE" pull; then
        print_success "Images pulled successfully"
    else
        print_error "Failed to pull images"
        print_warning "Rolling back..."
        restore_backup "$BACKUP_PATH"
        exit 1
    fi
    
    # Restart services
    print_info "Restarting services..."
    if docker compose -f "$COMPOSE_FILE" up -d; then
        print_success "Services restarted"
    else
        print_error "Failed to restart services"
        print_warning "Rolling back..."
        restore_backup "$BACKUP_PATH"
        docker compose -f "$COMPOSE_FILE" up -d
        exit 1
    fi
    
    # Wait for services to be ready
    print_info "Waiting for services to be ready..."
    sleep 30
    
    # Validate health
    print_info "Validating service health..."
    HEALTHY_COUNT=0
    TOTAL_COUNT=0
    
    while IFS= read -r line; do
        TOTAL_COUNT=$((TOTAL_COUNT + 1))
        if echo "$line" | grep -q "healthy"; then
            HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
        fi
    done < <(docker ps --filter "name=rhinometric-" --format "{{.Status}}")
    
    if [ $HEALTHY_COUNT -eq $TOTAL_COUNT ] && [ $TOTAL_COUNT -gt 0 ]; then
        print_success "All services healthy ($HEALTHY_COUNT/$TOTAL_COUNT)"
        print_success "Update completed successfully!"
        
        # Update version file
        echo "$TARGET" > VERSION
        
        # Keep backup but mark as successful
        echo "SUCCESS" > "${BACKUP_PATH}/update_result.txt"
        
        return 0
    else
        print_error "Some services are unhealthy ($HEALTHY_COUNT/$TOTAL_COUNT)"
        print_warning "Rolling back..."
        restore_backup "$BACKUP_PATH"
        docker compose -f "$COMPOSE_FILE" up -d
        
        echo "FAILED" > "${BACKUP_PATH}/update_result.txt"
        exit 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

main() {
    print_header "RHINOMETRIC AUTO-UPDATE SYSTEM"
    
    # Parse arguments
    for arg in "$@"; do
        case $arg in
            --check-only)
                CHECK_ONLY=true
                ;;
            --force)
                FORCE_UPDATE=true
                ;;
            --version=*)
                TARGET_VERSION="${arg#*=}"
                ;;
        esac
    done
    
    # Check for updates
    if check_for_updates || [ "$FORCE_UPDATE" = true ]; then
        if [ "$CHECK_ONLY" = true ]; then
            print_info "Update available but check-only mode enabled"
            exit 0
        fi
        
        # Determine target version
        if [ -z "$TARGET_VERSION" ]; then
            TARGET_VERSION="$LATEST_VERSION"
        fi
        
        # Ask for confirmation unless forced
        if [ "$FORCE_UPDATE" = false ]; then
            echo ""
            read -p "Do you want to update to version $TARGET_VERSION? (y/N) " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_info "Update cancelled"
                exit 0
            fi
        fi
        
        # Perform update
        perform_update "$TARGET_VERSION"
    else
        if [ "$CHECK_ONLY" = false ]; then
            print_info "No updates needed"
        fi
        exit 0
    fi
}

main "$@"
