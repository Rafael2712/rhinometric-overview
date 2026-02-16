#!/bin/sh
set -e

echo "🔐 Validando licencia..."
python3 validator.pyc /license/license.lic
if [ $? -ne 0 ]; then
    echo "❌ Licencia inválida o expirada"
    exit 1
fi

echo "✅ Licencia válida"
echo "🚀 Iniciando plataforma Rhinometric..."

# Arrancar todos los servicios
docker-compose up -d

# Esperar a que Grafana esté listo
echo "⏳ Esperando servicios..."
sleep 30

# Importar dashboards si no existen
for file in /app/monitoring/grafana/dashboards/*.json; do
  if [ -f "$file" ]; then
    curl -s -X POST http://admin:admin@grafana:3000/api/dashboards/db \
      -H "Content-Type: application/json" \
      -d @"$file" > /dev/null 2>&1
  fi
done

echo "✅ Plataforma lista"
echo "📊 Accesos:"
echo "   Grafana: http://localhost:3000 (admin/admin)"
echo "   Prometheus: http://localhost:9090"

# Mantener contenedor vivo
tail -f /dev/null
