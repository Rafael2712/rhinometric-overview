#!/bin/bash
#
# Prometheus Entrypoint con Time-Bomb Validator
#

set -e

export SERVICE_NAME="prometheus"
export LICENSE_SERVER_URL="${LICENSE_SERVER_URL:-http://license-server:5000}"
export LICENSE_KEY="${LICENSE_KEY:-/data/.license_key}"
export VALIDATION_INTERVAL="${VALIDATION_INTERVAL:-21600}"

echo "🚀 Starting Rhinometric Prometheus with Time-Bomb protection"

# Generar licencia si no existe
if [ ! -f "$LICENSE_KEY" ]; then
    echo "⚠️  License key not found, attempting to generate..."
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"client_name":"Rhinometric Trial","type":"trial"}' \
        "$LICENSE_SERVER_URL/generate" 2>&1 || echo '{"error":"failed"}')
    
    license=$(echo "$response" | grep -o '"license_key":"[^"]*"' | cut -d'"' -f4)
    if [ ! -z "$license" ]; then
        echo "$license" > "$LICENSE_KEY"
        chmod 600 "$LICENSE_KEY"
        echo "✅ License generated"
    fi
fi

# Iniciar Time-Bomb validator
if [ -f "/opt/timebomb_validator.sh" ]; then
    echo "🔒 Starting Time-Bomb validator..."
    bash /opt/timebomb_validator.sh &
fi

# Iniciar Prometheus
echo "🚀 Starting Prometheus server..."
exec /bin/prometheus \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/prometheus \
    --web.console.libraries=/etc/prometheus/console_libraries \
    --web.console.templates=/etc/prometheus/consoles \
    --web.enable-lifecycle \
    "$@"
