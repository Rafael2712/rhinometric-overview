#!/usr/bin/env bash
###############################################################################
# RHINOMETRIC v2.6.0 — All-in-One Bootstrap Installer
# From bare Ubuntu to running platform in ONE command
#
# Usage:
#   sudo bash rhinometric-bootstrap.sh                  # Interactive
#   sudo bash rhinometric-bootstrap.sh --dry-run        # Validate only
#   sudo bash rhinometric-bootstrap.sh --non-interactive --edition trial
#   sudo bash rhinometric-bootstrap.sh --edition trial \
#       --github-user USER --github-token ghp_xxx
#
# What this script does (12 phases):
#   1.  Pre-flight checks (OS, CPU ≥ 2, RAM ≥ 8 GB, disk ≥ 50 GB)
#   2.  Installs system deps (curl, git, jq, openssl)
#   3.  Installs Docker CE + Docker Compose plugin
#   4.  Clones Rhinometric repo from GitHub (correct branch)
#   5.  Creates persistent data directories
#   6.  Generates .env with cryptographically random passwords
#   7.  Configures Docker Compose symlink + nginx
#   8.  Builds application Docker images (backend, frontend, AI, etc.)
#   9.  Starts the full 21-service stack
#  10.  Runs health checks and smoke tests
#  11.  Installs rhinoctl CLI management tool
#  12.  Outputs credentials and access URLs
#
# Supports: Ubuntu 22.04 / 24.04, Debian 12
# Requirements: Root access, 4+ CPU, 8+ GB RAM, 50+ GB disk, internet
###############################################################################
set -Eeuo pipefail

readonly SCRIPT_VERSION="2.6.0"
readonly SCRIPT_DATE="2026-02-25"
readonly LOG_FILE="/var/log/rhinometric-install.log"
readonly DEFAULT_INSTALL_DIR="/opt/rhinometric"
readonly REPO_URL="https://github.com/Rafael2712/mi-proyecto.git"
readonly REPO_BRANCH="feature/use-direct-grafana-links"
readonly COMPOSE_FILE="docker-compose-v2.5.0-SECURE.yml"
readonly SYMLINK_NAME="docker-compose.yml"
readonly DATA_DIR_SUFFIX="rhinometric_data_v2.5"
readonly MIN_RAM_MB=7500
readonly MIN_DISK_GB=50
readonly MIN_CPU=2

# ─── Colours ────────────────────────────────────────────────────────────────
C_RESET="\033[0m"; C_GREEN="\033[0;32m"; C_BLUE="\033[0;34m"
C_YELLOW="\033[1;33m"; C_RED="\033[0;31m"; C_BOLD="\033[1m"

# ─── CLI Defaults ──────────────────────────────────────────────────────────
INSTALL_DIR="$DEFAULT_INSTALL_DIR"
EDITION=""
LICENSE_FILE=""
NON_INTERACTIVE=false
DRY_RUN=false
SKIP_BUILD=false
DOMAIN=""
GITHUB_USER=""
GITHUB_TOKEN=""
PRESERVE_ENV=false

###############################################################################
# LOGGING
###############################################################################
_ts() { date -u +"%Y-%m-%d %H:%M:%S UTC"; }

log_init() {
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "=== Rhinometric Bootstrap v${SCRIPT_VERSION} started at $(_ts) ===" >> "$LOG_FILE"
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
        DRY)   echo -e "${C_BLUE}[ DRY]${C_RESET}  $msg" ;;
        STEP)  echo -e "${C_BLUE}${C_BOLD}[STEP]${C_RESET}  $msg" ;;
    esac
}

die() {
    log ERROR "$*"
    echo ""
    echo "Installation aborted. See $LOG_FILE"
    exit 1
}

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
  ║           All-in-One Bootstrap Installer                  ║
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
            --domain)            DOMAIN="$2"; shift 2 ;;
            --github-user)       GITHUB_USER="$2"; shift 2 ;;
            --github-token)      GITHUB_TOKEN="$2"; shift 2 ;;
            -h|--help)           usage; exit 0 ;;
            *)                   die "Unknown option: $1. Use --help." ;;
        esac
    done
}

