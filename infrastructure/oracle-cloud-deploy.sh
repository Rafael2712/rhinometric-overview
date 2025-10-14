#!/bin/bash
# =============================================================================
# Oracle Cloud CI/CD Deployment Script
# =============================================================================
# Este script es llamado desde GitHub Actions para deployar a Oracle Cloud
# Autor: Rhinometric Development Team
# Versión: 1.0.0
# =============================================================================

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# =============================================================================
# VALIDACIÓN DE PARÁMETROS
# =============================================================================

if [ $# -lt 2 ]; then
    error "Uso: $0 <environment> <image_tag> [rollback]"
    error "Environments: development, staging, production"
    error "Ejemplo: $0 production ghcr.io/rafael2712/mi-proyecto:v1.0.0"
fi

ENVIRONMENT=$1
IMAGE_TAG=$2
ROLLBACK=${3:-false}

# Validar environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    error "Environment debe ser: development, staging, o production"
fi

log "🚀 Iniciando deployment de Rhinometric"
info "Environment: ${ENVIRONMENT}"
info "Image: ${IMAGE_TAG}"
info "Rollback: ${ROLLBACK}"

# =============================================================================
# CONFIGURACIÓN POR AMBIENTE
# =============================================================================

case $ENVIRONMENT in
    "development")
        APP_PORT=3001
        DB_PORT=5433
        REDIS_PORT=6380
        DOMAIN="dev-api.rhinometric.com"
        NGINX_CONFIG="dev-api.rhinometric.com.conf"
        COMPOSE_FILE="docker-compose.dev.yml"
        ;;
    "staging")
        APP_PORT=3002
        DB_PORT=5434
        REDIS_PORT=6381
        DOMAIN="staging-api.rhinometric.com"
        NGINX_CONFIG="staging-api.rhinometric.com.conf"
        COMPOSE_FILE="docker-compose.staging.yml"
        ;;
    "production")
        APP_PORT=3000
        DB_PORT=5432
        REDIS_PORT=6379
        DOMAIN="api.rhinometric.com"
        NGINX_CONFIG="api.rhinometric.com.conf"
        COMPOSE_FILE="docker-compose.prod.yml"
        ;;
esac

log "📋 Configuración del ambiente:"
info "Puerto aplicación: ${APP_PORT}"
info "Puerto base de datos: ${DB_PORT}"
info "Puerto Redis: ${REDIS_PORT}"
info "Dominio: ${DOMAIN}"

# =============================================================================
# VERIFICACIONES PREVIAS
# =============================================================================

log "🔍 Ejecutando verificaciones previas..."

# Verificar que estamos en Oracle Cloud
if [ ! -f /etc/oracle-cloud-agent/oracle-cloud-agent.conf ]; then
    warn "No se detectó Oracle Cloud Agent, continuando..."
fi

# Verificar Docker
if ! command -v docker &> /dev/null; then
    error "Docker no está instalado"
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose no está instalado"
fi

# Verificar nginx
if ! command -v nginx &> /dev/null; then
    error "Nginx no está instalado"
fi

# Verificar que el usuario puede usar Docker
if ! docker info &> /dev/null; then
    error "El usuario actual no puede ejecutar Docker"
fi

log "✅ Verificaciones previas completadas"

# =============================================================================
# BACKUP PRE-DEPLOYMENT
# =============================================================================

if [ "$ROLLBACK" = "false" ] && [ "$ENVIRONMENT" = "production" ]; then
    log "💾 Creando backup pre-deployment..."
    
    BACKUP_DIR="/opt/rhinometric/backups"
    BACKUP_FILE="rhinometric-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup de configuración actual
    if [ -d "/opt/rhinometric/current" ]; then
        tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" \
            -C "/opt/rhinometric" \
            current/ || warn "Error creando backup de configuración"
    fi
    
    # Backup de base de datos
    if docker ps | grep -q "rhinometric-postgres-${ENVIRONMENT}"; then
        DB_BACKUP_FILE="db-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S).sql"
        docker exec rhinometric-postgres-${ENVIRONMENT} \
            pg_dump -U postgres rhinometric_${ENVIRONMENT} \
            > "${BACKUP_DIR}/${DB_BACKUP_FILE}" || warn "Error creando backup de DB"
        info "Backup de DB creado: ${DB_BACKUP_FILE}"
    fi
    
    info "Backup creado: ${BACKUP_FILE}"
