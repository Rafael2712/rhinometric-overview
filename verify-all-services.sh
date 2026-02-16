#!/bin/bash
# Verificar trazas de cada servicio individual

echo "=== VERIFICACION DE TRAZAS POR SERVICIO ==="
echo ""

services=("frontend-web" "api-gateway" "auth-service" "payment-service" "user-service" "notification-service" "inventory-service" "database-proxy" "telemetrygen")

for service in "${services[@]}"; do
    query="%7Bresource.service.name%3D%22${service}%22%7D"
    count=$(curl -s "http://localhost:3200/api/search?q=${query}&limit=200" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('traces', [])))")
    
    if [ "$count" -gt 0 ]; then
        echo "✅ $service: $count trazas"
    else
        echo "❌ $service: 0 trazas"
    fi
done

echo ""
echo "=== RESUMEN FINAL ==="
