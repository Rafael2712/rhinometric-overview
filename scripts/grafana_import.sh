#!/usr/bin/env bash
set -euo pipefail
FILE="${1:?Usage: grafana_import.sh <dashboard.json>}"
URL="${GRAFANA_URL:-http://localhost:80/grafana}"

# Auth: usa token si existe, si no user/pass
if [ -n "${GRAFANA_TOKEN:-}" ]; then
  AUTH=(-H "Authorization: Bearer $GRAFANA_TOKEN")
else
  USER="${GRAFANA_USER:-admin}"
  PASS="${GRAFANA_PASSWORD:-admin}"
  AUTH=(-u "$USER:$PASS")
fi

# Leer el archivo JSON completo (ya incluye structure "dashboard": {...})
DASH_CONTENT=$(cat "$FILE")

echo "🚀 Importing dashboard from: $FILE"
echo "📡 Grafana URL: $URL/api/dashboards/db"
echo "👤 User: $USER"

# Enviar el JSON tal como está (ya tiene formato correcto)
curl -s "${AUTH[@]}" -H "Content-Type: application/json" \
  -X POST "$URL/api/dashboards/db" \
  -d "$DASH_CONTENT" \
  | jq .