usage() {
    cat <<EOF
Rhinometric All-in-One Bootstrap Installer v${SCRIPT_VERSION}

Installs EVERYTHING from a bare Ubuntu server: Docker, Git, dependencies,
the platform code, builds images, starts services, and installs CLI tools.

Usage: sudo bash $0 [OPTIONS]

Options:
  --install-dir DIR       Installation directory (default: /opt/rhinometric)
  --edition TYPE          Edition: trial | annual (prompted if omitted)
  --license-file FILE     Path to .lic / .key file (optional)
  --non-interactive       Run without prompts (requires --edition)
  --dry-run               Validate system without making changes
  --skip-build            Skip docker image builds
  --domain DOMAIN         Public domain (defaults to server IP)
  --github-user USER      GitHub username (for private repo)
  --github-token TOKEN    GitHub PAT token (for private repo)
  -h, --help              Show this help

Examples:
  # Interactive install (prompts for everything)
  sudo bash $0

  # Non-interactive trial
  sudo bash $0 --non-interactive --edition trial

  # With GitHub auth (private repo)
  sudo bash $0 --edition trial --github-user myuser --github-token ghp_xxx

Post-install commands:
  rhinoctl status          Show platform status
  rhinoctl fingerprint     Generate hardware ID for licensing
  rhinoctl apply-license   Apply a license file
  rhinoctl health          Detailed health check
  rhinoctl logs [service]  View service logs
EOF
}

###############################################################################
# PHASE 1: PRE-FLIGHT CHECKS
###############################################################################
check_root() {
    if [[ $EUID -ne 0 ]]; then
        die "Must run as root. Use: sudo bash $0"
    fi
    log OK "Running as root"
}

check_os() {
    if [[ ! -f /etc/os-release ]]; then
        die "Cannot detect OS (/etc/os-release missing)"
    fi
    # shellcheck disable=SC1091
    . /etc/os-release
    case "$ID" in
        ubuntu)
            if [[ "${VERSION_ID}" != "22.04" ]] && [[ "${VERSION_ID}" != "24.04" ]]; then
                log WARN "Ubuntu ${VERSION_ID} — tested on 22.04/24.04"
            else
                log OK "Ubuntu ${VERSION_ID}"
            fi
            ;;
        debian)
            log WARN "Debian ${VERSION_ID} — officially tested on Ubuntu"
            ;;
        *)
            die "Unsupported OS: ${PRETTY_NAME}. Requires Ubuntu 22.04/24.04 or Debian 12."
            ;;
    esac
}

check_resources() {
    local cpu_cores ram_mb disk_gb

    cpu_cores=$(nproc 2>/dev/null) || cpu_cores=1
    ram_mb=$(awk '/^MemTotal:/ {printf "%.0f", $2/1024}' /proc/meminfo 2>/dev/null) || ram_mb=0
    disk_gb=$(df -BG "${INSTALL_DIR%/*}" 2>/dev/null | awk 'NR==2 {gsub(/G/,"",$4); print $4}') || \
        disk_gb=$(df -BG / | awk 'NR==2 {gsub(/G/,"",$4); print $4}')

    if (( cpu_cores < MIN_CPU )); then
        die "CPU: ${cpu_cores} cores detected. Minimum: ${MIN_CPU}."
    fi
    if (( ram_mb < MIN_RAM_MB )); then
        die "RAM: ${ram_mb} MB detected. Minimum: ${MIN_RAM_MB} MB."
    fi
    if (( disk_gb < MIN_DISK_GB )); then
        die "Disk: ${disk_gb} GB free. Minimum: ${MIN_DISK_GB} GB."
    fi

    log OK "Resources: ${cpu_cores} CPU, ${ram_mb} MB RAM, ${disk_gb} GB disk"
}

###############################################################################
# PHASE 2: INSTALL SYSTEM DEPENDENCIES
###############################################################################
install_system_deps() {
    log STEP "Phase 2: Installing system dependencies..."

    if $DRY_RUN; then
        log DRY "Would install: curl git jq openssl ca-certificates gnupg lsb-release"
        return 0
    fi

    export DEBIAN_FRONTEND=noninteractive

    log INFO "Updating package lists..."
    apt-get update -qq >> "$LOG_FILE" 2>&1

    log INFO "Installing base packages..."
    apt-get install -y -qq \
        curl git jq openssl ca-certificates gnupg lsb-release \
        apt-transport-https software-properties-common \
        >> "$LOG_FILE" 2>&1

    log OK "System dependencies installed"
}

