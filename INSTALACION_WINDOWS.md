# 🪟 MANUAL DE INSTALACIÓN - WINDOWS 10/11

**Rhinometric v2.1.0 Trial**  
**Tiempo estimado**: 15-20 minutos  
**Nivel**: Principiante

---

## 📋 REQUISITOS PREVIOS

### **Hardware Mínimo**
- ✅ Procesador: Intel i5 / AMD Ryzen 5 (2+ cores)
- ✅ RAM: 4 GB disponible (8 GB recomendado)
- ✅ Disco: 20 GB libres (SSD preferido)
- ✅ Red: Conexión a internet (10+ Mbps)

### **Software Requerido**

#### 1. **Windows 10/11** (64-bit)
- Versión: 20H2 o superior
- Verificar: `Win + R` → `winver` → Enter

#### 2. **Docker Desktop**
- Versión: 4.25.0 o superior
- Descarga: https://www.docker.com/products/docker-desktop/

#### 3. **Git for Windows** (incluye Git Bash)
- Versión: 2.40.0 o superior
- Descarga: https://git-scm.com/download/win

#### 4. **(Opcional) Windows Terminal**
- Recomendado para mejor experiencia
- Descarga desde Microsoft Store

---

## 🔧 PASO 1: INSTALAR DOCKER DESKTOP

### **1.1 Descargar Docker Desktop**

1. Ve a: https://www.docker.com/products/docker-desktop/
2. Click en **"Download for Windows"**
3. Espera a que descargue `Docker Desktop Installer.exe` (~600 MB)

### **1.2 Ejecutar Instalador**

1. **Doble click** en `Docker Desktop Installer.exe`
2. Acepta el UAC (User Account Control) → **"Sí"**
3. En la pantalla de configuración:
   - ✅ **Marcar**: "Use WSL 2 instead of Hyper-V"
   - ✅ **Marcar**: "Add shortcut to desktop"
4. Click **"Ok"** → Espera instalación (3-5 minutos)
5. Click **"Close and restart"**

### **1.3 Verificar Instalación**

Después del reinicio:

1. Abre **Docker Desktop** (icono en escritorio)
2. Espera a que Docker inicie (verás icono de ballena en taskbar)
3. Abre **PowerShell** o **Git Bash** y ejecuta:

```powershell
docker --version
# Debe mostrar: Docker version 4.25.x o superior

docker compose version
# Debe mostrar: Docker Compose version v2.23.x o superior

docker ps
# Debe mostrar tabla vacía (sin contenedores aún)
```

**✅ Si ves las versiones, Docker está instalado correctamente**

### **Troubleshooting Docker**

#### ❌ Error: "WSL 2 installation is incomplete"

**Solución**:
```powershell
# Abre PowerShell como Administrador
wsl --install
wsl --set-default-version 2
wsl --update

# Reinicia la PC
```

#### ❌ Error: "Hardware assisted virtualization is not enabled"

**Solución**:
1. Reinicia PC → Entra a BIOS (F2/F10/DEL durante arranque)
2. Busca "Virtualization Technology" o "VT-x" o "AMD-V"
3. Cambia a **"Enabled"**
4. Guarda y reinicia

---

## 🔧 PASO 2: INSTALAR GIT FOR WINDOWS

### **2.1 Descargar Git**

1. Ve a: https://git-scm.com/download/win
2. Descarga automáticamente `Git-2.43.0-64-bit.exe`

### **2.2 Ejecutar Instalador**

1. **Doble click** en el instalador
2. Configuración recomendada:
   - Destination: `C:\Program Files\Git` (default)
   - Components: ✅ Marcar todo
   - Default editor: **"Use Vim"** o **"Use Notepad++"**
   - PATH: ✅ **"Git from the command line and also from 3rd-party software"**
   - SSH: **"Use bundled OpenSSH"**
   - HTTPS: **"Use the native Windows Secure Channel library"**
   - Line ending: **"Checkout Windows-style, commit Unix-style"**
   - Terminal: ✅ **"Use MinTTY"**
