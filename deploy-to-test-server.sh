#!/bin/bash
# ========================================
# Rhinometric v2.5.0 - Deployment Script
# ========================================
# Transfer files to test server and deploy core stack

set -e

SERVER_IP="100.51.216.214"
KEY_FILE="$HOME/.ssh/rhinometric-test-key.pem"
REMOTE_USER="ubuntu"
REMOTE_DIR="rhinometric-v2.5.0"
LOCAL_DIR="/c/Users/canel/mi-proyecto/infrastructure/mi-proyecto"

echo "🚀 Rhinometric v2.5.0 - Automated Deployment"
echo "=============================================="
echo ""

# Step 1: Verify SSH key exists
echo "[1/7] Verifying SSH key..."
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ ERROR: SSH key not found at $KEY_FILE"
    exit 1
fi
chmod 400 "$KEY_FILE"
echo "✅ SSH key verified"
echo ""

# Step 2: Test SSH connection
echo "[2/7] Testing SSH connection..."
if ! ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no -o ConnectTimeout=5 $REMOTE_USER@$SERVER_IP "echo 'SSH OK'"; then
    echo "❌ ERROR: Cannot connect to server"
    exit 1
fi
echo "✅ SSH connection successful"
echo ""

# Step 3: Create package (excluding unnecessary files)
echo "[3/7] Creating deployment package..."
cd "$LOCAL_DIR"
tar czf /tmp/rhinometric-v2.5.0-deploy.tar.gz \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='terraform/.terraform' \
    --exclude='terraform/terraform.tfstate*' \
    --exclude='terraform/.terraform.lock.hcl' \
    --exclude='*.tar.gz' \
    --exclude='*.log' \
    docker-compose-v2.5.0-core.yml \
    nginx-core-v2.5.0.conf \
    config/ \
    licenses/ \
    security/ \
    entrypoint-*.sh \
    grafana/ \
    grafana-plugins-simple/ \
    grafana-branding/ \
    init-db/ \
    scripts/ \
    alertmanager/ \
    license-server-v2/ \
    rhinometric-ai-anomaly/ \
    rhinometric-veriverde/ \
    rhinometric-backup/ \
    rhinometric-report-generator/ \
    rhinometric-console/ \
    dashboard-builder/ \
    api-connector/ \
    api-proxy/

echo "✅ Package created: $(du -h /tmp/rhinometric-v2.5.0-deploy.tar.gz | cut -f1)"
echo ""

# Step 4: Transfer package to server
echo "[4/7] Transferring package to server..."
scp -i "$KEY_FILE" \
    -o StrictHostKeyChecking=no \
    /tmp/rhinometric-v2.5.0-deploy.tar.gz \
    $REMOTE_USER@$SERVER_IP:~/
echo "✅ Transfer complete"
echo ""

# Step 5: Extract and setup on server
echo "[5/7] Extracting files on server..."
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no $REMOTE_USER@$SERVER_IP <<'ENDSSH'
    set -e
    
    # Extract files
    rm -rf rhinometric-v2.5.0
    mkdir -p rhinometric-v2.5.0
    tar xzf rhinometric-v2.5.0-deploy.tar.gz -C rhinometric-v2.5.0/
    cd rhinometric-v2.5.0
    
    # Create .env file
    cat > .env <<'EOF'
# Database Credentials
POSTGRES_PASSWORD=rhinometric_secure_2024
REDIS_PASSWORD=redis_secure_2024

# Grafana Credentials
GRAFANA_USER=admin
GRAFANA_PASSWORD=RhinoAdmin2024!

# Console Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=ConsoleAdmin2024!
SECRET_KEY=$(openssl rand -base64 32)

# SMTP Configuration
SMTP_HOST=smtp.zoho.eu
SMTP_PORT=587
SMTP_USER=rafael.canelon@rhinometric.com
SMTP_PASSWORD=CHANGEME
SMTP_FROM=rafael.canelon@rhinometric.com
ALERT_EMAIL_TO=rafael.canelon@rhinometric.com

# JWT Secret
JWT_SECRET=$(openssl rand -base64 32)

# Timezone
TZ=Europe/Madrid

# CO2 Metrics
RENEWABLE_PERCENT=0
CO2_FACTOR=0.233
EOF

    echo "✅ Files extracted and .env created"
    
    # Show structure
    echo ""
    echo "📂 Deployment structure:"
    ls -lh
    echo ""
    echo "✅ Ready to deploy!"
ENDSSH

echo "✅ Server setup complete"
echo ""

# Step 6: Pull Docker images
echo "[6/7] Pulling Docker images (this may take 5-10 minutes)..."
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no $REMOTE_USER@$SERVER_IP <<'ENDSSH'
    cd rhinometric-v2.5.0
    docker compose -f docker-compose-v2.5.0-core.yml pull
ENDSSH
echo "✅ Docker images pulled"
echo ""

# Step 7: Build custom images
echo "[7/7] Building custom Docker images..."
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no $REMOTE_USER@$SERVER_IP <<'ENDSSH'
    cd rhinometric-v2.5.0
    docker compose -f docker-compose-v2.5.0-core.yml build --parallel
ENDSSH
echo "✅ Custom images built"
echo ""

# Cleanup local package
rm -f /tmp/rhinometric-v2.5.0-deploy.tar.gz

echo "=============================================="
echo "✅ DEPLOYMENT PREPARATION COMPLETE!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. SSH into server: ssh -i $KEY_FILE $REMOTE_USER@$SERVER_IP"
echo "2. Start stack: cd rhinometric-v2.5.0 && docker compose -f docker-compose-v2.5.0-core.yml up -d"
echo "3. Monitor logs: docker compose -f docker-compose-v2.5.0-core.yml logs -f"
echo ""
echo "Access URLs:"
echo "  - Console UI: http://$SERVER_IP:3002"
echo "  - Grafana:    http://$SERVER_IP:3000"
echo "  - Prometheus: http://$SERVER_IP:9090"
echo "  - Jaeger:     http://$SERVER_IP:16686"
echo ""
echo "Time to start testing! 🎉"
