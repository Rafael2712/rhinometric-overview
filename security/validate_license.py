#!/usr/bin/env python3
"""
RHINOMETRIC License Validator for Service Entrypoints
======================================================

Script simple para validar licencias en entrypoints de servicios Docker.

Si la licencia es inválida, el servicio NO arranca.

Uso en entrypoint.sh:
    python3 /opt/rhinometric/validate_license.py "Grafana"
    # Si retorna exit code 0 → continúa con el servicio
    # Si retorna exit code 1 → termina el entrypoint

Autor: RHINOMETRIC Security Team
Versión: 2.3.0
"""

import os
import sys
import json
from datetime import datetime

# Rutas estándar de licencia y clave pública
LICENSE_PATHS = [
    '/opt/rhinometric/license/cliente.lic',
    '/opt/rhinometric/license/license.lic',
    '/licenses/cliente.lic',
    '/licenses/license.lic',
    '/app/license.lic',
    # Local development paths
    './licenses/cliente.lic',
    './licenses/license.lic',
    '../licenses/cliente.lic'
]

PUBLIC_KEY_PATHS = [
    '/opt/rhinometric/keys/rhinometric_public.pem',
    '/security/rhinometric_public.pem',
    '/app/rhinometric_public.pem',
    # Local development paths
    './security/rhinometric_public.pem',
    '../security/rhinometric_public.pem'
]


def find_file(paths, file_type="archivo"):
    """Busca un archivo en múltiples ubicaciones"""
    for path in paths:
        if os.path.exists(path):
            return path
    
    print(f"❌ {file_type.capitalize()} no encontrado en:", file=sys.stderr)
    for path in paths:
        print(f"   - {path}", file=sys.stderr)
    return None


def load_license(license_path):
    """Carga y parsea el archivo de licencia"""
    try:
        with open(license_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error al leer licencia: {e}", file=sys.stderr)
        return None


def validate_license_simple(license_file, service_name):
    """
    Validación simple de licencia (solo estructura y expiración).
    
    NOTA: La validación de firma RSA completa requiere la librería cryptography.
    En un entrypoint mínimo podemos validar solo estructura + expiración.
    """
    # Verificar estructura básica
    if 'license' not in license_file or 'signature' not in license_file:
        print(f"❌ Estructura de licencia inválida", file=sys.stderr)
        return False
    
    license_data = license_file['license']
    
    # Verificar campos requeridos
    required_fields = ['customer', 'hwid', 'type', 'expires']
    for field in required_fields:
        if field not in license_data:
            print(f"❌ Campo requerido faltante: {field}", file=sys.stderr)
            return False
    
    # Verificar expiración
    expires_str = license_data['expires']
    
    # Licencias perpetuas
    if expires_str >= '2099-01-01':
        print(f"✅ Licencia perpetua")
        return True
    
    try:
        expires_dt = datetime.strptime(expires_str, '%Y-%m-%d')
        now = datetime.utcnow()
        
        if now > expires_dt:
            days_expired = (now - expires_dt).days
            print(f"❌ Licencia expirada hace {days_expired} días", file=sys.stderr)
            return False
        
        days_remaining = (expires_dt - now).days
        
        # Advertencias de expiración próxima
        if days_remaining <= 3:
            print(f"⚠️  CRÍTICO: Licencia expira en {days_remaining} días", file=sys.stderr)
        elif days_remaining <= 10:
            print(f"⚠️  Licencia expira en {days_remaining} días", file=sys.stderr)
        
        return True
        
    except ValueError:
        print(f"❌ Formato de fecha inválido: {expires_str}", file=sys.stderr)
        return False


def main():
    """Validación de licencia en entrypoint"""
    
    # Obtener nombre del servicio (primer argumento)
    service_name = sys.argv[1] if len(sys.argv) > 1 else "RHINOMETRIC Service"
    
    print(f"🔐 Validando licencia de {service_name}...")
    
    # 1. Buscar archivo de licencia
    license_path = find_file(LICENSE_PATHS, "archivo de licencia")
    if not license_path:
        print(f"\n❌ No se encontró archivo de licencia", file=sys.stderr)
        print(f"   Coloca el archivo .lic en una de estas ubicaciones", file=sys.stderr)
        sys.exit(1)
    
    print(f"   Licencia: {license_path}")
    
    # 2. Cargar licencia
    license_file = load_license(license_path)
    if not license_file:
        sys.exit(1)
    
    # 3. Validar estructura y expiración
    if not validate_license_simple(license_file, service_name):
        print(f"\n{'='*70}", file=sys.stderr)
        print(f"❌ LICENCIA INVÁLIDA - {service_name.upper()} NO PUEDE INICIAR", file=sys.stderr)
        print(f"{'='*70}", file=sys.stderr)
        print(f"\n📧 Contacta a: licenses@rhinometric.com", file=sys.stderr)
        print(f"{'='*70}\n", file=sys.stderr)
        sys.exit(1)
    
    # 4. Mostrar información
    license_data = license_file['license']
    print(f"✅ Licencia válida")
    print(f"   Cliente: {license_data.get('customer', 'Unknown')}")
    print(f"   Tipo: {license_data.get('type', 'unknown')}")
    
    expires_str = license_data.get('expires', '')
    if expires_str >= '2099-01-01':
        print(f"   Expiración: Perpetua")
    else:
        try:
            expires_dt = datetime.strptime(expires_str, '%Y-%m-%d')
            now = datetime.utcnow()
            days = (expires_dt - now).days
            print(f"   Días restantes: {days}")
        except:
            pass
    
    print(f"✅ {service_name} puede iniciar\n")
    sys.exit(0)


if __name__ == '__main__':
    main()
