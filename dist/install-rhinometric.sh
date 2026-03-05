#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# RHINOMETRIC v3.0.2 — PRODUCTION INSTALLER
# Integrates Ed25519 license validation via rhino-lic
# Date: 2026-03-04
# Requires: Ubuntu 20.04+, Docker 24.x+, Docker Compose v2
#
# IMPORTANT: This installer NEVER aborts due to license issues.
#            The platform always starts. License status is informational.
#
# EXIT CODES:
#   0 — Installation completed, platform healthy
#   1 — Critical failure (docker compose failed, health check failed, etc.)
#
# v3.0.2 CHANGES:
#   - Auto-create runtime volume directories with correct UID/permissions
#   - Full stack health check (all services, not just console+grafana)
#   - Auto-fix for common issues (permission denied, missing dirs)
#   - Rollback on failure + debug bundle generation
#   - --no-traces flag to skip Jaeger if desired
# ═══════════════════════════════════════════════════════════════════════════════

# ── Do NOT use set -e — we handle every error explicitly ──────────────────────

# ─── Constants ────────────────────────────────────────────────────────────────
readonly VERSION="3.0.2"
readonly INSTALL_DIR="${INSTALL_DIR:-/opt/rhinometric}"
readonly COMPOSE_FILE="docker-compose.yml"
readonly CREDENTIALS_FILE="${INSTALL_DIR}/install-info.txt"
readonly LICENSE_DEST="${INSTALL_DIR}/license.key"
readonly RHINO_LIC_BIN="/usr/local/bin/rhino-lic"
readonly MIN_RAM_GB=8
readonly MIN_CPU_CORES=4
readonly REQUIRED_SPACE_GB=150
readonly HEALTH_URL="http://127.0.0.1:3002"
readonly HEALTH_RETRIES=30
readonly HEALTH_DELAY=10
readonly PULL_RETRIES=3
readonly PULL_DELAY=10
readonly MAX_AUTO_FIX_ATTEMPTS=2

# ─── Colors (disabled when not a terminal) ────────────────────────────────────
if [ -t 1 ]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
    CYAN='\033[0;36m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; CYAN=''; BLUE=''; BOLD=''; NC=''
fi

# ─── State variables ─────────────────────────────────────────────────────────
LICENSE_STATUS="unlicensed"
LICENSE_PLAN=""
LICENSE_HOSTS=""
LICENSE_EXPIRES=""
LICENSE_CUSTOMER=""
MACHINE_FINGERPRINT=""
POSTGRES_PASSWORD=""
REDIS_PASSWORD=""
GRAFANA_PASSWORD=""
ADMIN_PASSWORD=""
INSTALL_WARNINGS=()
SKIP_JAEGER=false
DATA_ROOT=""

# ─── Critical failure tracking ───────────────────────────────────────────────
INSTALL_CRITICAL_FAILURE=false
FAILURE_REASONS=()

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

log_info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; INSTALL_WARNINGS+=("$1"); }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Mark a critical (non-recoverable) failure ────────────────────────────────
fail_critical() {
    INSTALL_CRITICAL_FAILURE=true
    FAILURE_REASONS+=("$1")
    log_error "$1"
}
log_step()  { echo -e "\n${BLUE}${BOLD}═══ $1 ═══${NC}\n"; }

banner() {
    echo -e "${CYAN}"
    cat << 'BANNER'
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ██████╗ ██╗  ██╗██╗███╗   ██╗ ██████╗ ███╗   ███╗             ║
║   ██╔══██╗██║  ██║██║████╗  ██║██╔═══██╗████╗ ████║             ║
║   ██████╔╝███████║██║██╔██╗ ██║██║   ██║██╔████╔██║             ║
║   ██╔══██╗██╔══██║██║██║╚██╗██║██║   ██║██║╚██╔╝██║             ║
║   ██║  ██║██║  ██║██║██║ ╚████║╚██████╔╝██║ ╚═╝ ██║             ║
║   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝             ║
║                                                                  ║
║          Enterprise Observability Platform v3.0.2                ║
║                   Production Installer                           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
BANNER
    echo -e "${NC}"
}

generate_password() {
    openssl rand -base64 24 2>/dev/null | tr -d "=+/" | cut -c1-20 \
        || LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom 2>/dev/null | head -c 20 \
        || echo "Rh1n0$(date +%s | tail -c 12)"
}

# ── Retry wrapper for network operations ──────────────────────────────────────
retry() {
    local description="$1"; shift
    local max="${RETRY_MAX:-$PULL_RETRIES}"
    local delay="${RETRY_DELAY:-$PULL_DELAY}"
    local n=0

    until "$@"; do
        n=$((n + 1))
        if [ "$n" -ge "$max" ]; then
            log_warn "Failed after ${max} attempts: ${description}"
            return 1
        fi
        log_warn "Attempt ${n}/${max} failed for: ${description}. Retrying in ${delay}s..."
        sleep "$delay"
    done
    return 0
}

# ── Parse CLI arguments ───────────────────────────────────────────────────────
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --no-traces)
                SKIP_JAEGER=true
                log_info "Jaeger/tracing disabled via --no-traces flag"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — ROOT CHECK
# ═══════════════════════════════════════════════════════════════════════════════

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root or with sudo."
        echo ""
        echo "  Usage:  sudo bash install-rhinometric.sh"
        echo ""
        exit 1  # This is the ONLY hard exit — root is non-negotiable
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — SYSTEM CHECKS (warnings, not fatal)
# ═══════════════════════════════════════════════════════════════════════════════

check_os() {
    log_info "Checking operating system..."
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        if [[ "$ID" == "ubuntu" ]]; then
            log_info "✓ Ubuntu ${VERSION_ID} detected"
        else
            log_warn "OS: ${PRETTY_NAME} — Ubuntu 22.04+ recommended"
        fi
    else
        log_warn "Could not detect OS. Ubuntu 22.04+ recommended."
    fi
}

check_resources() {
    log_info "Checking system resources..."

    local cpu_cores
    cpu_cores=$(nproc 2>/dev/null || echo 0)
    if [[ "$cpu_cores" -ge "$MIN_CPU_CORES" ]]; then
        log_info "✓ CPU: ${cpu_cores} cores (minimum ${MIN_CPU_CORES})"
    else
        log_warn "CPU: ${cpu_cores} cores detected (recommended: ${MIN_CPU_CORES}+)"
    fi

    local total_ram_gb
    total_ram_gb=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}' || echo 0)
    if [[ "$total_ram_gb" -ge "$MIN_RAM_GB" ]]; then
        log_info "✓ RAM: ${total_ram_gb} GB (minimum ${MIN_RAM_GB} GB)"
    else
        log_warn "RAM: ${total_ram_gb} GB detected (recommended: ${MIN_RAM_GB} GB). Installation continues."
    fi

    local available_gb
    available_gb=$(df -BG "${INSTALL_DIR}" 2>/dev/null | awk 'NR==2{print $4}' | sed 's/G//' || echo 0)
    if [[ "$available_gb" -ge "$REQUIRED_SPACE_GB" ]]; then
        log_info "✓ Disk: ${available_gb} GB available (minimum ${REQUIRED_SPACE_GB} GB)"
    else
        log_warn "Disk: ${available_gb} GB available (recommended: ${REQUIRED_SPACE_GB} GB). Installation continues."
    fi
}

