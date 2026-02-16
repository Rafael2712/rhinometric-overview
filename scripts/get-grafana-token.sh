#!/bin/bash
# ============================================
# Script para obtener Grafana API Token
# ============================================

echo "🔑 Obteniendo Grafana API Token..."
echo ""

# Esperar a que Grafana esté listo
echo "⏳ Esperando a que Grafana esté listo..."
sleep 5

# Crear API token
TOKEN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -u admin:admin \
  http://localhost:3000/api/auth/keys \
  -d "{\"name\":\"rhinometric-connector-$(date +%s)\",\"role\":\"Admin\"}")

# Extraer el token
API_TOKEN=$(echo "$TOKEN_RESPONSE" | grep -o '"key":"[^"]*' | cut -d'"' -f4)

if [ -z "$API_TOKEN" ]; then
  echo "❌ Error al crear el token. Respuesta de Grafana:"
  echo "$TOKEN_RESPONSE"
  echo ""
  echo "Intenta manualmente:"
  echo "1. Abre http://localhost:80 (Grafana)"
  echo "2. Login: admin / admin"
  echo "3. Configuration → API Keys → Add API Key"
  echo "4. Name: rhinometric-connector, Role: Admin"
  echo "5. Copia el token generado"
  exit 1
fi

echo "✅ Token creado exitosamente:"
echo ""
echo "$API_TOKEN"
echo ""
echo "📝 Copia este token y ejecuta:"
echo ""
echo "echo 'GRAFANA_URL=http://rhinometric-grafana:3000' > api-connector/.env"
echo "echo 'GRAFANA_API_TOKEN=$API_TOKEN' >> api-connector/.env"
echo "echo 'DATABASE_URL=postgresql://rhinometric:rhinometric2024@rhinometric-postgres:5432/rhinometric' >> api-connector/.env"
echo ""
echo "Luego reinicia el API Connector:"
echo "docker compose -f docker-compose-v2.2.0.yml restart api-connector"
