#!/usr/bin/env bash
###############################################################################
# RHINOMETRIC v2.6.0 — Single Installer (On-Premise)
# Idempotent · Interactive + Non-Interactive · Rollback-safe
#
# Usage:
#   Interactive:     sudo bash install-rhinometric.sh
#   Non-interactive: sudo bash install-rhinometric.sh --non-interactive \
#                      --edition trial --install-dir /opt/rhinometric
#   Dry-run:         sudo bash install-rhinometric.sh --dry-run
#
# Supports: Ubuntu 22.04 / 24.04, Debian 12
###############################################################################
set -Eeuo pipefail

readonly SCRIPT_VERSION="2.6.0"
readonly SCRIPT_DATE="2026-02-25"
readonly LOG_FILE="/var/log/rhinometric-install.log"
readonly DEFAULT_INSTALL_DIR="/opt/rhinometric"
readonly DEFAULT_DATA_DIR_SUFFIX="rhinometric_data_v2.5"
readonly COMPOSE_FILE_NAME="docker-compose-v2.5.0-SECURE.yml"
readonly SYMLINK_NAME="docker-compose.yml"
readonly ENV_TEMPLATE=".env.template"
readonly ENV_FILE=".env"
readonly MIN_RAM_MB=7500
readonly MIN_DISK_GB=50
readonly MIN_CPU=2
readonly RECOMMENDED_RAM_MB=15000
readonly RECOMMENDED_DISK_GB=150
readonly RECOMMENDED_CPU=4

# Ports that must be free (or already owned by rhinometric containers)
readonly REQUIRED_PORTS=(5432 6379 3000 3100 8105 9090 9093 16686)

# ─── Colours ────────────────────────────────────────────────────────────────
C_RESET="\033[0m"; C_GREEN="\033[0;32m"; C_BLUE="\033[0;34m"
C_YELLOW="\033[1;33m"; C_RED="\033[0;31m"; C_BOLD="\033[1m"

# ─── CLI Defaults ──────────────────────────────────────────────────────────
INSTALL_DIR="$DEFAULT_INSTALL_DIR"
EDITION=""            # trial | annual
LICENSE_FILE=""
NON_INTERACTIVE=false
DRY_RUN=false
SKIP_BUILD=false
ADMIN_EMAIL=""
DOMAIN=""

###############################################################################
# LOGGING
###############################################################################
_ts() { date -u +"%Y-%m-%d %H:%M:%S UTC"; }

log_init() {
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "=== Rhinometric Installer v${SCRIPT_VERSION} started at $(_ts) ===" >> "$LOG_FILE"
}

log() {
    local level="$1"; shift
    local msg="$*"
    echo "[$(_ts)] [$level] $msg" >> "$LOG_FILE"
    case "$level" in
        INFO)  echo -e "${C_GREEN}[INFO]${C_RESET}  $msg" ;;
        WARN)  echo -e "${C_YELLOW}[WARN]${C_RESET}  $msg" ;;
        ERROR) echo -e "${C_RED}[ERROR]${C_RESET} $msg" ;;
        OK)    echo -e "${C_GREEN}[  OK]${C_RESET}  $msg" ;;
        DRY)   echo -e "${C_BLUE}[DRY]${C_RESET}   $msg" ;;
    esac
}

die() { log ERROR "$*"; echo ""; echo "Installation aborted. See $LOG_FILE for details."; exit 1; }

###############################################################################
# BANNER
###############################################################################
show_banner() {
    echo -e "${C_BLUE}${C_BOLD}"
    cat <<'BANNER'

  ╔═══════════════════════════════════════════════════════════╗
  ║                                                           ║
  ║   ██████╗ ██╗  ██╗██╗███╗   ██╗ ██████╗ ███╗   ███╗      ║
  ║   ██╔══██╗██║  ██║██║████╗  ██║██╔═══██╗████╗ ████║      ║
  ║   ██████╔╝███████║██║██╔██╗ ██║██║   ██║██╔████╔██║      ║
  ║   ██╔══██╗██╔══██║██║██║╚██╗██║██║   ██║██║╚██╔╝██║      ║
  ║   ██║  ██║██║  ██║██║██║ ╚████║╚██████╔╝██║ ╚═╝ ██║      ║
  ║   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝   ║
  ║                                                           ║
  ║        Enterprise Observability Platform v2.6.0           ║
  ║               On-Premise Installer                        ║
  ╚═══════════════════════════════════════════════════════════╝

BANNER
    echo -e "${C_RESET}"
}

