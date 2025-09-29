#!/usr/bin/env bash
set -Eeuo pipefail

IMG="${RHINO_IMG:-rafael0410/rhinometric:trial-v2}"
CONTAINER="${RHINO_NAME:-rhinometric-platform}"

# Exposición mínima: solo Grafana en loopback
BIND_ADDR="${RHINO_BIND:-127.0.0.1}"
GRAFANA_PORT="${RHINO_GRAFANA_PORT:-3000}"

# 0 = seguro (sin docker.sock), 1 = habilita métricas de contenedores
WITH_DOCKER="${RHINO_WITH_DOCKER:-0}"

# Ruta de licencia: permite LICENSE_PATH o intenta ../license.lic
LICENSE_PATH="${LICENSE_PATH:-./license.lic}"
if [[ ! -f "$LICENSE_PATH" && -f "../license.lic" ]]; then
  LICENSE_PATH="../license.lic"
fi

log()  { echo "[$(date +'%H:%M:%S')] $*"; }
fail() { echo "❌ $*" >&2; exit 1; }

echo "================================================"
echo "  Rhinometric Platform - Instalador Oficial"
echo "================================================"
# 1) Prechequeos
command -v docker >/dev/null 2>&1 \
  || fail "Docker no está instalado o no es accesible desde WSL. Activa WSL Integration en Docker Desktop."

[[ -f "$LICENSE_PATH" ]] \
  || fail "No se encontró license.lic (buscado en: $LICENSE_PATH o ../license.lic)."

# 2) Password aleatoria para Grafana admin
ADMIN_PASS="$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 20 || true)"
[[ -n "$ADMIN_PASS" ]] || ADMIN_PASS="Admin$(date +%s)"

log "Descargando imagen ${IMG} ..."
docker pull "${IMG}"

# 3) Limpieza de contenedor previo
if docker ps -a --format '{{.Names}}' | grep -qx "${CONTAINER}"; then
  log "Eliminando contenedor previo ${CONTAINER} ..."
  docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
fi
# 4) Montajes opcionales para métricas de contenedores
EXTRA_VOLS=()
if [[ "${WITH_DOCKER}" == "1" ]]; then
  log "⚠️  Habilitando métricas de contenedores (montando /var/run/docker.sock)."
  EXTRA_VOLS+=("-v" "/var/run/docker.sock:/var/run/docker.sock")
fi

# 5) Arranque: SOLO Grafana expuesto; Prometheus/Loki internos
log "Iniciando servicios (Grafana en http://${BIND_ADDR}:${GRAFANA_PORT}) ..."
docker run -d --name "${CONTAINER}" --restart unless-stopped \
  -p "${BIND_ADDR}:${GRAFANA_PORT}:3000" \
  -v "$(readlink -f "$LICENSE_PATH"):/license/license.lic:ro" \
  "${EXTRA_VOLS[@]}" \
  -e GF_SECURITY_ADMIN_USER=admin \
  -e GF_SECURITY_ADMIN_PASSWORD="${ADMIN_PASS}" \
  -e GF_AUTH_ANONYMOUS_ENABLED=false \
  -e GF_USERS_ALLOW_SIGN_UP=false \
  -e GF_USERS_ALLOW_ORG_CREATE=false \
  -e GF_USERS_AUTO_ASSIGN_ORG=true \
  -e GF_USERS_AUTO_ASSIGN_ROLE=Viewer \
  -e GF_SECURITY_ALLOW_EMBEDDING=false \
  -e GF_SNAPSHOTS_ENABLED=false \
  -e GF_SNAPSHOTS_EXTERNAL_ENABLED=false \
  -e GF_EXPLORE_ENABLED=false \
  "${IMG}" >/dev/null
# 6) Esperar Grafana ready
log "Esperando a que Grafana esté listo..."
for i in {1..60}; do
  if curl -fsS "http://${BIND_ADDR}:${GRAFANA_PORT}/api/health" >/dev/null; then
    break
  fi
  sleep 1
done

echo
echo "✅ Instalación completada"
echo "URL  : http://${BIND_ADDR}:${GRAFANA_PORT}"
echo "User : admin"
echo "Pass : ${ADMIN_PASS}"
echo
echo "🔒 Seguridad aplicada:"
echo "   • Solo Grafana expuesto en ${BIND_ADDR}:${GRAFANA_PORT}"
echo "   • Prometheus/Loki quedan internos"
echo "   • Sin docker.sock por defecto (actívalo solo si necesitas cadvisor):"
echo "        RHINO_WITH_DOCKER=1 ./install.sh"
echo
echo "🧹 Para desinstalar:"
echo "   docker rm -f ${CONTAINER}"
