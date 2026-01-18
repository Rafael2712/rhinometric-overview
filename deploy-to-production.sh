#!/bin/bash
# Rhinometric v2.5.0 - Production Deployment Script
# Autor: Rafael Canelón
# Fecha: 16 Diciembre 2025

set -e

echo "=========================================="
echo "Rhinometric v2.5.0 - Production Deploy"
echo "=========================================="
echo ""

# === CONFIGURATION ===
SERVER_USER="${SERVER_USER:-root}"
SERVER_HOST="${SERVER_HOST:-licensing.rhinometric.com}"
SERVER_PORT="${SERVER_PORT:-22}"
SERVER_BASE_PATH="${SERVER_BASE_PATH:-/app}"

DOWNLOADS_DIR="${SERVER_BASE_PATH}/static/downloads"
DOCS_DIR="${SERVER_BASE_PATH}/static/docs"

# === FILES TO DEPLOY ===
DEMO_OVA="rhinometric-demo-2.5.0.ova"
TRIAL_INSTALLER="rhinometric-trial-2.5.0-install.sh"
DOCS_ES_PDF="rhinometric-installation-guide-es.pdf"
DOCS_EN_PDF="rhinometric-installation-guide-en.pdf"

echo "📋 Pre-flight Check:"
echo "  Server: ${SERVER_USER}@${SERVER_HOST}:${SERVER_PORT}"
echo "  Base Path: ${SERVER_BASE_PATH}"
echo ""

# === STEP 1: Check SSH Connection ===
echo "🔑 Step 1/6: Testing SSH connection..."
if ssh -p ${SERVER_PORT} -o ConnectTimeout=10 ${SERVER_USER}@${SERVER_HOST} "echo 'SSH OK'" > /dev/null 2>&1; then
    echo "✅ SSH connection successful"
else
    echo "❌ ERROR: Cannot connect to ${SERVER_HOST}"
    echo "   Please check:"
    echo "   - Server is accessible"
    echo "   - SSH credentials are correct"
    echo "   - Firewall allows port ${SERVER_PORT}"
    exit 1
fi
echo ""

# === STEP 2: Create directories on server ===
echo "📁 Step 2/6: Creating directories on server..."
ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} << 'EOF'
mkdir -p /app/static/downloads
mkdir -p /app/static/docs/es
mkdir -p /app/static/docs/en
chmod -R 755 /app/static
echo "✅ Directories created"
EOF
echo ""

# === STEP 3: Upload Demo OVA (if exists) ===
echo "📦 Step 3/6: Uploading Demo OVA..."
if [ -f "${DEMO_OVA}" ]; then
    echo "   Uploading ${DEMO_OVA} (~3GB, this may take 10-30 minutes)..."
    scp -P ${SERVER_PORT} "${DEMO_OVA}" ${SERVER_USER}@${SERVER_HOST}:${DOWNLOADS_DIR}/ || {
        echo "⚠️  Warning: OVA upload failed (file may not exist locally)"
        echo "   You can upload it manually later"
    }
    echo "✅ OVA uploaded"
else
    echo "⚠️  Warning: ${DEMO_OVA} not found locally"
    echo "   Skipping OVA upload - you'll need to create and upload it manually"
fi
echo ""

# === STEP 4: Upload Trial Installer (if exists) ===
echo "📦 Step 4/6: Uploading Trial Installer..."
if [ -f "${TRIAL_INSTALLER}" ]; then
    scp -P ${SERVER_PORT} "${TRIAL_INSTALLER}" ${SERVER_USER}@${SERVER_HOST}:${DOWNLOADS_DIR}/
    ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} "chmod +x ${DOWNLOADS_DIR}/${TRIAL_INSTALLER}"
    echo "✅ Installer uploaded"
else
    echo "⚠️  Warning: ${TRIAL_INSTALLER} not found locally"
    echo "   Skipping installer upload - you'll need to create it manually"
fi
echo ""

# === STEP 5: Upload Documentation PDFs (if exist) ===
echo "📚 Step 5/6: Uploading Documentation..."
if [ -f "${DOCS_ES_PDF}" ]; then
    scp -P ${SERVER_PORT} "${DOCS_ES_PDF}" ${SERVER_USER}@${SERVER_HOST}:${DOCS_DIR}/es/
    echo "✅ Spanish PDF uploaded"
else
    echo "⚠️  Warning: ${DOCS_ES_PDF} not found - skipping"
fi

if [ -f "${DOCS_EN_PDF}" ]; then
    scp -P ${SERVER_PORT} "${DOCS_EN_PDF}" ${SERVER_USER}@${SERVER_HOST}:${DOCS_DIR}/en/
    echo "✅ English PDF uploaded"
else
    echo "⚠️  Warning: ${DOCS_EN_PDF} not found - skipping"
fi
echo ""

# === STEP 6: Configure and restart License Server ===
echo "🔧 Step 6/6: Configuring License Server..."
ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} << 'EOF'
cd /app

# Update .env with production URL
if ! grep -q "SERVER_BASE_URL" .env 2>/dev/null; then
    echo "SERVER_BASE_URL=https://licensing.rhinometric.com:5000" >> .env
    echo "✅ Added SERVER_BASE_URL to .env"
else
    sed -i 's|^SERVER_BASE_URL=.*|SERVER_BASE_URL=https://licensing.rhinometric.com:5000|' .env
    echo "✅ Updated SERVER_BASE_URL in .env"
fi

# Update SMTP password if not set
if ! grep -q "SMTP_PASSWORD" .env 2>/dev/null; then
    echo "⚠️  Warning: SMTP_PASSWORD not found in .env"
    echo "   You need to add it manually: SMTP_PASSWORD=041080Fe#"
fi

# Restart License Server container
echo "🔄 Restarting License Server..."
if docker ps | grep -q "rhinometric-license-server"; then
    docker restart rhinometric-license-server-v2 || docker restart license-server || {
        echo "⚠️  Could not find License Server container"
        echo "   Please restart it manually"
    }
    sleep 5
    echo "✅ License Server restarted"
else
    echo "⚠️  License Server container not running"
    echo "   You may need to start the stack with: docker compose up -d"
fi
EOF
echo ""

echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Verify .env on server has:"
echo "   SERVER_BASE_URL=https://licensing.rhinometric.com:5000"
echo "   SMTP_PASSWORD=041080Fe#"
echo ""
echo "2. Test download endpoints:"
echo "   ./test-download-endpoints.sh https://licensing.rhinometric.com:5000"
echo ""
echo "3. Test email system:"
echo "   ./scripts/test_license_emails.sh https://licensing.rhinometric.com:5000"
echo ""
echo "4. If all tests pass, proceed to Fase D (WordPress + GitHub release)"
echo ""
