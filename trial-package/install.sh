#!/usr/bin/env bash
###############################################################################
# RHINOMETRIC TRIAL v2.6.0 — One-Command Installer
# Usage:
#   sudo bash install.sh                      # Interactive online install
#   sudo bash install.sh --non-interactive    # Unattended
#   sudo bash install.sh --offline            # Use pre-packaged images
#   sudo bash install.sh --license /path.lic  # Install with license file
###############################################################################
set -euo pipefail

readonly INST_VERSION="2.6.0"
readonly INSTALL_DIR="/opt/rhinometric"
readonly DATA_DIR="${HOME}/rhinometric_data_v2.5"
readonly LOG_FILE="/var/log/rhinometric-install.log"
readonly COMPOSE_FILE="docker-compose-trial.yml"

# Colors
R="\033[0m"; G="\033[0;32m"; B="\033[0;34m"; Y="\033[1;33m"; RD="\033[0;31m"; BD="\033[1m"

# Defaults
MODE="online"
NON_INTERACTIVE=false
LICENSE_FILE=""
DOMAIN=""
SKIP_BUILD=false

###############################################################################
# HELPERS
###############################################################################
_ts() { date -u +"%Y-%m-%d %H:%M:%S UTC"; }

log() {
    local lvl="$1"; shift
    echo "[$(_ts)] [$lvl] $*" >> "$LOG_FILE" 2>/dev/null || true
    case "$lvl" in
        OK)    echo -e "${G}[  OK]${R}  $*" ;;
        INFO)  echo -e "${G}[INFO]${R}  $*" ;;
        WARN)  echo -e "${Y}[WARN]${R}  $*" ;;
        ERR)   echo -e "${RD}[ERR!]${R}  $*" ;;
        STEP)  echo -e "${B}${BD}[STEP]${R}  $*" ;;
    esac
}

die() { log ERR "$*"; echo ""; echo "Installation aborted. See $LOG_FILE"; exit 1; }

generate_password() { openssl rand -base64 24 | tr -d "=+/" | cut -c1-24; }

###############################################################################
# PARSE ARGS
###############################################################################
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --offline)         MODE="offline" ;;
            --online)          MODE="online" ;;
            --non-interactive) NON_INTERACTIVE=true ;;
            --license)         LICENSE_FILE="$2"; shift ;;
            --domain)          DOMAIN="$2"; shift ;;
            --skip-build)      SKIP_BUILD=true ;;
            -h|--help)         show_help; exit 0 ;;
            *) die "Unknown option: $1" ;;
        esac
        shift
    done
}

show_help() {
    cat << 'HELPEOF'
Rhinometric Trial Installer v2.6.0

Usage: sudo bash install.sh [OPTIONS]

Options:
  --online            Install using internet (default)
  --offline           Use pre-packaged Docker images
  --non-interactive   Skip all prompts
  --license FILE      Apply license file during install
  --domain DOMAIN     Set domain (default: auto-detect IP)
  --skip-build        Skip Docker image builds (use existing)
  -h, --help          Show this help

Examples:
  sudo bash install.sh
  sudo bash install.sh --offline --non-interactive
  sudo bash install.sh --license /tmp/client.lic --domain monitor.acme.com
HELPEOF
}

###############################################################################
# BANNER
###############################################################################
show_banner() {
    echo -e "${B}${BD}"
    echo "  ╔═══════════════════════════════════════════════════════╗"
    echo "  ║   RHINOMETRIC — Observability Platform    ║"
    echo "  ║   Trial Installer v${INST_VERSION}                             ║"
    echo "  ╚═══════════════════════════════════════════════════════╝"
    echo -e "${R}"
}

