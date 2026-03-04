#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# RHINOMETRIC — UNINSTALLER
# Safely removes the Rhinometric platform
# ═══════════════════════════════════════════════════════════════════════════════

# ── Colors ────────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
    CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; CYAN=''; BOLD=''; NC=''
fi

readonly INSTALL_DIR="${INSTALL_DIR:-/opt/rhinometric}"

log_info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Root check ────────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root or with sudo."
    exit 1
fi

echo ""
echo -e "${RED}${BOLD}"
cat << 'BANNER'
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║                RHINOMETRIC — UNINSTALLER                         ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
BANNER
echo -e "${NC}"

echo -e "${YELLOW}  This will stop and remove the Rhinometric platform.${NC}"
echo ""
echo "  Install directory: ${INSTALL_DIR}"
echo ""

# ── Confirmation ──────────────────────────────────────────────────────────────
read -r -p "  Are you sure you want to uninstall? (type YES to confirm): " confirm
if [[ "$confirm" != "YES" ]]; then
    log_info "Uninstall cancelled."
    exit 0
fi

echo ""

# ── Step 1: Stop containers ──────────────────────────────────────────────────
log_info "Stopping Docker containers..."
if [[ -f "${INSTALL_DIR}/docker-compose.yml" ]]; then
    cd "${INSTALL_DIR}" || true
    docker compose down --timeout 30 2>/dev/null || true
    log_info "✓ Containers stopped"
else
    log_warn "docker-compose.yml not found. Attempting to stop known containers..."
    containers=(
        rhinometric-console-frontend
        rhinometric-console-backend
        rhinometric-grafana
        rhinometric-prometheus
        rhinometric-alertmanager
        rhinometric-loki
        rhinometric-postgres
        rhinometric-redis
        rhinometric-nginx
        rhinometric-node-exporter
        rhinometric-cadvisor
        rhinometric-blackbox-exporter
        rhinometric-victoria-metrics
        rhinometric-otel-collector
        rhinometric-promtail
        rhinometric-redis-exporter
        rhinometric-postgres-exporter
        rhinometric-ai-anomaly
        rhinometric-license-server-v2
        rhinometric-license-ui
    )
    for c in "${containers[@]}"; do
        docker rm -f "$c" 2>/dev/null || true
    done
    log_info "✓ Known containers removed"
fi

# ── Step 2: Remove Docker volumes ────────────────────────────────────────────
echo ""
read -r -p "  Remove Docker volumes (database data will be LOST)? (y/N): " remove_volumes
if [[ "$remove_volumes" =~ ^[Yy]$ ]]; then
    log_info "Removing Docker volumes..."
    if [[ -f "${INSTALL_DIR}/docker-compose.yml" ]]; then
        cd "${INSTALL_DIR}" || true
        docker compose down -v 2>/dev/null || true
    fi
    # Remove named volumes matching rhinometric pattern
    docker volume ls -q 2>/dev/null | grep -i rhinometric | while read -r vol; do
        docker volume rm "$vol" 2>/dev/null || true
    done
    log_info "✓ Docker volumes removed"
else
    log_info "Docker volumes preserved."
fi

# ── Step 3: Remove Docker network ────────────────────────────────────────────
log_info "Removing Docker network..."
docker network rm rhinometric_rhinometric_network 2>/dev/null || true
docker network ls -q --filter name=rhinometric 2>/dev/null | while read -r net; do
    docker network rm "$net" 2>/dev/null || true
done
log_info "✓ Docker networks cleaned"

# ── Step 4: Backup credentials before removal ────────────────────────────────
if [[ -f "${INSTALL_DIR}/install-info.txt" ]]; then
    backup_path="/root/rhinometric-credentials-backup-$(date +%Y%m%d%H%M%S).txt"
    cp "${INSTALL_DIR}/install-info.txt" "$backup_path" 2>/dev/null || true
    log_info "Credentials backed up to: ${backup_path}"
fi

if [[ -f "${INSTALL_DIR}/CREDENCIALES.txt" ]]; then
    backup_path2="/root/rhinometric-credenciales-backup-$(date +%Y%m%d%H%M%S).txt"
    cp "${INSTALL_DIR}/CREDENCIALES.txt" "$backup_path2" 2>/dev/null || true
fi

# ── Step 5: Remove installation directory ─────────────────────────────────────
echo ""
read -r -p "  Remove ${INSTALL_DIR} directory completely? (y/N): " remove_dir
if [[ "$remove_dir" =~ ^[Yy]$ ]]; then
    log_warn "Removing ${INSTALL_DIR}..."
    rm -rf "${INSTALL_DIR}"
    log_info "✓ Installation directory removed"
else
    log_info "Installation directory preserved at ${INSTALL_DIR}"
fi

# ── Step 6: Remove rhino-lic binary ──────────────────────────────────────────
if [[ -f "/usr/local/bin/rhino-lic" ]]; then
    echo ""
    read -r -p "  Remove /usr/local/bin/rhino-lic binary? (y/N): " remove_bin
    if [[ "$remove_bin" =~ ^[Yy]$ ]]; then
        rm -f /usr/local/bin/rhino-lic
        log_info "✓ rhino-lic binary removed"
    else
        log_info "rhino-lic binary preserved."
    fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║                ✓ Uninstall Complete                              ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  To reinstall, run:"
echo "    sudo bash install-rhinometric.sh"
echo ""
