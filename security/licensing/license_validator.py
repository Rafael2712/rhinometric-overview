#!/usr/bin/env python3
import json
import base64
import hashlib
import sys
import os
from datetime import datetime
import subprocess

class LicenseValidator:
    def __init__(self):
        self.secret_key = "RHN2024$ecur3K3y!"

    def get_hardware_id(self):
        """Obtiene un ID único del hardware/sistema operativo/contenedor."""
        try:
            # Opción 1: /etc/machine-id (Común en Linux)
            if os.path.exists('/etc/machine-id'):
                with open('/etc/machine-id', 'r') as f:
                    return f.read().strip()
            # Opción 2: Hostname (Común en Docker/Contenedores)
            hostname = subprocess.check_output(['hostname']).decode().strip()
            return hashlib.md5(hostname.encode()).hexdigest()
        except:
            return "unknown_hw_id" # ID por defecto si falla

    def validate(self, license_file):
        try:
            with open(license_file, 'r') as f:
                encoded_data = f.read().strip()

            license_data = json.loads(base64.b64decode(encoded_data))

            # 1. Verificar expiración
            expires = datetime.fromisoformat(license_data['expires'])
            now = datetime.now()

            if now > expires:
                print("❌ LICENCIA EXPIRADA")
                return False

            # 2. Verificar firma digital
            expected_signature = hashlib.sha256(
                f"{license_data['id']}{license_data['customer']}{license_data['expires']}{self.secret_key}".encode()
            ).hexdigest()

            if license_data['signature'] != expected_signature:
                print("❌ LICENCIA INVÁLIDA (firma incorrecta)")
                return False

            # 3. Verificar hardware lock
            if license_data.get('hardware_id'):
                current_hw = self.get_hardware_id()
                if license_data['hardware_id'] != current_hw:
                    print(f"❌ LICENCIA NO VÁLIDA PARA ESTE HARDWARE. Requerido: {license_data['hardware_id'][:8]}, Actual: {current_hw[:8]}")
                    return False

            days_left = (expires - now).days
            print(f"✅ Licencia válida")
            print(f"   Cliente: {license_data['customer']}")
            print(f"   Expira en: {days_left} días")

            # 4. Registrar uso para Loki/Logs
            self.log_validation(license_data['id'], license_data['customer'])

            return True

        except Exception as e:
            print(f"❌ ERROR durante la validación: {str(e)}")
            return False

    def log_validation(self, license_id, customer):
        """Registrar uso de licencia en el archivo que Loki leerá."""
        log_entry = {
            'level': 'INFO',
            'timestamp': datetime.now().isoformat(),
            'msg': 'License Validation Success',
            'license_id': license_id,
            'customer': customer,
            'hardware_id': self.get_hardware_id(),
            'app': 'license_validator'
        }
        # En el contenedor, esto irá a /var/log/app/license_usage.log
        with open('/tmp/license_usage.log', 'a') as f: 
            f.write(json.dumps(log_entry) + '\n')
            
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: validator.py <license_file>")
        sys.exit(1)
    
    validator = LicenseValidator()
    if not validator.validate(sys.argv[1]):
        sys.exit(1)
