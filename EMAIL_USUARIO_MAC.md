# 📧 EMAIL PARA ENVIAR AL USUARIO DE MAC

---

**Asunto**: ✅ Rhinometric Trial - PROBLEMA SOLUCIONADO (Versión para Mac)

---

Hola,

He identificado y **solucionado completamente** el problema que impedía que Rhinometric arrancara en tu Mac.

## 🔍 QUÉ ESTABA FALLANDO

El script `start-trial.sh` se quedaba colgado porque:

1. **Docker Compose v2** (incluido en Docker Desktop para Mac) ya **NO soporta** el atributo `version: '3.8'` que teníamos en el archivo `docker-compose.yml`
2. Los volúmenes de `node-exporter` y `cadvisor` estaban configurados para Linux y no funcionaban en macOS
3. No había validación automática que detectara estos problemas antes de intentar arrancar

## ✅ QUÉ HE ARREGLADO

**Versión nueva**: `1.0.1-FIXED-MAC`

Cambios aplicados:
- ✅ Eliminado el atributo `version` obsoleto
- ✅ Volúmenes ajustados para compatibilidad con macOS
- ✅ Validación automática de sintaxis antes de arrancar
- ✅ Limpieza automática de contenedores colgados
- ✅ Logging detallado de errores
- ✅ **NUEVO**: Script de diagnóstico automático (`debug.sh`)

## 📦 ARCHIVO ADJUNTO

**rhinometric-trial-v1.0.1-FIXED-MAC.zip** (50 KB)

Este archivo contiene TODO lo necesario para que Rhinometric funcione en tu Mac.

---

## 🚀 INSTALACIÓN EN 4 PASOS (5-10 MINUTOS)

### 1️⃣ Descomprimir

```bash
cd ~/Downloads
unzip rhinometric-trial-v1.0.1-FIXED-MAC.zip
cd trial-package
```

### 2️⃣ Asegúrate de que Docker Desktop esté corriendo

- Abre **Docker Desktop** desde Aplicaciones
- Espera a que el ícono en la barra superior diga "Docker Desktop is running"

### 3️⃣ Ejecutar instalador

```bash
./start-trial.sh
```

**El script te preguntará**:
- Nombre del cliente: escribe `rhinometric` (o tu nombre de empresa)
- ¿Reescribir .env?: presiona `S` + Enter
- ¿Iniciar ahora?: presiona `S` + Enter

**Espera 5-10 minutos** mientras descarga e inicia los 11 servicios.

### 4️⃣ Acceder a Grafana

Una vez que termine, abre tu navegador:

```
http://localhost:3000
```

**Usuario**: `admin`  
**Password**: (el script lo mostrará al finalizar, también está en `credentials.txt`)

---

## 🔍 SI ALGO FALLA (muy improbable ahora)

He incluido un **script de diagnóstico automático**:

```bash
cd ~/Downloads/trial-package
./debug.sh
```

Este script:
- ✅ Verifica que Docker esté instalado y corriendo
- ✅ Valida la sintaxis del `docker-compose.yml`
- ✅ Detecta puertos ocupados
- ✅ Detecta contenedores colgados y los limpia
- ✅ Te dice EXACTAMENTE qué está mal y cómo arreglarlo

---

## 📚 DOCUMENTACIÓN INCLUIDA

Dentro del paquete encontrarás:

- **GUIA_RAPIDA_MAC.md** → Resumen de 1 página (START HERE) ⭐
- **INSTRUCCIONES_MAC.md** → Guía completa paso a paso con troubleshooting
- **SOLUCION_MAC.md** → Detalles técnicos de los cambios aplicados
- **README.md** → Documentación general de Rhinometric

---

## 🚨 ERRORES COMUNES (Y SOLUCIONES)

| Error | Solución |
|-------|----------|
| "Docker no está corriendo" | Abre Docker Desktop y espera que inicie |
| "Permission denied" | `chmod +x start-trial.sh debug.sh` |
| "Port 3000 already in use" | `lsof -i :3000` → mata el proceso con `kill -9 PID` |
| "Out of memory" | Docker Desktop → Settings → Resources → aumenta RAM a 8GB+ |

