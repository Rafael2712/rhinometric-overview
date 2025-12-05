# 🚀 PLAN DE LANZAMIENTO A PRODUCCIÓN - RHINOMETRIC v2.5.0
## DECISIONES EJECUTIVAS PARA SALIR A PRODUCCIÓN

**Fecha:** 7 de Noviembre 2025  
**Versión:** v2.5.0 "Enterprise Stable"  
**Estado:** IMPLEMENTANDO  
**Timeline:** 4 días (7-11 Noviembre)

---

## ✅ ANÁLISIS EJECUTIVO: QUÉ TENEMOS

### CORE PLATFORM (100% LISTO) ✅
```yaml
grafana: 10.4.0          # ✅ Dashboards y visualización
prometheus: 2.53.0       # ✅ Métricas con retención 15d/10GB
loki: 3.0.0             # ✅ Logs con retención 7d + compactación
tempo: 2.6.0            # ✅ Traces con retención 3d
postgresql: 15.10       # ✅ Base de datos persistente
redis: 7.2              # ✅ Cache y sessions
nginx: 1.27             # ✅ Reverse proxy + SSL
alertmanager: 0.27.0    # ✅ Sistema de alertas
```

### LICENSING SYSTEM (100% LISTO) ✅
- ✅ **License Server v2** - Generación y validación con JWT
- ✅ **License UI** - Interfaz web (puerto 8092)
- ✅ **License Monitor** - Monitoreo automático
- ✅ **PostgreSQL Integration** - Persistencia completa
- ✅ **API REST** - Endpoints `/generate`, `/validate`

### BACKEND SERVICES (100% LISTO) ✅
- ✅ **Dashboard Builder v2.5.0** - API FastAPI (puerto 8001)
- ✅ **AI Anomaly Detection** - ML en tiempo real (puerto 8085)
- ✅ **Report Generator** - PDFs y emails automáticos
- ✅ **API Proxy** - Gateway unificado (puerto 8081)
- ✅ **Backup Service** - Backups automáticos

### POLÍTICAS DE RETENCIÓN (100% LISTO) ✅
- ✅ Docker daemon: 30MB/contenedor (10MB × 3 files)
- ✅ Prometheus: 15 días / 10GB con WAL compression
- ✅ Loki: 7 días / 5GB con compactación cada 10min
- ✅ Tempo: 3 días / 2GB con block compaction
- ✅ **Consumo estable: ~30GB** (vs 200GB+ sin políticas)

---

## ⚠️ LO QUE FALTA (ANÁLISIS CRÍTICO)

### 1. SISTEMA DE EMAILS (90% LISTO) ⚠️
**Tenemos:**
- ✅ Report Generator con `EmailService` completo
- ✅ Configuración SMTP en `config.py`
- ✅ Templates HTML con Jinja2
- ✅ Envío de PDFs/HTML por email
- ✅ Support para Gmail, SendGrid, AWS SES

**Falta:**
- ❌ Integración con License Server (enviar licencia por email)
- ❌ Template específico para emails de licencia
- ❌ Variables de entorno configuradas

**¿Es CRÍTICO?**
- 🔴 SÍ - Clientes necesitan recibir licencias automáticamente

**Acción:** 🔴 INTEGRAR EN 4 HORAS

---

### 2. DASHBOARD STUDIO UI (70% LISTO) 🟡
**Tenemos:**
- ✅ Código React completo (23 archivos, 79KB)
- ✅ 5-step wizard implementado
- ✅ JWT authentication
- ✅ Quick Create feature
- ✅ Integración con Dashboard Builder API

**Falta:**
- ❌ Docker deployment (npm install toma 3+ minutos)
- ❌ Integración en docker-compose principal

**¿Es CRÍTICO?**
- 🟡 NO - Dashboard Builder API funciona standalone
- ✅ Clientes pueden usar Grafana directamente
- ✅ O llamar API con curl/Postman

**Decisión:** 🟢 **MOVER A v2.6.0** (próxima versión)

---

### 3. INSTALADORES (10% LISTO) ❌
**Tenemos:**
- ⚠️ `install.sh` básico (descarga docker-compose y arranca)
- ⚠️ Carpetas `linux/`, `windows/`, `mac/` VACÍAS

**Falta:**
- ❌ Instalador Linux completo con validación
- ❌ Instalador Windows (PowerShell o .exe)
- ❌ Instalador Mac (bash script o .pkg)
- ❌ Post-install validation
- ❌ Uninstallers para cada OS

