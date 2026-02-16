#!/bin/bash
# ==============================================================================
# RHINOMETRIC TRIAL v2.0.0 - REBUILD & DEPLOYMENT SCRIPT
# ==============================================================================
# Este script prepara y despliega Rhinometric Trial v2.0.0 en Ubuntu WSL2
# con versiones fijas, healthchecks completos y bind mounts persistentes.
#
# Autor: Sistema Automatizado
# Fecha: 24 de Octubre, 2025
# ==============================================================================

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables globales
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${HOME}/rhinometric_data"
LOG_FILE="${PROJECT_DIR}/rebuild_$(date +%Y%m%d_%H%M%S).log"
VALIDATION_REPORT="${PROJECT_DIR}/validation_report.txt"

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        error "Comando '$1' no encontrado. Por favor instálalo primero."
    fi
}

# ==============================================================================
# PASO 1: VERIFICACIÓN DEL SISTEMA
# ==============================================================================

verify_system() {
    log "=== PASO 1: Verificación del Sistema ==="
    
    # Verificar Ubuntu
    if [ ! -f /etc/lsb-release ]; then
        error "Este script requiere Ubuntu"
    fi
    
    source /etc/lsb-release
    info "Sistema: $DISTRIB_DESCRIPTION"
    
    # Verificar WSL2
    if grep -qi microsoft /proc/version; then
        info "Ejecutando en WSL2 ✓"
    else
        warn "No detectado WSL2, continuando de todos modos..."
    fi
    
    # Verificar Docker
    check_command docker
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | tr -d ',')
    info "Docker version: $DOCKER_VERSION"
    
    # Verificar Docker Compose
    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version | awk '{print $4}')
        info "Docker Compose version: $COMPOSE_VERSION"
    else
        error "Docker Compose no encontrado"
    fi
    
    # Verificar que Docker esté corriendo
    if ! docker info &> /dev/null; then
        error "Docker daemon no está corriendo. Inicia Docker primero."
    fi
    
    log "Verificación del sistema completada ✓"
}

# ==============================================================================
# PASO 2: VERIFICACIÓN DE ARCHIVOS
# ==============================================================================

