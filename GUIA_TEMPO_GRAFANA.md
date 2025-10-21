# 🎯 GUÍA PARA VER TRAZAS EN GRAFANA TEMPO

## ✅ Estado Actual

### Datasource Tempo Configurado
- **URL**: http://tempo:3200
- **UID**: ff1lwsj8cnta8f  
- **Características**:
  - ✅ httpMethod: GET
  - ✅ Integración con Loki (traces → logs)
  - ✅ Integración con Prometheus (traces → metrics)
  - ✅ Service Map habilitado
  - ✅ Node Graph habilitado

### Trazas Generadas
**8 microservicios con ~820 trazas totales:**

1. **frontend-web**: 150 trazas
   - Operación: GET /home
   - Atributos: http.method, http.route, environment=production
   
2. **api-gateway**: 120 trazas
   - Operación: POST /api/v1/request
   - Atributos: http.method, http.route
   
3. **auth-service**: 80 trazas
   - Operación: POST /auth/login
   - Atributos: http.method, http.route, auth.type=jwt
   
4. **payment-service**: 50 trazas ⚠️ **CON ERRORES**
   - Operación: POST /payment/process
   - Atributos: payment.gateway=stripe, error.type=timeout
   - **Status**: Error (ideal para testing de alertas)
   
5. **user-service**: 49 trazas
   - Operación: GET /users/:id
   - Atributos: http.method, http.route
   
6. **notification-service**: 51 trazas
   - Operación: POST /notifications
   - Atributos: http.method, http.route
   
7. **inventory-service**: 140 trazas
   - Operación: GET /products/search
   - Atributos: http.method, http.route, cache.hit=false
   
8. **database-proxy**: 180 trazas
   - Operación: SELECT FROM users
   - Atributos: db.system=postgresql, db.operation=SELECT, db.name=rhinometric

### Generación Continua
- **telemetrygen** ejecutándose en background
- Genera trazas continuas del servicio "telemetrygen"

---

## 📖 CÓMO VER TRAZAS EN GRAFANA

### Paso 1: Abrir Grafana
```
URL: http://localhost:3000
Usuario: admin
Contraseña: admin_trial_2024
```

### Paso 2: Ir a Explore
1. Clic en el icono de **brújula** (Explore) en el menú lateral izquierdo
2. O ir directamente a: http://localhost:3000/explore

### Paso 3: Seleccionar Datasource Tempo
1. En el dropdown superior, seleccionar **"Tempo"**
2. Verás la interfaz de TraceQL

### Paso 4: Probar Queries

#### Query 1: Ver TODAS las trazas
```traceql
{}
```
- Muestra todas las trazas de todos los servicios
- Límite por defecto: 20 trazas

#### Query 2: Ver trazas de un servicio específico
```traceql
{service.name="frontend-web"}
```
Otros servicios:
```traceql
{service.name="payment-service"}
{service.name="auth-service"}
{service.name="database-proxy"}
```

#### Query 3: Ver SOLO trazas con errores ⚠️
```traceql
{status=error}
```
- Mostrará las 50 trazas del payment-service con errores

#### Query 4: Filtrar por atributos
```traceql
{resource.service.name="payment-service" && span.http.method="POST"}
```

```traceql
{resource.environment="production"}
```

```traceql
{span.db.system="postgresql"}
```

#### Query 5: Búsqueda por duración
```traceql
{duration > 100ms}
```

### Paso 5: Ajustar Rango de Tiempo
⚠️ **IMPORTANTE**: Las trazas están en el tiempo actual

1. En la esquina superior derecha, clic en el selector de tiempo
2. Seleccionar **"Last 15 minutes"** o **"Last 1 hour"**
3. Si no ves trazas, prueba **"Last 6 hours"**

### Paso 6: Explorar una Traza
1. Clic en cualquier traza de la lista
2. Verás:
   - **Timeline**: duración de cada span
   - **Service Graph**: mapa de servicios
   - **Attributes**: todos los metadatos
   - **Logs**: si hay logs correlacionados (integración Loki)

---

## 🔍 VERIFICACIÓN RÁPIDA

### Desde Terminal (para confirmar que hay trazas):
```bash
bash check-traces.sh
```

Debería mostrar algo como:
```
📊 Total de trazas: 100

📦 Trazas por servicio:
   frontend-web: 36 trazas
   api-gateway: 23 trazas
   database-proxy: 12 trazas
   auth-service: 12 trazas
   inventory-service: 12 trazas
   payment-service: 5 trazas

🔢 Servicios únicos: 6
```

### Verificar API de Tempo directamente:
```bash
curl "http://localhost:3200/api/search?q=%7B%7D&limit=10"
```

---

## ❓ TROUBLESHOOTING

### Problema: "No data for selected query"

**Solución 1: Verificar rango de tiempo**
- Expandir a "Last 6 hours" o "Last 24 hours"
- Las trazas pueden estar fuera del rango seleccionado

**Solución 2: Verificar datasource**
- Ir a Configuration → Data Sources → Tempo
- Clic en "Save & Test"
- Debe mostrar: ✅ "Data source successfully connected"

**Solución 3: Refrescar página**
- F5 o Ctrl+R para refrescar
- A veces Grafana cachea el estado "No data"

**Solución 4: Usar la pestaña "Search"**
- En lugar de TraceQL, usa la pestaña "Search"
- Selecciona service.name y busca "frontend-web"
- Más visual y fácil para empezar

### Problema: No aparecen los servicios nuevos

**Verificar que los contenedores terminaron:**
```bash
docker ps -a | grep tracegen
```
- Si siguen corriendo, esperar a que terminen
- Si ya terminaron (hace 10+ segundos), las trazas están en Tempo

**Generar más trazas manualmente:**
```bash
bash generate-all-traces.sh
```

---

## 🎨 FEATURES AVANZADAS

### Service Map
1. Después de seleccionar una traza
2. Clic en la pestaña "Service Graph"
3. Verás un grafo visual de los servicios relacionados

### Node Graph
- Visualización de la relación entre spans dentro de una traza
- Útil para entender el flujo de ejecución

### Trace to Logs
- Si un span tiene logs, verás un botón "Logs for this span"
- Te lleva directamente a Loki con los logs correlacionados

### Trace to Metrics
- Botón "Metrics" en la traza
- Te lleva a Prometheus con las métricas del servicio

---

## 📊 PRÓXIMOS PASOS

Una vez confirmes que ves las trazas en Grafana:

1. ✅ **Aprobar que Tempo funciona**
2. 🎨 **Crear 14 dashboards enterprise**:
   - Tempo Tracing Overview (RED metrics, Service Map)
   - Loki Logs Analysis
   - Prometheus Metrics
   - Postgres DB Performance
   - Redis Cache Metrics
   - Nginx Proxy Statistics
   - Sistema (Node Exporter)
   - Containers (cAdvisor)
   - Blackbox Probes
   - Alertmanager Status
   - Stack Health Overview
   - Application Performance Monitoring (APM)

---

## 📞 COMANDOS ÚTILES

### Ver métricas de Tempo:
```bash
curl http://localhost:3200/metrics | grep tempo_distributor
```

### Ver logs de Tempo:
```bash
docker logs rhinometric-tempo --tail 50
```

### Regenerar trazas:
```bash
bash generate-all-traces.sh
```

### Verificar trazas en Tempo:
```bash
bash check-traces.sh
```

---

**✨ ¡Todo está listo! Abre Grafana y empieza a explorar las trazas!**
