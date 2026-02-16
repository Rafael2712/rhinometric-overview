#!/bin/bash
# Script de Instalación y Ejecución FINAL de la Plataforma Segura

# Configuración
IMAGE_NAME="rhinometric/platform:secure"
LICENSE_PATH="./security/licensing/license.lic"
VALIDATOR_DIR="./security/licensing/dist"

echo "╔══════════════════════════════════════════╗"
echo "║   Rhinometric Platform - Instalador FINAL  ║"
echo "╚══════════════════════════════════════════╝"

# --- Paso 1: Verificación de Requisitos y Limpieza ---
echo "🔍 Verificando requisitos..."
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker no está instalado."
    exit 1
fi

# Verificar la existencia de archivos clave
if [ ! -f "$LICENSE_PATH" ]; then
    echo "❌ Error: Archivo de licencia no encontrado. Debe existir en $LICENSE_PATH"
    exit 1
fi
if [ ! -d "$VALIDATOR_DIR" ]; then
    echo "❌ Error: El directorio del validador ($VALIDATOR_DIR) no existe."
    exit 1
fi

# Limpiar el contenedor anterior que pudo haber fallado
docker rm -f rhinometric > /dev/null 2>&1
echo "✅ Requisitos cumplidos y contenedor anterior limpiado."

# --- Paso 2: Construcción de la Imagen (Se usará el cache si no hay cambios) ---
echo "📦 Construyendo imagen segura con configuraciones corregidas..."
if ! docker build -f Dockerfile.secure -t "$IMAGE_NAME" .; then
    echo "❌ Error construyendo la imagen Docker. (Revisa tu login si no usa cache)."
    exit 1
fi

# --- Paso 3: Ejecución del Contenedor con Puerto Aleatorio y Montaje de Licencia ---
echo "🚀 Iniciando contenedor en puerto aleatorio (Docker buscará uno libre)..."

# Generar un puerto aleatorio entre 10000 y 65535
RANDOM_PORT=$(shuf -i 10000-65535 -n 1)

# Comando DOCKER RUN: Monta la licencia en /license/license.lic
CONTAINER_ID=$(docker run -d \
    --name rhinometric \
    -p 127.0.0.1:$RANDOM_PORT:80 \
    -v "$(pwd)/$LICENSE_PATH":/license/license.lic \
    "$IMAGE_NAME")

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ Error: No se pudo iniciar el contenedor Docker."
    exit 1
fi
echo "ID del Contenedor: $CONTAINER_ID"

echo "⏳ Esperando 10 segundos para la validación..."
sleep 10

# --- Paso 4: Verificación del Estado de la Validación ---
# Buscar la cadena que el validador SIMULADO imprime y que el entrypoint detecta.
LOGS=$(docker logs "$CONTAINER_ID")
VALID_CHECK=$(echo "$LOGS" | grep "LICENCIA VÁLIDA. Servicio iniciado.")

echo "--- LOGS DE VALIDACIÓN ---"
echo "$LOGS" | tail -n 10
echo "--------------------------"

if [ -n "$VALID_CHECK" ]; then
    echo "🎉 VALIDACIÓN DE LICENCIA EXITOSA. El servicio pasó la prueba de seguridad."
    # CORRECCIÓN FINAL: Usamos la variable $RANDOM_PORT conocida, no docker inspect.
    echo "URL potencial: http://127.0.0.1:$RANDOM_PORT"
    EXIT_CODE=0
else
    echo "❌ VALIDACIÓN DE LICENCIA FALLIDA. El contenedor no reportó el mensaje de éxito."
    EXIT_CODE=1
fi

# --- Paso 5: Limpieza ---
echo "🧹 Deteniendo y eliminando contenedor: $CONTAINER_ID"
docker rm -f "$CONTAINER_ID" > /dev/null 2>&1

exit $EXIT_CODE