###############################################################################
# PHASE 3: INSTALL DOCKER
###############################################################################
install_docker() {
    log STEP "Phase 3: Installing Docker..."

    # Check if Docker is already installed and running
    if command -v docker &>/dev/null; then
        if docker info &>/dev/null; then
            local docker_ver
            docker_ver=$(docker --version 2>/dev/null | grep -oP '\d+\.\d+' | head -1)
            log OK "Docker ${docker_ver} already installed and running"

            # Check compose plugin
            if docker compose version &>/dev/null; then
                local compose_ver
                compose_ver=$(docker compose version --short 2>/dev/null)
                log OK "Docker Compose ${compose_ver} available"
            else
                log WARN "Docker Compose plugin missing — installing..."
                if ! $DRY_RUN; then
                    apt-get install -y -qq docker-compose-plugin >> "$LOG_FILE" 2>&1 || {
                        log WARN "Plugin install failed — reinstalling Docker..."
                        curl -fsSL https://get.docker.com | sh >> "$LOG_FILE" 2>&1
                    }
                fi
            fi
            return 0
        fi
    fi

    if $DRY_RUN; then
        log DRY "Would install Docker CE + Compose plugin"
        return 0
    fi

    log INFO "Installing Docker CE via get.docker.com..."
    curl -fsSL https://get.docker.com | sh >> "$LOG_FILE" 2>&1

    # Enable and start Docker
    systemctl enable docker >> "$LOG_FILE" 2>&1
    systemctl start docker >> "$LOG_FILE" 2>&1

    # Wait a moment for daemon to be ready
    sleep 3

    # Verify
    if ! docker info &>/dev/null; then
        die "Docker installed but daemon failed to start. Check: systemctl status docker"
    fi

    local docker_ver compose_ver
    docker_ver=$(docker --version | grep -oP '\d+\.\d+' | head -1)
    compose_ver=$(docker compose version --short 2>/dev/null || echo "N/A")
    log OK "Docker ${docker_ver} + Compose ${compose_ver} installed"

    # Add the real user (not root) to docker group
    local real_user="${SUDO_USER:-}"
    if [[ -n "$real_user" ]] && [[ "$real_user" != "root" ]]; then
        usermod -aG docker "$real_user" 2>/dev/null || true
        log INFO "Added $real_user to docker group (re-login for non-sudo use)"
    fi
}

###############################################################################
# PHASE 4: CLONE REPOSITORY
###############################################################################
clone_repository() {
    log STEP "Phase 4: Downloading Rhinometric platform..."

    if $DRY_RUN; then
        log DRY "Would clone ${REPO_URL} branch ${REPO_BRANCH} to ${INSTALL_DIR}"
        return 0
    fi

    # Build clone URL with auth if provided
    local clone_url="$REPO_URL"
    if [[ -n "$GITHUB_USER" ]] && [[ -n "$GITHUB_TOKEN" ]]; then
        clone_url="https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/Rafael2712/mi-proyecto.git"
        log INFO "Using authenticated GitHub access"
    fi

    if [[ -d "${INSTALL_DIR}/.git" ]]; then
        log INFO "Existing git repo found — updating..."
        cd "$INSTALL_DIR"

        # Temporarily set authenticated URL
        if [[ -n "$GITHUB_USER" ]] && [[ -n "$GITHUB_TOKEN" ]]; then
            git remote set-url origin "$clone_url" 2>/dev/null || true
        fi

        git fetch origin >> "$LOG_FILE" 2>&1

        # Checkout the correct branch
        local current_branch
        current_branch=$(git branch --show-current 2>/dev/null || echo "")
        if [[ "$current_branch" != "$REPO_BRANCH" ]]; then
            git checkout "$REPO_BRANCH" >> "$LOG_FILE" 2>&1 || \
                git checkout -b "$REPO_BRANCH" "origin/$REPO_BRANCH" >> "$LOG_FILE" 2>&1
        fi

        # Pull latest
        git reset --hard "origin/$REPO_BRANCH" >> "$LOG_FILE" 2>&1

        # Remove token from remote URL
        if [[ -n "$GITHUB_TOKEN" ]]; then
            git remote set-url origin "$REPO_URL" 2>/dev/null || true
        fi

        log OK "Repository updated at ${INSTALL_DIR}"
    else
        # Fresh clone
        mkdir -p "$(dirname "$INSTALL_DIR")"

        # If /opt/rhinometric exists but isn't a git repo, back it up
        if [[ -d "$INSTALL_DIR" ]]; then
            local backup="${INSTALL_DIR}.bak.$(date +%s)"
            log WARN "Moving existing ${INSTALL_DIR} to ${backup}"
            mv "$INSTALL_DIR" "$backup"
        fi

        log INFO "Cloning repository (this may take 1-2 minutes)..."
        if ! git clone --branch "$REPO_BRANCH" --single-branch "$clone_url" "$INSTALL_DIR" >> "$LOG_FILE" 2>&1; then
            # If single-branch fails, try full clone
            log WARN "Single-branch clone failed — trying full clone..."
            git clone "$clone_url" "$INSTALL_DIR" >> "$LOG_FILE" 2>&1
            cd "$INSTALL_DIR"
            git checkout "$REPO_BRANCH" >> "$LOG_FILE" 2>&1
        fi

        # Remove token from remote URL
        if [[ -n "$GITHUB_TOKEN" ]]; then
            cd "$INSTALL_DIR"
            git remote set-url origin "$REPO_URL" 2>/dev/null || true
        fi

        log OK "Platform downloaded to ${INSTALL_DIR}"
    fi

    # Verify compose file exists
    cd "$INSTALL_DIR"
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log ERROR "Available compose files:"
        ls -1 docker-compose*.yml 2>/dev/null >> "$LOG_FILE" || true
        die "Compose file not found: ${INSTALL_DIR}/${COMPOSE_FILE}. Check branch ${REPO_BRANCH}."
    fi

    log OK "Compose file verified: ${COMPOSE_FILE}"
}

