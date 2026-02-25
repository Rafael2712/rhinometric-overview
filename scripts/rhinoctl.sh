#!/usr/bin/env bash
###############################################################################
# RHINOCTL — Rhinometric Platform Control CLI
# v2.6.0 — Management wrapper for on-premise deployments
#
# Usage:  rhinoctl <command> [options]
#
# Install: cp scripts/rhinoctl.sh /usr/local/bin/rhinoctl && chmod +x /usr/local/bin/rhinoctl
###############################################################################
set -euo pipefail

readonly RHINOCTL_VERSION="2.6.0"
RHINO_DIR="/opt/rhinometric"
DATA_DIR="${HOME}/rhinometric_data_v2.5"
COMPOSE_FILE="docker-compose.yml"

# ─── Colors ────────────────────────────────────────────────────────────────
C_RESET="\033[0m"; C_GREEN="\033[0;32m"; C_RED="\033[0;31m"
C_YELLOW="\033[1;33m"; C_BLUE="\033[0;34m"; C_BOLD="\033[1m"

###############################################################################
# COMPOSE WRAPPER
###############################################################################
_compose() {
    cd "$RHINO_DIR"
    if docker compose version &>/dev/null; then
        docker compose -f "$COMPOSE_FILE" "$@"
    else
        docker-compose -f "$COMPOSE_FILE" "$@"
    fi
}

###############################################################################
# COMMANDS
###############################################################################

cmd_start() {
    echo -e "${C_GREEN}Starting Rhinometric...${C_RESET}"
    local scale_flags=""
    # Skip license-ui if no image exists
    if ! docker image ls --format '{{.Repository}}' 2>/dev/null | grep -q "license.*ui"; then
        scale_flags="--scale license-ui=0"
    fi
    # shellcheck disable=SC2086
    _compose up -d --remove-orphans $scale_flags
    echo -e "${C_GREEN}Done.${C_RESET} Use 'rhinoctl status' to check."
}

cmd_stop() {
    echo -e "${C_YELLOW}Stopping Rhinometric...${C_RESET}"
    _compose down
    echo -e "${C_GREEN}Stopped.${C_RESET}"
}

cmd_restart() {
    echo -e "${C_YELLOW}Restarting Rhinometric...${C_RESET}"
    cmd_stop
    cmd_start
}

cmd_status() {
    echo -e "${C_BOLD}Rhinometric Platform Status${C_RESET}"
    echo "─────────────────────────────────"
    echo ""

    # Container status
    local total running healthy unhealthy
    total=$(_compose ps -q 2>/dev/null | wc -l)
    running=$(docker ps --filter "label=com.docker.compose.project" \
              --filter "status=running" --format '{{.Names}}' 2>/dev/null \
              | grep -c rhinometric || echo 0)
    healthy=$(docker ps --filter "label=com.docker.compose.project" \
              --filter "health=healthy" --format '{{.Names}}' 2>/dev/null \
              | grep -c rhinometric || echo 0)
    unhealthy=$(docker ps --filter "label=com.docker.compose.project" \
                --filter "health=unhealthy" --format '{{.Names}}' 2>/dev/null \
                | grep -c rhinometric || echo 0)

    echo "  Containers:  ${running}/${total} running"
    echo "  Healthy:     ${healthy}"
    if (( unhealthy > 0 )); then
        echo -e "  Unhealthy:   ${C_RED}${unhealthy}${C_RESET}"
    fi
    echo ""

    # Disk usage
    local disk_used
    disk_used=$(du -sh "$DATA_DIR" 2>/dev/null | awk '{print $1}' || echo "N/A")
    echo "  Data dir:    $DATA_DIR"
    echo "  Disk used:   $disk_used"
    echo ""

    # License
    if [[ -f "$RHINO_DIR/license.key" ]]; then
        echo -e "  License:     ${C_GREEN}Applied${C_RESET}"
    else
        echo -e "  License:     ${C_YELLOW}Not applied${C_RESET} (rhinoctl apply-license)"
    fi

    echo ""

    # Per-service status
    echo -e "${C_BOLD}  Service Details:${C_RESET}"
    echo ""
    _compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || \
        _compose ps 2>/dev/null
    echo ""
}

cmd_logs() {
    local service="${1:-}"
    local lines="${2:-100}"

    if [[ -n "$service" ]]; then
        _compose logs --tail="$lines" -f "$service"
    else
        _compose logs --tail="$lines" -f
    fi
}