verify_files() {
    log "=== PASO 2: Verificación de Archivos ==="
    
    local required_files=(
        "docker-compose-rebuilt.yml"
        ".env"
        "licensing/Dockerfile"
        "licensing/license_server.py"
        "license-dashboard/Dockerfile"
        "license-dashboard/app.py"
        "config/prometheus-saas.yml"
        "config/loki-saas.yml"
        "config/tempo-saas.yml"
        "config/alertmanager-saas.yml"
        "config/promtail-config.yml"
        "config/nginx-trial.conf"
        "config/blackbox.yml"
        "config/rules/alerts.yml"
        "grafana/provisioning/datasources/datasources.yml"
        "grafana/provisioning/dashboards/dashboards.yml"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$PROJECT_DIR/$file" ] && [ ! -d "$PROJECT_DIR/$file" ]; then
            missing_files+=("$file")
            warn "Archivo faltante: $file"
        else
            info "✓ $file"
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        error "Faltan ${#missing_files[@]} archivos críticos. Revisa el log."
    fi
    
    log "Verificación de archivos completada ✓"
}

# ==============================================================================
# PASO 3: PREPARACIÓN DE DIRECTORIOS
# ==============================================================================

prepare_directories() {
    log "=== PASO 3: Preparación de Directorios de Datos ==="
    
    # Crear directorio raíz de datos
    if [ ! -d "$DATA_DIR" ]; then
        info "Creando directorio de datos: $DATA_DIR"
        mkdir -p "$DATA_DIR"
    fi
    
    # Crear subdirectorios para cada servicio
    local data_dirs=(
        "postgres"
        "redis"
        "prometheus"
        "grafana"
        "loki"
        "tempo"
        "license"
        "alertmanager"
    )
    
    for dir in "${data_dirs[@]}"; do
        local full_path="$DATA_DIR/$dir"
        if [ ! -d "$full_path" ]; then
            info "Creando: $full_path"
            mkdir -p "$full_path"
        fi
        
        # Establecer permisos apropiados
        chmod 755 "$full_path"
    done
    
    # Permisos especiales para Loki (user 10001)
    chown 10001:10001 "$DATA_DIR/loki" 2>/dev/null || warn "No se pudo cambiar owner de loki (ejecuta como root si es necesario)"
    
    # Permisos especiales para Grafana (user 472)
    chown 472:472 "$DATA_DIR/grafana" 2>/dev/null || warn "No se pudo cambiar owner de grafana (ejecuta como root si es necesario)"
    
    # Permisos especiales para Prometheus (user 65534 = nobody)
    chown 65534:65534 "$DATA_DIR/prometheus" 2>/dev/null || warn "No se pudo cambiar owner de prometheus (ejecuta como root si es necesario)"
    
    log "Directorios de datos preparados ✓"
    info "Ubicación: $DATA_DIR"
}

# ==============================================================================
# PASO 4: VALIDACIÓN DE .ENV
# ==============================================================================

validate_env() {
    log "=== PASO 4: Validación de .env ==="
    
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        error "Archivo .env no encontrado"
    fi
    
    # Cargar .env
    set -a
    source "$PROJECT_DIR/.env"
    set +a
    
    # Verificar variables críticas
    if [ -z "${POSTGRES_PASSWORD:-}" ]; then
        error "POSTGRES_PASSWORD no definido en .env"
    fi
    
    if [ -z "${JWT_SECRET:-}" ]; then
        warn "JWT_SECRET no definido, usando default (NO SEGURO)"
    fi
    
    info "Variables de entorno cargadas ✓"
    log "Validación de .env completada ✓"
}

# ==============================================================================
# PASO 5: LIMPIEZA DE CONTENEDORES ANTERIORES
# ==============================================================================

cleanup_containers() {
    log "=== PASO 5: Limpieza de Contenedores Anteriores ==="
    
    info "Deteniendo contenedores existentes..."
    docker compose -f "$PROJECT_DIR/docker-compose-rebuilt.yml" down -v 2>/dev/null || true
    
    # Opcional: limpieza agresiva
    read -p "¿Deseas hacer limpieza completa de Docker (images, networks, build cache)? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        warn "Ejecutando limpieza completa de Docker..."
        docker system prune -a -f --volumes
        log "Limpieza completa ejecutada ✓"
    else
        info "Omitiendo limpieza completa"
    fi
}

# ==============================================================================
# PASO 6: CONSTRUCCIÓN DE IMÁGENES
# ==============================================================================

build_images() {
    log "=== PASO 6: Construcción de Imágenes ==="
    
    info "Construyendo imágenes custom (license-server, license-dashboard)..."
    
    cd "$PROJECT_DIR"
    
    docker compose -f docker-compose-rebuilt.yml build --no-cache --progress=plain 2>&1 | tee -a "$LOG_FILE"
    
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        error "Falló la construcción de imágenes. Revisa el log."
    fi
    
    log "Imágenes construidas exitosamente ✓"
}

# ==============================================================================
# PASO 7: DESPLIEGUE DE SERVICIOS
# ==============================================================================

deploy_services() {
    log "=== PASO 7: Despliegue de Servicios ==="
    
    info "Iniciando stack Rhinometric Trial v2.0.0..."
    
    cd "$PROJECT_DIR"
    
    docker compose -f docker-compose-rebuilt.yml up -d 2>&1 | tee -a "$LOG_FILE"
    
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        error "Falló el despliegue. Revisa el log."
    fi
    
    log "Servicios desplegados ✓"
}

# ==============================================================================
# PASO 8: ESPERA Y VALIDACIÓN DE HEALTHCHECKS
# ==============================================================================

wait_for_healthy() {
    log "=== PASO 8: Esperando Healthchecks ==="
    
    local max_wait=300  # 5 minutos
    local elapsed=0
    local check_interval=10
    
    info "Esperando a que los 16 contenedores estén 'healthy'..."
    info "Máximo tiempo de espera: ${max_wait}s"
    
    while [ $elapsed -lt $max_wait ]; do
        local healthy_count=$(docker ps --filter "name=rhinometric-" --format "{{.Status}}" | grep -c "healthy" || true)
        local total_count=$(docker ps --filter "name=rhinometric-" --format "{{.Names}}" | wc -l)
        
        info "Progreso: $healthy_count/$total_count contenedores healthy (${elapsed}s)"
        
        if [ "$healthy_count" -eq 16 ]; then
            log "Todos los contenedores están healthy ✓"
            return 0
        fi
        
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    warn "Timeout alcanzado. No todos los contenedores están healthy."
    return 1
}

# ==============================================================================
# PASO 9: VALIDACIÓN FUNCIONAL
# ==============================================================================

validate_services() {
    log "=== PASO 9: Validación Funcional ==="
    
    # Crear reporte de validación
    {
        echo "=========================================="
        echo "RHINOMETRIC TRIAL v2.0.0 - VALIDATION REPORT"
        echo "=========================================="
        echo "Fecha: $(date)"
        echo "Hostname: $(hostname)"
        echo ""
        echo "ESTADO DE CONTENEDORES:"
        echo "=========================================="
        docker ps --filter "name=rhinometric-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -n 20
        echo ""
        echo "HEALTHCHECK DETALLADO:"
        echo "=========================================="
    } > "$VALIDATION_REPORT"
    
    # Verificar cada servicio
    local services=(
        "license-server:5000:/health"
        "prometheus:9090:/-/healthy"
        "grafana:3000:/api/health"
        "loki:3100:/ready"
        "tempo:3200:/ready"
        "alertmanager:9093:/-/healthy"
        "license-dashboard:8080:/health"
    )
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r service port endpoint <<< "$service_info"
        
        info "Validando $service..."
        
        if curl -sf "http://localhost:$port$endpoint" > /dev/null 2>&1; then
            echo "✓ $service: HEALTHY (http://localhost:$port$endpoint)" | tee -a "$VALIDATION_REPORT"
        else
            echo "✗ $service: UNHEALTHY (http://localhost:$port$endpoint)" | tee -a "$VALIDATION_REPORT"
        fi
    done
    
    # Verificar modo oscuro de Grafana
    info "Verificando modo oscuro de Grafana..."
    
    GRAFANA_THEME=$(docker exec rhinometric-grafana env | grep GF_USERS_DEFAULT_THEME | cut -d= -f2)
    
    {
        echo ""
        echo "GRAFANA - MODO OSCURO:"
        echo "=========================================="
        echo "GF_USERS_DEFAULT_THEME: $GRAFANA_THEME"
    } >> "$VALIDATION_REPORT"
    
    if [ "$GRAFANA_THEME" = "dark" ]; then
        log "Modo oscuro de Grafana: HABILITADO ✓"
    else
        warn "Modo oscuro de Grafana: NO configurado correctamente"
    fi
    
    # Verificar persistencia de datos
    {
        echo ""
        echo "PERSISTENCIA DE DATOS:"
        echo "=========================================="
        du -sh "$DATA_DIR"/* 2>/dev/null | sort -rh
    } >> "$VALIDATION_REPORT"
    
    # Logs de servicios críticos (últimas 20 líneas)
    {
        echo ""
        echo "LOGS RECIENTES (license-server):"
        echo "=========================================="
        docker logs rhinometric-license-server --tail 20 2>&1
        echo ""
        echo "LOGS RECIENTES (grafana):"
        echo "=========================================="
        docker logs rhinometric-grafana --tail 20 2>&1
    } >> "$VALIDATION_REPORT"
    
    log "Reporte de validación generado: $VALIDATION_REPORT"
}

# ==============================================================================
# PASO 10: RESUMEN FINAL
# ==============================================================================

print_summary() {
    log "=== PASO 10: Resumen Final ==="
    
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✅ RHINOMETRIC TRIAL v2.0.0 RECONSTRUIDO"
    echo -e "==========================================${NC}"
    echo ""
    echo -e "${BLUE}Servicios Desplegados:${NC}"
    docker ps --filter "name=rhinometric-" --format "  • {{.Names}} ({{.Status}})" | head -n 20
    echo ""
    echo -e "${BLUE}Acceso a Servicios:${NC}"
    echo "  • Grafana:         http://localhost:3000 (admin / admin_trial_2024)"
    echo "  • Prometheus:      http://localhost:9090"
    echo "  • Loki:            http://localhost:3100"
    echo "  • Tempo:           http://localhost:3200"
    echo "  • Alertmanager:    http://localhost:9093"
    echo "  • License Dashboard: http://localhost:8080"
    echo "  • Nginx:           http://localhost:80"
    echo ""
    echo -e "${BLUE}Archivos Generados:${NC}"
    echo "  • Log completo:    $LOG_FILE"
    echo "  • Reporte validación: $VALIDATION_REPORT"
    echo ""
    echo -e "${BLUE}Datos Persistentes:${NC}"
    echo "  • Ubicación:       $DATA_DIR"
    echo "  • Tamaño total:    $(du -sh "$DATA_DIR" 2>/dev/null | cut -f1)"
    echo ""
    echo -e "${YELLOW}Comandos Útiles:${NC}"
    echo "  • Ver logs:        docker compose -f docker-compose-rebuilt.yml logs -f [servicio]"
    echo "  • Detener:         docker compose -f docker-compose-rebuilt.yml down"
    echo "  • Reiniciar:       docker compose -f docker-compose-rebuilt.yml restart [servicio]"
    echo "  • Estado:          docker compose -f docker-compose-rebuilt.yml ps"
    echo ""
    echo -e "${GREEN}Reconstrucción completada exitosamente ✓${NC}"
    echo ""
}

# ==============================================================================
# MAIN SCRIPT
# ==============================================================================

main() {
    clear
    
    echo ""
    echo "========================================================================"
    echo "  RHINOMETRIC TRIAL v2.0.0 - REBUILD & DEPLOYMENT"
    echo "========================================================================"
    echo "  Este script reconstruirá completamente el stack con:"
    echo "    • Versiones fijas (sin 'latest')"
    echo "    • Healthchecks en 16/16 servicios"
    echo "    • Bind mounts persistentes en ~/rhinometric_data"
    echo "========================================================================"
    echo ""
    
    read -p "¿Deseas continuar? [Y/n]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        info "Operación cancelada por el usuario"
        exit 0
    fi
    
    # Ejecutar pasos
    verify_system
    verify_files
    prepare_directories
    validate_env
    cleanup_containers
    build_images
    deploy_services
    wait_for_healthy
    validate_services
    print_summary
    
    exit 0
}

# Ejecutar script
main "$@"
