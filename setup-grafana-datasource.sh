#!/bin/bash

# Script para configurar datasource de Prometheus en Grafana automáticamente
echo "🔧 Configurando Grafana datasource..."

# Configuración del datasource
GRAFANA_URL="http://localhost:3003"
GRAFANA_USER="admin"
GRAFANA_PASS="admin123"
PROMETHEUS_URL="http://rhinometric-prometheus:9090"

# Crear datasource via API
curl -X POST \
  -H "Content-Type: application/json" \
  -u "$GRAFANA_USER:$GRAFANA_PASS" \
  -d '{
    "name": "Prometheus-Rhinometric",
    "type": "prometheus",
    "url": "'$PROMETHEUS_URL'",
    "access": "proxy",
    "basicAuth": false,
    "isDefault": true
  }' \
  "$GRAFANA_URL/api/datasources"

echo ""
echo "✅ Datasource configurado"