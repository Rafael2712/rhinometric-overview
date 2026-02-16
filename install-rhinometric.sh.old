#!/bin/bash
echo "🦏 Instalador Rhinometric Platform v1.0"
echo "======================================"

# Verificar Docker
if ! docker --version >/dev/null 2>&1; then
    echo "❌ Docker no instalado"
    echo "📥 Instale desde: https://docker.com"
    exit 1
fi

# Descargar configuración
echo "📥 Descargando plataforma..."
curl -sL https://rhinometric.com/demo/config.tar.gz | tar xz

# Iniciar
echo "🚀 Iniciando servicios..."
docker-compose up -d

# Esperar
echo "⏳ Configurando (30 segundos)..."
sleep 30

# Verificar
if curl -sf http://localhost:3000 >/dev/null; then
    echo ""
    echo "✅ INSTALACIÓN EXITOSA"
    echo "======================================"
    echo "📊 Acceso: http://localhost:3000"
    echo "👤 Usuario: admin"
    echo "🔑 Contraseña: admin"
    echo "📧 Soporte: soporte@rhinometric.com"
    echo "======================================"
else
    echo "⚠️ Error. Contacte soporte@rhinometric.com"
fi
