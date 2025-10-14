#!/usr/bin/env python3
import os
import hvac
import json
import time

def get_vault_client():
    return hvac.Client(
        url=os.environ['VAULT_ADDR'],
        role_id=os.environ['VAULT_ROLE_ID'],
        secret_id=os.environ['VAULT_SECRET_ID']
    )

def load_secrets():
    client = get_vault_client()
    
    # Esperar hasta que Vault esté disponible
    max_retries = 30
    for i in range(max_retries):
        try:
            if client.is_authenticated():
                break
        except Exception:
            print(f"Esperando a Vault... {i+1}/{max_retries}")
            time.sleep(2)
            continue
    
    # Leer secretos
    try:
        secrets = client.secrets.kv.v2.read_secret(
            path='api-monitor/config'
        )['data']['data']
        
        # Establecer variables de entorno
        for key, value in secrets.items():
            os.environ[key.upper()] = value
            
        print("Secretos cargados correctamente")
    except Exception as e:
        print(f"Error al cargar secretos: {e}")
        raise

if __name__ == "__main__":
    load_secrets()
    
    # Ejecutar el comando original
    os.execvp("python", ["python"] + sys.argv[1:])