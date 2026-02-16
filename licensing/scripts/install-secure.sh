#!/bin/bash
set -e

IMAGE="rafael0410/rhinometric:secure"
CONTAINER="rhinometric"
PORT="${RHINO_PORT:-3000}"

# Verificaciones
[ -f "license.lic" ] || { echo "❌ Falta license.lic"; exit 1; }
[ -f "loki-config.yml" ] || { echo "❌ Falta loki-config.yml"; exit 1; }

# Limpiar anterior
docker rm -f $CONTAINER 2>/dev/null || true

echo "🚀 Iniciando Rhinometric..."

# Arrancar con configuración correcta
docker run -d --name $CONTAINER \
  --restart unless-stopped \
  -p 127.0.0.1:$PORT:3000 \
  -v "$(pwd)/license.lic:/license/license.lic:ro" \
  -v "$(pwd)/loki-config.yml:/etc/loki/config.yml:ro" \
  $IMAGE

echo "⏳ Esperando servicios (40s)..."
for i in {1..40}; do
  if curl -sf http://localhost:$PORT/api/health > /dev/null 2>&1; then
    echo ""
    echo "✅ Instalación completada"
    echo "URL: http://localhost:$PORT"
    echo "Usuario: admin"
    echo "Contraseña: admin"
    exit 0
  fi
  echo -n "."
  sleep 1
done

echo "⚠️ Verificar: docker logs $CONTAINER"
