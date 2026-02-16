#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# RHINOMETRIC LICENSE SERVER - Database Initialization Script
# ═══════════════════════════════════════════════════════════════════════════
# 
# This script initializes the database schema on first run.
# It's safe to run multiple times (uses IF NOT EXISTS).
#
# Usage:
#   ./init_database.sh
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

echo "🔧 Initializing Rhinometric License Database..."

# Database connection parameters
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-rhinometric_trial}"
DB_USER="${POSTGRES_USER:-rhinometric}"
DB_PASSWORD="${POSTGRES_PASSWORD:-rhinometric}"

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "   PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Run the SQL initialization script
echo "📊 Creating tables and indexes..."
PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f /app/init_db.sql

if [ $? -eq 0 ]; then
    echo "✅ Database initialized successfully!"
    echo ""
    echo "📋 Summary:"
    echo "   - licenses table: ✅"
    echo "   - license_activations table: ✅"
    echo "   - license_validation_failures table: ✅"
    echo "   - external_apis table: ✅"
    echo "   - Indexes created: ✅"
    echo "   - Views created: ✅"
    echo ""
    echo "🚀 Ready to start License Server!"
else
    echo "❌ Database initialization failed!"
    exit 1
fi
