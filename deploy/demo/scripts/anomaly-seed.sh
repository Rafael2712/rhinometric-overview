#!/bin/bash
# anomaly-seed.sh - Generador de anomalÃ­as REAL con picos forzados
# Rhinometric v2.5.0 - Garantiza datos >0 en dashboards AI en <3 min

set -euo pipefail

API_URL="${API_URL:-http://localhost:8085}"
INTERVAL="${INTERVAL:-60}"
LOG_FILE="${LOG_FILE:-/tmp/anomaly-seed.log}"

mkdir -p "$(dirname "$LOG_FILE")"

echo "í¼± Rhinometric Anomaly Seed v2.5.0" | tee "$LOG_FILE"
echo "API: $API_URL | Intervalo: ${INTERVAL}s" | tee -a "$LOG_FILE"
echo "=================================" | tee -a "$LOG_FILE"

ITERATION=0

while true; do
    ITERATION=$((ITERATION + 1))
    TIMESTAMP=$(date +%s)
    echo "" | tee -a "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] IteraciÃ³n #$ITERATION" | tee -a "$LOG_FILE"
    
    # Cada 5 iteraciones: FORZAR ANOMALÃA
    if [ $((ITERATION % 5)) -eq 0 ]; then
        CPU=$(awk 'BEGIN{srand(); print 85 + rand()*15}')  # 85-100%
        MEM=$(awk 'BEGIN{srand(); print 85 + rand()*15}')
        LATENCY=$(awk 'BEGIN{srand(); print int(800 + rand()*500)}')  # 800-1300ms
        ERROR=$(awk 'BEGIN{srand(); print 8 + rand()*7}')  # 8-15%
        DISK=$(awk 'BEGIN{srand(); print 40 + rand()*30}')
        echo "âš ï¸  ANOMALÃA FORZADA (pico detectado)" | tee -a "$LOG_FILE"
    else
        # Valores normales
        CPU=$(awk 'BEGIN{srand(); print 20 + rand()*40}')  # 20-60%
        MEM=$(awk 'BEGIN{srand(); print 40 + rand()*30}')
        LATENCY=$(awk 'BEGIN{srand(); print int(100 + rand()*200)}')  # 100-300ms
        ERROR=$(awk 'BEGIN{srand(); print 0.1 + rand()*2}')  # 0.1-2.1%
        DISK=$(awk 'BEGIN{srand(); print 5 + rand()*15}')
    fi
    
    # POST a AI Anomaly Detection
    for METRIC in "node_cpu_usage:$CPU" "api_latency:$LATENCY" "memory_pressure:$MEM" "error_rate:$ERROR" "disk_io_wait:$DISK"; do
        METRIC_NAME="${METRIC%%:*}"
        METRIC_VALUE="${METRIC##*:}"
        
        HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$API_URL/detect/$METRIC_NAME" \
            -H "Content-Type: application/json" \
            -d "{\"value\": $METRIC_VALUE, \"timestamp\": $TIMESTAMP}" 2>/dev/null || echo "000")
        
        if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
            echo "  âœ“ $METRIC_NAME: $METRIC_VALUE (HTTP $HTTP_CODE)" | tee -a "$LOG_FILE"
        else
            echo "  âœ— $METRIC_NAME: FALLÃ“ (HTTP $HTTP_CODE)" | tee -a "$LOG_FILE"
        fi
    done
    
    echo "í³Š CPU:${CPU}%, Mem:${MEM}%, Latency:${LATENCY}ms, Err:${ERROR}%, Disk:${DISK}%" | tee -a "$LOG_FILE"
    
    # Cada 3 iteraciones: verificar detecciones acumuladas
    if [ $((ITERATION % 3)) -eq 0 ]; then
        DETECTIONS=$(curl -s "$API_URL/metrics" 2>/dev/null | grep "rhinometric_anomaly_detections_total" | awk '{print $2}' | head -1 || echo "0")
        echo "í´ Detecciones acumuladas: $DETECTIONS" | tee -a "$LOG_FILE"
        
        if (( $(echo "$DETECTIONS > 0" | bc -l 2>/dev/null || echo 0) )); then
            echo "âœ… AI ANOMALY DETECTION OPERATIVO" | tee -a "$LOG_FILE"
        fi
    fi
    
    sleep "$INTERVAL"
done
