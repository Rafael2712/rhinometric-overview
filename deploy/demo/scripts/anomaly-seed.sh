#!/bin/bash
# anomaly-seed.sh - Genera trÃ¡fico para dashboards con datos visibles

set -euo pipefail

API_URL="${API_URL:-http://localhost:8085}"
INTERVAL="${INTERVAL:-90}"

echo "í¼± Anomaly Seed - Generando datos para dashboards"
echo "API: $API_URL | Intervalo: ${INTERVAL}s"

while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Enviando mÃ©tricas..."
    
    # CPU Usage (50-95%)
    CPU=$(awk -v min=50 -v max=95 'BEGIN{srand(); print min+rand()*(max-min)}')
    curl -s -X POST "$API_URL/detect/node_cpu_usage" \
        -H "Content-Type: application/json" \
        -d "{\"value\": $CPU, \"timestamp\": $(date +%s)}" > /dev/null
    
    # API Latency (100-500ms)
    LATENCY=$(awk -v min=100 -v max=500 'BEGIN{srand(); print int(min+rand()*(max-min))}')
    curl -s -X POST "$API_URL/detect/api_latency" \
        -H "Content-Type: application/json" \
        -d "{\"value\": $LATENCY, \"timestamp\": $(date +%s)}" > /dev/null
    
    # Memory Pressure (60-90%)
    MEM=$(awk -v min=60 -v max=90 'BEGIN{srand(); print min+rand()*(max-min)}')
    curl -s -X POST "$API_URL/detect/memory_pressure" \
        -H "Content-Type: application/json" \
        -d "{\"value\": $MEM, \"timestamp\": $(date +%s)}" > /dev/null
    
    # Error Rate (0.1-5%)
    ERROR=$(awk -v min=0.1 -v max=5 'BEGIN{srand(); print min+rand()*(max-min)}')
    curl -s -X POST "$API_URL/detect/error_rate" \
        -H "Content-Type: application/json" \
        -d "{\"value\": $ERROR, \"timestamp\": $(date +%s)}" > /dev/null
    
    # Disk I/O Wait (5-25%)
    DISK=$(awk -v min=5 -v max=25 'BEGIN{srand(); print min+rand()*(max-min)}')
    curl -s -X POST "$API_URL/detect/disk_io_wait" \
        -H "Content-Type: application/json" \
        -d "{\"value\": $DISK, \"timestamp\": $(date +%s)}" > /dev/null
    
    echo "âœ“ MÃ©tricas enviadas (CPU:${CPU}%, Latency:${LATENCY}ms, Mem:${MEM}%, Err:${ERROR}%, Disk:${DISK}%)"
    
    sleep "$INTERVAL"
done