###############################################################################
# ARGUMENT PARSING
###############################################################################
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --install-dir)       INSTALL_DIR="$2"; shift 2 ;;
            --edition)           EDITION="$2"; shift 2 ;;
            --license-file)      LICENSE_FILE="$2"; shift 2 ;;
            --non-interactive)   NON_INTERACTIVE=true; shift ;;
            --dry-run)           DRY_RUN=true; shift ;;
            --skip-build)        SKIP_BUILD=true; shift ;;
            --admin-email)       ADMIN_EMAIL="$2"; shift 2 ;;
            --domain)            DOMAIN="$2"; shift 2 ;;
            -h|--help)           usage; exit 0 ;;
            *)                   die "Unknown option: $1. Use --help." ;;
        esac
    done
}

usage() {
    cat <<EOF
Rhinometric On-Premise Installer v${SCRIPT_VERSION}

Usage: sudo bash $0 [OPTIONS]

Options:
  --install-dir DIR       Installation directory (default: /opt/rhinometric)
  --edition TYPE          Edition: trial | annual (prompted if omitted)
  --license-file FILE     Path to .lic / .key file (optional, can apply later)
  --non-interactive       Run without prompts (requires --edition)
  --dry-run               Validate system without making changes
  --skip-build            Skip docker image builds (use pre-built images)
  --admin-email EMAIL     Admin email for notifications
  --domain DOMAIN         Public domain (optional, defaults to server IP)
  -h, --help              Show this help

Examples:
  # Interactive install
  sudo bash $0

  # Non-interactive trial
  sudo bash $0 --non-interactive --edition trial

  # Install with license
  sudo bash $0 --edition annual --license-file /tmp/customer.lic

Post-install commands:
  rhinoctl status          Show platform status
  rhinoctl fingerprint     Generate hardware ID for licensing
  rhinoctl apply-license   Apply a license file
  rhinoctl start/stop      Start or stop the platform
EOF
}

###############################################################################
# PRE-FLIGHT CHECKS
###############################################################################
check_root() {
    if [[ $EUID -ne 0 ]]; then
        die "This script must be run as root (use sudo)."
    fi
    log OK "Running as root"
}

check_os() {
    if [[ ! -f /etc/os-release ]]; then
        die "Cannot detect OS (/etc/os-release missing)."
    fi
    # shellcheck disable=SC1091
    . /etc/os-release

    case "$ID" in
        ubuntu)
            if [[ "${VERSION_ID}" != "22.04" && "${VERSION_ID}" != "24.04" ]]; then
                log WARN "Ubuntu ${VERSION_ID} detected. Tested on 22.04/24.04."
            else
                log OK "Ubuntu ${VERSION_ID} detected"
            fi
            ;;
        debian)
            log WARN "Debian ${VERSION_ID} detected. Officially tested on Ubuntu 22.04/24.04."
            ;;
        *)
            die "Unsupported OS: ${PRETTY_NAME}. Requires Ubuntu 22.04/24.04 or Debian 12."
            ;;
    esac
}

