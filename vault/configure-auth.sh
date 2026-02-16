#!/bin/bash

# Script para configurar la autenticación de servicios en Vault

# Variables
VAULT_ADDR=${VAULT_ADDR:-"http://127.0.0.1:8200"}
VAULT_TOKEN=$(cat /vault/config/root_token)

# Habilitar el método de autenticación AppRole
vault auth enable approle

# Crear políticas para los servicios
vault policy write prometheus-policy -<<EOF
path "kv/data/prometheus/*" {
  capabilities = ["read"]
}
path "kv/data/shared/*" {
  capabilities = ["read"]
}
EOF

vault policy write loki-policy -<<EOF
path "kv/data/loki/*" {
  capabilities = ["read"]
}
path "kv/data/shared/*" {
  capabilities = ["read"]
}
EOF

# Crear AppRoles para cada servicio
for SERVICE in prometheus loki; do
    vault write auth/approle/role/$SERVICE \
        token_policies="$SERVICE-policy" \
        token_ttl=1h \
        token_max_ttl=24h \
        secret_id_ttl=24h

    # Obtener Role ID y Secret ID
    ROLE_ID=$(vault read -field=role_id auth/approle/role/$SERVICE/role-id)
    SECRET_ID=$(vault write -f -field=secret_id auth/approle/role/$SERVICE/secret-id)

    # Guardar las credenciales en archivos seguros
    echo "VAULT_${SERVICE^^}_ROLE_ID=$ROLE_ID" > /vault/config/$SERVICE.env
    echo "VAULT_${SERVICE^^}_SECRET_ID=$SECRET_ID" >> /vault/config/$SERVICE.env
done

# Crear secretos para los servicios
vault kv put kv/prometheus/config \
    web_config_password="$(openssl rand -hex 32)" \
    basic_auth_password="$(openssl rand -hex 32)"

vault kv put kv/loki/config \
    http_auth_password="$(openssl rand -hex 32)" \
    storage_s3_access_key="$(openssl rand -hex 16)" \
    storage_s3_secret_key="$(openssl rand -hex 32)"

echo "Configuración de autenticación completada!"
echo "Las credenciales se han guardado en /vault/config/[service].env"