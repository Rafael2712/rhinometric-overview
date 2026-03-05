#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# RHINOMETRIC v3.0.4 — PRODUCTION INSTALLER
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
# v3.0.4 CHANGES (from v3.0.3):
#   - FIX(A): VictoriaMetrics promscrape — installer patches localhost:9090 ->
#             rhinometric-prometheus:9090 in prometheus config after copy.
#             Creates empty loadtest_targets.json if missing.
#   - FIX(B): AI Anomaly healthcheck — installer patches curl -> python urllib
#             in compose so containers without curl pass healthcheck.
#   - FIX(C): Endpoint validation — `docker compose port` returns "invalid IP:0"
#             for unpublished ports. Now validated with regex; only real
#             host:port values used.  Nginx is tested on port 80. Internal
#             services (grafana, prometheus, console) tested through nginx
#             proxy routes (/grafana, /api, /) — NOT via host ports.
#   - FIX(D): License/fingerprint UX — fingerprint saved to
#             /opt/rhinometric/fingerprint.txt; post-install license guide
#             printed; optional --wait-for-license mode.
# ═══════════════════════════════════════════════════════════════════════════════

# ── Do NOT use set -e — we handle every error explicitly ──────────────────────

# ─── Constants ────────────────────────────────────────────────────────────────
readonly INSTALLER_VERSION="3.0.4"
readonly INSTALL_DIR="${INSTALL_DIR:-/opt/rhinometric}"
readonly COMPOSE_FILE="docker-compose.yml"
readonly CREDENTIALS_FILE="${INSTALL_DIR}/install-info.txt"
readonly LICENSE_DEST="${INSTALL_DIR}/license.key"
readonly FINGERPRINT_FILE="${INSTALL_DIR}/fingerprint.txt"
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
WAIT_FOR_LICENSE=false
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
║          Enterprise Observability Platform v3.0.4                ║
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
            --wait-for-license)
                WAIT_FOR_LICENSE=true
                log_info "Will pause for license.key placement"
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
        # v3.0.3 FIX: parse safely — do NOT source (VERSION is readonly in this script)
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

    # v3.0.3 FIX: walk to existing parent for df; also check Docker data-root
    check_disk_space "${INSTALL_DIR}" "install-dir"
    local docker_root
    docker_root=$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || echo "/var/lib/docker")
    if [[ "$docker_root" != "$(df "${INSTALL_DIR}" 2>/dev/null | awk 'NR==2{print $6}')" ]]; then
        check_disk_space "$docker_root" "docker-root"
    fi
}

