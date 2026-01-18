# Pasos para subir los archivos a GitHub

## 1. Clonar o actualizar el repositorio rhinometric-overview

```bash
cd c:\Users\canel
git clone https://github.com/Rafael2712/rhinometric-overview.git
# O si ya lo tienes clonado:
# cd rhinometric-overview
# git pull
```

## 2. Crear las carpetas necesarias

```bash
cd rhinometric-overview
mkdir -p docs
mkdir -p installers
```

## 3. Copiar los archivos

```bash
# Manual de Usuario
cp "c:\Users\canel\mi-proyecto\infrastructure\mi-proyecto\rhinometric-trial-v2.1.0-universal\docs\manual_usuario.md" docs/

# Guía de Instalación
cp "c:\Users\canel\mi-proyecto\infrastructure\mi-proyecto\rhinometric-trial-v2.1.0-universal\docs\guia_instalacion.md" docs/

# Script de Instalación
cp "c:\Users\canel\mi-proyecto\infrastructure\mi-proyecto\install-rhinometric.sh" installers/
```

## 4. Subir a GitHub

```bash
git add docs/manual_usuario.md
git add docs/guia_instalacion.md
git add installers/install-rhinometric.sh
git commit -m "Add Rhinometric documentation and installer

- Manual de Usuario (español)
- Guía de Instalación (español)
- Script de instalación automatizado para Linux"

git push origin main
```

## 5. Verificar que los archivos están disponibles

Una vez subidos, los archivos estarán disponibles en:
- https://raw.githubusercontent.com/Rafael2712/rhinometric-overview/main/docs/manual_usuario.md
- https://raw.githubusercontent.com/Rafael2712/rhinometric-overview/main/docs/guia_instalacion.md
- https://raw.githubusercontent.com/Rafael2712/rhinometric-overview/main/installers/install-rhinometric.sh

## 6. Probar los enlaces

```bash
# Probar descarga del instalador
curl -O https://raw.githubusercontent.com/Rafael2712/rhinometric-overview/main/installers/install-rhinometric.sh

# Probar descarga del manual
curl -O https://raw.githubusercontent.com/Rafael2712/rhinometric-overview/main/docs/manual_usuario.md
```

¡Los enlaces en el servidor de licencias ya están actualizados! Solo falta que subas los archivos.
