# 🚀 Rhinometric v2.1.0 - Guía de Instalación Completa

**Instalación paso a paso para Linux, macOS y Windows**

---

## 📋 Tabla de Contenidos

1. [Pre-requisitos](#pre-requisitos)
2. [Descarga e Instalación](#descarga-e-instalación)
3. [Instalación Linux/macOS](#instalación-linux-macos)
4. [Instalación Windows](#instalación-windows)
5. [Configuración Post-Instalación](#configuración-post-instalación)
6. [Verificación](#verificación)
7. [Desinstalación](#desinstalación)

---

## ✅ Pre-requisitos

### Software Requerido

#### 1. Docker Desktop (OBLIGATORIO)

**Linux**:
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Verificar
docker --version  # Debe mostrar 20.10+
```

**macOS**:
1. Descargar desde: https://www.docker.com/products/docker-desktop/
2. Instalar `.dmg`
3. Abrir Docker Desktop
4. Esperar que inicie completamente (ícono en barra superior)

**Windows**:
1. Descargar desde: https://www.docker.com/products/docker-desktop/
2. Ejecutar instalador
3. Habilitar WSL 2 si se solicita
4. Reiniciar PC
5. Abrir Docker Desktop y esperar inicio completo

#### 2. Git (RECOMENDADO)

**Linux**:
```bash
sudo apt-get install git  # Ubuntu/Debian
sudo yum install git       # RHEL/CentOS
```

**macOS**:
```bash
brew install git  # Con Homebrew
# O descargar desde: https://git-scm.com/download/mac
```

**Windows**:
- Descargar desde: https://git-scm.com/download/win
- Instalar con opciones por defecto

### Hardware Mínimo

| Componente | Mínimo | Recomendado |
|-----------|--------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Disco | 50 GB libres | 200 GB SSD |
| Red | 100 Mbps | 1 Gbps |

### Puertos Disponibles

Verificar que estos puertos NO estén en uso:

```bash
# Linux/macOS
netstat -tuln | grep -E '3000|5000|5432|8090|8091|8092|9090'

# Windows (PowerShell)
netstat -ano | findstr -E "3000 5000 5432 8090 8091 8092 9090"
```

Si algún puerto está ocupado, detener el servicio o cambiar el puerto en `docker-compose-v2.1.0.yml`.

---

## 📥 Descarga e Instalación

### Opción 1: Clonar desde GitHub (Recomendado)

```bash
git clone https://github.com/Rafael2712/mi-proyecto.git
cd mi-proyecto/infrastructure/mi-proyecto/rhinometric-trial-v2.1.0-universal
```

### Opción 2: Descargar Release ZIP

1. Ir a: https://github.com/Rafael2712/mi-proyecto/releases
2. Descargar `rhinometric-trial-v2.1.0-universal.tar.gz`
3. Extraer:

```bash
# Linux/macOS
tar -xzf rhinometric-trial-v2.1.0-universal.tar.gz
cd rhinometric-trial-v2.1.0-universal

# Windows (PowerShell)
Expand-Archive rhinometric-trial-v2.1.0-universal.zip
cd rhinometric-trial-v2.1.0-universal
```

---

## 🐧 Instalación Linux/macOS

### Método 1: Instalador Automático (Recomendado)

```bash
# 1. Dar permisos de ejecución
chmod +x install.sh

# 2. Ejecutar instalador
./install.sh

# El instalador:
# ✅ Verifica Docker instalado
# ✅ Verifica puertos disponibles
# ✅ Crea .env con contraseñas seguras
# ✅ Descarga imágenes Docker
# ✅ Inicia todos los servicios
# ✅ Espera a que estén healthy
# ✅ Muestra URLs de acceso
```

**Salida esperada**:

```
╔════════════════════════════════════════════════════════════════╗
║  Rhinometric v2.1.0 - Observability Platform                 ║
╚════════════════════════════════════════════════════════════════╝

[STEP] Checking Docker installation...
✅ Docker 24.0.6 found
✅ Docker daemon is running

[STEP] Checking Docker Compose...
✅ Docker Compose v2.23.0 found

[STEP] Checking port availability...
✅ All required ports are available

[STEP] Checking disk space...
✅ 150GB available

[STEP] Setting up environment configuration...
✅ Environment configured with secure passwords
✅ Credentials saved to credentials.txt (permissions: 600)

[STEP] Deploying Rhinometric stack...
Pulling Docker images (this may take 5-10 minutes on first run)...
[+] Pulling 16/16
 ✔ postgres Pulled
 ✔ redis Pulled
 ✔ grafana Pulled
 ... (más servicios)
 
Starting services...
[+] Running 16/16
 ✔ Container rhinometric-postgres    Healthy
 ✔ Container rhinometric-redis       Healthy
 ✔ Container rhinometric-grafana     Healthy
 ... (más servicios)
 
✅ All services started

[STEP] Waiting for services to become healthy...
Healthy containers: 16/16  
✅ Core services are healthy

╔════════════════════════════════════════════════════════════════╗
║  Installation Complete!                                      ║
╚════════════════════════════════════════════════════════════════╝

🌐 Access URLs:
  Grafana:              http://localhost:3000
  Prometheus:           http://localhost:9090
  License Server:       http://localhost:5000/api/docs
  API Connector UI:     http://localhost:8091
  License Management:   http://localhost:8092

🔐 Credentials:
  Saved in: credentials.txt
  Grafana username: admin

📋 Quick Commands:
  View logs:        docker compose -f docker-compose-v2.1.0.yml logs -f
  Check status:     docker compose -f docker-compose-v2.1.0.yml ps
  Stop services:    docker compose -f docker-compose-v2.1.0.yml down
  Restart:          docker compose -f docker-compose-v2.1.0.yml restart
```

### Método 2: Instalación Manual

```bash
# 1. Copiar y configurar .env
cp .env.example .env
nano .env  # O usar vim, vi, etc.

# Configurar:
POSTGRES_PASSWORD=tu_password_seguro
REDIS_PASSWORD=tu_password_seguro
GRAFANA_PASSWORD=tu_password_seguro

# 2. Descargar imágenes
docker compose -f docker-compose-v2.1.0.yml pull

# 3. Iniciar servicios
docker compose -f docker-compose-v2.1.0.yml up -d

# 4. Esperar a que estén healthy (2-3 minutos)
watch docker compose -f docker-compose-v2.1.0.yml ps

# 5. Verificar logs
docker compose -f docker-compose-v2.1.0.yml logs -f
```

---

## 🪟 Instalación Windows

### Método 1: Instalador PowerShell (Recomendado)

```powershell
# 1. Abrir PowerShell como Administrador
# Botón derecho en PowerShell → "Ejecutar como administrador"

# 2. Navegar al directorio
cd C:\Users\TuUsuario\Downloads\rhinometric-trial-v2.1.0-universal

# 3. Habilitar ejecución de scripts (solo primera vez)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 4. Ejecutar instalador
.\install.ps1

# El instalador hace lo mismo que en Linux/macOS
```

**Solución de problemas comunes**:

```powershell
# Error: "No se puede ejecutar scripts"
Set-ExecutionPolicy Bypass -Scope Process

# Error: "Docker no encontrado"
# - Verificar Docker Desktop esté running
# - Reiniciar PowerShell
# - Verificar: docker --version

# Error: "Puertos ocupados"
# - Detener servicios conflictivos:
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process
```

### Método 2: Instalación Manual (PowerShell)

```powershell
# 1. Copiar .env
Copy-Item .env.example .env
notepad .env  # Configurar contraseñas

# 2. Descargar imágenes
docker compose -f docker-compose-v2.1.0.yml pull

# 3. Iniciar servicios
docker compose -f docker-compose-v2.1.0.yml up -d

# 4. Verificar estado
docker compose -f docker-compose-v2.1.0.yml ps

# 5. Ver logs
docker compose -f docker-compose-v2.1.0.yml logs -f
```

---

## ⚙️ Configuración Post-Instalación

### 1. Configurar Licencia (Si ya la tienes)

```bash
# Editar .env
nano .env  # Linux/macOS
notepad .env  # Windows

# Agregar al final:
LICENSE_KEY=RHINO-TRIAL-2025-ABC123XYZ456

# Reiniciar License Server
docker compose -f docker-compose-v2.1.0.yml restart license-server-v2
```

### 2. Configurar Email (Opcional)

Para envío automático de licencias:

```bash
# Editar .env
SMTP_HOST=smtp.zoho.eu
SMTP_PORT=465
SMTP_USER=tu_email@tudominio.com
SMTP_PASSWORD=tu_app_password_zoho
SMTP_FROM=tu_email@tudominio.com

# Reiniciar
docker compose -f docker-compose-v2.1.0.yml restart license-server-v2
```

**Generar App Password en Zoho**:
1. Ir a: https://accounts.zoho.com/home#security/security
2. Click en "App Passwords"
3. Generar password para "Rhinometric"
4. Copiar y pegar en `.env`

### 3. Cambiar Contraseña de Grafana

```bash
# Primer login en http://localhost:3000
# Usuario: admin
# Password: Ver credentials.txt

# Grafana te obligará a cambiar la contraseña
# Recomendación: Usar password manager (1Password, LastPass, Bitwarden)
```

### 4. Configurar Alertas Email (Opcional)

Editar `prometheus/alertmanager/config.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.zoho.eu:587'
  smtp_from: 'alertas@tudominio.com'
  smtp_auth_username: 'alertas@tudominio.com'
  smtp_auth_password: 'tu_app_password'

route:
  receiver: 'email-alerts'

receivers:
  - name: 'email-alerts'
    email_configs:
      - to: 'ops@tuempresa.com'
        send_resolved: true
```

Reiniciar Alertmanager:
```bash
docker compose -f docker-compose-v2.1.0.yml restart alertmanager
```

---

## ✅ Verificación

### 1. Verificar Todos los Servicios Running

```bash
docker compose -f docker-compose-v2.1.0.yml ps
```

**Salida esperada**: 16 servicios con estado `Up` y `(healthy)`:

```
NAME                              STATUS                    PORTS
rhinometric-grafana               Up 5 minutes (healthy)    0.0.0.0:3000->3000/tcp
rhinometric-prometheus            Up 5 minutes (healthy)    0.0.0.0:9090->9090/tcp
rhinometric-postgres              Up 5 minutes (healthy)    0.0.0.0:5432->5432/tcp
... (13 servicios más)
```

### 2. Verificar URLs Accesibles

```bash
# Linux/macOS
curl -I http://localhost:3000  # Grafana - debe retornar 200
curl -I http://localhost:9090  # Prometheus - debe retornar 200
curl http://localhost:5000/api/health  # License Server - JSON con "status": "healthy"

# Windows (PowerShell)
Invoke-WebRequest -Uri http://localhost:3000 -Method Head
Invoke-WebRequest -Uri http://localhost:9090 -Method Head
Invoke-WebRequest -Uri http://localhost:5000/api/health
```

### 3. Verificar Dashboards en Grafana

1. Abrir http://localhost:3000
2. Login (admin + password de credentials.txt)
3. Ir a Dashboards → Browse
4. Verificar que existen 8 dashboards:
   - System Overview
   - Database Health
   - Container Metrics
   - API Monitoring
   - Logs Explorer
   - Distributed Tracing
   - License Management
   - Alerting Dashboard

### 4. Verificar Prometheus Targets

1. Abrir http://localhost:9090/targets
2. Verificar que todos los targets estén `UP` (color verde):
   - node-exporter (métricas del sistema)
   - postgres-exporter (métricas de PostgreSQL)
   - prometheus (self-monitoring)
   - otel-collector (trazas)

### 5. Test de Licencia (Opcional)

```bash
curl -X POST http://localhost:5000/api/admin/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test User",
    "client_email": "test@example.com",
    "client_company": "Test Company",
    "license_type": "trial"
  }'
```

Debe retornar JSON con la licencia creada.

---

## 🗑️ Desinstalación

### Desinstalación Completa (Borra TODO)

```bash
# Detener servicios
docker compose -f docker-compose-v2.1.0.yml down

# Borrar volúmenes (CUIDADO: Elimina datos permanentemente)
docker compose -f docker-compose-v2.1.0.yml down -v

# Borrar imágenes
docker images | grep rhinometric | awk '{print $3}' | xargs docker rmi

# Verificar
docker ps -a | grep rhinometric  # No debe mostrar nada
```

### Desinstalación Conservando Datos

```bash
# Solo detener servicios (conserva volúmenes)
docker compose -f docker-compose-v2.1.0.yml down

# Para volver a iniciar más tarde:
docker compose -f docker-compose-v2.1.0.yml up -d
```

### Limpieza de Docker (Liberar Espacio)

```bash
# Ver uso de disco
docker system df

# Limpiar todo lo no usado
docker system prune -a --volumes

# ADVERTENCIA: Esto borrará:
# - Contenedores detenidos
# - Redes no usadas
# - Imágenes sin contenedores
# - Volúmenes no montados
```

---

## 🆘 Troubleshooting Instalación

### Problema: Docker no está instalado

**Error**: `docker: command not found`

**Solución**:
- Instalar Docker Desktop (ver sección Pre-requisitos)
- Verificar `docker --version`
- Reiniciar terminal

### Problema: Permisos denegados (Linux)

**Error**: `permission denied while trying to connect to the Docker daemon socket`

**Solución**:
```bash
sudo usermod -aG docker $USER
newgrp docker
# O reiniciar sesión
```

### Problema: Puertos ocupados

**Error**: `Error starting userland proxy: listen tcp4 0.0.0.0:3000: bind: address already in use`

**Solución**:
```bash
# Identificar qué proceso usa el puerto
sudo lsof -i :3000  # Linux/macOS
netstat -ano | findstr :3000  # Windows

# Detener proceso o cambiar puerto en docker-compose-v2.1.0.yml
```

### Problema: Sin espacio en disco

**Error**: `no space left on device`

**Solución**:
```bash
# Limpiar Docker
docker system prune -a --volumes

# Verificar espacio
df -h  # Linux/macOS
Get-PSDrive  # Windows
```

### Problema: Servicios quedan en "Restarting"

**Síntomas**: `docker ps` muestra servicios reiniciando constantemente

**Solución**:
```bash
# Ver logs del servicio problemático
docker compose -f docker-compose-v2.1.0.yml logs <servicio>

# Causas comunes:
# 1. Configuración incorrecta en .env
# 2. Puerto ocupado
# 3. Falta de recursos (RAM/CPU)

# Verificar recursos:
docker stats

# Si es falta de RAM, aumentar límites en Docker Desktop:
# Settings → Resources → Memory → Aumentar a 8GB mínimo
```

---

## 📞 Soporte Instalación

Si la instalación falla después de seguir esta guía:

1. **Recopilar información**:
   ```bash
   # Sistema operativo
   uname -a  # Linux/macOS
   systeminfo  # Windows
   
   # Docker version
   docker --version
   docker compose version
   
   # Logs completos
   docker compose -f docker-compose-v2.1.0.yml logs > logs.txt
   ```

2. **Contactar soporte**:
   - Email: soporte@rhinometric.com
   - Asunto: "Instalación fallida v2.1.0"
   - Adjuntar: logs.txt + información del sistema

3. **GitHub Issues**:
   - https://github.com/Rafael2712/mi-proyecto/issues
   - Template: "Installation Problem"

---

**© 2025 Rhinometric. Todos los derechos reservados.**

Versión del documento: 2.1.0  
Última actualización: Octubre 2025

---

> **Nota**: Para convertir a PDF:
> ```bash
> pandoc guia_instalacion.md -o guia_instalacion.pdf --toc --toc-depth=2
> ```
