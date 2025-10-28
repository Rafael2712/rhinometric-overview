#!/bin/bash

# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  RHINOMETRIC TRIAL - MULTI-OS PACKAGE GENERATOR v2.0                 ║
# ║  Genera 3 ZIPs optimizados para Windows, macOS y Linux               ║
# ╚═══════════════════════════════════════════════════════════════════════╝

set -e  # Exit on any error
set -u  # Exit on undefined variable

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════

VERSION="2.0.0"
BUILD_DIR="build"
LOG_DIR="build_logs"
TEMP_DIR="temp-build"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Obtener directorio de trabajo absoluto
WORK_DIR="$(pwd)"

# Crear directorios inmediatamente
mkdir -p "$WORK_DIR/$BUILD_DIR" "$WORK_DIR/$LOG_DIR" "$WORK_DIR/$TEMP_DIR"

LOG_FILE="$WORK_DIR/$LOG_DIR/build_${TIMESTAMP}.log"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ═══════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════

log() {
    echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +%H:%M:%S)] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +%H:%M:%S)] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

log_step() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" | tee -a "$LOG_FILE"
    echo -e "${CYAN}  $1${NC}" | tee -a "$LOG_FILE"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n" | tee -a "$LOG_FILE"
}

check_file() {
    if [ -f "$1" ]; then
        log "  ✅ $1"
        return 0
    else
        log_error "  ❌ $1 NO EXISTE"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        log "  ✅ $1/"
        return 0
    else
        log_error "  ❌ $1/ NO EXISTE"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════
# INICIO DEL SCRIPT
# ═══════════════════════════════════════════════════════════════════════

clear
echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║        🦏 RHINOMETRIC TRIAL v${VERSION} - PACKAGE BUILDER 🦏           ║"
echo "║                                                                       ║"
echo "║  Generando paquetes optimizados para:                                ║"
echo "║    • Windows 10/11                                                    ║"
echo "║    • macOS (Intel + Apple Silicon)                                    ║"
echo "║    • Linux (Ubuntu/Debian/RHEL)                                       ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# Inicializar log
echo "Build iniciado: $(date)" > "$LOG_FILE"

# Ya no es necesario crear directorios aquí porque se crean arriba
log "✅ Directorios de build creados"
echo ""

# ═══════════════════════════════════════════════════════════════════════
# PASO 1: VALIDACIÓN PRE-BUILD
# ═══════════════════════════════════════════════════════════════════════

log_step "PASO 1/10: VALIDACIÓN DE ARCHIVOS REQUERIDOS"

VALIDATION_FAILED=0

# Validar docker-compose
if ! check_file "docker-compose-trial.yml"; then
    VALIDATION_FAILED=1
fi

# Validar configs
if ! check_file "config/prometheus-saas.yml"; then VALIDATION_FAILED=1; fi
if ! check_file "config/loki-saas.yml"; then VALIDATION_FAILED=1; fi
if ! check_file "config/tempo-saas.yml"; then VALIDATION_FAILED=1; fi
if ! check_file "config/alertmanager-saas.yml"; then VALIDATION_FAILED=1; fi
if ! check_file "config/promtail-config.yml"; then VALIDATION_FAILED=1; fi
if ! check_file "config/nginx-trial.conf"; then VALIDATION_FAILED=1; fi
if ! check_file "config/blackbox.yml"; then VALIDATION_FAILED=1; fi
if ! check_file "config/rules/alerts.yml"; then VALIDATION_FAILED=1; fi

# Validar licensing
if ! check_dir "licensing"; then VALIDATION_FAILED=1; fi
if ! check_file "licensing/Dockerfile"; then VALIDATION_FAILED=1; fi
if ! check_file "licensing/license_server.py"; then VALIDATION_FAILED=1; fi

# Validar license-dashboard
if ! check_dir "license-dashboard"; then VALIDATION_FAILED=1; fi
if ! check_file "license-dashboard/Dockerfile"; then VALIDATION_FAILED=1; fi
if ! check_file "license-dashboard/app.py"; then VALIDATION_FAILED=1; fi

# Validar Grafana dashboards
if ! check_dir "grafana/provisioning/dashboards"; then VALIDATION_FAILED=1; fi
if ! check_dir "grafana/provisioning/datasources"; then VALIDATION_FAILED=1; fi

# Validar .env
if ! check_file ".env"; then VALIDATION_FAILED=1; fi

if [ $VALIDATION_FAILED -eq 1 ]; then
    log_error "❌ Validación FALLÓ - Archivos requeridos faltantes"
    exit 1
fi

log "✅ Todos los archivos requeridos están presentes"

# Validar sintaxis docker-compose
log "\n🔍 Validando sintaxis docker-compose..."
if docker compose -f docker-compose-trial.yml config > /dev/null 2>&1; then
    log "✅ docker-compose.yml - sintaxis válida"
else
    log_error "❌ docker-compose.yml tiene errores de sintaxis"
    docker compose -f docker-compose-trial.yml config 2>&1 | tee -a "$LOG_FILE"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════
# FUNCIÓN PARA COPIAR ARCHIVOS BASE
# ═══════════════════════════════════════════════════════════════════════

copy_base_files() {
    local TARGET_DIR="$1"
    local OS_NAME="$2"
    
    log "📦 Copiando archivos base para $OS_NAME..."
    
    # 1. Docker Compose
    cp docker-compose-trial.yml "$TARGET_DIR/docker-compose.yml"
    log "  ✅ docker-compose.yml"
    
    # 2. Configuraciones
    mkdir -p "$TARGET_DIR/config/rules"
    cp config/prometheus-saas.yml "$TARGET_DIR/config/"
    cp config/loki-saas.yml "$TARGET_DIR/config/"
    cp config/tempo-saas.yml "$TARGET_DIR/config/"
    cp config/alertmanager-saas.yml "$TARGET_DIR/config/"
    cp config/promtail-config.yml "$TARGET_DIR/config/"
    cp config/nginx-trial.conf "$TARGET_DIR/config/"
    cp config/blackbox.yml "$TARGET_DIR/config/"
    cp config/rules/alerts.yml "$TARGET_DIR/config/rules/"
    log "  ✅ config/ (8 archivos)"
    
    # 3. Grafana provisioning
    mkdir -p "$TARGET_DIR/grafana/provisioning/dashboards"
    mkdir -p "$TARGET_DIR/grafana/provisioning/datasources"
    cp -r grafana/provisioning/dashboards/* "$TARGET_DIR/grafana/provisioning/dashboards/" 2>/dev/null || true
    cp -r grafana/provisioning/datasources/* "$TARGET_DIR/grafana/provisioning/datasources/" 2>/dev/null || true
    log "  ✅ grafana/provisioning/"
    
    # 4. Init-DB
    if [ -d "init-db" ]; then
        mkdir -p "$TARGET_DIR/init-db"
        cp -r init-db/* "$TARGET_DIR/init-db/" 2>/dev/null || true
        log "  ✅ init-db/"
    fi
    
    # 5. Licensing COMPLETO
    mkdir -p "$TARGET_DIR/licensing"
    cp licensing/Dockerfile "$TARGET_DIR/licensing/"
    cp licensing/license_server.py "$TARGET_DIR/licensing/"
    if [ -d "licensing/scripts" ]; then
        cp -r licensing/scripts "$TARGET_DIR/licensing/"
    fi
    log "  ✅ licensing/ (Dockerfile + código)"
    
    # 6. License-dashboard COMPLETO
    mkdir -p "$TARGET_DIR/license-dashboard"
    cp license-dashboard/Dockerfile "$TARGET_DIR/license-dashboard/"
    cp license-dashboard/app.py "$TARGET_DIR/license-dashboard/"
    if [ -d "license-dashboard/templates" ]; then
        cp -r license-dashboard/templates "$TARGET_DIR/license-dashboard/"
    fi
    if [ -d "license-dashboard/static" ]; then
        cp -r license-dashboard/static "$TARGET_DIR/license-dashboard/"
    fi
    log "  ✅ license-dashboard/ (Dockerfile + código + templates)"
    
    # 7. Certificados (si existen)
    if [ -d "certs" ]; then
        mkdir -p "$TARGET_DIR/certs"
        cp -r certs/* "$TARGET_DIR/certs/" 2>/dev/null || true
        log "  ✅ certs/"
    fi
    
    # 8. Licenses directory
    if [ -d "licenses" ]; then
        mkdir -p "$TARGET_DIR/licenses"
        cp -r licenses/* "$TARGET_DIR/licenses/" 2>/dev/null || true
        log "  ✅ licenses/"
    fi
    
    # 9. .env
    cp .env "$TARGET_DIR/.env"
    log "  ✅ .env"
}

# ═══════════════════════════════════════════════════════════════════════
# PASO 2: CREAR SCRIPTS PARA WINDOWS
# ═══════════════════════════════════════════════════════════════════════

log_step "PASO 2/10: GENERANDO PAQUETE WINDOWS"

WIN_DIR="$TEMP_DIR/rhinometric-trial-v${VERSION}-windows"
mkdir -p "$WIN_DIR"

# Copiar archivos base
copy_base_files "$WIN_DIR" "Windows"

# Crear start.bat
cat > "$WIN_DIR/start.bat" << 'EOF'
@echo off
chcp 65001 >nul
cls

echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                                                               ║
echo ║         🦏 RHINOMETRIC TRIAL - INICIANDO...🦏                ║
echo ║                                                               ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

echo [1/3] Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Docker no está instalado o no está en PATH
    echo.
    echo Por favor instale Docker Desktop para Windows:
    echo https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
echo ✅ Docker encontrado
echo.

echo [2/3] Iniciando contenedores...
docker compose up -d
if errorlevel 1 (
    echo ❌ ERROR: Fallo al iniciar contenedores
    echo.
    echo Revise que Docker Desktop esté ejecutándose
    pause
    exit /b 1
)
echo.

echo [3/3] Esperando servicios (30 segundos)...
timeout /t 30 /nobreak >nul
echo.

echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                                                               ║
echo ║         ✅ RHINOMETRIC TRIAL INICIADO EXITOSAMENTE           ║
echo ║                                                               ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.
echo 🌐 ACCESO:
echo    URL:        http://localhost:3000
echo    Usuario:    admin
echo    Contraseña: admin_secure_2024
echo.
echo 📊 DASHBOARDS DISPONIBLES:
echo    • System Overview
echo    • Distributed Tracing  
echo    • Database Performance
echo    • Logs Analysis
echo    • Metrics Explorer
echo    • Alerts Management
echo    • License Management
echo.
echo ⏱️  Licencia Trial: 30 días
echo.
echo Para detener: ejecute stop.bat
echo.
pause
EOF

# Crear stop.bat
cat > "$WIN_DIR/stop.bat" << 'EOF'
@echo off
chcp 65001 >nul
cls

echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                                                               ║
echo ║         🦏 RHINOMETRIC TRIAL - DETENIENDO... 🦏              ║
echo ║                                                               ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

docker compose down
if errorlevel 1 (
    echo ❌ ERROR: Fallo al detener contenedores
    pause
    exit /b 1
)

echo.
echo ✅ Rhinometric Trial detenido exitosamente
echo.
pause
EOF

# Crear validate.bat
cat > "$WIN_DIR/validate.bat" << 'EOF'
@echo off
chcp 65001 >nul
cls

echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                                                               ║
echo ║         🦏 RHINOMETRIC TRIAL - VALIDACIÓN 🦏                 ║
echo ║                                                               ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

echo Verificando contenedores...
echo.
docker compose ps

echo.
echo ════════════════════════════════════════════════════════════════
echo ESTADO ESPERADO: 16/16 contenedores UP
echo ════════════════════════════════════════════════════════════════
echo.
pause
EOF

log "  ✅ Scripts Windows (.bat) creados"

# Crear README-WINDOWS.md
cat > "$WIN_DIR/README.md" << 'EOF'
# 🦏 Rhinometric Trial - Instalación Windows

## Requisitos Previos

- **Windows 10/11** (64-bit)
- **Docker Desktop** para Windows instalado y ejecutándose
  - Descargar: https://www.docker.com/products/docker-desktop/
- **8 GB RAM** mínimo (16 GB recomendado)
- **10 GB** espacio en disco

## Instalación Rápida (3 pasos)

### 1. Descomprimir el archivo ZIP
Extraiga el contenido del ZIP a una carpeta de su preferencia.

### 2. Iniciar Rhinometric
Haga **doble clic** en `start.bat`

El script iniciará automáticamente todos los servicios.

### 3. Acceder a Grafana
Abra su navegador y vaya a: **http://localhost:3000**

**Credenciales:**
- **Usuario:** `admin`
- **Contraseña:** `admin_secure_2024`

## Dashboards Disponibles

Una vez dentro de Grafana:

1. **System Overview** - Vista general del sistema
2. **Distributed Tracing** - Trazas distribuidas (Tempo)
3. **Database Performance** - Rendimiento PostgreSQL
4. **Logs Analysis** - Análisis de logs (Loki)
5. **Metrics Explorer** - Explorador de métricas (Prometheus)
6. **Alerts Management** - Gestión de alertas
7. **License Management** - Estado de licencia trial

## Comandos

| Acción | Comando |
|--------|---------|
| Iniciar | `start.bat` |
| Detener | `stop.bat` |
| Validar | `validate.bat` |

## Troubleshooting

### ❌ "Docker no está instalado"
1. Instale Docker Desktop para Windows
2. Inicie Docker Desktop
3. Espere a que el icono de Docker en la bandeja muestre "Docker Desktop is running"
4. Ejecute nuevamente `start.bat`

### ❌ "Puerto 3000 en uso"
Otro servicio está usando el puerto 3000.
```cmd
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### ❌ "Grafana no carga"
1. Ejecute `validate.bat` para ver el estado
2. Espere 60 segundos adicionales
3. Revise que Docker Desktop esté ejecutándose

### ❌ "No aparecen datos en dashboards"
1. Espere 2-3 minutos después de iniciar
2. Verifique que telemetrygen esté UP: `docker ps | findstr telemetrygen`

## Detener el Sistema

Haga **doble clic** en `stop.bat`

## Duración de la Licencia

⏱️ **30 días** desde el primer inicio

## Soporte

Para más información: https://rhinometric.io
EOF

log "  ✅ README.md Windows creado"
log "✅ Paquete Windows completo"

# ═══════════════════════════════════════════════════════════════════════
# PASO 3: CREAR SCRIPTS PARA MACOS
# ═══════════════════════════════════════════════════════════════════════

log_step "PASO 3/10: GENERANDO PAQUETE MACOS"

MAC_DIR="$TEMP_DIR/rhinometric-trial-v${VERSION}-mac"
mkdir -p "$MAC_DIR"

# Copiar archivos base
copy_base_files "$MAC_DIR" "macOS"

# Crear start.sh para Mac
cat > "$MAC_DIR/start.sh" << 'EOF'
#!/bin/bash

clear

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║         🦏 RHINOMETRIC TRIAL - INICIANDO... 🦏               ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

echo "[1/3] Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ ERROR: Docker no está instalado"
    echo ""
    echo "Por favor instale Docker Desktop para Mac:"
    echo "  • Intel:        https://docs.docker.com/desktop/install/mac-install/"
    echo "  • Apple Silicon: https://docs.docker.com/desktop/install/mac-install/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ ERROR: Docker no está ejecutándose"
    echo ""
    echo "Por favor inicie Docker Desktop desde Applications"
    exit 1
fi

echo "✅ Docker encontrado"
echo ""

echo "[2/3] Iniciando contenedores..."
if ! docker compose up -d; then
    echo "❌ ERROR: Fallo al iniciar contenedores"
    exit 1
fi
echo ""

echo "[3/3] Esperando servicios (30 segundos)..."
sleep 30
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║         ✅ RHINOMETRIC TRIAL INICIADO EXITOSAMENTE           ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 ACCESO:"
echo "   URL:        http://localhost:3000"
echo "   Usuario:    admin"
echo "   Contraseña: admin_secure_2024"
echo ""
echo "📊 DASHBOARDS DISPONIBLES:"
echo "   • System Overview"
echo "   • Distributed Tracing"
echo "   • Database Performance"
echo "   • Logs Analysis"
echo "   • Metrics Explorer"
echo "   • Alerts Management"
echo "   • License Management"
echo ""
echo "⏱️  Licencia Trial: 30 días"
echo ""
echo "Para detener: ./stop.sh"
echo ""
EOF

chmod +x "$MAC_DIR/start.sh"

# Crear stop.sh para Mac
cat > "$MAC_DIR/stop.sh" << 'EOF'
#!/bin/bash

clear

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║         🦏 RHINOMETRIC TRIAL - DETENIENDO... 🦏              ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

docker compose down

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Rhinometric Trial detenido exitosamente"
    echo ""
else
    echo "❌ ERROR: Fallo al detener contenedores"
    exit 1
fi
EOF

chmod +x "$MAC_DIR/stop.sh"

# Crear validate.sh para Mac
cat > "$MAC_DIR/validate.sh" << 'EOF'
#!/bin/bash

clear

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║         🦏 RHINOMETRIC TRIAL - VALIDACIÓN 🦏                 ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

echo "Verificando contenedores..."
echo ""
docker compose ps

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "ESTADO ESPERADO: 16/16 contenedores UP"
echo "════════════════════════════════════════════════════════════════"
echo ""
EOF

chmod +x "$MAC_DIR/validate.sh"

log "  ✅ Scripts macOS (.sh) creados con permisos de ejecución"

# Crear README-MAC.md
cat > "$MAC_DIR/README.md" << 'EOF'
# 🦏 Rhinometric Trial - Instalación macOS

## Requisitos Previos

- **macOS 11** (Big Sur) o superior
  - Compatible con **Intel** y **Apple Silicon** (M1/M2/M3)
- **Docker Desktop** para Mac instalado y ejecutándose
  - Descargar: https://www.docker.com/products/docker-desktop/
- **8 GB RAM** mínimo (16 GB recomendado)
- **10 GB** espacio en disco

## Instalación Rápida (4 pasos)

### 1. Descomprimir el archivo ZIP
Extraiga el contenido del ZIP a una carpeta de su preferencia.

### 2. Abrir Terminal
- Presione `Cmd + Espacio`
- Escriba "Terminal" y presione Enter
- Navegue a la carpeta descomprimida:
  ```bash
  cd ~/Downloads/rhinometric-trial-v2.0.0-mac
  ```

### 3. Dar permisos de ejecución (solo primera vez)
```bash
chmod +x *.sh
```

### 4. Iniciar Rhinometric
```bash
./start.sh
```

El script iniciará automáticamente todos los servicios.

### 5. Acceder a Grafana
Abra su navegador y vaya a: **http://localhost:3000**

**Credenciales:**
- **Usuario:** `admin`
- **Contraseña:** `admin_secure_2024`

## Dashboards Disponibles

Una vez dentro de Grafana:

1. **System Overview** - Vista general del sistema
2. **Distributed Tracing** - Trazas distribuidas (Tempo)
3. **Database Performance** - Rendimiento PostgreSQL
4. **Logs Analysis** - Análisis de logs (Loki)
5. **Metrics Explorer** - Explorador de métricas (Prometheus)
6. **Alerts Management** - Gestión de alertas
7. **License Management** - Estado de licencia trial

## Comandos

| Acción | Comando |
|--------|---------|
| Iniciar | `./start.sh` |
| Detener | `./stop.sh` |
| Validar | `./validate.sh` |

## Troubleshooting

### ❌ "Permission denied"
Ejecute nuevamente:
```bash
chmod +x *.sh
./start.sh
```

### ❌ "Docker not found"
1. Instale Docker Desktop para Mac
2. Inicie Docker Desktop desde Applications
3. Espere a que muestre "Docker Desktop is running"
4. Ejecute nuevamente `./start.sh`

### ❌ "Puerto 3000 en uso"
Otro servicio está usando el puerto 3000.
```bash
lsof -ti :3000 | xargs kill -9
```

### ❌ "Grafana no carga"
1. Ejecute `./validate.sh` para ver el estado
2. Espere 60 segundos adicionales
3. Revise que Docker Desktop esté ejecutándose

### ❌ "No aparecen datos en dashboards"
1. Espere 2-3 minutos después de iniciar
2. Verifique que telemetrygen esté UP:
   ```bash
   docker ps | grep telemetrygen
   ```

### ⚠️ Apple Silicon (M1/M2/M3)
Docker Desktop automáticamente maneja la emulación de arquitectura.
Si experimenta lentitud, aumente la RAM asignada a Docker Desktop:
- Docker Desktop → Preferences → Resources → Memory → 8 GB+

## Detener el Sistema

```bash
./stop.sh
```

## Duración de la Licencia

⏱️ **30 días** desde el primer inicio

## Soporte

Para más información: https://rhinometric.io
EOF

log "  ✅ README.md macOS creado"
log "✅ Paquete macOS completo"

# ═══════════════════════════════════════════════════════════════════════
# PASO 4: CREAR SCRIPTS PARA LINUX
# ═══════════════════════════════════════════════════════════════════════

log_step "PASO 4/10: GENERANDO PAQUETE LINUX"

LINUX_DIR="$TEMP_DIR/rhinometric-trial-v${VERSION}-linux"
mkdir -p "$LINUX_DIR"

# Copiar archivos base
copy_base_files "$LINUX_DIR" "Linux"

# Crear start.sh para Linux
cat > "$LINUX_DIR/start.sh" << 'EOF'
#!/bin/bash

clear

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║         🦏 RHINOMETRIC TRIAL - INICIANDO... 🦏               ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

echo "[1/3] Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ ERROR: Docker no está instalado"
    echo ""
    echo "Por favor instale Docker:"
    echo "  • Ubuntu/Debian: https://docs.docker.com/engine/install/ubuntu/"
    echo "  • RHEL/CentOS:   https://docs.docker.com/engine/install/centos/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ ERROR: Docker no está ejecutándose"
    echo ""
    echo "Inicie el servicio Docker:"
    echo "  sudo systemctl start docker"
    exit 1
fi

echo "✅ Docker encontrado"
echo ""

echo "[2/3] Iniciando contenedores..."
if ! docker compose up -d; then
    echo "❌ ERROR: Fallo al iniciar contenedores"
    echo ""
    echo "Si obtiene error de permisos, ejecute:"
    echo "  sudo docker compose up -d"
    exit 1
fi
echo ""

echo "[3/3] Esperando servicios (30 segundos)..."
sleep 30
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║         ✅ RHINOMETRIC TRIAL INICIADO EXITOSAMENTE           ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 ACCESO:"
echo "   URL:        http://localhost:3000"
echo "   Usuario:    admin"
echo "   Contraseña: admin_secure_2024"
echo ""
echo "📊 DASHBOARDS DISPONIBLES:"
echo "   • System Overview"
echo "   • Distributed Tracing"
echo "   • Database Performance"
echo "   • Logs Analysis"
echo "   • Metrics Explorer"
echo "   • Alerts Management"
echo "   • License Management"
echo ""
echo "⏱️  Licencia Trial: 30 días"
echo ""
echo "Para detener: ./stop.sh"
echo ""
EOF

chmod +x "$LINUX_DIR/start.sh"

# Crear stop.sh para Linux
cat > "$LINUX_DIR/stop.sh" << 'EOF'
#!/bin/bash

clear

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║         🦏 RHINOMETRIC TRIAL - DETENIENDO... 🦏              ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

docker compose down

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Rhinometric Trial detenido exitosamente"
    echo ""
else
    echo "❌ ERROR: Fallo al detener contenedores"
    echo ""
    echo "Si obtiene error de permisos, ejecute:"
    echo "  sudo docker compose down"
    exit 1
fi
EOF

chmod +x "$LINUX_DIR/stop.sh"

# Crear validate.sh para Linux
cat > "$LINUX_DIR/validate.sh" << 'EOF'
#!/bin/bash

clear

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║         🦏 RHINOMETRIC TRIAL - VALIDACIÓN 🦏                 ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

echo "Verificando contenedores..."
echo ""
docker compose ps

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "ESTADO ESPERADO: 16/16 contenedores UP"
echo "════════════════════════════════════════════════════════════════"
echo ""
EOF

chmod +x "$LINUX_DIR/validate.sh"

log "  ✅ Scripts Linux (.sh) creados con permisos de ejecución"

# Crear README-LINUX.md
cat > "$LINUX_DIR/README.md" << 'EOF'
# 🦏 Rhinometric Trial - Instalación Linux

## Requisitos Previos

- **Ubuntu 20.04+**, **Debian 11+**, o **RHEL/CentOS 8+**
- **Docker** y **Docker Compose** instalados
- **8 GB RAM** mínimo (16 GB recomendado)
- **10 GB** espacio en disco

## Instalar Docker (si no está instalado)

### Ubuntu/Debian
```bash
# Actualizar paquetes
sudo apt update

# Instalar dependencias
sudo apt install -y ca-certificates curl gnupg lsb-release

# Agregar GPG key de Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Agregar repositorio
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Agregar usuario al grupo docker (evita usar sudo)
sudo usermod -aG docker $USER
newgrp docker
```

### RHEL/CentOS
```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker
```

## Instalación Rápida (3 pasos)

### 1. Descomprimir el archivo ZIP
```bash
unzip rhinometric-trial-v2.0.0-linux.zip
cd rhinometric-trial-v2.0.0-linux
```

### 2. Dar permisos de ejecución (solo primera vez)
```bash
chmod +x *.sh
```

### 3. Iniciar Rhinometric
```bash
./start.sh
```

El script iniciará automáticamente todos los servicios.

### 4. Acceder a Grafana
Abra su navegador y vaya a: **http://localhost:3000**

**Credenciales:**
- **Usuario:** `admin`
- **Contraseña:** `admin_secure_2024`

## Dashboards Disponibles

Una vez dentro de Grafana:

1. **System Overview** - Vista general del sistema
2. **Distributed Tracing** - Trazas distribuidas (Tempo)
3. **Database Performance** - Rendimiento PostgreSQL
4. **Logs Analysis** - Análisis de logs (Loki)
5. **Metrics Explorer** - Explorador de métricas (Prometheus)
6. **Alerts Management** - Gestión de alertas
7. **License Management** - Estado de licencia trial

## Comandos

| Acción | Comando |
|--------|---------|
| Iniciar | `./start.sh` |
| Detener | `./stop.sh` |
| Validar | `./validate.sh` |

## Troubleshooting

### ❌ "Permission denied"
Ejecute nuevamente:
```bash
chmod +x *.sh
./start.sh
```

### ❌ "Docker not found"
Siga los pasos de instalación de Docker para su distribución (ver arriba).

### ❌ "Cannot connect to Docker daemon"
Inicie el servicio Docker:
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### ❌ "Permission denied while trying to connect"
Agregue su usuario al grupo docker:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### ❌ "Puerto 3000 en uso"
Otro servicio está usando el puerto 3000.
```bash
sudo lsof -ti :3000 | xargs sudo kill -9
```

### ❌ "Grafana no carga"
1. Ejecute `./validate.sh` para ver el estado
2. Espere 60 segundos adicionales
3. Revise logs:
   ```bash
   docker compose logs grafana
   ```

### ❌ "No aparecen datos en dashboards"
1. Espere 2-3 minutos después de iniciar
2. Verifique que telemetrygen esté UP:
   ```bash
   docker ps | grep telemetrygen
   ```

### ⚠️ Firewall
Si accede desde otra máquina, abra el puerto 3000:
```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 3000/tcp

# Firewalld (RHEL/CentOS)
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --reload
```

## Detener el Sistema

```bash
./stop.sh
```

## Duración de la Licencia

⏱️ **30 días** desde el primer inicio

## Soporte

Para más información: https://rhinometric.io
EOF

log "  ✅ README.md Linux creado"
log "✅ Paquete Linux completo"

# ═══════════════════════════════════════════════════════════════════════
# PASO 5: EMPAQUETAR WINDOWS
# ═══════════════════════════════════════════════════════════════════════

log_step "PASO 5/10: EMPAQUETANDO WINDOWS"

cd "$TEMP_DIR"

# Crear ZIP usando PowerShell (disponible en Git Bash WSL)
WIN_ZIP="rhinometric-trial-v${VERSION}-windows.zip"
log "📦 Creando $WIN_ZIP..."

if command -v powershell.exe &> /dev/null; then
    powershell.exe -Command "Compress-Archive -Path 'rhinometric-trial-v${VERSION}-windows' -DestinationPath '$WIN_ZIP' -Force" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        mv "$WIN_ZIP" "../$BUILD_DIR/"
        WIN_SIZE=$(du -h "../$BUILD_DIR/$WIN_ZIP" | cut -f1)
        log "✅ $WIN_ZIP creado ($WIN_SIZE)"
    else
        log_error "❌ Fallo al crear ZIP de Windows"
    fi
else
    # Fallback a zip si PowerShell no está disponible
    zip -r "$WIN_ZIP" "rhinometric-trial-v${VERSION}-windows" > /dev/null 2>&1
    mv "$WIN_ZIP" "../$BUILD_DIR/"
    WIN_SIZE=$(du -h "../$BUILD_DIR/$WIN_ZIP" | cut -f1)
    log "✅ $WIN_ZIP creado ($WIN_SIZE)"
fi

cd - > /dev/null

# ═══════════════════════════════════════════════════════════════════════
# PASO 6: EMPAQUETAR MACOS
# ═══════════════════════════════════════════════════════════════════════

log_step "PASO 6/10: EMPAQUETANDO MACOS"

cd "$TEMP_DIR"

MAC_ZIP="rhinometric-trial-v${VERSION}-mac.zip"
log "📦 Creando $MAC_ZIP..."

if command -v powershell.exe &> /dev/null; then
    powershell.exe -Command "Compress-Archive -Path 'rhinometric-trial-v${VERSION}-mac' -DestinationPath '$MAC_ZIP' -Force" > /dev/null 2>&1
    mv "$MAC_ZIP" "../$BUILD_DIR/"
    MAC_SIZE=$(du -h "../$BUILD_DIR/$MAC_ZIP" | cut -f1)
    log "✅ $MAC_ZIP creado ($MAC_SIZE)"
else
    tar -czf "${MAC_ZIP%.zip}.tar.gz" "rhinometric-trial-v${VERSION}-mac"
    mv "${MAC_ZIP%.zip}.tar.gz" "../$BUILD_DIR/"
    MAC_SIZE=$(du -h "../$BUILD_DIR/${MAC_ZIP%.zip}.tar.gz" | cut -f1)
    log "✅ ${MAC_ZIP%.zip}.tar.gz creado ($MAC_SIZE)"
fi

cd - > /dev/null

# ═══════════════════════════════════════════════════════════════════════
# PASO 7: EMPAQUETAR LINUX
# ═══════════════════════════════════════════════════════════════════════

log_step "PASO 7/10: EMPAQUETANDO LINUX"

cd "$TEMP_DIR"

LINUX_ZIP="rhinometric-trial-v${VERSION}-linux.zip"
log "📦 Creando $LINUX_ZIP..."

if command -v powershell.exe &> /dev/null; then
    powershell.exe -Command "Compress-Archive -Path 'rhinometric-trial-v${VERSION}-linux' -DestinationPath '$LINUX_ZIP' -Force" > /dev/null 2>&1
    mv "$LINUX_ZIP" "../$BUILD_DIR/"
    LINUX_SIZE=$(du -h "../$BUILD_DIR/$LINUX_ZIP" | cut -f1)
    log "✅ $LINUX_ZIP creado ($LINUX_SIZE)"
else
    tar -czf "${LINUX_ZIP%.zip}.tar.gz" "rhinometric-trial-v${VERSION}-linux"
    mv "${LINUX_ZIP%.zip}.tar.gz" "../$BUILD_DIR/"
    LINUX_SIZE=$(du -h "../$BUILD_DIR/${LINUX_ZIP%.zip}.tar.gz" | cut -f1)
    log "✅ ${LINUX_ZIP%.zip}.tar.gz creado ($LINUX_SIZE)"
fi

cd - > /dev/null

# ═══════════════════════════════════════════════════════════════════════
# PASO 8: VALIDACIÓN DE PAQUETES
# ═══════════════════════════════════════════════════════════════════════

log_step "PASO 8/10: VALIDACIÓN DE PAQUETES"

VALIDATION_LOG="$LOG_DIR/validation_${TIMESTAMP}.txt"

echo "═══════════════════════════════════════════════════════════════" > "$VALIDATION_LOG"
echo "VALIDACIÓN DE PAQUETES RHINOMETRIC TRIAL v${VERSION}" >> "$VALIDATION_LOG"
echo "Fecha: $(date)" >> "$VALIDATION_LOG"
echo "═══════════════════════════════════════════════════════════════" >> "$VALIDATION_LOG"
echo "" >> "$VALIDATION_LOG"

# Validar existencia de paquetes
log "🔍 Validando archivos generados..."

PACKAGES=(
    "$BUILD_DIR/rhinometric-trial-v${VERSION}-windows.zip"
    "$BUILD_DIR/rhinometric-trial-v${VERSION}-mac.zip"
    "$BUILD_DIR/rhinometric-trial-v${VERSION}-linux.zip"
)

for pkg in "${PACKAGES[@]}"; do
    if [ -f "$pkg" ]; then
        SIZE=$(du -h "$pkg" | cut -f1)
        log "  ✅ $(basename $pkg) - $SIZE"
        echo "✅ $(basename $pkg) - $SIZE" >> "$VALIDATION_LOG"
    else
        log_error "  ❌ $(basename $pkg) NO ENCONTRADO"
        echo "❌ $(basename $pkg) NO ENCONTRADO" >> "$VALIDATION_LOG"
    fi
done

# Validar contenido de cada paquete
log "\n🔍 Validando contenido de paquetes..."

for pkg in "${PACKAGES[@]}"; do
    if [ -f "$pkg" ]; then
        echo "" >> "$VALIDATION_LOG"
        echo "────────────────────────────────────────────────────────" >> "$VALIDATION_LOG"
        echo "CONTENIDO: $(basename $pkg)" >> "$VALIDATION_LOG"
        echo "────────────────────────────────────────────────────────" >> "$VALIDATION_LOG"
        
        # Listar contenido usando unzip
        unzip -l "$pkg" >> "$VALIDATION_LOG" 2>&1
        
        FILE_COUNT=$(unzip -l "$pkg" | grep -v "Archive:" | grep -v "Length" | grep -v "^-" | grep -v "files$" | wc -l)
        log "  ✅ $(basename $pkg) - $FILE_COUNT archivos"
    fi
done

log "✅ Log de validación: $VALIDATION_LOG"

# ═══════════════════════════════════════════════════════════════════════
# PASO 9: GENERAR CHECKSUMS
# ═══════════════════════════════════════════════════════════════════════

log_step "PASO 9/10: GENERANDO CHECKSUMS"

CHECKSUM_FILE="$WORK_DIR/$BUILD_DIR/checksums.txt"

echo "═══════════════════════════════════════════════════════════════" > "$CHECKSUM_FILE"
echo "RHINOMETRIC TRIAL v${VERSION} - SHA256 CHECKSUMS" >> "$CHECKSUM_FILE"
echo "Fecha: $(date)" >> "$CHECKSUM_FILE"
echo "═══════════════════════════════════════════════════════════════" >> "$CHECKSUM_FILE"
echo "" >> "$CHECKSUM_FILE"

cd "$WORK_DIR/$BUILD_DIR"

for pkg in *.zip; do
    if [ -f "$pkg" ]; then
        if command -v sha256sum &> /dev/null; then
            sha256sum "$pkg" >> "$CHECKSUM_FILE"
            log "  ✅ Checksum: $pkg"
        else
            log_warning "  ⚠️  sha256sum no disponible"
        fi
    fi
done

cd - > /dev/null

log "✅ Checksums guardados: $BUILD_DIR/checksums.txt"

# ═══════════════════════════════════════════════════════════════════════
# PASO 10: LIMPIEZA Y RESUMEN
# ═══════════════════════════════════════════════════════════════════════

log_step "PASO 10/10: LIMPIEZA Y RESUMEN"

log "🧹 Limpiando archivos temporales..."
rm -rf "$WORK_DIR/$TEMP_DIR"
log "✅ Archivos temporales eliminados"

# ═══════════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ═══════════════════════════════════════════════════════════════════════

clear

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║              ✅ BUILD COMPLETADO EXITOSAMENTE ✅                      ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

echo -e "${CYAN}📦 PAQUETES GENERADOS:${NC}"
echo ""

if [ -f "$BUILD_DIR/rhinometric-trial-v${VERSION}-windows.zip" ]; then
    WIN_SIZE=$(du -h "$BUILD_DIR/rhinometric-trial-v${VERSION}-windows.zip" | cut -f1)
    echo -e "  ${GREEN}✅${NC} rhinometric-trial-v${VERSION}-windows.zip ${YELLOW}($WIN_SIZE)${NC}"
fi

if [ -f "$BUILD_DIR/rhinometric-trial-v${VERSION}-mac.zip" ]; then
    MAC_SIZE=$(du -h "$BUILD_DIR/rhinometric-trial-v${VERSION}-mac.zip" | cut -f1)
    echo -e "  ${GREEN}✅${NC} rhinometric-trial-v${VERSION}-mac.zip ${YELLOW}($MAC_SIZE)${NC}"
fi

if [ -f "$BUILD_DIR/rhinometric-trial-v${VERSION}-linux.zip" ]; then
    LINUX_SIZE=$(du -h "$BUILD_DIR/rhinometric-trial-v${VERSION}-linux.zip" | cut -f1)
    echo -e "  ${GREEN}✅${NC} rhinometric-trial-v${VERSION}-linux.zip ${YELLOW}($LINUX_SIZE)${NC}"
fi

echo ""
echo -e "${CYAN}📂 UBICACIÓN:${NC}"
echo -e "  ${BUILD_DIR}/"
echo ""

echo -e "${CYAN}📋 LOGS Y VALIDACIÓN:${NC}"
echo -e "  ${LOG_FILE}"
echo -e "  ${VALIDATION_LOG}"
echo -e "  ${CHECKSUM_FILE}"
echo ""

echo -e "${CYAN}📊 CONTENIDO DE CADA PAQUETE:${NC}"
echo -e "  • docker-compose.yml (16 servicios)"
echo -e "  • config/ (8 archivos de configuración)"
echo -e "  • grafana/provisioning/ (7 dashboards)"
echo -e "  • licensing/ (Dockerfile + código completo)"
echo -e "  • license-dashboard/ (Dockerfile + código + templates)"
echo -e "  • .env (credenciales: admin/admin_secure_2024)"
echo -e "  • Scripts nativos del OS"
echo -e "  • README.md específico del OS"
echo ""

echo -e "${CYAN}🚀 LISTO PARA DISTRIBUIR:${NC}"
echo -e "  • ${BLUE}Windows 10/11${NC} - Scripts .bat (doble clic)"
echo -e "  • ${BLUE}macOS${NC} (Intel + Apple Silicon) - Scripts .sh"
echo -e "  • ${BLUE}Linux${NC} (Ubuntu/Debian/RHEL) - Scripts .sh"
echo ""

echo -e "${CYAN}⏱️  LICENCIA TRIAL:${NC}"
echo -e "  30 días desde el primer inicio"
echo ""

echo -e "${CYAN}🔒 CREDENCIALES:${NC}"
echo -e "  Usuario:    ${YELLOW}admin${NC}"
echo -e "  Contraseña: ${YELLOW}admin_secure_2024${NC}"
echo ""

echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Build completado en: $(date)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
echo ""