###############################################################################
# PHASE 1: PRE-FLIGHT CHECKS
###############################################################################
preflight() {
    log STEP "Phase 1: Pre-flight checks..."

    # Root check
    if [[ $EUID -ne 0 ]]; then
        die "This installer must be run as root (use sudo)"
    fi
    log OK "Running as root"

    # OS check
    if [[ ! -f /etc/os-release ]]; then
        die "Cannot detect OS (no /etc/os-release)"
    fi
    source /etc/os-release
    if [[ "$ID" != "ubuntu" ]] && [[ "$ID" != "debian" ]]; then
        die "Unsupported OS: $ID. Requires Ubuntu 22.04/24.04 or Debian 12"
    fi
    log OK "OS: $PRETTY_NAME"

    # CPU check
    local cpus
    cpus=$(nproc)
    if [[ $cpus -lt 2 ]]; then
        die "Minimum 2 CPU cores required (found: $cpus)"
    fi
    log OK "CPUs: $cpus"

    # RAM check
    local ram_mb
    ram_mb=$(awk '/MemTotal/ {printf "%d", $2/1024}' /proc/meminfo)
    if [[ $ram_mb -lt 7000 ]]; then
        die "Minimum 7 GB RAM required (found: ${ram_mb}MB)"
    fi
    log OK "RAM: ${ram_mb}MB"

    # Disk check
    local disk_gb
    disk_gb=$(df -BG / | awk 'NR==2 {gsub("G",""); print $4}')
    if [[ $disk_gb -lt 30 ]]; then
        die "Minimum 30 GB free disk required (found: ${disk_gb}GB)"
    fi
    log OK "Disk free: ${disk_gb}GB"

    echo ""
    log OK "All pre-flight checks passed"
}

