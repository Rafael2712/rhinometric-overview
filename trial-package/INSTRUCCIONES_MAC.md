# 🚀 RHINOMETRIC TRIAL - INSTRUCCIONES PARA MAC (VERSIÓN ARREGLADA)

## ✅ PROBLEMA SOLUCIONADO

Tu instalación de Rhinometric estaba fallando porque:

1. **❌ `version: '3.8'` obsoleto** → Docker Compose v2+ lo rechaza
2. **❌ Volúmenes incompatibles con macOS** → `node-exporter` y `cadvisor` configurados para Linux
3. **❌ Sin validación de sintaxis** → El script no detectaba estos errores

**TODO ESTÁ ARREGLADO EN ESTA NUEVA VERSIÓN** ✅

---

## 📥 PASO 1: DESCARGAR EL PAQUETE ARREGLADO

**Archivo**: `rhinometric-trial-v1.0.1-FIXED-MAC.zip` (45 KB)

**Ubicación actual**: `C:\Users\canel\mi-proyecto\infrastructure\mi-proyecto\`

### Opciones de transferencia al Mac:

**Opción A: Email**
1. Envía el ZIP por email a tu cuenta
2. Descárgalo en tu Mac

**Opción B: USB**
1. Copia el ZIP a una memoria USB
2. Conecta la USB a tu Mac
3. Copia el archivo a `~/Downloads`

**Opción C: Cloud (Dropbox, Google Drive, etc.)**
1. Sube el ZIP a tu servicio favorito
2. Descárgalo desde tu Mac

**Opción D: Red local (si ambas máquinas están en la misma red)**
```bash
# En Mac, ejecutar:
scp usuario@IP_WINDOWS:/ruta/al/rhinometric-trial-v1.0.1-FIXED-MAC.zip ~/Downloads/
```

---

## 🧹 PASO 2: LIMPIAR INSTALACIÓN ANTERIOR (Si existe)

Abre **Terminal** en tu Mac (`Cmd + Espacio` → escribe "Terminal" → Enter)

```bash
# Ir al directorio anterior
cd ~/Downloads/trial-package

# Detener servicios colgados
docker compose down --remove-orphans

# Limpiar contenedores
docker container prune -f

# Volver a Downloads
cd ~/Downloads

# Eliminar directorio viejo
rm -rf trial-package
```

---

## 📦 PASO 3: DESCOMPRIMIR EL NUEVO PAQUETE

```bash
# Ir a Downloads
cd ~/Downloads

# Descomprimir
unzip rhinometric-trial-v1.0.1-FIXED-MAC.zip

# Entrar al directorio
cd trial-package

# Verificar que los archivos estén ahí
ls -la
```

Deberías ver:
```
-rwxr-xr-x  start-trial.sh     ← Script principal (EJECUTABLE ✅)
-rwxr-xr-x  debug.sh           ← Script de diagnóstico (EJECUTABLE ✅)
-rw-r--r--  docker-compose.yml ← Configuración ARREGLADA ✅
-rw-r--r--  README.md
-rw-r--r--  .env.example
drwxr-xr-x  config/
drwxr-xr-x  licensing/
drwxr-xr-x  dashboard/
drwxr-xr-x  grafana/
...
```

---

## 🎯 PASO 4: EJECUTAR EL INSTALADOR

### Antes de empezar:

1. ✅ **Docker Desktop debe estar corriendo**
   - Abre Docker Desktop desde Aplicaciones
   - Espera a que el ícono en la barra superior diga "Docker Desktop is running"

2. ✅ **Cierra aplicaciones que puedan estar usando puertos 3000, 8080, 9090**
   - Si tienes Grafana local, ciérralo
   - Si tienes otro servidor en puerto 3000, detenlo

### Ejecutar instalador:

```bash
cd ~/Downloads/trial-package

# Ejecutar
./start-trial.sh
```

### El instalador te preguntará:

1. **Nombre del cliente**: Escribe `rhinometric` (o tu nombre de empresa)
2. **¿Reescribir .env?**: Presiona `S` + Enter (o solo Enter)
3. **¿Iniciar Rhinometric ahora?**: Presiona `S` + Enter (o solo Enter)

### Lo que deberías ver:

```
════════════════════════════════════════════════════════════════
  🦏 RHINOMETRIC TRIAL - INSTALADOR
  Plataforma de Observabilidad Completa
  Versión Trial: 180 días
════════════════════════════════════════════════════════════════