check_docker() {
    log_info "Checking Docker..."

    if ! command -v docker &>/dev/null; then
        log_warn "Docker is not installed. Attempting automatic install..."
        if retry "Docker install" bash -c "curl -fsSL https://get.docker.com | sh"; then
            log_info "✓ Docker installed successfully"
        else
            fail_critical "Docker installation failed. Install manually: curl -fsSL https://get.docker.com | sh"
            return 1
        fi
    fi

    local docker_ver
    docker_ver=$(docker --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1 || echo "unknown")
    log_info "✓ Docker ${docker_ver} installed"

    if ! docker compose version &>/dev/null; then
        fail_critical "Docker Compose v2 not available. Required for multi-container stack."
        return 1
    fi

    local compose_ver
    compose_ver=$(docker compose version --short 2>/dev/null || echo "unknown")
    log_info "✓ Docker Compose ${compose_ver} installed"
    return 0
}

check_ports() {
    log_info "Checking port availability..."

    local required_ports=(3000 3002 5432 6379 8105 9090 9093 3100 16686)
    local ports_in_use=()

    for port in "${required_ports[@]}"; do
        if ss -tuln 2>/dev/null | grep -q ":${port} "; then
            ports_in_use+=("$port")
        fi
    done

    if [[ ${#ports_in_use[@]} -gt 0 ]]; then
        log_warn "Ports already in use: ${ports_in_use[*]}. This may be a previous installation or conflicting services."
    else
        log_info "✓ All required ports are available"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — MACHINE FINGERPRINT
# ═══════════════════════════════════════════════════════════════════════════════

detect_fingerprint() {
    log_step "STEP 1/8 — Machine Fingerprint Detection"

    install_rhino_lic

    if command -v rhino-lic &>/dev/null; then
        MACHINE_FINGERPRINT=$(rhino-lic fingerprint 2>/dev/null || echo "")
    fi

    if [[ -n "$MACHINE_FINGERPRINT" ]]; then
        echo ""
        echo -e "${BOLD}┌──────────────────────────────────────────────────────────────┐${NC}"
        echo -e "${BOLD}│           Machine Fingerprint Detected                       │${NC}"
        echo -e "${BOLD}├──────────────────────────────────────────────────────────────┤${NC}"
        echo -e "${BOLD}│${NC}                                                              ${BOLD}│${NC}"
        echo -e "${BOLD}│${NC}  ${CYAN}${MACHINE_FINGERPRINT}${NC}"
        echo -e "${BOLD}│${NC}                                                              ${BOLD}│${NC}"
        echo -e "${BOLD}│${NC}  Provide this fingerprint to Rhinometric to obtain           ${BOLD}│${NC}"
        echo -e "${BOLD}│${NC}  your signed license file (license.key).                     ${BOLD}│${NC}"
        echo -e "${BOLD}│${NC}                                                              ${BOLD}│${NC}"
        echo -e "${BOLD}└──────────────────────────────────────────────────────────────┘${NC}"
        echo ""
    else
        log_warn "Could not detect machine fingerprint. License validation will be skipped."
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — LICENSE VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

validate_license() {
    log_step "STEP 2/8 — License Validation"

    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local default_license=""

    if [[ -f "${script_dir}/license.key" ]]; then
        default_license="${script_dir}/license.key"
        log_info "Found license.key in installer directory."
    elif [[ -f "${INSTALL_DIR}/license.key" ]]; then
        default_license="${INSTALL_DIR}/license.key"
        log_info "Found existing license.key in ${INSTALL_DIR}."
    fi

    echo ""
    if [[ -n "$default_license" ]]; then
        echo -e "  License file found: ${CYAN}${default_license}${NC}"
        read -r -p "  Use this license? (Y/n): " use_default
        if [[ "$use_default" =~ ^[Nn]$ ]]; then
            default_license=""
        fi
    fi

    local license_path="$default_license"

    if [[ -z "$license_path" ]]; then
        echo ""
        read -r -p "  Enter path to license.key (or press ENTER to continue without license): " license_path
    fi

    if [[ -z "$license_path" ]]; then
        LICENSE_STATUS="unlicensed"
        echo ""
        log_warn "No license provided. Platform will start in unlicensed mode."
        log_info "You can add a license later by placing license.key in ${INSTALL_DIR}/"
        return 0
    fi

    if [[ ! -f "$license_path" ]]; then
        log_warn "License file not found: ${license_path}. Continuing in unlicensed mode."
        LICENSE_STATUS="unlicensed"
        return 0
    fi

    mkdir -p "${INSTALL_DIR}" 2>/dev/null || true
    cp "$license_path" "${LICENSE_DEST}" 2>/dev/null || true

    if ! command -v rhino-lic &>/dev/null; then
        log_warn "rhino-lic binary not available. Cannot validate license. Continuing."
        LICENSE_STATUS="unverified"
        return 0
    fi

    echo ""
    log_info "Validating license..."

    local validation_output
    validation_output=$(rhino-lic validate "${license_path}" 2>&1)
    local exit_code=$?

    case $exit_code in
        0)
            LICENSE_STATUS="valid"
            LICENSE_PLAN=$(echo "$validation_output" | grep -oP '"plan"\s*:\s*"\K[^"]+' || echo "unknown")
            LICENSE_HOSTS=$(echo "$validation_output" | grep -oP '"max_hosts"\s*:\s*\K[0-9]+' || echo "unknown")
            LICENSE_EXPIRES=$(echo "$validation_output" | grep -oP '"expires_at"\s*:\s*"\K[^"]+' || echo "unknown")
            LICENSE_CUSTOMER=$(echo "$validation_output" | grep -oP '"customer"\s*:\s*"\K[^"]+' || echo "unknown")

            echo ""
            echo -e "${GREEN}${BOLD}┌──────────────────────────────────────────────────────────────┐${NC}"
            echo -e "${GREEN}${BOLD}│               ✓ License Valid                                │${NC}"
            echo -e "${GREEN}${BOLD}├──────────────────────────────────────────────────────────────┤${NC}"
            echo -e "${GREEN}│${NC}  Customer   : ${BOLD}${LICENSE_CUSTOMER}${NC}"
            echo -e "${GREEN}│${NC}  Plan       : ${BOLD}${LICENSE_PLAN}${NC}"
            echo -e "${GREEN}│${NC}  Max Hosts  : ${BOLD}${LICENSE_HOSTS}${NC}"
            echo -e "${GREEN}│${NC}  Expires    : ${BOLD}${LICENSE_EXPIRES}${NC}"
            echo -e "${GREEN}│${NC}  Fingerprint: ${BOLD}${MACHINE_FINGERPRINT}${NC}"
            echo -e "${GREEN}${BOLD}└──────────────────────────────────────────────────────────────┘${NC}"
            echo ""
            ;;
        1)
            LICENSE_STATUS="invalid_signature"
            log_warn "License signature is INVALID. The license file may be corrupted or tampered."
            log_warn "The platform will start but licensing will be limited."
            ;;
        2)
            LICENSE_STATUS="expired"
            log_warn "License has EXPIRED. Contact Rhinometric for renewal."
            log_warn "The platform will start but licensing will be limited."
            ;;
        3)
            LICENSE_STATUS="fingerprint_mismatch"
            log_warn "License FINGERPRINT MISMATCH. This license was issued for a different machine."
            log_warn "Expected fingerprint for this machine: ${MACHINE_FINGERPRINT}"
            log_warn "The platform will start but licensing will be limited."
            ;;
        4)
            LICENSE_STATUS="parse_error"
            log_warn "License file could not be parsed. It may be in an incorrect format."
            log_warn "The platform will start but licensing will be limited."
            ;;
        *)
            LICENSE_STATUS="unknown_error"
            log_warn "License validation returned unexpected code: ${exit_code}"
            log_warn "The platform will start but licensing will be limited."
            ;;
    esac

    return 0
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5 — INSTALL RHINO-LIC BINARY
# ═══════════════════════════════════════════════════════════════════════════════

