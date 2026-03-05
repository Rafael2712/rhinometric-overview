#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# RHINOMETRIC v3.0.3 — PRODUCTION INSTALLER
# Integrates Ed25519 license validation via rhino-lic
# Date: 2026-03-05
# Requires: Ubuntu 20.04+, Docker 24.x+, Docker Compose v2
#
# IMPORTANT: This installer NEVER aborts due to license issues.
#            The platform always starts. License status is informational.
#
# EXIT CODES:
#   0 — Installation completed, platform healthy
#   1 — Critical failure (docker compose failed, health check failed, etc.)
#
# v3.0.3 CHANGES (from v3.0.2):
#   - FIX: /etc/os-release sourcing no longer clashes with readonly VERSION
#   - FIX: Disk check prints actual GB (was empty), checks Docker data-root too
#   - FIX: Endpoint checks are dynamic — reads published ports from compose
#          instead of hardcoding 3002/3000/9090
#   - FIX: Rollback NO LONGER destroys the stack by default; add
#          --rollback-on-failure to opt-in
#   - FIX: VictoriaMetrics unhealthy triggers root-cause diagnosis (OOM, disk,
#          slow start) instead of hard failing
#   - FIX: Correct runtime-dirs-created counter
#   - NEW: Enhanced debug bundle (docker info, system df, journalctl, per-svc)
#   - NEW: .env includes sane SMTP/MAIL defaults to suppress compose warnings
#   - NEW: Strips obsolete compose `version:` field at copy time
# ═══════════════════════════════════════════════════════════════════════════════

# ── Do NOT use set -e — we handle every error explicitly ──────────────────────

# ─── Constants ────────────────────────────────────────────────────────────────
readonly INSTALLER_VERSION="3.0.3"
readonly INSTALL_DIR="${INSTALL_DIR:-/opt/rhinometric}"
readonly COMPOSE_FILE="docker-compose.yml"
readonly CREDENTIALS_FILE="${INSTALL_DIR}/install-info.txt"
readonly LICENSE_DEST="${INSTALL_DIR}/license.key"
readonly RHINO_LIC_BIN="/usr/local/bin/rhino-lic"
readonly MIN_RAM_GB=8
readonly MIN_CPU_CORES=4
readonly REQUIRED_SPACE_GB=20
readonly HEALTH_RETRIES=40
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
ROLLBACK_ON_FAILURE=false
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
║          Enterprise Observability Platform v3.0.3                ║
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
                ;;
            --rollback-on-failure)
                ROLLBACK_ON_FAILURE=true
                log_info "Rollback on failure enabled"
                ;;
            *)
                ;;
        esac
        shift
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
        exit 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — SYSTEM CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

check_os() {
    log_info "Checking operating system..."
    if [[ -f /etc/os-release ]]; then
        # Parse safely — do NOT source the file (VERSION is a readonly in this
        # script and /etc/os-release also defines VERSION, causing a conflict).
        local os_id os_version os_pretty
        os_id=$(grep -oP '^ID=\K.*' /etc/os-release 2>/dev/null | tr -d '"' || echo "unknown")
        os_version=$(grep -oP '^VERSION_ID=\K.*' /etc/os-release 2>/dev/null | tr -d '"' || echo "")
        os_pretty=$(grep -oP '^PRETTY_NAME=\K.*' /etc/os-release 2>/dev/null | tr -d '"' || echo "unknown")
        if [[ "$os_id" == "ubuntu" ]]; then
            log_info "✓ Ubuntu ${os_version} detected"
        else
            log_warn "OS: ${os_pretty} — Ubuntu 22.04+ recommended"
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

    # Disk: check INSTALL_DIR partition
    check_disk_space "${INSTALL_DIR}" "install-dir"

    # Disk: check Docker data-root partition
    local docker_root
    docker_root=$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || echo "/var/lib/docker")
    if [[ "$docker_root" != "$(df "${INSTALL_DIR}" 2>/dev/null | awk 'NR==2{print $6}')" ]]; then
        check_disk_space "$docker_root" "docker-root"
    fi
}

check_disk_space() {
    local path="$1"
    local label="$2"

    # Ensure parent exists for df
    local check_path="$path"
    while [[ ! -d "$check_path" && "$check_path" != "/" ]]; do
        check_path=$(dirname "$check_path")
    done

    local avail_kb avail_gb total_kb used_pct
    avail_kb=$(df -k "$check_path" 2>/dev/null | awk 'NR==2{print $4}')
    total_kb=$(df -k "$check_path" 2>/dev/null | awk 'NR==2{print $2}')
    used_pct=$(df -k "$check_path" 2>/dev/null | awk 'NR==2{print $5}')

    if [[ -z "$avail_kb" || "$avail_kb" == "0" ]]; then
        fail_critical "Disk check failed for ${path} (${label}): could not determine available space. df output: $(df -h "$check_path" 2>&1 | head -3)"
        return 1
    fi

    avail_gb=$((avail_kb / 1048576))

    if [[ "$avail_gb" -ge "$REQUIRED_SPACE_GB" ]]; then
        log_info "✓ Disk (${label}): ${avail_gb} GB available (${used_pct} used) at ${check_path}"
    else
        log_warn "Disk (${label}): ${avail_gb} GB available (${used_pct} used) at ${check_path} — minimum ${REQUIRED_SPACE_GB} GB recommended"
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

    local required_ports=(80 3000 3002 5432 6379 8105 9090 9093 3100 16686)
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
        1)  LICENSE_STATUS="invalid_signature"
            log_warn "License signature is INVALID. The platform will start but licensing will be limited." ;;
        2)  LICENSE_STATUS="expired"
            log_warn "License has EXPIRED. The platform will start but licensing will be limited." ;;
        3)  LICENSE_STATUS="fingerprint_mismatch"
            log_warn "License FINGERPRINT MISMATCH (expected: ${MACHINE_FINGERPRINT}). Platform will start." ;;
        4)  LICENSE_STATUS="parse_error"
            log_warn "License file could not be parsed. Platform will start." ;;
        *)  LICENSE_STATUS="unknown_error"
            log_warn "License validation returned unexpected code: ${exit_code}. Platform will start." ;;
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

    log_warn "rhino-lic binary not found. Fingerprint/license validation skipped."
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
# RHINOMETRIC v${INSTALLER_VERSION} — Auto-generated $(date -u +"%Y-%m-%d %H:%M:%S UTC")
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
API_VERSION=${INSTALLER_VERSION}

