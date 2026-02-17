#!/usr/bin/env bash
# =============================================================
# stop_host_load_test.sh - Stop all simulated hosts
# =============================================================
#
# Stops the sim-node-exporter container, clears Prometheus targets,
# restarts Prometheus, and WAITS until the host count drops back
# to baseline (1 real host).
#
# Usage:
#   ./scripts/stop_host_load_test.sh          # Wait for cleanup
#   ./scripts/stop_host_load_test.sh --no-wait  # Don't wait
#
# Prometheus has a 5-minute staleness window: after the last scrape,
# series remain queryable for 5 minutes. This script polls until
# the count is back to normal so you don't see ghost hosts.
# =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.loadtest.yml"
TARGETS_FILE="$PROJECT_DIR/prometheus/loadtest_targets.json"
WAIT_FOR_CLEANUP=true
MAX_WAIT=360  # 6 minutes max (staleness is 5 min)

# Parse args
if [[ "${1:-}" == "--no-wait" ]]; then
    WAIT_FOR_CLEANUP=false
fi

echo "=============================================="
echo " Stopping Host Load Test"
echo "=============================================="

# --- Step 1: Stop simulation container ---
echo ""
echo "[1/4] Stopping sim-node-exporter container..."
cd "$PROJECT_DIR"
docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
echo "  Container stopped."

# --- Step 2: Clear targets file ---
echo ""
echo "[2/4] Clearing Prometheus loadtest targets..."
echo "[]" > "$TARGETS_FILE"
echo "  Targets file cleared."

# --- Step 3: Restart Prometheus ---
echo ""
echo "[3/4] Restarting Prometheus..."
docker restart rhinometric-prometheus >/dev/null 2>&1
# Wait for Prometheus to be healthy
for i in $(seq 1 30); do
    if docker exec rhinometric-prometheus wget -q -O /dev/null http://localhost:9090/-/healthy 2>/dev/null; then
        echo "  Prometheus is healthy."
        break
    fi
    sleep 2
done

# --- Step 4: Wait for staleness to clear ---
if $WAIT_FOR_CLEANUP; then
    echo ""
    echo "[4/4] Waiting for Prometheus staleness window to clear..."
    echo "  (Prometheus keeps stale series for ~5 minutes after last scrape)"
    echo ""

    ELAPSED=0
    INTERVAL=10
    while [ $ELAPSED -lt $MAX_WAIT ]; do
        # Query current host count
        COUNT=$(docker exec rhinometric-prometheus wget -q -O- \
            'http://localhost:9090/api/v1/query?query=count(count%20by%20(instance)%20(up%7Bjob%3D%22node-exporter%22%7D))' 2>/dev/null \
            | python3 -c "import sys,json; d=json.load(sys.stdin); r=d['data']['result']; print(r[0]['value'][1] if r else '0')" 2>/dev/null \
            || echo "?")

        if [ "$COUNT" = "1" ]; then
            echo "  ✓ Host count is back to 1 (baseline). Clean!"
            break
        fi

        REMAINING=$((MAX_WAIT - ELAPSED))
        echo "  Host count: $COUNT (waiting for staleness... ${REMAINING}s remaining)"
        sleep $INTERVAL
        ELAPSED=$((ELAPSED + INTERVAL))
    done

    if [ "$COUNT" != "1" ]; then
        echo "  ⚠ Host count still at $COUNT after ${MAX_WAIT}s."
        echo "  This is unusual. Try: docker restart rhinometric-prometheus"
    fi
else
    echo ""
    echo "[4/4] Skipping wait (--no-wait flag)."
    echo "  ⚠ Stale hosts may appear in License for up to 5 minutes."
fi

echo ""
echo "=============================================="
echo " LOAD TEST STOPPED"
echo "=============================================="
echo " Simulated hosts have been removed."
if $WAIT_FOR_CLEANUP; then
    echo " Host count is back to baseline."
else
    echo " Host count will return to normal within ~5 minutes."
fi
echo " The Rhinometric stack is back to its normal state."
echo "=============================================="
