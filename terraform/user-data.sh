#!/bin/bash
set -e

# Script de inicialización para instancia Rhinometric Test Server
# Instala Docker, Docker Compose y prepara el sistema

echo "=========================================="
echo "Rhinometric v2.5.0 Test Server Setup"
echo "=========================================="

# Update system
echo "[1/8] Updating system packages..."
apt-get update -y
apt-get upgrade -y

# Install dependencies
echo "[2/8] Installing dependencies..."
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    wget \
    git \
    htop \
    vim \
    unzip \
    jq

# Install Docker
echo "[3/8] Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose v2
echo "[4/8] Installing Docker Compose..."
DOCKER_COMPOSE_VERSION="2.24.0"
curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Enable Docker service
echo "[5/8] Enabling Docker service..."
systemctl enable docker
systemctl start docker

# Configure data volume (si está montado)
echo "[6/8] Preparing data directories..."
mkdir -p /home/ubuntu/rhinometric_data_v2.2/{postgres,redis,loki,jaeger,prometheus,grafana,nginx/logs,license-server/logs,console-backend/logs,ai-anomaly/{models,data},reports,temp,alertmanager,license-monitor/logs}
mkdir -p /home/ubuntu/rhinometric_backups

# Montar EBS volume si existe
if [ -e /dev/xvdf ]; then
    echo "[7/8] Mounting EBS data volume..."
    # Check if filesystem exists
    if ! blkid /dev/xvdf; then
        mkfs -t ext4 /dev/xvdf
    fi
    mkdir -p /mnt/rhinometric-data
    mount /dev/xvdf /mnt/rhinometric-data
    echo '/dev/xvdf /mnt/rhinometric-data ext4 defaults,nofail 0 2' >> /etc/fstab
    # Link data directories to mounted volume
    ln -sf /mnt/rhinometric-data /home/ubuntu/rhinometric_data_v2.2
else
    echo "[7/8] No EBS volume detected, using instance storage"
fi

# Set ownership
chown -R ubuntu:ubuntu /home/ubuntu/rhinometric_data_v2.2
chown -R ubuntu:ubuntu /home/ubuntu/rhinometric_backups

# Create marker file
echo "[8/8] Finalizing setup..."
touch /home/ubuntu/.rhinometric-setup-complete
echo "v2.5.0-$(date +%Y%m%d-%H%M%S)" > /home/ubuntu/.rhinometric-version

# System optimizations for Rhinometric
echo "vm.max_map_count=262144" >> /etc/sysctl.conf
echo "fs.file-max=65536" >> /etc/sysctl.conf
sysctl -p

# Docker daemon optimizations
cat > /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF
systemctl restart docker

echo "=========================================="
echo "✅ Rhinometric Test Server Setup Complete"
echo "=========================================="
echo "Docker Version: $(docker --version)"
echo "Docker Compose Version: $(docker-compose --version)"
echo "System Ready: $(date)"
echo ""
echo "Next steps:"
echo "1. Transfer project files to /home/ubuntu/"
echo "2. Create .env file with credentials"
echo "3. Run: docker-compose -f docker-compose-v2.5.0-core.yml up -d"
echo "=========================================="
