#!/bin/bash
# support-bundle.sh - Recolecta informaciÃ³n para diagnÃ³stico

set -euo pipefail

BUNDLE_DIR="support-bundle-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "í³‹ Recolectando informaciÃ³n de soporte..."

# Logs de contenedores
echo "[1/6] Logs de contenedores..."
for container in $(docker ps --filter "name=rhinometric-" --format "{{.Names}}"); do
    docker logs --tail 500 "$container" > "$BUNDLE_DIR/${container}.log" 2>&1
done

# Docker info
echo "[2/6] Docker info..."
docker version > "$BUNDLE_DIR/docker-version.txt"
docker compose version > "$BUNDLE_DIR/docker-compose-version.txt"
docker ps -a > "$BUNDLE_DIR/containers.txt"
docker images > "$BUNDLE_DIR/images.txt"
docker volume ls > "$BUNDLE_DIR/volumes.txt"

# Configs
echo "[3/6] Configuraciones..."
cp ../docker-compose-demo.yml "$BUNDLE_DIR/"
cp ../.env.demo "$BUNDLE_DIR/env.demo.txt" 2>/dev/null || echo "No .env"
cp -r ../prometheus "$BUNDLE_DIR/" 2>/dev/null || echo "No prometheus config"
cp -r ../grafana/provisioning "$BUNDLE_DIR/grafana-provisioning" 2>/dev/null || echo "No grafana provisioning"

# System info
echo "[4/6] System info..."
df -h > "$BUNDLE_DIR/disk-usage.txt"
free -h > "$BUNDLE_DIR/memory.txt" 2>/dev/null || echo "N/A"
uname -a > "$BUNDLE_DIR/system.txt"

# Network
echo "[5/6] Network..."
docker network inspect demo_rhinometric > "$BUNDLE_DIR/network.json" 2>&1 || echo "No network"

# Health checks
echo "[6/6] Health checks..."
curl -s http://localhost:3000/api/health > "$BUNDLE_DIR/grafana-health.json" 2>&1 || echo "Grafana unreachable"
curl -s http://localhost:9090/-/healthy > "$BUNDLE_DIR/prometheus-health.txt" 2>&1 || echo "Prometheus unreachable"
curl -s http://localhost:8085/health > "$BUNDLE_DIR/ai-health.json" 2>&1 || echo "AI unreachable"

# Comprimir
tar czf "${BUNDLE_DIR}.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"

echo "âœ“ Support bundle creado: ${BUNDLE_DIR}.tar.gz"
