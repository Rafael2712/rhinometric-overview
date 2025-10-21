# 🚀 RHINOMETRIC - GUÍA RÁPIDA PARA MAC (1 PÁGINA)

## ✅ TU PROBLEMA ESTÁ SOLUCIONADO

**Qué falló**: Docker Compose v2 en Mac rechazaba el `version: '3.8'` en docker-compose.yml

**Qué arreglamos**: 
- ✅ Eliminado atributo obsoleto
- ✅ Volúmenes compatibles con macOS
- ✅ Validación automática antes de arrancar

---

## 📥 INSTALACIÓN EN 4 PASOS

### 1️⃣ DESCARGAR Y DESCOMPRIMIR

```bash
# Ve a Downloads
cd ~/Downloads

# Descomprime (doble clic o:)
unzip rhinometric-trial-v1.0.1-FIXED-MAC.zip

# Entra al directorio
cd trial-package
```

### 2️⃣ ASEGÚRATE DE QUE DOCKER ESTÉ CORRIENDO

- Abre **Docker Desktop** desde Aplicaciones
- Espera a que el ícono en la barra superior diga **"Docker Desktop is running"**

### 3️⃣ EJECUTA EL INSTALADOR

```bash
./start-trial.sh
```

**Preguntas que te hará**:
- Nombre del cliente: `rhinometric` (o tu nombre)
- ¿Reescribir .env?: `S` + Enter
- ¿Iniciar ahora?: `S` + Enter

**Tiempo**: 5-10 minutos (primera vez)

### 4️⃣ ACCEDE A GRAFANA

```
http://localhost:3000
```

**Usuario**: `admin`  
**Password**: (busca en la pantalla o en `credentials.txt`)

---

## 🔍 SI ALGO FALLA

### Ejecuta el diagnóstico automático:

```bash
./debug.sh
```

Te dirá EXACTAMENTE qué está mal y cómo arreglarlo.

---

## 🚨 ERRORES COMUNES

| Error | Solución |
|-------|----------|
| "Docker no está corriendo" | Abre Docker Desktop y espera que inicie |
| "Permission denied" | `chmod +x start-trial.sh debug.sh` |
| "Port 3000 already in use" | `lsof -i :3000` → `kill -9 PID` |
| "Out of memory" | Docker Desktop → Settings → Resources → 8GB+ RAM |

---

## 📊 LO QUE OBTENDRÁS

**11 Servicios de Observabilidad**:
- 🎨 **Grafana** → `http://localhost:3000` (Dashboard principal)
- 📈 **Prometheus** → `http://localhost:9090` (Métricas)
- 📝 **Loki** → `http://localhost:3100` (Logs)
- 🔍 **Tempo** → `http://localhost:3200` (Trazas)
- 🚨 **Alertmanager** → `http://localhost:9093` (Alertas)
- 🔑 **License Dashboard** → `http://localhost:8080` (Licencias)

**Trial**: 180 días  
**Retención**: 7 días  
**Usuarios**: 5 máximo

---

## 📞 SOPORTE

**Email**: soporte@rhinometric.com

**Si necesitas ayuda**, envía:
```bash
./debug.sh > debug.txt
docker compose logs > logs.txt
```

Adjunta `debug.txt` y `logs.txt` al email.

---

## ✅ COMANDOS ÚTILES

```bash
# Ver estado
docker compose ps

# Ver logs
docker compose logs -f

# Reiniciar
docker compose restart

# Detener
docker compose stop

# Iniciar
docker compose start

# Eliminar TODO
docker compose down -v
```

---

## 🎯 CHECKLIST

- [ ] Docker Desktop instalado y corriendo ✅
- [ ] Paquete descomprimido en `~/Downloads/trial-package` ✅
- [ ] Ejecutado `./start-trial.sh` ✅
- [ ] 11 servicios corriendo (verificar con `docker compose ps`) ✅
- [ ] Grafana accesible en `http://localhost:3000` ✅
- [ ] Credenciales guardadas en `credentials.txt` ✅

**¡LISTO!** 🎉

---

**Archivo**: rhinometric-trial-v1.0.1-FIXED-MAC.zip (48.57 KB)  
**Versión**: 1.0.1  
**Fecha**: 17 de Octubre, 2025
