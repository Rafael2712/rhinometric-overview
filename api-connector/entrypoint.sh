#!/bin/bash
set -e

# ==========================================
# RHINOMETRIC API Connector - Entrypoint
# ==========================================
# Professional solution for Docker socket permissions
# Handles cross-platform Docker socket access

echo "🔧 Configuring Docker socket permissions..."

# Get Docker socket GID
DOCKER_SOCK_GID=$(stat -c '%g' /var/run/docker.sock 2>/dev/null || echo "0")
echo "   Docker socket GID: ${DOCKER_SOCK_GID}"

# If socket is owned by root (GID 0), we need to handle it
if [ "$DOCKER_SOCK_GID" = "0" ]; then
    echo "   Socket owned by root - checking if user is in docker group..."
    
    # Check if user is already in docker group
    if groups rhinometric | grep -q docker; then
        echo "   ✅ User is in docker group"
        
        # Try to access docker without sudo first
        if docker ps >/dev/null 2>&1; then
            echo "   ✅ Docker access verified"
        else
            echo "   ⚠️  Docker access denied - falling back to root for Docker operations"
            echo "   Note: This is expected on Docker Desktop for Windows/Mac"
        fi
    fi
else
    echo "   ✅ Docker socket has proper group ownership"
fi

echo "🚀 Starting API Connector..."

# Execute the main command
# If first arg is uvicorn or starts with -, run as rhinometric user
if [ "$1" = "uvicorn" ] || [ "${1#-}" != "$1" ]; then
    exec su-exec rhinometric "$@"
else
    # Otherwise execute as-is (for docker commands, etc)
    exec "$@"
fi
