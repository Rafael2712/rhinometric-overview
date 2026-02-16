#!/usr/bin/env bash
set -euo pipefail

# Password de Grafana para la demo (puedes cambiarla)
: "${GF_ADMIN_PASS:=Demo-Password-Temporal-123}"
export GF_ADMIN_USER=admin GF_ADMIN_PASS

echo "[*] Parando cualquier stack previo (para liberar puertos)..."
docker compose down || true

echo "[*] Construyendo 'web' si hace falta..."
if ! docker image inspect mi-proyecto-web >/dev/null 2>&1; then
  docker compose build web
fi

echo "[*] Iniciando stack DEMO (solo en 127.0.0.1)..."
if docker compose pull --help | grep -q -- '--ignore-buildable'; then
  docker compose -f docker-compose.yml -f demo/docker-compose.override.demo.yml pull --ignore-buildable || true
else
  docker compose -f docker-compose.yml -f demo/docker-compose.override.demo.yml pull || true
fi

docker compose -f docker-compose.yml -f demo/docker-compose.override.demo.yml up -d --remove-orphans

wait_for () {
  local name="$1" url="$2" pattern="$3" timeout="${4:-180}"
  echo "[*] Esperando ${name}..."
  SECONDS=0
  while true; do
    body="$(curl -fsS "$url" 2>/dev/null || true)"
    if echo "$body" | grep -Eq "$pattern"; then
      echo "    → ${name}: OK"
      break
    fi
    if (( SECONDS >= timeout )); then
      echo "✖ Timeout esperando ${name} (${url})"
      echo "Última respuesta:"
      echo "$body"
      exit 1
    fi
    sleep 1
  done
}

# Nota: patrones tolerantes a espacios
wait_for "Grafana (DB interna)" "http://127.0.0.1:3300/api/health" '"database"[[:space:]]*:[[:space:]]*"ok"'
wait_for "Prometheus"           "http://127.0.0.1:9099/-/ready"      'Ready'
wait_for "Loki"                 "http://127.0.0.1:3110/ready"         'ready'

echo
echo "✅ DEMO lista SOLO LOCAL:"
echo "- App:        http://127.0.0.1:8088"
echo "- Grafana:    http://127.0.0.1:3300  (user: admin / pass: ${GF_ADMIN_PASS})"
echo "- Prometheus: http://127.0.0.1:9099"
echo "- Loki API:   http://127.0.0.1:3110"
echo "- Traefik M.: http://127.0.0.1:8099/metrics"
