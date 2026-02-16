#!/bin/bash
set -e

#═══════════════════════════════════════════════════════════════════════════════
# RHINOMETRIC v2.5.0 - INSTALADOR AUTOMATIZADO ON-PREMISE
# Fecha: 2025-12-30
# Requisitos: Ubuntu 22.04, Docker 24.x+, Docker Compose v2
#═══════════════════════════════════════════════════════════════════════════════

COLOR_RESET="\033[0m"
COLOR_GREEN="\033[0;32m"
COLOR_BLUE="\033[0;34m"
COLOR_YELLOW="\033[1;33m"
COLOR_RED="\033[0;31m"

echo -e "${COLOR_BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   ██████╗ ██╗  ██╗██╗███╗   ██╗ ██████╗ ███╗   ███╗███████╗████████╗ ║
║   ██╔══██╗██║  ██║██║████╗  ██║██╔═══██╗████╗ ████║██╔════╝╚══██╔══╝ ║
║   ██████╔╝███████║██║██╔██╗ ██║██║   ██║██╔████╔██║█████╗     ██║    ║
║   ██╔══██╗██╔══██║██║██║╚██╗██║██║   ██║██║╚██╔╝██║██╔══╝     ██║    ║
║   ██║  ██║██║  ██║██║██║ ╚████║╚██████╔╝██║ ╚═╝ ██║███████╗   ██║    ║
║   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝   ╚═╝    ║
║                                                                       ║
║              Enterprise Observability Platform v2.5.0                ║
║                    Instalación On-Premise                            ║
╚═══════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${COLOR_RESET}"

INSTALL_DIR="${INSTALL_DIR:-/opt/rhinometric}"
COMPOSE_FILE="docker-compose-v2.5.0-core.yml"
REQUIRED_SPACE_GB=150
MIN_RAM_GB=8
MIN_CPU_CORES=4

#═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
#═══════════════════════════════════════════════════════════════════════════════

log_info() {
    echo -e "${COLOR_GREEN}[INFO]${COLOR_RESET} $1"
}

log_warn() {
    echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Este script debe ejecutarse como root o con sudo"
        exit 1
    fi
}

generate_password() {
    openssl rand -base64 24 | tr -d "=+/" | cut -c1-20
}

#═══════════════════════════════════════════════════════════════════════════════
# VALIDACIONES DE SISTEMA
#═══════════════════════════════════════════════════════════════════════════════

check_os() {
    log_info "Verificando sistema operativo..."
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        if [[ "$ID" == "ubuntu" ]]; then
            log_info "✓ Ubuntu ${VERSION_ID} detectado"
        else
            log_warn "Sistema operativo: $PRETTY_NAME (Ubuntu 22.04 recomendado)"
        fi
    else
        log_warn "No se pudo detectar el sistema operativo"
    fi
}

check_resources() {
    log_info "Verificando recursos del sistema..."
    
    # CPU
    CPU_CORES=$(nproc)
    if [[ $CPU_CORES -ge $MIN_CPU_CORES ]]; then
        log_info "✓ CPU: ${CPU_CORES} cores (mínimo ${MIN_CPU_CORES})"
    else
        log_warn "CPU: ${CPU_CORES} cores detectados (recomendado: ${MIN_CPU_CORES}+)"
    fi
    
    # RAM
    TOTAL_RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $TOTAL_RAM_GB -ge $MIN_RAM_GB ]]; then
        log_info "✓ RAM: ${TOTAL_RAM_GB} GB (mínimo ${MIN_RAM_GB} GB)"
    else
        log_error "RAM insuficiente: ${TOTAL_RAM_GB} GB (mínimo: ${MIN_RAM_GB} GB)"
        exit 1
    fi
    
    # Disco
    AVAILABLE_SPACE_GB=$(df -BG "$PWD" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $AVAILABLE_SPACE_GB -ge $REQUIRED_SPACE_GB ]]; then
        log_info "✓ Disco: ${AVAILABLE_SPACE_GB} GB disponibles (mínimo ${REQUIRED_SPACE_GB} GB)"
    else
        log_error "Espacio insuficiente: ${AVAILABLE_SPACE_GB} GB (mínimo: ${REQUIRED_SPACE_GB} GB)"
        exit 1
    fi
}