install_rhino_lic() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if command -v rhino-lic &>/dev/null; then
        log_info "✓ rhino-lic already installed at $(command -v rhino-lic)"
        return 0
    fi

    if [[ -f "${script_dir}/rhino-lic" ]]; then
        log_info "Installing rhino-lic from package..."
        cp "${script_dir}/rhino-lic" "${RHINO_LIC_BIN}"
        chmod 755 "${RHINO_LIC_BIN}"
        if command -v rhino-lic &>/dev/null; then
            log_info "✓ rhino-lic installed to ${RHINO_LIC_BIN}"
            return 0
        fi
    fi

    if [[ -f "${INSTALL_DIR}/rhino-lic" ]]; then
        log_info "Installing rhino-lic from ${INSTALL_DIR}..."
        cp "${INSTALL_DIR}/rhino-lic" "${RHINO_LIC_BIN}"
        chmod 755 "${RHINO_LIC_BIN}"
        if command -v rhino-lic &>/dev/null; then
            log_info "✓ rhino-lic installed to ${RHINO_LIC_BIN}"
            return 0
        fi
    fi

    log_warn "rhino-lic binary not found in package. Fingerprint and license validation will be skipped."
    return 1
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6 — DIRECTORY SETUP & CREDENTIALS
# ═══════════════════════════════════════════════════════════════════════════════

create_directories() {
    log_info "Creating directory structure..."

    local dirs=(
        "${INSTALL_DIR}"
        "${INSTALL_DIR}/config"
        "${INSTALL_DIR}/grafana/provisioning/dashboards/json"
        "${INSTALL_DIR}/prometheus"
        "${INSTALL_DIR}/alertmanager"
        "${INSTALL_DIR}/loki"
        "${INSTALL_DIR}/data"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "$dir" 2>/dev/null || true
    done

    log_info "✓ Directories created in ${INSTALL_DIR}"
}

generate_credentials() {
    log_info "Generating secure credentials..."

    POSTGRES_PASSWORD=$(generate_password)
    REDIS_PASSWORD=$(generate_password)
    GRAFANA_PASSWORD=$(generate_password)
    ADMIN_PASSWORD=$(generate_password)

    log_info "✓ Credentials generated"
}

write_env_file() {
    log_info "Writing environment file..."

    local server_ip
    server_ip=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")

    cat > "${INSTALL_DIR}/.env" << ENVEOF
# RHINOMETRIC v${VERSION} — Auto-generated $(date -u +"%Y-%m-%d %H:%M:%S UTC")
# DO NOT commit this file to git.

# === Public Access ===
PUBLIC_IP=${server_ip}
DOMAIN=${server_ip}
CUSTOMER_DOMAIN=${server_ip}

# === Database ===
POSTGRES_USER=rhinometric
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=rhinometric
DB_NAME=rhinometric

# === Cache ===
REDIS_PASSWORD=${REDIS_PASSWORD}

# === Grafana ===
GRAFANA_USER=admin
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}
GRAFANA_DOMAIN=${server_ip}

# === Console Backend ===
SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || generate_password)
JWT_SECRET=$(openssl rand -hex 48 2>/dev/null || generate_password)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=${ADMIN_PASSWORD}
API_VERSION=${VERSION}

# === License ===
LICENSE_STATUS=${LICENSE_STATUS}
ENVEOF

    chmod 600 "${INSTALL_DIR}/.env"
    log_info "✓ Environment file created"
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6b — PREPARE RUNTIME VOLUME DIRECTORIES (NEW in v3.0.2)
# ═══════════════════════════════════════════════════════════════════════════════
# docker-compose.yml mounts host directories under ${HOME}/rhinometric_data_v2.5/
# These MUST exist with correct ownership BEFORE docker compose up.
# Known UIDs:
#   Jaeger (all-in-one)  : 10001:0
#   PostgreSQL           : 999:999
#   Redis                : 999:999
#   Alertmanager         : 65534:65534 (nobody)
#   Loki                 : runs as root (user: '0' in compose)
#   Others               : root or generic — 777 is safe
# ═══════════════════════════════════════════════════════════════════════════════

