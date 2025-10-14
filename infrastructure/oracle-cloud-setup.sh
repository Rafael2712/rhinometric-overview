#!/bin/bash

# Oracle Cloud VM Configuration Script
# ===================================

set -e

echo "☁️  Oracle Cloud - RhinoMetric SaaS Setup"
echo "========================================"

# Configuration
OCI_USER="opc"  # Default Oracle Cloud user
PROJECT_DIR="/opt/rhinometric-saas"
BACKUP_DIR="/opt/backups"
LOG_FILE="/var/log/rhinometric-setup.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root or with sudo
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        log_success "✅ Running with root privileges"
    else
        log_error "❌ This script requires root privileges. Run with sudo."
        exit 1
    fi
}

# Install required packages for Oracle Linux
install_dependencies() {
    log "Installing required packages..."
    
    # Update system
    dnf update -y
    
    # Install Docker
    dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    dnf install -y docker-ce docker-ce-cli containerd.io
    
    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Install Node.js (using NodeSource repository)
    curl -fsSL https://rpm.nodesource.com/setup_16.x | bash -
    dnf install -y nodejs
    
    # Install other utilities
    dnf install -y git curl wget nano vim firewalld
    
    # Start and enable services
    systemctl start docker
    systemctl enable docker
    systemctl start firewalld
    systemctl enable firewalld
    
    # Add opc user to docker group
    usermod -aG docker opc
    
    log_success "✅ Dependencies installed successfully"
}

# Configure Oracle Cloud networking
setup_networking() {
    log "Configuring Oracle Cloud networking..."
    
    # Configure firewall for our applications
    firewall-cmd --permanent --add-port=3000/tcp  # Production
    firewall-cmd --permanent --add-port=3001/tcp  # Development  
    firewall-cmd --permanent --add-port=3002/tcp  # Staging
    firewall-cmd --permanent --add-port=80/tcp    # HTTP
    firewall-cmd --permanent --add-port=443/tcp   # HTTPS
    firewall-cmd --permanent --add-port=22/tcp    # SSH
    
    # Reload firewall
    firewall-cmd --reload
    
    log_success "✅ Firewall configured for multi-environment access"
}

# Create project structure
setup_project_structure() {
    log "Setting up project structure..."
    
    # Create main directories
    mkdir -p "$PROJECT_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "/var/log/rhinometric"
    
    # Set permissions
    chown -R opc:opc "$PROJECT_DIR"
    chown -R opc:opc "$BACKUP_DIR"
    chown -R opc:opc "/var/log/rhinometric"
    
    log_success "✅ Project structure created"
}

# Clone or update the repository
setup_repository() {
    log "Setting up repository..."
    
    cd "$PROJECT_DIR"
    
    # If directory exists and has .git, pull latest changes
    if [ -d ".git" ]; then
        log "Repository exists, pulling latest changes..."
        sudo -u opc git pull origin main
    else
        log "Cloning repository..."
        # Note: You'll need to replace this with your actual repo URL
        sudo -u opc git clone https://github.com/Rafael2712/mi-proyecto.git .
    fi
    
    log_success "✅ Repository setup completed"
}

# Create systemd services for each environment
create_systemd_services() {
    log "Creating systemd services..."
    
    # Development service
    cat > /etc/systemd/system/rhinometric-dev.service << 'EOF'
[Unit]
Description=RhinoMetric SaaS - Development Environment
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/rhinometric-saas/infrastructure/docker
ExecStart=/usr/local/bin/docker-compose -f docker-compose.dev.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.dev.yml down
User=opc
Group=opc

[Install]
WantedBy=multi-user.target
EOF

    # Staging service  
    cat > /etc/systemd/system/rhinometric-staging.service << 'EOF'
[Unit]
Description=RhinoMetric SaaS - Staging Environment
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/rhinometric-saas/infrastructure/docker
ExecStart=/usr/local/bin/docker-compose -f docker-compose.staging.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.staging.yml down
User=opc
Group=opc

[Install]
WantedBy=multi-user.target
EOF

    # Production service
    cat > /etc/systemd/system/rhinometric-prod.service << 'EOF'
[Unit]
Description=RhinoMetric SaaS - Production Environment
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/rhinometric-saas/infrastructure/docker
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
User=opc
Group=opc

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload
    
    log_success "✅ Systemd services created"
}

# Create management script
create_management_script() {
    log "Creating management script..."
    
    cat > /usr/local/bin/rhinometric << 'EOF'
#!/bin/bash

# RhinoMetric SaaS Management Script
# ================================

case "$1" in
    start)
        echo "🚀 Starting RhinoMetric SaaS environments..."
        systemctl start rhinometric-dev rhinometric-staging rhinometric-prod
        echo "✅ All environments started"
        ;;
    stop)
        echo "🛑 Stopping RhinoMetric SaaS environments..."
        systemctl stop rhinometric-dev rhinometric-staging rhinometric-prod
        echo "✅ All environments stopped"
        ;;
    restart)
        echo "🔄 Restarting RhinoMetric SaaS environments..."
        systemctl restart rhinometric-dev rhinometric-staging rhinometric-prod
        echo "✅ All environments restarted"
        ;;
    status)
        echo "📊 RhinoMetric SaaS Status:"
        echo "========================="
        systemctl is-active rhinometric-dev && echo "  • Development: ✅ Running" || echo "  • Development: ❌ Stopped"
        systemctl is-active rhinometric-staging && echo "  • Staging: ✅ Running" || echo "  • Staging: ❌ Stopped"
        systemctl is-active rhinometric-prod && echo "  • Production: ✅ Running" || echo "  • Production: ❌ Stopped"
        ;;
    logs)
        if [ -z "$2" ]; then
            echo "Usage: rhinometric logs [dev|staging|prod]"
            exit 1
        fi
        docker logs -f "rhinometric-api-$2"
        ;;
    *)
        echo "RhinoMetric SaaS Management Tool"
        echo "Usage: $0 {start|stop|restart|status|logs [env]}"
        exit 1
        ;;
esac
EOF

    chmod +x /usr/local/bin/rhinometric
    
    log_success "✅ Management script created at /usr/local/bin/rhinometric"
}

# Main setup function
main() {
    log "Starting Oracle Cloud setup for RhinoMetric SaaS..."
    
    check_permissions
    install_dependencies
    setup_networking
    setup_project_structure
    setup_repository
    create_systemd_services
    create_management_script
    
    log_success "🎉 Oracle Cloud setup completed successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo "============="
    echo "1. Switch to opc user: sudo -u opc -i"
    echo "2. Navigate to project: cd $PROJECT_DIR"  
    echo "3. Run deployment: ./infrastructure/deploy-multi-env.sh"
    echo "4. Manage services: rhinometric {start|stop|restart|status}"
    echo ""
    echo "🌐 Access URLs (replace <YOUR-IP> with actual IP):"
    echo "  • Production:  http://<YOUR-IP>:3000"
    echo "  • Staging:     http://<YOUR-IP>:3002"
    echo "  • Development: http://<YOUR-IP>:3001"
}

# Run setup
main "$@"