import base64
import json
from datetime import datetime

def validate_license(license_file):
    with open(license_file, 'r') as f:
        data = json.loads(base64.b64decode(f.read()))
    
    expires = datetime.fromisoformat(data['expires'])
    now = datetime.now()
    
    if now > expires:
        print("LICENCIA EXPIRADA")
        exit(1)
    
    days_left = (expires - now).days
    print(f"Licencia válida. Expira en {days_left} días")
    
    # Para 15 días:
    # data['expires'] = (now + timedelta(days=15)).isoformat()
