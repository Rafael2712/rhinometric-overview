#!/bin/bash

#═══════════════════════════════════════════════════════════════════════════════
# RHINOMETRIC v2.5.0 - RECOPILADOR DE DIAGNÓSTICOS
# Para enviar a soporte técnico
#═══════════════════════════════════════════════════════════════════════════════

set -e

INSTALL_DIR="${INSTALL_DIR:-/opt/rhinometric}"
OUTPUT_FILE="rhinometric-diagnostics-$(date +%Y%m%d-%H%M%S).tar.gz"
TEMP_DIR="/tmp/rhinometric-diagnostics-$$"

echo "═══════════════════════════════════════════════════════════════"
echo "  RHINOMETRIC v2.5.0 - Recopilador de Diagnósticos"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Crear directorio temporal
mkdir -p "$TEMP_DIR"

echo "[1/10] Recopilando información del sistema..."
{
    echo "=== SYSTEM INFO ==="
    uname -a
    cat /etc/os-release
    echo ""
    echo "=== RECURSOS ==="
    free -h
    df -h
    echo ""
    echo "=== CPU ==="
    lscpu | grep -E '(Model name|^CPU\(s\)|Thread|Socket)'
} > "$TEMP_DIR/system-info.txt"

echo "[2/10] Recopilando versiones de Docker..."
{
    docker --version
    docker compose version
    docker info
} > "$TEMP_DIR/docker-info.txt"

echo "[3/10] Recopilando estado de contenedores..."
cd "$INSTALL_DIR"
docker compose ps > "$TEMP_DIR/containers-status.txt"
docker compose ps --format json > "$TEMP_DIR/containers-status.json"

echo "[4/10] Recopilando logs de servicios (últimas 500 líneas)..."
for service in $(docker compose config --services); do
    echo "Extrayendo logs de $service..."
    docker compose logs --tail 500 "$service" > "$TEMP_DIR/logs-$service.txt" 2>&1 || true
done

echo "[5/10] Recopilando configuración del stack..."
cp docker-compose.yml "$TEMP_DIR/" 2>/dev/null || true

# .env sin credenciales
if [ -f .env ]; then
    grep -v 'PASSWORD' .env > "$TEMP_DIR/env-sanitized.txt"
fi

echo "[6/10] Recopilando métricas de recursos..."
docker stats --no-stream > "$TEMP_DIR/docker-stats.txt"

echo "[7/10] Recopilando información de red..."
{
    echo "=== PUERTOS EN USO ==="
    ss -tuln | grep -E ':(3000|3002|5000|5432|6379|8085|8105|9090|9093|3100|16686)'
    echo ""
    echo "=== RED DOCKER ==="
    docker network ls
    docker network inspect rhinometric_network 2>/dev/null || true
} > "$TEMP_DIR/network-info.txt"

echo "[8/10] Verificando salud de servicios..."
{
    echo "=== PROMETHEUS ==="
    curl -s http://localhost:9090/-/healthy || echo "ERROR: No responde"
    echo ""
    echo "=== GRAFANA ==="
    curl -s http://localhost:3000/api/health || echo "ERROR: No responde"
    echo ""
    echo "=== CONSOLE BACKEND ==="
    curl -s http://localhost:8105/health || echo "ERROR: No responde"
} > "$TEMP_DIR/health-checks.txt"

echo "[9/10] Recopilando errores del kernel..."
dmesg | grep -i 'error\|warning\|oom' | tail -100 > "$TEMP_DIR/kernel-errors.txt" || true

echo "[10/10] Comprimiendo diagnósticos..."
cd /tmp
tar -czf "$OUTPUT_FILE" "rhinometric-diagnostics-$$/"

# Limpiar
rm -rf "$TEMP_DIR"

# Mover al directorio de instalación
mv "$OUTPUT_FILE" "$INSTALL_DIR/"

echo ""
echo "✓ Diagnósticos recopilados exitosamente"
echo ""
echo "Archivo generado: $INSTALL_DIR/$OUTPUT_FILE"
echo "Tamaño: $(du -h "$INSTALL_DIR/$OUTPUT_FILE" | cut -f1)"
echo ""
echo "Envía este archivo a: soporte@rhinometric.com"
echo ""