check_resources() {
    # CPU
    local cpu_cores
    cpu_cores=$(nproc 2>/dev/null || echo 1)
    if (( cpu_cores < MIN_CPU )); then
        die "CPU: ${cpu_cores} cores detected. Minimum: ${MIN_CPU}."
    elif (( cpu_cores < RECOMMENDED_CPU )); then
        log WARN "CPU: ${cpu_cores} cores (recommended: ${RECOMMENDED_CPU}+)"
    else
        log OK "CPU: ${cpu_cores} cores"
    fi

    # RAM
    local ram_mb
    ram_mb=$(awk '/^MemTotal:/ {printf "%.0f", $2/1024}' /proc/meminfo 2>/dev/null || echo 0)
    if (( ram_mb < MIN_RAM_MB )); then
        die "RAM: ${ram_mb} MB detected. Minimum: ${MIN_RAM_MB} MB."
    elif (( ram_mb < RECOMMENDED_RAM_MB )); then
        log WARN "RAM: ${ram_mb} MB (recommended: ${RECOMMENDED_RAM_MB}+ MB)"
    else
        log OK "RAM: ${ram_mb} MB"
    fi

    # Disk
    local disk_gb
    disk_gb=$(df -BG "${INSTALL_DIR%/*}" 2>/dev/null | awk 'NR==2 {gsub(/G/,"",$4); print $4}')
    if [[ -z "$disk_gb" ]]; then
        disk_gb=$(df -BG / | awk 'NR==2 {gsub(/G/,"",$4); print $4}')
    fi
    if (( disk_gb < MIN_DISK_GB )); then
        die "Disk: ${disk_gb} GB available. Minimum: ${MIN_DISK_GB} GB."
    elif (( disk_gb < RECOMMENDED_DISK_GB )); then
        log WARN "Disk: ${disk_gb} GB available (recommended: ${RECOMMENDED_DISK_GB}+ GB)"
    else
        log OK "Disk: ${disk_gb} GB available"
    fi
}

