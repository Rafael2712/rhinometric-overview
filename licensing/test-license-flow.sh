#!/usr/bin/env bash
set -euo pipefail

# RHINOMETRIC v2.5.0 - License Flow Test Script
# Propósito: Probar emisión de licencias de prueba de 30 días y envío por email

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }

# Configuración (NO hardcoded - usar variables de entorno)
LICENSE_API="${LICENSE_API:-http://localhost:8002}"
SMTP_HOST="${SMTP_HOST:-smtp.example.com}"
SMTP_PORT="${SMTP_PORT:-587}"
SMTP_USER="${SMTP_USER:-noreply@example.com}"
SMTP_FROM="${SMTP_FROM:-RhinoMetric Licensing <licenses@example.com>}"
TEST_EMAIL="${TEST_EMAIL:-user@example.com}"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  RHINOMETRIC License Flow - Test Script"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 1. Verificar License Server
log_info "[1/5] Verificando License Server..."
if curl -sf --max-time 10 "${LICENSE_API}/health" > /dev/null 2>&1; then
    log_success "License Server responde en ${LICENSE_API}"
else
    log_error "License Server NO responde en ${LICENSE_API}"
    exit 1
fi

# 2. Solicitar licencia de prueba de 30 días
log_info "[2/5] Solicitando licencia de prueba de 30 días..."
EXPIRATION_DATE=$(date -d "+30 days" +%Y-%m-%d 2>/dev/null || date -v+30d +%Y-%m-%d)

REQUEST_RESPONSE=$(curl -sf --max-time 10 -X POST "${LICENSE_API}/api/licenses/trial" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"${TEST_EMAIL}\",
        \"license_type\": \"trial\",
        \"expiration\": \"${EXPIRATION_DATE}\",
        \"host_limit\": 1,
        \"company\": \"Test Company\",
        \"features\": [\"monitoring\", \"alerting\", \"ai-anomaly\"]
    }" 2>&1)

if echo "$REQUEST_RESPONSE" | grep -q "license_key"; then
    LICENSE_KEY=$(echo "$REQUEST_RESPONSE" | grep -o '"license_key":"[^"]*"' | cut -d'"' -f4)
    log_success "Licencia generada: ${LICENSE_KEY:0:20}..."
else
    log_error "No se pudo generar licencia: ${REQUEST_RESPONSE}"
    exit 1
fi

# 3. Verificar archivo .lic generado
log_info "[3/5] Verificando archivo .lic generado..."
LICENSE_FILE=$(echo "$REQUEST_RESPONSE" | grep -o '"file":"[^"]*"' | cut -d'"' -f4 || echo "")

if [ -n "$LICENSE_FILE" ] && [ -f "$LICENSE_FILE" ]; then
    log_success "Archivo .lic existe: ${LICENSE_FILE}"
    log_info "Contenido (primeras líneas):"
    head -5 "$LICENSE_FILE" | sed 's/^/  /'
else
    log_error "Archivo .lic NO existe"
fi

# 4. Enviar email con licencia adjunta
log_info "[4/5] Enviando email con licencia adjunta..."

# Crear payload para envío de email
EMAIL_PAYLOAD=$(cat <<EOF
{
    "to": "${TEST_EMAIL}",
    "from": "${SMTP_FROM}",
    "subject": "Tu licencia de prueba de RhinoMetric v2.5.0",
    "body": "Hola,\n\nGracias por solicitar RhinoMetric. Adjunto encontrarás tu licencia de prueba de 30 días.\n\nCaracterísticas incluidas:\n- Monitoreo completo\n- Alertas personalizadas\n- Detección de anomalías con IA\n\nPara activar la licencia:\n1. Descarga el archivo adjunto (.lic)\n2. Copia el archivo a /opt/rhinometric/licenses/\n3. Reinicia el servicio: docker compose restart\n\nLa licencia expira el: ${EXPIRATION_DATE}\n\nSoporte: support@rhinometric.com\n\n--\nRhinoMetric Team",
    "attachment": "${LICENSE_FILE}",
    "smtp_config": {
        "host": "${SMTP_HOST}",
        "port": ${SMTP_PORT},
        "user": "${SMTP_USER}",
        "use_tls": true
    }
}
EOF
)

EMAIL_RESPONSE=$(curl -sf --max-time 20 -X POST "${LICENSE_API}/api/licenses/send-email" \
    -H "Content-Type: application/json" \
    -d "$EMAIL_PAYLOAD" 2>&1) || true

if echo "$EMAIL_RESPONSE" | grep -q "sent"; then
    log_success "Email enviado a ${TEST_EMAIL}"
else
    log_error "No se pudo enviar email: ${EMAIL_RESPONSE}"
fi

# 5. Validar licencia generada
log_info "[5/5] Validando licencia generada..."
VALIDATE_RESPONSE=$(curl -sf --max-time 10 -X POST "${LICENSE_API}/api/licenses/validate" \
    -H "Content-Type: application/json" \
    -d "{\"license_key\": \"${LICENSE_KEY}\"}" 2>&1)

if echo "$VALIDATE_RESPONSE" | grep -q '"valid":true'; then
    log_success "Licencia válida"
    
    # Mostrar detalles
    log_info "Detalles de la licencia:"
    echo "$VALIDATE_RESPONSE" | grep -o '"expiration":"[^"]*"' | sed 's/^/  /'
    echo "$VALIDATE_RESPONSE" | grep -o '"features":\[[^]]*\]' | sed 's/^/  /'
else
    log_error "Licencia inválida: ${VALIDATE_RESPONSE}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
log_success "TEST LICENSE FLOW COMPLETADO"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Configuración SMTP usada (verificar en .env):"
echo "  SMTP_HOST=${SMTP_HOST}"
echo "  SMTP_PORT=${SMTP_PORT}"
echo "  SMTP_USER=${SMTP_USER}"
echo "  SMTP_FROM=${SMTP_FROM}"
echo ""
echo "IMPORTANTE: Actualizar variables en .env.prod/.env.demo:"
echo "  LICENSE_API=http://license-server:8002"
echo "  SMTP_HOST=smtp.tu-dominio.com"
echo "  SMTP_PORT=587"
echo "  SMTP_USER=noreply@tu-dominio.com"
echo "  SMTP_PASSWORD=<contraseña_segura>"
echo "  SMTP_FROM='RhinoMetric Licensing <licenses@tu-dominio.com>'"
echo ""
