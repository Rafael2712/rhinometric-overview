#!/bin/bash
#
# RHINOMETRIC TIER CONFIGURATION
# Aplica configuraciones de almacenamiento según tier de licencia
#
# Uso:
#   ./scripts/configure-tier.sh [essentials|growth|enterprise]
#

set -euo pipefail

TIER=${1:-essentials}
LOKI_CONFIG="config/loki-config.yml"
ENV_FILE=".env"

echo "=========================================="
echo " RHINOMETRIC TIER CONFIGURATION"
echo "=========================================="
echo ""
echo "Configurando tier: ${TIER}"
echo ""

# Validar tier
if [[ ! "${TIER}" =~ ^(essentials|growth|enterprise)$ ]]; then
    echo "❌ ERROR: Tier inválido: ${TIER}"
    echo "Valores permitidos: essentials, growth, enterprise"
    exit 1
fi

# Configurar según tier
case "${TIER}" in
    essentials)
        PROMETHEUS_RETENTION="30d"
        PROMETHEUS_SIZE="50GB"
        LOKI_RETENTION="168h"  # 7 días
        JAEGER_TTL="72h"        # 3 días
        DISK_MIN="200GB"
        ;;
    growth)
        PROMETHEUS_RETENTION="30d"
        PROMETHEUS_SIZE="100GB"
        LOKI_RETENTION="120h"  # 5 días
        JAEGER_TTL="48h"        # 2 días
        DISK_MIN="500GB"
        ;;
    enterprise)
        PROMETHEUS_RETENTION="15d"
        PROMETHEUS_SIZE="200GB"
        LOKI_RETENTION="72h"   # 3 días
        JAEGER_TTL="24h"        # 1 día
        DISK_MIN="1TB"
        ;;
esac

echo "Configuración aplicada:"
echo "  - Prometheus: retention=${PROMETHEUS_RETENTION}, size=${PROMETHEUS_SIZE}"
echo "  - Loki: retention=${LOKI_RETENTION}"
echo "  - Jaeger: TTL=${JAEGER_TTL}"
echo "  - Disco mínimo recomendado: ${DISK_MIN}"
echo ""

# Actualizar .env
if [ -f "${ENV_FILE}" ]; then
    if grep -q "RHINO_LICENSE_TIER=" "${ENV_FILE}"; then
        sed -i.bak "s/^RHINO_LICENSE_TIER=.*/RHINO_LICENSE_TIER=${TIER}/" "${ENV_FILE}"
        echo "✅ Actualizado RHINO_LICENSE_TIER en ${ENV_FILE}"
    else
        echo "RHINO_LICENSE_TIER=${TIER}" >> "${ENV_FILE}"
        echo "✅ Añadido RHINO_LICENSE_TIER a ${ENV_FILE}"
    fi
else
    echo "⚠️  ${ENV_FILE} no encontrado, usando ${ENV_FILE}.example"
    cp .env.example "${ENV_FILE}"
    sed -i.bak "s/^RHINO_LICENSE_TIER=.*/RHINO_LICENSE_TIER=${TIER}/" "${ENV_FILE}"
fi

# Actualizar Loki config
if [ -f "${LOKI_CONFIG}" ]; then
    sed -i.bak "s/retention_period: [0-9]*h/retention_period: ${LOKI_RETENTION}/" "${LOKI_CONFIG}"
    sed -i.bak "s/reject_old_samples_max_age: [0-9]*h/reject_old_samples_max_age: ${LOKI_RETENTION}/" "${LOKI_CONFIG}"
    echo "✅ Actualizado ${LOKI_CONFIG} con retention=${LOKI_RETENTION}"
else
    echo "⚠️  ${LOKI_CONFIG} no encontrado"
fi

echo ""
echo "=========================================="
echo " SIGUIENTE PASO"
echo "=========================================="
echo ""
echo "Para aplicar los cambios:"
echo "  1. Editar docker-compose-v2.5.0-core.yml:"
echo ""
echo "     prometheus:"
echo "       command:"
echo "         - '--storage.tsdb.retention.time=${PROMETHEUS_RETENTION}'"
echo "         - '--storage.tsdb.retention.size=${PROMETHEUS_SIZE}'"
echo ""
echo "     jaeger:"
echo "       environment:"
echo "         BADGER_TTL: \"${JAEGER_TTL}\""
echo ""
echo "  2. Recrear contenedores:"
echo "     docker compose -f docker-compose-v2.5.0-core.yml up -d --force-recreate prometheus loki jaeger"
echo ""
echo "  3. Verificar:"
echo "     ./scripts/verify-storage-policies.sh"
echo ""
