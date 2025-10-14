#!/bin/bash

# RhinoMetric SaaS - Quick Multi-Environment Deployment
# ===================================================

set -e

# Configuration
ENVIRONMENTS=("dev" "staging" "prod")
PORTS=("3001" "3002" "3000")

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

# Check if Docker is running
check_docker() {
    if ! docker ps > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    log_success "Docker is running"
}

# Deploy specific environment
deploy_environment() {
    local env=$1
    local port=$2
    
    log_info "Deploying $env environment on port $port..."
    
    cd infrastructure/docker
    
    # Use appropriate compose file and env file
    local compose_file="docker-compose.${env}.yml"
    local env_file=".env.${env}"
    
    if [ ! -f "$compose_file" ]; then
        log_warning "$compose_file not found, using docker-compose.dev.yml"
        compose_file="docker-compose.dev.yml"
    fi
    
    if [ ! -f "$env_file" ]; then
        log_warning "$env_file not found, using .env.development"
        env_file=".env.development"
    fi
    
    log_info "Using compose file: $compose_file"
    log_info "Using env file: $env_file"
    
    # Deploy the environment
    docker-compose --env-file "$env_file" -f "$compose_file" up -d
    
    # Wait for services to start
    log_info "Waiting for $env services to start..."
    sleep 15
    
    # Health check
    log_info "Testing $env environment health..."
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/api/v1/health" > /dev/null 2>&1; then
            log_success "✅ $env environment is healthy on port $port"
            break
        else
            log_warning "Attempt $attempt/$max_attempts: $env not ready yet..."
            sleep 5
            ((attempt++))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "❌ $env environment failed to start properly"
    fi
    
    cd ../..
}

# Stop all environments
stop_all() {
    log_info "Stopping all environments..."
    
    cd infrastructure/docker
    
    for env in "${ENVIRONMENTS[@]}"; do
        log_info "Stopping $env..."
        docker-compose -f "docker-compose.${env}.yml" down 2>/dev/null || true
    done
    
    # Also stop dev environment if running
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    
    log_success "✅ All environments stopped"
    cd ../..
}

# Show status of all environments
show_status() {
    echo ""
    log_info "📊 RhinoMetric SaaS Environment Status:"
    echo "======================================"
    
    for i in "${!ENVIRONMENTS[@]}"; do
        local env=${ENVIRONMENTS[$i]}
        local port=${PORTS[$i]}
        
        printf "  %-12s" "• $env:"
        if curl -s -f "http://localhost:$port/api/v1/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Running${NC} (http://localhost:$port)"
        else
            echo -e "${RED}❌ Stopped${NC}"
        fi
    done
    echo ""
}

# Show help
show_help() {
    echo "RhinoMetric SaaS - Multi-Environment Deployment Tool"
    echo "=================================================="
    echo ""
    echo "Usage: $0 [COMMAND] [ENVIRONMENT]"
    echo ""
    echo "Commands:"
    echo "  deploy [env]   Deploy specific environment (dev|staging|prod) or all"
    echo "  stop           Stop all environments"
    echo "  status         Show status of all environments" 
    echo "  logs [env]     Show logs for specific environment"
    echo "  restart [env]  Restart specific environment"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy dev     # Deploy only development"
    echo "  $0 deploy         # Deploy all environments"
    echo "  $0 status         # Show all environment status"
    echo "  $0 logs prod      # Show production logs"
}

# Main command handler
main() {
    local command=${1:-help}
    local env_target=$2
    
    case "$command" in
        "deploy")
            check_docker
            
            if [ -n "$env_target" ]; then
                # Deploy specific environment
                case "$env_target" in
                    "dev"|"development")
                        deploy_environment "dev" "3001"
                        ;;
                    "staging")
                        deploy_environment "staging" "3002"
                        ;;
                    "prod"|"production")
                        deploy_environment "prod" "3000"
                        ;;
                    *)
                        log_error "Invalid environment: $env_target"
                        log_info "Valid options: dev, staging, prod"
                        exit 1
                        ;;
                esac
            else
                # Deploy all environments
                log_info "🚀 Deploying all environments..."
                for i in "${!ENVIRONMENTS[@]}"; do
                    deploy_environment "${ENVIRONMENTS[$i]}" "${PORTS[$i]}"
                    echo ""
                done
            fi
            
            show_status
            ;;
            
        "stop")
            stop_all
            ;;
            
        "status")
            show_status
            ;;
            
        "logs")
            if [ -z "$env_target" ]; then
                log_error "Please specify environment for logs"
                exit 1
            fi
            
            log_info "Showing logs for $env_target..."
            docker logs -f "rhinometric-api-$env_target" 2>/dev/null || \
            docker logs -f "rhinometric-api" 2>/dev/null || \
            log_error "No container found for $env_target"
            ;;
            
        "restart")
            if [ -n "$env_target" ]; then
                log_info "Restarting $env_target..."
                cd infrastructure/docker
                docker-compose -f "docker-compose.${env_target}.yml" restart 2>/dev/null || \
                docker-compose -f "docker-compose.dev.yml" restart
                cd ../..
            else
                log_error "Please specify environment to restart"
                exit 1
            fi
            ;;
            
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function
main "$@"