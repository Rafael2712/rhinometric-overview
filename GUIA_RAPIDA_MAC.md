# 🍎 RHINOMETRIC TRIAL - GUÍA RÁPIDA PARA macOS

## ⚡ INSTALACIÓN RÁPIDA (3 minutos)

### Pre-requisitos
- **macOS** 10.15+ (Catalina o superior)
- **Docker Desktop** instalado y corriendo
- **Terminal** (aplicación incluida en macOS)

---

## 📦 PASO 1: OBTENER ARCHIVOS

```bash
# Si tienes el proyecto clonado:
cd /ruta/a/mi-proyecto/infrastructure/mi-proyecto

# O si recibes un ZIP:
unzip rhinometric-trial-v1.0.zip
cd rhinometric-trial-v1.0
```

---

## 🚀 PASO 2: EJECUTAR INSTALADOR

```bash
# Dar permisos de ejecución
chmod +x start-trial.sh

# Ejecutar instalador
./start-trial.sh
```

**Eso es todo.** El script te guiará paso a paso.

---

## 📝 DURANTE LA INSTALACIÓN

El script te preguntará:

1. **Nombre del cliente**: Introduce el nombre (ej: "Ayuntamiento Madrid")
2. **¿Iniciar ahora?**: Presiona `S` para iniciar inmediatamente

```
Nombre del cliente/organización: Ayuntamiento Madrid
¿Iniciar Rhinometric ahora? [S/n]: S
```

---

## ✅ VERIFICAR QUE FUNCIONA

### 1. Espera 30 segundos después de iniciar

### 2. Abre tu navegador:
```
http://localhost:3000
```

### 3. Login en Grafana:
- **Usuario**: `admin`
- **Password**: *(se muestra en terminal al finalizar)*

### 4. Ver estado de contenedores:
```bash
docker compose -f docker-compose-trial.yml ps
```

Deberías ver **11 servicios** corriendo con estado `Up`.

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### Error: "Docker no está corriendo"
```bash
# Abrir Docker Desktop desde Aplicaciones
open -a Docker

# Esperar 30 segundos y volver a intentar
./start-trial.sh
```

### Error: "Puerto ya en uso"
```bash
# Ver qué proceso usa el puerto 3000
lsof -i :3000

# Detener servicios previos
docker compose -f docker-compose-trial.yml down

# O cambiar puertos editando docker-compose-trial.yml
```

### Error: "Archivos faltantes"
```bash
# Verificar que tienes todos los archivos
ls -la config/

# Deberías ver:
# - prometheus-saas.yml
# - loki-saas.yml
# - tempo-saas.yml
# - alertmanager-saas.yml
# - nginx-trial.conf
```

### Servicios no inician
```bash
# Ver logs detallados
docker compose -f docker-compose-trial.yml logs -f

# Reiniciar contenedores específicos
docker compose -f docker-compose-trial.yml restart grafana
docker compose -f docker-compose-trial.yml restart prometheus
```

### "Permission denied" en start-trial.sh
```bash
# Asegurar permisos correctos
chmod +x start-trial.sh

# Ejecutar con bash explícitamente
bash start-trial.sh
```

---

## 📊 ACCESO A SERVICIOS

Una vez iniciado, accede a:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Grafana** | http://localhost:3000 | Dashboard principal |
| **Prometheus** | http://localhost:9090 | Métricas |
| **Loki** | http://localhost:3100 | Logs |
| **Tempo** | http://localhost:3200 | Trazas |
| **Alertmanager** | http://localhost:9093 | Alertas |
| **License Dashboard** | http://localhost:8080 | Monitor licencias |

---

## 🛠️ COMANDOS ÚTILES

### Ver todos los servicios
```bash
docker compose -f docker-compose-trial.yml ps
```

### Ver logs en tiempo real
```bash
# Todos los servicios
docker compose -f docker-compose-trial.yml logs -f

# Solo Grafana
docker compose -f docker-compose-trial.yml logs -f grafana

# Solo errores
docker compose -f docker-compose-trial.yml logs | grep -i error
```

### Reiniciar servicios
```bash
# Reiniciar todo
docker compose -f docker-compose-trial.yml restart

# Reiniciar servicio específico
docker compose -f docker-compose-trial.yml restart grafana
```

### Detener (sin borrar datos)
```bash
docker compose -f docker-compose-trial.yml stop
```

### Iniciar (después de detener)
```bash
docker compose -f docker-compose-trial.yml start
```

### Detener y eliminar TODO (incluye datos)
```bash
docker compose -f docker-compose-trial.yml down -v
```

### Ver uso de recursos
```bash
docker stats
```

---

## 🔍 VERIFICACIÓN DE SALUD

