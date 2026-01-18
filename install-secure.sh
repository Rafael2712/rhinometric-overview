#!/usr/bin/env bash

################################################################################
#                                                                              #
#                     RHINOMETRIC v2.3.0 - SECURE INSTALLER                   #
#                                                                              #
#  Instalador seguro con validación de licencia, verificación de dependencias,#
#  chequeo de puertos, TUI interactivo, logs y rollback automático            #
#                                                                              #
#  Compatible: Linux / macOS / Windows (WSL2)                                  #
#                                                                              #
################################################################################

set -e  # Exit on error (disabled during checks)
set -u  # Exit on undefined variable

# ============================================================================
# CONFIGURACIÓN Y VARIABLES GLOBALES
# ============================================================================

VERSION="2.3.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/install-secure-$(date +%Y%m%d-%H%M%S).log"
BACKUP_DIR="${SCRIPT_DIR}/backup-$(date +%Y%m%d-%H%M%S)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose-v2.2.0.yml"
LICENSE_FILE="${SCRIPT_DIR}/licenses/cliente.lic"
VALIDATOR_SCRIPT="${SCRIPT_DIR}/validate_license.py"

# Puertos críticos a verificar
CRITICAL_PORTS=(3000 9090 3100 5432 9093 8080 8081 9080 9115)

# Estado de instalación
INSTALL_STATE="NOT_STARTED"
ROLLBACK_NEEDED=false

# ============================================================================
# COLORES Y FORMATO (ANSI)
# ============================================================================

if [[ -t 1 ]] && command -v tput &>/dev/null; then
    COLOR_RESET=$(tput sgr0)
    COLOR_BOLD=$(tput bold)
    COLOR_RED=$(tput setaf 1)
    COLOR_GREEN=$(tput setaf 2)
    COLOR_YELLOW=$(tput setaf 3)
    COLOR_BLUE=$(tput setaf 4)
    COLOR_MAGENTA=$(tput setaf 5)
    COLOR_CYAN=$(tput setaf 6)
    COLOR_WHITE=$(tput setaf 7)
else
    COLOR_RESET=""
    COLOR_BOLD=""
    COLOR_RED=""
    COLOR_GREEN=""
    COLOR_YELLOW=""
    COLOR_BLUE=""
    COLOR_MAGENTA=""
    COLOR_CYAN=""
    COLOR_WHITE=""
fi

# ============================================================================
# FUNCIONES DE UTILIDAD Y LOGS
# ============================================================================

# Función para logging con timestamp
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" >> "${LOG_FILE}"
    
    case "${level}" in
        INFO)
            echo "${COLOR_BLUE}[INFO]${COLOR_RESET} ${message}"
            ;;
        SUCCESS)
            echo "${COLOR_GREEN}[OK]${COLOR_RESET} ${message}"
            ;;
        WARNING)
            echo "${COLOR_YELLOW}[WARN]${COLOR_RESET} ${message}"
            ;;
        ERROR)
            echo "${COLOR_RED}[ERROR]${COLOR_RESET} ${message}"
            ;;
        STEP)
            echo "${COLOR_CYAN}[===>]${COLOR_RESET} ${COLOR_BOLD}${message}${COLOR_RESET}"
            ;;
    esac
}

# Función para imprimir encabezado
print_header() {
    local title="$1"
    echo ""
    echo "${COLOR_MAGENTA}${COLOR_BOLD}╔════════════════════════════════════════════════════════════════════════╗${COLOR_RESET}"
    printf "${COLOR_MAGENTA}${COLOR_BOLD}║%-72s║${COLOR_RESET}\n" " ${title}"
    echo "${COLOR_MAGENTA}${COLOR_BOLD}╚════════════════════════════════════════════════════════════════════════╝${COLOR_RESET}"
    echo ""
}

# Función para imprimir separador
print_separator() {
    echo "${COLOR_CYAN}────────────────────────────────────────────────────────────────────────${COLOR_RESET}"
}

# Progress bar
progress_bar() {
    local current=$1
    local total=$2
    local description=$3
    local percentage=$((current * 100 / total))
    local filled=$((percentage / 2))
    local empty=$((50 - filled))
    
    printf "\r${COLOR_CYAN}["
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "] ${percentage}%% - ${description}${COLOR_RESET}"
    
    if [[ $current -eq $total ]]; then
        echo ""
    fi
}

# Confirmar acción
confirm() {
    local prompt="$1"
    local default="${2:-n}"
    
    if [[ "${default}" == "y" ]]; then
        prompt="${prompt} [Y/n]: "
    else
        prompt="${prompt} [y/N]: "
    fi
    
    while true; do
        read -r -p "${COLOR_YELLOW}${prompt}${COLOR_RESET}" response
        response=${response:-${default}}
        
        case "${response}" in
            [Yy]|[Yy][Ee][Ss])
                return 0
                ;;
            [Nn]|[Nn][Oo])
                return 1
                ;;
            *)
                echo "${COLOR_RED}Por favor responda 'y' o 'n'${COLOR_RESET}"
                ;;
        esac
    done
}

# ============================================================================
# DETECCIÓN DE SISTEMA OPERATIVO
# ============================================================================