check_disk_space() {
    local path="$1" label="$2"
    local check_path="$path"
    while [[ ! -d "$check_path" && "$check_path" != "/" ]]; do
        check_path=$(dirname "$check_path")
    done
    local avail_kb avail_gb used_pct
    avail_kb=$(df -k "$check_path" 2>/dev/null | awk 'NR==2{print $4}')
    used_pct=$(df -k "$check_path" 2>/dev/null | awk 'NR==2{print $5}')
    if [[ -z "$avail_kb" || "$avail_kb" == "0" ]]; then
        fail_critical "Disk check failed for ${path} (${label}): could not determine available space."
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
# STEP 3 — MACHINE FINGERPRINT  (v3.0.4: saves to file, improved UX)
# ═══════════════════════════════════════════════════════════════════════════════

detect_fingerprint() {
    log_step "STEP 1/8 — Machine Fingerprint Detection"

    install_rhino_lic

    if command -v rhino-lic &>/dev/null; then
        MACHINE_FINGERPRINT=$(rhino-lic fingerprint 2>/dev/null || echo "")
    fi

    if [[ -n "$MACHINE_FINGERPRINT" ]]; then
        # v3.0.4: persist fingerprint so user can retrieve it later
        mkdir -p "${INSTALL_DIR}" 2>/dev/null || true
        echo "$MACHINE_FINGERPRINT" > "${FINGERPRINT_FILE}" 2>/dev/null || true
        chmod 644 "${FINGERPRINT_FILE}" 2>/dev/null || true

        echo ""
        echo -e "${BOLD}┌──────────────────────────────────────────────────────────────┐${NC}"
        echo -e "${BOLD}│           Machine Fingerprint Detected                       │${NC}"
        echo -e "${BOLD}├──────────────────────────────────────────────────────────────┤${NC}"
        echo -e "${BOLD}│${NC}                                                              ${BOLD}│${NC}"
        echo -e "${BOLD}│${NC}  ${CYAN}${MACHINE_FINGERPRINT}${NC}"
        echo -e "${BOLD}│${NC}                                                              ${BOLD}│${NC}"
        echo -e "${BOLD}│${NC}  Saved to: ${FINGERPRINT_FILE}                ${BOLD}│${NC}"
        echo -e "${BOLD}│${NC}                                                              ${BOLD}│${NC}"
        echo -e "${BOLD}│${NC}  Send this fingerprint to Rhinometric to obtain              ${BOLD}│${NC}"
        echo -e "${BOLD}│${NC}  your signed license file (license.key).                     ${BOLD}│${NC}"
        echo -e "${BOLD}│${NC}                                                              ${BOLD}│${NC}"
        echo -e "${BOLD}└──────────────────────────────────────────────────────────────┘${NC}"
        echo ""
    else
        log_warn "Could not detect machine fingerprint. License validation will be skipped."
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — LICENSE VALIDATION  (v3.0.4: --wait-for-license + apply guide)
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
        # v3.0.4: --wait-for-license mode
        if $WAIT_FOR_LICENSE; then
            echo ""
            echo -e "  ${BOLD}--wait-for-license mode active.${NC}"
            echo -e "  Place your ${CYAN}license.key${NC} in: ${CYAN}${INSTALL_DIR}/${NC}"
            echo ""
            local wait_secs=0
            local max_wait=300
            while [[ $wait_secs -lt $max_wait ]]; do
                if [[ -f "${INSTALL_DIR}/license.key" ]]; then
                    license_path="${INSTALL_DIR}/license.key"
                    log_info "✓ license.key detected!"
                    break
                fi
                echo -ne "\r  Waiting for license.key... (${wait_secs}/${max_wait}s) Press Ctrl+C to skip.  "
                sleep 5
                wait_secs=$((wait_secs + 5))
            done
            echo ""
            if [[ -z "$license_path" ]]; then
                log_info "Timeout reached. Continuing without license."
            fi
        else
            echo ""
            read -r -p "  Enter path to license.key (or press ENTER to continue without license): " license_path
        fi
    fi

    if [[ -z "$license_path" ]]; then
        LICENSE_STATUS="unlicensed"
        echo ""
        log_warn "No license provided. Platform will start in unlicensed mode."
        print_license_apply_guide
        return 0
    fi

    if [[ ! -f "$license_path" ]]; then
        log_warn "License file not found: ${license_path}. Continuing in unlicensed mode."
        LICENSE_STATUS="unlicensed"
        print_license_apply_guide
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
            log_warn "License signature is INVALID. Platform will start but licensing will be limited." ;;
        2)  LICENSE_STATUS="expired"
            log_warn "License has EXPIRED. Platform will start but licensing will be limited." ;;
        3)  LICENSE_STATUS="fingerprint_mismatch"
            log_warn "License FINGERPRINT MISMATCH (expected: ${MACHINE_FINGERPRINT}). Platform will start." ;;
        4)  LICENSE_STATUS="parse_error"
            log_warn "License file could not be parsed. Platform will start." ;;
        *)  LICENSE_STATUS="unknown_error"
            log_warn "License validation returned unexpected code: ${exit_code}. Platform will start." ;;
    esac
    return 0
}

# v3.0.4: print instructions for applying license after install
print_license_apply_guide() {
    echo ""
    echo -e "  ${BOLD}To apply a license later (no reinstall needed):${NC}"
    echo ""
    echo "    1. Get your fingerprint:  cat ${FINGERPRINT_FILE}"
    echo "    2. Send fingerprint to Rhinometric to receive license.key"
    echo "    3. Copy license.key to server:"
    echo "         scp license.key root@<SERVER_IP>:${LICENSE_DEST}"
    echo "    4. Restart the backend to pick up the license:"
    echo "         cd ${INSTALL_DIR} && docker compose restart rhinometric-console-backend license-server-v2"
    echo ""
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
SMTP_PASS=changeme
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
    log_info "✓ Jaeger: ${DATA_ROOT}/jaeger (uid=10001)"

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
# STEP 7 — COPY FILES + POST-COPY CONFIG PATCHES (v3.0.4)
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

    # ── v3.0.4: Post-copy config patches ──────────────────────────────────
    patch_configs_post_copy
}

