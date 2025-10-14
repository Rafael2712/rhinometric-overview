#!/bin/bash

# RhinoMetric SaaS - Oracle Cloud Multi-Environment Deployment
# ===========================================================

set -e

echo "🚀 RhinoMetric SaaS - Multi-Environment Deployment"
echo "=================================================="

# Environment configuration
ENVIRONMENTS=("dev" "staging" "prod")
PORTS=("3001" "3002" "3000")
DB_NAMES=("rhinometric_dev" "rhinometric_staging" "rhinometric_prod")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're running on Oracle Cloud
check_oracle_cloud() {
    log_info "Checking if we're running on Oracle Cloud..."
    
    # Check for Oracle Cloud metadata service
    if curl -s -m 5 http://169.254.169.254/opc/v1/instance/ > /dev/null 2>&1; then
        log_success "✅ Running on Oracle Cloud Infrastructure"
        return 0
    else
        log_warning "⚠️  Not running on Oracle Cloud (local development)"
        return 1
    fi
}

# Deploy environment
deploy_environment() {
    local env=$1
    local port=$2
    local db_name=$3
    
    log_info "Deploying $env environment on port $port..."
    
    # Create environment-specific directory if it doesn't exist
    mkdir -p "/opt/rhinometric-$env"
    
    # Copy project files
    cp -r ../backend "/opt/rhinometric-$env/"
    cp -r ../infrastructure/docker "/opt/rhinometric-$env/"
    
    # Create environment-specific .env file
    cat > "/opt/rhinometric-$env/.env" << EOF
# Environment: $env
NODE_ENV=$env
API_PORT=$port
BUILD_TARGET=$env

# Database Configuration
DB_NAME=$db_name
DB_USER=postgres
DB_PASSWORD=saas_${env}_password_$(date +%s)

# Redis Configuration  
REDIS_PASSWORD=${env}_redis_password

# JWT Configuration
JWT_SECRET=${env}_jwt_secret_$(openssl rand -hex 32)

# CORS Configuration
ALLOWED_ORIGINS=https://$env-api.rhinometric.com,https://rhinometric.com

# Security
RATE_LIMIT_MAX=100
RATE_LIMIT_WINDOW=900000
EOF

    # Create docker-compose override for this environment
    cat > "/opt/rhinometric-$env/docker-compose.override.yml" << EOF
version: '3.8'

services:
  rhinometric-api:
    container_name: rhinometric-api-$env
    ports:
      - "$port:$port"
    environment:
      - NODE_ENV=$env
      - PORT=$port
    networks:
      - rhinometric-$env-network

  postgres:
    container_name: rhinometric-postgres-$env
    environment:
      - POSTGRES_DB=$db_name
    volumes:
      - rhinometric-$env-postgres-data:/var/lib/postgresql/data/pgdata
    networks:
      - rhinometric-$env-network

  redis:
    container_name: rhinometric-redis-$env
    volumes:
      - rhinometric-$env-redis-data:/data
    networks:
      - rhinometric-$env-network

volumes:
  rhinometric-$env-postgres-data:
  rhinometric-$env-redis-data:
  rhinometric-$env-api-logs:

networks:
  rhinometric-$env-network:
    name: rhinometric-$env-network
    driver: bridge
EOF

    # Deploy the environment
    cd "/opt/rhinometric-$env"
    
    log_info "Starting $env environment..."
    docker-compose -f docker/docker-compose.dev.yml -f docker-compose.override.yml up -d
    
    # Wait for services to be ready
    log_info "Waiting for $env services to be ready..."
    sleep 30
    
    # Run migrations
    log_info "Running database migrations for $env..."
    docker exec "rhinometric-api-$env" npm run migrate || log_warning "Migrations might have failed for $env"
    
    # Health check
    log_info "Performing health check for $env..."
    if curl -s "http://localhost:$port/api/v1/health" > /dev/null; then
        log_success "✅ $env environment is healthy on port $port"
    else
        log_error "❌ $env environment health check failed"
    fi
    
    cd - > /dev/null
}

# Configure firewall rules for Oracle Cloud
configure_firewall() {
    log_info "Configuring firewall rules for multi-environment access..."
    
    # Open ports for each environment
    for port in "${PORTS[@]}"; do
        sudo firewall-cmd --permanent --add-port=$port/tcp
        log_info "Opened port $port"
    done
    
    # Reload firewall
    sudo firewall-cmd --reload
    log_success "✅ Firewall rules configured"
}

# Main deployment process
main() {
    log_info "Starting multi-environment deployment..."
    
    # Check Oracle Cloud
    if check_oracle_cloud; then
        configure_firewall
    fi
    
    # Deploy each environment
    for i in "${!ENVIRONMENTS[@]}"; do
        env=${ENVIRONMENTS[$i]}
        port=${PORTS[$i]}
        db_name=${DB_NAMES[$i]}
        
        log_info "Deploying environment: $env"
        deploy_environment "$env" "$port" "$db_name"
        
        echo ""
    done
    
    # Summary
    echo ""
    log_success "🎉 Multi-environment deployment completed!"
    echo ""
    echo "📊 Environment Summary:"
    echo "======================"
    for i in "${!ENVIRONMENTS[@]}"; do
        env=${ENVIRONMENTS[$i]}
        port=${PORTS[$i]}
        echo "  • $env: http://$(hostname -I | awk '{print $1}'):$port"
    done
    echo ""
    echo "🔧 Management Commands:"
    echo "====================="
    echo "  • View logs: docker logs rhinometric-api-{dev|staging|prod}"
    echo "  • Restart: docker restart rhinometric-api-{dev|staging|prod}"
    echo "  • Stop all: docker stop \$(docker ps -q --filter name=rhinometric)"
    echo ""
}

# Run main function
main "$@"