#!/bin/bash
set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║               RHINOMETRIC Loki - Entrypoint                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# VALIDACIÓN DE LICENCIA (OBLIGATORIA)
# ============================================================================

if [ -f "/security/validate_license.py" ]; then
    python3 /security/validate_license.py "Loki"
    VALIDATION_RESULT=$?
    
    if [ $VALIDATION_RESULT -ne 0 ]; then
        echo ""
        echo "❌ Loki no puede iniciar sin una licencia válida"
        echo ""
        exit 1
    fi
else
    echo "⚠️  validate_license.py no encontrado - continuando sin validación"
    echo "   (modo desarrollo)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Iniciando Loki..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
# CONFIGURACIÓN DE LOKI
# ============================================================================

# Variables de entorno
LOKI_CONFIG=${LOKI_CONFIG:-/etc/loki/loki-config.yml}
LOKI_DATA=${LOKI_DATA:-/loki}

# Crear directorios necesarios
mkdir -p "$LOKI_DATA"/{chunks,index,boltdb-cache,wal}

# Permisos (usuario loki es UID 10001)
chown -R 10001:10001 "$LOKI_DATA"

# Validar archivo de configuración
if [ ! -f "$LOKI_CONFIG" ]; then
    echo "❌ ERROR: Archivo de configuración no encontrado: $LOKI_CONFIG"
    exit 1
fi

echo "✅ Configuración encontrada: $LOKI_CONFIG"
echo "✅ Directorio de datos: $LOKI_DATA"
echo ""

# ============================================================================
# INICIAR LOKI
# ============================================================================

exec /usr/bin/loki \
  -config.file="$LOKI_CONFIG" \
  -target=all \
  -log.level=info
