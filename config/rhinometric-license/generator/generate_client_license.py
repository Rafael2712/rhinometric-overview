#!/usr/bin/env python3
import requests
import json
import sys
import os

LICENSE_SERVER = os.getenv('LICENSE_SERVER', 'http://localhost:5000')

def generate_license(client_name, license_type='trial'):
    # Obtener hardware ID
    try:
        with open('/sys/class/dmi/id/product_uuid', 'r') as f:
            hardware_id = f.read().strip()
    except:
        hardware_id = f"docker-{os.uname().nodename}"
    
    # Solicitar licencia al servidor
    response = requests.post(f'{LICENSE_SERVER}/generate', 
        json={
            'client_name': client_name,
            'type': license_type,
            'hardware_id': hardware_id
        })
    
    if response.status_code == 200:
        data = response.json()
        # Guardar licencias para cada servicio
        os.makedirs('licenses', exist_ok=True)
        for service in ['grafana', 'prometheus', 'loki']:
            with open(f'licenses/{service}.key', 'w') as f:
                f.write(data['license_key'])
        
        print(f"Licencia generada exitosamente:")
        print(f"Cliente: {client_name}")
        print(f"Tipo: {license_type}")
        print(f"Expira: {data['expires']}")
        print(f"ID: {data['client_id']}")
        return data['license_key']
    else:
        print(f"Error generando licencia: {response.text}")
        return None

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python generate_client_license.py <nombre_cliente> [tipo:trial/annual/permanent]")
        sys.exit(1)
    
    client = sys.argv[1]
    lic_type = sys.argv[2] if len(sys.argv) > 2 else 'trial'
    generate_license(client, lic_type)
