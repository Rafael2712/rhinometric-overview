#!/bin/bash
# Captura hardware único
MACHINE_ID=$(cat /etc/machine-id 2>/dev/null || hostname | md5sum | cut -d' ' -f1)
MAC_ADDR=$(ip link show | grep ether | head -1 | awk '{print $2}' | md5sum | cut -d' ' -f1)
FINGERPRINT="${MACHINE_ID}-${MAC_ADDR}"

# Generar licencia atada al hardware
python3 << PY
import json, base64, hashlib
from datetime import datetime, timedelta

license_data = {
    'customer': '$1',
    'fingerprint': '$FINGERPRINT',
    'expires': (datetime.now() + timedelta(days=15)).isoformat(),
    'type': 'trial',
    'signature': hashlib.sha256('$FINGERPRINT'.encode()).hexdigest()
}

encoded = base64.b64encode(json.dumps(license_data).encode()).decode()
print(encoded)
PY
