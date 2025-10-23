# 🧪 GUÍA DE PRUEBA LOCAL - RHINOMETRIC TRIAL

**Versión:** Trial 1.0  
**Plataforma:** Windows + WSL Docker  
**Tiempo estimado:** 15-20 minutos

---

## ✅ PRERREQUISITOS

Antes de comenzar, verificar que tienes instalado:

- ✅ **Docker Desktop** (con WSL 2 backend)
- ✅ **WSL 2** (Ubuntu, Debian o similar)
- ✅ **8 GB RAM mínimo** (16 GB recomendado)
- ✅ **20 GB espacio libre** en disco
- ✅ **Puertos libres:** 80, 3000, 3100, 3200, 4317, 4318, 5432, 6379, 9090, 9093

### Verificar Puertos Libres

```bash
# En PowerShell:
netstat -ano | findstr ":3000"
netstat -ano | findstr ":9090"
# Si hay output, el puerto está ocupado
```

Si algún puerto está ocupado, detén el servicio que lo usa o modifica `docker-compose.yml`.

---

## 🚀 INSTALACIÓN PASO A PASO

### Paso 1: Descargar Trial Package

```bash
# Opción A: Si tienes el archivo ZIP
cd C:\Users\TuUsuario\Downloads
unzip rhinometric-trial-package.zip -d C:\rhinometric-trial

# Opción B: Si tienes acceso a repositorio
git clone https://github.com/rhinometric/trial-package.git C:\rhinometric-trial
```

### Paso 2: Navegar al Directorio

```bash
cd C:\rhinometric-trial
# o la ruta donde descomprimiste el trial-package
```

### Paso 3: Verificar Archivos Necesarios

```bash
# Desde WSL:
wsl ls -la docker-compose.yml config/ grafana/ examples/
```

**Debes ver:**
- ✅ `docker-compose.yml` (archivo principal)
- ✅ `config/` (con prometheus-saas.yml, loki-saas.yml, tempo-saas.yml, etc.)
- ✅ `grafana/provisioning/` (datasources y dashboards)
- ✅ `examples/` (código Python y Node.js)
- ✅ `INTEGRATION_GUIDE.md`
- ✅ `WELCOME.html`

### Paso 4: Levantar los Contenedores

```bash
# Usando docker compose:
wsl docker compose up -d
```

**Output esperado:**
```
[+] Running 15/15
 ✔ Container rhinometric-postgres           Started
 ✔ Container rhinometric-redis              Started
 ✔ Container rhinometric-node-exporter      Started
 ✔ Container rhinometric-cadvisor           Started
 ✔ Container rhinometric-promtail           Started
 ✔ Container rhinometric-blackbox-exporter  Started
 ✔ Container rhinometric-license-server     Started
 ✔ Container rhinometric-postgres-exporter  Started
 ✔ Container rhinometric-tempo              Started
 ✔ Container rhinometric-prometheus         Started
 ✔ Container rhinometric-loki               Started
 ✔ Container rhinometric-alertmanager       Started
 ✔ Container rhinometric-grafana            Started
 ✔ Container rhinometric-telemetrygen       Started
 ✔ Container rhinometric-nginx              Started
```

### Paso 5: Esperar Inicialización (2-3 minutos)

```bash
# Monitorear estado:
wsl docker ps --format "table {{.Names}}\t{{.Status}}" | grep rhinometric
```

**Todos deben mostrar:** `Up X seconds` o `Up X minutes`

### Paso 6: Verificar Health Checks

```bash
# Grafana:
curl -s http://localhost:3000/api/health

# Prometheus:
curl -s http://localhost:9090/-/healthy

# License Server:
wsl docker compose exec license-server curl -s http://localhost:5000/health
```

**Output esperado:**
```json
{"database":"ok","version":"12.2.0",...}
Healthy
{"status":"OK","service":"rhinometric-license-server"}
```

---

## 🎯 ACCESO A LA PLATAFORMA

### Página de Bienvenida

Abre en tu navegador:
```
file:///C:/rhinometric-trial/WELCOME.html
```

### Grafana Dashboard

**URL:** `http://localhost:3000`

**Credenciales:**
- **Usuario:** `admin`
- **Contraseña:** `admin_secure_2024`

**Primera vez:**
1. Grafana puede pedirte cambiar contraseña → Puedes omitir (Skip)
2. Verás el Home dashboard de Grafana

### Otros Servicios

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| **Prometheus** | http://localhost:9090 | Sin auth |
| **Alertmanager** | http://localhost:9093 | Sin auth |
| **Tempo UI** | http://localhost:3200 | Sin auth |
| **Nginx (Proxy)** | http://localhost | Redirige a Grafana |

---

## 📊 VERIFICACIÓN DE DASHBOARDS

### Dashboards Precargados (Verificar que todos tienen datos):