3. Click **"Install"** → Espera 2 minutos
4. Click **"Finish"**

### **2.3 Verificar Instalación**

1. Busca **"Git Bash"** en el menú inicio
2. Abre **Git Bash**
3. Ejecuta:

```bash
git --version
# Debe mostrar: git version 2.43.0 o superior

echo $SHELL
# Debe mostrar: /usr/bin/bash
```

**✅ Si ves la versión, Git está instalado correctamente**

---

## 📥 PASO 3: DESCARGAR RHINOMETRIC

### **3.1 Obtener el Paquete Trial**

**Opción A: Descarga directa**

1. Ve a: https://github.com/Rafael2712/mi-proyecto/releases
2. Descarga: `rhinometric-trial-v2.1.0-universal.tar.gz` (~150 MB)
3. Guarda en: `C:\Users\TuUsuario\Downloads\`

**Opción B: Git Clone (si tienes acceso al repo)**

```bash
# Abre Git Bash
cd ~
git clone https://github.com/Rafael2712/mi-proyecto.git
cd mi-proyecto/infrastructure/mi-proyecto
```

### **3.2 Descomprimir**

**Usando Git Bash** (recomendado):

```bash
# Navega a Downloads
cd ~/Downloads

# Descomprime
tar -xzf rhinometric-trial-v2.1.0-universal.tar.gz

# Verifica que se creó la carpeta
ls -la rhinometric-trial-v2.1.0-universal/
# Debe mostrar: docker-compose-v2.1.0.yml, .env.example, etc.
```

**Usando 7-Zip** (alternativa):

1. Descarga 7-Zip: https://www.7-zip.org/
2. Instala 7-Zip
3. Click derecho en `rhinometric-trial-v2.1.0-universal.tar.gz`
4. **7-Zip** → **"Extract Here"** (2 veces, primero .gz, luego .tar)

---

## ⚙️ PASO 4: CONFIGURAR RHINOMETRIC

### **4.1 Navegar a la carpeta**

```bash
# En Git Bash
cd ~/Downloads/rhinometric-trial-v2.1.0-universal
pwd
# Debe mostrar: /c/Users/TuUsuario/Downloads/rhinometric-trial-v2.1.0-universal
```

### **4.2 Copiar archivo de configuración**

```bash
cp .env.example .env
```

### **4.3 Editar configuración (IMPORTANTE)**

```bash
# Abre el archivo .env en tu editor favorito
notepad .env

# O usa nano en Git Bash
nano .env
```

**Cambia estas variables**:

```env
# === CREDENCIALES (CAMBIALAS!) ===
GRAFANA_USER=admin
GRAFANA_PASSWORD=TuPasswordSeguro123!    # ← CAMBIAR

POSTGRES_USER=rhinometric
POSTGRES_PASSWORD=TuPasswordSeguro456!   # ← CAMBIAR
POSTGRES_DB=rhinometric_trial

REDIS_PASSWORD=TuPasswordSeguro789!      # ← CAMBIAR

# === PATHS (Windows) ===
# Docker Desktop usa rutas Unix style
HOME=/c/Users/TuUsuario                  # ← CAMBIAR TuUsuario

