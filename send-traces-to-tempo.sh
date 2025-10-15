#!/bin/bash

echo "🔥 Generando TRAZAS reales para Tempo..."

# Generar trazas usando OpenTelemetry formato JSON
for i in {1..10}; do
    TRACE_ID=$(openssl rand -hex 16)
    SPAN_ID=$(openssl rand -hex 8)
    TIMESTAMP=$(date +%s)000000000  # Nanoseconds
    
    # Simular diferentes servicios
    SERVICE_NAME=$([ $((i % 3)) -eq 0 ] && echo "rhinometric-api" || [ $((i % 2)) -eq 0 ] && echo "rhinometric-db" || echo "rhinometric-cache")
    OPERATION_NAME=$([ $((i % 3)) -eq 0 ] && echo "GET /api/users" || [ $((i % 2)) -eq 0 ] && echo "SELECT users" || echo "CACHE lookup")
    
    # Enviar traza a Tempo vía OTLP HTTP
    curl -X POST "http://localhost:4318/v1/traces" \
         -H "Content-Type: application/json" \
         -d "{
             \"resourceSpans\": [{
                 \"resource\": {
                     \"attributes\": [{
                         \"key\": \"service.name\",
                         \"value\": {\"stringValue\": \"$SERVICE_NAME\"}
                     }, {
                         \"key\": \"service.version\",
                         \"value\": {\"stringValue\": \"1.0.0\"}
                     }]
                 },
                 \"scopeSpans\": [{
                     \"spans\": [{
                         \"traceId\": \"$TRACE_ID\",
                         \"spanId\": \"$SPAN_ID\",
                         \"name\": \"$OPERATION_NAME\",
                         \"kind\": 1,
                         \"startTimeUnixNano\": \"$TIMESTAMP\",
                         \"endTimeUnixNano\": \"$(($TIMESTAMP + 50000000))\",
                         \"attributes\": [{
                             \"key\": \"http.method\",
                             \"value\": {\"stringValue\": \"GET\"}
                         }, {
                             \"key\": \"http.status_code\",
                             \"value\": {\"intValue\": \"200\"}
                         }]
                     }]
                 }]
             }]
         }"
    
    echo "✅ Traza $i enviada: $SERVICE_NAME -> $OPERATION_NAME"
    sleep 0.5
done

echo "🎉 Trazas enterprise enviadas a Tempo!"