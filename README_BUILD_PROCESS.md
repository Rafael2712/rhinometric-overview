# 🦏 Rhinometric Trial - Proceso de Build

Este documento describe cómo generar los paquetes de distribución de Rhinometric Trial v2.0.

---

## 📋 Requisitos Previos

- **Git Bash** o cualquier shell bash en Windows
- **Docker** instalado y ejecutándose (para validación)
- **PowerShell** (para crear ZIPs en Windows)
- Todos los archivos de configuración presentes en el proyecto

---

## 🚀 Generación de Paquetes

### Ejecutar el Script de Build

```bash
bash create-trial-package.sh
```

### Proceso Automático (10 pasos)

El script ejecuta automáticamente los siguientes pasos:

1. **Validación Pre-Build**
   - Verifica que todos los archivos requeridos existan
   - Valida sintaxis de `docker-compose-trial.yml`
   - Genera logs de validación

2. **Generación Paquete Windows**
   - Copia archivos base
   - Genera scripts `.bat` nativos
   - Crea README específico para Windows

3. **Generación Paquete macOS**
   - Copia archivos base
   - Genera scripts `.sh` con permisos de ejecución
   - Crea README específico para macOS (Intel + Apple Silicon)

4. **Generación Paquete Linux**
   - Copia archivos base
   - Genera scripts `.sh` con permisos de ejecución
   - Crea README específico para Linux (Ubuntu/Debian/RHEL)

5. **Empaquetado Windows**
   - Crea ZIP usando PowerShell
   - Calcula tamaño

6. **Empaquetado macOS**
   - Crea ZIP usando PowerShell (o tar.gz si no disponible)
   - Calcula tamaño

7. **Empaquetado Linux**
   - Crea ZIP usando PowerShell (o tar.gz si no disponible)
   - Calcula tamaño

8. **Validación de Paquetes**
   - Verifica existencia de ZIPs
   - Lista contenido de cada paquete
   - Cuenta archivos (41 esperados por paquete)
   - Genera `build_logs/validation_*.txt`

9. **Generación de Checksums**
   - Calcula SHA256 de cada ZIP
   - Guarda en `build/checksums.txt`

10. **Limpieza y Resumen**
    - Elimina archivos temporales
    - Muestra resumen completo

---

## 📂 Estructura de Salida

Después de ejecutar el script, se generan los siguientes archivos:

```
build/
├── rhinometric-trial-v2.0.0-windows.zip  (49K)
├── rhinometric-trial-v2.0.0-mac.zip      (48K)
├── rhinometric-trial-v2.0.0-linux.zip    (49K)
├── checksums.txt                         (SHA256 de cada ZIP)
└── RELEASE_NOTES_v2.0.0.md               (Notas de lanzamiento)

build_logs/
├── build_YYYYMMDD_HHMMSS.log             (Log detallado del build)
└── validation_YYYYMMDD_HHMMSS.txt        (Log de validación de paquetes)
```

---

## 🔍 Validación Manual

### Verificar Checksums

```bash
cat build/checksums.txt
```

### Listar Contenido de un Paquete

```bash
unzip -l build/rhinometric-trial-v2.0.0-windows.zip
```

### Verificar Sintaxis Docker Compose

```bash
docker compose -f docker-compose-trial.yml config
```

---

## 📊 Contenido de Cada Paquete

Todos los paquetes contienen **41 archivos**:

### Archivos Base (comunes a todos)
- `docker-compose.yml` - 16 servicios configurados
- `.env` - Variables de entorno y credenciales

### Configuraciones (8 archivos)
- `config/prometheus-saas.yml`
- `config/loki-saas.yml`
- `config/tempo-saas.yml`
- `config/alertmanager-saas.yml`
- `config/promtail-config.yml`
- `config/nginx-trial.conf`
- `config/blackbox.yml`
- `config/rules/alerts.yml` - 16 reglas de alertas

### Grafana Provisioning
- `grafana/provisioning/datasources/datasources.yml`
- `grafana/provisioning/dashboards/dashboards.yml`
- `grafana/provisioning/dashboards/json/` - 7 dashboards:
  - overview.json
  - distributed-tracing.json
  - docker-containers.json
  - logs-explorer.json
  - system-monitoring.json
  - license-status.json
  - (+ archivos .bak)

