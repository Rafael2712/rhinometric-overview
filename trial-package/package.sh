#!/bin/bash

# ════════════════════════════════════════════════════════════════════════════
# RHINOMETRIC TRIAL - SCRIPT DE EMPAQUETADO AUTOMÁTICO
# Crea el ZIP final listo para distribución
# ════════════════════════════════════════════════════════════════════════════

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  📦 RHINOMETRIC TRIAL - EMPAQUETADOR AUTOMÁTICO${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Limpiar archivos temporales
echo -e "${YELLOW}[1/5]${NC} Limpiando archivos temporales..."
rm -rf data/ licenses/ .env credentials.txt *.log 2>/dev/null || true
echo -e "${GREEN}✅${NC} Limpieza completada"
echo ""

# Validar paquete
echo -e "${YELLOW}[2/5]${NC} Validando estructura del paquete..."
if [ -f "validate.sh" ]; then
    chmod +x validate.sh
    if ./validate.sh; then
        echo -e "${GREEN}✅${NC} Validación exitosa"
    else
        echo -e "${RED}❌${NC} Validación falló - revisa los errores arriba"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️${NC}  validate.sh no encontrado, continuando..."
fi
echo ""

# Asegurar permisos
echo -e "${YELLOW}[3/5]${NC} Configurando permisos..."
chmod +x start-trial.sh 2>/dev/null || true
chmod +x validate.sh 2>/dev/null || true
echo -e "${GREEN}✅${NC} Permisos configurados"
echo ""

# Determinar versión
echo -e "${YELLOW}[4/5]${NC} Determinando versión..."
VERSION="1.0.0"
if [ -f "VERSION" ]; then
    VERSION=$(cat VERSION)
fi
echo -e "${GREEN}✅${NC} Versión: ${VERSION}"
echo ""

# Crear paquete
echo -e "${YELLOW}[5/5]${NC} Creando paquete comprimido..."

# Nombre del paquete
PACKAGE_NAME="rhinometric-trial-v${VERSION}"
TIMESTAMP=$(date +%Y%m%d)

cd ..

# Renombrar directorio temporal si es necesario
ORIGINAL_DIR=$(basename "$PWD/trial-package")
if [ "$ORIGINAL_DIR" != "rhinometric-trial" ]; then
    cp -r trial-package rhinometric-trial-temp
    WORK_DIR="rhinometric-trial-temp"
else
    WORK_DIR="trial-package"
fi

# Crear ZIP
echo "   Creando ZIP..."
zip -r "${PACKAGE_NAME}.zip" "${WORK_DIR}/" \
    -x "${WORK_DIR}/data/*" \
    -x "${WORK_DIR}/licenses/*" \
    -x "${WORK_DIR}/.env" \
    -x "${WORK_DIR}/credentials.txt" \
    -x "${WORK_DIR}/*.log" \
    -x "${WORK_DIR}/.git/*" \
    -x "${WORK_DIR}/.DS_Store" \
    -q

# Limpiar temporal
if [ "$WORK_DIR" = "rhinometric-trial-temp" ]; then
    rm -rf rhinometric-trial-temp
fi

# Verificar creación
if [ -f "${PACKAGE_NAME}.zip" ]; then
    SIZE=$(ls -lh "${PACKAGE_NAME}.zip" | awk '{print $5}')
    echo -e "${GREEN}✅${NC} Paquete creado: ${PACKAGE_NAME}.zip"
    echo -e "   Tamaño: ${SIZE}"
    
    # Calcular checksum
    if command -v shasum &> /dev/null; then
        CHECKSUM=$(shasum -a 256 "${PACKAGE_NAME}.zip" | awk '{print $1}')
        echo -e "   SHA256: ${CHECKSUM}"
        echo "${CHECKSUM}" > "${PACKAGE_NAME}.zip.sha256"
    fi
else
    echo -e "${RED}❌${NC} Error al crear el paquete"
    exit 1
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ PAQUETE CREADO EXITOSAMENTE${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📦 Archivo:${NC} ${PACKAGE_NAME}.zip"
echo -e "${BLUE}📏 Tamaño:${NC} ${SIZE}"
echo -e "${BLUE}📍 Ubicación:${NC} $(pwd)/${PACKAGE_NAME}.zip"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo "  1. Probar el paquete en un Mac limpio"
echo "  2. Enviar a cliente vía email/WeTransfer"
echo "  3. O subir a GitHub/S3 para distribución"
echo ""
echo -e "${BLUE}Instrucciones para el cliente:${NC}"
echo "  unzip ${PACKAGE_NAME}.zip"
echo "  cd rhinometric-trial"
echo "  ./start-trial.sh"
echo ""