###############################################################################
# PHASE 2: INSTALL SYSTEM DEPENDENCIES
###############################################################################
install_deps() {
    log STEP "Phase 2: Installing system dependencies..."

    local pkgs=(curl git jq openssl ca-certificates gnupg lsb-release)
    local to_install=()

    for pkg in "${pkgs[@]}"; do
        if ! dpkg -l "$pkg" &>/dev/null; then
            to_install+=("$pkg")
        fi
    done

    if [[ ${#to_install[@]} -gt 0 ]]; then
        apt-get update -qq >> "$LOG_FILE" 2>&1
        apt-get install -y -qq "${to_install[@]}" >> "$LOG_FILE" 2>&1
        log OK "Installed: ${to_install[*]}"
    else
        log OK "All dependencies already installed"
    fi
}

###############################################################################
# PHASE 3: INSTALL DOCKER
###############################################################################
install_docker() {
    log STEP "Phase 3: Installing Docker..."

    if command -v docker &>/dev/null; then
        local dver
        dver=$(docker --version 2>/dev/null)
        log OK "Docker already installed: $dver"
    else
        log INFO "Installing Docker CE..."
        curl -fsSL https://get.docker.com | bash >> "$LOG_FILE" 2>&1
        log OK "Docker installed"
    fi

    # Ensure docker service is running
    systemctl enable docker --now >> "$LOG_FILE" 2>&1 || true
    log OK "Docker service running"

    # Add current SUDO_USER to docker group
    if [[ -n "${SUDO_USER:-}" ]]; then
        usermod -aG docker "$SUDO_USER" 2>/dev/null || true
    fi

    # Verify compose
    if docker compose version &>/dev/null; then
        log OK "Docker Compose: $(docker compose version --short 2>/dev/null)"
    else
        die "Docker Compose plugin not found"
    fi
}

###############################################################################
# PHASE 4: SETUP INSTALL DIRECTORY
###############################################################################
setup_directory() {
    log STEP "Phase 4: Setting up installation directory..."

    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd)"

    if [[ -d "$INSTALL_DIR/.git" ]]; then
        log OK "Installation directory already exists: $INSTALL_DIR"
    elif [[ -f "$script_dir/docker-compose-trial.yml" ]]; then
        # We're running from the package — copy files
        if [[ "$script_dir" != "$INSTALL_DIR" ]]; then
            mkdir -p "$INSTALL_DIR"
            cp -a "$script_dir"/* "$INSTALL_DIR/" 2>/dev/null || true
            cp -a "$script_dir"/.env* "$INSTALL_DIR/" 2>/dev/null || true
            cp -a "$script_dir"/.git* "$INSTALL_DIR/" 2>/dev/null || true
            log OK "Copied package to $INSTALL_DIR"
        fi
    elif [[ -f "$INSTALL_DIR/docker-compose-trial.yml" ]]; then
        log OK "Compose already at $INSTALL_DIR"
    else
        die "No docker-compose-trial.yml found. Run from the trial package directory."
    fi
}

###############################################################################
# PHASE 5: CREATE DATA DIRECTORIES
###############################################################################
setup_data_dirs() {
    log STEP "Phase 5: Creating data directories..."

    local real_home
    if [[ -n "${SUDO_USER:-}" ]]; then
        real_home=$(getent passwd "$SUDO_USER" | cut -d: -f6)
    else
        real_home="$HOME"
    fi
    local data_base="${real_home}/rhinometric_data_v2.5"

    local dirs=(
        "${data_base}/postgres"
        "${data_base}/redis"
        "${data_base}/grafana"
        "${data_base}/prometheus"
        "${data_base}/loki"
        "${data_base}/jaeger"
        "${data_base}/victoria-metrics"
        "${data_base}/alertmanager"
        "${data_base}/ai-anomaly/models"
        "${data_base}/ai-anomaly/logs"
        "${data_base}/ai-anomaly/data"
        "${data_base}/console-backend/logs"
        "${data_base}/console-backend/uploads"
        "${data_base}/license-server/logs"
        "${data_base}/nginx/logs"
    )

    for d in "${dirs[@]}"; do
        mkdir -p "$d"
    done

    # Fix permissions
    chmod -R 777 "${data_base}/ai-anomaly" 2>/dev/null || true
    chown -R 472:472 "${data_base}/grafana" 2>/dev/null || true
    chown -R 65534:65534 "${data_base}/prometheus" 2>/dev/null || true

    if [[ -n "${SUDO_USER:-}" ]]; then
        chown -R "${SUDO_USER}:${SUDO_USER}" "${data_base}" 2>/dev/null || true
        chown 472:472 "${data_base}/grafana" 2>/dev/null || true
        chown 65534:65534 "${data_base}/prometheus" 2>/dev/null || true
    fi

    log OK "Data directories created at $data_base"
}

###############################################################################
# PHASE 6: GENERATE .env
###############################################################################
generate_env() {
    log STEP "Phase 6: Generating environment configuration..."

    cd "$INSTALL_DIR"

    # If .env exists with real passwords, preserve it
    if [[ -f ".env" ]]; then
        if ! grep -q "CHANGE_ME\|changeme\|your_password" .env 2>/dev/null; then
            log OK "Existing .env with custom passwords — preserving"
            return 0
        fi
    fi

    local pg_pass redis_pass grafana_pass secret_key admin_pass license_key jwt_secret
    pg_pass=$(generate_password)
    redis_pass=$(generate_password)
    grafana_pass=$(generate_password)
    secret_key=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-48)
    admin_pass=$(generate_password)
    license_key=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    jwt_secret=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)

    local public_ip="${DOMAIN:-$(hostname -I 2>/dev/null | awk '{print $1}')}"

    local real_home
    if [[ -n "${SUDO_USER:-}" ]]; then
        real_home=$(getent passwd "$SUDO_USER" | cut -d: -f6)
    else
        real_home="$HOME"
    fi

    cat > .env << ENVEOF
# RHINOMETRIC v${INST_VERSION} — Auto-generated $(_ts)
# DO NOT commit this file to git.

# === Public Access ===
PUBLIC_IP=${public_ip}
DOMAIN=${public_ip}
CUSTOMER_DOMAIN=${DOMAIN:-${public_ip}}

# === Database ===
POSTGRES_USER=rhinometric
POSTGRES_PASSWORD=${pg_pass}
POSTGRES_DB=rhinometric
DB_NAME=rhinometric

# === Cache ===
REDIS_PASSWORD=${redis_pass}

# === Grafana ===
GRAFANA_USER=admin
GRAFANA_PASSWORD=${grafana_pass}
GRAFANA_SECRET_KEY=${secret_key}
GRAFANA_DOMAIN=${public_ip}

# === Console Backend ===
SECRET_KEY=${secret_key}
JWT_SECRET=${jwt_secret}
ADMIN_USERNAME=admin
ADMIN_PASSWORD=${admin_pass}
API_VERSION=${INST_VERSION}

# === Bootstrap Admin (used by backend auto-init) ===
RHINO_ADMIN_USER=admin
RHINO_ADMIN_PASSWORD=admin123
RHINO_ADMIN_EMAIL=admin@rhinometric.local

# === License ===
LICENSE_ENCRYPTION_KEY=${license_key}

# === Paths ===
HOME=${real_home}

# === Environment ===
ENVIRONMENT=production
DEBUG=false

# === SSL ===
SSL_EMAIL=admin@rhinometric.com

# === Mail (optional) ===
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
MAIL_USERNAME=
MAIL_PASSWORD=

# === Slack (optional) ===
SLACK_WEBHOOK_URL=
ENVEOF

    chmod 600 .env
    log OK "Generated .env with secure random passwords"

    # Save credentials
    cat > CREDENTIALS.txt << CREDEOF
════════════════════════════════════════════════════════════
RHINOMETRIC v${INST_VERSION} — Access Credentials
Installed: $(_ts)
Server: $(hostname) (${public_ip})
Edition: trial (30 days)
════════════════════════════════════════════════════════════

RHINOMETRIC CONSOLE
  URL:      http://${public_ip}
  Username: admin
  Password: admin123  (default — change after first login)

GRAFANA DASHBOARDS
  URL:      http://${public_ip}/grafana/
  Username: admin
  Password: ${grafana_pass}

POSTGRESQL
  Host:     postgres:5432 (container-internal)
  Database: rhinometric
  Username: rhinometric
  Password: ${pg_pass}

REDIS
  Host:     redis:6379 (container-internal)
  Password: ${redis_pass}

JWT SECRET: ${jwt_secret}
════════════════════════════════════════════════════════════
  SAVE THESE IN A PASSWORD MANAGER. Then: rm CREDENTIALS.txt
════════════════════════════════════════════════════════════
CREDEOF

    chmod 600 CREDENTIALS.txt
    log OK "Credentials saved to CREDENTIALS.txt"
}

###############################################################################
# PHASE 7: LOAD/BUILD IMAGES
###############################################################################
load_images() {
    log STEP "Phase 7: Loading Docker images (mode: $MODE)..."

    cd "$INSTALL_DIR"

    if [[ "$MODE" == "offline" ]]; then
        # Offline mode: load from saved tar files
        if [[ -d "images" ]]; then
            local img_count
            img_count=$(find images -name "*.tar" 2>/dev/null | wc -l)
            if [[ $img_count -eq 0 ]]; then
                die "Offline mode but no images/*.tar found"
            fi
            log INFO "Loading $img_count pre-packaged images..."
            for tarfile in images/*.tar; do
                local basename
                basename=$(basename "$tarfile" .tar)
                printf "  Loading %-45s" "$basename..."
                if docker load < "$tarfile" >> "$LOG_FILE" 2>&1; then
                    echo -e "${G}OK${R}"
                else
                    echo -e "${RD}FAIL${R}"
                    log WARN "Failed to load $tarfile"
                fi
            done
            log OK "All images loaded from package"
        else
            die "Offline mode requires images/ directory with .tar files"
        fi
    else
        # Online mode: pull + build
        log INFO "Pulling public images..."
        docker compose -f "$COMPOSE_FILE" --env-file .env pull --ignore-pull-failures >> "$LOG_FILE" 2>&1 || true
        log OK "Public images pulled"

        if ! $SKIP_BUILD; then
            log INFO "Building application images (this may take 5-15 minutes)..."
            local build_services=("license-server-v2" "rhinometric-ai-anomaly" "rhinometric-console-backend" "rhinometric-console-frontend" "license-ui")
            for svc in "${build_services[@]}"; do
                printf "  Building %-45s" "$svc..."
                if docker compose -f "$COMPOSE_FILE" --env-file .env build "$svc" >> "$LOG_FILE" 2>&1; then
                    echo -e "${G}OK${R}"
                else
                    echo -e "${Y}SKIP${R}"
                    log WARN "Failed to build $svc"
                fi
            done
            log OK "Image build complete"
        else
            log OK "Skipping builds (--skip-build)"
        fi
    fi
}

###############################################################################
# PHASE 8: APPLY LICENSE
###############################################################################
apply_license() {
    log STEP "Phase 8: License configuration..."

    cd "$INSTALL_DIR"

    if [[ -n "$LICENSE_FILE" ]]; then
        if [[ -f "$LICENSE_FILE" ]]; then
            cp "$LICENSE_FILE" "${INSTALL_DIR}/license.key"
            chmod 600 "${INSTALL_DIR}/license.key"
            log OK "License applied from $LICENSE_FILE"
        else
            log WARN "License file not found: $LICENSE_FILE"
        fi
    elif [[ -f "${INSTALL_DIR}/license.key" ]]; then
        log OK "Existing license.key found"
    else
        log INFO "No license file provided. Platform will run in trial mode."
        log INFO "Use 'rhinoctl fingerprint' to get HWID, then 'rhinoctl apply-license /path/to/file.lic'"
    fi
}

###############################################################################
# PHASE 9: START STACK
###############################################################################
start_stack() {
    log STEP "Phase 9: Starting Rhinometric platform..."

    cd "$INSTALL_DIR"

    # Ensure nginx htpasswd exists
    mkdir -p nginx
    if [[ ! -f nginx/.htpasswd ]]; then
        echo 'proxy-admin:$apr1$sIOJfb7j$a9Xjf3VxEuyBeTJu/NRTs/' > nginx/.htpasswd
    fi

    log INFO "Starting 21 services..."
    docker compose -f "$COMPOSE_FILE" --env-file .env up -d --remove-orphans >> "$LOG_FILE" 2>&1 || {
        log WARN "Some services may have failed to start"
    }

    log OK "Stack started"
}

###############################################################################
# PHASE 10: HEALTH CHECKS
###############################################################################
health_check() {
    log STEP "Phase 10: Verifying platform health..."

    cd "$INSTALL_DIR"

    log INFO "Waiting for services to initialize (up to 120s)..."
    local max_wait=120 interval=10 elapsed=0

    while [[ $elapsed -lt $max_wait ]]; do
        local running healthy
        running=$(docker ps --filter "name=rhinometric" --format '{{.Names}}' 2>/dev/null | wc -l)
        healthy=$(docker ps --filter "name=rhinometric" --filter "health=healthy" --format '{{.Names}}' 2>/dev/null | wc -l)

        printf "\r  Waiting... %3ds — %d running, %d healthy  " "$elapsed" "$running" "$healthy"

        if [[ $running -ge 10 ]] && [[ $healthy -ge 6 ]]; then
            echo ""
            log OK "Platform healthy: ${healthy}/${running} services ready"
            break
        fi

        sleep "$interval"
        elapsed=$((elapsed + interval))
    done

    if [[ $elapsed -ge $max_wait ]]; then
        echo ""
        log WARN "Timeout: not all services healthy yet. Run 'rhinoctl health' to check."
    fi

    # Service status
    echo ""
    echo -e "${BD}── Service Status ──${R}"
    echo ""
    docker ps --filter "name=rhinometric" --format '{{.Names}}|{{.Status}}' 2>/dev/null | sort | while IFS='|' read -r name status; do
        [[ -z "$name" ]] && continue
        local short="${name#rhinometric-}"
        if echo "$status" | grep -q "(healthy)"; then
            echo -e "  ${G}✓${R} ${short}"
        elif echo "$status" | grep -q "Up"; then
            echo -e "  ${Y}~${R} ${short} (starting)"
        else
            echo -e "  ${RD}✗${R} ${short} (${status})"
        fi
    done

    # HTTP check
    echo ""
    local http_code
    http_code=$(curl -sf -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "http://localhost/" 2>/dev/null || echo "000")
    if echo "$http_code" | grep -qE "^(200|301|302)$"; then
        echo -e "  ${G}✓${R} Frontend HTTP: ${http_code}"
    else
        echo -e "  ${Y}~${R} Frontend HTTP: ${http_code} (may still be starting)"
    fi
    echo ""
}

###############################################################################
# PHASE 11: INSTALL RHINOCTL
###############################################################################
install_rhinoctl() {
    log STEP "Phase 11: Installing management CLI..."

    cd "$INSTALL_DIR"

    if [[ -f "rhinoctl" ]]; then
        cp rhinoctl /usr/local/bin/rhinoctl
        chmod +x /usr/local/bin/rhinoctl
        sed -i "s|^RHINO_DIR=.*|RHINO_DIR=\"${INSTALL_DIR}\"|" /usr/local/bin/rhinoctl
        log OK "rhinoctl installed to /usr/local/bin/rhinoctl"
    elif [[ -f "scripts/rhinoctl" ]]; then
        cp scripts/rhinoctl /usr/local/bin/rhinoctl
        chmod +x /usr/local/bin/rhinoctl
        sed -i "s|^RHINO_DIR=.*|RHINO_DIR=\"${INSTALL_DIR}\"|" /usr/local/bin/rhinoctl
        log OK "rhinoctl installed to /usr/local/bin/rhinoctl"
    else
        log WARN "rhinoctl not found in package — skipping CLI install"
    fi
}

###############################################################################
# PHASE 12: COMPLETION
###############################################################################
show_completion() {
    local public_ip="${DOMAIN:-$(hostname -I 2>/dev/null | awk '{print $1}')}"

    echo -e "${G}${BD}"
    echo "  ╔═══════════════════════════════════════════════════════╗"
    echo "  ║           ✓  INSTALLATION COMPLETE!                  ║"
    echo "  ╚═══════════════════════════════════════════════════════╝"
    echo -e "${R}"

    echo "  Access Rhinometric:"
    echo ""
    echo "    Console:    http://${public_ip}"
    echo "    Grafana:    http://${public_ip}/grafana/"
    echo ""
    echo "  Credentials:  ${INSTALL_DIR}/CREDENTIALS.txt"
    echo ""
    echo -e "  ${BD}Next steps:${R}"
    echo "    1. rhinoctl fingerprint        # Get hardware ID"
    echo "    2. Send HWID to licenses@rhinometric.com"
    echo "    3. rhinoctl apply-license /path/to/file.lic"
    echo "    4. rhinoctl health             # Verify"
    echo ""
    # Generate machine fingerprint
    local fingerprint=""
    if command -v rhinoctl &>/dev/null; then
        fingerprint=$(rhinoctl fingerprint 2>/dev/null | grep -oP "HWID: \K.*" || echo "")
    fi
    if [[ -z "$fingerprint" ]]; then
        fingerprint=$(cat /etc/machine-id 2>/dev/null || echo "unknown")
    fi

    echo "  ── Machine Fingerprint ──"
    echo "    ${fingerprint}"
    echo ""
    echo "  ── Next Steps ──"
    echo "    1. Copy the fingerprint above"
    echo "    2. Send to licenses@rhinometric.com to get your trial license"
    echo "    3. rhinoctl apply-license /path/to/file.lic"
    echo ""
    echo "  ── Default Login ──"
    echo "    Username: admin"
    echo "    Password: admin123  (change immediately after login!)"
    echo ""
    echo "  Management:   rhinoctl help"
    echo "  Full log:     ${LOG_FILE}"
    echo ""
}

###############################################################################
# MAIN
###############################################################################
main() {
    parse_args "$@"
    show_banner

    mkdir -p "$(dirname "$LOG_FILE")"
    echo "=== Rhinometric Trial Installer v${INST_VERSION} started at $(_ts) ===" >> "$LOG_FILE"
    log INFO "Mode: $MODE | Non-interactive: $NON_INTERACTIVE"

    # Phase 1: Pre-flight
    preflight

    # Confirm
    if ! $NON_INTERACTIVE; then
        echo ""
        echo -e "  ${BD}Ready to install Rhinometric Trial to ${INSTALL_DIR}${R}"
        echo "  Mode: $MODE | This will install Docker, build/load images, start 21 services."
        echo "  Estimated time: 5-15 minutes."
        echo ""
        read -rp "  Proceed? (Y/n): " confirm
        if [[ "$confirm" =~ ^[Nn] ]]; then
            echo "  Installation cancelled."
            exit 0
        fi
    fi

    echo ""

    # Phases 2-11
    install_deps
    install_docker
    setup_directory
    setup_data_dirs
    generate_env
    load_images
    apply_license
    start_stack
    health_check
    install_rhinoctl

    # Phase 12
    show_completion

    log INFO "Installation completed at $(_ts)"
}

main "$@"
