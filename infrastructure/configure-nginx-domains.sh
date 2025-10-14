#!/bin/bash

# Nginx Configuration for rhinometric.com Multi-Environment Setup
# ==============================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
DOMAIN="rhinometric.com"
NGINX_SITES="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"
EMAIL="admin@rhinometric.com"  # Change this to your email

# Check if running with sudo
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run with sudo"
        exit 1
    fi
}

# Install Nginx and Certbot
install_nginx() {
    log_info "Installing Nginx and Certbot..."
    
    dnf update -y
    dnf install -y nginx certbot python3-certbot-nginx
    
    # Enable and start services
    systemctl enable nginx
    systemctl start nginx
    
    # Create sites-available and sites-enabled directories
    mkdir -p "$NGINX_SITES"
    mkdir -p "$NGINX_ENABLED"
    
    log_success "✅ Nginx and Certbot installed"
}

# Configure Nginx main config
configure_main_nginx() {
    log_info "Configuring main Nginx configuration..."
    
    # Backup original config
    cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
    
    # Create new nginx.conf with sites-enabled include
    cat > /etc/nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Include sites-enabled configurations
    include /etc/nginx/sites-enabled/*;
}
EOF

    log_success "✅ Main Nginx configuration updated"
}

# Create API configurations
create_api_configs() {
    log_info "Creating API server configurations..."
    
    # Production API
    cat > "$NGINX_SITES/rhinometric-api-prod" << EOF
server {
    listen 80;
    server_name api.$DOMAIN;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # API routes
    location /api/ {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
        
        # Handle preflight requests
        if (\$request_method = 'OPTIONS') {
            return 204;
        }
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://localhost:3000/api/v1/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Default route
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    # Staging API
    cat > "$NGINX_SITES/rhinometric-api-staging" << EOF
server {
    listen 80;
    server_name staging-api.$DOMAIN;
    
    # Security headers  
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Environment "staging";
    
    location / {
        proxy_pass http://localhost:3002;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS headers for staging
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
        
        if (\$request_method = 'OPTIONS') {
            return 204;
        }
    }
}
EOF

    # Development API
    cat > "$NGINX_SITES/rhinometric-api-dev" << EOF
server {
    listen 80;
    server_name dev-api.$DOMAIN;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-Environment "development";
    
    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS headers for development
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
        
        if (\$request_method = 'OPTIONS') {
            return 204;
        }
    }
}
EOF

    log_success "✅ API configurations created"
}

# Enable sites
enable_sites() {
    log_info "Enabling sites..."
    
    ln -sf "$NGINX_SITES/rhinometric-api-prod" "$NGINX_ENABLED/"
    ln -sf "$NGINX_SITES/rhinometric-api-staging" "$NGINX_ENABLED/"
    ln -sf "$NGINX_SITES/rhinometric-api-dev" "$NGINX_ENABLED/"
    
    log_success "✅ Sites enabled"
}

# Test Nginx configuration
test_nginx() {
    log_info "Testing Nginx configuration..."
    
    nginx -t
    if [ $? -eq 0 ]; then
        log_success "✅ Nginx configuration is valid"
        systemctl reload nginx
        log_success "✅ Nginx reloaded"
    else
        log_error "❌ Nginx configuration has errors"
        exit 1
    fi
}

# Configure firewall
configure_firewall() {
    log_info "Configuring firewall for HTTP/HTTPS..."
    
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
    
    log_success "✅ Firewall configured"
}

# Install SSL certificates
install_ssl() {
    log_info "Installing SSL certificates with Let's Encrypt..."
    
    log_warning "⚠️  Make sure DNS records are pointing to this server before proceeding!"
    read -p "Press Enter to continue or Ctrl+C to cancel..."
    
    certbot --nginx \
        -d api.$DOMAIN \
        -d staging-api.$DOMAIN \
        -d dev-api.$DOMAIN \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --redirect
    
    if [ $? -eq 0 ]; then
        log_success "✅ SSL certificates installed successfully"
        
        # Setup auto-renewal
        crontab -l > /tmp/crontab.tmp || true
        echo "0 12 * * * /usr/bin/certbot renew --quiet" >> /tmp/crontab.tmp
        crontab /tmp/crontab.tmp
        rm /tmp/crontab.tmp
        
        log_success "✅ Auto-renewal configured"
    else
        log_warning "⚠️  SSL certificate installation failed. You can retry later with:"
        log_info "sudo certbot --nginx -d api.$DOMAIN -d staging-api.$DOMAIN -d dev-api.$DOMAIN"
    fi
}

# Show status
show_status() {
    log_info "📊 Configuration Status:"
    echo "========================"
    echo "• Nginx Status: $(systemctl is-active nginx)"
    echo "• Sites Available: $(ls -1 $NGINX_SITES | wc -l) configs"
    echo "• Sites Enabled: $(ls -1 $NGINX_ENABLED | wc -l) configs"
    echo ""
    echo "🌐 Configured Domains:"
    echo "• Production API:  https://api.$DOMAIN"
    echo "• Staging API:     https://staging-api.$DOMAIN"  
    echo "• Development API: https://dev-api.$DOMAIN"
    echo ""
    echo "🧪 Test Commands:"
    echo "curl https://api.$DOMAIN/api/v1/health"
    echo "curl https://staging-api.$DOMAIN/api/v1/health"
    echo "curl https://dev-api.$DOMAIN/api/v1/health"
}

# Main function
main() {
    log_info "🚀 Starting Nginx configuration for rhinometric.com..."
    
    check_root
    install_nginx
    configure_main_nginx
    create_api_configs
    enable_sites
    test_nginx
    configure_firewall
    
    echo ""
    read -p "Do you want to install SSL certificates now? (y/N): " install_ssl_now
    if [[ $install_ssl_now =~ ^[Yy]$ ]]; then
        install_ssl
    else
        log_info "SSL can be installed later with: sudo certbot --nginx -d api.$DOMAIN -d staging-api.$DOMAIN -d dev-api.$DOMAIN"
    fi
    
    echo ""
    show_status
    
    log_success "🎉 Nginx configuration completed!"
}

# Run main function
main "$@"