###############################################################################
# PHASE 5: SETUP DIRECTORIES
###############################################################################
setup_directories() {
    log STEP "Phase 5: Setting up directories..."

    local data_dir="${HOME}/${DATA_DIR_SUFFIX}"

    if $DRY_RUN; then
        log DRY "Would create data directories at ${data_dir}"
        return 0
    fi

    local dirs=(
        "${data_dir}/postgres"
        "${data_dir}/redis"
        "${data_dir}/loki"
        "${data_dir}/jaeger"
        "${data_dir}/alertmanager"
        "${data_dir}/ai-anomaly/models"
        "${data_dir}/ai-anomaly/data"
        "${data_dir}/console-backend/logs"
        "${data_dir}/console-backend/data"
        "${data_dir}/license-server/logs"
        "${data_dir}/nginx/logs"
        "${data_dir}/prometheus"
        "${data_dir}/victoria-metrics"
        "${data_dir}/grafana"
    )

    for d in "${dirs[@]}"; do
        mkdir -p "$d"
    done

    # Fix permissions for services that run as non-root
    chown -R 10001:10001 "${data_dir}/loki" 2>/dev/null || true      # Loki uid
    chown -R 472:472 "${data_dir}/grafana" 2>/dev/null || true       # Grafana uid
    chown -R 65534:65534 "${data_dir}/prometheus" 2>/dev/null || true # Prometheus uid

    log OK "Data directories created at ${data_dir}"
}

###############################################################################
# PHASE 6: GENERATE .ENV
###############################################################################
generate_password() {
    openssl rand -base64 24 | tr -d "=+/" | cut -c1-24
}

prompt_config() {
    if $NON_INTERACTIVE; then
        if [[ -z "$EDITION" ]]; then
            die "--non-interactive requires --edition (trial|annual)"
        fi
        DOMAIN="${DOMAIN:-$(hostname -I 2>/dev/null | awk '{print $1}')}"
        return 0
    fi

    echo ""
    echo -e "${C_BOLD}── Configuration ──${C_RESET}"
    echo ""

    # Edition
    if [[ -z "$EDITION" ]]; then
        echo "  Edition:"
        echo "    1) trial   — 30-day evaluation"
        echo "    2) annual  — licensed production"
        read -rp "  Select [1/2]: " ed_choice
        case "$ed_choice" in
            2) EDITION="annual" ;;
            *) EDITION="trial" ;;
        esac
    fi

    # Domain
    if [[ -z "$DOMAIN" ]]; then
        local default_ip
        default_ip=$(hostname -I 2>/dev/null | awk '{print $1}')
        read -rp "  Domain or IP [${default_ip}]: " DOMAIN
        DOMAIN="${DOMAIN:-$default_ip}"
    fi

    # GitHub auth (for private repo)
    if [[ -z "$GITHUB_USER" ]]; then
        echo ""
        echo "  GitHub credentials (needed to download the platform):"
        read -rp "  GitHub username: " GITHUB_USER
        read -rsp "  GitHub token (PAT): " GITHUB_TOKEN
        echo ""
    fi

    echo ""
    log INFO "Edition: ${EDITION}, Domain: ${DOMAIN}"
}

