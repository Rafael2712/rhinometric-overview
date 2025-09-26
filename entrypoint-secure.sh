#!/usr/bin/env bash
set -euo pipefail

LICENSE_FILE="/license/license.lic"
VALIDATOR="/usr/local/bin/container_validator.py"

echo "🔐 Verificando licencia..."
if [ ! -f "$LICENSE_FILE" ]; then
  echo "🚨 No se encontró $LICENSE_FILE" >&2
  exit 1
fi

python3 "$VALIDATOR" "$LICENSE_FILE"

echo "🎉 Licencia OK. Iniciando servicio..."
# TODO: reemplaza esta línea por tu comando real (grafana/prometheus/etc).
# Mientras tanto, mantenemos el contenedor vivo:
tail -f /dev/null