# ═══════════════════════════════════════════════════════════════════════════════
# POST-COPY CONFIG PATCHES (NEW in v3.0.4)
# ═══════════════════════════════════════════════════════════════════════════════
# Applies targeted fixes to config files AFTER they've been copied to
# INSTALL_DIR. This ensures the fixes survive even if the tarball ships
# with the old configs.
# ═══════════════════════════════════════════════════════════════════════════════

patch_configs_post_copy() {
    log_info "Applying post-copy config patches..."

    # ── FIX(A): VictoriaMetrics promscrape — localhost:9090 ───────────────
    # VictoriaMetrics uses -promscrape.config pointing to the same prometheus
    # config. Inside the VM container, localhost:9090 is unreachable.
    # Fix: use the Docker service name.
    local prom_configs=(
        "${INSTALL_DIR}/config/prometheus-v2.2.yml"
        "${INSTALL_DIR}/prometheus/prometheus.yml"
    )
    for cfg in "${prom_configs[@]}"; do
        if [[ -f "$cfg" ]]; then
            if grep -q "'localhost:9090'" "$cfg" 2>/dev/null; then
                sed -i "s/'localhost:9090'/'rhinometric-prometheus:9090'/g" "$cfg"
                log_info "✓ Patched ${cfg##*/}: localhost:9090 → rhinometric-prometheus:9090"
            fi
        fi
    done

    # ── FIX(A): Create empty loadtest_targets.json if missing ─────────────
    # VictoriaMetrics expects this file via file_sd_configs. An empty JSON
    # array is harmless and prevents scrape config parse errors.
    local loadtest_config="${INSTALL_DIR}/config/loadtest_targets.json"
    if [[ ! -f "$loadtest_config" ]]; then
        echo '[]' > "$loadtest_config"
        log_info "✓ Created empty loadtest_targets.json"
    fi
    # Also in prometheus/ dir (where Prometheus itself mounts it)
    local loadtest_prom="${INSTALL_DIR}/prometheus/loadtest_targets.json"
    if [[ ! -f "$loadtest_prom" ]]; then
        echo '[]' > "$loadtest_prom"
        log_info "✓ Created empty prometheus/loadtest_targets.json"
    fi

    # ── FIX(B): AI Anomaly healthcheck — curl → python urllib ─────────────
    # The ai-anomaly container is python:3.11-slim and does NOT have curl.
    # The Dockerfile already has a python-based HEALTHCHECK, but compose
    # overrides it. Patch compose to use python as well.
    local compose_file="${INSTALL_DIR}/docker-compose.yml"
    if grep -q '^\s*- curl' "$compose_file" 2>/dev/null; then
        # Use python to do the replacement safely
        python3 -c "
import pathlib, sys
f = pathlib.Path(sys.argv[1])
t = f.read_text()

old = '''    healthcheck:
      test:
      - CMD
      - curl
      - -f
      - http://localhost:8085/health
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s'''

new = '''    healthcheck:
      test:
      - CMD
      - python
      - -c
      - \"import urllib.request; urllib.request.urlopen('http://localhost:8085/health', timeout=5)\"
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 45s'''

if old in t:
    t = t.replace(old, new, 1)
    f.write_text(t)
    print('OK')
else:
    print('SKIP')
" "$compose_file" 2>/dev/null
        local patch_result=$?
        if [[ $patch_result -eq 0 ]]; then
            log_info "✓ Patched compose: ai-anomaly healthcheck curl → python urllib"
        fi
    else
        log_info "✓ AI Anomaly healthcheck already patched (no curl found)"
    fi

    # ── FIX(A): Mount loadtest_targets.json into victoria-metrics ─────────
    # Check if the mount is already there
    if ! grep -q 'loadtest_targets.json:/etc/prometheus/loadtest_targets.json' "$compose_file" 2>/dev/null; then
        # Try to add it alongside the existing prometheus config mount for VM
        python3 -c "
import pathlib, sys
f = pathlib.Path(sys.argv[1])
t = f.read_text()
marker = '    - ./config/prometheus-v2.2.yml:/etc/prometheus/prometheus.yml:ro\n    networks:'
replacement = '    - ./config/prometheus-v2.2.yml:/etc/prometheus/prometheus.yml:ro\n    - ./config/loadtest_targets.json:/etc/prometheus/loadtest_targets.json:ro\n    networks:'
if marker in t and 'loadtest_targets.json:/etc/prometheus/loadtest' not in t:
    t = t.replace(marker, replacement, 1)
    f.write_text(t)
    print('OK')
else:
    print('SKIP')
" "$compose_file" 2>/dev/null
        log_info "✓ Patched compose: added loadtest_targets.json mount to victoria-metrics"
    fi

    log_info "✓ Post-copy patches applied"
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

    # Validate compose config (suppress env-var warnings)
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

    log_info "Pulling Docker images (this may take several minutes)..."
    docker compose pull --ignore-buildable 2>/dev/null || true

    log_info "Building local images (this may take several minutes on first install)..."
    local build_output
    build_output=$(docker compose build 2>&1)
    local build_exit=$?
    if [[ $build_exit -ne 0 ]]; then
        log_warn "docker compose build had issues: $(echo "$build_output" | tail -10)"
    else
        log_info "✓ Local images built successfully"
    fi

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
# STEP 9 — FULL STACK HEALTH CHECK
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
                diagnose_unhealthy_service "$svc"
            fi
        done

        if [[ ${#crit_fail[@]} -gt 0 ]]; then
            log_error "Critical services not healthy:"
            for item in "${crit_fail[@]}"; do log_error "  ✗ ${item}"; done
        fi
        if [[ ${#important_fail[@]} -gt 0 ]]; then
            log_warn "Important services not healthy (may still be starting):"
            for item in "${important_fail[@]}"; do log_warn "  ⚠ ${item}"; done
        fi
        if [[ ${#optional_fail[@]} -gt 0 ]]; then
            log_warn "Optional services not healthy (non-blocking):"
            for item in "${optional_fail[@]}"; do log_warn "  ⚠ ${item}"; done
        fi

        for svc in "${critical_services[@]}"; do
            local s
            s=$(docker inspect --format '{{.State.Status}}' "$svc" 2>/dev/null || echo "unknown")
            if [[ "$s" != "running" ]]; then
                fail_critical "Critical service ${svc} is NOT running (state=${s})"
            fi
        done
    fi

    # ── Phase 3: HTTP endpoint checks (v3.0.4: fixed port detection) ──
    log_info "Phase 3: Verifying HTTP endpoints..."
    verify_http_endpoints

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
# HTTP ENDPOINT VERIFICATION (v3.0.4: COMPLETELY REWRITTEN)
# ═══════════════════════════════════════════════════════════════════════════════
# Root cause of v3.0.3 bug: `docker compose port <svc> <port>` returns the
# literal string "invalid IP:0" for services without host-published ports.
# The old code did `-n` check which passed (non-empty), created urls like
# "http://invalid IP:0/..." and declared a false critical failure.
#
# v3.0.4 strategy:
#   1. Discover the Nginx published host port (the ONLY public front door).
#   2. Verify Nginx responds on that port.
#   3. Verify internal services through Nginx proxy routes:
#        /          → console frontend
#        /api/health → console backend
#        /grafana/api/health → grafana
#   4. For services with NO Nginx proxy route (Prometheus, etc.), validate
#      using `docker inspect` health status (already covered in Phase 2).
#   5. NEVER construct URLs from `docker compose port` output without
#      validating the IP:PORT with a regex first.
# ═══════════════════════════════════════════════════════════════════════════════

# Helper: returns true only if the string matches a valid IP:PORT pattern
is_valid_hostport() {
    local hp="$1"
    # Must match: <IP>:<PORT>  where IP is dotted-quad or :: and PORT is numeric
    if [[ "$hp" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$ ]]; then
        return 0
    elif [[ "$hp" =~ ^\[::\]:[0-9]+$ ]]; then
        return 0
    fi
    return 1
}

verify_http_endpoints() {
    cd "${INSTALL_DIR}" || return 1

    # ── Step 1: Find the Nginx published host port ────────────────────────
    local nginx_hp
    nginx_hp=$(docker compose port nginx 80 2>/dev/null || echo "")

    if ! is_valid_hostport "$nginx_hp"; then
        log_warn "Nginx host port not detected (got: '${nginx_hp}'). Skipping HTTP checks."
        log_warn "Services may only be reachable via Docker internal network."
        return 0
    fi

    # Replace 0.0.0.0 with 127.0.0.1 for local curl
    local nginx_url
    nginx_url="http://${nginx_hp//0.0.0.0/127.0.0.1}"

    log_info "Nginx front door: ${nginx_url}"

    # ── Step 2: Build endpoint list (all go through Nginx) ────────────────
    # These are real routes served by nginx.conf upstream blocks.
    local -a endpoints=(
        "Nginx|${nginx_url}|critical"
        "Console (via Nginx)|${nginx_url}/|critical"
        "Backend API (via Nginx)|${nginx_url}/api/health|important"
        "Grafana (via Nginx)|${nginx_url}/grafana/api/health|important"
    )

    log_info "Checking ${#endpoints[@]} endpoint(s) through Nginx..."

    local http_attempts=0
    declare -A ep_ok

    while [ "$http_attempts" -lt 10 ]; do
        local all_ok=true
        for ep in "${endpoints[@]}"; do
            IFS='|' read -r label url criticality <<< "$ep"
            if [[ "${ep_ok[$label]:-}" == "1" ]]; then
                continue
            fi
            local http_code
            http_code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$url" 2>/dev/null || echo "000")
            if [[ "$http_code" -ge 200 && "$http_code" -lt 500 ]]; then
                ep_ok["$label"]="1"
                log_info "✓ ${label}: HTTP ${http_code} (${url})"
            else
                all_ok=false
            fi
        done
        if $all_ok; then break; fi
        http_attempts=$((http_attempts + 1))
        if [[ $http_attempts -lt 10 ]]; then sleep 8; fi
    done

    # ── Step 3: Report failures ──────────────────────────────────────────
    for ep in "${endpoints[@]}"; do
        IFS='|' read -r label url criticality <<< "$ep"
        if [[ "${ep_ok[$label]:-}" != "1" ]]; then
            if [[ "$criticality" == "critical" ]]; then
                fail_critical "${label} (${url}) not responding after ~80s"
            else
                log_warn "${label} (${url}) not responding — non-blocking"
            fi
        fi
    done

    local crit_count=0
    for ep in "${endpoints[@]}"; do
        IFS='|' read -r label url criticality <<< "$ep"
        if [[ "$criticality" == "critical" && "${ep_ok[$label]:-}" != "1" ]]; then
            crit_count=$((crit_count + 1))
        fi
    done

    if [[ "$crit_count" -eq 0 ]]; then
        log_info "✓ All critical endpoints responding through Nginx"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE DIAGNOSIS
# ═══════════════════════════════════════════════════════════════════════════════

diagnose_unhealthy_service() {
    local container="$1"
    local short_name="${container#rhinometric-}"

    log_info "  Diagnosing ${short_name}..."

    local oom_killed
    oom_killed=$(docker inspect --format '{{.State.OOMKilled}}' "$container" 2>/dev/null || echo "false")
    if [[ "$oom_killed" == "true" ]]; then
        log_error "  → ${short_name}: OOM killed! Container ran out of memory."
        log_error "  → Fix: increase VM RAM or reduce memory limits in compose."
        return
    fi

    local state exit_code
    state=$(docker inspect --format '{{.State.Status}}' "$container" 2>/dev/null || echo "unknown")
    exit_code=$(docker inspect --format '{{.State.ExitCode}}' "$container" 2>/dev/null || echo "-1")
    if [[ "$state" != "running" && "$exit_code" != "0" ]]; then
        log_warn "  → ${short_name}: exited with code ${exit_code}"
    fi

    local health_log
    health_log=$(docker inspect --format '{{range .State.Health.Log}}{{.Output}}{{end}}' "$container" 2>/dev/null || echo "")
    if [[ -n "$health_log" ]]; then
        log_info "  → Health check output (last): $(echo "$health_log" | tail -c 300)"
    fi

    local dmesg_oom
    dmesg_oom=$(dmesg 2>/dev/null | tail -100 | grep -i "oom\|killed process" | grep -i "${short_name}\|docker" | tail -3 || true)
    if [[ -n "$dmesg_oom" ]]; then
        log_error "  → Kernel OOM evidence: ${dmesg_oom}"
    fi

    local disk_avail
    disk_avail=$(df -BG "${INSTALL_DIR}" 2>/dev/null | awk 'NR==2{print $4}' | tr -d 'G' || echo 0)
    if [[ "$disk_avail" -lt 2 ]]; then
        log_error "  → ${short_name}: disk space critically low (${disk_avail} GB free)"
    fi

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

    local perm_errors
    perm_errors=$(docker compose logs --tail=50 2>/dev/null | grep -i "permission denied" || true)
    if [[ -n "$perm_errors" ]]; then
        log_info "Detected 'permission denied' errors. Re-applying volume permissions..."
        prepare_runtime_dirs
        fix_applied=true
    fi

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
# DEBUG BUNDLE
# ═══════════════════════════════════════════════════════════════════════════════

generate_debug_bundle() {
    log_info "Generating debug bundle for troubleshooting..."

    local bundle_dir="/tmp/rhinometric-debug-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "${bundle_dir}" 2>/dev/null || true

    cd "${INSTALL_DIR}" 2>/dev/null || true

    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" > "${bundle_dir}/compose-ps.txt" 2>&1 || true
    docker compose config > "${bundle_dir}/compose-config-resolved.yml" 2>&1 || true
    docker compose logs --tail=200 > "${bundle_dir}/all-services.log" 2>&1 || true

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

    journalctl -u docker --no-pager -n 200 > "${bundle_dir}/journalctl-docker.log" 2>&1 || true

    if [[ -f "${INSTALL_DIR}/.env" ]]; then
        sed 's/PASSWORD=.*/PASSWORD=***REDACTED***/g; s/SECRET=.*/SECRET=***REDACTED***/g; s/JWT_SECRET=.*/JWT_SECRET=***REDACTED***/g' \
            "${INSTALL_DIR}/.env" > "${bundle_dir}/env-sanitized.txt" 2>/dev/null || true
    fi

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
    if is_valid_hostport "$nginx_hp"; then
        local nginx_port="${nginx_hp##*:}"
        if [[ "$nginx_port" != "80" ]]; then
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

GRAFANA (Dashboards — via Nginx proxy)
  URL      : ${console_url}/grafana
  Username : admin
  Password : ${GRAFANA_PASSWORD}

POSTGRESQL (Database — internal)
  Host     : localhost:5432
  Database : rhinometric
  Username : rhinometric
  Password : ${POSTGRES_PASSWORD}

REDIS (Cache — internal)
  Host     : localhost:6379
  Password : ${REDIS_PASSWORD}

PROMETHEUS (Metrics — internal, not exposed to host)
  Access   : via Grafana datasource or docker exec

ALERTMANAGER (Alerts — internal)
  Access   : via console backend or docker exec

JAEGER (Tracing — internal)
  Access   : via console or docker exec

APPLYING LICENSE LATER (no reinstall):
  1. cat ${FINGERPRINT_FILE}
  2. Send fingerprint to Rhinometric
  3. scp license.key root@${server_ip}:${LICENSE_DEST}
  4. cd ${INSTALL_DIR} && docker compose restart rhinometric-console-backend license-server-v2

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
    echo -e "  ${BOLD}Grafana${NC}     : ${CYAN}${console_url}/grafana${NC} (admin / ${GRAFANA_PASSWORD})"
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

    # ── Copy files + post-copy patches ──
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
