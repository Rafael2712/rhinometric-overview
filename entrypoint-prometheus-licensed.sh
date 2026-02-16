#!/bin/bash
set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║            RHINOMETRIC Prometheus - Entrypoint             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# VALIDACIÓN DE LICENCIA (OBLIGATORIA)
# ============================================================================

if [ -f "/security/validate_license.py" ]; then
    python3 /security/validate_license.py "Prometheus"
    VALIDATION_RESULT=$?
    
    if [ $VALIDATION_RESULT -ne 0 ]; then
        echo ""
        echo "❌ Prometheus no puede iniciar sin una licencia válida"
        echo ""
        exit 1
    fi
else
    echo "⚠️  validate_license.py no encontrado - continuando sin validación"
    echo "   (modo desarrollo)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Iniciando Prometheus..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
# CONFIGURACIÓN DE PROMETHEUS
# ============================================================================

# Variables de entorno
PROMETHEUS_CONFIG=${PROMETHEUS_CONFIG:-/etc/prometheus/prometheus.yml}
PROMETHEUS_DATA=${PROMETHEUS_DATA:-/prometheus}
PROMETHEUS_RETENTION=${PROMETHEUS_RETENTION:-30d}
PROMETHEUS_RETENTION_SIZE=${PROMETHEUS_RETENTION_SIZE:-50GB}

# Crear directorios necesarios
mkdir -p "$PROMETHEUS_DATA"

# Permisos (usuario nobody es UID 65534)
chown -R 65534:65534 "$PROMETHEUS_DATA"

# Validar archivo de configuración
if [ ! -f "$PROMETHEUS_CONFIG" ]; then
    echo "❌ ERROR: Archivo de configuración no encontrado: $PROMETHEUS_CONFIG"
    exit 1
fi

echo "✅ Configuración encontrada: $PROMETHEUS_CONFIG"
echo "✅ Directorio de datos: $PROMETHEUS_DATA"
echo "✅ Retención: $PROMETHEUS_RETENTION (máximo $PROMETHEUS_RETENTION_SIZE)"
echo ""

# ============================================================================
# INICIAR PROMETHEUS
# ============================================================================

exec /bin/prometheus \
  --config.file="$PROMETHEUS_CONFIG" \
  --storage.tsdb.path="$PROMETHEUS_DATA" \
  --storage.tsdb.retention.time="$PROMETHEUS_RETENTION" \
  --storage.tsdb.retention.size="$PROMETHEUS_RETENTION_SIZE" \
  --web.console.libraries=/usr/share/prometheus/console_libraries \
  --web.console.templates=/usr/share/prometheus/consoles \
  --web.enable-lifecycle \
  --web.enable-admin-api \
  --log.level=info