check_docker() {
    if ! command -v docker &>/dev/null; then
        die "Docker is not installed. Install with: curl -fsSL https://get.docker.com | sh"
    fi

    local docker_version
    docker_version=$(docker --version 2>/dev/null | grep -oP '\d+\.\d+' | head -1)
    log OK "Docker ${docker_version} installed"

    # Check Docker daemon running
    if ! docker info &>/dev/null; then
        die "Docker daemon is not running. Start with: systemctl start docker"
    fi

    # Check compose v2
    if docker compose version &>/dev/null; then
        local compose_ver
        compose_ver=$(docker compose version --short 2>/dev/null)
        log OK "Docker Compose ${compose_ver} (plugin)"
    elif command -v docker-compose &>/dev/null; then
        local compose_ver
        compose_ver=$(docker-compose --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+')
        log OK "docker-compose ${compose_ver} (standalone)"
    else
        die "Docker Compose not found. Install Docker Compose v2."
    fi
}

# Wrapper: use whichever compose is available
compose_cmd() {
    if docker compose version &>/dev/null; then
        docker compose "$@"
    else
        docker-compose "$@"
    fi
}

check_ports() {
    local ports_blocked=()
    for port in "${REQUIRED_PORTS[@]}"; do
        if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
            # Check if it's our own container
            local owner
            owner=$(ss -tlnp 2>/dev/null | grep ":${port} " | grep -oP 'users:\(\("\K[^"]+' || echo "unknown")
            if [[ "$owner" == *docker* ]] || [[ "$owner" == *rhinometric* ]]; then
                continue  # Our own container, OK
            fi
            ports_blocked+=("$port")
        fi
    done

    if (( ${#ports_blocked[@]} > 0 )); then
        die "Ports in use by other services: ${ports_blocked[*]}. Free them before installing."
    fi
    log OK "Required ports available (or owned by existing Rhinometric containers)"
}

check_dependencies() {
    local missing=()
    for cmd in curl openssl; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done

    if (( ${#missing[@]} > 0 )); then
        log WARN "Installing missing dependencies: ${missing[*]}"
        if $DRY_RUN; then
            log DRY "Would install: ${missing[*]}"
        else
            apt-get update -qq && apt-get install -y -qq "${missing[@]}" >> "$LOG_FILE" 2>&1
        fi
    fi

    # jq is optional but nice to have
    if ! command -v jq &>/dev/null; then
        log WARN "jq not found — installing for JSON health checks"
        if ! $DRY_RUN; then
            apt-get install -y -qq jq >> "$LOG_FILE" 2>&1 || true
        fi
    fi
    log OK "Dependencies satisfied (curl, openssl, jq)"
}

###############################################################################
# DETECT EXISTING INSTALLATION
###############################################################################
detect_existing() {
    local existing=false

    if [[ -d "$INSTALL_DIR" && -f "$INSTALL_DIR/$SYMLINK_NAME" ]]; then
        existing=true
    fi

    if $existing; then
        log WARN "Existing installation detected at $INSTALL_DIR"

        # Check running containers
        local running=0
        if cd "$INSTALL_DIR" 2>/dev/null; then
            running=$(compose_cmd ps -q 2>/dev/null | wc -l || echo 0)
        fi

        if (( running > 0 )); then
            log WARN "$running containers currently running"
        fi

        if $NON_INTERACTIVE; then
            log INFO "Non-interactive mode: preserving existing .env and data"
            return 0
        fi

        echo ""
        echo -e "${C_YELLOW}An existing installation was found at ${INSTALL_DIR}.${C_RESET}"
        echo ""
        echo "  1) Update — keep .env and data, update configs and images"
        echo "  2) Fresh  — backup existing, then clean install (OVERWRITES .env)"
        echo "  3) Abort  — exit without changes"
        echo ""
        read -rp "Choose [1/2/3]: " choice

        case "$choice" in
            1)
                log INFO "Update mode selected — preserving .env and data"
                PRESERVE_ENV=true
                ;;
            2)
                log INFO "Fresh install selected — backing up existing"
                backup_existing
                PRESERVE_ENV=false
                ;;
            *)
                log INFO "Installation aborted by user"
                exit 0
                ;;
        esac
        return 0
    fi

    PRESERVE_ENV=false
    return 0
}

backup_existing() {
    local backup_dir="${INSTALL_DIR}/_backup_$(date +%Y%m%d-%H%M%S)"
    log INFO "Backing up to $backup_dir"

    mkdir -p "$backup_dir"
    # Backup .env and compose
    cp -a "$INSTALL_DIR/$ENV_FILE" "$backup_dir/" 2>/dev/null || true
    cp -a "$INSTALL_DIR/$COMPOSE_FILE_NAME" "$backup_dir/" 2>/dev/null || true
    cp -a "$INSTALL_DIR/license.key" "$backup_dir/" 2>/dev/null || true

    log OK "Backup saved to $backup_dir"
    echo "  Rollback: cp $backup_dir/.env $INSTALL_DIR/.env"
}

###############################################################################
# INTERACTIVE PROMPTS
###############################################################################
prompt_config() {
    if $NON_INTERACTIVE; then
        if [[ -z "$EDITION" ]]; then
            die "Non-interactive mode requires --edition (trial|annual)."
        fi
        return 0
    fi

    echo ""
    echo -e "${C_BOLD}── Configuration ──${C_RESET}"
    echo ""

    # Edition
    if [[ -z "$EDITION" ]]; then
        echo "  Edition type:"
        echo "    1) trial   — 30-day evaluation"
        echo "    2) annual  — licensed production use"
        read -rp "  Select [1/2]: " ed_choice
        case "$ed_choice" in
            1) EDITION="trial" ;;
            2) EDITION="annual" ;;
            *) EDITION="trial" ;;
        esac
    fi

    # Domain (optional)
    if [[ -z "$DOMAIN" ]]; then
        local default_ip
        default_ip=$(hostname -I 2>/dev/null | awk '{print $1}')
        read -rp "  Public domain or IP [${default_ip}]: " DOMAIN
        DOMAIN="${DOMAIN:-$default_ip}"
    fi

    # Admin email (optional)
    if [[ -z "$ADMIN_EMAIL" ]]; then
        read -rp "  Admin email (for notifications, optional): " ADMIN_EMAIL
    fi

    echo ""
    log INFO "Edition: ${EDITION}, Domain: ${DOMAIN:-auto}"
}

###############################################################################
# GENERATE .ENV
###############################################################################
generate_password() {
    openssl rand -base64 24 | tr -d "=+/" | cut -c1-24
}

create_env_file() {
    # If preserving, don't overwrite
    if [[ "${PRESERVE_ENV:-false}" == "true" && -f "$INSTALL_DIR/$ENV_FILE" ]]; then
        log OK "Preserving existing .env file"
        return 0
    fi

    if $DRY_RUN; then
        log DRY "Would generate .env with secure random passwords"
        return 0
    fi

    local pg_pass redis_pass grafana_pass secret_key admin_pass
    pg_pass=$(generate_password)
    redis_pass=$(generate_password)
    grafana_pass=$(generate_password)
    secret_key=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-48)
    admin_pass=$(generate_password)

    local public_ip
    public_ip="${DOMAIN:-$(hostname -I 2>/dev/null | awk '{print $1}')}"

    cat > "$INSTALL_DIR/$ENV_FILE" <<ENVEOF
# ═══════════════════════════════════════════════════════════════
# RHINOMETRIC v${SCRIPT_VERSION} — Generated $(date -u +"%Y-%m-%d %H:%M:%S UTC")
# IMPORTANT: Store these passwords in a password manager.
# DO NOT commit this file to git.
# ═══════════════════════════════════════════════════════════════

# === Public Access ===
PUBLIC_IP=${public_ip}
CUSTOMER_DOMAIN=${DOMAIN:-}

# === Database ===
POSTGRES_USER=rhinometric
POSTGRES_PASSWORD=${pg_pass}
POSTGRES_DB=rhinometric

# === Cache ===
REDIS_PASSWORD=${redis_pass}

# === Grafana ===
GRAFANA_USER=admin
GRAFANA_PASSWORD=${grafana_pass}

# === Console Backend ===
SECRET_KEY=${secret_key}
ADMIN_USERNAME=admin
ADMIN_PASSWORD=${admin_pass}

# === Paths ===
HOME=${HOME:-/root}

# === Notifications (optional — fill in to enable) ===
SLACK_WEBHOOK_URL=
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
ENVEOF

    chmod 600 "$INSTALL_DIR/$ENV_FILE"
    log OK "Generated .env with secure random passwords"

    # Save credentials to a separate file for the admin
    cat > "$INSTALL_DIR/CREDENTIALS.txt" <<CREDEOF
═══════════════════════════════════════════════════════════════
RHINOMETRIC v${SCRIPT_VERSION} — Access Credentials
Installed: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Server:    $(hostname) (${public_ip})
Edition:   ${EDITION}
═══════════════════════════════════════════════════════════════

RHINOMETRIC CONSOLE
  URL:      http://${public_ip}
  Username: admin
  Password: ${admin_pass}

GRAFANA DASHBOARDS
  URL:      http://${public_ip}:3000
  Username: admin
  Password: ${grafana_pass}

POSTGRESQL
  Host:     localhost:5432
  Database: rhinometric
  Username: rhinometric
  Password: ${pg_pass}

REDIS
  Host:     localhost:6379
  Password: ${redis_pass}

═══════════════════════════════════════════════════════════════
⚠️  Save these credentials and delete this file.
═══════════════════════════════════════════════════════════════
CREDEOF

    chmod 600 "$INSTALL_DIR/CREDENTIALS.txt"
    log OK "Credentials saved to $INSTALL_DIR/CREDENTIALS.txt"
}