# === License ===
LICENSE_STATUS=${LICENSE_STATUS}

# === SMTP / Mail (set real values to enable email features) ===
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=changeme
MAIL_USERNAME=noreply@example.com
MAIL_PASSWORD=changeme
MAIL_FROM=noreply@example.com
ENVEOF

    chmod 600 "${INSTALL_DIR}/.env"
    log_info "✓ Environment file created"
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6b — PREPARE RUNTIME VOLUME DIRECTORIES
# ═══════════════════════════════════════════════════════════════════════════════

prepare_runtime_dirs() {
    log_info "Preparing runtime volume directories..."

    DATA_ROOT="${HOME}/rhinometric_data_v2.5"
    export HOME

    log_info "Data root: ${DATA_ROOT}"

    local all_dirs=(
        "${DATA_ROOT}/jaeger"
        "${DATA_ROOT}/jaeger/key"
        "${DATA_ROOT}/jaeger/data"
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
            mkdir -p "$dir" 2>/dev/null || true
            created=$((created + 1))
        fi
    done

    log_info "Created ${created} of ${#all_dirs[@]} runtime directories (rest already existed)"

    # ── Jaeger (UID 10001, GID 0) ──
    chown -R 10001:0 "${DATA_ROOT}/jaeger" 2>/dev/null || true
    chmod -R 755 "${DATA_ROOT}/jaeger" 2>/dev/null || true
    log_info "✓ Jaeger: ${DATA_ROOT}/jaeger (uid=10001, badger subdirs ensured)"

    # ── Alertmanager (UID 65534 = nobody) ──
    chown -R 65534:65534 "${DATA_ROOT}/alertmanager" 2>/dev/null || true
    chmod -R 755 "${DATA_ROOT}/alertmanager" 2>/dev/null || true
    log_info "✓ Alertmanager: ${DATA_ROOT}/alertmanager (uid=65534)"

    # ── PostgreSQL (UID 999) ──
    chown -R 999:999 "${DATA_ROOT}/postgres" 2>/dev/null || true
    chmod -R 700 "${DATA_ROOT}/postgres" 2>/dev/null || true
    log_info "✓ PostgreSQL: ${DATA_ROOT}/postgres (uid=999)"

    # ── Redis (UID 999) ──
    chown -R 999:999 "${DATA_ROOT}/redis" 2>/dev/null || true
    chmod -R 755 "${DATA_ROOT}/redis" 2>/dev/null || true
    log_info "✓ Redis: ${DATA_ROOT}/redis (uid=999)"

    # ── Loki (root; user: '0' in compose) ──
    chmod -R 755 "${DATA_ROOT}/loki" 2>/dev/null || true
    log_info "✓ Loki: ${DATA_ROOT}/loki (root)"

    # ── General dirs ──
    for dir in "${DATA_ROOT}/ai-anomaly" "${DATA_ROOT}/console-backend" "${DATA_ROOT}/license-server"; do
        chmod -R 777 "$dir" 2>/dev/null || true
    done
    log_info "✓ General: ai-anomaly, console-backend, license-server (world-writable)"

    log_info "✓ All ${#all_dirs[@]} runtime volume directories prepared"
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7 — COPY FILES
# ═══════════════════════════════════════════════════════════════════════════════

copy_files() {
    log_info "Copying configuration files..."

    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Copy docker-compose.yml and strip obsolete 'version:' field
    if [[ -f "${script_dir}/${COMPOSE_FILE}" ]]; then
        sed '/^version:/d' "${script_dir}/${COMPOSE_FILE}" > "${INSTALL_DIR}/docker-compose.yml"
        log_info "✓ Docker Compose file copied (obsolete 'version:' field stripped)"
    elif [[ -f "${INSTALL_DIR}/docker-compose.yml" ]]; then
        # Strip version from existing copy too
        sed -i '/^version:/d' "${INSTALL_DIR}/docker-compose.yml" 2>/dev/null || true
        log_info "✓ Docker Compose file already exists (cleaned)"
    else
        fail_critical "docker-compose.yml not found in package or ${INSTALL_DIR}. Cannot proceed."
        return 1
    fi

    # Copy rhino-lic
    if [[ -f "${script_dir}/rhino-lic" ]]; then
        cp "${script_dir}/rhino-lic" "${INSTALL_DIR}/rhino-lic"
        chmod 755 "${INSTALL_DIR}/rhino-lic"
    fi

    # Copy uninstall script
    if [[ -f "${script_dir}/uninstall-rhinometric.sh" ]]; then
        cp "${script_dir}/uninstall-rhinometric.sh" "${INSTALL_DIR}/uninstall-rhinometric.sh"
        chmod 755 "${INSTALL_DIR}/uninstall-rhinometric.sh"
        log_info "✓ Uninstall script copied"
    fi

    # Copy config directories
    local config_dirs=("config" "alertmanager" "grafana" "nginx" "blackbox" "init-db" "prometheus" "loki")
    for dir in "${config_dirs[@]}"; do
        if [[ -d "${script_dir}/${dir}" ]]; then
            mkdir -p "${INSTALL_DIR}/${dir}" 2>/dev/null || true
            cp -a "${script_dir}/${dir}/." "${INSTALL_DIR}/${dir}/" 2>/dev/null || true
            log_info "✓ ${dir}/ copied"
        fi
    done

    # Copy build context directories
    local build_dirs=("rhinometric-ai-anomaly" "rhinometric-console" "license-server-v2" "license-management-ui")
    for dir in "${build_dirs[@]}"; do
        if [[ -d "${script_dir}/${dir}" ]]; then
            mkdir -p "${INSTALL_DIR}/${dir}" 2>/dev/null || true
            cp -a "${script_dir}/${dir}/." "${INSTALL_DIR}/${dir}/" 2>/dev/null || true
            log_info "✓ ${dir}/ copied (build context)"
        fi
    done

    # Verify critical file
    if [[ ! -f "${INSTALL_DIR}/docker-compose.yml" ]]; then
        fail_critical "docker-compose.yml missing in ${INSTALL_DIR} after copy step."
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# LOAD PRE-BUILT IMAGES
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
        log_info "✓ Docker images loaded (${loaded_count} images)"
    else
        fail_critical "Failed to load Docker images from ${images_file}."
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# VERIFY BUILD CONTEXTS
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
            log_warn "Build contexts missing but matching Docker images found locally."
        else
            fail_critical "Build context directories missing and no pre-built images found."
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

    # Validate compose config (suppress env-var warnings — they go to stderr)
    log_info "Validating Docker Compose configuration..."
    local config_exit
    docker compose config -q 2>/dev/null
    config_exit=$?
    if [[ $config_exit -ne 0 ]]; then
        local config_err
        config_err=$(docker compose config 2>&1 | grep -i "error" | head -5)
        fail_critical "Docker Compose config invalid: ${config_err}"
        return 1
    fi
    log_info "✓ Compose configuration valid"

    # Pull public images (ignore buildable, suppress repeated env warnings)
    log_info "Pulling Docker images (this may take several minutes)..."
    docker compose pull --ignore-buildable 2>/dev/null || true

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

    # Start stack (suppress env-var warnings)
    log_info "Starting services with docker compose up -d..."
    local compose_output
    compose_output=$(docker compose up -d 2>&1)
    local compose_exit=$?

    if [[ $compose_exit -ne 0 ]]; then
        log_error "docker compose up failed (exit ${compose_exit}). Will attempt auto-fix..."
        echo "$compose_output" | grep -v "WARN\[" | tail -20
        return 1
    fi

    log_info "✓ Docker Compose started"

    # Initial stabilization wait
    sleep 10
    local running_count
    running_count=$(docker compose ps --status running -q 2>/dev/null | wc -l || echo 0)
    if [[ "$running_count" -eq 0 ]]; then
        log_error "docker compose up succeeded but 0 containers are running."
        docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || true
        return 1
    fi

    log_info "Containers starting: ${running_count} running so far"
    log_info "Waiting for services to initialize (30s)..."
    sleep 30
    return 0
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 9 — FULL STACK HEALTH CHECK (v3.0.3: dynamic endpoint detection)
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
        docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || true
        docker compose logs --tail=20 2>/dev/null | tail -40 || true
        return 1
    fi

    # ── Phase 1: Wait for critical infrastructure (postgres, redis) ──
    log_info "Phase 1: Waiting for infrastructure services..."
    local infra_ok=true
    local n=0
    while [ "$n" -lt 12 ]; do
        local pg_ok=false redis_ok=false
        local pg_status redis_status
        pg_status=$(docker inspect --format '{{.State.Health.Status}}' rhinometric-postgres 2>/dev/null || echo "not_found")
        redis_status=$(docker inspect --format '{{.State.Health.Status}}' rhinometric-redis 2>/dev/null || echo "not_found")
        [[ "$pg_status" == "healthy" ]] && pg_ok=true
        [[ "$redis_status" == "healthy" ]] && redis_ok=true

        if $pg_ok && $redis_ok; then
            log_info "✓ PostgreSQL: healthy"
            log_info "✓ Redis: healthy"
            break
        fi
        n=$((n + 1))
        if [[ "$n" -ge 12 ]]; then
            $pg_ok || { log_warn "PostgreSQL not healthy after 120s (${pg_status})"; infra_ok=false; }
            $redis_ok || { log_warn "Redis not healthy after 120s (${redis_status})"; infra_ok=false; }
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
    log_info "Timeout: $((HEALTH_RETRIES * HEALTH_DELAY))s (${HEALTH_RETRIES} x ${HEALTH_DELAY}s)"

    # Services classified by criticality
    local critical_services=(
        "rhinometric-postgres"
        "rhinometric-redis"
        "rhinometric-console-backend"
        "rhinometric-console-frontend"
        "rhinometric-nginx"
        "rhinometric-grafana"
    )
    local important_services=(
        "rhinometric-license-server-v2"
        "rhinometric-prometheus"
        "rhinometric-loki"
        "rhinometric-otel-collector"
        "rhinometric-alertmanager"
        "rhinometric-cadvisor"
    )
    local optional_services=(
        "rhinometric-victoria-metrics"
        "rhinometric-ai-anomaly"
    )

    if ! $SKIP_JAEGER; then
        important_services+=("rhinometric-jaeger")
    fi

    local all_services=("${critical_services[@]}" "${important_services[@]}" "${optional_services[@]}")

    n=0
    local all_healthy=false
    while [ "$n" -lt "$HEALTH_RETRIES" ]; do
        local unhealthy_list=()

        for svc in "${all_services[@]}"; do
            local svc_health svc_state
            svc_health=$(docker inspect --format '{{.State.Health.Status}}' "$svc" 2>/dev/null || echo "no_healthcheck")
            svc_state=$(docker inspect --format '{{.State.Status}}' "$svc" 2>/dev/null || echo "not_found")

            if [[ "$svc_health" == "healthy" ]]; then
                continue
            elif [[ "$svc_health" == "no_healthcheck" && "$svc_state" == "running" ]]; then
                continue
            else
                unhealthy_list+=("${svc}=${svc_health}/${svc_state}")
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
        log_info "✓ All ${#all_services[@]} monitored services are healthy"
    else
        # Classify what's still unhealthy
        local crit_fail=() important_fail=() optional_fail=()

        for svc in "${critical_services[@]}"; do
            local h s
            h=$(docker inspect --format '{{.State.Health.Status}}' "$svc" 2>/dev/null || echo "unknown")
            s=$(docker inspect --format '{{.State.Status}}' "$svc" 2>/dev/null || echo "unknown")
            if [[ "$h" != "healthy" && "$s" != "running" ]]; then
                crit_fail+=("${svc} (state=${s}, health=${h})")
            elif [[ "$h" == "unhealthy" ]]; then
                crit_fail+=("${svc} (running but unhealthy)")
            fi
        done

        for svc in "${important_services[@]}"; do
            local h s
            h=$(docker inspect --format '{{.State.Health.Status}}' "$svc" 2>/dev/null || echo "unknown")
            s=$(docker inspect --format '{{.State.Status}}' "$svc" 2>/dev/null || echo "unknown")
            if [[ "$h" != "healthy" && "$s" != "running" ]]; then
                important_fail+=("${svc} (state=${s}, health=${h})")
            elif [[ "$h" == "unhealthy" ]]; then
                important_fail+=("${svc} (running but unhealthy)")
            fi
        done

        for svc in "${optional_services[@]}"; do
            local h s
            h=$(docker inspect --format '{{.State.Health.Status}}' "$svc" 2>/dev/null || echo "unknown")
            s=$(docker inspect --format '{{.State.Status}}' "$svc" 2>/dev/null || echo "unknown")
            if [[ "$h" != "healthy" ]]; then
                optional_fail+=("${svc} (state=${s}, health=${h})")
                # Run root-cause diagnosis for optional unhealthy services
                diagnose_unhealthy_service "$svc"
            fi
        done

        if [[ ${#crit_fail[@]} -gt 0 ]]; then
            log_error "Critical services not healthy:"
            for item in "${crit_fail[@]}"; do
                log_error "  ✗ ${item}"
            done
        fi
        if [[ ${#important_fail[@]} -gt 0 ]]; then
            log_warn "Important services not healthy (may still be starting):"
            for item in "${important_fail[@]}"; do
                log_warn "  ⚠ ${item}"
            done
        fi
        if [[ ${#optional_fail[@]} -gt 0 ]]; then
            log_warn "Optional services not healthy (non-blocking):"
            for item in "${optional_fail[@]}"; do
                log_warn "  ⚠ ${item}"
            done
        fi

        # Only fail on critical services that are actually down (not running)
        for svc in "${critical_services[@]}"; do
            local s
            s=$(docker inspect --format '{{.State.Status}}' "$svc" 2>/dev/null || echo "unknown")
            if [[ "$s" != "running" ]]; then
                fail_critical "Critical service ${svc} is NOT running (state=${s})"
            fi
        done
    fi

    # ── Phase 3: Dynamic HTTP endpoint checks ──
    log_info "Phase 3: Verifying HTTP endpoints (dynamic port detection)..."
    verify_http_endpoints

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
# DYNAMIC HTTP ENDPOINT VERIFICATION (NEW in v3.0.3)
# ═══════════════════════════════════════════════════════════════════════════════
# Instead of hardcoding ports, we discover published host ports from compose
# and verify only those endpoints that are actually exposed.
# ═══════════════════════════════════════════════════════════════════════════════

verify_http_endpoints() {
    cd "${INSTALL_DIR}" || return 1

    # Discover published ports via docker compose port
    # Returns HOST:PORT or empty if not published
    local nginx_hp console_hp grafana_hp prom_hp
    nginx_hp=$(docker compose port nginx 80 2>/dev/null || echo "")
    console_hp=$(docker compose port rhinometric-console-frontend 3002 2>/dev/null || echo "")
    grafana_hp=$(docker compose port grafana 3000 2>/dev/null || echo "")
    prom_hp=$(docker compose port prometheus 9090 2>/dev/null || echo "")

    # Build list of endpoints to check
    local -a endpoints=()  # "label|url"

    if [[ -n "$nginx_hp" ]]; then
        endpoints+=("Nginx (front door)|http://${nginx_hp}")
    fi
    if [[ -n "$console_hp" ]]; then
        endpoints+=("Console|http://${console_hp}")
    fi
    if [[ -n "$grafana_hp" ]]; then
        endpoints+=("Grafana|http://${grafana_hp}/api/health")
    fi
    if [[ -n "$prom_hp" ]]; then
        endpoints+=("Prometheus|http://${prom_hp}/-/ready")
    fi

    # If nginx is published, also check through nginx (it proxies console)
    if [[ -n "$nginx_hp" && -z "$console_hp" ]]; then
        # Console port is NOT directly published — nginx is the gateway
        log_info "Note: Console port (3002) is not published to host; nginx (${nginx_hp}) is the front door."
    fi

    if [[ ${#endpoints[@]} -eq 0 ]]; then
        log_warn "No published HTTP ports detected. Skipping HTTP endpoint checks."
        log_warn "Services may only be reachable via Docker internal network."
        return 0
    fi

    log_info "Checking ${#endpoints[@]} published endpoint(s)..."

    local http_attempts=0
    local -A ep_ok=()

    while [ "$http_attempts" -lt 8 ]; do
        local all_ok=true
        for ep in "${endpoints[@]}"; do
            local label="${ep%%|*}"
            local url="${ep##*|}"
            if [[ "${ep_ok[$label]:-}" == "1" ]]; then
                continue
            fi
            if curl -fsSL --max-time 5 "$url" >/dev/null 2>&1; then
                ep_ok["$label"]="1"
                log_info "✓ ${label}: responding (${url})"
            else
                all_ok=false
            fi
        done
        if $all_ok; then break; fi
        http_attempts=$((http_attempts + 1))
        if [[ $http_attempts -lt 8 ]]; then sleep 10; fi
    done

    # Report failures
    local any_critical_fail=false
    for ep in "${endpoints[@]}"; do
        local label="${ep%%|*}"
        local url="${ep##*|}"
        if [[ "${ep_ok[$label]:-}" != "1" ]]; then
            if [[ "$label" == *"Nginx"* || "$label" == *"Console"* ]]; then
                fail_critical "${label} (${url}) not responding after 80s"
                any_critical_fail=true
            else
                log_warn "${label} (${url}) not responding — non-blocking"
            fi
        fi
    done

    if ! $any_critical_fail; then
        log_info "✓ All published endpoints are responding"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE DIAGNOSIS (NEW in v3.0.3)
# ═══════════════════════════════════════════════════════════════════════════════
# When a service is unhealthy, try to determine WHY automatically.
# ═══════════════════════════════════════════════════════════════════════════════

diagnose_unhealthy_service() {
    local container="$1"
    local short_name="${container#rhinometric-}"

    log_info "  Diagnosing ${short_name}..."

    # 1. Check OOM killed
    local oom_killed
    oom_killed=$(docker inspect --format '{{.State.OOMKilled}}' "$container" 2>/dev/null || echo "false")
    if [[ "$oom_killed" == "true" ]]; then
        log_error "  → ${short_name}: OOM killed! Container ran out of memory."
        log_error "  → Fix: increase VM RAM or reduce -memory.allowedPercent in compose."
        return
    fi

    # 2. Check exit code (if not running)
    local state exit_code
    state=$(docker inspect --format '{{.State.Status}}' "$container" 2>/dev/null || echo "unknown")
    exit_code=$(docker inspect --format '{{.State.ExitCode}}' "$container" 2>/dev/null || echo "-1")
    if [[ "$state" != "running" && "$exit_code" != "0" ]]; then
        log_warn "  → ${short_name}: exited with code ${exit_code}"
    fi

    # 3. Health check log (last 3 entries)
    local health_log
    health_log=$(docker inspect --format '{{range .State.Health.Log}}{{.Output}}{{end}}' "$container" 2>/dev/null || echo "")
    if [[ -n "$health_log" ]]; then
        log_info "  → Health check output (last): $(echo "$health_log" | tail -c 300)"
    fi

    # 4. Check dmesg for OOM near this container
    local dmesg_oom
    dmesg_oom=$(dmesg 2>/dev/null | tail -100 | grep -i "oom\|killed process" | grep -i "${short_name}\|docker" | tail -3 || true)
    if [[ -n "$dmesg_oom" ]]; then
        log_error "  → Kernel OOM evidence: ${dmesg_oom}"
    fi

    # 5. Disk space check
    local disk_avail
    disk_avail=$(df -BG "${INSTALL_DIR}" 2>/dev/null | awk 'NR==2{print $4}' | tr -d 'G' || echo 0)
    if [[ "$disk_avail" -lt 2 ]]; then
        log_error "  → ${short_name}: disk space critically low (${disk_avail} GB free)"
    fi

    # 6. Last 5 logs
    log_info "  → Recent logs:"
    docker logs --tail=5 "$container" 2>&1 | sed 's/^/    /' || true
}

# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-FIX & RETRY
# ═══════════════════════════════════════════════════════════════════════════════

auto_fix_and_retry() {
    log_step "Auto-Fix: Detecting and fixing common issues..."

    cd "${INSTALL_DIR}" || return 1

    local fix_applied=false

    local containers
    containers=$(docker compose ps -q 2>/dev/null || echo "")
    if [[ -z "$containers" ]]; then
        log_error "No containers found. Cannot auto-fix."
        return 1
    fi

    # Permission denied errors
    local perm_errors
    perm_errors=$(docker compose logs --tail=50 2>/dev/null | grep -i "permission denied" || true)
    if [[ -n "$perm_errors" ]]; then
        log_info "Detected 'permission denied' errors. Re-applying volume permissions..."
        prepare_runtime_dirs
        fix_applied=true
    fi

    # mkdir errors (Jaeger badger)
    local mkdir_errors
    mkdir_errors=$(docker compose logs --tail=50 2>/dev/null | grep -i "mkdir.*permission denied\|Error Creating Dir" || true)
    if [[ -n "$mkdir_errors" ]]; then
        log_info "Detected directory creation errors. Fixing Jaeger badger..."
        if [[ -n "$DATA_ROOT" ]]; then
            mkdir -p "${DATA_ROOT}/jaeger/key" "${DATA_ROOT}/jaeger/data" 2>/dev/null || true
            chown -R 10001:0 "${DATA_ROOT}/jaeger" 2>/dev/null || true
            chmod -R 755 "${DATA_ROOT}/jaeger" 2>/dev/null || true
        fi
        fix_applied=true
    fi

    # Restarting/unhealthy containers
    local restarting
    restarting=$(docker compose ps --format "{{.Name}} {{.Status}}" 2>/dev/null | grep -i "restarting" | awk '{print $1}' || true)
    if [[ -n "$restarting" ]]; then
        log_info "Found restarting containers: ${restarting}"
        fix_applied=true
    fi

    if ! $fix_applied; then
        log_info "No auto-fixable issues detected."
        return 1
    fi

    # Restart stack after fixes
    log_info "Restarting stack after fixes..."
    docker compose down 2>/dev/null || true
    sleep 5

    docker compose up -d 2>/dev/null
    local compose_exit=$?

    if [[ $compose_exit -ne 0 ]]; then
        log_error "docker compose up still failing after auto-fix (exit ${compose_exit})"
        return 1
    fi

    log_info "✓ Stack restarted after auto-fix"
    log_info "Waiting for services to initialize (45s)..."
    sleep 45
    return 0
}

# ═══════════════════════════════════════════════════════════════════════════════
# DEBUG BUNDLE (Enhanced in v3.0.3)
# ═══════════════════════════════════════════════════════════════════════════════

generate_debug_bundle() {
    log_info "Generating debug bundle for troubleshooting..."

    local bundle_dir="/tmp/rhinometric-debug-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "${bundle_dir}" 2>/dev/null || true

    cd "${INSTALL_DIR}" 2>/dev/null || true

    # docker compose ps
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" > "${bundle_dir}/compose-ps.txt" 2>&1 || true

    # docker compose config (full resolved config)
    docker compose config > "${bundle_dir}/compose-config-resolved.yml" 2>&1 || true

    # All service logs (last 200 lines)
    docker compose logs --tail=200 > "${bundle_dir}/all-services.log" 2>&1 || true

    # Per-service logs for unhealthy or failed services
    while IFS= read -r line; do
        local svc_name svc_status
        svc_name=$(echo "$line" | awk '{print $1}')
        svc_status=$(echo "$line" | awk '{$1=""; print $0}')
        if echo "$svc_status" | grep -qi "unhealthy\|exit\|restart\|dead"; then
            local safe_name="${svc_name//\//_}"
            docker compose logs --tail=300 "${svc_name#rhinometric-}" > "${bundle_dir}/svc-${safe_name}.log" 2>&1 || true
            docker inspect "$svc_name" > "${bundle_dir}/inspect-${safe_name}.json" 2>&1 || true
        fi
    done < <(docker compose ps --format "{{.Name}} {{.Status}}" 2>/dev/null || true)

    # System info
    {
        echo "=== Rhinometric Installer v${INSTALLER_VERSION} Debug Bundle ==="
        echo "=== Date: $(date -u) ==="
        echo ""
        echo "=== System ==="
        echo "Hostname: $(hostname 2>/dev/null || echo unknown)"
        echo "Kernel: $(uname -a 2>/dev/null || echo unknown)"
        echo "CPU: $(nproc 2>/dev/null || echo unknown) cores"
        echo ""
        echo "=== Memory ==="
        free -h 2>/dev/null || echo "(unavailable)"
        echo ""
        echo "=== Disk ==="
        df -h 2>/dev/null || echo "(unavailable)"
        echo ""
        echo "=== Docker System DF ==="
        docker system df 2>/dev/null || echo "(unavailable)"
        echo ""
        echo "=== Docker Info ==="
        docker info 2>/dev/null || echo "(unavailable)"
        echo ""
        echo "=== Docker Version ==="
        docker version 2>/dev/null || echo "(unavailable)"
        echo ""
        echo "=== Docker Compose Version ==="
        docker compose version 2>/dev/null || echo "(unavailable)"
        echo ""
        echo "=== Docker Images ==="
        docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}" 2>/dev/null || true
        echo ""
        echo "=== Published Ports ==="
        docker compose ps --format "table {{.Name}}\t{{.Ports}}" 2>/dev/null || true
        echo ""
        echo "=== Dmesg (last 50, OOM-related) ==="
        dmesg 2>/dev/null | tail -50 | grep -i "oom\|killed\|memory" || echo "(none)"
    } > "${bundle_dir}/system-info.txt" 2>&1

    # Journalctl docker
    journalctl -u docker --no-pager -n 200 > "${bundle_dir}/journalctl-docker.log" 2>&1 || true

    # Sanitized .env
    if [[ -f "${INSTALL_DIR}/.env" ]]; then
        sed 's/PASSWORD=.*/PASSWORD=***REDACTED***/g; s/SECRET=.*/SECRET=***REDACTED***/g; s/JWT_SECRET=.*/JWT_SECRET=***REDACTED***/g' \
            "${INSTALL_DIR}/.env" > "${bundle_dir}/env-sanitized.txt" 2>/dev/null || true
    fi

    # Failure report inline
    if [[ ${#FAILURE_REASONS[@]} -gt 0 ]]; then
        {
            echo "=== FAILURE REASONS ==="
            local i=1
            for reason in "${FAILURE_REASONS[@]}"; do
                echo "  ${i}. ${reason}"
                i=$((i + 1))
            done
        } > "${bundle_dir}/failure-reasons.txt" 2>/dev/null || true
    fi

    # Package
    local bundle_archive="${INSTALL_DIR}/install-debug-bundle.tar.gz"
    tar -czf "${bundle_archive}" -C "$(dirname "${bundle_dir}")" "$(basename "${bundle_dir}")" 2>/dev/null || true
    rm -rf "${bundle_dir}" 2>/dev/null || true

    if [[ -f "${bundle_archive}" ]]; then
        local bundle_size
        bundle_size=$(du -h "${bundle_archive}" 2>/dev/null | awk '{print $1}' || echo "?")
        log_info "✓ Debug bundle saved: ${bundle_archive} (${bundle_size})"
    else
        log_warn "Could not create debug bundle."
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# FAILURE REPORT & ROLLBACK
# ═══════════════════════════════════════════════════════════════════════════════

write_failure_report() {
    local report_file="${INSTALL_DIR}/install-failure-report.txt"
    local server_ip
    server_ip=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")

    mkdir -p "${INSTALL_DIR}" 2>/dev/null || true

    {
        echo "════════════════════════════════════════════════════════════════"
        echo " RHINOMETRIC v${INSTALLER_VERSION} — INSTALLATION FAILURE REPORT"
        echo " Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
        echo " Server: $(hostname 2>/dev/null || echo unknown) (${server_ip})"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        echo "CRITICAL FAILURES:"
        local i=1
        for reason in "${FAILURE_REASONS[@]}"; do
            echo "  ${i}. ${reason}"
            i=$((i + 1))
        done
        echo ""
        echo "WARNINGS (${#INSTALL_WARNINGS[@]}):"
        for w in "${INSTALL_WARNINGS[@]}"; do
            echo "  - ${w}"
        done
        echo ""
        echo "CONTAINER STATUS AT FAILURE:"
        cd "${INSTALL_DIR}" 2>/dev/null || true
        docker compose ps 2>/dev/null || echo "  (could not retrieve)"
        echo ""
        echo "PER-SERVICE DIAGNOSIS:"
        for svc in $(docker compose ps --format "{{.Name}}" 2>/dev/null || true); do
            local h s oom
            h=$(docker inspect --format '{{.State.Health.Status}}' "$svc" 2>/dev/null || echo "n/a")
            s=$(docker inspect --format '{{.State.Status}}' "$svc" 2>/dev/null || echo "n/a")
            oom=$(docker inspect --format '{{.State.OOMKilled}}' "$svc" 2>/dev/null || echo "n/a")
            if [[ "$h" != "healthy" || "$s" != "running" ]]; then
                echo "  ${svc}: state=${s} health=${h} OOMKilled=${oom}"
            fi
        done
        echo ""
        echo "MEMORY:"
        free -h 2>/dev/null || echo "  (unavailable)"
        echo ""
        echo "DISK:"
        df -h 2>/dev/null || echo "  (unavailable)"
        echo ""
        echo "════════════════════════════════════════════════════════════════"
    } > "${report_file}" 2>/dev/null || true

    if [[ -f "${report_file}" ]]; then
        log_info "Failure report saved: ${report_file}"
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
    echo "    3. Check disk space     : df -h"
    echo "    4. Check Docker daemon  : systemctl status docker"
    echo "    5. Retry installation   : sudo bash install-rhinometric.sh"
    echo ""

    echo -e "  ${BOLD}NOTE: Stack is still running for troubleshooting.${NC}"
    echo -e "  To clean up: cd ${INSTALL_DIR} && docker compose down -v --remove-orphans"
    echo ""

    if [[ -f "${INSTALL_DIR}/install-debug-bundle.tar.gz" ]]; then
        echo -e "  ${BOLD}Debug bundle:${NC} ${INSTALL_DIR}/install-debug-bundle.tar.gz"
    fi
    if [[ -f "${INSTALL_DIR}/install-failure-report.txt" ]]; then
        echo -e "  ${BOLD}Failure report:${NC} ${INSTALL_DIR}/install-failure-report.txt"
    fi
    echo ""
}

maybe_rollback() {
    if $ROLLBACK_ON_FAILURE; then
        log_info "Rolling back failed installation (--rollback-on-failure was set)..."
        cd "${INSTALL_DIR}" 2>/dev/null || true
        if docker compose ps -q 2>/dev/null | head -1 | grep -q .; then
            docker compose down -v --remove-orphans 2>/dev/null || true
        fi
        log_info "Rollback completed. Containers stopped and volumes removed."
    else
        log_info "Stack left running for troubleshooting (use --rollback-on-failure to auto-destroy)."
    fi
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

    # Discover the actual published console URL
    cd "${INSTALL_DIR}" 2>/dev/null || true
    local nginx_hp
    nginx_hp=$(docker compose port nginx 80 2>/dev/null || echo "")
    local console_url="http://${server_ip}"
    if [[ -n "$nginx_hp" ]]; then
        local nginx_port="${nginx_hp##*:}"
        if [[ "$nginx_port" == "80" ]]; then
            console_url="http://${server_ip}"
        else
            console_url="http://${server_ip}:${nginx_port}"
        fi
    fi

    cat > "${CREDENTIALS_FILE}" << CREDEOF
════════════════════════════════════════════════════════════════════════
 RHINOMETRIC v${INSTALLER_VERSION} — INSTALLATION CREDENTIALS
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

RHINOMETRIC CONSOLE (Main Interface — via Nginx)
  URL      : ${console_url}
  Username : admin
  Password : ${ADMIN_PASSWORD}

GRAFANA (Dashboards — internal, via Nginx proxy)
  URL      : ${console_url}/grafana  (or internal http://${server_ip}:3000 if published)
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

PROMETHEUS (Metrics — internal)
  URL      : http://${server_ip}:9090 (if published)

ALERTMANAGER (Alerts — internal)
  URL      : http://${server_ip}:9093 (if published)

JAEGER (Tracing — internal)
  URL      : http://${server_ip}:16686 (if published)

════════════════════════════════════════════════════════════════════════
CREDEOF

    chmod 600 "${CREDENTIALS_FILE}"

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

    echo -e "  ${BOLD}Console${NC}     : ${CYAN}${console_url}${NC}"
    echo -e "  ${BOLD}Admin User${NC}  : admin"
    echo -e "  ${BOLD}Admin Pass${NC}  : ${ADMIN_PASSWORD}"
    echo ""
    echo -e "  ${BOLD}Grafana${NC}     : admin / ${GRAFANA_PASSWORD}"
    echo -e "  ${BOLD}License${NC}     : ${LICENSE_STATUS}"
    if [[ "$LICENSE_STATUS" == "valid" ]]; then
        echo -e "  ${BOLD}Plan${NC}        : ${LICENSE_PLAN} (${LICENSE_HOSTS} hosts, expires ${LICENSE_EXPIRES})"
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
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

main() {
    parse_args "$@"
    banner
    check_root

    log_info "Starting Rhinometric v${INSTALLER_VERSION} installation..."
    log_info "Install directory: ${INSTALL_DIR}"
    echo ""

    # ── System checks ──
    log_step "STEP 0/8 — System Validation"
    check_os
    check_resources
    check_docker
    check_ports
    echo ""

    # Abort early if Docker is missing
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

    if [[ "$INSTALL_CRITICAL_FAILURE" == "true" ]]; then
        print_failure_report
        exit 1
    fi

    # ── Load pre-built images ──
    log_step "STEP 4b/8 — Load Docker Images"
    load_images
    echo ""

    if [[ "$INSTALL_CRITICAL_FAILURE" == "true" ]]; then
        print_failure_report
        exit 1
    fi

    # ── Verify build contexts ──
    verify_build_contexts

    if [[ "$INSTALL_CRITICAL_FAILURE" == "true" ]]; then
        print_failure_report
        exit 1
    fi

    # ── Prepare runtime volume directories ──
    log_step "STEP 5/8 — Prepare Runtime Volumes"
    prepare_runtime_dirs
    echo ""

    # ── Start stack ──
    start_stack
    local stack_exit=$?

    # ── Auto-fix loop if stack failed ──
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

    # Abort if stack completely failed
    if [[ "$INSTALL_CRITICAL_FAILURE" == "true" ]]; then
        generate_debug_bundle
        write_failure_report
        maybe_rollback
        print_failure_report
        exit 1
    fi

    # ── Health check ──
    health_check
    local health_exit=$?

    # If health check found fixable issues, try one more auto-fix round
    if [[ $health_exit -ne 0 && "$INSTALL_CRITICAL_FAILURE" != "true" ]]; then
        log_info "Health check found issues. Attempting one more auto-fix cycle..."
        if auto_fix_and_retry; then
            INSTALL_CRITICAL_FAILURE=false
            FAILURE_REASONS=()
            health_check
        fi
    fi

    # ════════════════════════════════════════════════════════════════════════
    # FINAL DECISION
    # ════════════════════════════════════════════════════════════════════════
    if [[ "$INSTALL_CRITICAL_FAILURE" == "true" ]]; then
        generate_debug_bundle
        write_failure_report
        maybe_rollback
        print_failure_report
        exit 1
    fi

    # ── Success ──
    save_credentials
    log_info "Installation completed. Rhinometric v${INSTALLER_VERSION} is ready."
    exit 0
}

# ── Entry point ──
main "$@"