# === CONFIGURACION ===
RHINOMETRIC_MODE=trial
RHINOMETRIC_VERSION=2.1.0
```

**⚠️ IMPORTANTE**: 
- Usa passwords **diferentes** para cada servicio
- Mínimo 12 caracteres con mayúsculas, números y símbolos
- Guarda estos passwords en un gestor de contraseñas (LastPass, 1Password, etc.)

**Guardar**:
- En **Notepad**: Archivo → Guardar
- En **nano**: `Ctrl + O` → Enter → `Ctrl + X`

### **4.4 Verificar configuración**

```bash
cat .env | grep -E "(GRAFANA|POSTGRES|REDIS)_PASSWORD"
# Debe mostrar tus nuevos passwords (no los defaults)
```

---

## 🚀 PASO 5: LEVANTAR RHINOMETRIC

### **5.1 Verificar Docker está corriendo**

```bash
docker ps
# No debe dar error "Cannot connect to Docker daemon"
```

**Si da error**: 
1. Abre **Docker Desktop**
2. Espera a que inicie (icono ballena en taskbar sin animación)
3. Vuelve a intentar `docker ps`

### **5.2 Pull de imágenes (PRIMER USO)**

```bash
# Descarga todas las imágenes Docker (esto toma 5-10 minutos)
docker compose -f docker-compose-v2.1.0.yml pull

# Verás progreso:
# [+] Pulling grafana
# [+] Pulling prometheus
# [+] Pulling loki
# etc...
```

**Tamaño total**: ~2.5 GB de imágenes Docker

### **5.3 Iniciar Rhinometric**

```bash
# Levanta todos los contenedores en background
docker compose -f docker-compose-v2.1.0.yml up -d

# Verás:
# [+] Running 17/17
#  ✔ Container rhinometric-postgres      Started
#  ✔ Container rhinometric-redis         Started
#  ✔ Container rhinometric-prometheus    Started
#  ✔ Container rhinometric-loki          Started
#  ✔ Container rhinometric-tempo         Started
#  ✔ Container rhinometric-grafana       Started
#  ✔ Container rhinometric-api-proxy     Started
#  ... (17 contenedores total)
```

**Tiempo de inicio**: 30-60 segundos para que todos estén healthy

### **5.4 Verificar que todo está corriendo**

```bash
# Ver estado de contenedores
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep rhinometric

# Debe mostrar 17 contenedores con status "Up" o "Up (healthy)"
```

**Verificar logs** (si algo falla):

```bash
# Ver logs de Grafana
docker logs rhinometric-grafana --tail 50

# Ver logs de Prometheus
docker logs rhinometric-prometheus --tail 50