1. **System Overview**
   - Path: http://localhost:3000/d/system-overview
   - **Verificar:** Gráficos de CPU, memoria, disco, red
   - **Datos esperados:** Métricas en tiempo real

2. **Distributed Tracing**
   - Path: http://localhost:3000/d/distributed-tracing
   - **Verificar:** Tabla de traces recientes
   - **Datos esperados:** Traces de `demo-rhinometric` service

3. **Logs Explorer**
   - Path: http://localhost:3000/d/logs-explorer
   - **Verificar:** Logs de servicios Docker
   - **Datos esperados:** Logs de prometheus, grafana, loki, etc.

4. **Database Monitoring**
   - Path: http://localhost:3000/d/database-monitoring
   - **Verificar:** Métricas PostgreSQL (conexiones, queries)
   - **Datos esperados:** Estado de PostgreSQL 15

5. **Redis Monitoring**
   - Path: http://localhost:3000/d/redis-monitoring
   - **Verificar:** Métricas de cache Redis
   - **Datos esperados:** Memoria usada, comandos/sec

6. **License Status**
   - Path: http://localhost:3000/d/license-status
   - **Verificar:** Estado trial, días restantes
   - **Datos esperados:** "TRIAL ACTIVE", "30 días restantes"

### Explorar con Explore View

**Prometheus:**
1. Click en "Explore" (icono brújula) en sidebar izquierdo
2. Selecciona datasource "Prometheus"
3. Query de ejemplo:
   ```promql
   rate(container_cpu_usage_seconds_total[5m])
   ```
4. **Resultado esperado:** Gráfico de uso CPU de contenedores

**Loki:**
1. Explore → Datasource "Loki"
2. Query de ejemplo:
   ```logql
   {service_name="unknown_service"}
   ```
3. **Resultado esperado:** Logs de los servicios

**Tempo:**
1. Explore → Datasource "Tempo"
2. Query: (dejar vacío y click en "Run query")
3. **Resultado esperado:** Lista de trace IDs recientes

---

## 🔧 PRUEBA DE INTEGRACIÓN

### Ejemplo Python

```bash
# 1. Navegar a ejemplos:
cd examples/python

# 2. Instalar dependencias:
pip install -r requirements.txt

# 3. Ejecutar script:
python send_metrics_logs_traces.py
```

**Output esperado:**
```
✅ Metrics sent to Prometheus
✅ Logs sent to Loki
✅ Traces sent to Tempo
Generating sample observability data every 10 seconds...
```

**Verificación:**
- Ve a Grafana → Explore → Prometheus
- Query: `my_app_requests_total`
- Deberías ver la métrica creciendo

### Ejemplo Node.js

```bash
# 1. Navegar:
cd examples/nodejs

# 2. Instalar:
npm install

# 3. Ejecutar:
node send-observability.js
```

**Verificación similar a Python**

### PostgreSQL

```bash
# Conectar a base de datos:
wsl docker compose exec postgres psql -U postgres -d rhinometric_trial

# Una vez dentro:
\dt  # Listar tablas
SELECT * FROM users LIMIT 5;
SELECT * FROM app_metrics ORDER BY timestamp DESC LIMIT 10;
```

**Debes ver:**
- Tablas: `users`, `sessions`, `audit_events`, `app_metrics`
- Datos de ejemplo precargados

---

## 📸 SCREENSHOTS ESPERADOS

### 1. Docker Desktop
![Contenedores](screenshot1.png)
- 15 contenedores corriendo
- Todos con status "Running"
- CPU < 5%, Memory < 4 GB

### 2. Grafana Home
![Grafana Home](screenshot2.png)
- Login exitoso
- 6 dashboards listados en sidebar
- Sin errores

### 3. System Overview Dashboard
![System Overview](screenshot3.png)
- 4-6 paneles con gráficos
- Datos en tiempo real (líneas moviéndose)
- Sin "No Data" messages

### 4. Logs Explorer
![Logs Explorer](screenshot4.png)
- Tabla con logs recientes
- Timestamps en tiempo real
- Diferentes service_name (prometheus, grafana, loki)

### 5. Distributed Tracing
![Tracing](screenshot5.png)
- Tabla de traces
- Trace IDs cliqueables
- Duración en ms

---

## 🐛 TROUBLESHOOTING

### Problema 1: "Port already in use"

**Síntoma:**
```
Error response from daemon: Ports are not available: exposing port TCP 0.0.0.0:3000 -> 0.0.0.0:0: listen tcp 0.0.0.0:3000: bind: Only one usage of each socket address...
```

**Solución:**
```bash
# Ver qué proceso usa el puerto:
netstat -ano | findstr ":3000"

# Matar proceso (reemplaza PID):
taskkill /PID 12345 /F

# O cambiar puerto en docker-compose.yml:
ports:
  - "3001:3000"  # Cambiar de 3000 a 3001
```

