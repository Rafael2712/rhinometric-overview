#!/usr/bin/env bash

# ═══════════════════════════════════════════════════════════════════════════
#  RHINOMETRIC v2.1.0 - VALIDATION SCRIPT
# ═══════════════════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  RHINOMETRIC v2.1.0 - SYSTEM VALIDATION${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""

FAILED=0

# Container health
echo -e "${BLUE}▶ Container Health${NC}"
CONTAINERS=(
    "rhinometric-postgres"
    "rhinometric-redis"
    "rhinometric-license-server-v2"
    "rhinometric-api-proxy"
    "rhinometric-prometheus"
    "rhinometric-loki"
    "rhinometric-tempo"
    "rhinometric-grafana"
    "rhinometric-otel-collector"
    "rhinometric-alertmanager"
    "rhinometric-promtail"
    "rhinometric-node-exporter"
    "rhinometric-cadvisor"
    "rhinometric-blackbox-exporter"
    "rhinometric-postgres-exporter"
    "rhinometric-nginx"
)

for container in "${CONTAINERS[@]}"; do
    if docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null | grep -q healthy; then
        print_success "$container"
    elif docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null | grep -q running; then
        print_info "$container (running, no healthcheck)"
    else
        print_error "$container (not healthy)"
        FAILED=$((FAILED + 1))
    fi
done

echo ""

# Endpoint checks
echo -e "${BLUE}▶ Endpoint Accessibility${NC}"

check_endpoint() {
    if curl -sf "$1" > /dev/null 2>&1; then
        print_success "$2: $1"
    else
        print_error "$2: $1"
        FAILED=$((FAILED + 1))
    fi
}

check_endpoint "http://localhost:3000/api/health" "Grafana"
check_endpoint "http://localhost:9090/-/healthy" "Prometheus"
check_endpoint "http://localhost:5000/api/health" "License Server"
check_endpoint "http://localhost:8090/health" "API Proxy"
check_endpoint "http://localhost:3100/ready" "Loki"
check_endpoint "http://localhost:3200/ready" "Tempo"

echo ""

# Prometheus targets
echo -e "${BLUE}▶ Prometheus Targets${NC}"
TARGETS=$(curl -s http://localhost:9090/api/v1/targets 2>/dev/null | grep -o '"health":"up"' | wc -l)
print_info "Healthy targets: $TARGETS"

echo ""

# Summary
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All validation checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ $FAILED validation checks failed${NC}"
    echo -e "${YELLOW}Run: docker compose -f docker-compose-v2.1.0.yml logs -f${NC}"
    exit 1
fi
