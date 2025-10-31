#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
#  CONTINUOUS TRACE GENERATOR FOR TEMPO - RHINOMETRIC v2.2.0
# ═══════════════════════════════════════════════════════════════════════════

OTLP_ENDPOINT="http://localhost:4318/v1/traces"

echo "🔍 RHINOMETRIC Continuous Trace Generator v2.2.0"
echo "============================================================"
echo "Endpoint: ${OTLP_ENDPOINT}"
echo "Generating traces every 30 seconds..."
echo "============================================================"
echo ""

SERVICES=(
    "rhinometric-grafana:render_dashboard:load_panel:query_datasource"
    "rhinometric-prometheus:query_range:query_instant:scrape_targets"
    "rhinometric-loki:push_logs:query_logs:tail_logs"
    "rhinometric-veriverde:collect_metrics:calculate_efficiency:read_sensors"
    "rhinometric-ai-anomaly:detect_anomalies:analyze_metrics:train_model"
    "rhinometric-license-server:validate_license:check_expiry:activate_trial"
    "rhinometric-api-proxy:proxy_request:auth_middleware:rate_limit"
    "rhinometric-postgres:execute_query:transaction_commit:vacuum"
    "rhinometric-nginx:handle_request:serve_static:proxy_upstream"
    "rhinometric-redis:get_cache:set_cache:pub_message"
)

generate_trace() {
    local service=$1
    local operation=$2
    local duration=$3
    local status_code=${4:-200}
    
    local trace_id=$(openssl rand -hex 16)
    local span_id=$(openssl rand -hex 8)
    local timestamp=$(date +%s%N)
    local end_timestamp=$((timestamp + duration * 1000000))
    
    local payload="{\"resourceSpans\":[{\"resource\":{\"attributes\":[{\"key\":\"service.name\",\"value\":{\"stringValue\":\"${service}\"}},{\"key\":\"service.version\",\"value\":{\"stringValue\":\"2.2.0\"}}]},\"scopeSpans\":[{\"spans\":[{\"traceId\":\"${trace_id}\",\"spanId\":\"${span_id}\",\"name\":\"${operation}\",\"kind\":1,\"startTimeUnixNano\":\"${timestamp}\",\"endTimeUnixNano\":\"${end_timestamp}\",\"attributes\":[{\"key\":\"http.method\",\"value\":{\"stringValue\":\"GET\"}},{\"key\":\"http.status_code\",\"value\":{\"intValue\":${status_code}}}],\"status\":{\"code\":1}}]}]}]}"
    
    curl -s -X POST "${OTLP_ENDPOINT}" \
        -H "Content-Type: application/json" \
        -d "${payload}" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "  ✅ ${service}/${operation} (${duration}ms, HTTP ${status_code})"
        return 0
    else
        echo "  ❌ Failed: ${service}/${operation}"
        return 1
    fi
}

iteration=0
while true; do
    iteration=$((iteration + 1))
    echo ""
    echo "[$(date +%H:%M:%S)] Iteration #${iteration}"
    
    success=0
    total=8
    
    for i in $(seq 1 ${total}); do
        # Select random service and operation
        service_data=${SERVICES[$RANDOM % ${#SERVICES[@]}]}
        IFS=':' read -ra parts <<< "$service_data"
        service_name="${parts[0]}"
        
        # Select random operation from this service
        ops_start=1
        ops_count=$((${#parts[@]} - 1))
        op_index=$((ops_start + RANDOM % ops_count))
        operation="${parts[$op_index]}"
        
        # Random duration and status
        duration=$((RANDOM % 490 + 10))
        status_code=$((RANDOM % 100 < 95 ? 200 : 500))
        
        if generate_trace "${service_name}" "${operation}" ${duration} ${status_code}; then
            success=$((success + 1))
        fi
        
        sleep 0.3
    done
    
    echo "  📊 Sent ${success}/${total} traces successfully"
    echo "  ⏳ Waiting 30 seconds for next batch..."
    
    sleep 30
done