[PASO 1/7] Verificando Docker Desktop
✅ Docker Desktop está instalado y corriendo
ℹ️  Versión: Docker 24.0.x

[PASO 2/7] Verificando Docker Compose
✅ Docker Compose está disponible
ℹ️  Versión: Docker Compose v2.x.x

[PASO 3/7] Verificando recursos del sistema
✅ RAM disponible: 16 GB (mínimo: 8 GB)
✅ Espacio en disco: 150 GB (mínimo: 20 GB)

[PASO 4/7] Configurando variables de entorno
ℹ️  Generando .env...
✅ Archivo .env creado correctamente

[PASO 5/7] Creando estructura de directorios
✅ Directorios creados

[PASO 6/7] Generando licencia trial
✅ Licencia generada: licenses/trial_rhinometric.lic
ℹ️  Cliente: rhinometric
ℹ️  Expira: 2026-04-15

[PASO 7/7] Iniciando servicios Rhinometric
ℹ️  Validando docker-compose.yml...
✅ Sintaxis de docker-compose.yml válida
ℹ️  Descargando imágenes Docker (esto puede tardar varios minutos)...
⚠️  Primera ejecución: ~5-10 minutos dependiendo de tu conexión

ℹ️  Limpiando contenedores anteriores...
ℹ️  Iniciando servicios...

[+] Building 1.2s (15/15) FINISHED
[+] Running 11/11
 ✔ Container rhinometric-postgres           Started
 ✔ Container rhinometric-redis              Started
 ✔ Container rhinometric-license-server     Started
 ✔ Container rhinometric-prometheus         Started
 ✔ Container rhinometric-loki               Started
 ✔ Container rhinometric-tempo              Started
 ✔ Container rhinometric-grafana            Started
 ✔ Container rhinometric-alertmanager       Started
 ✔ Container rhinometric-node-exporter      Started
 ✔ Container rhinometric-cadvisor           Started
 ✔ Container rhinometric-license-dashboard  Started
 ✔ Container rhinometric-nginx              Started

✅ Contenedores iniciados correctamente

ℹ️  Esperando que los servicios estén listos (30 segundos)...
..............................

ℹ️  Estado de servicios:
NAME                                STATUS    PORTS
rhinometric-grafana                 Up        0.0.0.0:3000->3000/tcp
rhinometric-prometheus              Up        0.0.0.0:9090->9090/tcp
rhinometric-loki                    Up        0.0.0.0:3100->3100/tcp
rhinometric-tempo                   Up        0.0.0.0:3200->3200/tcp
rhinometric-license-dashboard       Up        0.0.0.0:8080->8080/tcp
...

✅ 11 servicios están corriendo

════════════════════════════════════════════════════════════════
  ✅ RHINOMETRIC TRIAL INSTALADO CORRECTAMENTE
════════════════════════════════════════════════════════════════

📊 ACCESO A LOS SERVICIOS:

  🎨 Grafana Dashboard (Principal)
     URL:      http://localhost:3000
     Usuario:  admin
     Password: [TU_PASSWORD_AQUÍ]

  📈 Prometheus (Métricas)
     URL:      http://localhost:9090

  🔑 License Dashboard
     URL:      http://localhost:8080

════════════════════════════════════════════════════════════════
```

---

## 🎉 PASO 5: VERIFICAR QUE TODO FUNCIONA

### 1. Abre tu navegador y ve a:

```
http://localhost:3000
```

Deberías ver el login de Grafana.

**Credenciales**:
- Usuario: `admin`
- Password: (busca en la salida del script o en `credentials.txt`)

### 2. Verifica el dashboard de licencias:

```
http://localhost:8080
```

Deberías ver tu licencia trial con 180 días de validez.

### 3. Verifica Prometheus:

```
http://localhost:9090
```

Deberías ver la UI de Prometheus con métricas.

---

## 🔍 SI ALGO SALE MAL

### Opción 1: Script de diagnóstico automático

```bash
cd ~/Downloads/trial-package
./debug.sh
```

Este script:
- ✅ Verifica Docker y Docker Compose
- ✅ Valida archivos esenciales
- ✅ Valida sintaxis de `docker-compose.yml`
- ✅ Muestra estado de servicios
- ✅ Detecta contenedores colgados
- ✅ Detecta puertos ocupados
- ✅ Sugiere soluciones

### Opción 2: Ver logs manualmente

```bash
cd ~/Downloads/trial-package