detect_os() {
    print_header "DETECCIÓN DE SISTEMA OPERATIVO"
    
    log INFO "Detectando sistema operativo..."
    
    local os_type=""
    local os_version=""
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        os_type="Linux"
        if [[ -f /etc/os-release ]]; then
            os_version=$(grep PRETTY_NAME /etc/os-release | cut -d'"' -f2)
        else
            os_version=$(uname -r)
        fi
        
        # Verificar si es WSL
        if grep -qi microsoft /proc/version 2>/dev/null; then
            os_type="Linux (WSL2)"
        fi
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        os_type="macOS"
        os_version=$(sw_vers -productVersion)
        
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        os_type="Windows (Git Bash/Cygwin)"
        os_version=$(cmd //c ver 2>/dev/null | grep -o 'Version.*' || echo "Unknown")
        
    else
        os_type="Unknown"
        os_version="$OSTYPE"
    fi
    
    log SUCCESS "Sistema detectado: ${os_type} ${os_version}"
    echo "${COLOR_GREEN}✓${COLOR_RESET} Sistema: ${COLOR_BOLD}${os_type}${COLOR_RESET}"
    echo "${COLOR_GREEN}✓${COLOR_RESET} Versión: ${os_version}"
    
    # Verificar compatibilidad
    if [[ "${os_type}" == "Unknown" ]]; then
        log ERROR "Sistema operativo no soportado: ${OSTYPE}"
        echo "${COLOR_RED}✗${COLOR_RESET} Sistema operativo no soportado oficialmente"
        if ! confirm "¿Desea continuar de todas formas?" "n"; then
            exit 1
        fi
    fi
    
    print_separator
}

# ============================================================================
# VALIDACIÓN DE LICENCIA
# ============================================================================

validate_license() {
    print_header "VALIDACIÓN DE LICENCIA"
    
    log INFO "Verificando licencia de RHINOMETRIC..."
    
    # Verificar existencia de archivos
    if [[ ! -f "${LICENSE_FILE}" ]]; then
        log ERROR "Archivo de licencia no encontrado: ${LICENSE_FILE}"
        echo "${COLOR_RED}✗${COLOR_RESET} No se encontró el archivo de licencia"
        echo "   Ubicación esperada: ${LICENSE_FILE}"
        echo ""
        echo "${COLOR_YELLOW}Solución:${COLOR_RESET}"
        echo "  1. Obtenga su HWID ejecutando: ./get-hwid.sh"
        echo "  2. Envíe el HWID a RHINOMETRIC para obtener su licencia"
        echo "  3. Coloque el archivo cliente.lic en: ${SCRIPT_DIR}/licenses/"
        echo ""
        return 1
    fi
    
    if [[ ! -f "${VALIDATOR_SCRIPT}" ]]; then
        log ERROR "Script validador no encontrado: ${VALIDATOR_SCRIPT}"
        echo "${COLOR_RED}✗${COLOR_RESET} Script de validación no encontrado"
        return 1
    fi
    
    log SUCCESS "Archivos de licencia encontrados"
    echo "${COLOR_GREEN}✓${COLOR_RESET} Archivo de licencia encontrado"
    
    # Ejecutar validador
    log INFO "Ejecutando validador de licencia..."
    
    local validation_output
    local validation_exitcode
    
    set +e  # Deshabilitar exit on error temporalmente
    validation_output=$(python3 "${VALIDATOR_SCRIPT}" 2>&1)
    validation_exitcode=$?
    set -e
    
    if [[ $validation_exitcode -eq 0 ]]; then
        log SUCCESS "Licencia válida"
        echo "${COLOR_GREEN}✓${COLOR_RESET} Licencia verificada correctamente"
        
        # Extraer información de la licencia
        echo ""
        echo "${COLOR_CYAN}Información de la licencia:${COLOR_RESET}"
        echo "${validation_output}" | grep -E "Cliente|Tipo|Expira|Días restantes|Features" | while IFS= read -r line; do
            echo "  ${line}"
        done
        
        # Verificar días restantes
        local days_remaining=$(echo "${validation_output}" | grep -oP "Días restantes: \K\d+" || echo "0")
        
        if [[ ${days_remaining} -lt 7 ]]; then
            echo ""
            echo "${COLOR_YELLOW}⚠️  ADVERTENCIA: Su licencia expira en ${days_remaining} días${COLOR_RESET}"
            echo "   Contacte a RHINOMETRIC para renovar: licenses@rhinometric.com"
        fi
        
        print_separator
        return 0
        
    else
        log ERROR "Validación de licencia falló"
        echo "${COLOR_RED}✗${COLOR_RESET} Licencia inválida o expirada"
        echo ""
        echo "${COLOR_RED}Detalles del error:${COLOR_RESET}"
        echo "${validation_output}" | sed 's/^/  /'
        echo ""
        echo "${COLOR_YELLOW}Contacte a RHINOMETRIC:${COLOR_RESET}"
        echo "  Email: licenses@rhinometric.com"
        echo "  Web: https://rhinometric.com"
        echo ""
        
        print_separator
        return 1
    fi
}

# ============================================================================
# VERIFICACIÓN DE DEPENDENCIAS
# ============================================================================

check_dependencies() {
    print_header "VERIFICACIÓN DE DEPENDENCIAS"
    
    local all_ok=true
    
    # Docker Engine
    log INFO "Verificando Docker Engine..."
    if command -v docker &>/dev/null; then
        local docker_version=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
        log SUCCESS "Docker encontrado: ${docker_version}"
        echo "${COLOR_GREEN}✓${COLOR_RESET} Docker Engine: ${COLOR_BOLD}${docker_version}${COLOR_RESET}"
        
        # Verificar que Docker daemon esté corriendo
        if docker info &>/dev/null; then
            log SUCCESS "Docker daemon corriendo"
            echo "  ${COLOR_GREEN}→${COLOR_RESET} Docker daemon: ${COLOR_GREEN}activo${COLOR_RESET}"
        else
            log ERROR "Docker daemon no está corriendo"
            echo "  ${COLOR_RED}→${COLOR_RESET} Docker daemon: ${COLOR_RED}inactivo${COLOR_RESET}"
            all_ok=false
        fi
    else
        log ERROR "Docker no encontrado"
        echo "${COLOR_RED}✗${COLOR_RESET} Docker Engine: ${COLOR_RED}no instalado${COLOR_RESET}"
        all_ok=false
    fi
    
    # Docker Compose
    log INFO "Verificando Docker Compose..."
    if docker compose version &>/dev/null; then
        local compose_version=$(docker compose version | grep -oP '\d+\.\d+\.\d+' | head -1)
        log SUCCESS "Docker Compose V2 encontrado: ${compose_version}"
        echo "${COLOR_GREEN}✓${COLOR_RESET} Docker Compose: ${COLOR_BOLD}v${compose_version}${COLOR_RESET}"
    elif command -v docker-compose &>/dev/null; then
        local compose_version=$(docker-compose --version | grep -oP '\d+\.\d+\.\d+' | head -1)
        log WARNING "Docker Compose V1 encontrado (legacy): ${compose_version}"
        echo "${COLOR_YELLOW}⚠${COLOR_RESET} Docker Compose: ${COLOR_YELLOW}v${compose_version} (legacy)${COLOR_RESET}"
        echo "  ${COLOR_YELLOW}→${COLOR_RESET} Se recomienda actualizar a Docker Compose V2"
    else
        log ERROR "Docker Compose no encontrado"
        echo "${COLOR_RED}✗${COLOR_RESET} Docker Compose: ${COLOR_RED}no instalado${COLOR_RESET}"
        all_ok=false
    fi
    
    # Python
    log INFO "Verificando Python..."
    if command -v python3 &>/dev/null; then
        local python_version=$(python3 --version | grep -oP '\d+\.\d+\.\d+')
        local python_major=$(echo "${python_version}" | cut -d. -f1)
        local python_minor=$(echo "${python_version}" | cut -d. -f2)
        
        if [[ ${python_major} -eq 3 ]] && [[ ${python_minor} -ge 8 ]]; then
            log SUCCESS "Python encontrado: ${python_version}"
            echo "${COLOR_GREEN}✓${COLOR_RESET} Python: ${COLOR_BOLD}${python_version}${COLOR_RESET}"
        else
            log WARNING "Python versión antigua: ${python_version} (se requiere 3.8+)"
            echo "${COLOR_YELLOW}⚠${COLOR_RESET} Python: ${COLOR_YELLOW}${python_version}${COLOR_RESET} (se requiere 3.8+)"
            all_ok=false
        fi
    else
        log ERROR "Python3 no encontrado"
        echo "${COLOR_RED}✗${COLOR_RESET} Python 3: ${COLOR_RED}no instalado${COLOR_RESET}"
        all_ok=false
    fi
    
    # Librería cryptography
    log INFO "Verificando librería cryptography de Python..."
    if python3 -c "import cryptography" 2>/dev/null; then
        local crypto_version=$(python3 -c "import cryptography; print(cryptography.__version__)" 2>/dev/null)
        log SUCCESS "Librería cryptography encontrada: ${crypto_version}"
        echo "${COLOR_GREEN}✓${COLOR_RESET} cryptography: ${COLOR_BOLD}${crypto_version}${COLOR_RESET}"
    else
        log ERROR "Librería cryptography no encontrada"
        echo "${COLOR_RED}✗${COLOR_RESET} cryptography: ${COLOR_RED}no instalada${COLOR_RESET}"
        echo "  ${COLOR_YELLOW}→${COLOR_RESET} Instalar con: pip3 install cryptography"
        all_ok=false
    fi
    
    # Git (opcional pero recomendado)
    if command -v git &>/dev/null; then
        local git_version=$(git --version | grep -oP '\d+\.\d+\.\d+')
        log SUCCESS "Git encontrado: ${git_version}"
        echo "${COLOR_GREEN}✓${COLOR_RESET} Git: ${COLOR_BOLD}${git_version}${COLOR_RESET} (opcional)"
    fi
    
    # Verificar espacio en disco
    log INFO "Verificando espacio en disco..."
    local available_space
    if command -v df &>/dev/null; then
        available_space=$(df -BG "${SCRIPT_DIR}" | awk 'NR==2 {print $4}' | sed 's/G//')
        
        if [[ ${available_space} -ge 10 ]]; then
            log SUCCESS "Espacio disponible: ${available_space}GB"
            echo "${COLOR_GREEN}✓${COLOR_RESET} Espacio en disco: ${COLOR_BOLD}${available_space}GB${COLOR_RESET} disponibles"
        else
            log WARNING "Poco espacio disponible: ${available_space}GB (se recomiendan 10GB+)"
            echo "${COLOR_YELLOW}⚠${COLOR_RESET} Espacio en disco: ${COLOR_YELLOW}${available_space}GB${COLOR_RESET} (bajo)"
            
            if ! confirm "¿Desea continuar con poco espacio en disco?" "n"; then
                all_ok=false
            fi
        fi
    fi
    
    print_separator
    
    if [[ "${all_ok}" == "false" ]]; then
        log ERROR "Algunas dependencias faltan o tienen problemas"
        echo ""
        echo "${COLOR_RED}Dependencias faltantes o con problemas detectadas${COLOR_RESET}"
        echo ""
        echo "${COLOR_YELLOW}Guía de instalación:${COLOR_RESET}"
        echo ""
        echo "${COLOR_BOLD}Linux (Ubuntu/Debian):${COLOR_RESET}"
        echo "  sudo apt update"
        echo "  sudo apt install docker.io docker-compose-v2 python3 python3-pip"
        echo "  sudo pip3 install cryptography"
        echo ""
        echo "${COLOR_BOLD}macOS:${COLOR_RESET}"
        echo "  brew install docker docker-compose python3"
        echo "  pip3 install cryptography"
        echo ""
        echo "${COLOR_BOLD}Windows (WSL2):${COLOR_RESET}"
        echo "  # En WSL2 Ubuntu:"
        echo "  sudo apt install docker.io python3 python3-pip"
        echo "  sudo pip3 install cryptography"
        echo ""
        return 1
    fi
    
    log SUCCESS "Todas las dependencias verificadas correctamente"
    return 0
}

# ============================================================================
# VERIFICACIÓN DE PUERTOS
# ============================================================================

check_ports() {
    print_header "VERIFICACIÓN DE PUERTOS"
    
    log INFO "Verificando disponibilidad de puertos críticos..."
    
    local ports_in_use=()
    local all_available=true
    
    echo "${COLOR_CYAN}Verificando puertos necesarios para RHINOMETRIC:${COLOR_RESET}"
    echo ""
    
    for port in "${CRITICAL_PORTS[@]}"; do
        # Determinar servicio
        local service=""
        case $port in
            3000) service="Grafana" ;;
            9090) service="Prometheus" ;;
            3100) service="Loki" ;;
            5432) service="PostgreSQL" ;;
            9093) service="Alertmanager" ;;
            8080) service="Landing Page" ;;
            8081) service="Rhino API" ;;
            9080) service="Pushgateway" ;;
            9115) service="Blackbox Exporter" ;;
            *) service="Unknown" ;;
        esac
        
        # Verificar puerto (compatible multiplataforma)
        local port_check=""
        if command -v netstat &>/dev/null; then
            port_check=$(netstat -tuln 2>/dev/null | grep ":${port} " || true)
        elif command -v ss &>/dev/null; then
            port_check=$(ss -tuln 2>/dev/null | grep ":${port} " || true)
        elif command -v lsof &>/dev/null; then
            port_check=$(lsof -i ":${port}" 2>/dev/null || true)
        fi
        
        if [[ -n "${port_check}" ]]; then
            log WARNING "Puerto ${port} (${service}) en uso"
            echo "${COLOR_RED}✗${COLOR_RESET} Puerto ${COLOR_BOLD}${port}${COLOR_RESET} (${service}): ${COLOR_RED}EN USO${COLOR_RESET}"
            ports_in_use+=("${port}:${service}")
            all_available=false
        else
            log SUCCESS "Puerto ${port} (${service}) disponible"
            echo "${COLOR_GREEN}✓${COLOR_RESET} Puerto ${COLOR_BOLD}${port}${COLOR_RESET} (${service}): ${COLOR_GREEN}disponible${COLOR_RESET}"
        fi
    done
    
    print_separator
    
    if [[ "${all_available}" == "false" ]]; then
        echo ""
        echo "${COLOR_YELLOW}⚠️  ADVERTENCIA: Algunos puertos están en uso${COLOR_RESET}"
        echo ""
        echo "${COLOR_CYAN}Puertos en conflicto:${COLOR_RESET}"
        for port_service in "${ports_in_use[@]}"; do
            echo "  • ${port_service}"
        done
        echo ""
        echo "${COLOR_YELLOW}Soluciones:${COLOR_RESET}"
        echo "  1. Detener los servicios que usan estos puertos"
        echo "  2. Modificar docker-compose-v2.2.0.yml para usar puertos diferentes"
        echo "  3. Usar Docker en modo host (no recomendado)"
        echo ""
        
        if ! confirm "¿Desea continuar de todas formas?" "n"; then
            log ERROR "Instalación cancelada por usuario debido a puertos en uso"
            return 1
        fi
    else
        log SUCCESS "Todos los puertos están disponibles"
        echo "${COLOR_GREEN}✓${COLOR_RESET} Todos los puertos necesarios están disponibles"
    fi
    
    return 0
}

