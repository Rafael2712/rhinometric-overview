#!/bin/bash
# Script para generar trazas variadas con telemetrygen para testing de Tempo/Grafana

echo "🚀 Iniciando generación de trazas variadas..."

# Array de servicios simulados
SERVICES=("frontend-web" "api-gateway" "auth-service" "user-service" "payment-service" "inventory-service" "notification-service" "database-proxy")

# Array de operaciones HTTP
OPERATIONS=("GET /api/users" "POST /api/orders" "PUT /api/profile" "DELETE /api/cart" "GET /api/products" "POST /api/payment" "GET /api/inventory" "POST /api/login")

# Función para generar trazas para un servicio
generate_service_traces() {
    local service=$1
    local operation=$2
    local rate=$3
    local duration=$4
    
    echo "📊 Generando trazas para $service ($operation) - Rate: $rate/s, Duration: ${duration}s"
    
    docker exec rhinometric-telemetrygen telemetrygen traces \
        --otlp-endpoint=tempo:4317 \
        --otlp-insecure \
        --rate=$rate \
        --duration=${duration}s \
        --service-name="$service" \
        --trace-name="$operation" \
        --status-code=0 \
        --workers=1 \
        > /dev/null 2>&1 &
}

# Generar trazas de fondo para múltiples servicios simultáneamente
echo ""
echo "🔧 Configurando generación de trazas de múltiples microservicios..."
echo ""

# Frontend web - alto tráfico
generate_service_traces "frontend-web" "GET /home" 5 30 &
sleep 1

# API Gateway - tráfico medio
generate_service_traces "api-gateway" "POST /api/v1/request" 3 30 &
sleep 1

# Auth service - tráfico bajo
generate_service_traces "auth-service" "POST /api/auth/login" 2 30 &
sleep 1

# User service - tráfico medio
generate_service_traces "user-service" "GET /api/users/:id" 3 30 &
sleep 1

# Payment service - tráfico bajo (crítico)
generate_service_traces "payment-service" "POST /api/payments/process" 1 30 &
sleep 1

# Inventory service - tráfico alto
generate_service_traces "inventory-service" "GET /api/products/search" 4 30 &
sleep 1

# Notification service - tráfico medio
generate_service_traces "notification-service" "POST /api/notifications/send" 2 30 &
sleep 1

# Database proxy - tráfico alto
generate_service_traces "database-proxy" "QUERY SELECT * FROM users" 5 30 &

echo ""
echo "✅ Generando trazas para 8 microservicios simultáneamente"
echo "⏱️  Duración: 30 segundos"
echo "📈 Total estimado: ~750 trazas nuevas"
echo ""
echo "📊 Desglose por servicio:"
echo "   - frontend-web: 150 trazas (5/s)"
echo "   - api-gateway: 90 trazas (3/s)"
echo "   - auth-service: 60 trazas (2/s)"
echo "   - user-service: 90 trazas (3/s)"
echo "   - payment-service: 30 trazas (1/s)"
echo "   - inventory-service: 120 trazas (4/s)"
echo "   - notification-service: 60 trazas (2/s)"
echo "   - database-proxy: 150 trazas (5/s)"
echo ""
echo "⏳ Espera 30 segundos y luego verifica en Grafana Explore → Tempo"
echo ""
echo "🔍 Consultas sugeridas en Grafana:"
echo "   - {} (todas las trazas)"
echo "   - {service.name=\"frontend-web\"}"
echo "   - {service.name=\"payment-service\"}"
echo "   - {span.name=\"POST /api/payments/process\"}"
echo ""

# Esperar a que terminen todos los procesos
wait

echo "✅ ¡Generación completada! Revisa Grafana ahora."
