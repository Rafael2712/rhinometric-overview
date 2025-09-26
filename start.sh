#!/bin/bash

# Verificar licencia antes de arrancar
if [ ! -f "license.lic" ]; then
    echo "❌ No se encontró archivo de licencia (license.lic)"
    echo "   Solicite una licencia de prueba en admin@rhinometric.com"
    exit 1
fi

echo "Validando licencia..."
python3 licensing/scripts/license_validator.py license.lic

if [ $? -ne 0 ]; then
    echo "❌ Licencia inválida o expirada"
    exit 1
fi

echo "✅ Licencia válida, iniciando servicios..."
source .env.license
docker-compose up -d

echo "Plataforma iniciada correctamente"
echo "Acceda a http://localhost:3000 para Grafana"