fi

# =============================================================================
# PREPARACIÓN DE DIRECTORIOS
# =============================================================================

log "📁 Preparando estructura de directorios..."

DEPLOY_DIR="/opt/rhinometric"
ENV_DIR="${DEPLOY_DIR}/environments/${ENVIRONMENT}"
CURRENT_DIR="${DEPLOY_DIR}/current"

# Crear directorios necesarios
sudo mkdir -p "$DEPLOY_DIR"/{environments,backups,logs,ssl}
sudo mkdir -p "$ENV_DIR"/{data,logs}
sudo mkdir -p "/var/log/rhinometric"

# Ajustar permisos
sudo chown -R opc:opc "$DEPLOY_DIR"
sudo chmod -R 755 "$DEPLOY_DIR"

log "✅ Directorios preparados"

# =============================================================================
# CONFIGURACIÓN DE VARIABLES DE AMBIENTE
# =============================================================================

log "🔧 Configurando variables de ambiente..."

# Crear archivo .env para el ambiente
cat > "${ENV_DIR}/.env" << EOF
# Rhinometric ${ENVIRONMENT^^} Environment Configuration
# Generated: $(date)

# Application
NODE_ENV=${ENVIRONMENT}
PORT=${APP_PORT}
API_VERSION=v1

# Database
DB_HOST=rhinometric-postgres-${ENVIRONMENT}
DB_PORT=5432
DB_NAME=rhinometric_${ENVIRONMENT}
DB_USER=${DB_USER:-rhinometric_user}
DB_PASSWORD=${DB_PASSWORD:-default_password}
DB_CONNECTION_TIMEOUT=30000

# Redis
REDIS_HOST=rhinometric-redis-${ENVIRONMENT}
REDIS_PORT=6379
REDIS_URL=redis://rhinometric-redis-${ENVIRONMENT}:6379

# Security
JWT_SECRET=${JWT_SECRET:-default-jwt-secret-change-in-production}
JWT_EXPIRES_IN=24h
API_ENCRYPTION_KEY=${API_ENCRYPTION_KEY:-default-encryption-key}

# CORS
CORS_ORIGIN=https://${DOMAIN}
ALLOWED_ORIGINS=https://${DOMAIN},https://www.rhinometric.com

# Logs
LOG_LEVEL=${LOG_LEVEL:-info}
LOG_FILE=/app/logs/rhinometric-${ENVIRONMENT}.log

# Health Check
HEALTH_CHECK_PATH=/api/v1/health

# Feature Flags
ENABLE_SWAGGER=${ENABLE_SWAGGER:-false}
ENABLE_METRICS=${ENABLE_METRICS:-true}
ENABLE_RATE_LIMITING=${ENABLE_RATE_LIMITING:-true}

# Docker Configuration
IMAGE_TAG=${IMAGE_TAG}
CONTAINER_NAME=rhinometric-app-${ENVIRONMENT}
NETWORK_NAME=rhinometric-${ENVIRONMENT}
EOF

log "✅ Variables de ambiente configuradas"

# =============================================================================
# DOCKER COMPOSE CONFIGURATION
# =============================================================================

log "🐳 Configurando Docker Compose..."

# Crear docker-compose.yml específico para el ambiente
cat > "${ENV_DIR}/docker-compose.yml" << EOF
version: '3.8'

networks:
  rhinometric-${ENVIRONMENT}:
    name: rhinometric-${ENVIRONMENT}
    driver: bridge

volumes:
  rhinometric-postgres-data-${ENVIRONMENT}:
    name: rhinometric-postgres-data-${ENVIRONMENT}
  rhinometric-redis-data-${ENVIRONMENT}:
    name: rhinometric-redis-data-${ENVIRONMENT}
  rhinometric-app-logs-${ENVIRONMENT}:
    name: rhinometric-app-logs-${ENVIRONMENT}