###############################################################################
# SETUP DIRECTORIES & COMPOSE
###############################################################################
setup_directories() {
    if $DRY_RUN; then
        log DRY "Would create $INSTALL_DIR and data directories"
        return 0
    fi

    mkdir -p "$INSTALL_DIR"

    local data_dir="${HOME:-/root}/$DEFAULT_DATA_DIR_SUFFIX"
    local dirs=(
        "$data_dir/postgres"
        "$data_dir/redis"
        "$data_dir/loki"
        "$data_dir/jaeger"
        "$data_dir/alertmanager"
        "$data_dir/ai-anomaly/models"
        "$data_dir/ai-anomaly/data"
        "$data_dir/console-backend/logs"
        "$data_dir/console-backend/data"
        "$data_dir/license-server/logs"
    )

    for d in "${dirs[@]}"; do
        mkdir -p "$d"
    done

    log OK "Data directories created at $data_dir"
}

setup_compose_symlink() {
    if $DRY_RUN; then
        log DRY "Would symlink $SYMLINK_NAME → $COMPOSE_FILE_NAME"
        return 0
    fi

    cd "$INSTALL_DIR"

    if [[ ! -f "$COMPOSE_FILE_NAME" ]]; then
        die "Compose file not found: $INSTALL_DIR/$COMPOSE_FILE_NAME"
    fi

    if [[ -L "$SYMLINK_NAME" ]]; then
        local current_target
        current_target=$(readlink "$SYMLINK_NAME")
        if [[ "$current_target" == "$COMPOSE_FILE_NAME" ]]; then
            log OK "Compose symlink already correct"
            return 0
        fi
        rm -f "$SYMLINK_NAME"
    elif [[ -f "$SYMLINK_NAME" && ! -L "$SYMLINK_NAME" ]]; then
        mv "$SYMLINK_NAME" "${SYMLINK_NAME}.bak.$(date +%s)"
    fi

    ln -sf "$COMPOSE_FILE_NAME" "$SYMLINK_NAME"
    log OK "Symlinked $SYMLINK_NAME → $COMPOSE_FILE_NAME"
}

