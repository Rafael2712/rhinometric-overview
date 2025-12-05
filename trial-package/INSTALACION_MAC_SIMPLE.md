# 🍎 GUÍA DE INSTALACIÓN RHINOMETRIC TRIAL - macOS

## Instalación Paso a Paso para Mac

---

## ⚡ REQUISITOS PREVIOS

### 1️⃣ Docker Desktop para Mac

**¿Ya tienes Docker Desktop?**
- Abre Spotlight (⌘ + Espacio) y busca "Docker"
- Si lo encuentras, ábrelo y asegúrate que esté corriendo (ícono de ballena en la barra superior)
- Si NO lo tienes instalado, sigue estos pasos:

**Instalar Docker Desktop:**

1. Ve a: https://www.docker.com/products/docker-desktop/
2. Haz clic en "Download for Mac"
   - Si tienes Mac con chip Apple Silicon (M1/M2/M3): Descarga "Apple Chip"
   - Si tienes Mac Intel: Descarga "Intel Chip"
3. Abre el archivo `.dmg` descargado
4. Arrastra Docker a la carpeta Aplicaciones
5. Abre Docker desde Aplicaciones
6. **IMPORTANTE:** Docker te pedirá permisos, acéptalos
7. Espera a que arranque completamente (verás una ballena en la barra superior)

---

## 📦 PASO 1: EXTRAER EL ARCHIVO

1. **Ubica el archivo que te enviaron:**
   - Busca en tu carpeta de Descargas: `rhinometric-trial-v1.0.0-production.tar.gz`

2. **Extrae el archivo:**
   - Doble clic sobre el archivo (macOS lo extraerá automáticamente)
   - O desde Terminal:
   ```bash
   cd ~/Downloads
   tar -xzf rhinometric-trial-v1.0.0-production.tar.gz
   ```

3. **Mueve la carpeta a un lugar conveniente:**
   ```bash
   mv rhinometric-trial-v1.0.0-production ~/rhinometric-trial
   ```

---

## 💻 PASO 2: ABRIR TERMINAL

1. **Opción A:** Abre Spotlight (⌘ + Espacio) y escribe "Terminal"
2. **Opción B:** Ve a Aplicaciones → Utilidades → Terminal

---

## 📁 PASO 3: NAVEGAR A LA CARPETA

En la Terminal, escribe:

```bash
cd ~/rhinometric-trial
```

Verifica que estás en el lugar correcto:

```bash
ls
```

Deberías ver archivos como `docker-compose.yml`, `start.sh`, etc.

---

## 🚀 PASO 4: INICIAR RHINOMETRIC

Copia y pega este comando en Terminal:

```bash
docker compose up -d
```

**¿Qué va a pasar?**
- Verás que empieza a descargar imágenes Docker (esto es normal)
- Puede tardar 5-10 minutos la primera vez
- Verás mensajes como "Pulling...", "Creating...", "Started"
- Al final dirá algo como "✔ Container rhinometric-grafana Started"

**Espera hasta que termine** (cuando vuelva a aparecer el prompt `$`)

---

## ⏱️ PASO 5: ESPERAR A QUE INICIE

Espera 2 minutos para que todos los servicios arranquen.

Verifica el progreso con:

```bash
docker ps
```

Deberías ver una lista de contenedores con estado "Up".

---

## 🌐 PASO 6: ABRIR GRAFANA

1. **Abre tu navegador** (Safari, Chrome, Firefox, etc.)

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
2. Deberías ver 7 dashboards:
   - ✅ System Overview
   - ✅ Distributed Tracing
   - ✅ Logs Explorer
   - ✅ Database Monitoring
   - ✅ Redis Monitoring
   - ✅ License Status
   - ✅ License Management

3. Haz clic en **"License Status"** para ver la información de tu trial:
   - Días restantes: 30
   - Fecha de expiración
   - Estado: Activo

---

## 🛑 PARA DETENER RHINOMETRIC

Cuando quieras detener la plataforma:

```bash
# Navega a la carpeta (si no estás ahí)
cd ~/rhinometric-trial

# Detener todos los servicios
docker compose down
```

---

## 🔄 PARA REINICIAR RHINOMETRIC

Si reiniciaste tu Mac o cerraste Docker:

```bash
# 1. Abre Docker Desktop desde Aplicaciones
# 2. Espera a que arranque (ícono de ballena en barra superior)

# 3. Abre Terminal (⌘ + Espacio → "Terminal")

# 4. Navega a la carpeta
cd ~/rhinometric-trial

# 5. Inicia los servicios
docker compose up -d

# 6. Espera 2 minutos

# 7. Abre el navegador en http://localhost:3000
```

---

## 📊 COMANDOS ÚTILES

### Ver el estado de los servicios:
```bash
docker ps
```

### Ver cuántos contenedores están corriendo:
```bash
docker ps | wc -l
```
Deberías ver **17** (16 contenedores + 1 línea de header)

### Ver los logs de un servicio específico:
```bash
# Ver logs de Grafana
docker logs rhinometric-grafana

# Ver logs del License Server
docker logs rhinometric-license-server

# Seguir logs en tiempo real
docker logs -f rhinometric-grafana
```

### Verificar el estado de la licencia:
```bash
curl -s http://localhost:5000/status | jq .
```

*(Si no tienes `jq`, instálalo con: `brew install jq`)*

---

## 🔧 SCRIPTS AUXILIARES

La instalación incluye scripts para facilitar el uso:

### Iniciar servicios:
```bash
./start.sh
```

### Detener servicios:
```bash
./stop.sh
```

### Ver estado:
```bash
./status.sh
```

