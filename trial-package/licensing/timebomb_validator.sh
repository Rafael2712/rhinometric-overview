#!/bin/bash
#
# RHINOMETRIC TIME-BOMB VALIDATOR
# Valida licencia cada 6 horas y hace shutdown si falla
#
# Uso: Se ejecuta en background en servicios críticos (Grafana, Prometheus)
#

set -e

# Configuración
LICENSE_SERVER_URL="${LICENSE_SERVER_URL:-http://license-server:5000}"
LICENSE_KEY="${LICENSE_KEY:-/data/.license_key}"
VALIDATION_INTERVAL="${VALIDATION_INTERVAL:-21600}"  # 6 horas en segundos
SERVICE_NAME="${SERVICE_NAME:-unknown}"
LOG_FILE="${LOG_FILE:-/var/log/timebomb.log}"

# Colores para logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para loguear con timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

# Función para validar licencia
validate_license() {
    log "Validating license for service: $SERVICE_NAME"
    
    # Leer license key si existe
    if [ ! -f "$LICENSE_KEY" ]; then
        log_error "License key file not found: $LICENSE_KEY"
        return 1
    fi
    
    local license_key=$(cat "$LICENSE_KEY" | tr -d '\n\r ')
    
    # Hacer request al license server
    local response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"license_key\":\"$license_key\"}" \
        "$LICENSE_SERVER_URL/validate" 2>&1)
    
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)
    
    # Verificar respuesta
    if [ "$http_code" != "200" ]; then
        log_error "License validation failed (HTTP $http_code)"
        log_error "Response: $body"
        return 1
    fi
    
    # Parsear JSON response
    local valid=$(echo "$body" | grep -o '"valid"[[:space:]]*:[[:space:]]*true' || echo "false")
    local action=$(echo "$body" | grep -o '"action"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)
    local days_remaining=$(echo "$body" | grep -o '"days_remaining"[[:space:]]*:[[:space:]]*[0-9]*' | grep -o '[0-9]*$')
    
    if [ "$valid" == "false" ] || [ "$action" == "shutdown" ]; then
        log_error "License invalid or expired!"
        log_error "Action required: $action"
        return 1
    fi
    
    log_success "License valid - $days_remaining days remaining"
    return 0
}

# Función para hacer shutdown del servicio
shutdown_service() {
    log_error "⛔ LICENSE VALIDATION FAILED - INITIATING SHUTDOWN"
    log_error "Service: $SERVICE_NAME"
    log_error "Reason: License expired or hardware mismatch"
    
    # Esperar 10 segundos para que se vean los logs
    sleep 10
    
    # Diferentes estrategias de shutdown según el servicio
    case "$SERVICE_NAME" in
        grafana)
            log_error "Killing Grafana process..."
            pkill -9 grafana-server || true
            ;;
        prometheus)
            log_error "Killing Prometheus process..."
            pkill -9 prometheus || true
            ;;
        loki)
            log_error "Killing Loki process..."
            pkill -9 loki || true
            ;;
        tempo)
            log_error "Killing Tempo process..."
            pkill -9 tempo || true
            ;;
        *)
            log_error "Unknown service, attempting generic shutdown..."
            ;;
    esac
    
    # Exit con código de error
    exit 1
}

# Función principal de monitoreo
monitor_license() {
    log "🔒 Rhinometric Time-Bomb Validator started"
    log "Service: $SERVICE_NAME"
    log "License Server: $LICENSE_SERVER_URL"
    log "Validation Interval: ${VALIDATION_INTERVAL}s ($(($VALIDATION_INTERVAL / 3600)) hours)"
    
    # Validación inicial (después de 60 segundos para que todo arranque)
    log "Waiting 60 seconds for services to start..."
    sleep 60
    
    log "Performing initial validation..."
    if ! validate_license; then
        log_error "Initial validation failed!"
        shutdown_service
    fi
    
    # Loop infinito de validación
    while true; do
        log "Sleeping for ${VALIDATION_INTERVAL}s until next validation..."
        sleep "$VALIDATION_INTERVAL"
        
        log "Performing scheduled validation..."
        if ! validate_license; then
            log_error "Scheduled validation failed!"
            shutdown_service
        fi
    done
}

# Manejo de señales
trap 'log "Time-Bomb validator stopped"; exit 0' SIGTERM SIGINT

# Iniciar monitoreo en background
monitor_license &

# Mantener el script vivo
wait

