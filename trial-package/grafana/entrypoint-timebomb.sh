#!/bin/bash
#
# Grafana Entrypoint con Time-Bomb Validator
# Inicia Grafana y el validador de licencia en background
#

set -e

# Variables de entorno
export SERVICE_NAME="grafana"
export LICENSE_SERVER_URL="${LICENSE_SERVER_URL:-http://license-server:5000}"
export LICENSE_KEY="${LICENSE_KEY:-/data/.license_key}"
export VALIDATION_INTERVAL="${VALIDATION_INTERVAL:-21600}"  # 6 horas

echo "🚀 Starting Rhinometric Grafana with Time-Bomb protection"
echo "📁 License Key: $LICENSE_KEY"
echo "🔒 License Server: $LICENSE_SERVER_URL"
echo "⏰ Validation Interval: $(($VALIDATION_INTERVAL / 3600)) hours"

# Verificar que existe el license key file
if [ ! -f "$LICENSE_KEY" ]; then
    echo "⚠️  License key not found, attempting to generate..."
    
    # Intentar generar licencia trial
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"client_name":"Rhinometric Trial","type":"trial"}' \
        "$LICENSE_SERVER_URL/generate" 2>&1 || echo '{"error":"failed"}')
    
    license=$(echo "$response" | grep -o '"license_key":"[^"]*"' | cut -d'"' -f4)
    
    if [ ! -z "$license" ] && [ "$license" != "failed" ]; then
        echo "$license" > "$LICENSE_KEY"
        chmod 600 "$LICENSE_KEY"
        echo "✅ License generated and saved"
    else
        echo "❌ Failed to generate license - starting anyway (will shutdown after 60s)"
    fi
fi

# Iniciar Time-Bomb validator en background
if [ -f "/opt/timebomb_validator.sh" ]; then
    echo "🔒 Starting Time-Bomb validator..."
    bash /opt/timebomb_validator.sh &
    TIMEBOMB_PID=$!
    echo "   Validator PID: $TIMEBOMB_PID"
else
    echo "⚠️  Time-Bomb validator script not found!"
fi

# Iniciar Grafana (exec para que reciba señales)
echo "🚀 Starting Grafana server..."
exec /run.sh "$@"
