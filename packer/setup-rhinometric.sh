#!/bin/bash
# setup-rhinometric.sh - Copia deploy/demo a /opt/rhinometric
# Packer provisioner script

set -euo pipefail

echo "========================================="
echo "Setting up Rhinometric Demo"
echo "========================================="

# Create rhinometric directory
mkdir -p /opt/rhinometric
mkdir -p /var/lib/rhinometric

# Copy deploy/demo files (mounted by Packer)
cp -r /tmp/packer-files/deploy/demo /opt/rhinometric/deploy

# Set permissions
chown -R rhinouser:rhinouser /opt/rhinometric
chmod +x /opt/rhinometric/deploy/demo/scripts/*.sh

# Install systemd service
cp /tmp/packer-files/packer/rhinometric-first-boot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable rhinometric-first-boot.service

# Create VERSION file
echo "2.5.0" > /opt/rhinometric/VERSION

# Setup firewall
ufw --force enable
ufw allow 22/tcp     # SSH
ufw allow 3000/tcp   # Grafana
ufw allow 9090/tcp   # Prometheus
ufw allow 3001/tcp   # Dashboard Builder
ufw allow 443/tcp    # HTTPS (Traefik)
ufw allow 80/tcp     # HTTP redirect

echo "========================================="
echo "Rhinometric setup completed"
echo "========================================="
