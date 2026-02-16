#!/usr/bin/env bash
set -Eeuo pipefail
IMAGE="${RHINO_IMG:-rafael0410/rhinometric:secure}"
CONTAINER="${RHINO_NAME:-rhinometric}"
PORT="${RHINO_PORT:-3000}"
BIND="${RHINO_BIND:-127.0.0.1}"
[ -f "license.lic" ] || { echo "❌ Falta license.lic"; exit 1; }
command -v docker >/dev/null || { echo "❌ Docker no instalado"; exit 1; }
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER" --restart unless-stopped \
  -p "$BIND:$PORT:3000" \
  -v "$(pwd)/license.lic:/license/license.lic:ro" \
  -e GF_SECURITY_ADMIN_USER=admin \
  -e GF_SECURITY_ADMIN_PASSWORD="Admin$(date +%s)" \
  -e GF_AUTH_ANONYMOUS_ENABLED=false \
  "$IMAGE" >/dev/null
for i in {1..60}; do curl -fsS "http://$BIND:$PORT/api/health" >/dev/null && break; sleep 1; done
curl -fsS "http://$BIND:$PORT/api/health" >/dev/null || { echo "⚠️ No respondió. Revisa: docker logs $CONTAINER"; exit 1; }
echo "✅ Listo → http://$BIND:$PORT  (admin / la pass que pasaste por GF_SECURITY_ADMIN_PASSWORD)"
