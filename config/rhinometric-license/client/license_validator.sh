#!/bin/bash
set -e

LICENSE_FILE="/etc/rhinometric/license.key"
HARDWARE_ID=$(cat /sys/class/dmi/id/product_uuid 2>/dev/null || echo "docker-$(hostname)")
LICENSE_SERVER="${LICENSE_SERVER:-http://license-server:5000}"

# Función para validar licencia
validate_license() {
    if [ ! -f "$LICENSE_FILE" ]; then
        echo "ERROR: No se encuentra archivo de licencia en $LICENSE_FILE"
        exit 1
    fi
    
    LICENSE_KEY=$(cat $LICENSE_FILE)
    
    # Validar con servidor si está disponible
    if curl -f -X POST "$LICENSE_SERVER/validate" \
        -H "Content-Type: application/json" \
        -d "{\"license_key\":\"$LICENSE_KEY\",\"hardware_id\":\"$HARDWARE_ID\"}" \
        2>/dev/null; then
        echo "Licencia validada con servidor"
    else
        # Validación offline con JWT
        python3 -c "
import jwt
import sys
from datetime import datetime

try:
    payload = jwt.decode('$LICENSE_KEY', 'rhinometric-2025-secret-key', algorithms=['HS256'])
    if datetime.fromtimestamp(payload['exp']) < datetime.now():
        print('ERROR: Licencia expirada')
        sys.exit(1)
    print('Licencia válida hasta:', datetime.fromtimestamp(payload['exp']))
except Exception as e:
    print('ERROR: Licencia inválida:', e)
    sys.exit(1)
        "
    fi
}

# Validar antes de iniciar servicios
validate_license

# Iniciar el servicio real
exec "$@"
