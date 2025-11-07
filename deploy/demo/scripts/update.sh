#!/bin/bash
# update.sh - Actualizaci√≥n segura del stack

set -euo pipefail

echo "Ì¥Ñ Rhinometric Demo - Update"

# 1. Backup antes de actualizar
echo "[1/5] Ejecutando backup..."
bash ./backup.sh || { echo "Error en backup"; exit 1; }

# 2. Pull de im√°genes actualizadas
echo "[2/5] Descargando im√°genes actualizadas..."
docker compose pull

# 3. Reiniciar servicios
echo "[3/5] Reiniciando servicios..."
docker compose down
docker compose up -d

# 4. Esperar health
echo "[4/5] Esperando healthchecks..."
sleep 30

# 5. Smoke test
echo "[5/5] Verificando funcionamiento..."
bash ./smoke-test.sh || { echo "Smoke test fall√≥ - revisar logs"; exit 1; }

echo "‚úì Update completado exitosamente"
