#!/bin/bash
echo "================================"
echo "  Rhinometric Platform Installer"
echo "================================"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no instalado"
    exit 1
fi

# Verificar licencia
if [ ! -f "license.lic" ]; then
    echo "❌ Archivo license.lic no encontrado"
    echo "Solicite su licencia en: soporte@rhinometric.com"
    exit 1
fi

# Descargar imagen (privada)
echo "Descargando plataforma..."
docker pull rhinometric/platform:trial

# Arrancar
docker-compose -f docker-compose.client.yml up -d

echo "✅ Instalación completada"
echo "Acceda a: http://localhost:3000"
