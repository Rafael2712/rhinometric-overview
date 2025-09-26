#!/usr/bin/env bash
set -euo pipefail
URL="${GRAFANA_URL:-http://localhost:3000}"
USER="${GRAFANA_USER:-admin}"
PASS="${GRAFANA_PASS:-admin}"

PROM_UID=$(curl -s -u "$USER:$PASS" "$URL/api/datasources" \
  | jq -r '.[] | select(.type=="prometheus") | .uid')

DASH_UID=$(curl -s -u "$USER:$PASS" "$URL/api/search?query=Containers%20-%20Mini" \
  | jq -r '.[0].uid')

curl -s -u "$USER:$PASS" "$URL/api/dashboards/uid/$DASH_UID" > /tmp/cadv.json

jq --arg uid "$PROM_UID" '
  .dashboard.panels |= map(
    .datasource={"type":"prometheus","uid":$uid}
    | .targets = ( .targets // [] | map(.datasource={"type":"prometheus","uid":$uid}) )
  )' /tmp/cadv.json > /tmp/cadv_fix.json

curl -s -u "$USER:$PASS" -H "Content-Type: application/json" \
  -X POST "$URL/api/dashboards/db" \
  -d "$(jq -c '{dashboard:.dashboard, overwrite:true, folderId:0}' /tmp/cadv_fix.json)" | jq .
