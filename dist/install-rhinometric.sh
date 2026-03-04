#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# RHINOMETRIC v3.0.1 — PRODUCTION INSTALLER
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
# ═══════════════════════════════════════════════════════════════════════════════

# ── Do NOT use set -e — we handle every error explicitly ──────────────────────

# ─── Constants ────────────────────────────────────────────────────────────────
readonly VERSION="3.0.1"
readonly INSTALL_DIR="${INSTALL_DIR:-/opt/rhinometric}"
readonly COMPOSE_FILE="docker-compose.yml"
readonly CREDENTIALS_FILE="${INSTALL_DIR}/install-info.txt"
readonly LICENSE_DEST="${INSTALL_DIR}/license.key"
readonly RHINO_LIC_BIN="/usr/local/bin/rhino-lic"
readonly MIN_RAM_GB=8
readonly MIN_CPU_CORES=4
readonly REQUIRED_SPACE_GB=150
readonly HEALTH_URL="http://127.0.0.1:3002"
readonly HEALTH_RETRIES=20
readonly HEALTH_DELAY=10
readonly PULL_RETRIES=3
readonly PULL_DELAY=10

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

# ─── Critical failure tracking ────────────────────────────────────
INSTALL_CRITICAL_FAILURE=false
FAILURE_REASONS=()

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

log_info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; INSTALL_WARNINGS+=("$1"); }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Mark a critical (non-recoverable) failure ─────────────────────────────────
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
║          Enterprise Observability Platform v3.0.1                ║
║                   Production Installer                           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
BANNER
    echo -e "${NC}"
}

generate_password() {
    # Try openssl first, fallback to /dev/urandom
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

    # CPU
    local cpu_cores
    cpu_cores=$(nproc 2>/dev/null || echo 0)
    if [[ "$cpu_cores" -ge "$MIN_CPU_CORES" ]]; then
        log_info "✓ CPU: ${cpu_cores} cores (minimum ${MIN_CPU_CORES})"
    else
        log_warn "CPU: ${cpu_cores} cores detected (recommended: ${MIN_CPU_CORES}+)"
    fi

    # RAM
    local total_ram_gb
    total_ram_gb=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}' || echo 0)
    if [[ "$total_ram_gb" -ge "$MIN_RAM_GB" ]]; then
        log_info "✓ RAM: ${total_ram_gb} GB (minimum ${MIN_RAM_GB} GB)"
    else
        log_warn "RAM: ${total_ram_gb} GB detected (recommended: ${MIN_RAM_GB} GB). Installation continues."
    fi

    # Disk
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
    log_step "STEP 1/7 — Machine Fingerprint Detection"

    # Ensure rhino-lic is available
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
    log_step "STEP 2/7 — License Validation"

    # Check if license.key is already in the script directory
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

    # No license provided — continue unlicensed
    if [[ -z "$license_path" ]]; then
        LICENSE_STATUS="unlicensed"
        echo ""
        log_warn "No license provided. Platform will start in unlicensed mode."
        log_info "You can add a license later by placing license.key in ${INSTALL_DIR}/"
        return 0
    fi

    # Provided but file doesn't exist
    if [[ ! -f "$license_path" ]]; then
        log_warn "License file not found: ${license_path}. Continuing in unlicensed mode."
        LICENSE_STATUS="unlicensed"
        return 0
    fi

    # Copy license to install dir
    mkdir -p "${INSTALL_DIR}" 2>/dev/null || true
    cp "$license_path" "${LICENSE_DEST}" 2>/dev/null || true

    # Validate with rhino-lic
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
            # Parse JSON output
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

    # Already installed
    if command -v rhino-lic &>/dev/null; then
        log_info "✓ rhino-lic already installed at $(command -v rhino-lic)"
        return 0
    fi

    # Check if binary is in the installer package
    if [[ -f "${script_dir}/rhino-lic" ]]; then
        log_info "Installing rhino-lic from package..."
        cp "${script_dir}/rhino-lic" "${RHINO_LIC_BIN}"
        chmod 755 "${RHINO_LIC_BIN}"
        if command -v rhino-lic &>/dev/null; then
            log_info "✓ rhino-lic installed to ${RHINO_LIC_BIN}"
            return 0
        fi
    fi

    # Check if it exists at install dir
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
        "${INSTALL_DIR}/config/rules"
        "${INSTALL_DIR}/grafana/provisioning/dashboards/json"
        "${INSTALL_DIR}/grafana/provisioning/dashboards/json-clean"
        "${INSTALL_DIR}/grafana/provisioning/datasources"
        "${INSTALL_DIR}/grafana/provisioning/plugins"
        "${INSTALL_DIR}/prometheus"
        "${INSTALL_DIR}/alertmanager/templates"
        "${INSTALL_DIR}/nginx"
        "${INSTALL_DIR}/blackbox"
        "${INSTALL_DIR}/init-db"
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

    # ── Copy all configuration directories from package ───────────────────────
    # These are required by docker-compose.yml volume mounts.
    local config_dirs=("config" "alertmanager" "grafana" "nginx" "blackbox" "init-db" "prometheus" "loki")
    for dir in "${config_dirs[@]}"; do
        if [[ -d "${script_dir}/${dir}" ]]; then
            cp -a "${script_dir}/${dir}/." "${INSTALL_DIR}/${dir}/" 2>/dev/null || true
            log_info "✓ ${dir}/ copied"
        fi
    done

    # ── Copy build context directories for locally-built services ─────────────
    # These directories contain Dockerfiles and source code that docker compose
    # builds at startup. They MUST exist at ${INSTALL_DIR} for compose to work.
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
    log_step "STEP 5/7 — Starting Docker Stack"

    cd "${INSTALL_DIR}" || {
        log_error "Cannot access ${INSTALL_DIR}"
        return 1
    }

    if [[ ! -f "docker-compose.yml" ]]; then
        log_error "docker-compose.yml not found in ${INSTALL_DIR}"
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
        fail_critical "docker compose up failed (exit code ${compose_exit})"
        echo ""
        log_error "Docker Compose output:"
        echo "$compose_output" | tail -30
        echo ""
        log_error "Container statuses:"
        docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || true
        return 1
    fi

    log_info "✓ Docker Compose started"

    # Verify at least some containers came up
    sleep 10
    local running_count
    running_count=$(docker compose ps --status running -q 2>/dev/null | wc -l || echo 0)
    if [[ "$running_count" -eq 0 ]]; then
        fail_critical "docker compose up succeeded but 0 containers are running."
        docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || true
        return 1
    fi

    log_info "Containers starting: ${running_count} running so far"

    # Wait for initialization
    log_info "Waiting for services to initialize (30s)..."
    sleep 30
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 9 — HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════

