#!/usr/bin/env python3
import json, base64, hashlib, uuid, os
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

class RhinometricLicense:
    def __init__(self):
        # Clave única por instalación
        self.master_key = "RHN2024$PROD#KEY!@"
        self.cipher = Fernet(base64.urlsafe_b64encode(self.master_key.encode().ljust(32)[:32]))
        
    def generate(self, customer, license_type="trial", days=15):
        license_data = {
            'id': str(uuid.uuid4()),
            'customer': customer,
            'type': license_type,  # trial, annual, permanent
            'issued': datetime.now().isoformat(),
            'expires': None if license_type == "permanent" else (datetime.now() + timedelta(days=days)).isoformat(),
            'hardware_lock': hashlib.sha256(f"{customer}{datetime.now()}".encode()).hexdigest()[:16],
            'features': {
                'max_nodes': 5 if license_type == "trial" else -1,
                'alerting': True,
                'dashboards': 10 if license_type == "trial" else -1,
                'retention_days': 7 if license_type == "trial" else 365
            }
        }
        
        # Firma criptográfica
        signature = hashlib.sha512(
            f"{license_data['id']}{customer}{license_data['type']}{self.master_key}".encode()
        ).hexdigest()
        
        license_data['signature'] = signature
        
        # Encriptar todo
        encrypted = self.cipher.encrypt(json.dumps(license_data).encode())
        return base64.b64encode(encrypted).decode()
        
    def validate(self, license_content):
        try:
            # Desencriptar
            encrypted = base64.b64decode(license_content)
            decrypted = self.cipher.decrypt(encrypted)
            data = json.loads(decrypted)
            
            # Verificar firma
            expected_sig = hashlib.sha512(
                f"{data['id']}{data['customer']}{data['type']}{self.master_key}".encode()
            ).hexdigest()
            
            if data['signature'] != expected_sig:
                return False, "Invalid signature"
                
            # Verificar expiración
            if data['expires']:
                if datetime.now() > datetime.fromisoformat(data['expires']):
                    return False, "License expired"
                    
            return True, data
        except:
            return False, "Invalid license"

# Generar licencias
if __name__ == "__main__":
    import sys
    engine = RhinometricLicense()
    
    # Demo 15 días
    demo_license = engine.generate(sys.argv[1] if len(sys.argv) > 1 else "DemoClient", "trial", 15)
    with open("license_demo_15d.lic", "w") as f:
        f.write(demo_license)
    print(f"✅ Licencia demo creada: license_demo_15d.lic")
    
    # Anual
    annual_license = engine.generate(sys.argv[1] if len(sys.argv) > 1 else "DemoClient", "annual", 365)
    with open("license_annual.lic", "w") as f:
        f.write(annual_license)
    
    # Permanente
    perm_license = engine.generate(sys.argv[1] if len(sys.argv) > 1 else "DemoClient", "permanent")
    with open("license_permanent.lic", "w") as f:
        f.write(perm_license)