services:
  postgres:
    image: postgres:13-alpine
    container_name: rhinometric-postgres-${ENVIRONMENT}
    restart: unless-stopped
    environment:
      POSTGRES_DB: rhinometric_${ENVIRONMENT}
      POSTGRES_USER: \${DB_USER}
      POSTGRES_PASSWORD: \${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=C --lc-ctype=C"
    volumes:
      - rhinometric-postgres-data-${ENVIRONMENT}:/var/lib/postgresql/data
      - ${ENV_DIR}/logs:/var/log/postgresql
    ports:
      - "${DB_PORT}:5432"
    networks:
      - rhinometric-${ENVIRONMENT}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \${DB_USER} -d rhinometric_${ENVIRONMENT}"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  redis:
    image: redis:6-alpine
    container_name: rhinometric-redis-${ENVIRONMENT}
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass "\${REDIS_PASSWORD:-}"
    volumes:
      - rhinometric-redis-data-${ENVIRONMENT}:/data
      - ${ENV_DIR}/logs:/var/log/redis
    ports:
      - "${REDIS_PORT}:6379"
    networks:
      - rhinometric-${ENVIRONMENT}
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  app:
    image: ${IMAGE_TAG}
    container_name: rhinometric-app-${ENVIRONMENT}
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "${APP_PORT}:3000"
    volumes:
      - rhinometric-app-logs-${ENVIRONMENT}:/app/logs
      - ${ENV_DIR}/logs:/var/log/rhinometric
    networks:
      - rhinometric-${ENVIRONMENT}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

EOF

log "✅ Docker Compose configurado"

# =============================================================================
# NGINX CONFIGURATION
# =============================================================================

log "🌐 Configurando Nginx..."

# Crear configuración de Nginx para el dominio
sudo tee "/etc/nginx/sites-available/${NGINX_CONFIG}" > /dev/null << EOF
# Rhinometric ${ENVIRONMENT^^} - ${DOMAIN}
# Generated: $(date)

upstream rhinometric_${ENVIRONMENT} {
    server 127.0.0.1:${APP_PORT} max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN};
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Rate Limiting
    limit_req_zone \$binary_remote_addr zone=${ENVIRONMENT}_api:10m rate=100r/m;
    limit_req zone=${ENVIRONMENT}_api burst=20 nodelay;
    
    # Client Settings
    client_max_body_size 10M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    # Proxy Settings
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    proxy_buffering off;
    proxy_request_buffering off;
    
    # API Routes
    location /api/ {
        proxy_pass http://rhinometric_${ENVIRONMENT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # CORS Headers (backup, app should handle this)
        add_header Access-Control-Allow-Origin "https://www.rhinometric.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
        
        # Handle OPTIONS requests
        if (\$request_method = 'OPTIONS') {
            return 204;
        }
    }
    
    # Health Check (no auth required)
    location /api/v1/health {
        proxy_pass http://rhinometric_${ENVIRONMENT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        access_log off;
    }
    
    # Deny access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # Logs
    access_log /var/log/nginx/${DOMAIN}.access.log;
    error_log /var/log/nginx/${DOMAIN}.error.log;
}
EOF

# Habilitar el sitio
sudo ln -sf "/etc/nginx/sites-available/${NGINX_CONFIG}" "/etc/nginx/sites-enabled/"

# Verificar configuración de Nginx
if ! sudo nginx -t; then
    error "Error en la configuración de Nginx"
fi

log "✅ Nginx configurado"

# =============================================================================
# SSL CERTIFICATE SETUP
# =============================================================================

log "🔒 Configurando certificados SSL..."