# ============================================================================
# RESUMEN PRE-INSTALACIÓN
# ============================================================================

show_pre_install_summary() {
    print_header "RESUMEN PRE-INSTALACIÓN"
    
    echo "${COLOR_BOLD}Configuración de instalación:${COLOR_RESET}"
    echo ""
    
    echo "${COLOR_CYAN}Versión:${COLOR_RESET}          RHINOMETRIC v${VERSION}"
    echo "${COLOR_CYAN}Directorio:${COLOR_RESET}       ${SCRIPT_DIR}"
    echo "${COLOR_CYAN}Compose File:${COLOR_RESET}     ${COMPOSE_FILE}"
    echo "${COLOR_CYAN}Licencia:${COLOR_RESET}         ${LICENSE_FILE}"
    echo "${COLOR_CYAN}Log File:${COLOR_RESET}         ${LOG_FILE}"
    echo "${COLOR_CYAN}Backup Dir:${COLOR_RESET}       ${BACKUP_DIR}"
    echo ""
    
    echo "${COLOR_BOLD}Servicios a desplegar:${COLOR_RESET}"
    echo "  • Grafana (Visualización)"
    echo "  • Prometheus (Métricas)"
    echo "  • Loki (Logs)"
    echo "  • Alertmanager (Alertas)"
    echo "  • PostgreSQL (Base de datos)"
    echo "  • Blackbox Exporter (Monitoreo)"
    echo "  • Pushgateway (Métricas push)"
    echo "  • License Monitor (Alertas de licencia)"
    echo "  • Landing Page (Interfaz web)"
    echo "  • + otros servicios de soporte"
    echo ""
    
    print_separator
    
    if ! confirm "¿Desea continuar con la instalación?" "y"; then
        log INFO "Instalación cancelada por el usuario"
        echo "${COLOR_YELLOW}Instalación cancelada${COLOR_RESET}"
        exit 0
    fi
}

