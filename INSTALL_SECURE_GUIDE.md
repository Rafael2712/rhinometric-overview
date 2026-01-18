# 📦 RHINOMETRIC v2.3.0 - GUÍA DE INSTALACIÓN SEGURA

**Sistema de Instalación Automatizada con Validación de Licencia**  
**Compatible**: Linux | macOS | Windows (WSL2)  
**Versión**: 2.3.0  
**Fecha**: Noviembre 2025

---

## 📋 ÍNDICE

1. [Visión General](#visión-general)
2. [Requisitos del Sistema](#requisitos-del-sistema)
3. [Pre-Instalación](#pre-instalación)
4. [Proceso de Instalación](#proceso-de-instalación)
5. [Flujo de Validación](#flujo-de-validación)
6. [Troubleshooting](#troubleshooting)
7. [Rollback](#rollback)
8. [FAQ](#faq)

---

## 🎯 VISIÓN GENERAL

`install-secure.sh` es un instalador completamente automatizado que:

- ✅ **Valida la licencia** antes de cualquier despliegue
- ✅ **Verifica dependencias** (Docker, Python, librerías)
- ✅ **Comprueba puertos** en uso para evitar conflictos
- ✅ **Crea backup automático** de configuración existente
- ✅ **Despliegue con Docker Compose** de 22 servicios
- ✅ **Healthchecks post-instalación** automáticos
- ✅ **Rollback automático** si algo falla
- ✅ **Logs detallados** de toda la instalación
- ✅ **Interfaz TUI con colores** para mejor experiencia

### Características de Seguridad

| Característica | Descripción |
|----------------|-------------|
| **Validación de Licencia** | RSA-4096 offline, verifica antes de instalar |
| **Verificación HWID** | Licencia ligada al hardware del servidor |
| **Backup Automático** | Copia de seguridad antes de modificar |
| **Rollback Inteligente** | Restauración automática si falla |
| **Logs Auditables** | Registro completo de cada operación |
| **Zero Telemetry** | 100% on-premise, sin phone-home |

---

## 💻 REQUISITOS DEL SISTEMA

### Hardware Mínimo

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8+ GB |
| **Disco** | 10 GB libres | 20+ GB |
| **Red** | 100 Mbps | 1 Gbps |

### Software Requerido

#### Linux (Ubuntu 20.04+ / Debian 11+)

```bash
# Dependencias esenciales
sudo apt update
sudo apt install -y docker.io docker-compose-v2 python3 python3-pip curl

# Librería cryptography
sudo pip3 install cryptography

# Iniciar Docker
sudo systemctl start docker
sudo systemctl enable docker

# Agregar usuario al grupo docker (opcional)
sudo usermod -aG docker $USER
newgrp docker
```

#### macOS (11+)

```bash
# Instalar Homebrew si no está instalado
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar dependencias
brew install docker docker-compose python3

# Instalar Docker Desktop
# Descargar desde: https://www.docker.com/products/docker-desktop

# Librería cryptography
pip3 install cryptography
```

#### Windows (WSL2)

```powershell
# En PowerShell (Administrator)
# Habilitar WSL2
wsl --install

# Instalar Ubuntu desde Microsoft Store
# Luego en WSL2:
```

```bash
# En Ubuntu WSL2
sudo apt update
sudo apt install -y docker.io python3 python3-pip curl

# Iniciar Docker
sudo service docker start

# Librería cryptography
sudo pip3 install cryptography
```

### Verificar Requisitos

```bash
# Docker
docker --version
# Esperado: Docker version 20.10+

# Docker Compose
docker compose version
# Esperado: Docker Compose version v2.0+

# Python
python3 --version
# Esperado: Python 3.8+

# Cryptography
python3 -c "import cryptography; print(cryptography.__version__)"
# Esperado: 40.0+
```

---

## 🔐 PRE-INSTALACIÓN

### Paso 1: Obtener HWID del Servidor

```bash
# Ejecutar script de obtención de HWID
./get-hwid.sh

# Salida esperada:
# ════════════════════════════════════════
#   RHINOMETRIC - Hardware ID Generator
# ════════════════════════════════════════
# 
# Hardware ID (HWID): A3F7C9E1B2D4F6A8
# 
# Envíe este HWID a RHINOMETRIC para obtener su licencia
```

**⚠️ IMPORTANTE**: Guarde este HWID, lo necesitará para solicitar su licencia.

### Paso 2: Solicitar Licencia a RHINOMETRIC

**Email**: licenses@rhinometric.com

**Asunto**: Solicitud de Licencia RHINOMETRIC v2.3.0

**Cuerpo del email**:

```
Empresa: [Su Empresa]
HWID: A3F7C9E1B2D4F6A8
Tipo de Licencia: [trial | annual | perpetual]
Número de Features: [básicas | completas]

Contacto:
- Nombre: [Su Nombre]
- Email: [su@email.com]
- Teléfono: [Opcional]
```

**Respuesta esperada**: Recibirá un archivo `cliente.lic` (1-2 KB)

### Paso 3: Colocar Licencia

```bash
# Crear directorio de licencias si no existe
mkdir -p licenses

# Copiar archivo de licencia recibido
cp /ruta/descarga/cliente.lic ./licenses/

# Verificar permisos
chmod 644 ./licenses/cliente.lic

# Verificar contenido (debe ser JSON)
cat ./licenses/cliente.lic
```

**Estructura esperada del archivo**:

```json
{
  "customer": "SuEmpresa",
  "type": "trial",
  "hwid": "A3F7C9E1B2D4F6A8",
  "issued_at": "2025-11-03T10:00:00Z",
  "expires": "2025-12-03",
  "features": ["monitoring", "alerting", "reporting"],
  "signature": "..."
}
```

### Paso 4: Verificar Licencia Manualmente (Opcional)

```bash
# Validar licencia antes de instalar
python3 validate_license.py

# Salida esperada si es válida:
# ✓ Licencia válida para: SuEmpresa
# ✓ Tipo: trial
# ✓ Expira: 2025-12-03
# ✓ Días restantes: 29
```

---

## 🚀 PROCESO DE INSTALACIÓN

### Ejecutar Instalador

```bash
# Navegar al directorio
cd /ruta/a/mi-proyecto/infrastructure/mi-proyecto

# Ejecutar instalador seguro
./install-secure.sh
```

### Flujo de Instalación Completo

```
╔════════════════════════════════════════════════════════════════════════╗
║                   RHINOMETRIC v2.3.0 - SECURE INSTALLER                ║
║        Observability Platform - On-Premise & GDPR Compliant           ║
╚════════════════════════════════════════════════════════════════════════╝


╔════════════════════════════════════════════════════════════════════════╗
║                      DETECCIÓN DE SISTEMA OPERATIVO                     ║
╚════════════════════════════════════════════════════════════════════════╝

[INFO] Detectando sistema operativo...
✓ Sistema: Linux (WSL2)
✓ Versión: Ubuntu 22.04.3 LTS

────────────────────────────────────────────────────────────────────────


╔════════════════════════════════════════════════════════════════════════╗
║                        VALIDACIÓN DE LICENCIA                          ║
╚════════════════════════════════════════════════════════════════════════╝

[INFO] Verificando licencia de RHINOMETRIC...
✓ Archivo de licencia encontrado
✓ Licencia verificada correctamente

Información de la licencia:
  Cliente: ClienteDemo
  Tipo: trial
  Expira: 2025-12-03
  Días restantes: 29
  Features: monitoring, alerting, reporting, ai_anomaly

────────────────────────────────────────────────────────────────────────


╔════════════════════════════════════════════════════════════════════════╗
║                     VERIFICACIÓN DE DEPENDENCIAS                       ║
╚════════════════════════════════════════════════════════════════════════╝

[INFO] Verificando Docker Engine...
✓ Docker Engine: 24.0.7
  → Docker daemon: activo

[INFO] Verificando Docker Compose...
✓ Docker Compose: v2.23.0

[INFO] Verificando Python...
✓ Python: 3.10.12

[INFO] Verificando librería cryptography de Python...
✓ cryptography: 41.0.7

✓ Git: 2.34.1 (opcional)

[INFO] Verificando espacio en disco...
✓ Espacio en disco: 157GB disponibles

────────────────────────────────────────────────────────────────────────


╔════════════════════════════════════════════════════════════════════════╗
║                       VERIFICACIÓN DE PUERTOS                          ║
╚════════════════════════════════════════════════════════════════════════╝

[INFO] Verificando disponibilidad de puertos críticos...

Verificando puertos necesarios para RHINOMETRIC:

✓ Puerto 3000 (Grafana): disponible
✓ Puerto 9090 (Prometheus): disponible
✓ Puerto 3100 (Loki): disponible
✓ Puerto 5432 (PostgreSQL): disponible
✓ Puerto 9093 (Alertmanager): disponible
✓ Puerto 8080 (Landing Page): disponible
✓ Puerto 8081 (Rhino API): disponible
✓ Puerto 9080 (Pushgateway): disponible
✓ Puerto 9115 (Blackbox Exporter): disponible

────────────────────────────────────────────────────────────────────────
✓ Todos los puertos necesarios están disponibles


╔════════════════════════════════════════════════════════════════════════╗
║                      RESUMEN PRE-INSTALACIÓN                           ║
╚════════════════════════════════════════════════════════════════════════╝

Configuración de instalación:

Versión:          RHINOMETRIC v2.3.0
Directorio:       /home/user/mi-proyecto/infrastructure/mi-proyecto
Compose File:     /home/user/mi-proyecto/.../docker-compose-v2.2.0.yml
Licencia:         /home/user/mi-proyecto/.../licenses/cliente.lic
Log File:         /home/user/.../install-secure-20251103-120000.log
Backup Dir:       /home/user/.../backup-20251103-120000

Servicios a desplegar:
  • Grafana (Visualización)
  • Prometheus (Métricas)
  • Loki (Logs)
  • Alertmanager (Alertas)
  • PostgreSQL (Base de datos)
  • Blackbox Exporter (Monitoreo)
  • Pushgateway (Métricas push)
  • License Monitor (Alertas de licencia)
  • Landing Page (Interfaz web)
  • + otros servicios de soporte

────────────────────────────────────────────────────────────────────────
¿Desea continuar con la instalación? [Y/n]: y


╔════════════════════════════════════════════════════════════════════════╗
║                         CREACIÓN DE BACKUP                             ║
╚════════════════════════════════════════════════════════════════════════╝

[INFO] Creando backup de configuración actual...
✓ docker-compose-v2.2.0.yml
✓ cliente.lic
✓ validate_license.py
✓ .env
✓ containers-before.txt

────────────────────────────────────────────────────────────────────────
✓ Backup completado


╔════════════════════════════════════════════════════════════════════════╗
║                    DESPLIEGUE DEL STACK RHINOMETRIC                    ║
╚════════════════════════════════════════════════════════════════════════╝

[===>] Descargando imágenes Docker...
Descargando imágenes necesarias...

[+] Pulling 22/22
 ✔ grafana Pulled
 ✔ prometheus Pulled
 ✔ loki Pulled
 ✔ alertmanager Pulled
 ✔ postgres Pulled
 ... (más servicios)

✓ Imágenes descargadas

[===>] Construyendo servicios personalizados...
Construyendo servicios personalizados...

[+] Building 45.2s (28/28) FINISHED
 => [license-monitor internal] load build definition
 => [landing internal] load metadata
 ... (más builds)

✓ Build completado

[===>] Levantando servicios...
Iniciando todos los servicios...

[+] Running 22/22
 ✔ Container rhinometric-postgres           Started
 ✔ Container rhinometric-loki               Started
 ✔ Container rhinometric-prometheus         Started
 ✔ Container rhinometric-grafana            Started
 ✔ Container rhinometric-alertmanager       Started
 ✔ Container rhinometric-license-monitor    Started
 ... (más contenedores)

✓ Servicios iniciados correctamente

────────────────────────────────────────────────────────────────────────


╔════════════════════════════════════════════════════════════════════════╗
║                      VERIFICACIÓN DE DESPLIEGUE                        ║
╚════════════════════════════════════════════════════════════════════════╝

[INFO] Esperando a que los servicios estén listos...
Esperando inicialización de servicios (30s)...

[████████████████████████████████████████████████] 100% - Inicializando

[INFO] Verificando estado de contenedores...

Estado de servicios:

✓ rhinometric-grafana: healthy
✓ rhinometric-prometheus: healthy
✓ rhinometric-loki: healthy
✓ rhinometric-postgres: healthy
✓ rhinometric-alertmanager: healthy
✓ rhinometric-license-monitor: running
✓ rhinometric-blackbox-exporter: running
✓ rhinometric-pushgateway: running
✓ rhinometric-landing: healthy
... (más servicios)

────────────────────────────────────────────────────────────────────────
Resumen: 22/22 servicios corriendo
✓ Todos los servicios están operativos


╔════════════════════════════════════════════════════════════════════════╗
║                  VERIFICACIÓN DE ACCESO A SERVICIOS                    ║
╚════════════════════════════════════════════════════════════════════════╝

[INFO] Probando acceso a servicios web...

Probando endpoints:

✓ Grafana: accesible (http://localhost:3000)
✓ Prometheus: accesible (http://localhost:9090)
✓ Alertmanager: accesible (http://localhost:9093)
✓ Landing: accesible (http://localhost:8080)

────────────────────────────────────────────────────────────────────────

Acceso a servicios:

  Grafana:       http://localhost:3000
                  Usuario: admin | Password: admin

  Prometheus:    http://localhost:9090
  Alertmanager:  http://localhost:9093
  Landing Page:  http://localhost:8080


╔════════════════════════════════════════════════════════════════════════╗
║                    INSTALACIÓN COMPLETADA EXITOSAMENTE                 ║
╚════════════════════════════════════════════════════════════════════════╝

🎉 ¡RHINOMETRIC v2.3.0 instalado correctamente!

Acceso a servicios:

  Grafana Dashboard:
    URL:      http://localhost:3000
    Usuario:  admin
    Password: admin

  Prometheus:        http://localhost:9090
  Alertmanager:      http://localhost:9093
  Landing Page:      http://localhost:8080

Comandos útiles:

  Ver logs:
    docker compose -f docker-compose-v2.2.0.yml logs -f [servicio]

  Estado de servicios:
    docker compose -f docker-compose-v2.2.0.yml ps

  Reiniciar servicios:
    docker compose -f docker-compose-v2.2.0.yml restart

  Detener todo:
    docker compose -f docker-compose-v2.2.0.yml down

Archivos generados:
  • Log de instalación: install-secure-20251103-120000.log
  • Backup: backup-20251103-120000

Soporte:
  Email: support@rhinometric.com
  Docs:  https://docs.rhinometric.com

────────────────────────────────────────────────────────────────────────
```

---

## 🔍 FLUJO DE VALIDACIÓN

### Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────────┐
│                      INICIO INSTALACIÓN                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                   ┌─────────────────────┐
                   │  Detectar OS        │
                   │  (Linux/Mac/Win)    │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │  Validar Licencia   │◄────── CRÍTICO
                   │  (RSA-4096)         │
                   └──────────┬──────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
              ✓ VÁLIDA            ✗ INVÁLIDA
                    │                   │
                    │                   ▼
                    │            [ABORT INSTALACIÓN]
                    │
                    ▼
         ┌─────────────────────┐
         │ Verificar           │
         │ Dependencias        │
         │ (Docker, Python)    │
         └──────────┬──────────┘
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
    ✓ TODO OK          ✗ FALTA ALGO
          │                   │
          │                   ▼
          │          [MOSTRAR GUÍA]
          │          [PERMITIR CONTINUAR?]
          │                   │
          │                   ├─ NO ──► [ABORT]
          │                   │
          │                   └─ SI ──► [CONTINUAR CON WARNING]
          │                               │
          └───────────────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │  Verificar Puertos  │
                   │  (3000, 9090, etc)  │
                   └──────────┬──────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
              ✓ LIBRES          ✗ EN USO
                    │                   │
                    │                   ▼
                    │          [MOSTRAR CONFLICTOS]
                    │          [PERMITIR CONTINUAR?]
                    │                   │
                    │                   ├─ NO ──► [ABORT]
                    │                   │
                    │                   └─ SI ──► [CONTINUAR]
                    │                               │
                    └───────────────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │  Mostrar Resumen    │
                   │  Pre-Instalación    │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │  Confirmar Usuario  │
                   │  [Y/n]              │
                   └──────────┬──────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
                  SI                  NO
                    │                   │
                    │                   ▼
                    │            [CANCELAR]
                    │
                    ▼
         ┌─────────────────────┐
         │  Crear Backup       │◄────── IMPORTANTE
         │  (compose, .env)    │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Docker Pull        │
         │  (Descargar imgs)   │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Docker Build       │
         │  (Servicios custom) │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Docker Compose Up  │
         │  (Levantar stack)   │
         └──────────┬──────────┘
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
    ✓ SUCCESS           ✗ ERROR
          │                   │
          │                   ▼
          │          ┌─────────────────────┐
          │          │  ROLLBACK           │
          │          │  - Stop containers  │
          │          │  - Restore backup   │
          │          │  - Show logs        │
          │          └─────────┬───────────┘
          │                    │
          │                    ▼
          │              [ABORT CON LOG]
          │
          ▼
┌─────────────────────┐
│  Healthchecks       │
│  (Wait 30s)         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Verificar Estado   │
│  de Contenedores    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Test Endpoints     │
│  (HTTP checks)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Mostrar Reporte    │
│  Final + URLs       │
└──────────┬──────────┘
           │
           ▼
     ✅ COMPLETADO
```

### Puntos de Validación Críticos

#### 1. Validación de Licencia

**Archivo**: `validate_license.py`  
**Método**: RSA-PSS con SHA-256  
**Clave**: `security/rhinometric_public.pem` (800 bytes)

**Validaciones realizadas**:
- ✓ Archivo `.lic` existe y es accesible
- ✓ JSON bien formado
- ✓ Campos obligatorios presentes (`customer`, `hwid`, `expires`, `signature`)
- ✓ Firma RSA válida (verificada con clave pública)
- ✓ HWID coincide con el servidor actual
- ✓ Fecha de expiración no superada
- ✓ Formato de fecha ISO 8601 correcto

**Si falla**: Instalación abortada inmediatamente.

#### 2. Verificación de Dependencias

**Verificaciones realizadas**:

| Dependencia | Versión Mínima | Verificación |
|-------------|----------------|--------------|
| **Docker Engine** | 20.10.0 | `docker --version` |
| **Docker Daemon** | N/A | `docker info` |
| **Docker Compose** | v2.0.0 | `docker compose version` |
| **Python 3** | 3.8.0 | `python3 --version` |
| **cryptography** | 40.0.0 | `python3 -c "import cryptography"` |
| **Espacio disco** | 10 GB | `df -BG` |

**Si falla**: Muestra guía de instalación, permite continuar con warning.

#### 3. Verificación de Puertos

**Puertos críticos verificados**:

```bash
# Comando usado (multiplataforma)
netstat -tuln | grep ":PORT "    # Linux
ss -tuln | grep ":PORT "         # Linux moderno
lsof -i :PORT                    # macOS
```

**Puertos verificados**:
- 3000 (Grafana)
- 9090 (Prometheus)
- 3100 (Loki)
- 5432 (PostgreSQL)
- 9093 (Alertmanager)
- 8080 (Landing)
- 8081 (Rhino API)
- 9080 (Pushgateway)
- 9115 (Blackbox Exporter)

**Si hay conflictos**: Muestra servicios en conflicto, permite continuar.

---

## 🐛 TROUBLESHOOTING

### Error: "Licencia no encontrada"

**Síntoma**:
```
[ERROR] Archivo de licencia no encontrado: ./licenses/cliente.lic
✗ No se encontró el archivo de licencia
```

**Solución**:
```bash
# 1. Verificar que el archivo existe
ls -la licenses/cliente.lic

# 2. Si no existe, obtener HWID y solicitar licencia
./get-hwid.sh
# Enviar HWID a licenses@rhinometric.com

# 3. Cuando reciba cliente.lic, colocarlo en:
mkdir -p licenses
cp /ruta/descarga/cliente.lic ./licenses/
chmod 644 ./licenses/cliente.lic
```

### Error: "Licencia inválida o expirada"

**Síntoma**:
```
[ERROR] Validación de licencia falló
✗ Licencia inválida o expirada

Detalles del error:
  ERROR: HWID no coincide
  Esperado: A3F7C9E1B2D4F6A8
  Actual: B4D8F2A9E3C7D1F5
```

**Causa**: La licencia fue generada para otro servidor.

**Solución**:
```bash
# 1. Verificar HWID actual
./get-hwid.sh

# 2. Solicitar nueva licencia con HWID correcto a RHINOMETRIC
# 3. Reemplazar archivo de licencia
```

### Error: "Docker daemon no está corriendo"

**Síntoma**:
```
✓ Docker Engine: 24.0.7
  → Docker daemon: inactivo
```

**Solución**:

**Linux**:
```bash
sudo systemctl start docker
sudo systemctl enable docker

# Verificar
docker info
```

**macOS**:
```bash
# Abrir Docker Desktop desde Applications
open -a Docker

# Esperar a que se inicie (icono en menu bar)
```

**Windows WSL2**:
```bash
# En WSL2
sudo service docker start

# O en PowerShell (Administrator)
wsl --shutdown
wsl
sudo service docker start
```

### Error: "Puerto en uso"

**Síntoma**:
```
✗ Puerto 3000 (Grafana): EN USO

⚠️  ADVERTENCIA: Algunos puertos están en uso

Puertos en conflicto:
  • 3000:Grafana
```

**Solución**:

**Opción 1**: Detener servicio que usa el puerto
```bash
# Identificar proceso
sudo lsof -i :3000
# O
sudo netstat -tulpn | grep :3000

# Detener proceso
sudo kill -9 <PID>
```

**Opción 2**: Cambiar puerto en docker-compose
```yaml
# En docker-compose-v2.2.0.yml
services:
  grafana:
    ports:
      - "3001:3000"  # Cambiar 3000 a 3001
```

### Error: "Falta librería cryptography"

**Síntoma**:
```
✗ cryptography: no instalada
  → Instalar con: pip3 install cryptography
```

**Solución**:
```bash
# Linux/WSL2
sudo pip3 install cryptography

# macOS (sin sudo)
pip3 install cryptography

# Verificar
python3 -c "import cryptography; print(cryptography.__version__)"
```

### Error: "Error al construir servicios"

**Síntoma**:
```
[===>] Construyendo servicios personalizados...
ERROR: failed to solve: process "/bin/sh -c apk add --no-cache ..." 
```

**Causa**: Problemas de red o dependencias faltantes en Dockerfile.

**Solución**:
```bash
# 1. Verificar conexión a internet
ping -c 3 google.com

# 2. Limpiar cache de Docker
docker builder prune -a

# 3. Reintentar build manualmente
docker compose -f docker-compose-v2.2.0.yml build --no-cache

# 4. Ver logs detallados
docker compose -f docker-compose-v2.2.0.yml build --progress=plain
```

### Error: "Servicio no está healthy"

**Síntoma**:
```
⚠ rhinometric-grafana: starting
⚠ rhinometric-prometheus: unhealthy
```

**Solución**:
```bash
# 1. Ver logs del servicio problemático
docker logs rhinometric-prometheus

# 2. Verificar healthcheck
docker inspect rhinometric-prometheus | grep -A 10 Health

# 3. Reiniciar servicio específico
docker compose -f docker-compose-v2.2.0.yml restart prometheus

# 4. Si persiste, verificar licencia del servicio
docker exec rhinometric-prometheus cat /opt/rhinometric/license/cliente.lic
```

### Servicio no accesible (HTTP timeout)

**Síntoma**:
```
⚠ Grafana: no responde (puede necesitar más tiempo)
```

**Causa**: Servicios tardan más en inicializar (especialmente PostgreSQL, Grafana).

**Solución**:
```bash
# 1. Esperar 1-2 minutos adicionales
sleep 60

# 2. Verificar estado
docker compose -f docker-compose-v2.2.0.yml ps

# 3. Verificar logs
docker compose -f docker-compose-v2.2.0.yml logs grafana | tail -50

# 4. Test manual
curl -v http://localhost:3000
```

---

## 🔄 ROLLBACK

### Rollback Automático

El instalador realiza rollback automático si:
- Falla el build de imágenes
- Falla el `docker compose up`
- Error crítico durante el despliegue

**Proceso automático**:
```bash
1. Detener todos los contenedores
2. Restaurar docker-compose.yml desde backup
3. Restaurar .env desde backup
4. Mostrar logs de error
5. Mantener backup intacto para análisis
```

### Rollback Manual

Si necesita revertir manualmente:

```bash
# 1. Detener servicios actuales
docker compose -f docker-compose-v2.2.0.yml down

# 2. Listar backups disponibles
ls -la backup-*/

# 3. Restaurar desde backup específico
BACKUP_DIR="backup-20251103-120000"

cp ${BACKUP_DIR}/docker-compose-v2.2.0.yml ./
cp ${BACKUP_DIR}/.env ./
cp ${BACKUP_DIR}/cliente.lic ./licenses/

# 4. Ver qué contenedores había antes
cat ${BACKUP_DIR}/containers-before.txt

# 5. Limpiar contenedores nuevos (opcional)
docker compose -f docker-compose-v2.2.0.yml down --volumes --remove-orphans

# 6. Reiniciar con configuración anterior (si había)
docker compose -f docker-compose-v2.2.0.yml up -d
```

### Limpiar Instalación Fallida

```bash
# Detener todo
docker compose -f docker-compose-v2.2.0.yml down --volumes --remove-orphans

# Limpiar imágenes huérfanas
docker image prune -a

# Limpiar volúmenes huérfanos
docker volume prune

# Limpiar redes huérfanas
docker network prune

# Reset completo (⚠️ CUIDADO: borra TODO de Docker)
docker system prune -a --volumes
```

---

## ❓ FAQ

### ¿Puedo instalar sin licencia para testing?

**No**. El instalador requiere una licencia válida antes de desplegar. Para testing:

```bash
# Opción 1: Solicitar licencia trial (15 días)
# Email: licenses@rhinometric.com
# Asunto: Solicitud Trial RHINOMETRIC

# Opción 2: Usar licencia de desarrollo (solo para Rhinometric)
# Contactar internamente
```

### ¿La instalación modifica mi Docker existente?

**No**. El instalador:
- ✓ Solo crea contenedores con prefijo `rhinometric-*`
- ✓ Usa red dedicada `rhinometric_network_v22`
- ✓ Usa volúmenes dedicados `rhinometric_data_*`
- ✓ No afecta otros contenedores o stacks

### ¿Qué pasa si cancelo la instalación (Ctrl+C)?

El instalador tiene un `trap` para SIGINT/SIGTERM:

```bash
# Si cancela durante:
# - Validaciones: No pasa nada, sale limpiamente
# - Despliegue: Pregunta si desea rollback
# - Post-despliegue: Servicios quedan corriendo (puede hacer down manual)
```

### ¿Puedo cambiar puertos después de instalar?

**Sí**:

```bash
# 1. Detener servicios
docker compose -f docker-compose-v2.2.0.yml down

# 2. Editar docker-compose-v2.2.0.yml
# Cambiar puertos en sección 'ports'

# 3. Re-levantar
docker compose -f docker-compose-v2.2.0.yml up -d
```

### ¿Cómo actualizo la licencia sin reinstalar?

```bash
# 1. Detener license-monitor
docker compose -f docker-compose-v2.2.0.yml stop license-monitor

# 2. Reemplazar licencia
cp nueva-cliente.lic ./licenses/cliente.lic

# 3. Reiniciar servicios (validan licencia en startup)
docker compose -f docker-compose-v2.2.0.yml restart

# 4. Verificar nueva licencia
docker logs rhinometric-license-monitor | tail -20
```

### ¿Los logs de instalación son seguros?

**Sí**. Los logs NO contienen:
- ❌ Passwords
- ❌ Claves privadas
- ❌ Secretos de .env
- ❌ Datos de licencia completos

Solo registran:
- ✓ Comandos ejecutados
- ✓ Outputs de verificaciones
- ✓ Errores y warnings
- ✓ Timestamps de eventos

### ¿Puedo ejecutar el instalador múltiples veces?

**Sí**, pero:

1. **Primera vez**: Instalación completa
2. **Siguientes veces**: Actualizará servicios existentes

**Recomendación**: Hacer `down` antes de reinstalar:
```bash
docker compose -f docker-compose-v2.2.0.yml down
./install-secure.sh
```

### ¿Funciona detrás de un proxy corporativo?

**Sí**, configure variables de entorno:

```bash
export HTTP_PROXY=http://proxy.empresa.com:8080
export HTTPS_PROXY=http://proxy.empresa.com:8080
export NO_PROXY=localhost,127.0.0.1

# Luego ejecutar
./install-secure.sh
```

### ¿Cómo verifico que la instalación fue exitosa?

```bash
# 1. Todos los contenedores corriendo
docker compose -f docker-compose-v2.2.0.yml ps
# Esperado: 22/22 servicios "Up"

# 2. Grafana accesible
curl -s http://localhost:3000 | grep "Grafana"

# 3. Prometheus accesible
curl -s http://localhost:9090/-/healthy

# 4. License monitor corriendo
docker logs rhinometric-license-monitor | grep "Daemon iniciado"

# 5. Ver log de instalación
tail -100 install-secure-*.log
```

---

## 📚 RECURSOS ADICIONALES

### Documentación Relacionada

- **`LICENSE_SYSTEM_OFFLINE.md`**: Sistema de licenciamiento completo
- **`FASE_D_TEST_REPORT.md`**: Tests del sistema de alertas
- **`CLOUD_DEPLOYMENT_GUIDE.md`**: Despliegue en cloud providers
- **`docker-compose-v2.2.0.yml`**: Stack completo de servicios

### Scripts Útiles

| Script | Propósito |
|--------|-----------|
| `get-hwid.sh` | Obtener HWID del servidor |
| `validate_license.py` | Validar licencia manualmente |
| `check-health.sh` | Verificar estado de servicios |
| `check_logs.sh` | Ver logs agregados |
| `docker-cleanup-auto.sh` | Limpiar recursos Docker |

### Comandos de Mantenimiento

```bash
# Ver todos los servicios
docker compose -f docker-compose-v2.2.0.yml ps

# Logs de un servicio específico
docker compose -f docker-compose-v2.2.0.yml logs -f grafana

# Reiniciar un servicio
docker compose -f docker-compose-v2.2.0.yml restart prometheus

# Actualizar un servicio
docker compose -f docker-compose-v2.2.0.yml up -d --no-deps --build grafana

# Ver uso de recursos
docker stats

# Ver volúmenes
docker volume ls | grep rhinometric

# Backup de volúmenes
docker run --rm -v rhinometric_data_v22:/data -v $(pwd):/backup \
  alpine tar czf /backup/rhinometric-backup-$(date +%Y%m%d).tar.gz /data
```

---

## 📞 SOPORTE

### Contacto RHINOMETRIC

- **Email Licencias**: licenses@rhinometric.com
- **Email Soporte**: support@rhinometric.com
- **Documentación**: https://docs.rhinometric.com
- **Tickets**: https://support.rhinometric.com

### Información para Ticket de Soporte

Cuando solicite soporte, incluya:

1. **Log de instalación**: `install-secure-YYYYMMDD-HHMMSS.log`
2. **Versión de RHINOMETRIC**: `2.3.0`
3. **Sistema operativo**: Output de `uname -a`
4. **Docker version**: Output de `docker --version`
5. **Docker Compose version**: Output de `docker compose version`
6. **Estado de servicios**: Output de `docker compose ps`
7. **Logs de servicios con error**: `docker logs <container>`

### Reporte de Bugs

Para reportar bugs, use el formato:

```markdown
**Versión**: RHINOMETRIC v2.3.0
**OS**: Ubuntu 22.04 (WSL2)
**Docker**: 24.0.7
**Compose**: v2.23.0

**Descripción del problema**:
[Describa qué pasó]

**Pasos para reproducir**:
1. [Paso 1]
2. [Paso 2]
3. [Error ocurre]

**Comportamiento esperado**:
[Qué debería pasar]

**Logs**:
```
[Pegue logs relevantes]
```

**Capturas** (opcional):
[Adjunte screenshots]
```

---

## 📝 CHANGELOG

### v2.3.0 (2025-11-03)

**Nuevo**:
- ✨ Instalador seguro multiplataforma (`install-secure.sh`)
- ✨ Validación de licencia pre-instalación (RSA-4096)
- ✨ Verificación automática de dependencias
- ✨ Chequeo de puertos con detección de conflictos
- ✨ Backup automático pre-instalación
- ✨ Rollback automático en caso de error
- ✨ TUI con colores y progress bars
- ✨ Logs detallados de instalación
- ✨ Healthchecks post-despliegue
- ✨ Tests de acceso a servicios

**Mejoras**:
- 🔧 Compatibilidad Linux / macOS / Windows WSL2
- 🔧 Detección inteligente de sistema operativo
- 🔧 Manejo de errores robusto
- 🔧 Confirmaciones interactivas
- 🔧 Mensajes de error descriptivos

**Seguridad**:
- 🔒 Validación obligatoria de licencia
- 🔒 Verificación de HWID
- 🔒 No expone secrets en logs
- 🔒 100% offline (excepto docker pull)

---

**Última actualización**: 3 de noviembre de 2025  
**Versión del documento**: 1.0.0  
**Autor**: RHINOMETRIC Team  
**Licencia**: Proprietary - All Rights Reserved