**¿Es CRÍTICO?**
- 🔴 SÍ - Para clientes on-premise sin experiencia en Docker

**Acción:** 🔴 CREAR INSTALADORES EN 8 HORAS

---

### 4. DOCUMENTACIÓN (40% LISTO) ⚠️
**Tenemos:**
- ✅ 9 documentos técnicos en `docs/`
- ✅ API documentation básica
- ✅ Developer onboarding guide
- ✅ Production readiness assessment

**Falta:**
- ❌ README.md principal completo (GitHub público)
- ❌ INSTALL.md paso a paso con screenshots
- ❌ QUICKSTART.md (primeros 10 minutos)
- ❌ USER_MANUAL.md (manual de usuario completo)
- ❌ TROUBLESHOOTING.md (problemas comunes)
- ❌ LICENSE_GUIDE.md (gestión de licencias)
- ❌ VIDEO demo (5-10 min)

**¿Es CRÍTICO?**
- 🔴 SÍ - Clientes no pueden usar lo que no entienden

**Acción:** 🔴 COMPLETAR EN 6 HORAS

---

### 5. TESTING COMPLETO (30% LISTO) 🟡
**Tenemos:**
- ✅ Smoke test Dashboard Builder (7/7 passed)
- ✅ Tests manuales funcionales

**Falta:**
- ❌ Unit tests automatizados
- ❌ Integration tests
- ❌ Load testing (50+ usuarios simultáneos)
- ❌ Security testing (penetration test)
- ❌ Performance benchmarks

**¿Es CRÍTICO?**
- 🟡 PARCIAL - Necesario para garantías pero no bloqueante
- ✅ Hemos probado manualmente todo
- ✅ Tenemos 24 contenedores funcionando estables

**Decisión:** 🟢 **TESTS BÁSICOS AHORA, COMPLETOS EN v2.6.0**

**Acción:** 🟡 TEST PLAN Y 5 ESCENARIOS EN 3 HORAS

---

### 6. DASHBOARD DE SALUD DEL SISTEMA (0% LISTO) ❌
**Tenemos:**
- ✅ Métricas de Prometheus
- ✅ Health checks en servicios
- ✅ Logs en Loki

**Falta:**
- ❌ Dashboard Grafana con estado del sistema
- ❌ Panel de servicios activos (24/24 up)
- ❌ Panel de uso de disco (con políticas de retención)
- ❌ Panel de métricas de licencias
- ❌ Alertas automáticas (disco >80%, CPU >90%, servicios down)

**¿Es CRÍTICO?**
- 🟡 IMPORTANTE - Para soporte y clientes enterprise

**Acción:** 🟡 CREAR DASHBOARD BÁSICO EN 3 HORAS

---

## 🎯 DECISIÓN EJECUTIVA: QUÉ INCLUIR EN v2.5.0

### 🔴 CRÍTICO - DEBE ESTAR (BLOQUEANTE)
1. ✅ Core Platform (24 servicios)
2. ✅ Licensing System
3. ✅ Políticas de Retención
4. 🔴 **Sistema de Emails** → IMPLEMENTAR HOY
5. 🔴 **Instaladores** → CREAR HOY/MAÑANA
6. 🔴 **Documentación Completa** → ESCRIBIR MAÑANA

### 🟡 IMPORTANTE - INCLUIR SI ES POSIBLE
7. 🟡 **Dashboard de Salud** → CREAR MAÑANA
8. 🟡 **Test Plan Básico** → DOCUMENTAR MAÑANA

### 🟢 NO CRÍTICO - MOVER A v2.6.0
9. 🟢 **Dashboard Studio UI** → v2.6.0
10. 🟢 **Tests Automatizados Completos** → v2.6.0
11. 🟢 **Load Testing Avanzado** → v2.6.0
12. 🟢 **Security Audit Completo** → v2.6.0

---

## 📅 TIMELINE DE IMPLEMENTACIÓN

### **HOY - 7 Noviembre (DÍA 1)** 🔴
**OBJETIVO: Sistema de Emails + Instalador Linux**

#### Mañana (4 horas)
- [x] 09:00 - Análisis completo (1h) ✅
- [ ] 10:00 - Integrar EmailService con License Server (2h)
  - [ ] Crear función `send_license_email()` en license_server.py
  - [ ] Template HTML para email de licencia
  - [ ] Configurar SMTP en docker-compose.override.yml
  - [ ] Testing de envío