# ============================================================================
# CREAR BACKUP PRE-INSTALACIÓN
# ============================================================================

create_backup() {
    print_header "CREACIÓN DE BACKUP"
    
    log INFO "Creando backup de configuración actual..."
    
    mkdir -p "${BACKUP_DIR}"
    log SUCCESS "Directorio de backup creado: ${BACKUP_DIR}"
    
    # Backup de docker-compose
    if [[ -f "${COMPOSE_FILE}" ]]; then
        cp "${COMPOSE_FILE}" "${BACKUP_DIR}/"
        log SUCCESS "Backup de docker-compose.yml"
        echo "${COLOR_GREEN}✓${COLOR_RESET} docker-compose-v2.2.0.yml"
    fi
    
    # Backup de licencia
    if [[ -f "${LICENSE_FILE}" ]]; then
        cp "${LICENSE_FILE}" "${BACKUP_DIR}/"
        log SUCCESS "Backup de licencia"
        echo "${COLOR_GREEN}✓${COLOR_RESET} cliente.lic"
    fi
    
    # Backup de scripts de validación
    if [[ -f "${VALIDATOR_SCRIPT}" ]]; then
        cp "${VALIDATOR_SCRIPT}" "${BACKUP_DIR}/"
        log SUCCESS "Backup de validador"
        echo "${COLOR_GREEN}✓${COLOR_RESET} validate_license.py"
    fi
    
    # Backup de .env si existe
    if [[ -f "${SCRIPT_DIR}/.env" ]]; then
        cp "${SCRIPT_DIR}/.env" "${BACKUP_DIR}/"
        log SUCCESS "Backup de .env"
        echo "${COLOR_GREEN}✓${COLOR_RESET} .env"
    fi
    
    # Listar contenedores actuales
    if docker ps -a --format '{{.Names}}' > "${BACKUP_DIR}/containers-before.txt" 2>/dev/null; then
        log SUCCESS "Lista de contenedores actuales guardada"
        echo "${COLOR_GREEN}✓${COLOR_RESET} containers-before.txt"
    fi
    
    print_separator
    log SUCCESS "Backup completado en: ${BACKUP_DIR}"
    echo "${COLOR_GREEN}✓${COLOR_RESET} Backup completado"
}