# Ver logs de TODOS los servicios
docker compose logs

# Ver logs en tiempo real
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs grafana
docker compose logs license-server
docker compose logs postgres
```

### Opción 3: Verificar sintaxis

```bash
cd ~/Downloads/trial-package
docker compose config
```

Si hay errores, se mostrarán aquí.

### Opción 4: Ver estado de contenedores

```bash
docker compose ps -a
```

Muestra TODOS los contenedores (corriendo, detenidos, fallidos).

---

## 🚨 ERRORES COMUNES Y SOLUCIONES

### Error: "Docker no está corriendo"

**Solución**:
1. Abre Docker Desktop
2. Espera a que inicie completamente
3. Verifica que el ícono muestre "Docker Desktop is running"
4. Ejecuta de nuevo `./start-trial.sh`

---

### Error: "Permission denied: ./start-trial.sh"

**Solución**:
```bash
chmod +x start-trial.sh debug.sh
./start-trial.sh
```

---

### Error: "Port 3000 already in use"

**Causa**: Otro servicio (Grafana local, otro servidor) está usando el puerto 3000.

**Solución A - Detener el otro servicio**:
```bash
# Ver qué está usando el puerto
lsof -i :3000

# Matar el proceso (reemplaza PID)
kill -9 PID
```

**Solución B - Cambiar puerto en Rhinometric**:

Edita `docker-compose.yml`:
```yaml
grafana:
  ports:
    - "3001:3000"  # Cambiar 3000 por 3001
```

Luego accede a: `http://localhost:3001`

---

### Error: "Out of memory" o servicios se reinician

**Causa**: Docker Desktop no tiene suficiente RAM asignada.

**Solución**:
1. Abre Docker Desktop
2. Ve a Settings (⚙️)
3. Resources
4. Aumenta Memory a **8 GB mínimo** (recomendado: 12 GB)
5. Aumenta CPU a **4 cores mínimo**
6. Apply & Restart
7. Ejecuta de nuevo `./start-trial.sh`

---

### Error: "No space left on device"

**Solución**:
```bash
# Limpiar imágenes viejas
docker system prune -a

# Eliminar volúmenes no usados
docker volume prune
```

---

## 📊 COMANDOS ÚTILES

### Ver estado de servicios
```bash
cd ~/Downloads/trial-package
docker compose ps
```

### Ver logs en tiempo real
```bash
docker compose logs -f
```

### Reiniciar servicios
```bash
docker compose restart
```

### Detener servicios (sin borrar datos)
```bash
docker compose stop
```

### Iniciar servicios (después de detener)
```bash
docker compose start
```

### Detener y eliminar TODO (incluye datos)
```bash
docker compose down -v
```

### Ver uso de recursos
```bash
docker stats
```

### Ver credenciales de Grafana
```bash
cat credentials.txt
# O
cat .env | grep GRAFANA_PASSWORD
```

---

## 📞 SOPORTE

Si después de seguir todos estos pasos sigue sin funcionar, proporciona:

```bash
cd ~/Downloads/trial-package

# 1. Ejecutar diagnóstico
./debug.sh > debug-output.txt

# 2. Capturar logs
docker compose logs > compose-logs.txt

# 3. Capturar configuración parseada
docker compose config > compose-parsed.yml

# 4. Info del sistema
sw_vers > system-info.txt
docker --version >> system-info.txt
docker compose version >> system-info.txt
```

Envía estos archivos a soporte:
- `debug-output.txt`
- `compose-logs.txt`
- `compose-parsed.yml`
- `system-info.txt`

**Email**: soporte@rhinometric.com

---

## ✅ RESUMEN

1. ✅ Descarga `rhinometric-trial-v1.0.1-FIXED-MAC.zip` (45 KB)
2. ✅ Descomprímelo en `~/Downloads`
3. ✅ Asegúrate de que Docker Desktop esté corriendo
4. ✅ Ejecuta `./start-trial.sh`
5. ✅ Espera 5-10 minutos (primera vez)
6. ✅ Accede a `http://localhost:3000`
7. ✅ Usuario: `admin`, Password: (ver `credentials.txt`)

**¡Ya está!** 🎉

---

**Versión**: 1.0.1 (Mac Fix)  
**Fecha**: 17 de Octubre, 2025  
**Tamaño**: 45 KB  
**Trial**: 180 días  
**Servicios**: 11 contenedores  
**Requisitos**: Docker Desktop, 8GB RAM, 20GB disco