# Verificar si el certificado existe
if [ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
    info "Obteniendo certificado SSL para ${DOMAIN}..."
    
    # Detener nginx temporalmente para obtener el certificado
    sudo systemctl stop nginx
    
    # Obtener certificado con certbot
    sudo certbot certonly \
        --standalone \
        --email admin@rhinometric.com \
        --agree-tos \
        --no-eff-email \
        -d "$DOMAIN" || error "Error obteniendo certificado SSL"
    
    # Reiniciar nginx
    sudo systemctl start nginx
    
    info "✅ Certificado SSL obtenido"
else
    info "Certificado SSL ya existe para ${DOMAIN}"
fi

# Configurar renovación automática
if ! sudo crontab -l | grep -q "certbot renew"; then
    (sudo crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | sudo crontab -
    info "Renovación automática de SSL configurada"
fi

# =============================================================================
# DEPLOYMENT EXECUTION
# =============================================================================

log "🚀 Ejecutando deployment..."

cd "$ENV_DIR"

if [ "$ROLLBACK" = "true" ]; then
    warn "🔄 Ejecutando rollback..."
    
    # Detener servicios actuales
    docker-compose down --remove-orphans
    
    # Buscar último backup disponible
    LAST_BACKUP=$(ls -t /opt/rhinometric/backups/rhinometric-${ENVIRONMENT}-*.tar.gz 2>/dev/null | head -1)
    
    if [ -n "$LAST_BACKUP" ]; then
        info "Restaurando desde: $(basename "$LAST_BACKUP")"
        tar -xzf "$LAST_BACKUP" -C /opt/rhinometric/
    else
        warn "No se encontró backup para rollback"
    fi
else
    # Pull de la imagen
    log "📥 Descargando imagen: ${IMAGE_TAG}"
    docker pull "$IMAGE_TAG" || error "Error descargando imagen"
    
    # Detener versión anterior (gracefully)
    if docker ps | grep -q "rhinometric-app-${ENVIRONMENT}"; then
        info "Deteniendo versión anterior..."
        docker-compose down --timeout 60
    fi
    
    # Limpiar recursos no utilizados
    docker system prune -f
    
    # Iniciar nuevos servicios
    log "🎬 Iniciando servicios..."
    docker-compose up -d --remove-orphans
fi

# =============================================================================
# DATABASE MIGRATIONS
# =============================================================================

if [ "$ROLLBACK" = "false" ]; then
    log "🗄️ Ejecutando migraciones de base de datos..."
    
    # Esperar a que la base de datos esté lista
    info "Esperando disponibilidad de la base de datos..."
    for i in {1..30}; do
        if docker exec "rhinometric-postgres-${ENVIRONMENT}" pg_isready -U "${DB_USER:-rhinometric_user}" -d "rhinometric_${ENVIRONMENT}"; then
            break
        fi
        sleep 5
        if [ $i -eq 30 ]; then
            error "Timeout esperando la base de datos"
        fi
    done
    
    # Ejecutar migraciones
    info "Ejecutando migraciones..."
    docker exec "rhinometric-app-${ENVIRONMENT}" npm run migrate || warn "Error en migraciones"
    
    # Ejecutar seeds solo en development
    if [ "$ENVIRONMENT" = "development" ]; then
        info "Ejecutando seeds de desarrollo..."
        docker exec "rhinometric-app-${ENVIRONMENT}" npm run seed || warn "Error en seeds"
    fi
    
    log "✅ Migraciones completadas"
fi

# =============================================================================
# HEALTH CHECKS
# =============================================================================

log "🔍 Ejecutando health checks..."

# Esperar a que el servicio esté disponible
info "Esperando disponibilidad del servicio..."
for i in {1..30}; do
    if curl -sf "http://localhost:${APP_PORT}/api/v1/health" > /dev/null; then
        break
    fi
    sleep 10
    if [ $i -eq 30 ]; then
        error "Timeout - servicio no disponible"
    fi
done

# Health check completo
HEALTH_RESPONSE=$(curl -s "http://localhost:${APP_PORT}/api/v1/health")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    log "✅ Health check local exitoso"
else
    error "Health check local falló: $HEALTH_RESPONSE"
fi

# Health check HTTPS (si no es development)
if [ "$ENVIRONMENT" != "development" ]; then
    info "Verificando HTTPS..."
    if curl -sf "https://${DOMAIN}/api/v1/health" > /dev/null; then
        log "✅ Health check HTTPS exitoso"
    else
        warn "Health check HTTPS falló - puede tomar unos minutos en propagarse"
    fi
fi

# =============================================================================
# NGINX RELOAD
# =============================================================================

log "🔄 Recargando Nginx..."

# Verificar configuración antes de recargar
if sudo nginx -t; then
    sudo systemctl reload nginx
    log "✅ Nginx recargado"
else
    error "Error en configuración de Nginx"
fi

# =============================================================================
# MONITORING SETUP
# =============================================================================

log "📊 Configurando monitoring..."

# Crear script de monitoring
cat > "${ENV_DIR}/monitor.sh" << 'EOF'
#!/bin/bash
# Monitoring script para Rhinometric

ENVIRONMENT=$1
LOG_FILE="/var/log/rhinometric/monitor-${ENVIRONMENT}.log"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Check Docker containers
    APP_STATUS=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "rhinometric-app-${ENVIRONMENT}" | awk '{print $2}' || echo "Down")
    DB_STATUS=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "rhinometric-postgres-${ENVIRONMENT}" | awk '{print $2}' || echo "Down")
    REDIS_STATUS=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "rhinometric-redis-${ENVIRONMENT}" | awk '{print $2}' || echo "Down")
    
    # Check health endpoint
    HEALTH_STATUS="Down"
    if curl -sf "http://localhost:${APP_PORT}/api/v1/health" > /dev/null; then
        HEALTH_STATUS="Up"
    fi
    
    # Log status
    echo "${TIMESTAMP} - App: ${APP_STATUS}, DB: ${DB_STATUS}, Redis: ${REDIS_STATUS}, Health: ${HEALTH_STATUS}" >> "$LOG_FILE"
    
    sleep 300 # Check every 5 minutes