create_env_file() {
    cd "$INSTALL_DIR"

    # If .env exists with real passwords, preserve it
    if [[ -f ".env" ]]; then
        if ! grep -qE "secure_password_2024|change_this|your_.*_change" .env 2>/dev/null; then
            log OK "Existing .env with custom passwords — preserving"
            return 0
        fi
        log WARN "Default/insecure .env found — regenerating with secure passwords"
    fi

    if $DRY_RUN; then
        log DRY "Would generate .env with secure random passwords"
        return 0
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

    # Backup existing .env
    if [[ -f ".env" ]]; then
        cp .env ".env.bak.$(date +%s)"
    fi

    cat > .env <<ENVEOF
# ═══════════════════════════════════════════════════════════════
# RHINOMETRIC v${SCRIPT_VERSION} — Auto-generated $(date -u +"%Y-%m-%d %H:%M:%S UTC")
# DO NOT commit this file to git.
# ═══════════════════════════════════════════════════════════════

# === Public Access ===
PUBLIC_IP=${public_ip}
DOMAIN=${DOMAIN:-${public_ip}}
CUSTOMER_DOMAIN=${DOMAIN:-}

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
GRAFANA_DOMAIN=${DOMAIN:-monitor.rhinometric.local}

# === Console Backend ===
SECRET_KEY=${secret_key}
JWT_SECRET=${jwt_secret}
ADMIN_USERNAME=admin
ADMIN_PASSWORD=${admin_pass}
API_VERSION=2.6.0

# === License ===
LICENSE_ENCRYPTION_KEY=${license_key}

# === Paths ===
HOME=${HOME:-/root}

# === Mail (optional — fill to enable) ===
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=

# === Slack (optional) ===
SLACK_WEBHOOK_URL=

# === Environment ===
ENVIRONMENT=production
DEBUG=false

# === SSL ===
SSL_EMAIL=admin@rhinometric.com
ENVEOF

    chmod 600 .env
    log OK "Generated .env with secure random passwords"

    # Save credentials for the admin
    cat > CREDENTIALS.txt <<CREDEOF
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

JWT_SECRET: ${jwt_secret}

═══════════════════════════════════════════════════════════════
  SAVE THESE CREDENTIALS IN A PASSWORD MANAGER.
  Then delete this file: rm ${INSTALL_DIR}/CREDENTIALS.txt
═══════════════════════════════════════════════════════════════
CREDEOF

    chmod 600 CREDENTIALS.txt
    log OK "Credentials saved to ${INSTALL_DIR}/CREDENTIALS.txt"
}

