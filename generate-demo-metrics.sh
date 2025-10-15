#!/bin/bash

# 🎯 GENERADOR DE MÉTRICAS FICTICIAS RHINOMETRIC
# Para hacer que los dashboards muestren datos realistas

echo "🚀 INICIANDO GENERADOR DE DATOS FICTICIOS PARA OBSERVABILIDAD..."

# URLs base
API_URL="http://localhost:3001"
GRAFANA_URL="http://localhost:3003"
PROMETHEUS_URL="http://localhost:9090"

# Función para generar métricas de aplicaciones ficticias
generate_fake_app_metrics() {
    local app_name="$1"
    local success_rate="$2"
    local rps="$3"
    
    echo "📊 Generando métricas para aplicación ficticia: $app_name"
    
    for i in {1..20}; do
        # Requests exitosos
        if [ $((RANDOM % 100)) -lt $success_rate ]; then
            curl -s "$API_URL/api/v1/health" > /dev/null
            curl -s "$API_URL/" > /dev/null
        else
            # Requests con errores
            curl -s "$API_URL/api/v1/nonexistent" > /dev/null
        fi
        
        sleep $(echo "scale=2; 1/$rps" | bc -l 2>/dev/null || echo "0.5")
    done
}

# Función para generar autenticaciones ficticias
generate_fake_auth_traffic() {
    echo "🔐 Generando tráfico de autenticación ficticio..."
    
    # Usuarios ficticios exitosos
    local users=("alice" "bob" "charlie" "diana" "eve")
    local fake_users=("hacker" "attacker" "bot" "spam")
    
    for user in "${users[@]}"; do
        for i in {1..3}; do
            curl -s -X POST "$API_URL/api/v1/auth/login" \
                -H "Content-Type: application/json" \
                -d "{\"username\":\"$user\",\"password\":\"password123\"}" > /dev/null
            sleep 0.3
        done
    done
    
    # Intentos fallidos
    for fake_user in "${fake_users[@]}"; do
        curl -s -X POST "$API_URL/api/v1/auth/login" \
            -H "Content-Type: application/json" \
            -d "{\"username\":\"$fake_user\",\"password\":\"wrongpass\"}" > /dev/null
        sleep 0.5
    done
}

# Función para generar métricas de base de datos ficticias
generate_fake_db_metrics() {
    echo "🗄️ Simulando consultas de base de datos..."
    
    local queries=("SELECT users" "UPDATE profile" "INSERT log" "DELETE temp" "JOIN tables")
    
    for query in "${queries[@]}"; do
        # Simular diferentes duraciones
        delay=$(echo "scale=2; $RANDOM/32767 * 0.1" | bc -l 2>/dev/null || echo "0.05")
        sleep $delay
        
        # Llamar endpoint que no existe para simular carga
        curl -s "$API_URL/api/v1/metrics-simulator" > /dev/null 2>&1
    done
}

# Función para generar tráfico continuo de diferentes aplicaciones
generate_continuous_traffic() {
    echo "🌊 Generando tráfico continuo de múltiples aplicaciones..."
    
    # Aplicación web principal (95% success)
    generate_fake_app_metrics "web-app" 95 10 &
    
    # API móvil (88% success) 
    generate_fake_app_metrics "mobile-api" 88 15 &
    
    # Microservicio de pagos (99% success)
    generate_fake_app_metrics "payments-svc" 99 5 &
    
    # Sistema legacy (70% success)
    generate_fake_app_metrics "legacy-system" 70 3 &
}

# Función para mostrar estadísticas en tiempo real
show_live_stats() {
    echo "📈 MOSTRANDO ESTADÍSTICAS EN TIEMPO REAL..."
    
    while true; do
        clear
        echo "🎯 RHINOMETRIC - PLATAFORMA DE OBSERVABILIDAD"
        echo "=============================================="
        echo "⏰ $(date)"
        echo ""
        echo "📊 MÉTRICAS ACTUALES:"
        
        # Intentar obtener métricas del API
        if curl -s "$API_URL/metrics" >/dev/null 2>&1; then
            echo "✅ API Métricas: FUNCIONANDO"
            auth_success=$(curl -s "$API_URL/metrics" | grep 'rhinometric_auth.*success' | tail -1 | awk '{print $2}' || echo "0")
            auth_failure=$(curl -s "$API_URL/metrics" | grep 'rhinometric_auth.*failure' | tail -1 | awk '{print $2}' || echo "0")
            echo "   🔐 Auth Success: $auth_success"
            echo "   ❌ Auth Failure: $auth_failure"
        else
            echo "⚠️  API Métricas: NO DISPONIBLE"
        fi
        
        echo ""
        echo "🔗 SERVICIOS:"
        echo "   📊 Grafana: $GRAFANA_URL (admin/admin123)"
        echo "   📈 Prometheus: $PROMETHEUS_URL"
        echo "   🚀 API: $API_URL"
        echo ""
        echo "⏹️  Presiona Ctrl+C para detener..."
        
        sleep 5
    done
}

# MAIN: Ejecutar generación de datos
echo "🎬 INICIANDO SIMULACIÓN COMPLETA..."

# Lanzar generadores en background
generate_fake_auth_traffic &
AUTH_PID=$!

generate_fake_db_metrics &
DB_PID=$!

generate_continuous_traffic &
TRAFFIC_PID=$!

# Mostrar estadísticas
show_live_stats &
STATS_PID=$!

# Cleanup al salir
cleanup() {
    echo ""
    echo "🛑 Deteniendo generadores..."
    kill $AUTH_PID $DB_PID $TRAFFIC_PID $STATS_PID 2>/dev/null
    echo "✅ Generadores detenidos"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Mantener el script corriendo
wait