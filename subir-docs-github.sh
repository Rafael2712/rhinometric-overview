#!/bin/bash
# Script para subir documentación de Rhinometric a GitHub Releases

REPO="rhinometric/rhinometric-platform"
VERSION="v2.5.0"
RELEASE_NAME="Rhinometric v2.5.0 - Documentación y Scripts"
RELEASE_NOTES="
# Rhinometric v2.5.0 - Documentación Completa

## 📥 Archivos Disponibles

### 📚 Documentación
- **Manual de Usuario** (español) - Guía completa de uso de la plataforma
- **Guía de Instalación** (español) - Instrucciones paso a paso para instalar Rhinometric

### 🛠️ Scripts de Instalación
- **install-rhinometric.sh** - Script automatizado de instalación para Linux

## 🚀 Instalación Rápida

\`\`\`bash
wget https://github.com/${REPO}/releases/download/${VERSION}/install-rhinometric.sh
chmod +x install-rhinometric.sh
sudo ./install-rhinometric.sh
\`\`\`

## 📖 Documentación

- [Manual de Usuario (PDF)](https://github.com/${REPO}/releases/download/${VERSION}/manual-usuario-rhinometric.pdf)
- [Guía de Instalación (PDF)](https://github.com/${REPO}/releases/download/${VERSION}/guia-instalacion-rhinometric.pdf)

## 📞 Soporte

- Email: rafael.canelon@rhinometric.com
- Web: https://rhinometric.com
"

echo "🚀 Creando Release ${VERSION} en GitHub..."

# Verificar que gh esté instalado
if ! command -v gh &> /dev/null; then
    echo "❌ Error: GitHub CLI (gh) no está instalado"
    echo "Instala con: winget install GitHub.cli"
    exit 1
fi

# Verificar autenticación
if ! gh auth status &> /dev/null; then
    echo "❌ Error: No estás autenticado en GitHub"
    echo "Ejecuta: gh auth login"
    exit 1
fi

# Crear el release si no existe
echo "📦 Creando release ${VERSION}..."
gh release create ${VERSION} \
    --repo ${REPO} \
    --title "${RELEASE_NAME}" \
    --notes "${RELEASE_NOTES}" \
    --draft \
    || echo "Release ya existe, continuando..."

# Subir archivos
echo "📤 Subiendo Manual de Usuario..."
gh release upload ${VERSION} \
    "rhinometric-trial-v2.1.0-universal/docs/manual_usuario.md" \
    --repo ${REPO} \
    --clobber

echo "📤 Subiendo Guía de Instalación..."
gh release upload ${VERSION} \
    "rhinometric-trial-v2.1.0-universal/docs/guia_instalacion.md" \
    --repo ${REPO} \
    --clobber

echo "📤 Subiendo Script de Instalación..."
gh release upload ${VERSION} \
    "install-rhinometric.sh" \
    --repo ${REPO} \
    --clobber

echo ""
echo "✅ Archivos subidos correctamente"
echo ""
echo "📋 URLs de descarga:"
echo "Manual Usuario: https://github.com/${REPO}/releases/download/${VERSION}/manual_usuario.md"
echo "Guía Instalación: https://github.com/${REPO}/releases/download/${VERSION}/guia_instalacion.md"
echo "Script Instalación: https://github.com/${REPO}/releases/download/${VERSION}/install-rhinometric.sh"
echo ""
echo "🔓 Para publicar el release (hacerlo público):"
echo "gh release edit ${VERSION} --repo ${REPO} --draft=false"