---

## 📊 LO QUE OBTENDRÁS

**11 Servicios de Observabilidad**:

- 🎨 **Grafana** → `http://localhost:3000` **(Principal)** ⭐
- 📈 **Prometheus** → `http://localhost:9090` (Métricas)
- 📝 **Loki** → `http://localhost:3100` (Logs)
- 🔍 **Tempo** → `http://localhost:3200` (Trazas distribuidas)
- 🚨 **Alertmanager** → `http://localhost:9093` (Alertas)
- 🔑 **License Dashboard** → `http://localhost:8080` (Monitor de licencia)
- 🌐 **Nginx** → `http://localhost` (Reverse proxy)
- **PostgreSQL** (Base de datos)
- **Redis** (Cache)
- **Node Exporter** (Métricas del sistema)
- **cAdvisor** (Métricas de contenedores)

**Características**:
- ⏱️ **Trial**: 180 días de validez
- 💾 **Retención**: 7 días de datos históricos
- 👥 **Usuarios**: Hasta 5 usuarios simultáneos

---

## ✅ VERIFICACIÓN RÁPIDA

Una vez instalado, verifica que todo funciona:

```bash
cd ~/Downloads/trial-package

# Ver estado de servicios
docker compose ps

# Deberías ver 11 servicios con STATUS "Up"
```

Si ves `Up` en los 11 servicios, **¡todo está funcionando!** 🎉

---

## 📞 SOPORTE

Si después de seguir estos pasos **sigue sin funcionar** (lo cual es muy improbable con esta versión arreglada), contacta:

**Email**: soporte@rhinometric.com  
**Comercial**: ventas@rhinometric.com

**Adjunta estos archivos**:
```bash
cd ~/Downloads/trial-package
./debug.sh > debug.txt
docker compose logs > logs.txt
```

Envía `debug.txt` y `logs.txt` por email.

---

## 🎯 RESUMEN

1. ✅ Descarga el adjunto: `rhinometric-trial-v1.0.1-FIXED-MAC.zip`
2. ✅ Descomprímelo en `~/Downloads`
3. ✅ Asegúrate de que Docker Desktop esté corriendo
4. ✅ Ejecuta `./start-trial.sh`
5. ✅ Espera 5-10 minutos
6. ✅ Accede a `http://localhost:3000`
7. ✅ Usuario: `admin`, Password: ver `credentials.txt`

**Eso es todo.** Ahora debería funcionar perfectamente. 🚀

---

## 💰 CONVERSIÓN A VERSIÓN COMERCIAL

Cuando estés listo para convertir a la versión completa:

**Ventajas de la versión comercial**:
- ⏱️ **Sin límite de tiempo** (vs 180 días trial)
- 💾 **Retención de 30/60/90 días** (vs 7 días trial)
- 👥 **Usuarios ilimitados** (vs 5 trial)
- 🔐 **Alta disponibilidad (HA)**
- 🔄 **Backups automáticos**
- 📞 **Soporte 24/7**
- 📈 **SLA 99.9%**
- 🏷️ **White Label** (tu marca)

**Contacto comercial**: ventas@rhinometric.com

---

Cualquier duda o problema, avísame.

¡Disfruta de Rhinometric! 🎉

Saludos,  
**[Tu Nombre]**  
Rhinometric Team  
soporte@rhinometric.com  
https://rhinometric.com

---

**P.D.**: Si te funciona, me encantaría saber tu experiencia con la plataforma. ¿Qué te parece Rhinometric hasta ahora?

---

**Archivo adjunto**: rhinometric-trial-v1.0.1-FIXED-MAC.zip (50 KB)  
**Versión**: 1.0.1 (Mac Fix)  
**Fecha**: 17 de Octubre, 2025  
**Trial**: 180 días