### Script de verificación rápida:
```bash
#!/bin/bash

echo "🔍 Verificando servicios Rhinometric..."

services=(
    "http://localhost:3000"
    "http://localhost:9090"
    "http://localhost:3100/ready"
    "http://localhost:3200/ready"
    "http://localhost:9093"
    "http://localhost:8080"
)

for url in "${services[@]}"; do
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|302"; then
        echo "✅ $url"
    else
        echo "❌ $url"
    fi
done
```

Guarda como `check-health.sh`, da permisos (`chmod +x check-health.sh`) y ejecuta.

---

## 📱 MONITOREAR DESDE TERMINAL

### Dashboard en terminal (requiere docker stats)
```bash
watch -n 2 'docker compose -f docker-compose-trial.yml ps'
```

### Ver uso de CPU/RAM en tiempo real
```bash
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

---

## 🧹 LIMPIEZA COMPLETA

Si quieres eliminar TODO (incluye volúmenes y datos):

```bash
# 1. Detener y eliminar contenedores + volúmenes
docker compose -f docker-compose-trial.yml down -v

# 2. Eliminar imágenes (opcional)
docker images | grep rhinometric | awk '{print $3}' | xargs docker rmi -f

# 3. Eliminar directorios locales
rm -rf data/ licenses/ certs/

# 4. Eliminar archivo .env
rm .env
```

**ADVERTENCIA**: Esto borra TODOS los datos. Solo para empezar de cero.

---

## 🎓 PRIMEROS PASOS EN GRAFANA

1. **Accede** a http://localhost:3000
2. **Login**: admin / *(password de terminal)*
3. **Ir a**: Configuration → Data Sources
4. **Verificar** que existen:
   - ✅ Prometheus (http://prometheus:9090)
   - ✅ Loki (http://loki:3100)
   - ✅ Tempo (http://tempo:3200)

5. **Explorar datos**:
   - Menú lateral → Explore
   - Selecciona data source → Prometheus
   - Query: `up` (ver servicios activos)

---

## 📞 SOPORTE

### Problema no resuelto:
1. Ejecuta:
   ```bash
   docker compose -f docker-compose-trial.yml logs > logs-completos.txt
   docker compose -f docker-compose-trial.yml ps >> logs-completos.txt
   ```

2. Envía `logs-completos.txt` a: **soporte@rhinometric.com**

### Información del sistema:
```bash
# Versión Docker
docker --version
docker compose version

# Sistema operativo
sw_vers

# Recursos disponibles
sysctl hw.memsize
sysctl hw.ncpu
```

---

## ⚙️ CONFIGURACIÓN AVANZADA

### Cambiar puertos (si hay conflicto)

Edita `docker-compose-trial.yml`:

```yaml
# Cambiar puerto de Grafana
services:
  grafana:
    ports:
      - "3001:3000"  # Cambiar 3000 → 3001
```

Luego reinicia:
```bash
docker compose -f docker-compose-trial.yml up -d
```

Accede a: http://localhost:3001

### Modificar retención de datos

Edita `config/prometheus-saas.yml`:
```yaml
command:
  - '--storage.tsdb.retention.time=7d'  # Cambiar a 15d, 30d, etc.
```

### Añadir más memoria a PostgreSQL

Edita `docker-compose-trial.yml`:
```yaml
postgres:
  deploy:
    resources:
      limits:
        memory: 4G  # Cambiar de 2G a 4G
```

---

## 🏁 CHECKLIST DE INSTALACIÓN EXITOSA

- [ ] Docker Desktop corriendo
- [ ] Script `start-trial.sh` ejecutado sin errores
- [ ] 11 servicios corriendo (`docker compose ps`)
- [ ] Grafana accesible en http://localhost:3000
- [ ] Login exitoso con admin + password
- [ ] Prometheus tiene métricas (query `up` en Explore)
- [ ] License Dashboard muestra licencia en http://localhost:8080
- [ ] No hay errores en logs (`docker compose logs | grep -i error`)

✅ **Si todos los items están OK, la instalación es correcta.**

---

## 📚 SIGUIENTE PASOS

1. **Configurar datasources** en Grafana
2. **Importar dashboards** predefinidos
3. **Configurar alertas** en Alertmanager
4. **Explorar Loki** para logs
5. **Probar Tempo** para trazas distribuidas

Ver documentación completa en: `RESUMEN_IMPLEMENTACION.md`

---

## ⏱️ TIEMPO ESTIMADO

- **Instalación**: 3 minutos
- **Primera carga** (build de imágenes): 2-5 minutos
- **Arranque de servicios**: 30-60 segundos
- **Total desde cero**: ~10 minutos

---

## 🔐 LICENCIA TRIAL

- **Duración**: 180 días (6 meses) desde instalación
- **Retención datos**: 7 días
- **Máximo usuarios**: 5
- **Características**: Todas las funciones core
- **Soporte**: Básico vía email

Para convertir a versión comercial: **comercial@rhinometric.com**