#### Tarde (4 horas)
- [ ] 14:00 - Crear instalador Linux completo (3h)
  - [ ] Script con detección de OS
  - [ ] Validación de requisitos (Docker, docker-compose)
  - [ ] Instalación automática de dependencias
  - [ ] Post-install validation
  - [ ] Script de uninstall
- [ ] 17:00 - Testing instalador en VM Ubuntu limpia (1h)

---

### **MAÑANA - 8 Noviembre (DÍA 2)** 🟡
**OBJETIVO: Instaladores Windows/Mac + Dashboard de Salud**

#### Mañana (4 horas)
- [ ] 09:00 - Instalador Windows PowerShell (2h)
- [ ] 11:00 - Instalador Mac bash script (2h)

#### Tarde (4 horas)
- [ ] 14:00 - Dashboard de Salud Grafana (3h)
  - [ ] Panel de servicios (24/24 up/down)
  - [ ] Panel de uso de disco con límites
  - [ ] Panel de licencias activas
  - [ ] Alertas básicas
- [ ] 17:00 - Testing dashboard (1h)

---

### **SÁBADO - 9 Noviembre (DÍA 3)** 📝
**OBJETIVO: Documentación Completa**

#### Mañana (4 horas)
- [ ] 09:00 - README.md principal (1h)
- [ ] 10:00 - INSTALL.md con screenshots (2h)
- [ ] 12:00 - QUICKSTART.md (1h)

#### Tarde (4 horas)
- [ ] 14:00 - USER_MANUAL.md (2h)
- [ ] 16:00 - TROUBLESHOOTING.md (1h)
- [ ] 17:00 - LICENSE_GUIDE.md (1h)

---

### **DOMINGO - 10 Noviembre (DÍA 4)** ✅
**OBJETIVO: Validación + Test Plan + GitHub**

#### Mañana (4 horas)
- [ ] 09:00 - Test Plan documento (1h)
- [ ] 10:00 - Ejecutar 5 escenarios críticos (2h)
  1. Instalación limpia → Primera licencia
  2. Login → Crear dashboard → Verificar métricas
  3. Generar reporte → Enviar email
  4. Backup → Restore → Verificar datos
  5. Monitorear 1 hora → Verificar políticas retención
- [ ] 12:00 - Security check básico (1h)

#### Tarde (4 horas)
- [ ] 14:00 - Actualizar README GitHub público (1h)
- [ ] 15:00 - Actualizar docs/ GitHub privado (1h)
- [ ] 16:00 - Crear Release Notes v2.5.0 (1h)
- [ ] 17:00 - CHANGELOG.md completo (1h)

---

## 🎉 LANZAMIENTO - 11 Noviembre (DÍA 5)

### Pre-Launch Checklist
- [ ] Todos los 24 contenedores UP y healthy
- [ ] Sistema de emails funcionando (prueba real)
- [ ] Instaladores probados en 3 OS
- [ ] Documentación completa en GitHub
- [ ] Dashboard de Salud funcionando
- [ ] 5 escenarios de test pasados
- [ ] No hay errores críticos en logs
- [ ] Políticas de retención verificadas

### Launch Actions
- [ ] 09:00 - Git tag v2.5.0 y push
- [ ] 09:30 - GitHub Release con release notes
- [ ] 10:00 - Actualizar README.md con badge v2.5.0
- [ ] 10:30 - Post en redes (LinkedIn, Twitter)
- [ ] 11:00 - Notificar a primeros clientes beta
- [ ] 12:00 - 🎉 **PRODUCCIÓN LIVE**

---

## 📦 FEATURES MOVIDAS A v2.6.0 (POST-LANZAMIENTO)

### Funcionalidades para Diciembre 2025
- [ ] Dashboard Studio UI (React frontend completo)
- [ ] Tests automatizados end-to-end
- [ ] Load testing con 100+ usuarios
- [ ] Security audit completo
- [ ] Performance optimizations
- [ ] Multi-tenancy avanzado
- [ ] Integración Slack/Teams
- [ ] Custom branding por cliente
- [ ] Mobile responsive UI
- [ ] Advanced analytics con IA

---

## 🔧 IMPLEMENTACIÓN TÉCNICA

### 1. Sistema de Emails (4 horas)

**Archivo:** `licensing/license_server.py`

