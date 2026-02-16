#!/bin/bash
# Instalador automático Rhinometric

echo "🚀 Instalando Rhinometric Platform..."

# Detectar OS
OS="$(uname -s)"

# Descargar configuración
curl -sL https://raw.githubusercontent.com/tu-repo/main/docker-compose-demo.yml -o docker-compose.yml
curl -sL https://raw.githubusercontent.com/tu-repo/main/prometheus.yml -o prometheus.yml

# Crear directorios necesarios
mkdir -p grafana-provisioning/datasources

# Descargar datasources preconfigurados
curl -sL https://raw.githubusercontent.com/tu-repo/main/datasources.yml \
  -o grafana-provisioning/datasources/datasources.yml

# Verificar Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker no está corriendo. Inicialo primero."
    exit 1
fi

# Limpiar instalaciones previas
docker-compose down 2>/dev/null || true

# Iniciar servicios
docker-compose up -d

echo "⏳ Esperando servicios..."
sleep 30

# Verificar salud
if curl -sf http://localhost:3000/api/health > /dev/null; then
    echo "✅ Instalación completada"
    echo "📊 Accede a: http://localhost:3000"
    echo "🔐 Usuario: admin / Contraseña: admin"
else
    echo "⚠️ Algo falló. Verifica: docker-compose logs"
fi
