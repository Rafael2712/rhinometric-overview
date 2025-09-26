#!/bin/bash

# Configuración
API_KEY="glsa_LhaVtAVmzU9NMnXOh955waHAUZtAShJQ_7a41ec80"
GRAFANA_URL="http://localhost:3000"
LOKI_URL="http://localhost:3100"  # Para comandos desde el host
DATASOURCE_NAME="Loki"
DATASOURCE_ID=5
DATASOURCE_UID="ceyulvcxhyww0f"

# 1. Verificar que Loki está listo
echo "=== Verificando estado de Loki ==="
curl -s $LOKI_URL/ready
echo ""
if ! curl -s $LOKI_URL/ready | grep -q "Ready"; then
  echo "Loki no está listo. Reiniciando contenedor..."
  docker compose -f docker-compose-unified.yml restart loki
  echo "Esperando 30 segundos para que Loki esté listo..."
  sleep 30
  curl -s $LOKI_URL/ready
  echo ""
fi

# 2. Eliminar datasource existente para evitar conflictos
echo "=== Eliminando datasource $DATASOURCE_NAME si existe ==="
curl -X DELETE \
  -H "Authorization: Bearer $API_KEY" \
  $GRAFANA_URL/api/datasources/name/$DATASOURCE_NAME
echo ""

# 3. Instrucciones para configurar manualmente en Grafana
echo "=== Por favor, configura el datasource en Grafana ==="
echo "1. Abre http://localhost:3000 en tu navegador"
echo "2. Inicia sesión (admin/admin o tu contraseña)"
echo "3. Ve a Administration > Data sources > Add data source"
echo "4. Selecciona 'Loki' y configura:"
echo "   - Name: $DATASOURCE_NAME"
echo "   - URL: http://loki:3100"
echo "   - Access: Server (default)"
echo "   - Custom HTTP Headers: Header='X-Scope-OrgID', Value='1'"
echo "   - Max lines: 1000"
echo "5. Haz clic en 'Save & Test' (debe decir 'Data source successfully connected')"
echo ""
echo "=== Presiona Enter después de configurar el datasource ==="
read -p ""

# 4. Enviar un log de prueba a Loki
echo "=== Enviando log de prueba a Loki ==="
curl -H "Content-Type: application/json" \
  -d '{"streams": [{"stream": {"job": "test"}, "values": [["'"$(date +%s%N)"'", "Log de prueba desde script corregido"]]}]}' \
  $LOKI_URL/loki/api/v1/push
echo ""

# 5. Verificar el datasource en Grafana
echo "=== Verificando health check del datasource ==="
curl -X GET \
  -H "Authorization: Bearer $API_KEY" \
  $GRAFANA_URL/api/datasources/$DATASOURCE_ID/health
echo ""

# 6. Instrucciones para probar en Grafana
echo "=== Prueba el log en Grafana ==="
echo "1. En Grafana, ve a Explore > Selecciona datasource 'Loki'"
echo "2. Ejecuta la query: {job=\"test\"}"
echo "3. Deberías ver 'Log de prueba desde script corregido'"
