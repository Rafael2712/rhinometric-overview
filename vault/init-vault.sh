#!/bin/bash

# Script para inicializar Vault y configurar los secretos básicos

# Variables de entorno necesarias
VAULT_ADDR='http://127.0.0.1:8200'

# Esperar a que Vault esté disponible
echo "Esperando a que Vault esté disponible..."
until curl -fs "$VAULT_ADDR/v1/sys/health" >/dev/null 2>&1; do
  sleep 1
done

# Inicializar Vault si no está inicializado
INIT_RESPONSE=$(curl -s "$VAULT_ADDR/v1/sys/init")
INITIALIZED=$(echo "$INIT_RESPONSE" | jq -r '.initialized')

if [ "$INITIALIZED" = "false" ]; then
  echo "Inicializando Vault..."
  INIT=$(curl -s -X PUT -d '{"secret_shares": 5, "secret_threshold": 3}' "$VAULT_ADDR/v1/sys/init")
  
  # Guardar las claves y el token root en archivos seguros
  echo "$INIT" | jq -r '.root_token' > /vault/config/root_token
  echo "$INIT" | jq -r '.keys_base64[]' > /vault/config/unseal_keys
  
  chmod 600 /vault/config/root_token /vault/config/unseal_keys
fi

# Usar el token root para configurar los secretos
export VAULT_TOKEN=$(cat /vault/config/root_token)

# Habilitar el motor de secretos KV versión 2
vault secrets enable -version=2 kv

# Crear políticas básicas
vault policy write app-policy -<<EOF
path "kv/data/app/*" {
  capabilities = ["read"]
}
EOF

# Agregar algunos secretos de ejemplo
vault kv put kv/app/database \
    db_host="postgres" \
    db_user="rhinometric" \
    db_password="tu_contraseña_segura"

vault kv put kv/app/api \
    api_key="tu_api_key" \
    api_secret="tu_api_secret"

echo "Configuración de Vault completada!"