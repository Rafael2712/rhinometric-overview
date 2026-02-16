#!/bin/bash

# RhinoMetric SaaS - Development Setup Script

set -e

echo "🏗️  RhinoMetric SaaS - Configuración de Desarrollo"
echo "================================================="

# Verificar dependencias
echo "📋 Verificando dependencias..."

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js no está instalado. Versión requerida: 10.24.0+"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✅ Node.js: $NODE_VERSION"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    exit 1
fi

echo "✅ Docker: $(docker --version)"

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado"
    exit 1
fi

echo "✅ Docker Compose: $(docker-compose --version)"

# Configurar backend
echo ""
echo "🔧 Configurando Backend..."
cd backend

# Instalar dependencias
echo "📦 Instalando dependencias de Node.js..."
npm install

# Crear archivo de entorno si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env..."
    cp .env.example .env
    echo "⚠️  IMPORTANTE: Edita backend/.env con tus configuraciones"
fi

# Volver a raíz
cd ..

# Configurar Docker
echo ""
echo "🐳 Configurando Docker..."
cd infrastructure/docker

# Crear archivo de entorno si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env para Docker..."
    cp .env.development .env
fi

echo ""
echo "🚀 Levantando servicios..."

# Levantar servicios de base de datos
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Esperar a que PostgreSQL esté listo
echo "⏳ Esperando a que PostgreSQL esté listo..."
sleep 10

# Volver a backend para migraciones
cd ../../backend

# Ejecutar migraciones
echo "🗄️  Ejecutando migraciones de base de datos..."
npm run migrate

echo ""
echo "✅ ¡Configuración completada!"
echo ""
echo "🎯 Próximos pasos:"
echo "  1. cd backend && npm run dev          # Iniciar API en desarrollo"
echo "  2. Abrir http://localhost:3001        # API endpoint"
echo "  3. Abrir http://localhost:3001/api/v1/health  # Health check"
echo ""
echo "📊 URLs útiles:"
echo "  - API: http://localhost:3001"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "📖 Documentación:"
echo "  - API: docs/api/README.md"
echo "  - Despliegue: docs/deployment/README.md"