check_docker() {
    log_info "Verificando Docker..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        echo ""
        echo "Instala Docker con:"
        echo "  curl -fsSL https://get.docker.com | sh"
        echo "  sudo usermod -aG docker \$USER"
        exit 1
    fi
    
    DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    log_info "✓ Docker ${DOCKER_VERSION} instalado"
    
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose v2 no está disponible"
        echo ""
        echo "Docker Compose v2 viene incluido con Docker Engine 20.10.0+"
        echo "Si tienes docker-compose v1, actualiza Docker Engine"
        exit 1
    fi
    
    COMPOSE_VERSION=$(docker compose version --short)
    log_info "✓ Docker Compose ${COMPOSE_VERSION} instalado"
}

check_ports() {
    log_info "Verificando puertos disponibles..."
    
    REQUIRED_PORTS=(3000 3002 5000 5432 6379 8085 8105 9090 9093 3100 16686)
    PORTS_IN_USE=()
    
    for port in "${REQUIRED_PORTS[@]}"; do
        if ss -tuln | grep -q ":${port} "; then
            PORTS_IN_USE+=($port)
        fi
    done
    
    if [[ ${#PORTS_IN_USE[@]} -gt 0 ]]; then
        log_error "Puertos en uso: ${PORTS_IN_USE[*]}"
        echo ""
        echo "Detén los servicios que usan estos puertos o modifica docker-compose.yml"
        exit 1
    fi
    
    log_info "✓ Todos los puertos requeridos están disponibles"
}

#═══════════════════════════════════════════════════════════════════════════════
# GENERACIÓN DE CREDENCIALES
#═══════════════════════════════════════════════════════════════════════════════

generate_credentials() {
    log_info "Generando credenciales seguras..."
    
    POSTGRES_PASSWORD=$(generate_password)
    REDIS_PASSWORD=$(generate_password)
    GRAFANA_PASSWORD=$(generate_password)
    ADMIN_PASSWORD=$(generate_password)
    
    cat > "${INSTALL_DIR}/.env" << EOF
# Credenciales generadas automáticamente - $(date -u +"%Y-%m-%d %H:%M:%S UTC")
# IMPORTANTE: Guardar en password manager

# Database
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Cache
REDIS_PASSWORD=${REDIS_PASSWORD}

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}

# License Validator
ADMIN_PASSWORD=${ADMIN_PASSWORD}

# SMTP (opcional)
SMTP_PASSWORD=
EOF

    chmod 600 "${INSTALL_DIR}/.env"
    log_info "✓ Archivo .env creado con credenciales seguras"
}

#═══════════════════════════════════════════════════════════════════════════════
# INSTALACIÓN
#═══════════════════════════════════════════════════════════════════════════════

create_directories() {
    log_info "Creando estructura de directorios..."
    
    mkdir -p "${INSTALL_DIR}"/{config,grafana/provisioning/dashboards/json,prometheus,alertmanager,loki,data}
    
    log_info "✓ Directorios creados en ${INSTALL_DIR}"
}

copy_files() {
    log_info "Copiando archivos de configuración..."
    
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Archivo ${COMPOSE_FILE} no encontrado"
        exit 1
    fi
    
    cp "$COMPOSE_FILE" "${INSTALL_DIR}/docker-compose.yml"
    log_info "✓ Docker Compose copiado"
    
    # Copiar configs si existen
    if [[ -d "grafana/provisioning/dashboards" ]]; then
        cp -r grafana/provisioning/dashboards/* "${INSTALL_DIR}/grafana/provisioning/dashboards/" 2>/dev/null || true
        log_info "✓ Dashboards de Grafana copiados"
    fi
    
    if [[ -d "config" ]]; then
        cp -r config/* "${INSTALL_DIR}/config/" 2>/dev/null || true
        log_info "✓ Archivos de configuración copiados"
    fi
}

start_stack() {
    log_info "Iniciando stack de Rhinometric..."
    
    cd "${INSTALL_DIR}"
    
    log_info "Descargando imágenes Docker..."
    docker compose pull
    
    log_info "Levantando servicios..."
    docker compose up -d
    
    log_info "Esperando inicialización de servicios (60 segundos)..."
    sleep 60
}

verify_installation() {
    log_info "Verificando instalación..."
    
    cd "${INSTALL_DIR}"
    
    TOTAL_CONTAINERS=$(docker compose ps -q | wc -l)
    HEALTHY_CONTAINERS=$(docker compose ps --format json | jq -r 'select(.Health=="healthy") | .Name' | wc -l)
    
    log_info "Contenedores: ${HEALTHY_CONTAINERS}/${TOTAL_CONTAINERS} saludables"
    
    if [[ $HEALTHY_CONTAINERS -ge 15 ]]; then
        log_info "✓ Stack iniciado correctamente"
        return 0
    else
        log_warn "Algunos contenedores pueden no estar listos aún"
        log_warn "Ejecuta: docker compose ps"
        return 1
    fi
}

#═══════════════════════════════════════════════════════════════════════════════
# INFORMACIÓN POST-INSTALACIÓN
#═══════════════════════════════════════════════════════════════════════════════

show_credentials() {
    log_info "Guardando credenciales en ${INSTALL_DIR}/CREDENCIALES.txt"
    
    cat > "${INSTALL_DIR}/CREDENCIALES.txt" << EOF
═══════════════════════════════════════════════════════════════════════════════
RHINOMETRIC v2.5.0 - CREDENCIALES DE ACCESO
Instalado: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Servidor: $(hostname)
IP: $(hostname -I | awk '{print $1}')
═══════════════════════════════════════════════════════════════════════════════

⚠️  IMPORTANTE: Guardar en password manager y eliminar este archivo

GRAFANA (Dashboards & Visualización)
  URL: http://$(hostname -I | awk '{print $1}'):3000
  Usuario: admin
  Contraseña: ${GRAFANA_PASSWORD}

RHINOMETRIC CONSOLE (Interfaz Principal)
  URL: http://$(hostname -I | awk '{print $1}'):3002
  Usuario: admin
  Contraseña: ${ADMIN_PASSWORD}

POSTGRESQL (Base de Datos)
  Host: localhost:5432
  Base de datos: rhinometric_licenses
  Usuario: rhinometric
  Contraseña: ${POSTGRES_PASSWORD}

REDIS (Cache)
  Host: localhost:6379
  Contraseña: ${REDIS_PASSWORD}

PROMETHEUS (Métricas)
  URL: http://$(hostname -I | awk '{print $1}'):9090
  (Sin autenticación - solo acceso interno)

ALERTMANAGER (Alertas)
  URL: http://$(hostname -I | awk '{print $1}'):9093
  (Sin autenticación - solo acceso interno)

JAEGER (Distributed Tracing)
  URL: http://$(hostname -I | awk '{print $1}'):16686
  (Sin autenticación - solo acceso interno)

═══════════════════════════════════════════════════════════════════════════════
EOF

    chmod 600 "${INSTALL_DIR}/CREDENCIALES.txt"
}

show_completion_message() {
    echo ""
    echo -e "${COLOR_GREEN}"
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════════════════╗
║                   ✓ INSTALACIÓN COMPLETADA                           ║
╚═══════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${COLOR_RESET}"
    
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    echo "Accede a Rhinometric en:"
    echo ""
    echo "  🌐 Console:     http://${SERVER_IP}:3002"
    echo "  📊 Grafana:     http://${SERVER_IP}:3000"
    echo "  📈 Prometheus:  http://${SERVER_IP}:9090"
    echo "  🔔 Alertmgr:    http://${SERVER_IP}:9093"
    echo "  🔍 Jaeger:      http://${SERVER_IP}:16686"
    echo ""
    echo "Credenciales guardadas en:"
    echo "  ${INSTALL_DIR}/CREDENCIALES.txt"
    echo ""
    echo "Comandos útiles:"
    echo "  Ver estado:     cd ${INSTALL_DIR} && docker compose ps"
    echo "  Ver logs:       cd ${INSTALL_DIR} && docker compose logs -f [servicio]"
    echo "  Reiniciar:      cd ${INSTALL_DIR} && docker compose restart"
    echo "  Detener:        cd ${INSTALL_DIR} && docker compose down"
    echo ""
    echo "Documentación completa: ${INSTALL_DIR}/README.md"
    echo ""
}

#═══════════════════════════════════════════════════════════════════════════════
# MAIN
#═══════════════════════════════════════════════════════════════════════════════

main() {
    check_root
    
    log_info "Iniciando instalación de Rhinometric v2.5.0..."
    log_info "Directorio de instalación: ${INSTALL_DIR}"
    echo ""
    
    # Validaciones
    check_os
    check_resources
    check_docker
    check_ports
    echo ""
    
    # Confirmación
    read -p "¿Continuar con la instalación? (s/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        log_info "Instalación cancelada"
        exit 0
    fi
    
    # Instalación
    create_directories
    generate_credentials
    copy_files
    start_stack
    
    # Verificación
    verify_installation
    
    # Post-instalación
    show_credentials
    show_completion_message
    
    log_info "Instalación finalizada exitosamente"
}

# Ejecutar instalación
main "$@"