###############################################################################
# PHASE 7: SETUP COMPOSE & NGINX
###############################################################################
setup_compose() {
    log STEP "Phase 7: Setting up Docker Compose..."

    if $DRY_RUN; then
        log DRY "Would symlink ${SYMLINK_NAME} -> ${COMPOSE_FILE}"
        return 0
    fi

    cd "$INSTALL_DIR"

    # Create/update compose symlink
    if [[ -f "$SYMLINK_NAME" ]] && [[ ! -L "$SYMLINK_NAME" ]]; then
        mv "$SYMLINK_NAME" "${SYMLINK_NAME}.bak.$(date +%s)"
    fi
    ln -sf "$COMPOSE_FILE" "$SYMLINK_NAME"
    log OK "Symlinked ${SYMLINK_NAME} -> ${COMPOSE_FILE}"

    # Ensure nginx htpasswd exists
    mkdir -p nginx
    if [[ ! -f nginx/.htpasswd ]]; then
        # Default htpasswd (proxy-admin / rhinometric)
        echo 'proxy-admin:$apr1$sIOJfb7j$a9Xjf3VxEuyBeTJu/NRTs/' > nginx/.htpasswd
        log OK "Created nginx/.htpasswd"
    fi

    # Verify nginx.conf exists (should be in the repo)
    if [[ ! -f nginx/nginx.conf ]]; then
        log WARN "nginx/nginx.conf missing — creating minimal reverse-proxy config"
        cat > nginx/nginx.conf <<'NGINXEOF'
worker_processes auto;
events { worker_connections 1024; }
http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    keepalive_timeout 65;
    client_max_body_size 50M;

    upstream backend  { server rhinometric-console-backend:8105; }
    upstream frontend { server rhinometric-console-frontend:3002; }
    upstream grafana  { server rhinometric-grafana:3000; }

    server {
        listen 80;
        server_name _;

        location /nginx-health { return 200 "ok\n"; }

        location /api/ {
            proxy_pass http://backend/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30;
            proxy_read_timeout 120;
        }

        location /grafana/ {
            proxy_pass http://grafana/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
NGINXEOF
        log OK "Created minimal nginx.conf"
    fi

    log OK "Compose and nginx configured"
}

###############################################################################
# PHASE 8: BUILD & PULL IMAGES
###############################################################################
build_images() {
    log STEP "Phase 8: Building Docker images..."

    if $DRY_RUN; then
        log DRY "Would pull base images and build application images"
        return 0
    fi

    if $SKIP_BUILD; then
        log INFO "Skipping build (--skip-build)"
        return 0
    fi

    cd "$INSTALL_DIR"

    log INFO "Pulling base images (postgres, redis, prometheus, grafana...)..."
    docker compose -f "$COMPOSE_FILE" pull --ignore-pull-failures >> "$LOG_FILE" 2>&1 || true

    log INFO "Building application images (5-15 minutes on first run)..."
    echo ""

    # Core services that MUST build
    local core_services=("license-server-v2" "rhinometric-console-backend" "rhinometric-console-frontend" "rhinometric-ai-anomaly")
    local built=0 failed=0

    for svc in "${core_services[@]}"; do
        printf "  Building %-42s" "${svc}..."
        if docker compose -f "$COMPOSE_FILE" build "$svc" >> "$LOG_FILE" 2>&1; then
            echo -e " ${C_GREEN}OK${C_RESET}"
            built=$((built + 1))
        else
            echo -e " ${C_RED}FAIL${C_RESET}"
            failed=$((failed + 1))
            log WARN "Failed to build $svc — check $LOG_FILE for details"
        fi
    done

    # Optional services (OK if they fail)
    local optional_services=("license-ui")
    for svc in "${optional_services[@]}"; do
        # Check if service is defined in compose
        if docker compose -f "$COMPOSE_FILE" config --services 2>/dev/null | grep -q "^${svc}$"; then
            printf "  Building %-42s" "${svc}..."
            if docker compose -f "$COMPOSE_FILE" build "$svc" >> "$LOG_FILE" 2>&1; then
                echo -e " ${C_GREEN}OK${C_RESET}"
                built=$((built + 1))
            else
                echo -e " ${C_YELLOW}SKIP${C_RESET}"
            fi
        fi
    done

    echo ""
    log OK "Build complete: ${built} built, ${failed} failed"

    if (( failed > 0 )); then
        log WARN "Some builds failed. Platform may start with reduced functionality."
        log WARN "Check: tail -100 $LOG_FILE"
    fi
}

###############################################################################
# PHASE 9: START STACK
###############################################################################
start_stack() {
    log STEP "Phase 9: Starting Rhinometric platform..."

    if $DRY_RUN; then
        log DRY "Would start all services with docker compose up -d"
        return 0
    fi

    cd "$INSTALL_DIR"

    # Build scale-to-zero flags for services without images
    local scale_flags=""
    local all_services
    all_services=$(docker compose -f "$COMPOSE_FILE" config --services 2>/dev/null || echo "")

    for svc in license-ui; do
        if echo "$all_services" | grep -q "^${svc}$"; then
            if ! docker compose -f "$COMPOSE_FILE" images "$svc" 2>/dev/null | grep -q "$svc"; then
                scale_flags="${scale_flags} --scale ${svc}=0"
                log INFO "Scaling ${svc}=0 (no image available)"
            fi
        fi
    done

    log INFO "Starting all services..."
    # shellcheck disable=SC2086
    docker compose -f "$COMPOSE_FILE" up -d --remove-orphans $scale_flags >> "$LOG_FILE" 2>&1 || {
        log WARN "docker compose up returned non-zero — some services may have issues"
    }

    log OK "Stack start command issued"
}

###############################################################################
# PHASE 10: HEALTH CHECKS
###############################################################################
wait_for_healthy() {
    log STEP "Phase 10: Verifying platform health..."

    if $DRY_RUN; then
        log DRY "Would wait for containers to become healthy"
        return 0
    fi

    cd "$INSTALL_DIR"

    log INFO "Waiting for services to initialize (up to 180s)..."

    local max_wait=180
    local interval=10
    local elapsed=0

    while (( elapsed < max_wait )); do
        local running healthy
        running=$(docker ps --filter "name=rhinometric" --format '{{.Names}}' 2>/dev/null | wc -l) || running=0
        healthy=$(docker ps --filter "name=rhinometric" --filter "health=healthy" --format '{{.Names}}' 2>/dev/null | wc -l) || healthy=0

        printf "\r  Waiting... %3ds — %d running, %d healthy  " "$elapsed" "$running" "$healthy"

        # Good enough: at least 10 running and 8 healthy
        if (( running >= 10 )) && (( healthy >= 8 )); then
            echo ""
            log OK "Platform healthy: ${healthy}/${running} services"
            return 0
        fi

        sleep "$interval"
        elapsed=$((elapsed + interval))
    done

    echo ""
    log WARN "Timeout after ${max_wait}s. ${healthy:-0}/${running:-0} healthy."
    log WARN "Services may still be starting. Check: docker ps"
    return 1
}

run_smoke_tests() {
    if $DRY_RUN; then
        return 0
    fi

    cd "$INSTALL_DIR"

    echo ""
    echo -e "${C_BOLD}── Service Status ──${C_RESET}"
    echo ""

    # List all rhinometric containers with health status
    docker ps --filter "name=rhinometric" --format '{{.Names}}|{{.Status}}' 2>/dev/null | sort | while IFS='|' read -r name status; do
        [[ -z "$name" ]] && continue
        local short="${name#rhinometric-}"
        if [[ "$status" == *"(healthy)"* ]]; then
            echo -e "  ${C_GREEN}✓${C_RESET} ${short}"
        elif [[ "$status" == *"(unhealthy)"* ]]; then
            echo -e "  ${C_RED}✗${C_RESET} ${short} (unhealthy)"
        elif [[ "$status" == *"Up"* ]]; then
            echo -e "  ${C_YELLOW}~${C_RESET} ${short} (running)"
        else
            echo -e "  ${C_RED}✗${C_RESET} ${short} (${status})"
        fi
    done

    # HTTP check on port 80
    echo ""
    local http_code
    http_code=$(curl -sf -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "http://localhost/" 2>/dev/null || echo "000")
    if [[ "$http_code" =~ ^(200|301|302)$ ]]; then
        echo -e "  ${C_GREEN}✓${C_RESET} Frontend HTTP: ${http_code}"
    else
        echo -e "  ${C_YELLOW}~${C_RESET} Frontend HTTP: ${http_code} (may still be starting)"
    fi
    echo ""
}

###############################################################################
# PHASE 11: INSTALL CLI (rhinoctl)
###############################################################################
install_rhinoctl() {
    log STEP "Phase 11: Installing management CLI..."

    if $DRY_RUN; then
        log DRY "Would install rhinoctl to /usr/local/bin/"
        return 0
    fi

    cd "$INSTALL_DIR"

    # If the full rhinoctl.sh exists in scripts/, use it
    if [[ -f "scripts/rhinoctl.sh" ]]; then
        cp scripts/rhinoctl.sh /usr/local/bin/rhinoctl
        chmod +x /usr/local/bin/rhinoctl
        sed -i "s|^RHINO_DIR=.*|RHINO_DIR=\"${INSTALL_DIR}\"|" /usr/local/bin/rhinoctl
        log OK "rhinoctl (full) installed → /usr/local/bin/rhinoctl"
        return 0
    fi

    # Otherwise create a minimal CLI inline
    cat > /usr/local/bin/rhinoctl <<'RHINOCTL_EOF'
#!/usr/bin/env bash
###############################################################################
# rhinoctl — Rhinometric Platform Management CLI (minimal)
###############################################################################
RHINO_DIR="/opt/rhinometric"
CF="docker-compose-v2.5.0-SECURE.yml"

cd "$RHINO_DIR" 2>/dev/null || { echo "ERROR: $RHINO_DIR not found"; exit 1; }

case "${1:-help}" in
    status)
        docker compose -f "$CF" ps
        ;;
    start)
        docker compose -f "$CF" up -d --remove-orphans
        ;;
    stop)
        docker compose -f "$CF" down
        ;;
    restart)
        docker compose -f "$CF" restart ${2:-}
        ;;
    logs)
        docker compose -f "$CF" logs --tail=${3:-100} -f ${2:-}
        ;;
    health)
        echo "=== Container Health ==="
        docker ps --filter "name=rhinometric" --format 'table {{.Names}}\t{{.Status}}' | sort
        echo ""
        echo "=== HTTP Check ==="
        code=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")
        echo "Frontend: HTTP $code"
        ;;
    fingerprint)
        _mac=$(ip -o link show 2>/dev/null | awk '/ether/ {print $NF}' | grep -v "00:00:00:00:00:00" | head -1)
        _ip=$(hostname -I | awk '{print $1}')
        _host=$(hostname)
        _raw="${_mac}-${_ip}-${_host}"
        _hwid=$(echo -n "$_raw" | sha256sum | cut -c1-16 | tr 'a-f' 'A-F')
        echo ""
        echo "  Hardware ID: $_hwid"
        echo "  MAC:         $_mac"
        echo "  IP:          $_ip"
        echo "  Hostname:    $_host"
        echo ""
        echo "  Send this HWID to licenses@rhinometric.com"
        ;;
    apply-license)
        if [[ -z "${2:-}" ]]; then
            echo "Usage: rhinoctl apply-license /path/to/file.lic"
            exit 1
        fi
        cp "$2" "$RHINO_DIR/license.key"
        chmod 600 "$RHINO_DIR/license.key"
        docker compose -f "$CF" restart license-server-v2
        echo "License applied and license server restarted."
        ;;
    *)
        echo "rhinoctl — Rhinometric Platform CLI"
        echo ""
        echo "Commands:"
        echo "  status          Show container status"
        echo "  start           Start platform"
        echo "  stop            Stop platform"
        echo "  restart [svc]   Restart all or specific service"
        echo "  logs [svc] [n]  View logs"
        echo "  health          Health check"
        echo "  fingerprint     Generate hardware ID"
        echo "  apply-license F Apply license file"
        ;;