cmd_health() {
    echo -e "${C_BOLD}Health Check${C_RESET}"
    echo "────────────"
    echo ""

    local pass=0 fail=0 warn=0

    # --- Docker native health status (reliable) ---
    echo -e "  ${C_BOLD}Container Health (Docker healthcheck):${C_RESET}"
    echo ""

    local containers
    containers=$(docker ps --filter "name=rhinometric" --format '{{.Names}}|{{.Status}}' 2>/dev/null | sort)

    while IFS='|' read -r name status; do
        [[ -z "$name" ]] && continue
        local short_name="${name#rhinometric-}"
        if [[ "$status" == *"(healthy)"* ]]; then
            printf "  ${C_GREEN}✓${C_RESET} %-28s healthy\n" "$short_name"
            pass=$((pass + 1))
        elif [[ "$status" == *"(unhealthy)"* ]]; then
            printf "  ${C_RED}✗${C_RESET} %-28s unhealthy\n" "$short_name"
            fail=$((fail + 1))
        elif [[ "$status" == *"Up"* ]]; then
            printf "  ${C_YELLOW}~${C_RESET} %-28s running (no healthcheck)\n" "$short_name"
            warn=$((warn + 1))
        else
            printf "  ${C_RED}✗${C_RESET} %-28s %s\n" "$short_name" "$status"
            fail=$((fail + 1))
        fi
    done <<< "$containers"

    echo ""

    # --- HTTP endpoint checks (nginx-exposed only) ---
    echo -e "  ${C_BOLD}HTTP Endpoints:${C_RESET}"
    echo ""

    # Only check ports actually mapped to host
    local http_pass=0 http_fail=0
    declare -A http_endpoints
    http_endpoints["Frontend (nginx:80)"]="http://localhost/"

    # Detect host-bound ports dynamically
    if docker port rhinometric-grafana 3000 &>/dev/null 2>&1; then
        http_endpoints["Grafana"]="http://localhost:3000/api/health"
    fi
    if docker port rhinometric-prometheus 9090 &>/dev/null 2>&1; then
        http_endpoints["Prometheus"]="http://localhost:9090/-/healthy"
    fi

    for name in "${!http_endpoints[@]}"; do
        local url="${http_endpoints[$name]}"
        local code
        code=$(curl -sf -o /dev/null -w "%{http_code}" --connect-timeout 3 --max-time 5 "$url" 2>/dev/null || echo "000")
        if [[ "$code" =~ ^(200|204|301|302)$ ]]; then
            printf "  ${C_GREEN}✓${C_RESET} %-28s %s\n" "$name" "$code"
            http_pass=$((http_pass + 1))
        else
            printf "  ${C_RED}✗${C_RESET} %-28s %s\n" "$name" "$code"
            http_fail=$((http_fail + 1))
        fi
    done

    echo ""
    echo "  Summary: ${pass} healthy, ${warn} running, ${fail} unhealthy"
    if (( http_fail > 0 )); then
        echo -e "           ${C_RED}${http_fail} HTTP endpoint(s) down${C_RESET}"
    fi
}

cmd_fingerprint() {
    echo -e "${C_BOLD}Hardware Fingerprint${C_RESET}"
    echo "────────────────────"
    echo ""

    # CPU info
    local cpu_info
    cpu_info=$(grep -m1 "model name" /proc/cpuinfo 2>/dev/null | cut -d: -f2 | xargs || echo "unknown")

    # MAC address (first non-loopback, non-zero)
    local mac_addr
    mac_addr=$(ip -o link show 2>/dev/null | grep -v "loopback" | awk -F'link/ether ' '{print $2}' | awk '{print $1}' | grep -v "^00:00:00" | head -1)
    mac_addr="${mac_addr:-00:00:00:00:00:00}"

    # Hostname
    local host_name
    host_name=$(hostname 2>/dev/null || echo "unknown")

    # Generate HWID: SHA256(CPU|MAC|HOSTNAME) → first 16 chars uppercase
    local combined="${cpu_info}|${mac_addr}|${host_name}"
    local hwid
    hwid=$(echo -n "$combined" | sha256sum | awk '{print toupper(substr($1,1,16))}')

    echo "  Components:"
    echo "    CPU:      $cpu_info"
    echo "    MAC:      $mac_addr"
    echo "    Hostname: $host_name"
    echo ""
    echo -e "  ${C_BOLD}HWID: ${C_GREEN}${hwid}${C_RESET}"
    echo ""
    echo "  Send this HWID to: licenses@rhinometric.com"
    echo "  Or request at:     https://license.rhinometric.com"
    echo ""

    # Also save to file
    echo "$hwid" > "$RHINO_DIR/HWID.txt"
    echo "  Saved to: $RHINO_DIR/HWID.txt"
}

