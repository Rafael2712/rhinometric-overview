#!/bin/bash
set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              RHINOMETRIC Grafana - Entrypoint              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# VALIDACIÓN DE LICENCIA (OBLIGATORIA)
# ============================================================================

if [ -f "/security/validate_license.py" ]; then
    python3 /security/validate_license.py "Grafana"
    VALIDATION_RESULT=$?
    
    if [ $VALIDATION_RESULT -ne 0 ]; then
        echo ""
        echo "❌ Grafana no puede iniciar sin una licencia válida"
        echo ""
        exit 1
    fi
else
    echo "⚠️  validate_license.py no encontrado - continuando sin validación"
    echo "   (modo desarrollo)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Iniciando Grafana..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
# CONFIGURACIÓN DE GRAFANA
# ============================================================================

# Variables de entorno por defecto
export GF_PATHS_CONFIG=${GF_PATHS_CONFIG:-/etc/grafana/grafana.ini}
export GF_PATHS_DATA=${GF_PATHS_DATA:-/var/lib/grafana}
export GF_PATHS_LOGS=${GF_PATHS_LOGS:-/var/log/grafana}
export GF_PATHS_PLUGINS=${GF_PATHS_PLUGINS:-/var/lib/grafana/plugins}
export GF_PATHS_PROVISIONING=${GF_PATHS_PROVISIONING:-/etc/grafana/provisioning}

# Crear directorios necesarios
mkdir -p "$GF_PATHS_DATA" "$GF_PATHS_LOGS" "$GF_PATHS_PLUGINS" "$GF_PATHS_PROVISIONING"

# Permisos (usuario grafana es UID 472)
chown -R 472:0 "$GF_PATHS_DATA" "$GF_PATHS_LOGS" "$GF_PATHS_PLUGINS" "$GF_PATHS_PROVISIONING"

echo "✅ Directorios de Grafana configurados"
echo "✅ Iniciando servidor Grafana..."
echo ""

# ============================================================================
# INICIAR GRAFANA
# ============================================================================

# Ejecutar Grafana como usuario grafana
exec su-exec grafana /usr/share/grafana/bin/grafana-server \
  --homepath=/usr/share/grafana \
  --config="$GF_PATHS_CONFIG" \
  cfg:default.paths.data="$GF_PATHS_DATA" \
  cfg:default.paths.logs="$GF_PATHS_LOGS" \
  cfg:default.paths.plugins="$GF_PATHS_PLUGINS" \
  cfg:default.paths.provisioning="$GF_PATHS_PROVISIONING"