esac
RHINOCTL_EOF

    # Patch RHINO_DIR in the inline script
    sed -i "s|^RHINO_DIR=.*|RHINO_DIR=\"${INSTALL_DIR}\"|" /usr/local/bin/rhinoctl
    sed -i "s|^CF=.*|CF=\"${COMPOSE_FILE}\"|" /usr/local/bin/rhinoctl
    chmod +x /usr/local/bin/rhinoctl
    log OK "rhinoctl (minimal) installed → /usr/local/bin/rhinoctl"
}

###############################################################################
# PHASE 12: COMPLETION
###############################################################################
show_completion() {
    local public_ip="${DOMAIN:-$(hostname -I 2>/dev/null | awk '{print $1}')}"

    echo ""
    echo -e "${C_GREEN}${C_BOLD}"
    cat <<'COMPLETE'
  ╔═══════════════════════════════════════════════════════════╗
  ║           ✓  INSTALLATION COMPLETE!                       ║
  ╚═══════════════════════════════════════════════════════════╝
COMPLETE
    echo -e "${C_RESET}"

    echo "  Access Rhinometric:"
    echo ""
    echo "    Console:    http://${public_ip}"
    echo "    Grafana:    http://${public_ip}/grafana/"
    echo ""
    echo "  Credentials: ${INSTALL_DIR}/CREDENTIALS.txt"
    echo ""
    echo -e "  ${C_BOLD}Next steps:${C_RESET}"
    echo "    1. rhinoctl fingerprint        # Get hardware ID"
    echo "    2. Send HWID to licenses@rhinometric.com"
    echo "    3. rhinoctl apply-license /path/to/license.lic"
    echo "    4. rhinoctl status             # Verify"
    echo ""
    echo "  Management: rhinoctl help"
    echo "  Full log:   ${LOG_FILE}"
    echo ""
}

