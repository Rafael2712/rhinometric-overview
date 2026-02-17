#!/usr/bin/env bash
# ================================================================
# run_host_load_test.sh - Start simulated hosts for load testing
# ================================================================
#
# Simulates N hosts by running lightweight node_exporter instances.
# Each host gets a unique port (9200+) and unique instance label.
#
# Usage:
#   ./scripts/run_host_load_test.sh 20    # Start 20 simulated hosts
#   ./scripts/run_host_load_test.sh 50    # Scale to 50 hosts
#   ./scripts/run_host_load_test.sh 70    # Scale to 70 hosts
#   ./scripts/run_host_load_test.sh 100   # Scale to 100 hosts
#
# What it does:
#   1. Generates Prometheus file_sd targets for N hosts
#   2. Starts/restarts the sim-node-exporter container with N hosts
#   3. Reloads Prometheus to pick up the new targets
#
# To stop: ./scripts/stop_host_load_test.sh
# ================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.loadtest.yml"
TARGETS_FILE="$PROJECT_DIR/prometheus/loadtest_targets.json"

# --- Parse arguments ---
NUM_HOSTS=${1:-}
if [[ -z "$NUM_HOSTS" ]]; then
    echo "Usage: $0 <num_hosts>"
    echo "  Example: $0 20"
    echo "  Valid range: 1 to 100"
    exit 1
fi

if [[ "$NUM_HOSTS" -lt 1 || "$NUM_HOSTS" -gt 100 ]]; then
    echo "Error: num_hosts must be between 1 and 100"
    exit 1
fi

echo "=============================================="
echo " Rhinometric Host Load Test"
echo " Simulating $NUM_HOSTS hosts"
echo "=============================================="

# --- Step 1: Generate Prometheus file_sd targets ---
echo ""
echo "[1/3] Generating Prometheus targets for $NUM_HOSTS hosts..."

# Build JSON array of targets
# Each simulated host listens on port 9200 + (host_id - 1)
# The container name is rhinometric-sim-node-exporter on the docker network
python3 -c "
import json
targets = []
for i in range(1, $NUM_HOSTS + 1):
    port = 9200 + i - 1
    targets.append({
        'targets': [f'rhinometric-sim-node-exporter:{port}'],
        'labels': {
            'env': 'loadtest',
            'rhinometric_role': 'simulated-host',
            'sim_host_id': f'sim-host-{i:03d}'
        }
    })
with open('$TARGETS_FILE', 'w') as f:
    json.dump(targets, f, indent=2)
print(f'  Written {len(targets)} targets to $TARGETS_FILE')
"

# --- Step 2: Verify Prometheus config has file_sd_configs ---
PROM_CONFIG="$PROJECT_DIR/config/prometheus-v2.2.yml"
if grep -q 'loadtest_targets.json' "$PROM_CONFIG"; then
    echo "  Prometheus config already has loadtest file_sd_configs."
else
    echo "  WARNING: Prometheus config missing loadtest_targets.json reference!"
    echo "  The file_sd_configs block should already be in the node-exporter job."
    echo "  Check config/prometheus-v2.2.yml manually."
fi

# --- Step 3: Start/restart the simulation container ---
echo ""
echo "[2/3] Starting sim-node-exporter container with $NUM_HOSTS hosts..."

cd "$PROJECT_DIR"

# Stop existing container if running
docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true

# Start with the specified number of hosts
NUM_HOSTS=$NUM_HOSTS docker-compose -f "$COMPOSE_FILE" up -d

echo "  Container started."

# --- Step 4: Reload Prometheus ---
echo ""
echo "[3/3] Reloading Prometheus configuration..."

# Wait a moment for the container to start
sleep 2

# Reload Prometheus (file_sd_configs auto-refreshes every 15s,
# but restart ensures immediate pickup)
echo "  Restarting Prometheus to pick up new targets..."
docker restart rhinometric-prometheus >/dev/null 2>&1
# Wait for Prometheus to be healthy
for i in $(seq 1 30); do
    if docker exec rhinometric-prometheus wget -q -O /dev/null http://localhost:9090/-/healthy 2>/dev/null; then
        echo "  Prometheus is healthy."
        break
    fi
    sleep 2
done

# --- Summary ---
echo ""
echo "=============================================="
echo " LOAD TEST ACTIVE"
echo "=============================================="
echo " Simulated hosts:  $NUM_HOSTS"
echo " Port range:       9200 - $((9200 + NUM_HOSTS - 1))"
echo " Targets file:     $TARGETS_FILE"
echo " Container:        rhinometric-sim-node-exporter"
echo ""
echo " The hosts should appear in Prometheus within ~30s."
echo " Check License page for updated host count."
echo ""
echo " Monitor resources:"
echo "   docker stats rhinometric-sim-node-exporter"
echo "   free -h"
echo ""
echo " To stop the test:"
echo "   ./scripts/stop_host_load_test.sh"
echo "=============================================="
