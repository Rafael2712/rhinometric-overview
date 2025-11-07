#!/bin/bash
# ============================================
# RhinoMetric Demo - First Boot Setup
# ============================================
# Systemd oneshot service - runs once on first boot

set -e

RHINOMETRIC_HOME="/opt/rhinometric"
LOG_FILE="/var/log/rhinometric-firstboot.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "RhinoMetric Demo Appliance - First Boot"
log "========================================="

# Get VM IP
VM_IP=$(hostname -I | awk '{print $1}')
log "VM IP: $VM_IP"

# Start Docker if not running
if ! systemctl is-active --quiet docker; then
    log "Starting Docker..."
    systemctl start docker
    sleep 5
fi

# Pull images
log "Pulling Docker images..."
cd "$RHINOMETRIC_HOME"
docker compose -f docker-compose-demo.yml pull >> "$LOG_FILE" 2>&1

# Start services
log "Starting RhinoMetric services..."
docker compose -f docker-compose-demo.yml up -d >> "$LOG_FILE" 2>&1

# Wait for healthchecks
log "Waiting for services to become healthy (90s)..."
sleep 90

# Run smoke tests
log "Running smoke tests..."
bash "$RHINOMETRIC_HOME/scripts/smoke-test.sh" >> "$LOG_FILE" 2>&1
SMOKE_EXIT=$?

# Seed anomalies
log "Seeding anomaly data..."
bash "$RHINOMETRIC_HOME/scripts/anomaly-seed.sh" >> "$LOG_FILE" 2>&1 &

# Display banner
log "Generating welcome banner..."
cat > /etc/motd <<EOF

════════════════════════════════════════════════════════════
 ██████╗ ██╗  ██╗██╗███╗   ██╗ ██████╗ ███╗   ███╗███████╗████████╗██████╗ ██╗ ██████╗
 ██╔══██╗██║  ██║██║████╗  ██║██╔═══██╗████╗ ████║██╔════╝╚══██╔══╝██╔══██╗██║██╔════╝
 ██████╔╝███████║██║██╔██╗ ██║██║   ██║██╔████╔██║█████╗     ██║   ██████╔╝██║██║     
 ██╔══██╗██╔══██║██║██║╚██╗██║██║   ██║██║╚██╔╝██║██╔══╝     ██║   ██╔══██╗██║██║     
 ██║  ██║██║  ██║██║██║ ╚████║╚██████╔╝██║ ╚═╝ ██║███████╗   ██║   ██║  ██║██║╚██████╗
 ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝ ╚═════╝
                                                                                        
          v2.5.0 Demo Appliance - Ready for immediate use
════════════════════════════════════════════════════════════

🌐 Access Grafana:    https://$VM_IP
👤 Username:          admin
🔑 Password:          rhinometric_demo

📊 Services Status:
$(docker ps --format "   ✓ {{.Names}}" | grep rhinometric)

📁 Location:          /opt/rhinometric
📝 Logs:              /var/log/rhinometric-firstboot.log
💾 Backup:            sudo bash /opt/rhinometric/scripts/backup.sh
🔄 Update:            sudo bash /opt/rhinometric/scripts/update.sh
📋 Support Bundle:    sudo bash /opt/rhinometric/scripts/support-bundle.sh

🔥 Anomaly detection is ACTIVE - dashboards will show data in 1-3 minutes

════════════════════════════════════════════════════════════
EOF

log "First boot complete!"
if [ $SMOKE_EXIT -eq 0 ]; then
    log "✅ DEMO READY - All smoke tests passed"
else
    log "⚠️  Some smoke tests failed - check logs"
fi

log "Access: https://$VM_IP (admin/rhinometric_demo)"

# Disable this service after first run
systemctl disable rhinometric-firstboot.service

exit 0
