#!/usr/bin/env bash
set -euo pipefail
echo "[*] Parando stack DEMO..."
docker compose -f docker-compose.yml -f demo/docker-compose.override.demo.yml down
echo "✔ DEMO detenida."
