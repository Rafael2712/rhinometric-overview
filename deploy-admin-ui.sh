#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# DEPLOY ADMIN UI TO AWS LICENSE SERVER
# ═══════════════════════════════════════════════════════════════════════════

SERVER="54.197.192.198"
USER="ubuntu"
REMOTE_PATH="/home/ubuntu/license-server/app"
SSH_KEY="$HOME/.ssh/lightsail-license-server.pem"

echo "🚀 Deploying Admin UI to AWS License Server..."

# 1. Upload modified main.py
echo "📤 Uploading main.py..."
scp -i ${SSH_KEY} license-server-v2/main.py ${USER}@${SERVER}:${REMOTE_PATH}/main.py

# 2. Create static directory on server
echo "📁 Creating static directory..."
ssh -i ${SSH_KEY} ${USER}@${SERVER} "mkdir -p ${REMOTE_PATH}/static"

# 3. Upload admin UI
echo "📤 Uploading Admin UI (index.html)..."
scp -i ${SSH_KEY} license-server-v2/static/index.html ${USER}@${SERVER}:${REMOTE_PATH}/static/index.html

# 4. Restart License Server (Docker)
echo "🔄 Restarting License Server container..."
ssh -i ${SSH_KEY} ${USER}@${SERVER} "cd /home/ubuntu/license-server && docker compose restart license-api"

# 5. Wait for service to start
echo "⏳ Waiting 10 seconds for service to start..."
sleep 10

# 6. Test Admin UI
echo "✅ Testing Admin UI..."
curl -s http://${SERVER}:8090/admin | grep -o '<title>.*</title>' || echo "❌ Admin UI not responding"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Admin UI URL: http://${SERVER}:8090/admin"
echo ""
echo "📊 Default credentials:"
echo "   Username: admin"
echo "   Password: rhinometric2024"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
