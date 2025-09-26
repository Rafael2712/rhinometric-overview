#!/usr/bin/env bash
set -euo pipefail
URL="${GRAFANA_URL:-http://localhost:3000}"
USER="${GRAFANA_USER:-admin}"
PASS="${GRAFANA_PASS:-admin}"

LOKI_UID=$(curl -s -u "$USER:$PASS" "$URL/api/datasources" \
  | jq -r '.[] | select(.type=="loki" and .name=="Loki") | .uid')

jq -nc --arg uid "$LOKI_UID" '
{
  dashboard:{
    id:null, uid:"logs-smoke", title:"Logs - Smoke Test",
    time:{from:"now-15m",to:"now"}, refresh:"5s",
    panels:[
      {
        type:"stat", title:"Log lines/sec (Loki)",
        gridPos:{h:6,w:12,x:0,y:0},
        datasource:{type:"loki",uid:$uid},
        targets:[{refId:"A", datasource:{type:"loki",uid:$uid}, expr:"sum(rate({}[1m]))"}]
      }
    ]
  },
  folderId:0, overwrite:true
}' \
| curl -s -u "$USER:$PASS" -H "Content-Type: application/json" \
  -X POST "$URL/api/dashboards/db" -d @- | jq .