show_dryrun_summary() {
    echo ""
    echo -e "${C_BLUE}${C_BOLD}── Dry-Run Complete ──${C_RESET}"
    echo ""
    echo "  All checks passed. The installer would:"
    echo ""
    echo "    Phase  1:  Pre-flight checks (OS, CPU, RAM, disk)"
    echo "    Phase  2:  Install curl, git, jq, openssl"
    echo "    Phase  3:  Install Docker CE + Compose plugin"
    echo "    Phase  4:  Clone repo from GitHub (branch: ${REPO_BRANCH})"
    echo "    Phase  5:  Create 14 persistent data directories"
    echo "    Phase  6:  Generate .env with secure random passwords"
    echo "    Phase  7:  Setup compose symlink + nginx reverse proxy"
    echo "    Phase  8:  Build 4+ application Docker images (5-15 min)"
    echo "    Phase  9:  Start 21-service observability stack"
    echo "    Phase 10:  Health checks and smoke tests"
    echo "    Phase 11:  Install rhinoctl management CLI"
    echo "    Phase 12:  Show access URLs and credentials"
    echo ""
    echo "  To proceed: sudo bash $0 ${EDITION:+--edition $EDITION}"
    echo ""
}

###############################################################################
# MAIN
###############################################################################
main() {
    parse_args "$@"
    show_banner
    log_init

    log INFO "Rhinometric Bootstrap v${SCRIPT_VERSION} — $(_ts)"
    if $DRY_RUN; then
        log INFO "=== DRY-RUN MODE ==="
    fi

    # ── Phase 1: Pre-flight ──
    echo -e "${C_BOLD}── Phase 1: Pre-flight Checks ──${C_RESET}"
    echo ""
    check_root
    check_os
    check_resources
    echo ""
    log OK "All pre-flight checks passed"

    # ── Configuration ──
    prompt_config

    if $DRY_RUN; then
        show_dryrun_summary
        exit 0
    fi

    # ── Confirm ──
    if ! $NON_INTERACTIVE; then
        echo ""
        echo -e "  ${C_BOLD}Ready to install Rhinometric ${EDITION} to ${INSTALL_DIR}${C_RESET}"
        echo "  This will: install Docker, download platform, build images,"
        echo "  and start 21 services. Estimated time: 10-20 minutes."
        echo ""
        read -rp "  Proceed? (Y/n): " confirm
        if [[ "$confirm" =~ ^[Nn] ]]; then
            echo "  Installation cancelled."
            exit 0
        fi
    fi

    echo ""

    # ── Phases 2-11 ──
    install_system_deps
    install_docker
    clone_repository
    setup_directories
    create_env_file
    setup_compose
    build_images
    start_stack
    wait_for_healthy || true
    run_smoke_tests
    install_rhinoctl

    # ── Phase 12 ──
    show_completion

    log INFO "Installation completed successfully at $(_ts)"
}

main "$@"