# ============================================================================
# DESPLIEGUE CON DOCKER COMPOSE
# ============================================================================

deploy_stack() {
    print_header "DESPLIEGUE DEL STACK RHINOMETRIC"
    
    log INFO "Iniciando despliegue de servicios..."
    
    INSTALL_STATE="DEPLOYING"
    
    # Pull de imágenes
    log STEP "Descargando imágenes Docker..."
    echo "${COLOR_CYAN}Descargando imágenes necesarias...${COLOR_RESET}"
    
    if docker compose -f "${COMPOSE_FILE}" pull 2>&1 | tee -a "${LOG_FILE}"; then
        log SUCCESS "Imágenes descargadas correctamente"
        echo "${COLOR_GREEN}✓${COLOR_RESET} Imágenes descargadas"
    else
        log ERROR "Error al descargar imágenes"
        echo "${COLOR_RED}✗${COLOR_RESET} Error al descargar imágenes"
        ROLLBACK_NEEDED=true
        return 1
    fi
    
    echo ""
    
    # Build de servicios custom
    log STEP "Construyendo servicios personalizados..."
    echo "${COLOR_CYAN}Construyendo servicios personalizados...${COLOR_RESET}"
    
    if docker compose -f "${COMPOSE_FILE}" build 2>&1 | tee -a "${LOG_FILE}"; then
        log SUCCESS "Servicios construidos correctamente"
        echo "${COLOR_GREEN}✓${COLOR_RESET} Build completado"
    else
        log ERROR "Error al construir servicios"
        echo "${COLOR_RED}✗${COLOR_RESET} Error en build"
        ROLLBACK_NEEDED=true
        return 1
    fi
    
    echo ""
    
    # Levantar servicios
    log STEP "Levantando servicios..."
    echo "${COLOR_CYAN}Iniciando todos los servicios...${COLOR_RESET}"
    echo ""
    
    if docker compose -f "${COMPOSE_FILE}" up -d 2>&1 | tee -a "${LOG_FILE}"; then
        log SUCCESS "Servicios levantados correctamente"
        echo ""
        echo "${COLOR_GREEN}✓${COLOR_RESET} Servicios iniciados correctamente"
    else
        log ERROR "Error al levantar servicios"
        echo ""
        echo "${COLOR_RED}✗${COLOR_RESET} Error al iniciar servicios"
        ROLLBACK_NEEDED=true
        return 1
    fi
    
    INSTALL_STATE="DEPLOYED"
    print_separator
    return 0
}