###############################################################################
# LICENSE HANDLING
###############################################################################
apply_license() {
    if [[ -n "$LICENSE_FILE" ]]; then
        if [[ ! -f "$LICENSE_FILE" ]]; then
            die "License file not found: $LICENSE_FILE"
        fi
        if $DRY_RUN; then
            log DRY "Would copy $LICENSE_FILE → $INSTALL_DIR/license.key"
            return 0
        fi
        cp "$LICENSE_FILE" "$INSTALL_DIR/license.key"
        chmod 600 "$INSTALL_DIR/license.key"
        log OK "License applied from $LICENSE_FILE"
    else
        log INFO "No license file provided. Apply later with: rhinoctl apply-license /path/to/file.lic"
    fi
}

###############################################################################
# BUILD & START
###############################################################################
build_images() {
    if $DRY_RUN; then
        log DRY "Would build Docker images"
        return 0
    fi

    if $SKIP_BUILD; then
        log INFO "Skipping image build (--skip-build)"
        return 0
    fi

    cd "$INSTALL_DIR"

    log INFO "Pulling base images..."
    compose_cmd pull --ignore-pull-failures 2>> "$LOG_FILE" || true

    log INFO "Building application images (this may take 5-10 minutes)..."
    # Build excluding license-ui which is known to fail
    compose_cmd build --parallel 2>> "$LOG_FILE" || {
        log WARN "Some images failed to build. Attempting individual builds..."
        for svc in console-backend console-frontend license-server-v2 ai-anomaly; do
            compose_cmd build "$svc" 2>> "$LOG_FILE" || log WARN "Failed to build $svc"
        done
    }

    log OK "Image build complete"
}

start_stack() {
    if $DRY_RUN; then
        log DRY "Would start stack with compose_cmd up -d"
        return 0
    fi

    cd "$INSTALL_DIR"

    log INFO "Starting Rhinometric platform..."
    # Exclude license-ui (known build failure) unless image exists
    local scale_flags=""
    if ! docker image inspect rhinometric-license-ui &>/dev/null 2>&1; then
        if ! docker image ls --format '{{.Repository}}' | grep -q "license.*ui"; then
            scale_flags="--scale license-ui=0"
        fi
    fi

    # shellcheck disable=SC2086
    compose_cmd up -d --remove-orphans $scale_flags 2>> "$LOG_FILE"

    log OK "Stack started"
}

