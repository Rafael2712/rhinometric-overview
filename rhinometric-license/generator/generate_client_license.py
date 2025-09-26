import requests
import sys
import os

LICENSE_SERVER = os.getenv('LICENSE_SERVER', 'http://localhost:5000')

if len(sys.argv) < 3:
    print("Uso: python3 generate_client_license.py <client_name> <type: trial/annual/permanent>")
    sys.exit(1)

client_name = sys.argv[1]
license_type = sys.argv[2]
hardware_id = f"docker-{os.uname().nodename}"

response = requests.post(f'{LICENSE_SERVER}/generate', json={
    'client_name': client_name,
    'type': license_type,
    'hardware_id': hardware_id
})

if response.status_code == 200:
    data = response.json()
    os.makedirs('/mnt/c/Users/canel/mi-proyecto/licenses', exist_ok=True)
    with open('/mnt/c/Users/canel/mi-proyecto/licenses/license.key', 'w') as f:
        f.write(data['license_key'])
    print(f"Licencia generada: {data['license_key']}")
    print(f"Expira: {data['expires']}")
else:
    print(f"Error: {response.json()['error']}")
