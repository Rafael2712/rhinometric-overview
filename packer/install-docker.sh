#!/bin/bash
# install-docker.sh - Instala Docker y Docker Compose en Ubuntu 22.04
# Packer provisioner script para Rhinometric Demo OVA

set -euo pipefail

echo "========================================="
echo "Installing Docker and Docker Compose"
echo "========================================="

# Update packages
apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable and start Docker
systemctl enable docker
systemctl start docker

# Add rhinouser to docker group
usermod -aG docker rhinouser

# Verify installation
docker --version
docker compose version

echo "========================================="
echo "Docker installation completed"
echo "========================================="