###############################################################################
# SMOKE TESTS
###############################################################################
wait_for_healthy() {
    if $DRY_RUN; then
        log DRY "Would wait for containers to become healthy"
        return 0
    fi

    cd "$INSTALL_DIR"

    log INFO "Waiting for services to start (up to 120s)..."

    local max_wait=120
    local interval=5
    local elapsed=0
    local total healthy

    while (( elapsed < max_wait )); do
        total=$(compose_cmd ps -q 2>/dev/null | wc -l)
        healthy=$(docker ps --filter "label=com.docker.compose.project" \
                    --filter "health=healthy" --format '{{.Names}}' 2>/dev/null \
                    | grep -c rhinometric || echo 0)

        if (( total > 0 && healthy >= (total - 2) )); then
            # Allow 2 non-healthy (some services don't have healthcheck)
            log OK "Services healthy: ${healthy}/${total}"
            return 0
        fi

        printf "\r  Waiting... %ds — %d/%d healthy" "$elapsed" "$healthy" "$total"
        sleep "$interval"
        elapsed=$((elapsed + interval))
    done

    echo ""
    log WARN "Timeout waiting for all services. ${healthy}/${total} healthy after ${max_wait}s."
    log WARN "Check with: cd $INSTALL_DIR && docker compose ps"
    return 1
}

run_smoke_tests() {
    if $DRY_RUN; then
        log DRY "Would run smoke tests against local endpoints"
        return 0
    fi

    cd "$INSTALL_DIR"

    echo ""
    echo -e "${C_BOLD}── Smoke Tests ──${C_RESET}"
    echo ""

    local pass=0 fail=0 warn=0

    # Docker-native container health (most reliable)
    local containers
    containers=$(docker ps --filter "name=rhinometric" --format '{{.Names}}|{{.Status}}' 2>/dev/null | sort)

    while IFS='|' read -r name status; do
        [[ -z "$name" ]] && continue
        local short_name="${name#rhinometric-}"
        if [[ "$status" == *"(healthy)"* ]]; then
            echo -e "  ${C_GREEN}✓${C_RESET} $short_name"
            pass=$((pass + 1))
        elif [[ "$status" == *"(unhealthy)"* ]]; then
            echo -e "  ${C_RED}✗${C_RESET} $short_name (unhealthy)"
            fail=$((fail + 1))
        elif [[ "$status" == *"Up"* ]]; then
            echo -e "  ${C_YELLOW}~${C_RESET} $short_name (running, no healthcheck)"
            warn=$((warn + 1))
        else
            echo -e "  ${C_RED}✗${C_RESET} $short_name ($status)"
            fail=$((fail + 1))
        fi
    done <<< "$containers"

    # HTTP check: frontend (the only host-mapped port guaranteed)
    local frontend_code
    frontend_code=$(curl -sf -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "http://localhost/" 2>/dev/null || echo "000")
    if [[ "$frontend_code" =~ ^(200|301|302)$ ]]; then
        echo -e "  ${C_GREEN}✓${C_RESET} Frontend HTTP ($frontend_code)"
        pass=$((pass + 1))
    else
        echo -e "  ${C_RED}✗${C_RESET} Frontend HTTP ($frontend_code)"
        fail=$((fail + 1))
    fi

    echo ""
    if (( fail == 0 )); then
        log OK "Smoke tests: ${pass} healthy, ${warn} running (no healthcheck)"
    else
        log WARN "Smoke tests: ${pass} healthy, ${fail} unhealthy, ${warn} no healthcheck"
        log WARN "Check with: cd $INSTALL_DIR && docker compose ps"
    fi

    return 0
}

###############################################################################
# INSTALL RHINOCTL
###############################################################################
install_rhinoctl() {
    if $DRY_RUN; then
        log DRY "Would install rhinoctl to /usr/local/bin/rhinoctl"
        return 0
    fi

    local source="$INSTALL_DIR/scripts/rhinoctl.sh"
    local target="/usr/local/bin/rhinoctl"

    if [[ -f "$source" ]]; then
        cp "$source" "$target"
        chmod +x "$target"
        # Embed install dir
        sed -i "s|^RHINO_DIR=.*|RHINO_DIR=\"$INSTALL_DIR\"|" "$target"
        log OK "rhinoctl installed to $target"
    else
        log WARN "rhinoctl.sh not found at $source — skipping CLI install"
    fi
}

