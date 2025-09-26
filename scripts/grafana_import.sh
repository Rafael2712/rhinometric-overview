#!/usr/bin/env bash
set -euo pipefail
FILE="${1:?Usage: grafana_import.sh <dashboard.json>}"
URL="${GRAFANA_URL:-http://localhost:3000}"

# Auth: usa token si existe, si no user/pass
if [ -n "${GRAFANA_TOKEN:-}" ]; then
  AUTH=(-H "Authorization: Bearer $GRAFANA_TOKEN")
else
  USER="${GRAFANA_USER:-admin}"
  PASS="${GRAFANA_PASS:-admin}"
  AUTH=(-u "$USER:$PASS")
fi

DASH=$(jq -c '.' "$FILE")
curl -s "${AUTH[@]}" -H "Content-Type: application/json" \
  -X POST "$URL/api/dashboards/db" \
  -d "{\"dashboard\":$DASH,\"overwrite\":true,\"folderId\":0}" \
  | jq .
