#!/usr/bin/env python3
import json
import base64
import hashlib
import uuid
from datetime import datetime, timedelta
import sys

class SecureLicenseGenerator:
    def __init__(self):
        # NOTA: Cambiar esta clave en producción
        self.secret_key = "RHN2024$ecur3K3y!"

    def generate(self, customer_name, days=15, hardware_id=None):
        license_id = str(uuid.uuid4())
        issued = datetime.now().isoformat()
        expires = (datetime.now() + timedelta(days=days)).isoformat()
        
        license_data = {
            'id': license_id,
            'customer': customer_name,
            'type': 'trial',
            'issued': issued,
            'expires': expires,
            'days': days,
            'hardware_id': hardware_id,
            'features': ['monitoring', 'alerting', 'dashboards'],
            'max_nodes': 5,
        }
        
        # Firma digital con la clave secreta
        signature = hashlib.sha256(
            f"{license_id}{customer_name}{expires}{self.secret_key}".encode()
        ).hexdigest()
        
        license_data['signature'] = signature

        # Codificar en Base64
        encoded = base64.b64encode(
            json.dumps(license_data).encode()
        ).decode()
        
        return encoded, license_id

if __name__ == "__main__":
    customer = sys.argv[1] if len(sys.argv) > 1 else "DemoCustomer"
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    
    gen = SecureLicenseGenerator()
    # Generar sin hardware_id por defecto para facilitar pruebas iniciales
    license_content, license_id = gen.generate(customer, days, hardware_id=None) 
    
    filename = f"license_{customer.replace(' ', '_')}_{days}d.lic"
    with open(filename, 'w') as f:
        f.write(license_content)
        
    print(f"✅ Licencia generada: {filename}")
    print(f"   ID: {license_id}")
    print(f"   Cliente: {customer}")
    print(f"   Validez: {days} días")
