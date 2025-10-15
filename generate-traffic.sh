#!/bin/bash

# 🚀 SCRIPT GENERADOR DE TRÁFICO EMPRESARIAL
# Simula patrones reales de uso de la plataforma SaaS

echo "🎯 INICIANDO SIMULACIÓN DE TRÁFICO EMPRESARIAL..."

# Función para generar tráfico de autenticación
generate_auth_traffic() {
    echo "🔐 Generando tráfico de autenticación..."
    
    # Logins exitosos
    for i in {1..20}; do
        curl -s -X POST http://localhost:3001/api/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email":"admin@rhinometric.com","password":"admin123"}' > /dev/null &
        
        sleep 0.5
    done
    
    # Algunos logins fallidos para simular intentos reales
    for i in {1..5}; do
        curl -s -X POST http://localhost:3001/api/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email":"user@test.com","password":"wrongpassword"}' > /dev/null &
        
        sleep 1
    done
}

# Función para generar tráfico de API
generate_api_traffic() {
    echo "📊 Generando tráfico de endpoints API..."
    
    # Obtener token válido
    TOKEN=$(curl -s -X POST http://localhost:3001/api/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email":"admin@rhinometric.com","password":"admin123"}' | \
        jq -r '.token' 2>/dev/null || echo "fake-token")
    
    # Tráfico variado en endpoints
    endpoints=(
        "/api/users"
        "/api/organizations" 
        "/api/projects"
        "/api/metrics"
        "/api/health"
    )
    
    methods=("GET" "POST" "PUT")
    
    for i in {1..50}; do
        endpoint=${endpoints[$RANDOM % ${#endpoints[@]}]}
        method=${methods[$RANDOM % ${#methods[@]}]}
        
        if [[ $method == "GET" ]]; then
            curl -s -X GET "http://localhost:3001${endpoint}" \
            -H "Authorization: Bearer $TOKEN" > /dev/null &
        elif [[ $method == "POST" ]]; then
            curl -s -X POST "http://localhost:3001${endpoint}" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"test": true}' > /dev/null &
        else
            curl -s -X PUT "http://localhost:3001${endpoint}/1" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"updated": true}' > /dev/null &
        fi
        
        sleep $(echo "scale=2; $RANDOM/32767 * 2" | bc)
    done
}

# Función para generar errores controlados
generate_error_traffic() {
    echo "⚠️  Generando algunos errores para mostrar monitoring..."
    
    # 404s
    for i in {1..10}; do
        curl -s http://localhost:3001/api/nonexistent > /dev/null &
        sleep 1
    done
    
    # 500s (si el endpoint existe)
    for i in {1..3}; do
        curl -s -X POST http://localhost:3001/api/error-test > /dev/null &
        sleep 2
    done
}

# Función para tráfico continuo de health checks
generate_health_traffic() {
    echo "💚 Generando health checks continuo..."
    
    for i in {1..100}; do
        curl -s http://localhost:3001/api/health > /dev/null &
        curl -s http://localhost:3001/metrics > /dev/null &
        sleep 3
    done
}

# Ejecutar todas las funciones en paralelo
echo "🚀 EJECUTANDO SIMULACIÓN COMPLETA..."

# Ejecutar tráfico base
generate_health_traffic &
HEALTH_PID=$!

generate_auth_traffic &
AUTH_PID=$!

generate_api_traffic &
API_PID=$!

generate_error_traffic &
ERROR_PID=$!

echo "✅ Tráfico generándose en background..."
echo "📊 Ve a Grafana: http://localhost:3003"
echo "👀 Dashboards disponibles:"
echo "   - 🚀 Executive Dashboard: Métricas de negocio"
echo "   - 🔧 Technical Dashboard: Métricas técnicas"
echo ""
echo "⏱️  La simulación correrá por ~5 minutos..."
echo "🔄 Puedes ejecutar este script múltiples veces para más tráfico"

# Esperar un poco y mostrar métricas
sleep 10
echo ""
echo "📈 MUESTRA DE MÉTRICAS ACTUALES:"
curl -s http://localhost:3001/metrics | grep -E "(rhinometric_|process_|nodejs_)" | head -15

# Cleanup después de 5 minutos
sleep 300
kill $HEALTH_PID $AUTH_PID $API_PID $ERROR_PID 2>/dev/null

echo ""
echo "🎉 SIMULACIÓN COMPLETA - ¡Revisa los dashboards!"