done
EOF

chmod +x "${ENV_DIR}/monitor.sh"

# Crear servicio systemd para monitoring
sudo tee "/etc/systemd/system/rhinometric-monitor-${ENVIRONMENT}.service" > /dev/null << EOF
[Unit]
Description=Rhinometric ${ENVIRONMENT} Monitor
After=docker.service

[Service]
Type=simple
User=opc
ExecStart=${ENV_DIR}/monitor.sh ${ENVIRONMENT}
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "rhinometric-monitor-${ENVIRONMENT}.service"
sudo systemctl start "rhinometric-monitor-${ENVIRONMENT}.service"

log "✅ Monitoring configurado"

# =============================================================================
# FIREWALL CONFIGURATION
# =============================================================================

log "🔥 Configurando firewall..."

# Permitir puertos necesarios
sudo ufw allow 80/tcp comment "HTTP"
sudo ufw allow 443/tcp comment "HTTPS"
sudo ufw allow 22/tcp comment "SSH"

# Permitir puerto específico del ambiente (solo desde localhost)
sudo ufw allow from 127.0.0.1 to any port "${APP_PORT}" comment "Rhinometric ${ENVIRONMENT}"

log "✅ Firewall configurado"

# =============================================================================
# CLEANUP
# =============================================================================

log "🧹 Limpieza post-deployment..."

# Limpiar imágenes Docker no utilizadas
docker image prune -f

# Limpiar logs antiguos (más de 30 días)
find /var/log/rhinometric -name "*.log" -type f -mtime +30 -delete 2>/dev/null || true

# Limpiar backups antiguos (más de 7 días)
find /opt/rhinometric/backups -name "*.tar.gz" -type f -mtime +7 -delete 2>/dev/null || true

log "✅ Limpieza completada"

# =============================================================================
# DEPLOYMENT SUMMARY
# =============================================================================

log "📋 Resumen del deployment:"
info "Ambiente: ${ENVIRONMENT}"
info "Imagen: ${IMAGE_TAG}"
info "Dominio: ${DOMAIN}"
info "Puerto aplicación: ${APP_PORT}"
info "Estado: $(docker ps --format 'table {{.Names}}\t{{.Status}}' | grep "rhinometric-app-${ENVIRONMENT}")"

# Mostrar logs recientes
info "📜 Logs recientes de la aplicación:"
docker logs --tail 20 "rhinometric-app-${ENVIRONMENT}" || warn "No se pudieron obtener logs"

# URLs de verificación
log "🔗 URLs de verificación:"
info "Health Check Local: http://localhost:${APP_PORT}/api/v1/health"
if [ "$ENVIRONMENT" != "development" ]; then
    info "Health Check HTTPS: https://${DOMAIN}/api/v1/health"
    info "API Base URL: https://${DOMAIN}/api/v1"
fi

log "🎉 ¡Deployment de ${ENVIRONMENT} completado exitosamente!"

# =============================================================================
# SAVE DEPLOYMENT INFO
# =============================================================================

# Guardar información del deployment
cat > "${ENV_DIR}/deployment-info.json" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "environment": "${ENVIRONMENT}",
    "image_tag": "${IMAGE_TAG}",
    "domain": "${DOMAIN}",
    "app_port": ${APP_PORT},
    "git_commit": "${GITHUB_SHA:-unknown}",
    "deployed_by": "${GITHUB_ACTOR:-$(whoami)}",
    "deployment_id": "${GITHUB_RUN_ID:-$(date +%s)}",
    "rollback": ${ROLLBACK}
}
EOF

log "✅ Información del deployment guardada"

exit 0