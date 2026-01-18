#!/usr/bin/env bash

################################################################################
# RHINOMETRIC - Get Hardware ID (HWID)
################################################################################
#
# Script para obtener el Hardware ID único del servidor.
#
# USO:
#   ./get-hwid.sh
#
# ESTE SCRIPT NO ENVÍA DATOS A NINGÚN SERVIDOR
# Solo muestra el HWID en pantalla para que lo envíes tú mismo
#
# Autor: RHINOMETRIC Security Team
# Versión: 2.3.0
# Fecha: Noviembre 2025
#
################################################################################

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║             🔍 RHINOMETRIC Hardware ID (HWID)              ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Función para obtener CPU info
get_cpu_info() {
    local cpu_info=""
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if [ -f /proc/cpuinfo ]; then
            cpu_model=$(grep "model name" /proc/cpuinfo | head -1 | cut -d':' -f2 | xargs)
            cpu_cores=$(grep -c "processor" /proc/cpuinfo)
            cpu_info="${cpu_model} (${cpu_cores} cores)"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        cpu_model=$(sysctl -n machdep.cpu.brand_string)
        cpu_cores=$(sysctl -n hw.ncpu)
        cpu_info="${cpu_model} (${cpu_cores} cores)"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows (Git Bash / Cygwin)
        cpu_model=$(wmic cpu get name | sed -n 2p | xargs)
        cpu_cores=$(wmic cpu get NumberOfCores | sed -n 2p | xargs)
        cpu_info="${cpu_model} (${cpu_cores} cores)"
    fi
    
    echo "$cpu_info"
}

# Función para obtener MAC address principal
get_primary_mac() {
    local mac_addr=""
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux - obtener interfaz de ruta por defecto
        default_iface=$(ip route show default | grep -oP '(?<=dev )\S+' | head -1)
        if [ -n "$default_iface" ]; then
            mac_addr=$(cat /sys/class/net/$default_iface/address 2>/dev/null | tr '[:lower:]' '[:upper:]')
        fi
        
        # Fallback: primera interfaz no-loopback
        if [ -z "$mac_addr" ]; then
            mac_addr=$(ip link show | grep -A1 "state UP" | grep "link/ether" | head -1 | awk '{print $2}' | tr '[:lower:]' '[:upper:]')
        fi
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        default_iface=$(route -n get default | grep interface | awk '{print $2}')
        if [ -z "$default_iface" ]; then
            default_iface="en0"
        fi
        mac_addr=$(ifconfig $default_iface | grep ether | awk '{print $2}' | tr '[:lower:]' '[:upper:]')
        
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows
        mac_addr=$(getmac /FO CSV /NH | head -1 | cut -d',' -f1 | tr -d '"' | tr '[:lower:]' '[:upper:]')
    fi
    
    echo "$mac_addr"
}

# Función para obtener hostname
get_hostname_info() {
    hostname | tr '[:lower:]' '[:upper:]'
}

# Función para generar HWID (hash SHA256)
generate_hwid() {
    local cpu="$1"
    local mac="$2"
    local hostname="$3"
    
    # Concatenar componentes
    local raw_hwid="${cpu}|${mac}|${hostname}"
    
    # Generar hash SHA256 y tomar primeros 16 caracteres
    if command -v sha256sum &> /dev/null; then
        echo -n "$raw_hwid" | sha256sum | cut -c1-16 | tr '[:lower:]' '[:upper:]'
    elif command -v shasum &> /dev/null; then
        echo -n "$raw_hwid" | shasum -a 256 | cut -c1-16 | tr '[:lower:]' '[:upper:]'
    else
        echo "ERROR: No se encontró sha256sum ni shasum" >&2
        exit 1
    fi
}

# ============================================================================
# OBTENER INFORMACIÓN DEL SISTEMA
# ============================================================================

echo -e "${YELLOW}📊 Recopilando información del sistema...${NC}\n"

# Sistema operativo
OS_INFO="$(uname -s) $(uname -r) $(uname -m)"

# CPU
CPU_INFO=$(get_cpu_info)
if [ -z "$CPU_INFO" ]; then
    CPU_INFO="Unknown CPU"
fi

# MAC Address
MAC_ADDR=$(get_primary_mac)
if [ -z "$MAC_ADDR" ]; then
    echo -e "${RED}❌ Error: No se pudo obtener la MAC address${NC}"
    exit 1
fi

# Hostname
HOSTNAME_INFO=$(get_hostname_info)
if [ -z "$HOSTNAME_INFO" ]; then
    HOSTNAME_INFO="UNKNOWN"
fi

# Generar HWID
HWID=$(generate_hwid "$CPU_INFO" "$MAC_ADDR" "$HOSTNAME_INFO")

# ============================================================================
# MOSTRAR RESULTADOS
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Sistema:${NC}  $OS_INFO"
echo -e "${GREEN}CPU:${NC}      $CPU_INFO"
echo -e "${GREEN}MAC:${NC}      $MAC_ADDR"
echo -e "${GREEN}Hostname:${NC} $HOSTNAME_INFO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}HWID:${NC}     ${YELLOW}${HWID}${NC}                                     ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ============================================================================
# INSTRUCCIONES
# ============================================================================

echo ""
echo -e "${YELLOW}📧 PRÓXIMOS PASOS:${NC}"
echo ""
echo "1. Envía el HWID a: licenses@rhinometric.com"
echo "2. Incluye en el email:"
echo "   - Nombre de tu empresa"
echo "   - Tipo de licencia (trial/annual/perpetual)"
echo "   - Duración (ej: 30 días, 1 año)"
echo ""
echo "3. Recibirás un archivo .lic por email"
echo "4. Copia el archivo .lic al servidor y ejecuta:"
echo "   ./install.sh --license-file tu-empresa.lic"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}⚠️  ESTE SCRIPT NO ENVÍA DATOS AUTOMÁTICAMENTE${NC}"
echo -e "${GREEN}⚠️  TÚ CONTROLAS TU INFORMACIÓN${NC}"
echo ""

# Opción para guardar en archivo
read -p "¿Deseas guardar esta información en un archivo? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[SsYy]$ ]]; then
    OUTPUT_FILE="rhinometric-hwid-$(date +%Y%m%d).txt"
    {
        echo "RHINOMETRIC Hardware ID Report"
        echo "=============================="
        echo ""
        echo "Fecha: $(date)"
        echo "Sistema: $OS_INFO"
        echo "CPU: $CPU_INFO"
        echo "MAC: $MAC_ADDR"
        echo "Hostname: $HOSTNAME_INFO"
        echo ""
        echo "HWID: $HWID"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Enviar a: licenses@rhinometric.com"
    } > "$OUTPUT_FILE"
    
    echo -e "${GREEN}✅ Información guardada en: $OUTPUT_FILE${NC}"
fi

echo ""
echo -e "${GREEN}✅ Proceso completado${NC}"
echo ""
