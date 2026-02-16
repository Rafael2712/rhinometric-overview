#!/bin/bash
set -e

echo "╔══════════════════════════════════════════╗"
echo "║    Rhinometric Platform - Instalador    ║"
echo "╚══════════════════════════════════════════╝"

# Verificaciones
check_requirements() {
    echo "🔍 Verificando requisitos..."
    
    # Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker no instalado"
        exit 1
    fi
    
    # Memoria
    MEM=$(free -m | awk '/^Mem:/{print $2}')
    if [ "$MEM" -lt 4096 ]; then
        echo "⚠️  Memoria insuficiente (mínimo 4GB)"
    fi
    
    # Licencia
    if [ ! -f "license.lic" ]; then
        echo "❌ Archivo license.lic no encontrado"
        exit 1
    fi
    
    echo "✅ Requisitos cumplidos"
}

# Fingerprinting del sistema
get_system_fingerprint() {
    HOSTNAME=$(hostname)
    KERNEL=$(uname -r)
    DOCKER_ID=$(docker info --format '{{.ID}}' 2>/dev/null || echo "unknown")
    
    FINGERPRINT=$(echo "$HOSTNAME-$KERNEL-$DOCKER_ID" | sha256sum | cut -d' ' -f1)
    echo "$FINGERPRINT"
}

# Instalación
install() {
    echo "📦 Descargando imagen segura..."
    docker pull rhinometric/platform:secure || {
        echo "❌ Error descargando imagen"
        exit 1
    }
    
    # Registrar instalación
    FINGERPRINT=$(get_system_fingerprint)
    echo "🔑 Sistema ID: ${FINGERPRINT:0:8}..."
    
    # Crear contenedor
    docker run -d \
        --name rhinometric \
        --restart unless-stopped \
        -p 127.0.0.1:80:80 \
        -v $(pwd)/license.lic:/license/license.lic:ro \
        -e SYSTEM_ID="$FINGERPRINT" \
        --memory="2g" \
        --cpus="1.5" \
        rhinometric/platform:secure
    
    echo "⏳ Iniciando servicios..."
    sleep 30
    
    # Verificar
    if curl -sf http://localhost/health > /dev/null; then
        echo ""
        echo "✅ INSTALACIÓN COMPLETADA"
        echo "══════════════════════════════════"
        echo "URL: http://localhost"
        echo "Usuario: admin"
        echo "Contraseña: (ver email de activación)"
        echo "══════════════════════════════════"
    else
        echo "❌ Error al iniciar. Verificar: docker logs rhinometric"
        exit 1
    fi
}

# Main
check_requirements
install
