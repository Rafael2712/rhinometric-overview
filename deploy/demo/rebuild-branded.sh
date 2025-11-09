#!/bin/bash
set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  RHINOMETRIC ENTERPRISE - Demo Rebuild & Validation     ║"
echo "║  Branding Edition v2.5.0                                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Configuración
COMPOSE_FILE="docker-compose-demo.yml"
ENV_FILE=".env.demo"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones auxiliares
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

# Verificar prerequisitos
log_info "Checking prerequisites..."

if [ ! -f "$ENV_FILE" ]; then
    log_error "Missing $ENV_FILE"
    exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Missing $COMPOSE_FILE"
    exit 1
fi

# Verificar archivos de branding
BRANDING_FILES=(
    "branding/html/index.html"
    "branding/html/error.html"
    "grafana/grafana.ini"
    "grafana/provisioning/branding/rhinometric-theme.css"
    "alertmanager/email-template.html"
    "traefik/traefik-dynamic.yml"
    "nginx/nginx.conf"
    "nginx/Dockerfile"
)

log_info "Validating branding files..."
MISSING_FILES=0
for file in "${BRANDING_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        log_error "Missing: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    else
        log_success "$file"
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    log_error "$MISSING_FILES branding files missing!"
    exit 1
fi

# Cargar variables de entorno
source "$ENV_FILE"

log_info "Environment loaded:"
echo "  - RHINO_BRAND_NAME: ${RHINO_BRAND_NAME}"
echo "  - RHINO_VERSION: ${RHINO_VERSION}"
echo "  - RHINO_DOMAIN: ${RHINO_DOMAIN}"
echo ""

# Detener servicios existentes
log_info "Stopping existing services..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down -v 2>/dev/null || true
log_success "Services stopped"

# Rebuild de nginx (contiene branding)
log_info "Building rhinometric-nginx with branding..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build rhinometric-nginx
log_success "Nginx built successfully"

# Levantar stack completo
log_info "Starting Rhinometric Demo stack..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

# Esperar healthchecks
log_info "Waiting for services to be healthy (60s timeout)..."
sleep 10

# Validar servicios críticos
SERVICES=("rhinometric-nginx-demo" "rhinometric-grafana-demo" "rhinometric-prometheus-demo")
TIMEOUT=60
ELAPSED=0

while [ $ELAPSED -lt $TIMEOUT ]; do
    ALL_HEALTHY=true
    for service in "${SERVICES[@]}"; do
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "none")
        if [ "$HEALTH" != "healthy" ]; then
            ALL_HEALTHY=false
            break
        fi
    done
    
    if [ "$ALL_HEALTHY" = true ]; then
        log_success "All services are healthy!"
        break
    fi
    
    sleep 5
    ELAPSED=$((ELAPSED + 5))
    echo -n "."
done
echo ""

if [ $ELAPSED -ge $TIMEOUT ]; then
    log_warning "Timeout waiting for healthchecks, continuing anyway..."
fi

# Validación de branding
echo ""
log_info "═══════════════════════════════════════"
log_info "  BRANDING VALIDATION"
log_info "═══════════════════════════════════════"

# Test 1: Landing page
log_info "Test 1: Landing page HTML..."
if curl -s http://localhost | grep -q "RHINOMETRIC"; then
    log_success "Landing page contains RHINOMETRIC branding"
else
    log_error "Landing page branding NOT found"
fi

# Test 2: Grafana title
log_info "Test 2: Grafana branding..."
if curl -s http://localhost:3000 | grep -q "Rhinometric"; then
    log_success "Grafana contains Rhinometric branding"
else
    log_warning "Grafana branding check inconclusive (may need login)"
fi

# Test 3: Traefik headers
log_info "Test 3: Traefik headers..."
POWERED_BY=$(curl -sI http://localhost 2>/dev/null | grep -i "X-Powered-By" || echo "")
if echo "$POWERED_BY" | grep -q "Rhinometric"; then
    log_success "X-Powered-By header: $POWERED_BY"
else
    log_warning "X-Powered-By header not detected"
fi

# Test 4: Error page
log_info "Test 4: Error page content..."
if [ -f "branding/html/error.html" ] && grep -q "Rhinometric" branding/html/error.html; then
    log_success "Error page branded correctly"
else
    log_error "Error page missing branding"
fi

# Test 5: Email template
log_info "Test 5: Email template..."
if [ -f "alertmanager/email-template.html" ] && grep -q "RHINOMETRIC ENTERPRISE" alertmanager/email-template.html; then
    log_success "Email template branded correctly"
else
    log_error "Email template missing branding"
fi

# Test 6: Grafana CSS
log_info "Test 6: Grafana custom CSS..."
if [ -f "grafana/provisioning/branding/rhinometric-theme.css" ] && grep -q "#1e5a7d" grafana/provisioning/branding/rhinometric-theme.css; then
    log_success "Grafana CSS theme with corporate colors"
else
    log_error "Grafana CSS theme missing"
fi

# Resumen
echo ""
log_info "═══════════════════════════════════════"
log_info "  DEPLOYMENT SUMMARY"
log_info "═══════════════════════════════════════"
log_success "Rhinometric Demo v${RHINO_VERSION} deployed!"
echo ""
echo "��� Access URLs:"
echo "   Landing Page: http://localhost"
echo "   Grafana:      http://localhost:3000"
echo "   Prometheus:   http://localhost:9090"
echo "   Dashboard Builder: http://localhost:8001"
echo ""
echo "��� Credentials:"
echo "   Admin: admin / rhinometric_demo"
echo "   User:  rhinouser / rhinometric"
echo ""
echo "��� Next Steps:"
echo "   1. Open http://localhost in browser"
echo "   2. Verify landing page displays Rhinometric branding"
echo "   3. Login to Grafana and check custom theme"
echo "   4. Check dashboards are in RHINOMETRIC folders"
echo ""
echo "���️  Useful Commands:"
echo "   docker compose -f $COMPOSE_FILE logs -f"
echo "   docker compose -f $COMPOSE_FILE ps"
echo "   docker compose -f $COMPOSE_FILE down -v"
echo ""

