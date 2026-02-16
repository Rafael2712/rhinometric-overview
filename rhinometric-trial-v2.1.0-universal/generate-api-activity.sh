#!/bin/bash
# Script para generar actividad en las APIs y mejorar visualización del dashboard

echo "🚀 Generando actividad en las APIs externas..."
echo "Esto ayudará a visualizar mejor los datos en el dashboard"
echo ""

# Función para hacer requests a través del API Proxy
call_api() {
    local api_name=$1
    curl -s "http://localhost:8090/api/proxy/$api_name" > /dev/null
    if [ $? -eq 0 ]; then
        echo "✓ Called $api_name"
    else
        echo "✗ Error calling $api_name"
    fi
}

echo "Generando 30 requests a cada API (esto tomará ~2 minutos)..."
echo ""

for i in {1..30}; do
    echo "Batch $i/30..."
    call_api "openweather" &
    call_api "github_status" &
    call_api "coindesk_btc" &
    wait
    sleep 2
done

echo ""
echo "✅ Actividad generada!"
echo ""
echo "📊 Ahora actualiza el dashboard en Grafana:"
echo "   http://localhost:3000/d/external-apis/f09f8c90-external-apis-monitoring"
echo ""
echo "Deberías ver:"
echo "  - Request rate aumentado"
echo "  - Cache hit rate > 80%"
echo "  - Success/Error counts más visibles"
