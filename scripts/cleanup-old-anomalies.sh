#!/bin/bash
#
# RHINOMETRIC ANOMALIES CLEANUP
# Limpieza automática de anomalías antiguas
#
# Función: Borra anomalías > 90 días de la tabla ai_anomalies
# Ejecutar mensualmente vía cron
#
# Instalación:
#   chmod +x /opt/rhinometric/scripts/cleanup-old-anomalies.sh
#   (crontab -l; echo "0 2 1 * * /opt/rhinometric/scripts/cleanup-old-anomalies.sh >> /var/log/anomalies-cleanup.log 2>&1") | crontab -
#
# Logs: /var/log/anomalies-cleanup.log
#

set -euo pipefail

# Configuración
RETENTION_DAYS=90
DB_CONTAINER="rhinometric-postgres"
DB_NAME="rhinometric"
DB_USER="rhinometric"
LOG_PREFIX="[$(date '+%Y-%m-%d %H:%M:%S')] ANOMALIES-CLEANUP"

echo "${LOG_PREFIX} - Starting anomalies cleanup (retention: ${RETENTION_DAYS} days)"

# Verificar que el contenedor de Postgres está corriendo
if ! docker ps --format '{{.Names}}' | grep -q "${DB_CONTAINER}"; then
    echo "${LOG_PREFIX} - ERROR: ${DB_CONTAINER} is not running"
    exit 1
fi

# Contar anomalías antes de cleanup
BEFORE_COUNT=$(docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -t -c \
    "SELECT COUNT(*) FROM ai_anomalies WHERE detected_at < NOW() - INTERVAL '${RETENTION_DAYS} days';" | tr -d ' ')

if [ "${BEFORE_COUNT}" -eq 0 ]; then
    echo "${LOG_PREFIX} - No anomalies older than ${RETENTION_DAYS} days found. Nothing to delete."
    exit 0
fi

echo "${LOG_PREFIX} - Found ${BEFORE_COUNT} anomalies older than ${RETENTION_DAYS} days"

# Borrar anomalías antiguas
docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c \
    "DELETE FROM ai_anomalies WHERE detected_at < NOW() - INTERVAL '${RETENTION_DAYS} days';" > /dev/null

# Contar anomalías después de cleanup
AFTER_COUNT=$(docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -t -c \
    "SELECT COUNT(*) FROM ai_anomalies;" | tr -d ' ')

# Vacuum para recuperar espacio
echo "${LOG_PREFIX} - Running VACUUM on ai_anomalies table..."
docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c "VACUUM ANALYZE ai_anomalies;" > /dev/null

echo "${LOG_PREFIX} - Cleanup completed:"
echo "${LOG_PREFIX} -   Deleted: ${BEFORE_COUNT} anomalies"
echo "${LOG_PREFIX} -   Remaining: ${AFTER_COUNT} anomalies"
echo "${LOG_PREFIX} -   VACUUM executed successfully"

exit 0
