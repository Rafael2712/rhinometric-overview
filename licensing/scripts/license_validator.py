#!/usr/bin/env python3
import json
import base64
from datetime import datetime
import sys
import os

def validate_license(license_file):
    """Valida una licencia y retorna su estado"""
    try:
        with open(license_file, 'r') as f:
            encoded_license = f.read().strip()
        
        # Decodificar
        decoded = base64.b64decode(encoded_license)
        license_data = json.loads(decoded)
        
        # Verificar campos requeridos
        required_fields = ["customer", "type", "issued", "product", "signature"]
        for field in required_fields:
            if field not in license_data:
                return False, f"Campo requerido faltante: {field}"
        
        # Verificar expiración
        if license_data.get("expires"):
            expire_date = datetime.fromisoformat(license_data["expires"])
            if datetime.now() > expire_date:
                return False, "Licencia expirada"
        
        # Validación OK
        return True, license_data
        
    except Exception as e:
        return False, f"Error validando licencia: {str(e)}"

def create_docker_env(license_data):
    """Crea variables de entorno para Docker basadas en la licencia"""
    env_file = ".env.license"
    
    with open(env_file, 'w') as f:
        f.write(f"LICENSE_TYPE={license_data['type']}\n")
        f.write(f"LICENSE_CUSTOMER={license_data['customer']}\n")
        f.write(f"LICENSE_EXPIRES={license_data.get('expires', 'never')}\n")
        f.write(f"LICENSE_FEATURES={','.join(license_data.get('features', []))}\n")
    
    print(f"Variables de entorno creadas en {env_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python license_validator.py <archivo_licencia>")
        sys.exit(1)
    
    license_file = sys.argv[1]
    valid, result = validate_license(license_file)
    
    if valid:
        print(f"✅ Licencia válida para: {result['customer']}")
        print(f"   Tipo: {result['type']}")
        print(f"   Expira: {result.get('expires', 'Nunca')}")
        create_docker_env(result)
    else:
        print(f"❌ Licencia inválida: {result}")
        sys.exit(1)
