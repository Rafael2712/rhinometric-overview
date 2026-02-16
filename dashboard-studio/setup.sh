#!/bin/bash

###############################################################################
# Quick Setup Script for Dashboard Studio
###############################################################################

set -e

echo "╔════════════════════════════════════════════════════╗"
echo "║  RhinoMetric Dashboard Studio - Quick Setup       ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Check if running in correct directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found"
    echo "   Please run this script from the dashboard-studio directory"
    exit 1
fi

# Step 1: Install dependencies
echo "📦 [1/4] Installing dependencies..."
npm install

# Step 2: Create .env if not exists
if [ ! -f ".env" ]; then
    echo "⚙️  [2/4] Creating .env file..."
    cat > .env <<EOF
VITE_API_BASE=http://localhost:8001
VITE_GRAFANA_URL=http://localhost:3000
EOF
    echo "✓ Created .env file"
else
    echo "⚙️  [2/4] Using existing .env file"
fi

# Step 3: Build for production
echo "🏗️  [3/4] Building production bundle..."
npm run build

# Step 4: Docker build
echo "🐳 [4/4] Building Docker image..."
docker build -t rhinometric-dashboard-studio:latest .

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║              ✓ Setup Complete!                     ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "🚀 Quick Start Options:"
echo ""
echo "1. Development mode (http://localhost:3001):"
echo "   npm run dev"
echo ""
echo "2. Production with Docker Compose:"
echo "   docker-compose up -d"
echo ""
echo "3. Production standalone:"
echo "   docker run -d -p 3001:3001 --name dashboard-studio \\"
echo "     --network mi-proyecto_rhinometric_network_v22 \\"
echo "     rhinometric-dashboard-studio:latest"
echo ""
echo "📖 Documentation: README.md"
echo "🧪 Run smoke test: ./smoke-test.sh"
echo ""
