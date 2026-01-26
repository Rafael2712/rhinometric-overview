#!/bin/bash
#
# RHINOMETRIC DISK GUARDIAN
# Protección automática contra saturación de disco
#
# Función: Monitorea uso de disco cada 5 minutos
# Si uso > 90%, para ingesta no crítica (promtail, otel-collector)
# NO toca servicios del cliente (PostgreSQL, Redis, Backend)
#
# Instalación:
#   chmod +x /opt/rhinometric/infrastructure/mi-proyecto/scripts/disk-guardian.sh
#   (crontab -l; echo "*/5 * * * * /opt/rhinometric/infrastructure/mi-proyecto/scripts/disk-guardian.sh >> /var/log/disk-guardian.log 2>&1") | crontab -
#
# Logs: /var/log/disk-guardian.log
#

set -euo pipefail

# Configuración
THRESHOLD_CRITICAL=90        # Activar medidas de emergencia
THRESHOLD_WARNING=85         # Solo alertar
MOUNTPOINT="/"
ALERTMANAGER_URL="http://localhost:9093"
LOG_PREFIX="[$(date '+%Y-%m-%d %H:%M:%S')] DISK-GUARDIAN"

# Obtener uso actual de disco
CURRENT_USE=$(df ${MOUNTPOINT} | grep ${MOUNTPOINT} | awk '{print $5}' | sed 's/%//')
AVAILABLE_GB=$(df -BG ${MOUNTPOINT} | grep ${MOUNTPOINT} | awk '{print $4}' | sed 's/G//')

# Log estado normal (cada ejecución)
echo "${LOG_PREFIX} - Disk usage: ${CURRENT_USE}% | Available: ${AVAILABLE_GB}GB | Status: CHECKING"

# Función: Enviar alerta a Alertmanager
send_alert() {
    local severity=$1
    local message=$2
    
    curl -s -X POST "${ALERTMANAGER_URL}/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d "[{
            \"labels\": {
                \"alertname\": \"DiskGuardianEmergency\",
                \"severity\": \"${severity}\",
                \"component\": \"disk-guardian\"
            },
            \"annotations\": {
                \"summary\": \"${message}\",
                \"description\": \"Disk usage: ${CURRENT_USE}% | Available: ${AVAILABLE_GB}GB\"
            }
        }]" > /dev/null 2>&1 || echo "${LOG_PREFIX} - WARNING: Could not send alert to Alertmanager"
}

# Función: Detener contenedores de ingesta
emergency_stop() {
    echo "${LOG_PREFIX} - 🚨 CRITICAL: Disk ${CURRENT_USE}% (threshold: ${THRESHOLD_CRITICAL}%)"
    echo "${LOG_PREFIX} - Activating emergency measures..."
    
    # Detener promtail (logs)
    if docker ps --format '{{.Names}}' | grep -q "rhinometric-promtail"; then
        echo "${LOG_PREFIX} - Stopping rhinometric-promtail (log ingestion)..."
        docker stop rhinometric-promtail || echo "${LOG_PREFIX} - WARNING: Could not stop promtail"
    fi
    
    # Detener otel-collector (traces)
    if docker ps --format '{{.Names}}' | grep -q "rhinometric-otel-collector"; then
        echo "${LOG_PREFIX} - Stopping rhinometric-otel-collector (trace ingestion)..."
        docker stop rhinometric-otel-collector || echo "${LOG_PREFIX} - WARNING: Could not stop otel-collector"
    fi
    
    # Enviar alerta crítica
    send_alert "critical" "🚨 DISK EMERGENCY: ${CURRENT_USE}% used. Stopped promtail and otel-collector."
    
    # Registrar en syslog
    logger -t disk-guardian -p user.crit "EMERGENCY: Disk ${CURRENT_USE}% - Stopped promtail and otel-collector"
    
    echo "${LOG_PREFIX} - Emergency measures activated. Waiting for human intervention."
    echo "${LOG_PREFIX} - Services NOT affected: postgres, redis, backend, frontend, grafana, prometheus"
    echo "${LOG_PREFIX} - To resume: docker start rhinometric-promtail rhinometric-otel-collector"
}

# Verificar nivel crítico (>= 90%)
if [ "${CURRENT_USE}" -ge "${THRESHOLD_CRITICAL}" ]; then
    emergency_stop
    exit 1
fi

# Verificar nivel warning (>= 85%)
if [ "${CURRENT_USE}" -ge "${THRESHOLD_WARNING}" ]; then
    echo "${LOG_PREFIX} - ⚠️  WARNING: Disk ${CURRENT_USE}% (threshold: ${THRESHOLD_WARNING}%)"
    send_alert "warning" "⚠️ Disk usage high: ${CURRENT_USE}% - Approaching critical threshold"
    exit 0
fi

# Estado normal
echo "${LOG_PREFIX} - ✅ OK: Disk ${CURRENT_USE}% - Normal operation"
exit 0