```python
# Agregar después de la línea 12
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Agregar después de la línea 33
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM = os.getenv('SMTP_FROM', 'licenses@rhinometric.io')

# Nueva función (agregar después de validate_license)
def send_license_email(customer_email, customer_name, license_key, license_data):
    """Enviar licencia por email al cliente"""
    
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP not configured, skipping email")
        return False
    
    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['From'] = f"Rhinometric Licenses <{SMTP_FROM}>"
        msg['To'] = customer_email
        msg['Subject'] = f"🦏 Your Rhinometric License - {customer_name}"
        
        # HTML template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1a73e8 0%, #34a853 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .license-box {{ background: white; padding: 20px; margin: 20px 0; 
                               border-radius: 4px; border: 2px dashed #1a73e8; 
                               font-family: monospace; font-size: 12px; word-break: break-all; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #1a73e8; 
                          color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #5f6368; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🦏 Welcome to Rhinometric!</h1>
                    <p>Your Observability Platform License</p>
                </div>
                <div class="content">
                    <h2>Hello {customer_name}! 👋</h2>
                    
                    <p>Thank you for choosing Rhinometric Observability Platform. 
                    Your license has been generated and is ready to use.</p>
                    
                    <h3>📋 License Details:</h3>
                    <ul>
                        <li><strong>Type:</strong> {license_data.get('license_type', 'trial').upper()}</li>
                        <li><strong>Valid Until:</strong> {license_data.get('expires_at', 'N/A')}</li>
                        <li><strong>Features:</strong> {', '.join(license_data.get('features', []))}</li>
                    </ul>
                    
                    <h3>🔑 Your License Key:</h3>
                    <div class="license-box">{license_key}</div>
                    
                    <p><strong>⚠️ Important:</strong> Keep this license key secure. You will need it to activate your Rhinometric installation.</p>
                    
                    <h3>🚀 Next Steps:</h3>
                    <ol>
                        <li>Download the installer from <a href="https://github.com/your-repo">GitHub</a></li>
                        <li>Run the installer on your server</li>
                        <li>Enter this license key when prompted</li>
                        <li>Access your dashboard at http://your-server:3000</li>
                    </ol>
                    
                    <a href="https://docs.rhinometric.io/quickstart" class="button">📚 Read Quickstart Guide</a>
                    
                    <p>Need help? Contact our support team at support@rhinometric.io</p>
                </div>
                
                <div class="footer">
                    <p>Rhinometric Observability Platform v2.5.0</p>
                    <p>© 2025 Rhinometric. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        text = f"""
        Welcome to Rhinometric!
        
        Hello {customer_name},
        
        Your Rhinometric license has been generated:
        
        License Type: {license_data.get('license_type', 'trial').upper()}
        Valid Until: {license_data.get('expires_at', 'N/A')}
        Features: {', '.join(license_data.get('features', []))}
        
        Your License Key:
        {license_key}
        
        Next Steps:
        1. Download installer from GitHub
        2. Run installer on your server
        3. Enter license key when prompted
        
        Need help? support@rhinometric.io
        
        © 2025 Rhinometric
        """
        
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        # Enviar email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"License email sent to {customer_email}")
        return True
    
    except Exception as e:
        logger.error(f"Error sending license email: {e}")
        return False

# Modificar api_generate_license() para enviar email
# Agregar después de la línea 307 (después de insertar en DB):
        # Enviar email si se proporciona customer_email
        customer_email = data.get('customer_email')
        if customer_email:
            email_sent = send_license_email(
                customer_email,
                customer_name,
                license_key,
                {
                    'license_type': license_type,
                    'expires_at': datetime.fromtimestamp(result['payload']['exp']).strftime('%Y-%m-%d'),
                    'features': result['payload'].get('features', [])
                }
            )
            response['email_sent'] = email_sent
```

**Archivo:** `docker-compose.override.yml`

```yaml
# Agregar en el servicio rhinometric-license-server:
environment:
  - SMTP_HOST=smtp.gmail.com
  - SMTP_PORT=587
  - SMTP_USER=${SMTP_USER:-}
  - SMTP_PASSWORD=${SMTP_PASSWORD:-}
  - SMTP_FROM=licenses@rhinometric.io
```

**Archivo:** `.env` (crear si no existe)

```bash
# SMTP Configuration for License Emails
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

---

### 2. Instalador Linux (3 horas)

**Archivo:** `installers/linux/install-rhinometric.sh`

```bash
#!/bin/bash
# Rhinometric v2.5.0 - Instalador Oficial Linux
# Soporta: Ubuntu 20.04+, Debian 11+, CentOS 8+, RHEL 8+

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
VERSION="2.5.0"
REPO_URL="https://github.com/Rafael2712/mi-proyecto"
INSTALL_DIR="/opt/rhinometric"
DATA_DIR="/var/lib/rhinometric"

