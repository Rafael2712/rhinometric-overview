#!/bin/bash

# 🚀 GENERADOR DE TRÁFICO COMPLETO PARA MÉTRICAS SAAS
echo "🎯 GENERANDO TRÁFICO PARA COMPLETAR MÉTRICAS DE DASHBOARDS..."

# Función para generar autenticación exitosa y fallida
generate_auth_metrics() {
    echo "🔐 Generando métricas de autenticación..."
    
    # 15 logins exitosos
    for i in {1..15}; do
        curl -s -X POST http://localhost:3001/api/v1/auth/login \
        -H "Content-Type: application/json" \
        -d '{"username":"admin","password":"admin123"}' > /dev/null
        sleep 0.3
    done
    
    # 8 logins fallidos para mostrar failure rate
    for i in {1..8}; do
        curl -s -X POST http://localhost:3001/api/v1/auth/login \
        -H "Content-Type: application/json" \
        -d '{"username":"hacker","password":"wrongpass"}' > /dev/null
        sleep 0.4
    done
}

# Función para generar tráfico HTTP variado
generate_http_traffic() {
    echo "📊 Generando tráfico HTTP para SLA compliance..."
    
    endpoints=(
        "/api/v1/health"
        "/api/v1/auth/config" 
        "/"
        "/api/v1/auth/verify"
        "/metrics"
    )
    
    # 100 requests exitosos  
    for i in {1..100}; do
        endpoint=${endpoints[$RANDOM % ${#endpoints[@]}]}
        
        if [[ $endpoint == "/api/v1/auth/verify" ]]; then
            # Necesita token para este endpoint, usar token dummy o omitir
            continue
        fi
        
        curl -s http://localhost:3001${endpoint} > /dev/null
        
        # Variar velocidad para simular tráfico real
        sleep $(echo "scale=2; $RANDOM/32767 * 1.5" | bc -l 2>/dev/null || echo "0.5")
    done
}

# Función para generar algunos errores 500 para SLA
generate_error_traffic() {
    echo "⚠️ Generando algunos errores para métricas de SLA..."
    
    # Requests a endpoints inexistentes (404s)
    for i in {1..15}; do
        curl -s http://localhost:3001/api/v1/nonexistent > /dev/null
        curl -s http://localhost:3001/fake-endpoint > /dev/null
        sleep 1
    done
}

# Función para hacer scraping continuo de métricas (simula Prometheus)
continuous_metrics_scraping() {
    echo "📈 Iniciando scraping continuo de métricas (simula Prometheus)..."
    
    for i in {1..60}; do  # 1 minuto de scraping cada 5 segundos
        curl -s http://localhost:3001/metrics > /dev/null
        sleep 5 &
    done
}

echo "🚀 EJECUTANDO GENERACIÓN COMPLETA DE MÉTRICAS..."

# Ejecutar funciones en paralelo
generate_auth_metrics &
AUTH_PID=$!

generate_http_traffic &
HTTP_PID=$!

generate_error_traffic &
ERROR_PID=$!

continuous_metrics_scraping &
METRICS_PID=$!

echo "✅ Tráfico generándose en background..."
echo "📊 Dashboards: http://localhost:3003"
echo "🎯 Executive Dashboard - Métricas de negocio"
echo "🔧 Technical Dashboard - Métricas técnicas"
echo ""
echo "⏱️ Ejecutándose por 2 minutos..."

# Mostrar progreso
for i in {1..8}; do
    sleep 15
    echo "⏳ Progreso: $((i*12.5))% - Generando métricas..."
    
    # Mostrar sample de métricas cada 30 segundos
    if [ $((i % 2)) -eq 0 ]; then
        echo "📊 Muestra de métricas actuales:"
        curl -s http://localhost:3001/metrics | grep -E "rhinometric_(auth|http)" | head -6
        echo ""
    fi
done

# Cleanup
kill $AUTH_PID $HTTP_PID $ERROR_PID $METRICS_PID 2>/dev/null

echo ""
echo "🎉 GENERACIÓN DE MÉTRICAS COMPLETA"
echo ""
echo "📈 RESUMEN DE MÉTRICAS GENERADAS:"
curl -s http://localhost:3001/metrics | grep -E "rhinometric_(auth_attempts|http_requests)" | grep -v "# "

echo ""
echo "✨ ¡Los dashboards ahora deberían mostrar datos completos!"