### Problema 2: "No data" en dashboards

**Síntoma:** Dashboards muestran "No data" o paneles vacíos

**Diagnóstico:**
```bash
# 1. Verificar que Prometheus está scrapeando:
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health=="down")'

# 2. Verificar logs de Grafana:
wsl docker compose logs grafana | grep -i error

# 3. Verificar datasources en Grafana:
curl -u admin:admin_secure_2024 http://localhost:3000/api/datasources
```

**Soluciones:**
- Esperar 2-3 minutos más (datos tardan en llegar)
- Refrescar dashboard (F5)
- Verificar tiempo de query (últimas 6 horas mínimo)

### Problema 3: Contenedor restart loop

**Síntoma:**
```
rhinometric-nginx    Restarting (1) 2 seconds ago
```

**Diagnóstico:**
```bash
wsl docker compose logs nginx --tail 50
```

**Soluciones comunes:**
- Archivo de configuración corrupto → Verificar config/nginx-trial.conf
- Puerto ocupado → Cambiar en docker-compose.yml
- Dependencia no disponible → Verificar que grafana está UP

### Problema 4: "Cannot connect to PostgreSQL"

**Solución:**
```bash
# Verificar que PostgreSQL está corriendo:
wsl docker compose exec postgres pg_isready -U postgres

# Si falla, revisar logs:
wsl docker compose logs postgres --tail 30

# Reiniciar solo PostgreSQL:
wsl docker compose restart postgres
```

### Problema 5: License Server unhealthy

**Síntoma:** Services no arrancan porque dependen de license-server

**Solución:**
```bash
# Verificar health:
wsl docker compose exec license-server curl http://localhost:5000/health

# Ver logs:
wsl docker compose logs license-server

# Reiniciar:
wsl docker compose restart license-server
wsl docker compose up -d  # Re-crear dependientes
```

---

## 🔄 COMANDOS ÚTILES

### Ver logs en tiempo real
```bash
# Todos los servicios:
wsl docker compose logs -f

# Un servicio específico:
wsl docker compose logs -f grafana
```

### Reiniciar servicios
```bash
# Todos:
wsl docker compose restart

# Uno específico:
wsl docker compose restart prometheus
```

### Detener todo
```bash
wsl docker compose down
```

### Detener y limpiar datos
```bash
wsl docker compose down -v  # ⚠️ Elimina volúmenes (datos)
```

### Ver uso de recursos
```bash
wsl docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### Ejecutar comando en contenedor
```bash
wsl docker compose exec prometheus promtool check config /etc/prometheus/prometheus.yml
```

---

## ✅ CHECKLIST DE VERIFICACIÓN COMPLETA

Usa este checklist después de la instalación:

- [ ] 15 contenedores corriendo (`docker ps | grep rhinometric | wc -l` = 15)
- [ ] Grafana accesible en http://localhost:3000
- [ ] Login exitoso con admin / admin_secure_2024
- [ ] 6 dashboards visibles en sidebar
- [ ] Dashboard "System Overview" muestra datos
- [ ] Dashboard "Logs Explorer" muestra logs
- [ ] Dashboard "Distributed Tracing" muestra traces
- [ ] Prometheus targets: 8/10 UP (http://localhost:9090/targets)
- [ ] Loki recibiendo logs (Explore → Loki → `{service_name=~".+"}`)
- [ ] Tempo recibiendo traces (Explore → Tempo → ver trace IDs)
- [ ] PostgreSQL conecta OK (`docker compose exec postgres pg_isready`)
- [ ] Redis UP (`docker compose exec redis redis-cli ping` = PONG)
- [ ] Ejemplo Python ejecuta sin errores
- [ ] Ejemplo Node.js ejecuta sin errores
- [ ] Métricas custom visibles en Prometheus (`my_app_requests_total`)
- [ ] License Status dashboard muestra "TRIAL ACTIVE"

**Si todos los checks pasan:** ✅ **Instalación exitosa**

---

## 📞 SOPORTE

### Documentación Adicional

- **Integración con tu app:** `INTEGRATION_GUIDE.md`
- **Seguridad del trial:** `SECURITY_AUDIT.md`
- **Página de bienvenida:** `WELCOME.html`

### Logs para Reportar Problemas

Si necesitas soporte, incluye:

```bash
# Generar reporte completo:
wsl docker compose ps > reporte.txt
wsl docker compose logs --tail 100 >> reporte.txt
wsl docker stats --no-stream >> reporte.txt
```

---

**¡Disfruta explorando Rhinometric Trial!** 🚀

**Recuerda:** Esta versión tiene funcionalidad completa por 30 días. Después de ese período, los servicios dejarán de funcionar automáticamente.

Para upgrade a versión completa, contacta a tu representante comercial.