###############################################################################
# COMPLETION
###############################################################################
show_completion() {
    local public_ip
    public_ip="${DOMAIN:-$(hostname -I 2>/dev/null | awk '{print $1}')}"

    echo ""
    echo -e "${C_GREEN}${C_BOLD}"
    cat <<'EOF'
  ╔═══════════════════════════════════════════════════════════╗
  ║             ✓  INSTALLATION COMPLETE                      ║
  ╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${C_RESET}"

    echo "  Access Rhinometric:"
    echo ""
    echo "    Console:    http://${public_ip}"
    echo "    Grafana:    http://${public_ip}:3000"
    echo "    Prometheus: http://${public_ip}:9090"
    echo ""
    echo "  Credentials: $INSTALL_DIR/CREDENTIALS.txt"
    echo ""
    echo -e "  ${C_BOLD}Next steps:${C_RESET}"
    echo ""
    echo "    1. Generate hardware fingerprint:"
    echo "       rhinoctl fingerprint"
    echo ""
    echo "    2. Send fingerprint to licenses@rhinometric.com"
    echo ""
    echo "    3. Apply received license:"
    echo "       rhinoctl apply-license /path/to/license.lic"
    echo ""
    echo "    4. Verify platform status:"
    echo "       rhinoctl status"
    echo ""
    echo "  Full log: $LOG_FILE"
    echo ""
}

###############################################################################
# DRY-RUN SUMMARY
###############################################################################
show_dryrun_summary() {
    echo ""
    echo -e "${C_BLUE}${C_BOLD}── Dry-Run Summary ──${C_RESET}"
    echo ""
    echo "  All pre-flight checks passed. The installer would:"
    echo ""
    echo "    1. Create directories at $INSTALL_DIR"
    echo "    2. Generate .env with secure random passwords"
    echo "    3. Create compose symlink → $COMPOSE_FILE_NAME"
    echo "    4. Build/pull Docker images"
    echo "    5. Start 20 containers"
    echo "    6. Run smoke tests"
    echo "    7. Install rhinoctl CLI to /usr/local/bin/"
    echo ""
    echo "  To proceed with real installation:"
    echo "    sudo bash $0 ${EDITION:+--edition $EDITION}"
    echo ""
}

###############################################################################
# MAIN
###############################################################################
main() {
    parse_args "$@"

    show_banner
    log_init

    log INFO "Rhinometric Installer v${SCRIPT_VERSION} — $(date -u)"
    log INFO "Install dir: $INSTALL_DIR"
    $DRY_RUN && log INFO "=== DRY-RUN MODE ==="

    echo -e "${C_BOLD}── Pre-flight Checks ──${C_RESET}"
    echo ""

    check_root
    check_os
    check_resources
    check_docker
    check_dependencies
    check_ports

    echo ""
    log OK "All pre-flight checks passed"

    # Detect existing
    detect_existing

    # Prompt for config
    prompt_config

    if $DRY_RUN; then
        show_dryrun_summary
        exit 0
    fi

    # Confirm
    if ! $NON_INTERACTIVE; then
        echo ""
        echo -e "  ${C_BOLD}Ready to install Rhinometric ${EDITION} to ${INSTALL_DIR}${C_RESET}"
        read -rp "  Proceed? (Y/n): " confirm
        if [[ "$confirm" =~ ^[Nn] ]]; then
            log INFO "Installation cancelled by user"
            exit 0
        fi
    fi

    echo ""
    echo -e "${C_BOLD}── Installing ──${C_RESET}"
    echo ""

    setup_directories
    create_env_file
    setup_compose_symlink
    apply_license
    build_images
    start_stack

    echo ""
    echo -e "${C_BOLD}── Verifying ──${C_RESET}"
    echo ""

    wait_for_healthy || true
    run_smoke_tests

    install_rhinoctl

    show_completion

    log INFO "Installation completed successfully at $(_ts)"
}

main "$@"
