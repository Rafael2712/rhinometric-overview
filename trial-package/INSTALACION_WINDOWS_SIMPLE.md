# 🪟 GUÍA DE INSTALACIÓN RHINOMETRIC TRIAL - WINDOWS

## Para usuarios NO técnicos - Paso a Paso Simple

---

## ⚡ REQUISITOS PREVIOS

Antes de comenzar, necesitas tener instalado:

### 1️⃣ Docker Desktop para Windows

**¿Ya tienes Docker Desktop?**
- Abre el menú inicio y busca "Docker Desktop"
- Si lo encuentras, ábrelo y asegúrate que esté corriendo (ícono de ballena en la barra de tareas)
- Si NO lo tienes instalado, sigue estos pasos:

**Instalar Docker Desktop:**

1. Ve a: https://www.docker.com/products/docker-desktop/
2. Haz clic en "Download for Windows"
3. Ejecuta el instalador descargado
4. Sigue el asistente (dale clic a "Next" y "OK" en todo)
5. **IMPORTANTE:** Cuando termine, reinicia tu computadora
6. Después del reinicio, abre Docker Desktop desde el menú inicio
7. Espera a que arranque (verás una ballena en la barra de tareas cuando esté listo)

---

## 📦 PASO 1: EXTRAER EL ARCHIVO

1. **Ubica el archivo que te enviaron:**
   - Busca en tu carpeta de Descargas el archivo: `rhinometric-trial-v1.0.0-production.zip`

2. **Extrae el archivo:**
   - Haz clic derecho sobre el archivo ZIP
   - Selecciona "Extraer todo..."
   - Elige una ubicación (por ejemplo: `C:\rhinometric-trial`)
   - Haz clic en "Extraer"

3. **Verifica:**
   - Deberías tener una carpeta llamada `rhinometric-trial-v1.0.0-production`
   - Dentro de esa carpeta verás archivos como `docker-compose.yml`, `start.sh`, etc.

---

## 💻 PASO 2: ABRIR POWERSHELL

1. Presiona las teclas `Windows + R` al mismo tiempo
2. Escribe: `powershell`
3. Presiona Enter
4. Se abrirá una ventana azul (PowerShell)

---

## 📁 PASO 3: NAVEGAR A LA CARPETA

En la ventana de PowerShell, escribe (o copia y pega) estos comandos uno por uno:

```powershell
# Ir a la carpeta donde extrajiste los archivos
cd C:\rhinometric-trial\rhinometric-trial-v1.0.0-production
```

**NOTA:** Si extrajiste en otra ubicación, ajusta la ruta. Por ejemplo:
- Si está en el Escritorio: `cd $HOME\Desktop\rhinometric-trial-v1.0.0-production`
- Si está en Documentos: `cd $HOME\Documents\rhinometric-trial-v1.0.0-production`

---

## 🚀 PASO 4: INICIAR RHINOMETRIC

Copia y pega este comando en PowerShell:

```powershell
docker compose up -d
```

**¿Qué va a pasar?**
- Verás que empieza a descargar cosas (esto es normal)
- Puede tardar 5-10 minutos la primera vez
- Verás mensajes como "Pulling...", "Creating...", "Started"
- Al final dirá algo como "✔ Container rhinometric-grafana Started"

**Espera hasta que termine** (cuando vuelva a aparecer el cursor parpadeando)

---

## ⏱️ PASO 5: ESPERAR A QUE INICIE

Ahora espera 2 minutos para que todos los servicios arranquen.

Mientras esperas, puedes verificar el progreso con:

```powershell
docker ps
```

Deberías ver una lista de contenedores con estado "Up" (arriba).

---

## 🌐 PASO 6: ABRIR GRAFANA

1. **Abre tu navegador web** (Chrome, Edge, Firefox, etc.)

2. **Ve a esta dirección:**
   ```
   http://localhost:3000
   ```

3. **Inicia sesión:**
   - **Usuario:** `admin`
   - **Contraseña:** `admin_trial_2024`

4. **¡Listo!** Deberías ver el panel de Rhinometric

---

## ✅ PASO 7: VERIFICAR QUE TODO FUNCIONA

Una vez dentro de Grafana:

1. En el menú lateral izquierdo, busca "Dashboards" (ícono de 4 cuadrados)
2. Deberías ver 6 dashboards:
   - ✅ System Overview
   - ✅ Distributed Tracing
   - ✅ Logs Explorer
   - ✅ Database Monitoring
   - ✅ Redis Monitoring
   - ✅ License Status

