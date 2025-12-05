#!/bin/bash
# check-health.sh - Script de verificación rápida para Rhinometric Trial

echo "🔍 Verificando servicios Rhinometric Trial..."
echo ""

services=(
    "http://localhost:3000|Grafana Dashboard"
    "http://localhost:9090/-/healthy|Prometheus"
    "http://localhost:3100/ready|Loki"
    "http://localhost:3200/ready|Tempo"
    "http://localhost:9093/-/healthy|Alertmanager"
    "http://localhost:8080|License Dashboard"
)

all_ok=true

for service in "${services[@]}"; do
    IFS='|' read -r url name <<< "$service"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [[ "$response" == "200" || "$response" == "302" ]]; then
        echo "✅ $name - OK (HTTP $response)"
    else
        echo "❌ $name - FALLO (HTTP ${response:-000})"
        all_ok=false
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════"

if [ "$all_ok" = true ]; then
    echo "✅ Todos los servicios están funcionando correctamente"
    exit 0
else
    echo "❌ Algunos servicios tienen problemas"
    echo ""
    echo "Ejecuta para ver logs:"
    echo "  docker compose -f docker-compose-trial.yml logs"
    exit 1
fi