cmd_apply_license() {
    local license_file="${1:-}"

    if [[ -z "$license_file" ]]; then
        echo "Usage: rhinoctl apply-license /path/to/license.lic"
        exit 1
    fi

    if [[ ! -f "$license_file" ]]; then
        echo -e "${C_RED}Error: File not found: $license_file${C_RESET}"
        exit 1
    fi

    cp "$license_file" "$RHINO_DIR/license.key"
    chmod 600 "$RHINO_DIR/license.key"
    echo -e "${C_GREEN}License applied.${C_RESET}"

    # Restart license server to pick up new key
    echo "Restarting license-server-v2..."
    _compose restart license-server-v2 2>/dev/null || true
    echo -e "${C_GREEN}Done.${C_RESET} Check with: rhinoctl status"
}

cmd_backup() {
    local backup_name="rhinometric-backup-$(date +%Y%m%d-%H%M%S)"
    local backup_dir="/tmp/$backup_name"

    echo -e "${C_BOLD}Creating backup: $backup_name${C_RESET}"
    mkdir -p "$backup_dir"

    # Stop services for consistent backup
    echo "Stopping services for consistent backup..."
    _compose stop postgres redis 2>/dev/null || true

    # Backup data dirs
    echo "Backing up data directories..."
    cp -a "$DATA_DIR/postgres" "$backup_dir/" 2>/dev/null || true
    cp -a "$DATA_DIR/redis" "$backup_dir/" 2>/dev/null || true
    cp -a "$DATA_DIR/loki" "$backup_dir/" 2>/dev/null || true
    cp -a "$DATA_DIR/alertmanager" "$backup_dir/" 2>/dev/null || true

    # Backup config
    cp -a "$RHINO_DIR/.env" "$backup_dir/" 2>/dev/null || true
    cp -a "$RHINO_DIR/license.key" "$backup_dir/" 2>/dev/null || true

    # Restart services
    echo "Restarting services..."
    _compose start postgres redis 2>/dev/null || true

    # Create tarball
    local tarball="/tmp/${backup_name}.tar.gz"
    tar -czf "$tarball" -C /tmp "$backup_name"
    rm -rf "$backup_dir"

    local size
    size=$(du -h "$tarball" | awk '{print $1}')
    echo ""
    echo -e "${C_GREEN}Backup complete: $tarball ($size)${C_RESET}"

    # Checksum
    local checksum
    checksum=$(sha256sum "$tarball" | awk '{print $1}')
    echo "SHA256: $checksum"
}

cmd_update() {
    echo -e "${C_BOLD}Updating Rhinometric images...${C_RESET}"

    cd "$RHINO_DIR"

    # Pull latest images
    _compose pull --ignore-pull-failures 2>/dev/null || true

    # Rebuild custom images
    echo "Rebuilding application images..."
    _compose build --parallel 2>/dev/null || true

    # Rolling restart
    echo "Restarting with new images..."
    cmd_start

    echo -e "${C_GREEN}Update complete.${C_RESET}"
}

cmd_version() {
    echo "rhinoctl v${RHINOCTL_VERSION}"
    echo "Install dir: $RHINO_DIR"
    echo "Data dir:    $DATA_DIR"
}

###############################################################################
# HELP
###############################################################################
show_help() {
    cat <<EOF
rhinoctl v${RHINOCTL_VERSION} — Rhinometric Platform Control

Usage: rhinoctl <command> [options]

Commands:
  start                  Start the platform
  stop                   Stop the platform
  restart                Restart all services
  status                 Show platform status summary
  health                 Run endpoint health checks
  logs [service] [n]     Follow logs (optionally for a service, last n lines)
  fingerprint            Generate hardware ID for licensing
  apply-license FILE     Apply a license file (.lic / .key)
  backup                 Create full backup (stops DB briefly)
  update                 Pull latest images and restart
  version                Show version info

Examples:
  rhinoctl status
  rhinoctl logs grafana 50
  rhinoctl fingerprint
  rhinoctl apply-license /tmp/customer.lic
  rhinoctl backup
EOF
}

###############################################################################
# MAIN
###############################################################################
main() {
    # Check RHINO_DIR exists
    if [[ ! -d "$RHINO_DIR" ]]; then
        echo -e "${C_RED}Error: Rhinometric not found at $RHINO_DIR${C_RESET}"
        echo "Set RHINO_DIR or reinstall."
        exit 1
    fi

    local cmd="${1:-help}"
    shift 2>/dev/null || true

    case "$cmd" in
        start)          cmd_start ;;
        stop)           cmd_stop ;;
        restart)        cmd_restart ;;
        status)         cmd_status ;;
        health)         cmd_health ;;
        logs)           cmd_logs "$@" ;;
        fingerprint)    cmd_fingerprint ;;
        apply-license)  cmd_apply_license "$@" ;;
        backup)         cmd_backup ;;
        update)         cmd_update ;;
        version|-v)     cmd_version ;;
        help|-h|--help) show_help ;;
        *)
            echo -e "${C_RED}Unknown command: $cmd${C_RESET}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
