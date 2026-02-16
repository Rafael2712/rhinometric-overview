#!/bin/bash
# Script para ejecutar migración de RBAC
# Uso: ./run_migration.sh

set -e  # Exit on error

echo "🔄 Ejecutando migración RBAC en PostgreSQL..."

# Variables de entorno (ajustar si es necesario)
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-rhinometric}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-rhinometric}"
POSTGRES_DB="${POSTGRES_DB:-rhinometric}"

# Construir connection string
export PGPASSWORD="$POSTGRES_PASSWORD"

echo "📡 Conectando a PostgreSQL..."
echo "   Host: $POSTGRES_HOST:$POSTGRES_PORT"
echo "   Database: $POSTGRES_DB"
echo "   User: $POSTGRES_USER"
echo ""

# Verificar conexión
if ! psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1" > /dev/null 2>&1; then
    echo "❌ Error: No se puede conectar a PostgreSQL"
    echo "   Verifica que el contenedor esté corriendo:"
    echo "   docker ps | grep postgres"
    exit 1
fi

echo "✅ Conexión a PostgreSQL exitosa"
echo ""

# Ejecutar migración
echo "🚀 Ejecutando 001_rbac_tables.sql..."
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f migrations/001_rbac_tables.sql

echo ""
echo "✅ Migración completada exitosamente!"
echo ""

# Mostrar resumen
echo "📊 Resumen de tablas creadas:"
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt" | grep -E "roles|users|permissions"

echo ""
echo "👤 Usuario OWNER creado:"
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT u.username, u.email, r.name as role FROM users u JOIN user_roles ur ON u.id = ur.user_id JOIN roles r ON ur.role_id = r.id;"

echo ""
echo "🎉 ¡Migración RBAC completada!"
echo ""
echo "⚠️  IMPORTANTE: Cambiar la contraseña del usuario 'admin' en el primer login"
echo "   Username: admin"
echo "   Password temporal: admin"