prepare_runtime_dirs() {
    log_info "Preparing runtime volume directories..."

    # Determine effective HOME for compose context
    # When running as sudo, HOME is typically /root
    DATA_ROOT="${HOME}/rhinometric_data_v2.5"
    export HOME  # ensure docker compose inherits the same HOME

    log_info "Data root: ${DATA_ROOT}"

    # All directories referenced by volume mounts in docker-compose.yml
    local all_dirs=(
        "${DATA_ROOT}/jaeger"
        "${DATA_ROOT}/ai-anomaly/models"
        "${DATA_ROOT}/ai-anomaly/data"
        "${DATA_ROOT}/alertmanager"
        "${DATA_ROOT}/console-backend/data"
        "${DATA_ROOT}/console-backend/logs"
        "${DATA_ROOT}/license-server/logs"
        "${DATA_ROOT}/loki"
        "${DATA_ROOT}/postgres"
        "${DATA_ROOT}/redis"
    )

    local created=0
    for dir in "${all_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir" 2>/dev/null
            created=$((created + 1))
        fi
    done

    if [[ $created -gt 0 ]]; then
        log_info "Created ${created} runtime directories"
    fi

    # ── Fix Jaeger permissions (UID 10001, GID 0) ──
    # Jaeger all-in-one runs as uid=10001 gid=0(root)
    # It needs to create /badger/key and /badger/data subdirectories
    if [[ -d "${DATA_ROOT}/jaeger" ]]; then
        # Pre-create the badger subdirectories to avoid mkdir failures
        mkdir -p "${DATA_ROOT}/jaeger/key" "${DATA_ROOT}/jaeger/data" 2>/dev/null || true
        chown -R 10001:0 "${DATA_ROOT}/jaeger" 2>/dev/null || true
        chmod -R 755 "${DATA_ROOT}/jaeger" 2>/dev/null || true
        log_info "✓ Jaeger volume: ${DATA_ROOT}/jaeger (uid=10001, badger subdirs created)"
    fi

    # ── Fix Alertmanager permissions (UID 65534 = nobody) ──
    if [[ -d "${DATA_ROOT}/alertmanager" ]]; then
        chown -R 65534:65534 "${DATA_ROOT}/alertmanager" 2>/dev/null || true
        chmod -R 755 "${DATA_ROOT}/alertmanager" 2>/dev/null || true
        log_info "✓ Alertmanager volume: ${DATA_ROOT}/alertmanager (uid=65534)"
    fi

    # ── Fix PostgreSQL permissions (UID 999) ──
    if [[ -d "${DATA_ROOT}/postgres" ]]; then
        chown -R 999:999 "${DATA_ROOT}/postgres" 2>/dev/null || true
        chmod -R 700 "${DATA_ROOT}/postgres" 2>/dev/null || true
        log_info "✓ PostgreSQL volume: ${DATA_ROOT}/postgres (uid=999)"
    fi

    # ── Fix Redis permissions (UID 999) ──
    if [[ -d "${DATA_ROOT}/redis" ]]; then
        chown -R 999:999 "${DATA_ROOT}/redis" 2>/dev/null || true
        chmod -R 755 "${DATA_ROOT}/redis" 2>/dev/null || true
        log_info "✓ Redis volume: ${DATA_ROOT}/redis (uid=999)"
    fi

    # ── Loki runs as root (user: '0' in compose) — just ensure dir exists ──
    if [[ -d "${DATA_ROOT}/loki" ]]; then
        chmod -R 755 "${DATA_ROOT}/loki" 2>/dev/null || true
        log_info "✓ Loki volume: ${DATA_ROOT}/loki (root)"
    fi

    # ── General permissive dirs (ai-anomaly, console-backend, license-server) ──
    local general_dirs=(
        "${DATA_ROOT}/ai-anomaly"
        "${DATA_ROOT}/console-backend"
        "${DATA_ROOT}/license-server"
    )
    for dir in "${general_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            chmod -R 777 "$dir" 2>/dev/null || true
        fi
    done
    log_info "✓ General volumes: ai-anomaly, console-backend, license-server (world-writable)"

    log_info "✓ All runtime volume directories prepared"
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7 — COPY FILES
# ═══════════════════════════════════════════════════════════════════════════════

copy_files() {
    log_info "Copying configuration files..."

    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Copy docker-compose.yml
    if [[ -f "${script_dir}/${COMPOSE_FILE}" ]]; then
        cp "${script_dir}/${COMPOSE_FILE}" "${INSTALL_DIR}/docker-compose.yml"
        log_info "✓ Docker Compose file copied"
    elif [[ -f "${INSTALL_DIR}/docker-compose.yml" ]]; then
        log_info "✓ Docker Compose file already exists"
    else
        fail_critical "docker-compose.yml not found in package or ${INSTALL_DIR}. Cannot proceed."
        return 1
    fi

    # Copy rhino-lic to install dir for future reference
    if [[ -f "${script_dir}/rhino-lic" ]]; then
        cp "${script_dir}/rhino-lic" "${INSTALL_DIR}/rhino-lic"
        chmod 755 "${INSTALL_DIR}/rhino-lic"
    fi

    # Copy uninstall script if present
    if [[ -f "${script_dir}/uninstall-rhinometric.sh" ]]; then
        cp "${script_dir}/uninstall-rhinometric.sh" "${INSTALL_DIR}/uninstall-rhinometric.sh"
        chmod 755 "${INSTALL_DIR}/uninstall-rhinometric.sh"
        log_info "✓ Uninstall script copied"
    fi

    # ── Copy all configuration directories from package ───────────────────
    local config_dirs=("config" "alertmanager" "grafana" "nginx" "blackbox" "init-db" "prometheus" "loki")
    for dir in "${config_dirs[@]}"; do
        if [[ -d "${script_dir}/${dir}" ]]; then
            mkdir -p "${INSTALL_DIR}/${dir}" 2>/dev/null || true
            cp -a "${script_dir}/${dir}/." "${INSTALL_DIR}/${dir}/" 2>/dev/null || true
            log_info "✓ ${dir}/ copied"
        fi
    done

    # ── Copy build context directories for locally-built services ─────────
    local build_dirs=("rhinometric-ai-anomaly" "rhinometric-console" "license-server-v2" "license-management-ui")
    for dir in "${build_dirs[@]}"; do
        if [[ -d "${script_dir}/${dir}" ]]; then
            mkdir -p "${INSTALL_DIR}/${dir}" 2>/dev/null || true
            cp -a "${script_dir}/${dir}/." "${INSTALL_DIR}/${dir}/" 2>/dev/null || true
            log_info "✓ ${dir}/ copied (build context)"
        fi
    done

    # Verify critical file exists after copy
    if [[ ! -f "${INSTALL_DIR}/docker-compose.yml" ]]; then
        fail_critical "docker-compose.yml missing in ${INSTALL_DIR} after copy step."
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7b — LOAD PRE-BUILT DOCKER IMAGES
# ═══════════════════════════════════════════════════════════════════════════════

load_images() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd)"

    local images_file=""
    if [[ -f "${script_dir}/images.tar.gz" ]]; then
        images_file="${script_dir}/images.tar.gz"
    elif [[ -f "${script_dir}/images.tar" ]]; then
        images_file="${script_dir}/images.tar"
    fi

    if [[ -z "$images_file" ]]; then
        log_info "No pre-built images archive found. Will build locally and pull from registries."
        return 0
    fi

    log_info "Loading pre-built Docker images from $(basename "$images_file")..."
    local load_output
    if [[ "$images_file" == *.gz ]]; then
        load_output=$(gunzip -c "$images_file" | docker load 2>&1)
    else
        load_output=$(docker load -i "$images_file" 2>&1)
    fi

    local load_exit=$?

    if [[ $load_exit -eq 0 ]]; then
        local loaded_count
        loaded_count=$(echo "$load_output" | grep -c "Loaded image" || echo 0)
        log_info "✓ Docker images loaded successfully (${loaded_count} images)"
    else
        fail_critical "Failed to load Docker images from ${images_file}."
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7c — VERIFY BUILD CONTEXTS
# ═══════════════════════════════════════════════════════════════════════════════

verify_build_contexts() {
    log_info "Verifying Docker Compose build contexts..."
    cd "${INSTALL_DIR}" || return 1

    local missing_contexts=()
    local context_path
    while IFS= read -r context_path; do
        context_path=$(echo "$context_path" | sed 's/^[[:space:]]*context:[[:space:]]*//' | sed 's/[[:space:]]*$//')
        if [[ "$context_path" == ./* ]]; then
            context_path="${INSTALL_DIR}/${context_path#./}"
        fi
        if [[ ! -d "$context_path" ]]; then
            missing_contexts+=("$context_path")
        fi
    done < <(grep 'context:' "${INSTALL_DIR}/docker-compose.yml" 2>/dev/null | grep -v '#')

    if [[ ${#missing_contexts[@]} -gt 0 ]]; then
        log_error "Missing build context directories:"
        for ctx in "${missing_contexts[@]}"; do
            log_error "  - ${ctx}"
        done
        local can_continue=true
        for ctx in "${missing_contexts[@]}"; do
            local dir_name
            dir_name=$(basename "$ctx")
            if ! docker images --format "{{.Repository}}" 2>/dev/null | grep -qi "$dir_name"; then
                can_continue=false
            fi
        done
        if $can_continue; then
            log_warn "Build context dirs missing but matching Docker images found locally."
        else
            fail_critical "Build context directories missing and no pre-built images found. Package may be incomplete."
            return 1
        fi
    else
        log_info "✓ All build context directories present"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 8 — START DOCKER STACK
# ═══════════════════════════════════════════════════════════════════════════════

start_stack() {
    log_step "STEP 6/8 — Starting Docker Stack"

    cd "${INSTALL_DIR}" || {
        fail_critical "Cannot access ${INSTALL_DIR}"
        return 1
    }

    if [[ ! -f "docker-compose.yml" ]]; then
        fail_critical "docker-compose.yml not found in ${INSTALL_DIR}"
        return 1
    fi

    # Validate compose config before anything else
    log_info "Validating Docker Compose configuration..."
    local config_output
    config_output=$(docker compose config 2>&1)
    local config_exit=$?
    if [[ $config_exit -ne 0 ]]; then
        fail_critical "Docker Compose configuration is invalid: $(echo "$config_output" | tail -5)"
        return 1
    fi
    log_info "✓ Compose configuration valid"

    # Pull public images (ignore failures for locally-built images)
    log_info "Pulling Docker images (this may take several minutes)..."
    docker compose pull --ignore-buildable 2>&1 || true

    # Build locally-built images
    log_info "Building local images (this may take several minutes on first install)..."
    local build_output
    build_output=$(docker compose build 2>&1)
    local build_exit=$?
    if [[ $build_exit -ne 0 ]]; then
        log_warn "docker compose build had issues: $(echo "$build_output" | tail -10)"
    else
        log_info "✓ Local images built successfully"
    fi

    # Start stack
    log_info "Starting services with docker compose up -d..."
    local compose_output
    compose_output=$(docker compose up -d 2>&1)
    local compose_exit=$?

    if [[ $compose_exit -ne 0 ]]; then
        log_error "docker compose up failed (exit code ${compose_exit}). Will attempt auto-fix..."
        echo ""
        echo "$compose_output" | tail -20
        echo ""
        # Don't fail_critical yet — auto_fix_and_retry will handle it
        return 1
    fi

    log_info "✓ Docker Compose started"

    # Verify at least some containers came up
    sleep 10
    local running_count
    running_count=$(docker compose ps --status running -q 2>/dev/null | wc -l || echo 0)
    if [[ "$running_count" -eq 0 ]]; then
        log_error "docker compose up succeeded but 0 containers are running."
        docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || true
        return 1
    fi

    log_info "Containers starting: ${running_count} running so far"

    # Wait for initialization
    log_info "Waiting for services to initialize (30s)..."
    sleep 30
    return 0
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 9 — FULL STACK HEALTH CHECK (Enhanced in v3.0.2)
# ═══════════════════════════════════════════════════════════════════════════════

health_check() {
    log_step "STEP 7/8 — Full Stack Health Verification"

    cd "${INSTALL_DIR}" || return 1

    local total running
    total=$(docker compose ps -q 2>/dev/null | wc -l || echo 0)
    running=$(docker compose ps --status running -q 2>/dev/null | wc -l || echo 0)

    log_info "Containers: ${running}/${total} running"

    if [[ "$running" -eq 0 ]]; then
        fail_critical "No containers are running. The platform failed to start."
        echo ""
        log_error "Container statuses:"
        docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || true
        echo ""
        log_error "Recent logs from failed containers:"
        docker compose logs --tail=20 2>/dev/null | tail -40 || true
        return 1
    fi

    # ── Phase 1: Wait for critical infrastructure (postgres, redis) ──
    log_info "Phase 1: Waiting for infrastructure services..."
    local infra_ok=true
    local n=0
    while [ "$n" -lt 12 ]; do
        local pg_ok=false
        local redis_ok=false
        local pg_status
        pg_status=$(docker inspect --format '{{.State.Health.Status}}' rhinometric-postgres 2>/dev/null || echo "not_found")
        if [[ "$pg_status" == "healthy" ]]; then pg_ok=true; fi
        local redis_status
        redis_status=$(docker inspect --format '{{.State.Health.Status}}' rhinometric-redis 2>/dev/null || echo "not_found")
        if [[ "$redis_status" == "healthy" ]]; then redis_ok=true; fi

        if $pg_ok && $redis_ok; then
            log_info "✓ PostgreSQL: healthy"
            log_info "✓ Redis: healthy"
            break
        fi
        n=$((n + 1))
        if [[ "$n" -ge 12 ]]; then
            if ! $pg_ok; then log_warn "PostgreSQL not healthy after 120s (status: ${pg_status})"; infra_ok=false; fi
            if ! $redis_ok; then log_warn "Redis not healthy after 120s (status: ${redis_status})"; infra_ok=false; fi
        else
            sleep 10
        fi
    done

    if ! $infra_ok; then
        fail_critical "Infrastructure services (postgres/redis) failed to become healthy within 120s."
        return 1
    fi

    # ── Phase 2: Wait for all services with healthchecks ──
    log_info "Phase 2: Waiting for all services to become healthy..."
    log_info "Timeout: $((HEALTH_RETRIES * HEALTH_DELAY))s (${HEALTH_RETRIES} attempts x ${HEALTH_DELAY}s)"

    # Services that have healthchecks defined in docker-compose.yml
    local healthy_services=(
        "rhinometric-license-server-v2"
        "rhinometric-postgres"
        "rhinometric-redis"
        "rhinometric-prometheus"
        "rhinometric-victoria-metrics"
        "rhinometric-loki"
        "rhinometric-grafana"
        "rhinometric-otel-collector"
        "rhinometric-alertmanager"
        "rhinometric-cadvisor"
        "rhinometric-console-backend"
        "rhinometric-console-frontend"
        "rhinometric-nginx"
    )

    # Only check Jaeger if not skipped
    if ! $SKIP_JAEGER; then
        healthy_services+=("rhinometric-jaeger")
    fi

    n=0
    local all_healthy=false
    while [ "$n" -lt "$HEALTH_RETRIES" ]; do
        local unhealthy_list=()
        local svc_status

        for svc in "${healthy_services[@]}"; do
            svc_status=$(docker inspect --format '{{.State.Health.Status}}' "$svc" 2>/dev/null || echo "no_healthcheck")
            if [[ "$svc_status" == "no_healthcheck" ]]; then
                # Check if running at least
                local svc_running
                svc_running=$(docker inspect --format '{{.State.Status}}' "$svc" 2>/dev/null || echo "not_found")
                if [[ "$svc_running" != "running" ]]; then
                    unhealthy_list+=("${svc}=${svc_running}")
                fi
            elif [[ "$svc_status" != "healthy" ]]; then
                unhealthy_list+=("${svc}=${svc_status}")
            fi
        done

        if [[ ${#unhealthy_list[@]} -eq 0 ]]; then
            all_healthy=true
            break
        fi

        n=$((n + 1))
        if [[ "$n" -lt "$HEALTH_RETRIES" ]]; then
            if [[ $((n % 6)) -eq 0 ]]; then
                log_info "  Still waiting (${n}/${HEALTH_RETRIES}): ${unhealthy_list[*]}"
            else
                log_info "  Waiting for services... (${n}/${HEALTH_RETRIES})"
            fi
            sleep "$HEALTH_DELAY"
        fi
    done

    if $all_healthy; then
        log_info "✓ All ${#healthy_services[@]} monitored services are healthy"
    else
        # Some services unhealthy — report but don't necessarily fail
        local critical_unhealthy=()
        local non_critical_unhealthy=()

        for svc in "${healthy_services[@]}"; do
            svc_status=$(docker inspect --format '{{.State.Health.Status}}' "$svc" 2>/dev/null || echo "unknown")
            local svc_state
            svc_state=$(docker inspect --format '{{.State.Status}}' "$svc" 2>/dev/null || echo "unknown")

            if [[ "$svc_status" != "healthy" && "$svc_state" != "running" ]]; then
                critical_unhealthy+=("${svc} (status=${svc_state}, health=${svc_status})")
            elif [[ "$svc_status" == "unhealthy" ]]; then
                non_critical_unhealthy+=("${svc} (health=unhealthy but running)")
            fi
        done

        if [[ ${#critical_unhealthy[@]} -gt 0 ]]; then
            log_error "Critical: These services are NOT running:"
            for item in "${critical_unhealthy[@]}"; do
                log_error "  ✗ ${item}"
                local svc_name
                svc_name=$(echo "$item" | cut -d' ' -f1 | sed 's/rhinometric-//')
                docker compose logs --tail=10 "$svc_name" 2>/dev/null || true
            done
        fi

        if [[ ${#non_critical_unhealthy[@]} -gt 0 ]]; then
            log_warn "These services are running but unhealthy (may still be starting):"
            for item in "${non_critical_unhealthy[@]}"; do
                log_warn "  ⚠ ${item}"
            done
        fi
    fi

    # ── Phase 3: HTTP-level checks on key endpoints ──
    log_info "Phase 3: Verifying key HTTP endpoints..."
    local console_ok=false
    local grafana_ok=false
    local prom_ok=false

    local http_attempts=0
    while [ "$http_attempts" -lt 6 ]; do
        if ! $console_ok && curl -fsS "http://127.0.0.1:3002" >/dev/null 2>&1; then
            console_ok=true
            log_info "✓ Console (port 3002): responding"
        fi
        if ! $grafana_ok && curl -fsS "http://127.0.0.1:3000/api/health" >/dev/null 2>&1; then
            grafana_ok=true
            log_info "✓ Grafana (port 3000): responding"
        fi
        if ! $prom_ok && curl -fsS "http://127.0.0.1:9090/-/ready" >/dev/null 2>&1; then
            prom_ok=true
            log_info "✓ Prometheus (port 9090): responding"
        fi
        if $console_ok && $grafana_ok && $prom_ok; then
            break
        fi
        http_attempts=$((http_attempts + 1))
        if [[ "$http_attempts" -lt 6 ]]; then
            sleep 10
        fi
    done

    if ! $console_ok; then
        fail_critical "Console (port 3002) not responding after health check timeout"
    fi
    if ! $grafana_ok; then
        log_warn "Grafana (port 3000) not responding — non-blocking but should be investigated"
    fi

    # ── Check ai-anomaly separately (non-blocking) ──
    local ai_status
    ai_status=$(docker inspect --format '{{.State.Health.Status}}' rhinometric-ai-anomaly 2>/dev/null || echo "unknown")
    if [[ "$ai_status" == "healthy" ]]; then
        log_info "✓ AI Anomaly: healthy"
    else
        log_warn "AI Anomaly: ${ai_status} — this is non-blocking. The service may need more time to initialize."
    fi

    # ── Final status summary ──
    echo ""
    log_info "Current container statuses:"
    docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || true
    echo ""

    if [[ "$INSTALL_CRITICAL_FAILURE" == "true" ]]; then
        return 1
    fi
    return 0
}

# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-FIX & RETRY (NEW in v3.0.2)
# ═══════════════════════════════════════════════════════════════════════════════

auto_fix_and_retry() {
    log_step "Auto-Fix: Detecting and fixing common issues..."

    cd "${INSTALL_DIR}" || return 1

    local fix_applied=false

    # ── Scan containers for known error patterns ──
    local containers
    containers=$(docker compose ps -q 2>/dev/null || echo "")
    if [[ -z "$containers" ]]; then
        log_error "No containers found. Cannot auto-fix."
        return 1
    fi

    # Check for permission denied errors in recent logs
    local perm_errors
    perm_errors=$(docker compose logs --tail=50 2>/dev/null | grep -i "permission denied" || true)
    if [[ -n "$perm_errors" ]]; then
        log_info "Detected 'permission denied' errors. Re-applying volume permissions..."
        prepare_runtime_dirs
        fix_applied=true
    fi

    # Check for "mkdir" errors (Jaeger badger)
    local mkdir_errors
    mkdir_errors=$(docker compose logs --tail=50 2>/dev/null | grep -i "mkdir.*permission denied\|Error Creating Dir" || true)
    if [[ -n "$mkdir_errors" ]]; then
        log_info "Detected directory creation errors (likely Jaeger/Badger). Fixing..."
        if [[ -n "$DATA_ROOT" ]]; then
            mkdir -p "${DATA_ROOT}/jaeger/key" "${DATA_ROOT}/jaeger/data" 2>/dev/null || true
            chown -R 10001:0 "${DATA_ROOT}/jaeger" 2>/dev/null || true
            chmod -R 755 "${DATA_ROOT}/jaeger" 2>/dev/null || true
            log_info "✓ Created and permissioned Jaeger badger subdirectories"
        fi
        fix_applied=true
    fi

    # Check for restarting containers
    local restarting
    restarting=$(docker compose ps --format "{{.Name}} {{.Status}}" 2>/dev/null | grep -i "restarting" | awk '{print $1}' || true)
    if [[ -n "$restarting" ]]; then
        log_info "Found restarting containers: ${restarting}"
        fix_applied=true
    fi

    # Check for unhealthy containers
    local unhealthy_containers
    unhealthy_containers=$(docker compose ps --format "{{.Name}} {{.Status}}" 2>/dev/null | grep -i "unhealthy" | awk '{print $1}' || true)
    if [[ -n "$unhealthy_containers" ]]; then
        log_info "Found unhealthy containers: ${unhealthy_containers}"
        fix_applied=true
    fi

    if ! $fix_applied; then
        log_info "No auto-fixable issues detected."
        return 1
    fi

    # ── Apply fix: stop and restart the stack ──
    log_info "Restarting stack after fixes..."
    docker compose down 2>/dev/null || true
    sleep 5

    log_info "Starting services with docker compose up -d..."
    local compose_output
    compose_output=$(docker compose up -d 2>&1)
    local compose_exit=$?

    if [[ $compose_exit -ne 0 ]]; then
        log_error "docker compose up still failing after auto-fix (exit code ${compose_exit})"
        echo "$compose_output" | tail -20
        return 1
    fi

    log_info "✓ Stack restarted after auto-fix"
    log_info "Waiting for services to initialize (45s)..."
    sleep 45

    return 0
}

# ═══════════════════════════════════════════════════════════════════════════════
# DEBUG BUNDLE GENERATION (NEW in v3.0.2)
# ═══════════════════════════════════════════════════════════════════════════════

generate_debug_bundle() {
    log_info "Generating debug bundle for troubleshooting..."

    local bundle_dir="/tmp/rhinometric-debug-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "${bundle_dir}" 2>/dev/null || true

    cd "${INSTALL_DIR}" 2>/dev/null || true

    # Collect docker compose ps
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" > "${bundle_dir}/docker-compose-ps.txt" 2>&1 || true

    # Collect docker compose config (non-sensitive)
    docker compose config > "${bundle_dir}/docker-compose-config.yml" 2>&1 || true

    # Collect logs from all services (last 100 lines each)
    docker compose logs --tail=100 > "${bundle_dir}/all-services.log" 2>&1 || true

    # Collect logs from known problematic services
    for svc in jaeger victoria-metrics rhinometric-ai-anomaly alertmanager; do
        docker compose logs --tail=200 "$svc" > "${bundle_dir}/${svc}.log" 2>&1 || true
    done

    # System info
    {
        echo "=== System Info ==="
        echo "Date: $(date -u)"
        echo "Hostname: $(hostname 2>/dev/null || echo unknown)"
        echo "Kernel: $(uname -r 2>/dev/null || echo unknown)"
        echo "CPU: $(nproc 2>/dev/null || echo unknown) cores"
        echo "RAM: $(free -h 2>/dev/null | head -2 || echo unknown)"
        echo "Disk: $(df -h "${INSTALL_DIR}" 2>/dev/null | tail -1 || echo unknown)"
        echo ""
        echo "=== Docker Info ==="
        docker --version 2>/dev/null || echo "Docker: not found"
        docker compose version 2>/dev/null || echo "Compose: not found"
        echo ""
        echo "=== Docker Images ==="
        docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>/dev/null || true
    } > "${bundle_dir}/system-info.txt" 2>&1

    # Sanitized .env (remove passwords)
    if [[ -f "${INSTALL_DIR}/.env" ]]; then
        sed 's/PASSWORD=.*/PASSWORD=***REDACTED***/g; s/SECRET=.*/SECRET=***REDACTED***/g; s/JWT_SECRET=.*/JWT_SECRET=***REDACTED***/g' \
            "${INSTALL_DIR}/.env" > "${bundle_dir}/env-sanitized.txt" 2>/dev/null || true
    fi

    # Package it
    local bundle_archive="${INSTALL_DIR}/install-debug-bundle.tar.gz"
    tar -czf "${bundle_archive}" -C "$(dirname "${bundle_dir}")" "$(basename "${bundle_dir}")" 2>/dev/null || true
    rm -rf "${bundle_dir}" 2>/dev/null || true

    if [[ -f "${bundle_archive}" ]]; then
        log_info "✓ Debug bundle saved to: ${bundle_archive}"
    else
        log_warn "Could not create debug bundle."
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# FAILURE REPORT & ROLLBACK (Enhanced in v3.0.2)
# ═══════════════════════════════════════════════════════════════════════════════

write_failure_report() {
    local report_file="${INSTALL_DIR}/install-failure-report.txt"
    local server_ip
    server_ip=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")

    mkdir -p "${INSTALL_DIR}" 2>/dev/null || true

    {
        echo "════════════════════════════════════════════════════════════════"
        echo " RHINOMETRIC v${VERSION} — INSTALLATION FAILURE REPORT"
        echo " Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
        echo " Server: $(hostname 2>/dev/null || echo unknown)"
        echo " IP: ${server_ip}"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        echo "CRITICAL FAILURES:"
        local i=1
        for reason in "${FAILURE_REASONS[@]}"; do
            echo "  ${i}. ${reason}"
            i=$((i + 1))
        done
        echo ""
        echo "WARNINGS:"
        for w in "${INSTALL_WARNINGS[@]}"; do
            echo "  - ${w}"
        done
        echo ""
        echo "CONTAINER STATUS AT FAILURE:"
        cd "${INSTALL_DIR}" 2>/dev/null || true
        docker compose ps 2>/dev/null || echo "  (could not retrieve)"
        echo ""
        echo "════════════════════════════════════════════════════════════════"
    } > "${report_file}" 2>/dev/null || true

    if [[ -f "${report_file}" ]]; then
        log_info "Failure report saved to: ${report_file}"
    fi
}

print_failure_report() {
    echo ""
    echo -e "${RED}${BOLD}"
    cat << 'FAILBANNER'
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║               ✗ INSTALLATION FAILED                              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
FAILBANNER
    echo -e "${NC}"

    echo -e "  ${RED}${BOLD}Critical failures:${NC}"
    local i=1
    for reason in "${FAILURE_REASONS[@]}"; do
        echo -e "  ${RED}${i}.${NC} ${reason}"
        i=$((i + 1))
    done
    echo ""

    if [[ ${#INSTALL_WARNINGS[@]} -gt 0 ]]; then
        echo -e "  ${YELLOW}${BOLD}Warnings:${NC}"
        for w in "${INSTALL_WARNINGS[@]}"; do
            echo -e "  ${YELLOW}⚠${NC}  ${w}"
        done
        echo ""
    fi

    echo -e "  ${BOLD}Troubleshooting:${NC}"
    echo "    1. Check container logs : cd ${INSTALL_DIR} && docker compose logs --tail=50"
    echo "    2. Check container state: cd ${INSTALL_DIR} && docker compose ps"
    echo "    3. Check disk space     : df -h ${INSTALL_DIR}"
    echo "    4. Check Docker daemon  : systemctl status docker"
    echo "    5. Retry installation   : sudo bash install-rhinometric.sh"
    echo ""

    if [[ -f "${INSTALL_DIR}/install-debug-bundle.tar.gz" ]]; then
        echo -e "  ${BOLD}Debug bundle:${NC} ${INSTALL_DIR}/install-debug-bundle.tar.gz"
    fi
    if [[ -f "${INSTALL_DIR}/install-failure-report.txt" ]]; then
        echo -e "  ${BOLD}Failure report:${NC} ${INSTALL_DIR}/install-failure-report.txt"
    fi
    echo ""
    echo -e "  ${BOLD}Support:${NC} Contact Rhinometric with the debug bundle and failure report."
    echo ""
}

rollback_on_failure() {
    log_info "Rolling back failed installation..."

    cd "${INSTALL_DIR}" 2>/dev/null || true

    # Stop and remove containers + volumes
    if docker compose ps -q 2>/dev/null | head -1 | grep -q .; then
        log_info "Stopping containers..."
        docker compose down -v --remove-orphans 2>/dev/null || true
    fi

    log_info "Rollback completed. Containers stopped and volumes removed."
    log_info "Config files and reports preserved in ${INSTALL_DIR}/"
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 10 — SAVE CREDENTIALS & SHOW SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

save_credentials() {
    log_step "STEP 8/8 — Installation Summary"

    local server_ip
    server_ip=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")
    local install_date
    install_date=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

    cat > "${CREDENTIALS_FILE}" << CREDEOF
════════════════════════════════════════════════════════════════════════
 RHINOMETRIC v${VERSION} — INSTALLATION CREDENTIALS
 Installed: ${install_date}
 Server:    $(hostname 2>/dev/null || echo "unknown")
 IP:        ${server_ip}
════════════════════════════════════════════════════════════════════════

⚠️  IMPORTANT: Save in a password manager and delete this file.

LICENSE STATUS
  Status      : ${LICENSE_STATUS}
  Plan        : ${LICENSE_PLAN:-N/A}
  Max Hosts   : ${LICENSE_HOSTS:-N/A}
  Expires     : ${LICENSE_EXPIRES:-N/A}
  Customer    : ${LICENSE_CUSTOMER:-N/A}
  Fingerprint : ${MACHINE_FINGERPRINT:-N/A}

RHINOMETRIC CONSOLE (Main Interface)
  URL      : http://${server_ip}:3002
  Username : admin
  Password : ${ADMIN_PASSWORD}

GRAFANA (Dashboards & Visualization)
  URL      : http://${server_ip}:3000
  Username : admin
  Password : ${GRAFANA_PASSWORD}

POSTGRESQL (Database)
  Host     : localhost:5432
  Database : rhinometric
  Username : rhinometric
  Password : ${POSTGRES_PASSWORD}

REDIS (Cache)
  Host     : localhost:6379
  Password : ${REDIS_PASSWORD}

PROMETHEUS (Metrics)
  URL      : http://${server_ip}:9090

ALERTMANAGER (Alerts)
  URL      : http://${server_ip}:9093

JAEGER (Distributed Tracing)
  URL      : http://${server_ip}:16686

════════════════════════════════════════════════════════════════════════
CREDEOF

    chmod 600 "${CREDENTIALS_FILE}"

    # Show summary to terminal
    echo ""
    echo -e "${GREEN}${BOLD}"
    cat << 'DONE'
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║                 ✓ INSTALLATION COMPLETED                         ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
DONE
    echo -e "${NC}"

    echo -e "  ${BOLD}Console${NC}     : ${CYAN}http://${server_ip}:3002${NC}"
    echo -e "  ${BOLD}Grafana${NC}     : ${CYAN}http://${server_ip}:3000${NC}"
    echo -e "  ${BOLD}Prometheus${NC}  : ${CYAN}http://${server_ip}:9090${NC}"
    echo -e "  ${BOLD}Alertmanager${NC}: ${CYAN}http://${server_ip}:9093${NC}"
    echo -e "  ${BOLD}Jaeger${NC}      : ${CYAN}http://${server_ip}:16686${NC}"
    echo ""
    echo -e "  ${BOLD}Admin User${NC}  : admin"
    echo -e "  ${BOLD}Admin Pass${NC}  : ${ADMIN_PASSWORD}"
    echo ""
    echo -e "  ${BOLD}License${NC}     : ${LICENSE_STATUS}"
    if [[ "$LICENSE_STATUS" == "valid" ]]; then
        echo -e "  ${BOLD}Plan${NC}        : ${LICENSE_PLAN} (${LICENSE_HOSTS} hosts)"
        echo -e "  ${BOLD}Expires${NC}     : ${LICENSE_EXPIRES}"
    fi
    echo ""
    echo -e "  Credentials saved to: ${BOLD}${CREDENTIALS_FILE}${NC}"
    echo ""

    if [[ ${#INSTALL_WARNINGS[@]} -gt 0 ]]; then
        echo -e "${YELLOW}${BOLD}  Warnings during installation:${NC}"
        for w in "${INSTALL_WARNINGS[@]}"; do
            echo -e "  ${YELLOW}⚠${NC}  ${w}"
        done
        echo ""
    fi

    echo -e "  ${BOLD}Useful commands:${NC}"
    echo "    Status  : cd ${INSTALL_DIR} && docker compose ps"
    echo "    Logs    : cd ${INSTALL_DIR} && docker compose logs -f [service]"
    echo "    Restart : cd ${INSTALL_DIR} && docker compose restart"
    echo "    Stop    : cd ${INSTALL_DIR} && docker compose down"
    echo "    Uninstall: ${INSTALL_DIR}/uninstall-rhinometric.sh"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

main() {
    parse_args "$@"
    banner
    check_root

    log_info "Starting Rhinometric v${VERSION} installation..."
    log_info "Install directory: ${INSTALL_DIR}"
    echo ""

    # ── System checks ──
    log_step "STEP 0/8 — System Validation"
    check_os
    check_resources
    check_docker
    check_ports
    echo ""

    # ── Abort early if Docker is missing (critical dependency) ──
    if [[ "$INSTALL_CRITICAL_FAILURE" == "true" ]]; then
        print_failure_report
        exit 1
    fi

    # ── Fingerprint detection ──
    detect_fingerprint

    # ── License validation ──
    validate_license

    # ── Confirmation ──
    echo ""
    read -r -p "  Continue with installation? (Y/n): " confirm
    if [[ "$confirm" =~ ^[Nn]$ ]]; then
        log_info "Installation cancelled by user."
        exit 0
    fi

    # ── Setup ──
    log_step "STEP 3/8 — Directory & Credential Setup"
    create_directories
    generate_credentials
    write_env_file
    echo ""

    # ── Copy files ──
    log_step "STEP 4/8 — Copy Configuration Files"
    copy_files
    echo ""

    # ── Abort if copy failed critically ──
    if [[ "$INSTALL_CRITICAL_FAILURE" == "true" ]]; then
        print_failure_report
        exit 1
    fi

    # ── Load pre-built images (if archive exists in package) ──
    log_step "STEP 4b/8 — Load Docker Images"
    load_images
    echo ""

    if [[ "$INSTALL_CRITICAL_FAILURE" == "true" ]]; then
        print_failure_report
        exit 1
    fi

    # ── Verify build contexts exist ──
    verify_build_contexts

    if [[ "$INSTALL_CRITICAL_FAILURE" == "true" ]]; then
        print_failure_report
        exit 1
    fi

    # ── Prepare runtime volume directories (NEW in v3.0.2) ──
    log_step "STEP 5/8 — Prepare Runtime Volumes"
    prepare_runtime_dirs
    echo ""

    # ── Start stack ──
    start_stack
    local stack_exit=$?

    # ── Auto-fix loop if stack failed or unhealthy ──
    if [[ $stack_exit -ne 0 ]]; then
        local fix_attempt=0
        while [[ $fix_attempt -lt $MAX_AUTO_FIX_ATTEMPTS ]]; do
            fix_attempt=$((fix_attempt + 1))
            log_info "Auto-fix attempt ${fix_attempt}/${MAX_AUTO_FIX_ATTEMPTS}..."

            if auto_fix_and_retry; then
                log_info "✓ Auto-fix succeeded on attempt ${fix_attempt}"
                break
            else
                if [[ $fix_attempt -ge $MAX_AUTO_FIX_ATTEMPTS ]]; then
                    fail_critical "Stack failed to start after ${MAX_AUTO_FIX_ATTEMPTS} auto-fix attempts."
                fi
            fi
        done
    fi

    # ── Abort if stack completely failed ──
    if [[ "$INSTALL_CRITICAL_FAILURE" == "true" ]]; then
        generate_debug_bundle
        write_failure_report
        rollback_on_failure
        print_failure_report
        exit 1
    fi

    # ── Health check ──
    health_check
    local health_exit=$?

    # ── If health check found fixable issues, try one more auto-fix round ──
    if [[ $health_exit -ne 0 && "$INSTALL_CRITICAL_FAILURE" != "true" ]]; then
        log_info "Health check found issues. Attempting one more auto-fix cycle..."
        if auto_fix_and_retry; then
            # Re-run health check
            INSTALL_CRITICAL_FAILURE=false
            FAILURE_REASONS=()
            health_check
        fi
    fi

    # ════════════════════════════════════════════════════════════════════════
    # FINAL DECISION: SUCCESS or FAILURE
    # ════════════════════════════════════════════════════════════════════════
    if [[ "$INSTALL_CRITICAL_FAILURE" == "true" ]]; then
        generate_debug_bundle
        write_failure_report
        rollback_on_failure
        print_failure_report
        exit 1
    fi

    # ── All good — save credentials and show success ──
    save_credentials
    log_info "Installation completed. Rhinometric v${VERSION} is ready."
    exit 0
}

# ── Entry point ──
main "$@"
