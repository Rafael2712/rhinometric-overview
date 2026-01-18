#!/bin/bash

# RHINOMETRIC v2.4.0 - Plugin Build Script
# Este script construye los plugins de Grafana para Rhinometric

set -e

echo "═══════════════════════════════════════════════════════════"
echo "🔨 RHINOMETRIC v2.4.0 - Building Grafana Plugins"
echo "═══════════════════════════════════════════════════════════"

PLUGINS_DIR="./grafana-plugins"

# Dashboard Builder Plugin
echo ""
echo "📦 Building Dashboard Builder Plugin..."
cd "$PLUGINS_DIR/rhinometric-dashboard-builder"

if [ ! -d "node_modules" ]; then
    echo "📥 Installing dependencies..."
    npm install --legacy-peer-deps
fi

echo "🔨 Building plugin..."
npm run build

cd ../..

# API Connector Plugin
echo ""
echo "📦 Building API Connector Plugin..."
cd "$PLUGINS_DIR/rhinometric-api-connector"

if [ ! -d "node_modules" ]; then
    echo "📥 Installing dependencies..."
    npm install --legacy-peer-deps
fi

echo "🔨 Building plugin..."
npm run build

cd ../..

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Plugins Built Successfully!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📂 Plugin Locations:"
echo "   - Dashboard Builder: $PLUGINS_DIR/rhinometric-dashboard-builder/dist"
echo "   - API Connector: $PLUGINS_DIR/rhinometric-api-connector/dist"
echo ""
echo "🚀 Next Steps:"
echo "   1. Run: docker compose -f docker-compose-v2.2.0.yml restart grafana"
echo "   2. Access Grafana at http://localhost:80"
echo "   3. Navigate to Menu → Apps → Rhinometric plugins"
echo ""