health_check() {
    log_step "STEP 6/7 — Health Verification"

    # Check container count
    cd "${INSTALL_DIR}" || return 1

    local total running healthy
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

    # Health check with retries
    log_info "Checking platform health (Console + Grafana)..."
    log_info "Timeout: $((HEALTH_RETRIES * HEALTH_DELAY))s (${HEALTH_RETRIES} attempts x ${HEALTH_DELAY}s)"
    local n=0
    local console_ok=false
    local grafana_ok=false
    while [ "$n" -lt "$HEALTH_RETRIES" ]; do
        if ! $console_ok && curl -fsS "http://127.0.0.1:3002" >/dev/null 2>&1; then
            console_ok=true
            log_info "✓ Console (port 3002) is responding"
        fi
        if ! $grafana_ok && curl -fsS "http://127.0.0.1:3000/api/health" >/dev/null 2>&1; then
            grafana_ok=true
            log_info "✓ Grafana (port 3000) is responding"
        fi
        if $console_ok && $grafana_ok; then
            log_info "✓ Platform is healthy"
            return 0
        fi
        n=$((n + 1))
        if [ "$n" -lt "$HEALTH_RETRIES" ]; then
            log_info "  Waiting for services... (${n}/${HEALTH_RETRIES})"
            sleep "$HEALTH_DELAY"
        fi
    done

    if $console_ok || $grafana_ok; then
        log_warn "Partial health: Console=$console_ok Grafana=$grafana_ok"
    else
        log_warn "Health check did not pass after ${HEALTH_RETRIES} attempts."
    fi
    log_warn "The platform may still be starting. Check: docker compose logs -f"

    # List container statuses as diagnostic
    echo ""
    log_info "Current container statuses:"
    docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || true
    echo ""

    return 1
}

# ═══════════════════════════════════════════════════════════════════════════════
# FAILURE REPORT
# ═══════════════════════════════════════════════════════════════════════════════

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
    echo "    1. Check container logs : cd ${INSTALL_DIR} ; docker compose logs --tail=50"
    echo "    2. Check container state: cd ${INSTALL_DIR} ; docker compose ps"
    echo "    3. Check disk space     : df -h ${INSTALL_DIR}"
    echo "    4. Check Docker daemon  : systemctl status docker"
    echo "    5. Retry installation   : sudo bash install-rhinometric.sh"
    echo ""
    echo -e "  ${BOLD}Support:${NC} Contact Rhinometric with the output above."
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 10 — SAVE CREDENTIALS & SHOW SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

save_credentials() {
    log_step "STEP 7/7 — Installation Summary"

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

    # Show warnings summary if any
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
    banner
    check_root

    log_info "Starting Rhinometric v${VERSION} installation..."
    log_info "Install directory: ${INSTALL_DIR}"
    echo ""

    # ── System checks ──
    log_step "STEP 0/7 — System Validation"
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
    log_step "STEP 3/7 — Directory & Credential Setup"
    create_directories
    generate_credentials
    write_env_file
    echo ""

    # ── Copy files ──
    log_step "STEP 4/7 — Copy Configuration Files"
    copy_files
    echo ""

    # ── Abort if copy failed critically ──
    if [[ "$INSTALL_CRITICAL_FAILURE" == "true" ]]; then
        print_failure_report
        exit 1
    fi

    # ── Load pre-built images (if archive exists in package) ──
    log_step "STEP 4b/7 — Load Docker Images"
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

    # ── Start stack ──
    start_stack

    # ── Health check (only if stack started) ──
    if [[ "$INSTALL_CRITICAL_FAILURE" != "true" ]]; then
        health_check
    fi

    # ══════════════════════════════════════════════════════════════════════════
    # FINAL DECISION: SUCCESS or FAILURE
    # ══════════════════════════════════════════════════════════════════════════
    if [[ "$INSTALL_CRITICAL_FAILURE" == "true" ]]; then
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