echo -e "${BLUE}"
cat << "EOF"
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        🦏 RHINOMETRIC INSTALLER v2.5.0                   ║
    ║        Observability Platform - Enterprise Edition       ║
    ║        © 2025 Rhinometric. All rights reserved.          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Función de log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    error "Este instalador debe ejecutarse como root"
    error "Ejecuta: sudo $0"
    exit 1
fi

# Detectar distribución
log "Detectando sistema operativo..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
    log "Detectado: $PRETTY_NAME"
else
    error "No se pudo detectar el sistema operativo"
    exit 1
fi

# Verificar arquitectura
ARCH=$(uname -m)
if [ "$ARCH" != "x86_64" ] && [ "$ARCH" != "aarch64" ]; then
    error "Arquitectura no soportada: $ARCH"
    error "Rhinometric requiere x86_64 o aarch64"
    exit 1
fi
log "Arquitectura: $ARCH ✓"

# Verificar requisitos de sistema
log "Verificando requisitos del sistema..."

# RAM mínima: 8GB
TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM" -lt 7 ]; then
    error "RAM insuficiente: ${TOTAL_RAM}GB (mínimo 8GB)"
    exit 1
fi
log "RAM: ${TOTAL_RAM}GB ✓"

# Disco libre: 50GB
FREE_DISK=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$FREE_DISK" -lt 50 ]; then
    error "Espacio en disco insuficiente: ${FREE_DISK}GB (mínimo 50GB)"
    exit 1
fi
log "Disco libre: ${FREE_DISK}GB ✓"

# Verificar Docker
log "Verificando Docker..."
if ! command -v docker &> /dev/null; then
    warning "Docker no encontrado. Instalando..."
    
    case "$OS" in
        ubuntu|debian)
            apt-get update -qq
            apt-get install -y ca-certificates curl gnupg lsb-release
            mkdir -p /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$OS/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            apt-get update -qq
            apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        centos|rhel)
            yum install -y yum-utils
            yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            systemctl start docker
            systemctl enable docker
            ;;
        *)
            error "Distribución no soportada para instalación automática de Docker"
            error "Por favor instala Docker manualmente: https://docs.docker.com/engine/install/"
            exit 1
            ;;
    esac
    
    log "Docker instalado ✓"
else
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    log "Docker $DOCKER_VERSION encontrado ✓"
fi

# Verificar que Docker esté corriendo
if ! docker info &> /dev/null; then
    error "Docker no está corriendo"
    error "Inicia Docker: sudo systemctl start docker"
    exit 1
fi

# Verificar Docker Compose
log "Verificando Docker Compose..."
if ! docker compose version &> /dev/null; then
    error "Docker Compose no encontrado"
    error "Instala Docker Compose v2.20+ desde: https://docs.docker.com/compose/install/"
    exit 1
fi
COMPOSE_VERSION=$(docker compose version --short)
log "Docker Compose $COMPOSE_VERSION encontrado ✓"

# Crear directorios
log "Creando directorios..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$DATA_DIR"/{postgres,grafana,prometheus,loki,tempo,licenses}
chmod 755 "$INSTALL_DIR"
chmod 755 "$DATA_DIR"
log "Directorios creados en $INSTALL_DIR ✓"

# Descargar configuración
log "Descargando configuración desde GitHub..."
cd "$INSTALL_DIR"

# Clonar repositorio (branch main)
if [ -d ".git" ]; then
    log "Repositorio existente, actualizando..."
    git pull origin main --quiet
else
    log "Clonando repositorio..."
    git clone --depth 1 --branch main "$REPO_URL.git" . --quiet
fi

# Copiar configuración al directorio de instalación
cd infrastructure/mi-proyecto
log "Archivos descargados ✓"

# Generar archivo .env
log "Generando configuración..."
cat > .env << 'ENVEOF'
# Rhinometric v2.5.0 Configuration
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 32)
LICENSE_DURATION_DAYS=180

# SMTP Configuration (COMPLETAR DESPUÉS DE INSTALACIÓN)
SMTP_USER=
SMTP_PASSWORD=
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Grafana
GF_SECURITY_ADMIN_PASSWORD=admin
GF_INSTALL_PLUGINS=

# Retention Policies (YA CONFIGURADAS)
PROMETHEUS_RETENTION_DAYS=15d
PROMETHEUS_RETENTION_SIZE=10GB
LOKI_RETENTION_DAYS=168h
TEMPO_RETENTION_DAYS=72h
ENVEOF