# ============================================================================
# HEALTHCHECKS POST-DESPLIEGUE
# ============================================================================

verify_deployment() {
    print_header "VERIFICACIÓN DE DESPLIEGUE"
    
    log INFO "Esperando a que los servicios estén listos..."
    echo "${COLOR_CYAN}Esperando inicialización de servicios (30s)...${COLOR_RESET}"
    
    for i in {1..30}; do
        progress_bar $i 30 "Inicializando"
        sleep 1
    done
    
    echo ""
    
    log INFO "Verificando estado de contenedores..."
    
    local all_healthy=true
    local total_services=0
    local running_services=0
    
    # Listar contenedores del stack
    local containers=$(docker compose -f "${COMPOSE_FILE}" ps --format '{{.Name}}' 2>/dev/null || true)
    
    if [[ -z "${containers}" ]]; then
        log ERROR "No se encontraron contenedores del stack"
        echo "${COLOR_RED}✗${COLOR_RESET} No se detectaron contenedores"
        return 1
    fi
    
    echo "${COLOR_CYAN}Estado de servicios:${COLOR_RESET}"
    echo ""
    
    while IFS= read -r container; do
        total_services=$((total_services + 1))
        
        local status=$(docker inspect --format='{{.State.Status}}' "${container}" 2>/dev/null || echo "unknown")
        local health=$(docker inspect --format='{{.State.Health.Status}}' "${container}" 2>/dev/null || echo "none")
        
        if [[ "${status}" == "running" ]]; then
            running_services=$((running_services + 1))
            
            if [[ "${health}" == "healthy" ]]; then
                log SUCCESS "${container}: running (healthy)"
                echo "${COLOR_GREEN}✓${COLOR_RESET} ${container}: ${COLOR_GREEN}healthy${COLOR_RESET}"
            elif [[ "${health}" == "none" ]]; then
                log SUCCESS "${container}: running (no healthcheck)"
                echo "${COLOR_GREEN}✓${COLOR_RESET} ${container}: ${COLOR_GREEN}running${COLOR_RESET}"
            else
                log WARNING "${container}: running (${health})"
                echo "${COLOR_YELLOW}⚠${COLOR_RESET} ${container}: ${COLOR_YELLOW}${health}${COLOR_RESET}"
            fi
        else
            log ERROR "${container}: ${status}"
            echo "${COLOR_RED}✗${COLOR_RESET} ${container}: ${COLOR_RED}${status}${COLOR_RESET}"
            all_healthy=false
        fi
    done <<< "${containers}"
    
    echo ""
    print_separator
    
    log INFO "Servicios corriendo: ${running_services}/${total_services}"
    echo "${COLOR_CYAN}Resumen:${COLOR_RESET} ${running_services}/${total_services} servicios corriendo"
    
    if [[ "${all_healthy}" == "false" ]]; then
        log WARNING "Algunos servicios no están completamente saludables"
        echo "${COLOR_YELLOW}⚠${COLOR_RESET} Algunos servicios requieren más tiempo para inicializar"
        echo "   Puede verificar el estado más tarde con: docker compose ps"
    else
        log SUCCESS "Todos los servicios están corriendo correctamente"
        echo "${COLOR_GREEN}✓${COLOR_RESET} Todos los servicios están operativos"
    fi
    
    return 0
}

# ============================================================================
# VERIFICACIÓN DE ACCESO A SERVICIOS
# ============================================================================

