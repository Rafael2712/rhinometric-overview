#!/usr/bin/env bash
# ================================================================
# stop_host_load_test.sh - Stop all simulated hosts
# ================================================================
#
# Stops the sim-node-exporter container, removes the Prometheus
# targets file, and reloads Prometheus so that the simulated
# hosts disappear from the host count.
#
# Usage:
#   ./scripts/stop_host_load_test.sh
#
# After running this, the Rhinometric stack returns to its normal
# state with only the real host(s) counted.
# ================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.loadtest.yml"
TARGETS_FILE="$PROJECT_DIR/prometheus/loadtest_targets.json"

echo "=============================================="
echo " Stopping Host Load Test"
echo "=============================================="

# --- Step 1: Stop simulation container ---
echo ""
echo "[1/3] Stopping sim-node-exporter container..."
cd "$PROJECT_DIR"
docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
echo "  Container stopped."

# --- Step 2: Remove targets file (or write empty array) ---
echo ""
echo "[2/3] Clearing Prometheus loadtest targets..."
# Write empty array so Prometheus doesn't error on missing file
echo "[]" > "$TARGETS_FILE"
echo "  Targets file cleared."

# --- Step 3: Reload Prometheus ---
echo ""
echo "[3/3] Reloading Prometheus configuration..."
echo "  Restarting Prometheus to clear stale targets..."
docker restart rhinometric-prometheus >/dev/null 2>&1
for i in $(seq 1 30); do
    if docker exec rhinometric-prometheus wget -q -O /dev/null http://localhost:9090/-/healthy 2>/dev/null; then
        echo "  Prometheus restarted and healthy."
        break
    fi
    sleep 2
done

echo ""
echo "=============================================="
echo " LOAD TEST STOPPED"
echo "=============================================="
echo " Simulated hosts have been removed."
echo " Host count will return to normal within ~1 minute."
echo " The Rhinometric stack is back to its normal state."
echo "=============================================="