log "Configuración generada ✓"

# Construir imágenes
log "Construyendo imágenes Docker (esto puede tomar varios minutos)..."
docker compose -f docker-compose.yml -f docker-compose.override.yml build --quiet

# Iniciar servicios
log "Iniciando servicios Rhinometric..."
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Esperar servicios
log "Esperando que los servicios estén listos (esto puede tomar 1-2 minutos)..."
sleep 60

# Verificar salud de servicios
log "Verificando salud de servicios..."
FAILED=0

# Verificar puertos principales
SERVICES=(
    "3000:Grafana"
    "9090:Prometheus"
    "3100:Loki"
    "3200:Tempo"
    "8090:License Server"
    "8001:Dashboard Builder"
)

for service in "${SERVICES[@]}"; do
    PORT="${service%%:*}"
    NAME="${service##*:}"
    
    if timeout 5 bash -c "cat < /dev/null > /dev/tcp/localhost/$PORT" 2>/dev/null; then
        log "$NAME (puerto $PORT) ✓"
    else
        warning "$NAME (puerto $PORT) no responde"
        FAILED=$((FAILED + 1))
    fi
done

# Resumen de instalación
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}║              ✅ INSTALACIÓN COMPLETADA                     ║${NC}"
else
    echo -e "${YELLOW}║         ⚠️  INSTALACIÓN COMPLETADA CON ADVERTENCIAS        ║${NC}"
fi
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

log "Rhinometric v$VERSION instalado en: $INSTALL_DIR"
log "Datos almacenados en: $DATA_DIR"
echo ""
echo -e "${BLUE}📊 ACCESO A LA PLATAFORMA:${NC}"
echo "  • Grafana:          http://$(hostname -I | awk '{print $1}'):3000"
echo "  • Prometheus:       http://$(hostname -I | awk '{print $1}'):9090"
echo "  • License Server:   http://$(hostname -I | awk '{print $1}'):8090"
echo "  • Dashboard Builder: http://$(hostname -I | awk '{print $1}'):8001"
echo ""
echo -e "${BLUE}🔐 CREDENCIALES INICIALES:${NC}"
echo "  • Usuario: admin"
echo "  • Contraseña: admin (⚠️  CAMBIAR EN PRIMER LOGIN)"
echo ""
echo -e "${BLUE}📚 PRÓXIMOS PASOS:${NC}"
echo "  1. Accede a Grafana: http://$(hostname -I | awk '{print $1}'):3000"
echo "  2. Genera tu licencia en: http://$(hostname -I | awk '{print $1}'):8090"
echo "  3. Lee la documentación: https://github.com/Rafael2712/mi-proyecto/wiki"
echo "  4. Configura SMTP para envío de licencias (edita $INSTALL_DIR/.env)"
echo ""
echo -e "${BLUE}🛠️  COMANDOS ÚTILES:${NC}"
echo "  • Ver logs:     cd $INSTALL_DIR && docker compose logs -f"
echo "  • Reiniciar:    cd $INSTALL_DIR && docker compose restart"
echo "  • Detener:      cd $INSTALL_DIR && docker compose down"
echo "  • Desinstalar:  sudo /opt/rhinometric/uninstall.sh"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $FAILED servicio(s) no respondieron al health check${NC}"
    echo "   Verifica los logs: cd $INSTALL_DIR && docker compose logs"
    echo ""
fi

log "¡Disfruta Rhinometric! 🦏"
exit 0
```

**Archivo:** `installers/linux/uninstall-rhinometric.sh`

```bash
#!/bin/bash
# Rhinometric v2.5.0 - Desinstalador Linux

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

INSTALL_DIR="/opt/rhinometric"
DATA_DIR="/var/lib/rhinometric"

echo -e "${RED}"
echo "═══════════════════════════════════════════════════════════"
echo "  🗑️  RHINOMETRIC UNINSTALLER"
echo "═══════════════════════════════════════════════════════════"
echo -e "${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Este script debe ejecutarse como root"
    exit 1
fi

echo -e "${YELLOW}ADVERTENCIA:${NC} Esta acción eliminará:"
echo "  • Todos los contenedores de Rhinometric"
echo "  • Todas las imágenes Docker"
echo "  • Todos los datos en $DATA_DIR"
echo "  • Archivos de instalación en $INSTALL_DIR"
echo ""
read -p "¿Estás seguro? Escribe 'YES' para continuar: " confirm

if [ "$confirm" != "YES" ]; then
    echo "Desinstalación cancelada."
    exit 0