# Ver logs de todos
docker compose -f docker-compose-v2.1.0.yml logs --tail 20
```

---

## 🌐 PASO 6: ACCEDER A RHINOMETRIC

### **6.1 Abrir Grafana**

1. Abre tu navegador (Chrome, Firefox, Edge)
2. Ve a: **http://localhost:3000**
3. Espera a que cargue (puede tomar 10-15 segundos la primera vez)

### **6.2 Login**

```
Usuario: admin
Password: [El que configuraste en .env]
```

### **6.3 Primera vez - Change Password**

Grafana te pedirá cambiar el password:
- Puedes **saltarlo** (Skip) o cambiarlo
- Recomendado: usa el mismo que configuraste en `.env`

### **6.4 Explorar Dashboards**

1. Click en **menú hamburguesa** (☰) arriba izquierda
2. Click en **"Dashboards"**
3. Click en carpeta **"Rhinometric"**
4. Verás los 15 dashboards:
   - 📊 **Executive Summary**: Overview ejecutivo
   - 🖥️ **System Monitoring**: CPU, RAM, Disco
   - 📈 **Overview**: Vista general de servicios
   - 📝 **Logs Explorer**: Búsqueda de logs
   - 🔍 **Traces**: Trazas distribuidas
   - 🌐 **External APIs Monitoring**: APIs externas
   - ... y 9 más

### **6.5 Verificar otros servicios**

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Grafana** | http://localhost:3000 | Dashboards principales |
| **API Connector UI** | http://localhost:8091 | Agregar/gestionar APIs |
| **Prometheus** | http://localhost:9090 | Queries de métricas |
| **Loki** | http://localhost:3100 | Queries de logs |
| **Tempo** | http://localhost:3200 | Queries de traces |

---

## ✅ PASO 7: PRIMEROS PASOS

### **7.1 Ver métricas en tiempo real**

1. En Grafana, abre dashboard **"System Monitoring"**
2. Verás métricas de tu máquina Windows:
   - CPU Usage
   - Memory Usage
   - Disk I/O
   - Network Traffic

**Todo actualizado cada 30 segundos automáticamente**

### **7.2 Agregar tu primera API externa**

1. Abre: **http://localhost:8091**
2. Click **"+ Agregar Nueva API"**
3. Llena el formulario:
   ```
   Nombre: jsonplaceholder_posts
   Endpoint: https://jsonplaceholder.typicode.com/posts
   Auth Type: none
   Intervalo: 60
   ```
4. Click **"Test Connection"** → Debe mostrar ✅
5. Click **"Guardar API"**

6. Espera 60 segundos y abre dashboard **"External APIs Monitoring"**
7. Verás tu nueva API siendo monitoreada!

### **7.3 Explorar logs**

1. Dashboard **"Logs Explorer"**
2. En el query builder, selecciona:
   - Container: `rhinometric-api-proxy`
3. Click **"Run Query"**
4. Verás logs en tiempo real del API Proxy

### **7.4 Probar Drilldown**

1. Dashboard **"Drilldown Demo"**
2. Lee la documentación incluida
3. Sigue los ejemplos para navegar:
   - Métrica → Logs
   - Logs → Traces
   - Traces → Métricas

---

## 🔄 COMANDOS ÚTILES

### **Ver estado de contenedores**

```bash
docker ps | grep rhinometric
# Muestra los 17 contenedores
```

### **Ver logs de un servicio**

```bash
docker logs rhinometric-grafana --tail 50 --follow
# --tail 50: últimas 50 líneas
# --follow: sigue mostrando nuevos logs (Ctrl+C para salir)
```

### **Reiniciar un servicio**

```bash
docker restart rhinometric-grafana
# Reinicia solo Grafana
```

### **Reiniciar todo**

```bash
docker compose -f docker-compose-v2.1.0.yml restart
```

### **Detener Rhinometric**

```bash
docker compose -f docker-compose-v2.1.0.yml stop
# Los datos se conservan
```

### **Iniciar después de detener**

```bash
docker compose -f docker-compose-v2.1.0.yml start
```

### **Detener y eliminar todo (CUIDADO)**

```bash
# Esto ELIMINA todos los datos (métricas, logs, configuración)
docker compose -f docker-compose-v2.1.0.yml down -v
```

### **Ver uso de recursos**

```bash
docker stats --no-stream | grep rhinometric
# Muestra CPU%, MEM%, NET I/O, BLOCK I/O
```

---

## 🐛 TROUBLESHOOTING

### **❌ Error: "port is already allocated"**

**Problema**: Otro programa está usando el puerto 3000, 9090, etc.

**Solución**:

```powershell
# Ver qué programa usa el puerto 3000
netstat -ano | findstr :3000

# Anota el PID (último número)
# Abre Task Manager → Details → busca ese PID → End Task
```

**Alternativa**: Cambia el puerto en `docker-compose-v2.1.0.yml`:

```yaml
services:
  grafana:
    ports:
      - "3001:3000"  # Cambiar 3000 a 3001
```

### **❌ Error: "Cannot connect to Docker daemon"**

**Problema**: Docker Desktop no está corriendo

**Solución**:
1. Abre **Docker Desktop**
2. Espera a que inicie (icono ballena en taskbar)
3. Verifica: `docker ps`

### **❌ Error: "no configuration file provided"**

**Problema**: No estás en la carpeta correcta

**Solución**:

```bash
cd ~/Downloads/rhinometric-trial-v2.1.0-universal
ls -la docker-compose-v2.1.0.yml
# Debe existir
```

### **❌ Grafana muestra "Internal Server Error"**

**Problema**: Grafana aún está iniciando

**Solución**:
1. Espera 30 segundos más
2. Refresca el navegador (F5)
3. Verifica logs:
   ```bash
   docker logs rhinometric-grafana --tail 50
   ```

### **❌ Dashboards muestran "NO DATA"**

**Problema**: Prometheus no ha recolectado suficientes datos aún

**Solución**:
1. Espera 2-3 minutos
2. Verifica Prometheus: http://localhost:9090
3. Query de prueba: `up` → Debe mostrar 10+ targets

### **❌ Contenedor se reinicia continuamente**

**Problema**: Falta memoria RAM o error de configuración

**Solución**:

```bash
# Ver logs del contenedor problemático
docker logs rhinometric-[nombre-servicio] --tail 100