---

## ❓ PROBLEMAS COMUNES

### "docker: command not found"
**Solución:** Docker Desktop no está instalado o no está en el PATH.
- Asegúrate que Docker Desktop esté instalado
- Abre Docker Desktop desde Aplicaciones
- Reinicia la Terminal

### "Cannot connect to Docker daemon"
**Solución:** Docker Desktop no está corriendo.
- Busca el ícono de Docker (ballena) en la barra superior
- Si no está, abre Docker Desktop desde Aplicaciones
- Espera a que arranque completamente

### "Port 3000 is already in use"
**Solución:** Otro programa está usando el puerto 3000.
- Verifica qué programa: `lsof -i :3000`
- Cierra ese programa
- O cambia el puerto en `docker-compose.yml`

### No puedo acceder a http://localhost:3000
**Solución:**
1. Verifica que los contenedores estén corriendo: `docker ps`
2. Espera 2-3 minutos más
3. Verifica que Docker Desktop esté corriendo
4. Intenta con: `http://127.0.0.1:3000`
5. Revisa los logs: `docker logs rhinometric-grafana`

### "No such file or directory"
**Solución:** Estás en la carpeta incorrecta.
- Verifica dónde estás: `pwd`
- Navega a la carpeta correcta: `cd ~/rhinometric-trial`
- Lista archivos para confirmar: `ls`

### Permisos denegados
**Solución:**
```bash
# Dar permisos de ejecución a los scripts
chmod +x start.sh stop.sh status.sh
```

---

## 🍺 TIPS PARA MAC

### Instalar Homebrew (opcional pero recomendado):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Herramientas útiles con Homebrew:
```bash
brew install jq         # Para formatear JSON
brew install htop       # Monitor de recursos
brew install watch      # Para ejecutar comandos repetidamente
```

### Monitorear recursos de Docker:
```bash
# Ver uso de CPU y RAM de contenedores
docker stats

# Ver solo los de Rhinometric
docker stats $(docker ps --filter name=rhinometric --format "{{.Names}}")
```

---

## 🎯 OPTIMIZACIÓN PARA MAC

### Ajustar recursos de Docker Desktop:

1. Abre Docker Desktop
2. Ve a Settings (⚙️) → Resources
3. Ajusta:
   - **CPUs:** Mínimo 2, recomendado 4
   - **Memory:** Mínimo 4 GB, recomendado 8 GB
   - **Disk:** Mínimo 10 GB
4. Aplica los cambios y reinicia Docker

---

## 📋 CHECKLIST DE VERIFICACIÓN

Antes de decir que está instalado, verifica:

- [ ] Docker Desktop está corriendo (ícono de ballena visible en barra superior)
- [ ] `docker ps` muestra 16 contenedores
- [ ] http://localhost:3000 abre Grafana
- [ ] Puedes iniciar sesión (admin/admin_trial_2024)
- [ ] Ves los 7 dashboards en el menú
- [ ] El dashboard "License Status" muestra 30 días restantes
- [ ] El dashboard "License Management" muestra tu licencia activa

---

## 🎉 ¡FELICIDADES!

Si completaste todos los pasos, **Rhinometric Trial está instalado y funcionando** en tu Mac.

Ahora tienes 30 días para probar todas las funcionalidades de la plataforma de observabilidad.

---

## 🔐 INFORMACIÓN DE SEGURIDAD

### Hardware Fingerprinting
Tu licencia está vinculada a este Mac específico mediante:
- Dirección MAC
- Hostname
- ID del contenedor Docker
- Información del CPU

**Esto significa:**
- ✅ Puedes reiniciar tu Mac y seguirá funcionando
- ✅ Puedes detener y reiniciar los contenedores
- ❌ NO puedes copiar los archivos a otro Mac (no funcionará)
- ❌ NO puedes compartir tu licencia con otros

### Time-Bomb Protection
El sistema valida tu licencia cada 6 horas automáticamente:
- ✅ Si la licencia es válida → Continúa funcionando
- ❌ Si la licencia expiró → Se detiene automáticamente
- ⏰ Expira después de 30 días

---

## 📖 DOCUMENTACIÓN ADICIONAL

Para aprender más sobre cómo usar Rhinometric:
- **Manual completo:** Abre el archivo `MANUAL_INSTALACION.html` en tu navegador
- **Guía de integración:** Revisa `INTEGRATION_GUIDE.md`
- **Testing con API:** Revisa `TESTING_API_PUBLICA.md`
- **Documentación online:** https://docs.rhinometric.com

---

## ⚠️ IMPORTANTE

- Esta es una **versión TRIAL de 30 días**
- La licencia está vinculada a tu Mac
- No copies los archivos a otro Mac (no funcionará)
- Para licencia completa: sales@rhinometric.com
- Para soporte técnico: support@rhinometric.com

---

## 🆘 OBTENER AYUDA

Si algo no funciona:

1. **Revisa los logs:**
   ```bash
   docker logs rhinometric-grafana
   docker logs rhinometric-license-server
   ```

2. **Captura pantallas de los errores**

3. **Ejecuta diagnóstico:**
   ```bash
   docker ps
   docker compose ps
   curl http://localhost:5000/status
   ```

4. **Contacta soporte:**
   - Email: support@rhinometric.com
   - Incluye: sistema operativo, logs, capturas

---

**Versión:** 1.0.0  
**Fecha:** Octubre 2025  
**Compatible con:** macOS 11+ (Big Sur, Monterey, Ventura, Sonoma)  
**Arquitecturas:** Intel (x86_64) y Apple Silicon (ARM64/M1/M2/M3)
