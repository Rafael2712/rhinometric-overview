#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
#  GENERATE TRACES FOR TEMPO - RHINOMETRIC v2.2.0
# ═══════════════════════════════════════════════════════════════════════════

set -e

TEMPO_URL="http://localhost:4318"
OTEL_ENDPOINT="http://localhost:4317"

echo "🔍 Generando trazas de prueba para Tempo..."

# Function to generate a trace using OTLP HTTP
generate_trace_http() {
    local service_name=$1
    local operation=$2
    local duration_ms=$3
    local trace_id=$(openssl rand -hex 16)
    local span_id=$(openssl rand -hex 8)
    local timestamp=$(date +%s%N)
    
    curl -X POST "${TEMPO_URL}/v1/traces" \
        -H "Content-Type: application/json" \
        -d '{
            "resourceSpans": [{
                "resource": {
                    "attributes": [{
                        "key": "service.name",
                        "value": {"stringValue": "'${service_name}'"}
                    },{
                        "key": "service.version",
                        "value": {"stringValue": "2.2.0"}
                    },{
                        "key": "deployment.environment",
                        "value": {"stringValue": "production"}
                    }]
                },
                "scopeSpans": [{
                    "spans": [{
                        "traceId": "'${trace_id}'",
                        "spanId": "'${span_id}'",
                        "name": "'${operation}'",
                        "kind": 1,
                        "startTimeUnixNano": "'${timestamp}'",
                        "endTimeUnixNano": "'$((timestamp + duration_ms * 1000000))'",
                        "attributes": [{
                            "key": "http.method",
                            "value": {"stringValue": "GET"}
                        },{
                            "key": "http.status_code",
                            "value": {"intValue": 200}
                        },{
                            "key": "http.url",
                            "value": {"stringValue": "http://rhinometric.local/api/metrics"}
                        }]
                    }]
                }]
            }]
        }' 2>/dev/null
}

# Generate traces for different services
echo "📊 Generando trazas de Prometheus..."
for i in {1..5}; do
    generate_trace_http "rhinometric-prometheus" "query_metrics" $((RANDOM % 100 + 50))
    sleep 0.2
done

echo "📈 Generando trazas de Grafana..."
for i in {1..5}; do
    generate_trace_http "rhinometric-grafana" "render_dashboard" $((RANDOM % 200 + 100))
    sleep 0.2
done

echo "🔐 Generando trazas de License Server..."
for i in {1..5}; do
    generate_trace_http "rhinometric-license-server" "validate_license" $((RANDOM % 50 + 20))
    sleep 0.2
done

echo "🌱 Generando trazas de VeriVerde..."
for i in {1..5}; do
    generate_trace_http "rhinometric-veriverde" "collect_metrics" $((RANDOM % 80 + 40))
    sleep 0.2
done

echo "🤖 Generando trazas de AI Anomaly..."
for i in {1..5}; do
    generate_trace_http "rhinometric-ai-anomaly" "detect_anomalies" $((RANDOM % 150 + 100))
    sleep 0.2
done

echo "🔍 Generando trazas de API Proxy..."
for i in {1..5}; do
    generate_trace_http "rhinometric-api-proxy" "proxy_request" $((RANDOM % 60 + 30))
    sleep 0.2
done

echo ""
echo "✅ Trazas generadas exitosamente!"
echo ""
echo "🔗 Verifica en Grafana:"
echo "   http://localhost:3000/d/rhinometric-tracing"
echo ""
echo "🔗 O consulta directamente en Tempo:"
echo "   http://localhost:3200/api/search"