# Ver eventos Docker
docker events --since 5m

# Aumentar memoria de Docker Desktop:
# Docker Desktop → Settings → Resources → Memory → 6 GB
```

---

## 📊 VERIFICACIÓN POST-INSTALACIÓN

### **Checklist Completo**

Ejecuta este script de verificación:

```bash
#!/bin/bash
echo "=== VERIFICACION RHINOMETRIC v2.1.0 ==="
echo ""
echo "[1] Docker Version:"
docker --version
echo ""
echo "[2] Containers Running:"
docker ps | grep rhinometric | wc -l
echo "    (Esperado: 17)"
echo ""
echo "[3] Grafana Status:"
curl -s http://localhost:3000/api/health | grep "ok"
echo ""
echo "[4] Prometheus Targets:"
curl -s http://localhost:9090/api/v1/targets | grep -o "\"health\":\"up\"" | wc -l
echo "    (Esperado: 10+)"
echo ""
echo "[5] Loki Status:"
curl -s http://localhost:3100/ready
echo ""
echo "[6] API Proxy Status:"
curl -s http://localhost:8090/api/health/all | python -m json.tool
echo ""
echo "=== FIN VERIFICACION ==="
```

**Guarda como** `verify.sh` y ejecuta:

```bash
chmod +x verify.sh
./verify.sh
```

---

## 📚 PRÓXIMOS PASOS

1. **Lee la documentación de usuario**: `docs/MANUAL_USUARIO_v2.1.0.md`
2. **Explora los 15 dashboards** en Grafana
3. **Agrega más APIs externas** para monitorear
4. **Configura alertas** (Slack, email, webhook)
5. **Prueba el auto-update**: `./auto-update.sh --check-only`

---

## 🆘 SOPORTE

### **Documentación**
- 📖 Resumen Ejecutivo: `docs/RESUMEN_EJECUTIVO_v2.1.0.md`
- 📖 Manual de Usuario: `docs/MANUAL_USUARIO_v2.1.0.md`
- 📖 API Connector Guide: `API_CONNECTOR_GUIDE.md`

### **Comunidad**
- 💬 GitHub Issues: https://github.com/Rafael2712/mi-proyecto/issues
- 📧 Email (solo versión comercial): info@rhinometric.com

### **Logs para reportar problemas**

Si necesitas ayuda, incluye esta información:

```bash
# 1. Versión
cat VERSION

# 2. Sistema operativo
uname -a

# 3. Docker version
docker --version

# 4. Estado de contenedores
docker ps -a | grep rhinometric

# 5. Logs de servicios problemáticos
docker compose -f docker-compose-v2.1.0.yml logs --tail 100 > rhinometric-logs.txt
```

---

**✅ INSTALACIÓN COMPLETADA**

Si llegaste hasta aquí, **¡Rhinometric está corriendo en tu Windows!** 🎉

**Accede a**: http://localhost:3000 (admin / tu_password)

**Tiempo total**: ~20 minutos  
**Containers running**: 17/17  
**Status**: Ready for production monitoring

---

**Versión del Manual**: 1.0.0  
**Fecha**: Octubre 2025  
**OS**: Windows 10/11 (64-bit)  
**Rhinometric**: v2.1.0 Trial