test_service_access() {
    print_header "VERIFICACIÓN DE ACCESO A SERVICIOS"
    
    log INFO "Probando acceso a servicios web..."
    
    local services=(
        "Grafana:http://localhost:3000:admin:admin"
        "Prometheus:http://localhost:9090:-:-"
        "Alertmanager:http://localhost:9093:-:-"
        "Landing:http://localhost:8080:-:-"
    )
    
    echo "${COLOR_CYAN}Probando endpoints:${COLOR_RESET}"
    echo ""
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r name url user pass <<< "${service_info}"
        
        local response
        local http_code
        
        if command -v curl &>/dev/null; then
            http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${url}" 2>/dev/null || echo "000")
        else
            http_code="000"
            log WARNING "curl no disponible, no se puede probar ${name}"
        fi
        
        if [[ "${http_code}" == "200" ]] || [[ "${http_code}" == "302" ]]; then
            log SUCCESS "${name}: accesible (HTTP ${http_code})"
            echo "${COLOR_GREEN}✓${COLOR_RESET} ${name}: ${COLOR_GREEN}accesible${COLOR_RESET} (${url})"
        elif [[ "${http_code}" == "000" ]]; then
            log WARNING "${name}: no accesible (timeout o conexión rechazada)"
            echo "${COLOR_YELLOW}⚠${COLOR_RESET} ${name}: ${COLOR_YELLOW}no responde${COLOR_RESET} (puede necesitar más tiempo)"
        else
            log WARNING "${name}: HTTP ${http_code}"
            echo "${COLOR_YELLOW}⚠${COLOR_RESET} ${name}: ${COLOR_YELLOW}HTTP ${http_code}${COLOR_RESET}"
        fi
    done
    
    print_separator
    
    echo ""
    echo "${COLOR_CYAN}${COLOR_BOLD}Acceso a servicios:${COLOR_RESET}"
    echo ""
    echo "  ${COLOR_BOLD}Grafana:${COLOR_RESET}       http://localhost:3000"
    echo "                  Usuario: ${COLOR_GREEN}admin${COLOR_RESET} | Password: ${COLOR_GREEN}admin${COLOR_RESET}"
    echo ""
    echo "  ${COLOR_BOLD}Prometheus:${COLOR_RESET}    http://localhost:9090"
    echo "  ${COLOR_BOLD}Alertmanager:${COLOR_RESET}  http://localhost:9093"
    echo "  ${COLOR_BOLD}Landing Page:${COLOR_RESET}  http://localhost:8080"
    echo ""
}

# ============================================================================
# ROLLBACK EN CASO DE ERROR
# ============================================================================

rollback_installation() {
    print_header "ROLLBACK DE INSTALACIÓN"
    
    log WARNING "Iniciando rollback de la instalación..."
    echo "${COLOR_YELLOW}Revirtiendo cambios...${COLOR_RESET}"
    echo ""
    
    # Detener servicios
    log INFO "Deteniendo servicios..."
    if docker compose -f "${COMPOSE_FILE}" down 2>&1 | tee -a "${LOG_FILE}"; then
        log SUCCESS "Servicios detenidos"
        echo "${COLOR_GREEN}✓${COLOR_RESET} Servicios detenidos"
    else
        log ERROR "Error al detener servicios"
        echo "${COLOR_RED}✗${COLOR_RESET} Error al detener servicios"
    fi
    
    # Restaurar archivos desde backup
    if [[ -d "${BACKUP_DIR}" ]]; then
        log INFO "Restaurando archivos desde backup..."
        
        if [[ -f "${BACKUP_DIR}/docker-compose-v2.2.0.yml" ]]; then
            cp "${BACKUP_DIR}/docker-compose-v2.2.0.yml" "${COMPOSE_FILE}"
            log SUCCESS "docker-compose restaurado"
            echo "${COLOR_GREEN}✓${COLOR_RESET} docker-compose restaurado"
        fi
        
        if [[ -f "${BACKUP_DIR}/.env" ]]; then
            cp "${BACKUP_DIR}/.env" "${SCRIPT_DIR}/"
            log SUCCESS ".env restaurado"
            echo "${COLOR_GREEN}✓${COLOR_RESET} .env restaurado"
        fi
    fi
    
    print_separator
    
    log WARNING "Rollback completado"
    echo "${COLOR_YELLOW}Rollback completado${COLOR_RESET}"
    echo ""
    echo "Para más información revise: ${LOG_FILE}"
}

# ============================================================================
# REPORTE FINAL
# ============================================================================