3. Haz clic en **"License Status"** para ver la información de tu trial:
   - Días restantes: 30
   - Fecha de expiración
   - Estado: Activo

---

## 🛑 PARA DETENER RHINOMETRIC

Cuando quieras detener la plataforma:

```powershell
# Navega a la carpeta (si no estás ahí)
cd C:\rhinometric-trial\rhinometric-trial-v1.0.0-production

# Detener todos los servicios
docker compose down
```

---

## 🔄 PARA REINICIAR RHINOMETRIC

Si reiniciaste tu computadora o cerraste Docker:

```powershell
# 1. Abre Docker Desktop desde el menú inicio
# 2. Espera a que arranque (ícono de ballena en barra de tareas)

# 3. Abre PowerShell (Windows + R, escribe "powershell")

# 4. Navega a la carpeta
cd C:\rhinometric-trial\rhinometric-trial-v1.0.0-production

# 5. Inicia los servicios
docker compose up -d

# 6. Espera 2 minutos

# 7. Abre el navegador en http://localhost:3000
```

---

## 📊 COMANDOS ÚTILES

### Ver el estado de los servicios:
```powershell
docker ps
```

### Ver cuántos contenedores están corriendo:
```powershell
docker ps | Measure-Object -Line
```
Deberías ver **16 contenedores** (más el header = 17 líneas)

### Ver los logs de un servicio específico:
```powershell
# Ver logs de Grafana
docker logs rhinometric-grafana

# Ver logs del License Server
docker logs rhinometric-license-server
```

### Verificar el estado de la licencia:
```powershell
# Desde PowerShell
Invoke-WebRequest -Uri http://localhost:5000/status | ConvertFrom-Json
```

---

## ❓ PROBLEMAS COMUNES

### "docker: command not found"
**Solución:** Docker Desktop no está instalado o no está corriendo.
- Abre Docker Desktop desde el menú inicio
- Espera a que arranque completamente
- Intenta de nuevo

### "Cannot connect to Docker daemon"
**Solución:** Docker Desktop no está corriendo.
- Busca el ícono de Docker (ballena) en la barra de tareas
- Si no está, abre Docker Desktop
- Espera a que arranque

### "Port 3000 is already in use"
**Solución:** Otro programa está usando el puerto 3000.
- Cierra cualquier programa que pueda estar usando ese puerto
- O reinicia tu computadora
- Intenta de nuevo

### No puedo acceder a http://localhost:3000
**Solución:**
1. Verifica que los contenedores estén corriendo: `docker ps`
2. Espera 2-3 minutos más
3. Verifica que Docker Desktop esté corriendo
4. Intenta con: `http://127.0.0.1:3000`

### "No such file or directory"
**Solución:** Estás en la carpeta incorrecta.
- Verifica la ruta donde extrajiste los archivos
- Usa `cd` para navegar a la carpeta correcta

---

## 📞 OBTENER AYUDA

Si algo no funciona:

1. **Toma capturas de pantalla** de los errores que veas
2. **Copia el mensaje de error completo**
3. **Anota qué paso estabas haciendo**
4. Envía esa información a: rafael.canelon@rhinometric.com

---

## 📋 CHECKLIST DE VERIFICACIÓN

Antes de decir que está instalado, verifica:

- [ ] Docker Desktop está corriendo (ícono de ballena visible)
- [ ] `docker ps` muestra 16 contenedores
- [ ] http://localhost:3000 abre Grafana
- [ ] Puedes iniciar sesión (admin/admin_trial_2024)
- [ ] Ves los 6 dashboards en el menú
- [ ] El dashboard "License Status" muestra 30 días restantes

---

## 🎉 ¡FELICIDADES!

Si completaste todos los pasos, **Rhinometric Trial está instalado y funcionando** en tu computadora Windows.

Ahora tienes 30 días para probar todas las funcionalidades de la plataforma de observabilidad.

---

## 📖 DOCUMENTACIÓN ADICIONAL

Para aprender más sobre cómo usar Rhinometric:
- **Manual completo:** Abre el archivo `MANUAL_INSTALACION.html` en tu navegador
- **Guía de integración:** Revisa `INTEGRATION_GUIDE.md`
- **Documentación online:** https://docs.rhinometric.com

---

## ⚠️ IMPORTANTE

- Esta es una **versión TRIAL de 30 días**
- La licencia está vinculada a tu computadora
- No copies los archivos a otra computadora (no funcionará)
- Para licencia completa: sales@rhinometric.com

---

**Versión:** 1.0.0  
**Fecha:** Octubre 2025  
**Soporte:** rafael.canelon@rhinometric.com
