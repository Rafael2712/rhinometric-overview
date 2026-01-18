#!/usr/bin/env python3
"""
Actualizar enlaces en el servidor de licencias con URLs de GitHub
"""
import sys

REPO = "Rafael2712/rhinometric-overview"
BRANCH = "main"

# URLs directas a los archivos en GitHub (raw)
INSTALLER_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/installers/install-rhinometric.sh"
MANUAL_INSTALACION_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/docs/guia_instalacion.md"
MANUAL_USUARIO_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/docs/manual_usuario.md"

print("📝 URLs que se usarán:")
print(f"Instalador: {INSTALLER_URL}")
print(f"Guía Instalación: {MANUAL_INSTALACION_URL}")
print(f"Manual Usuario: {MANUAL_USUARIO_URL}")
print()

# Crear script para actualizar en el servidor
update_script = f"""#!/bin/bash
# Actualizar enlaces en main.py del License Server

cd /home/ubuntu/license-server/app

# Backup
cp main.py main.py.backup-$(date +%Y%m%d-%H%M%S)

# Actualizar URL del instalador (línea 354)
sed -i 's|https://drive.google.com/drive/folders/[^"]*|{INSTALLER_URL}|g' main.py

# Actualizar URL del manual de instalación (línea 360)
sed -i 's|https://drive.google.com/file/d/1aiwBdrvYnF-frvgVb_G9TuQj9yz0nfud/view?usp=sharing|{MANUAL_INSTALACION_URL}|g' main.py

# Actualizar URL del manual de usuario (línea 361)
sed -i 's|https://drive.google.com/file/d/1Iuo9Bm3rRX13mrcZ1dh40Zg2m8npGS2I/view?usp=sharing|{MANUAL_USUARIO_URL}|g' main.py

echo "✅ Enlaces actualizados en main.py"

# Verificar cambios
echo ""
echo "📋 Verificando enlaces nuevos:"
grep -n "raw.githubusercontent.com" main.py | head -5

# Reiniciar contenedor
echo ""
echo "🔄 Reiniciando contenedor..."
cd /home/ubuntu/license-server
docker compose restart license-api

echo ""
echo "✅ Actualización completada"
"""

# Guardar script
with open('/tmp/update-links.sh', 'w') as f:
    f.write(update_script)

print("✅ Script creado en /tmp/update-links.sh")
print()
print("Ahora ejecutando en el servidor...")