### Licensing
- `licensing/Dockerfile`
- `licensing/license_server.py`
- `licensing/scripts/` - Scripts auxiliares

### License Dashboard
- `license-dashboard/Dockerfile`
- `license-dashboard/app.py`
- `license-dashboard/templates/index.html`

### Init Scripts
- `init-db/01-init-saas.sh` - Inicialización de PostgreSQL

### Licenses
- `licenses/license.key`
- `licenses/licenses.db`

### Scripts Nativos (varían por OS)

**Windows:**
- `start.bat`
- `stop.bat`
- `validate.bat`

**macOS / Linux:**
- `start.sh` (chmod +x)
- `stop.sh` (chmod +x)
- `validate.sh` (chmod +x)

### Documentación
- `README.md` - Específico para cada OS

---

## 🛠️ Modificar el Script de Build

El archivo `create-trial-package.sh` está organizado en funciones:

```bash
# Función para copiar archivos base (usada por los 3 paquetes)
copy_base_files() {
    local TARGET_DIR="$1"
    local OS_NAME="$2"
    # ... código ...
}
```

### Variables de Configuración

Al inicio del script:

```bash
VERSION="2.0.0"              # Versión del paquete
BUILD_DIR="build"            # Directorio de salida
LOG_DIR="build_logs"         # Directorio de logs
TEMP_DIR="temp-build"        # Directorio temporal
```

### Personalizar Scripts por OS

Los scripts nativos se generan con heredocs:

```bash
# Ejemplo: start.bat para Windows
cat > "$WIN_DIR/start.bat" << 'EOF'
@echo off
echo Iniciando Rhinometric...
docker compose up -d
EOF
```

---

## 🐛 Troubleshooting del Build

### Error: "docker-compose-trial.yml no existe"

Asegúrese de ejecutar el script desde el directorio raíz del proyecto:

```bash
cd /c/Users/canel/mi-proyecto/infrastructure/mi-proyecto
bash create-trial-package.sh
```

### Error: "PowerShell no encontrado"

El script usa PowerShell para crear ZIPs en Windows. Si no está disponible, fallback a tar.gz.

### Error: "docker compose config failed"

Verifique que Docker esté instalado y ejecutándose:

```bash
docker --version
docker compose version
```

### Error: "Permission denied"

De permisos de ejecución al script:

```bash
chmod +x create-trial-package.sh
```

---

## 📝 Logs y Debugging

### Ver Log Completo del Build

```bash
cat build_logs/build_YYYYMMDD_HHMMSS.log
```

### Ver Log de Validación

```bash
cat build_logs/validation_YYYYMMDD_HHMMSS.txt
```

### Ejecutar con Debug Verbose

```bash
bash -x create-trial-package.sh
```

---

## 🔄 Proceso de Desarrollo

### 1. Hacer Cambios en el Proyecto

Modifique archivos de configuración, dashboards, etc.

### 2. Actualizar Versión

Edite `create-trial-package.sh`:

```bash
VERSION="2.1.0"  # Nueva versión
```

### 3. Generar Paquetes

```bash
bash create-trial-package.sh
```

### 4. Validar Paquetes

```bash
# Extraer y probar en cada OS
unzip build/rhinometric-trial-v2.1.0-windows.zip -d test/
cd test/rhinometric-trial-v2.1.0-windows
docker compose up -d
```

### 5. Distribuir

Subir los ZIPs a GitHub Releases, S3, etc.

---

## ✅ Checklist Pre-Distribución

Antes de distribuir los paquetes, verificar:

- [ ] Sintaxis `docker-compose.yml` válida
- [ ] Credenciales correctas en `.env`
- [ ] 41 archivos presentes en cada paquete
- [ ] Checksums SHA256 generados
- [ ] Scripts nativos tienen permisos correctos
- [ ] README específico por OS actualizado
- [ ] Versión correcta en todos los archivos
- [ ] Logs de validación sin errores
- [ ] Paquetes probados en al menos 2 sistemas operativos

---

## 📞 Soporte

Para preguntas sobre el proceso de build:

- Revisar logs en `build_logs/`
- Consultar `RELEASE_NOTES_v2.0.0.md`
- Verificar sintaxis docker-compose manualmente

---

**Script:** `create-trial-package.sh` v2.0  
**Última actualización:** 24 de Octubre, 2025