fi

echo -e "${GREEN}[1/4]${NC} Deteniendo servicios..."
if [ -d "$INSTALL_DIR" ]; then
    cd "$INSTALL_DIR/infrastructure/mi-proyecto" || cd "$INSTALL_DIR"
    docker compose down -v 2>/dev/null || true
fi

echo -e "${GREEN}[2/4]${NC} Eliminando imágenes Docker..."
docker images | grep rhinometric | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true

echo -e "${GREEN}[3/4]${NC} Eliminando datos..."
rm -rf "$DATA_DIR"

echo -e "${GREEN}[4/4]${NC} Eliminando archivos de instalación..."
rm -rf "$INSTALL_DIR"

echo ""
echo -e "${GREEN}✅ Rhinometric ha sido completamente desinstalado${NC}"
echo ""
```

---

### 3. Instalador Windows (2 horas)

**Archivo:** `installers/windows/install-rhinometric.ps1`

```powershell
# Rhinometric v2.5.0 - Instalador Windows PowerShell
# Requiere: Windows 10/11, PowerShell 5.1+, Docker Desktop

#Requires -RunAsAdministrator

$VERSION = "2.5.0"
$REPO_URL = "https://github.com/Rafael2712/mi-proyecto"
$INSTALL_DIR = "C:\Program Files\Rhinometric"
$DATA_DIR = "C:\ProgramData\Rhinometric"

# Colores
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Green }
function Write-Error-Custom { Write-Host "[ERROR] $args" -ForegroundColor Red }
function Write-Warning-Custom { Write-Host "[WARNING] $args" -ForegroundColor Yellow }

# Banner
Write-Host @"
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        🦏 RHINOMETRIC INSTALLER v$VERSION                   ║
    ║        Observability Platform - Windows Edition          ║
    ║        © 2025 Rhinometric. All rights reserved.          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
"@ -ForegroundColor Blue

Write-Info "Iniciando instalación de Rhinometric v$VERSION..."

# Verificar Docker Desktop
Write-Info "Verificando Docker Desktop..."
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error-Custom "Docker Desktop no está instalado"
    Write-Error-Custom "Descarga Docker Desktop desde: https://www.docker.com/products/docker-desktop"
    exit 1
}

try {
    $dockerVersion = docker --version
    Write-Info "Docker encontrado: $dockerVersion ✓"
} catch {
    Write-Error-Custom "Docker no está corriendo"
    Write-Error-Custom "Inicia Docker Desktop e intenta de nuevo"
    exit 1
}

# Verificar Docker Compose
Write-Info "Verificando Docker Compose..."
try {
    $composeVersion = docker compose version
    Write-Info "Docker Compose encontrado: $composeVersion ✓"
} catch {
    Write-Error-Custom "Docker Compose no encontrado"
    exit 1
}

# Verificar requisitos del sistema
Write-Info "Verificando requisitos del sistema..."