show_final_report() {
    print_header "INSTALACIÓN COMPLETADA EXITOSAMENTE"
    
    echo "${COLOR_GREEN}${COLOR_BOLD}🎉 ¡RHINOMETRIC v${VERSION} instalado correctamente!${COLOR_RESET}"
    echo ""
    
    echo "${COLOR_CYAN}${COLOR_BOLD}Acceso a servicios:${COLOR_RESET}"
    echo ""
    echo "  ${COLOR_BOLD}Grafana Dashboard:${COLOR_RESET}"
    echo "    URL:      http://localhost:3000"
    echo "    Usuario:  ${COLOR_GREEN}admin${COLOR_RESET}"
    echo "    Password: ${COLOR_GREEN}admin${COLOR_RESET}"
    echo ""
    echo "  ${COLOR_BOLD}Prometheus:${COLOR_RESET}        http://localhost:9090"
    echo "  ${COLOR_BOLD}Alertmanager:${COLOR_RESET}      http://localhost:9093"
    echo "  ${COLOR_BOLD}Landing Page:${COLOR_RESET}      http://localhost:8080"
    echo ""
    
    echo "${COLOR_CYAN}${COLOR_BOLD}Comandos útiles:${COLOR_RESET}"
    echo ""
    echo "  ${COLOR_BOLD}Ver logs:${COLOR_RESET}"
    echo "    docker compose -f ${COMPOSE_FILE} logs -f [servicio]"
    echo ""
    echo "  ${COLOR_BOLD}Estado de servicios:${COLOR_RESET}"
    echo "    docker compose -f ${COMPOSE_FILE} ps"
    echo ""
    echo "  ${COLOR_BOLD}Reiniciar servicios:${COLOR_RESET}"
    echo "    docker compose -f ${COMPOSE_FILE} restart"
    echo ""
    echo "  ${COLOR_BOLD}Detener todo:${COLOR_RESET}"
    echo "    docker compose -f ${COMPOSE_FILE} down"
    echo ""
    
    echo "${COLOR_CYAN}${COLOR_BOLD}Archivos generados:${COLOR_RESET}"
    echo "  • Log de instalación: ${LOG_FILE}"
    echo "  • Backup: ${BACKUP_DIR}"
    echo ""
    
    echo "${COLOR_CYAN}${COLOR_BOLD}Soporte:${COLOR_RESET}"
    echo "  Email: support@rhinometric.com"
    echo "  Docs:  https://docs.rhinometric.com"
    echo ""
    
    print_separator
    
    log SUCCESS "Instalación completada exitosamente"
}

# ============================================================================
# TRAP PARA MANEJAR ERRORES Y CTRL+C
# ============================================================================

cleanup_on_exit() {
    local exit_code=$?
    
    if [[ ${exit_code} -ne 0 ]] && [[ "${ROLLBACK_NEEDED}" == "true" ]]; then
        echo ""
        log ERROR "Error durante la instalación (código: ${exit_code})"
        
        if confirm "¿Desea realizar un rollback automático?" "y"; then
            rollback_installation
        fi
    fi
    
    log INFO "Script finalizado con código: ${exit_code}"
}

trap cleanup_on_exit EXIT INT TERM

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

main() {
    # Banner
    clear
    echo "${COLOR_MAGENTA}${COLOR_BOLD}"
    cat << "EOF"
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║                   RHINOMETRIC v2.3.0 - SECURE INSTALLER                ║
║                                                                        ║
║        Observability Platform - On-Premise & GDPR Compliant           ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
EOF
    echo "${COLOR_RESET}"
    
    log INFO "Iniciando instalador seguro de RHINOMETRIC v${VERSION}"
    log INFO "Directorio de trabajo: ${SCRIPT_DIR}"
    
    # Fase 1: Detección de OS
    detect_os || exit 1
    
    # Fase 2: Validación de licencia
    validate_license || {
        log ERROR "Validación de licencia falló - instalación abortada"
        exit 1
    }
    
    # Fase 3: Verificación de dependencias
    check_dependencies || {
        log ERROR "Dependencias faltantes - instalación abortada"
        exit 1
    }
    
    # Fase 4: Verificación de puertos
    check_ports || {
        log ERROR "Verificación de puertos falló - instalación abortada"
        exit 1
    }
    
    # Fase 5: Resumen y confirmación
    show_pre_install_summary
    
    # Fase 6: Backup
    create_backup || {
        log ERROR "Error al crear backup"
        exit 1
    }
    
    # Fase 7: Despliegue
    deploy_stack || {
        log ERROR "Error durante el despliegue"
        exit 1
    }
    
    # Fase 8: Verificación post-despliegue
    verify_deployment || {
        log WARNING "Verificación post-despliegue con advertencias"
    }
    
    # Fase 9: Test de acceso
    test_service_access
    
    # Fase 10: Reporte final
    show_final_report
    
    log SUCCESS "Instalación completada exitosamente en $(date)"
    
    return 0
}

# ============================================================================
# EJECUCIÓN
# ============================================================================

# Verificar que se ejecuta desde el directorio correcto
if [[ ! -f "${COMPOSE_FILE}" ]]; then
    echo "${COLOR_RED}ERROR: docker-compose-v2.2.0.yml no encontrado${COLOR_RESET}"
    echo "Por favor ejecute este script desde el directorio de RHINOMETRIC"
    exit 1
fi

# Inicializar log
echo "RHINOMETRIC v${VERSION} - Secure Installer Log" > "${LOG_FILE}"
echo "Started at: $(date)" >> "${LOG_FILE}"
echo "=======================================" >> "${LOG_FILE}"
echo "" >> "${LOG_FILE}"

# Ejecutar instalación
main "$@"

exit $?
