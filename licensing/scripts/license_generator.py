#!/usr/bin/env python3
import json
import base64
import hashlib
from datetime import datetime, timedelta
import sys

def generate_license(license_type, customer_name, days=None):
    now = datetime.now()
    
    license_data = {
        "customer": customer_name,
        "type": license_type,
        "issued": now.isoformat(),
        "product": "Rhinometric Observability Platform",
        "version": "1.0.0"
    }
    
    if license_type == "trial":
        expire_date = now + timedelta(days=days or 180)
        license_data["expires"] = expire_date.isoformat()
        license_data["features"] = ["monitoring", "alerting", "dashboards"]
        
    elif license_type == "permanent":
        license_data["expires"] = None
        license_data["features"] = ["monitoring", "alerting", "dashboards", "source_code"]
        
    elif license_type == "annual":
        expire_date = now + timedelta(days=365)
        license_data["expires"] = expire_date.isoformat()
        license_data["features"] = ["monitoring", "alerting", "dashboards", "support", "updates"]
    
    content = json.dumps(license_data, sort_keys=True)
    license_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    license_data["signature"] = license_hash
    
    encoded = base64.b64encode(json.dumps(license_data).encode()).decode()
    return encoded

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python license_generator.py <tipo> <cliente> [días]")
        print("Tipos: trial, permanent, annual")
        sys.exit(1)
    
    license_type = sys.argv[1]
    customer = sys.argv[2]
    days = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    license_key = generate_license(license_type, customer, days)
    
    filename = f"../../license_{customer.replace(' ', '_')}_{license_type}.lic"
    with open(filename, 'w') as f:
        f.write(license_key)
    
    print(f"Licencia generada: {filename}")
    print(f"Clave: {license_key}")