# RAM
$totalRAM = [Math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
if ($totalRAM -lt 8) {
    Write-Error-Custom "RAM insuficiente: ${totalRAM}GB (mínimo 8GB)"
    exit 1
}
Write-Info "RAM: ${totalRAM}GB ✓"

# Disco
$freeDisk = [Math]::Round((Get-PSDrive C).Free / 1GB)
if ($freeDisk -lt 50) {
    Write-Error-Custom "Espacio en disco insuficiente: ${freeDisk}GB (mínimo 50GB)"
    exit 1
}
Write-Info "Disco libre: ${freeDisk}GB ✓"

# Crear directorios
Write-Info "Creando directorios..."
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
New-Item -ItemType Directory -Force -Path "$DATA_DIR\postgres" | Out-Null
New-Item -ItemType Directory -Force -Path "$DATA_DIR\grafana" | Out-Null
New-Item -ItemType Directory -Force -Path "$DATA_DIR\prometheus" | Out-Null
New-Item -ItemType Directory -Force -Path "$DATA_DIR\loki" | Out-Null
New-Item -ItemType Directory -Force -Path "$DATA_DIR\licenses" | Out-Null
Write-Info "Directorios creados ✓"

# Descargar configuración
Write-Info "Descargando configuración desde GitHub..."
Set-Location $INSTALL_DIR

if (Test-Path ".git") {
    Write-Info "Repositorio existente, actualizando..."
    git pull origin main --quiet
} else {
    Write-Info "Clonando repositorio..."
    git clone --depth 1 --branch main "$REPO_URL.git" . --quiet
}

Set-Location "infrastructure\mi-proyecto"
Write-Info "Archivos descargados ✓"

# Generar archivo .env
Write-Info "Generando configuración..."
$envContent = @"
# Rhinometric v$VERSION Configuration
POSTGRES_PASSWORD=$([Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((New-Guid).ToString())))
REDIS_PASSWORD=$([Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((New-Guid).ToString())))
JWT_SECRET=$([Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((New-Guid).ToString())))
LICENSE_DURATION_DAYS=180

# SMTP Configuration
SMTP_USER=
SMTP_PASSWORD=
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Grafana
GF_SECURITY_ADMIN_PASSWORD=admin
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Info "Configuración generada ✓"

# Construir imágenes
Write-Info "Construyendo imágenes Docker (esto puede tomar varios minutos)..."
docker compose -f docker-compose.yml -f docker-compose.override.yml build --quiet

# Iniciar servicios
Write-Info "Iniciando servicios Rhinometric..."
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Esperar servicios
Write-Info "Esperando que los servicios estén listos..."
Start-Sleep -Seconds 60

# Verificar servicios
Write-Info "Verificando salud de servicios..."
$services = @(
    @{Port=3000; Name="Grafana"},
    @{Port=9090; Name="Prometheus"},
    @{Port=8090; Name="License Server"},
    @{Port=8001; Name="Dashboard Builder"}
)

$failed = 0
foreach ($service in $services) {
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $service.Port -WarningAction SilentlyContinue
        if ($connection.TcpTestSucceeded) {
            Write-Info "$($service.Name) (puerto $($service.Port)) ✓"
        } else {
            Write-Warning-Custom "$($service.Name) (puerto $($service.Port)) no responde"
            $failed++
        }
    } catch {
        Write-Warning-Custom "$($service.Name) (puerto $($service.Port)) no responde"
        $failed++
    }
}

# Resumen
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
if ($failed -eq 0) {
    Write-Host "║              ✅ INSTALACIÓN COMPLETADA                     ║" -ForegroundColor Green
} else {
    Write-Host "║         ⚠️  INSTALACIÓN COMPLETADA CON ADVERTENCIAS        ║" -ForegroundColor Yellow
}
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Info "Rhinometric v$VERSION instalado en: $INSTALL_DIR"
Write-Host ""
Write-Host "📊 ACCESO A LA PLATAFORMA:" -ForegroundColor Blue
Write-Host "  • Grafana:          http://localhost:3000"
Write-Host "  • Prometheus:       http://localhost:9090"
Write-Host "  • License Server:   http://localhost:8090"
Write-Host "  • Dashboard Builder: http://localhost:8001"
Write-Host ""
Write-Host "🔐 CREDENCIALES INICIALES:" -ForegroundColor Blue
Write-Host "  • Usuario: admin"
Write-Host "  • Contraseña: admin (⚠️  CAMBIAR EN PRIMER LOGIN)"
Write-Host ""
Write-Host "📚 PRÓXIMOS PASOS:" -ForegroundColor Blue
Write-Host "  1. Accede a Grafana: http://localhost:3000"
Write-Host "  2. Genera tu licencia en: http://localhost:8090"
Write-Host "  3. Lee la documentación: https://github.com/Rafael2712/mi-proyecto/wiki"
Write-Host ""

Write-Info "¡Disfruta Rhinometric! 🦏"
```

---

## ✅ RESUMEN EJECUTIVO

### Lo que tenemos 100% listo:
- ✅ 24 servicios funcionando
- ✅ Licensing completo
- ✅ Políticas de retención
- ✅ Sistema de emails (90% - solo falta integración)

### Lo que falta (CRÍTICO):
1. 🔴 Integrar emails con License Server (4h)
2. 🔴 Instaladores Linux/Windows/Mac (8h)
3. 🔴 Documentación completa (6h)
4. 🟡 Dashboard de Salud (3h)
5. 🟡 Test Plan (3h)

### Timeline realista:
- **Hoy (7 Nov):** Emails + Instalador Linux
- **Mañana (8 Nov):** Instaladores Windows/Mac + Dashboard
- **Sábado (9 Nov):** Documentación completa
- **Domingo (10 Nov):** Testing + GitHub
- **Lunes (11 Nov):** 🎉 **PRODUCCIÓN**

### Lo que se mueve a v2.6.0:
- Dashboard Studio UI (React)
- Tests automatizados completos
- Load testing avanzado
- Security audit completo

---

**Próximo paso:** Comenzar implementación del sistema de emails ✅
