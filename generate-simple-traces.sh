#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
#  GENERATE SIMPLE TRACES FOR TEMPO - RHINOMETRIC v2.2.0
# ═══════════════════════════════════════════════════════════════════════════

echo "🔍 Generando trazas de prueba para Tempo..."
echo ""

# Usar el puerto interno de OTLP collector (4317)
OTEL_ENDPOINT="http://localhost:4317"

# Function to generate trace using curl to Tempo's HTTP API
generate_trace() {
    local service=$1
    local operation=$2
    local duration_ms=$3
    
    # Generate IDs
    local trace_id=$(openssl rand -hex 16)
    local span_id=$(openssl rand -hex 8)
    local timestamp=$(date +%s%N)
    local end_timestamp=$((timestamp + duration_ms * 1000000))
    
    echo "📊 Generando traza: ${service}/${operation} (${duration_ms}ms)"
    
    # Use Jaeger's HTTP endpoint which is simpler
    curl -X POST "http://localhost:14268/api/traces" \
        -H "Content-Type: application/json" \
        -d '{
            "data": [{
                "traceID": "'${trace_id}'",
                "spans": [{
                    "traceID": "'${trace_id}'",
                    "spanID": "'${span_id}'",
                    "operationName": "'${operation}'",
                    "startTime": '${timestamp}',
                    "duration": '${duration_ms}'000,
                    "tags": [
                        {"key": "service.name", "type": "string", "value": "'${service}'"},
                        {"key": "http.method", "type": "string", "value": "GET"},
                        {"key": "http.status_code", "type": "int64", "value": 200}
                    ],
                    "logs": []
                }],
                "processes": {
                    "p1": {
                        "serviceName": "'${service}'",
                        "tags": [
                            {"key": "version", "type": "string", "value": "2.2.0"}
                        ]
                    }
                }
            }]
        }' 2>/dev/null
    
    sleep 0.3
}

# Generate traces for different services
echo "📈 Servicios Grafana..."
for i in {1..3}; do
    generate_trace "rhinometric-grafana" "render_dashboard" $((RANDOM % 200 + 100))
done

echo ""
echo "📊 Servicios Prometheus..."
for i in {1..3}; do
    generate_trace "rhinometric-prometheus" "query_metrics" $((RANDOM % 100 + 50))
done

echo ""
echo "🌱 Servicios VeriVerde..."
for i in {1..3}; do
    generate_trace "rhinometric-veriverde" "collect_sustainability_metrics" $((RANDOM % 80 + 40))
done

echo ""
echo "🤖 Servicios AI Anomaly..."
for i in {1..3}; do
    generate_trace "rhinometric-ai-anomaly" "detect_anomalies" $((RANDOM % 150 + 100))
done

echo ""
echo "🔐 Servicios License Server..."
for i in {1..3}; do
    generate_trace "rhinometric-license-server" "validate_license" $((RANDOM % 50 + 20))
done

echo ""
echo "✅ Trazas generadas exitosamente!"
echo ""
echo "🔗 Verifica en Grafana:"
echo "   http://localhost:3000/explore"
echo "   Selecciona 'Tempo' como datasource"
echo ""
echo "🔗 O consulta directamente:"
echo "   http://localhost:3200/api/search"
