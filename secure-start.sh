#!/bin/bash
# Genera password aleatoria para cada instalación
PASS=$(openssl rand -base64 12)
docker run -d \
  -e GF_SECURITY_ADMIN_PASSWORD=$PASS \
  -p 3000:3000 \
  grafana/grafana
echo "Password admin: $PASS" > credentials.txt
echo "✅ Password guardada en credentials.txt"
