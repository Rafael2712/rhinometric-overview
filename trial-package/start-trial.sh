#!/bin/bash

# ════════════════════════════════════════════════════════════════════════════
# RHINOMETRIC TRIAL - SCRIPT DE INSTALACIÓN
# Versión: 1.0
# Plataforma de Observabilidad - Trial 180 días
# Compatible: macOS 10.15+, Linux
# ════════════════════════════════════════════════════════════════════════════

set -e  # Salir si hay errores

# ════════════════════════════════════════════════════════════════════════════
# COLORES Y FORMATEO
# ════════════════════════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # Sin color
BOLD='\033[1m'

# ════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ════════════════════════════════════════════════════════════════════════════

print_header() {
    echo ""
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  🦏 RHINOMETRIC TRIAL - INSTALADOR${NC}"
    echo -e "${CYAN}  Plataforma de Observabilidad Completa${NC}"
    echo -e "${YELLOW}  Versión Trial: 180 días${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}[PASO $1/$2]${NC} ${BOLD}$3${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# ════════════════════════════════════════════════════════════════════════════
# VERIFICACIONES INICIALES
# ════════════════════════════════════════════════════════════════════════════

check_docker() {
    print_step 1 7 "Verificando Docker Desktop"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado"
        echo ""
        echo "Por favor instala Docker Desktop desde:"
        echo -e "${CYAN}https://www.docker.com/products/docker-desktop${NC}"
        echo ""
        echo "Instrucciones:"
        echo "  1. Descarga Docker Desktop para Mac"
        echo "  2. Instala y abre Docker Desktop"
        echo "  3. Espera que el ícono de Docker en la barra superior muestre 'Docker is running'"
        echo "  4. Vuelve a ejecutar este script"
        exit 1
    fi
    
    if ! docker info &> /dev/null 2>&1; then
        print_error "Docker no está corriendo"
        echo ""
        echo "Por favor:"
        echo "  1. Abre Docker Desktop desde Aplicaciones"
        echo "  2. Espera a que inicie (ícono de Docker en la barra superior)"
        echo "  3. Vuelve a ejecutar este script"
        exit 1
    fi
    
    print_success "Docker Desktop está instalado y corriendo"
    
    # Mostrar versión
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    print_info "Versión: Docker $DOCKER_VERSION"
}

check_docker_compose() {
    print_step 2 7 "Verificando Docker Compose"
    
    if docker compose version &> /dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
        COMPOSE_VERSION=$(docker compose version --short)
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        COMPOSE_VERSION=$(docker-compose version --short)
    else
        print_error "Docker Compose no está disponible"
        echo ""
        echo "Docker Compose debería venir incluido con Docker Desktop."
        echo "Si no está disponible, reinstala Docker Desktop."
        exit 1
    fi
    
    print_success "Docker Compose está disponible"
    print_info "Versión: $COMPOSE_VERSION"
}

check_resources() {
    print_step 3 7 "Verificando recursos del sistema"
    
    # Verificar memoria disponible (macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        TOTAL_RAM=$(sysctl hw.memsize | awk '{print int($2/1024/1024/1024)}')
        print_info "RAM total: ${TOTAL_RAM}GB"
        
        if [ "$TOTAL_RAM" -lt 8 ]; then
            print_warning "Se recomiendan al menos 8GB de RAM"
            print_warning "Tu sistema tiene ${TOTAL_RAM}GB, puede funcionar más lento"
        else
            print_success "RAM suficiente (${TOTAL_RAM}GB)"
        fi
    fi
    
    # Verificar espacio en disco
    DISK_FREE=$(df -h . | tail -1 | awk '{print $4}')
    print_info "Espacio disponible: $DISK_FREE"
    print_success "Recursos verificados"
}

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ════════════════════════════════════════════════════════════════════════════

generate_random_string() {
    LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c "$1"
}

create_env_file() {
    print_step 4 7 "Configurando variables de entorno"
    
    if [ -f .env ]; then
        print_warning "Archivo .env ya existe"
        read -p "¿Deseas sobrescribirlo? (s/N): " OVERWRITE
        if [[ ! "$OVERWRITE" =~ ^[Ss]$ ]]; then
            print_info "Usando .env existente"
            return
        fi
    fi
    
    echo "Generando configuración segura..."
    
    # Generar contraseñas aleatorias
    POSTGRES_PASS=$(generate_random_string 32)
    GRAFANA_PASS=$(generate_random_string 16)
    JWT_SECRET=$(generate_random_string 64)
    
    # Crear archivo .env
    cat > .env << EOF
# ════════════════════════════════════════════════════════════════
# RHINOMETRIC TRIAL - CONFIGURACIÓN
# Generado: $(date +"%Y-%m-%d %H:%M:%S")
# ════════════════════════════════════════════════════════════════

# Base de datos PostgreSQL
POSTGRES_DB=rhinometric
POSTGRES_USER=rhinometric
POSTGRES_PASSWORD=${POSTGRES_PASS}

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=${GRAFANA_PASS}

# Sistema de licencias
JWT_SECRET=${JWT_SECRET}

# Configuración adicional
TZ=America/New_York
COMPOSE_PROJECT_NAME=rhinometric-trial

# ════════════════════════════════════════════════════════════════
# IMPORTANTE: Guarda estas credenciales en un lugar seguro
# ════════════════════════════════════════════════════════════════
EOF

    chmod 600 .env
    print_success "Archivo .env generado"
    
    # Guardar credenciales en archivo separado
    cat > credentials.txt << EOF
════════════════════════════════════════════════════════════════
RHINOMETRIC TRIAL - CREDENCIALES DE ACCESO
Fecha: $(date +"%Y-%m-%d %H:%M:%S")
════════════════════════════════════════════════════════════════

🎨 GRAFANA DASHBOARD
   URL:      http://localhost:3000
   Usuario:  admin
   Password: ${GRAFANA_PASS}

🗄️  POSTGRESQL
   Host:     localhost:5432
   Database: rhinometric
   Usuario:  rhinometric
   Password: ${POSTGRES_PASS}

🔐 JWT SECRET
   ${JWT_SECRET}

════════════════════════════════════════════════════════════════
⚠️  IMPORTANTE: Guarda este archivo en un lugar seguro
════════════════════════════════════════════════════════════════
EOF

    chmod 600 credentials.txt
    print_success "Credenciales guardadas en credentials.txt"
}

create_directories() {
    print_step 5 7 "Creando estructura de directorios"
    
    mkdir -p licenses
    mkdir -p certs
    mkdir -p data/postgres
    mkdir -p data/grafana
    mkdir -p data/prometheus
    mkdir -p data/loki
    mkdir -p logs
    
    print_success "Directorios creados"
}

generate_license() {
    print_step 6 7 "Generando licencia Trial"
    
    echo ""
    read -p "Nombre del cliente u organización: " CLIENT_NAME
    CLIENT_NAME=${CLIENT_NAME:-"Trial Demo"}
    
    # Calcular fecha de expiración (180 días)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        EXPIRE_DATE=$(date -v+180d +"%Y-%m-%d")
    else
        EXPIRE_DATE=$(date -d "+180 days" +"%Y-%m-%d")
    fi
    
    # Crear archivo de licencia
    LICENSE_FILE="licenses/trial_${CLIENT_NAME// /_}.lic"
    
    cat > "$LICENSE_FILE" << EOF
════════════════════════════════════════════════════════════════
RHINOMETRIC TRIAL LICENSE
════════════════════════════════════════════════════════════════

Cliente:      ${CLIENT_NAME}
Tipo:         Trial
Producto:     Rhinometric Observability Platform
Versión:      1.0

Generado:     $(date +"%Y-%m-%d")
Expira:       ${EXPIRE_DATE}
Duración:     180 días (6 meses)

════════════════════════════════════════════════════════════════
CARACTERÍSTICAS INCLUIDAS
════════════════════════════════════════════════════════════════

✅ Grafana Dashboard completo
✅ Prometheus (métricas)
✅ Loki (logs)
✅ Tempo (trazas distribuidas)
✅ Alertmanager
✅ Exportadores de sistema
✅ Dashboard de licencias

════════════════════════════════════════════════════════════════
LIMITACIONES TRIAL
════════════════════════════════════════════════════════════════

- Retención de datos: 7 días
- Máximo usuarios Grafana: 5
- Sin alta disponibilidad
- Soporte: Básico vía email
- No apto para producción

════════════════════════════════════════════════════════════════
SOPORTE Y CONTACTO
════════════════════════════════════════════════════════════════

Email:        soporte@rhinometric.com
Comercial:    ventas@rhinometric.com
Web:          https://rhinometric.com

Para convertir a versión comercial, contacta con nuestro equipo.

════════════════════════════════════════════════════════════════
EOF

    print_success "Licencia generada: $LICENSE_FILE"
    print_info "Cliente: ${CLIENT_NAME}"
    print_info "Expira: ${EXPIRE_DATE}"
}

# ════════════════════════════════════════════════════════════════════════════
# INSTALACIÓN
# ════════════════════════════════════════════════════════════════════════════

start_services() {
    print_step 7 7 "Iniciando servicios Rhinometric"
    
    echo ""
    read -p "¿Iniciar Rhinometric ahora? (S/n): " START_NOW
    START_NOW=${START_NOW:-S}
    
    if [[ ! "$START_NOW" =~ ^[Ss]$ ]]; then
        echo ""
        print_warning "Instalación completada pero servicios no iniciados"
        echo ""
        echo "Para iniciar manualmente:"
        echo -e "${CYAN}  $COMPOSE_CMD up -d${NC}"
        return
    fi
    
    echo ""
    print_info "Validando docker-compose.yml..."
    
    # Validar sintaxis de docker-compose.yml
    if ! $COMPOSE_CMD config > /dev/null 2>&1; then
        print_error "Error de sintaxis en docker-compose.yml"
        echo ""
        echo "Ejecuta para ver detalles:"
        echo "  $COMPOSE_CMD config"
        exit 1
    fi
    
    print_success "Sintaxis de docker-compose.yml válida"
    
    echo ""
    print_info "Descargando imágenes Docker (esto puede tardar varios minutos)..."
    print_warning "Primera ejecución: ~5-10 minutos dependiendo de tu conexión"
    echo ""
    
    # Detener servicios previos si existen
    $COMPOSE_CMD down --remove-orphans 2>/dev/null || true
    
    # Limpiar contenedores colgados
    print_info "Limpiando contenedores anteriores..."
    docker container prune -f 2>/dev/null || true
    
    echo ""
    print_info "Iniciando servicios..."
    
    # Iniciar servicios con logging mejorado
    if $COMPOSE_CMD up -d --build 2>&1 | tee /tmp/rhinometric-startup.log; then
        print_success "Contenedores iniciados correctamente"
    else
        print_error "Falló el inicio de servicios"
        echo ""
        echo "Detalles del error en: /tmp/rhinometric-startup.log"
        echo ""
        echo "Ver logs con:"
        echo "  $COMPOSE_CMD logs"
        echo ""
        echo "Para diagnóstico detallado ejecuta:"
        echo "  ./debug.sh"
        exit 1
    fi
    
    echo ""
    print_info "Esperando que los servicios estén listos (30 segundos)..."
    
    # Mostrar progreso
    for i in {1..30}; do
        echo -n "."
        sleep 1
    done
    echo ""
    
    # Verificar servicios
    echo ""
    print_info "Estado de servicios:"
    $COMPOSE_CMD ps
    
    # Verificar que al menos algunos servicios estén corriendo
    RUNNING_SERVICES=$($COMPOSE_CMD ps --services --filter "status=running" | wc -l)
    
    if [ "$RUNNING_SERVICES" -eq 0 ]; then
        print_warning "Ningún servicio está corriendo"
        echo ""
        echo "Ejecuta para ver errores:"
        echo "  $COMPOSE_CMD logs"
        echo ""
        echo "O usa el script de diagnóstico:"
        echo "  ./debug.sh"
    else
        print_success "$RUNNING_SERVICES servicios están corriendo"
    fi
}

# ════════════════════════════════════════════════════════════════════════════
# FINALIZACIÓN
# ════════════════════════════════════════════════════════════════════════════

show_success_message() {
    # Leer password de Grafana del .env
    GRAFANA_PWD=$(grep GRAFANA_PASSWORD .env | cut -d'=' -f2)
    
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${GREEN}  ✅ RHINOMETRIC TRIAL INSTALADO CORRECTAMENTE${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BOLD}📊 ACCESO A LOS SERVICIOS:${NC}"
    echo ""
    echo -e "${CYAN}  🎨 Grafana Dashboard (Principal)${NC}"
    echo -e "     URL:      ${BOLD}http://localhost:3000${NC}"
    echo -e "     Usuario:  ${BOLD}admin${NC}"
    echo -e "     Password: ${BOLD}${GRAFANA_PWD}${NC}"
    echo ""
    echo -e "${CYAN}  📈 Prometheus (Métricas)${NC}"
    echo -e "     URL:      http://localhost:9090"
    echo ""
    echo -e "${CYAN}  📝 Loki (Logs)${NC}"
    echo -e "     URL:      http://localhost:3100"
    echo ""
    echo -e "${CYAN}  🔍 Tempo (Trazas)${NC}"
    echo -e "     URL:      http://localhost:3200"
    echo ""
    echo -e "${CYAN}  🚨 Alertmanager (Alertas)${NC}"
    echo -e "     URL:      http://localhost:9093"
    echo ""
    echo -e "${CYAN}  🔑 License Dashboard${NC}"
    echo -e "     URL:      http://localhost:8080"
    echo ""
    echo -e "${CYAN}  🌐 Nginx (Proxy)${NC}"
    echo -e "     URL:      http://localhost"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${BOLD}📚 COMANDOS ÚTILES:${NC}"
    echo ""
    echo -e "  Ver logs en tiempo real:"
    echo -e "    ${CYAN}$COMPOSE_CMD logs -f${NC}"
    echo ""
    echo -e "  Ver estado de servicios:"
    echo -e "    ${CYAN}$COMPOSE_CMD ps${NC}"
    echo ""
    echo -e "  Reiniciar servicios:"
    echo -e "    ${CYAN}$COMPOSE_CMD restart${NC}"
    echo ""
    echo -e "  Detener (sin borrar datos):"
    echo -e "    ${CYAN}$COMPOSE_CMD stop${NC}"
    echo ""
    echo -e "  Iniciar (después de detener):"
    echo -e "    ${CYAN}$COMPOSE_CMD start${NC}"
    echo ""
    echo -e "  Detener y eliminar TODO:"
    echo -e "    ${CYAN}$COMPOSE_CMD down -v${NC}"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
    echo ""
    echo "  • Esta es una versión TRIAL válida por 180 días"
    echo "  • Retención de datos: 7 días"
    echo "  • NO usar en entornos de producción"
    echo "  • Credenciales guardadas en: ${BOLD}credentials.txt${NC}"
    echo "  • Licencia en: ${BOLD}licenses/${NC}"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${BOLD}📞 SOPORTE:${NC}"
    echo ""
    echo "  Email:     soporte@rhinometric.com"
    echo "  Comercial: ventas@rhinometric.com"
    echo "  Docs:      README.md"
    echo ""
    echo -e "${GREEN}🎉 ¡Disfruta de Rhinometric Trial!${NC}"
    echo ""
}

# ════════════════════════════════════════════════════════════════════════════
# MAIN - FLUJO PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════

main() {
    # Limpiar pantalla
    clear
    
    # Mostrar header
    print_header
    
    # Ejecutar pasos
    check_docker
    echo ""
    
    check_docker_compose
    echo ""
    
    check_resources
    echo ""
    
    create_env_file
    echo ""
    
    create_directories
    echo ""
    
    generate_license
    echo ""
    
    start_services
    echo ""
    
    # Mostrar mensaje de éxito
    show_success_message
}

# ════════════════════════════════════════════════════════════════════════════
# EJECUCIÓN
# ════════════════════════════════════════════════════════════════════════════

main

exit 0
