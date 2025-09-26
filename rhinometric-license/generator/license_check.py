import requests
import sys
import os

# Obtener LICENSE_SERVER desde variable de entorno, con fallback a localhost
LICENSE_SERVER = os.getenv('LICENSE_SERVER', 'http://localhost:5000')
LICENSE_FILE = "/etc/license.key"  # Montado en Docker

# Generar hardware_id basado en el nombre del nodo
hardware_id = f"docker-{os.uname().nodename}"

# Leer el license_key
with open(LICENSE_FILE, 'r') as f:
    license_key = f.read().strip()

try:
    # Intentar validar en línea
    response = requests.post(f'{LICENSE_SERVER}/validate', json={
        'license_key': license_key,
        'hardware_id': hardware_id
    }, timeout=5)  # Timeout para evitar espera infinita
    response.raise_for_status()  # Lanza excepción si el código no es 200
    print("License valid")
except requests.exceptions.RequestException as e:
    # Fallback: validación local básica (ejemplo: longitud del key)
    if len(license_key) == 243:  # Ajusta según tu lógica real
        print("License valid (local fallback)")
    else:
        print(f"Error: No se pudo validar en línea y licencia local inválida. Detalle: {str(e)}")
        sys.exit(1)
