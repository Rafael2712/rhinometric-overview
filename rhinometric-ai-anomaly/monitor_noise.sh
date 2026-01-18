#!/bin/bash
# Monitor de Ruido - AI Anomaly Detection
# Captura snapshots cada 10min durante 30min

API_URL="http://localhost:8085"
OUTPUT_FILE="/tmp/noise_test_$(date +%Y%m%d_%H%M%S).txt"

echo "=== NOISE TEST STARTED ===" | tee $OUTPUT_FILE
echo "Timestamp: $(date)" | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

for i in {0..3}; do
    TIMESTAMP=$(date +"%H:%M:%S")
    echo "=== Snapshot t=${i}0min ($TIMESTAMP) ===" | tee -a $OUTPUT_FILE
    
    # Capturar estado de anomalías
    curl -s $API_URL/anomalies | python -c "
import sys, json
from collections import Counter

data = json.load(sys.stdin)
active = data.get('active_count', 0)
total = len(data['anomalies'])

print(f'Active: {active}')
print(f'Total stored: {total}')

if data['anomalies']:
    metrics = [a['metric_name'] for a in data['anomalies']]
    severities = [a['severity'] for a in data['anomalies']]
    
    print('\nTop 5 metrics:')
    for m, c in Counter(metrics).most_common(5):
        print(f'  {m}: {c}')
    
    print('\nBy severity:')
    for s, c in Counter(severities).most_common():
        print(f'  {s}: {c}')
" | tee -a $OUTPUT_FILE
    
    # Capturar total detections
    echo "" | tee -a $OUTPUT_FILE
    curl -s $API_URL/metrics | grep "rhinometric_anomaly_detections_total{" | \
        grep -v created | awk '{print $NF}' | \
        awk '{s+=$1} END {print "Total detections counter: " s}' | tee -a $OUTPUT_FILE
    
    echo "---" | tee -a $OUTPUT_FILE
    
    # Esperar 10 minutos (excepto última iteración)
    if [ $i -lt 3 ]; then
        echo "Waiting 10 minutes..." | tee -a $OUTPUT_FILE
        sleep 600
    fi
done

echo "" | tee -a $OUTPUT_FILE
echo "=== NOISE TEST COMPLETED ===" | tee -a $OUTPUT_FILE
echo "Results saved to: $OUTPUT_FILE" | tee -a $OUTPUT_FILE

# Calcular tasa de ruido
echo "" | tee -a $OUTPUT_FILE
echo "=== ANALYSIS ===" | tee -a $OUTPUT_FILE
echo "Test duration: 30 minutes" | tee -a $OUTPUT_FILE
echo "Expected anomalies/hour (extrapolated from 30min data)" | tee -a $OUTPUT_FILE
