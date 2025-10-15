#!/bin/bash

echo "🚀 Generando datos de demo para observabilidad enterprise..."

# Generar métricas con trazas simuladas
echo "📊 Generando métricas en Prometheus..."
for i in {1..100}; do
  # Simular requests al API
  curl -s http://localhost:3001/api/v1/health > /dev/null || echo "API request $i"
  
  # Generar métricas custom vía push gateway
  echo "rhinometric_demo_requests_total $((RANDOM % 1000 + 500))" | curl -s --data-binary @- http://localhost:9091/metrics/job/demo-app/instance/localhost:3001 || echo "Metrics $i sent"
  
  sleep 0.1
done

echo "�� Generando logs en Loki..."
# Generar logs JSON
for i in {1..50}; do
  LOG_LEVEL=$((i % 4 == 0 ? "ERROR" : i % 3 == 0 ? "WARN" : "INFO"))
  LOG_MSG="Demo log entry $i with level $LOG_LEVEL"
  
  echo "{\"timestamp\":\"$(date -Iseconds)\", \"level\":\"$LOG_LEVEL\", \"service\":\"rhinometric-api\", \"message\":\"$LOG_MSG\", \"user_id\":$((RANDOM % 100))}" | \
  curl -s -H "Content-Type: application/json" \
       -X POST "http://localhost:3100/loki/api/v1/push" \
       -d "{\"streams\":[{\"stream\":{\"job\":\"rhinometric-api\", \"level\":\"$LOG_LEVEL\"}, \"values\":[[\"$(date +%s)000000000\", \"$LOG_MSG\"]]}]}" || echo "Log $i sent"
  
  sleep 0.2
done

echo "✅ Datos de demo generados!"
