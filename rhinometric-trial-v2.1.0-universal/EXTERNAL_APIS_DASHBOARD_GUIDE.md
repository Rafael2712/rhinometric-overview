# 🌐 DASHBOARD "EXTERNAL APIs MONITORING" - GUÍA COMPLETA

**Dashboard UID**: `external-apis`  
**Fecha**: 2025-10-28  
**Versión Rhinometric**: 2.1.0 Trial

---

## 📊 DESCRIPCIÓN

Este dashboard demuestra **cómo Rhinometric se conecta con aplicaciones externas** y monitorea su rendimiento en tiempo real usando:
- ✅ **Métricas** (Prometheus)
- ✅ **Logs** (Loki)
- ✅ **Trazas** (próximamente en Tempo)

Es perfecto para mostrar a clientes potenciales la **capacidad de integración de Rhinometric** con APIs de terceros.

---

## 🎯 PROPÓSITO COMERCIAL

### **Demo Ideal Para**:
1. **Clientes SaaS**: Mostrar monitoreo de integraciones (Stripe, SendGrid, Twilio)
2. **E-commerce**: Monitoreo de pasarelas de pago (PayPal, Stripe)
3. **Fintech**: APIs de proveedores financieros (CoinDesk, Yahoo Finance)
4. **DevOps**: Health checks de servicios externos (GitHub, AWS Status)

### **Mensaje de Venta**:
> "Rhinometric no solo monitorea tu infraestructura interna, **también vigila todas tus integraciones externas** en tiempo real. Detecta problemas antes que tus clientes."

---

## 📈 PANELES DEL DASHBOARD

### **SECCIÓN 1: HEALTH STATUS (4 gauges)**

#### Panel 1-3: Individual API Status
- **OpenWeather Status** 🟢
- **GitHub Status API** 🟢
- **CoinDesk BTC Status** 🔴

**Qué muestra**:
- 🟢 Verde = API funcionando correctamente
- 🔴 Rojo = API caída o con errores

**Métrica usada**:
```promql
api_proxy_health_status{api_name="openweather"}
```

#### Panel 4: APIs Health Overview
**Gráfico de líneas** mostrando el estado de todas las APIs en el tiempo.

---

### **SECCIÓN 2: PERFORMANCE**

#### Panel 5: API Request Rate (Successful)
**Time series graph** mostrando:
- Requests por segundo (rps) de cada API
- Solo requests exitosos (status 200)
- Leyenda con: mean, max, last

**Métrica**:
```promql
rate(api_proxy_requests_total{status="200"}[5m])
```

**Lo que debes notar**:
- OpenWeather: ~0.017 rps (1 request cada 60s)
- GitHub Status: ~0.017 rps (1 request cada 60s)
- CoinDesk: 0 rps (API caída)

#### Panel 6: API Response Time (p95 & p50)
**Time series graph** mostrando:
- Percentil 95 (p95): El 95% de requests son más rápidos que este tiempo
- Percentil 50 (p50): Mediana del tiempo de respuesta

**Métricas**:
```promql
# p95
histogram_quantile(0.95, sum(rate(api_proxy_request_duration_seconds_bucket[5m])) by (api_name, le))

# p50
histogram_quantile(0.50, sum(rate(api_proxy_request_duration_seconds_bucket[5m])) by (api_name, le))
```

**Valores esperados**:
- OpenWeather: ~0.24s (rápido ✅)
- GitHub Status: ~0.28-0.38s (aceptable ✅)

---

### **SECCIÓN 3: RELIABILITY**

#### Panel 7: Request Success vs Errors
**Stacked time series** mostrando:
- Requests exitosos (verde)
- Requests fallidos (rojo)

**Métricas**:
```promql
# Success
sum(increase(api_proxy_requests_total{status="200"}[5m])) by (api_name)

# Errors
sum(increase(api_proxy_requests_total{status="0"}[5m])) by (api_name)
```

**Qué buscar**:
- Stack grande de rojo = API con problemas persistentes
- Todo verde = APIs saludables

#### Panel 8: Redis Cache Hit Rate
**Time series** mostrando el porcentaje de requests que fueron servidos desde cache.

**Métrica**:
```promql
rate(api_proxy_cache_hits_total[5m]) / (rate(api_proxy_requests_total[5m]) + rate(api_proxy_cache_hits_total[5m])) * 100
```

**Valores esperados**:
- 0% al inicio (cache vacío)
- Incrementa con el tiempo hasta ~80% (cache funcionando)

---

### **SECCIÓN 4: LOGS**

#### Panel 9: API Proxy Logs - Fetch Events
**Logs panel** mostrando:
- Eventos de fetch exitosos: `✓ Fetched openweather in 0.24s`
- Eventos de fetch fallidos: `✗ Error fetching coindesk_btc`

**Query Loki**:
```logql
{container="rhinometric-api-proxy"} |= "Fetched" or |= "Error fetching"
```

**Uso**:
- Click en cualquier log para expandir detalles
- Usa el time range picker para explorar eventos pasados
- **DRILLDOWN**: Click en un timestamp → Ve métricas relacionadas

#### Panel 10: API Proxy Logs - Errors Only
**Logs panel** mostrando SOLO errores.

**Query Loki**:
```logql
{container="rhinometric-api-proxy"} |= "error" or |= "Error" or |= "ERROR"
```

**Uso**:
- Identifica rápidamente problemas
- Filtra por API específica: `|= "coindesk"`

---

### **SECCIÓN 5: STATISTICS**

#### Panel 11-13: Total Requests por API
**Stat panels** mostrando:
- OpenWeather Total Requests: **182** (desde inicio del contenedor)
- GitHub Status Total Requests: **450+**
- CoinDesk Total Requests: **910** (todos fallidos)

#### Panel 14: Total Cache Hits
**Stat panel** mostrando:
- Total de requests servidos desde Redis cache

---

## 🔍 CÓMO USAR EL DASHBOARD

### **1. Acceso**
```
http://localhost:3000/d/external-apis/f09f8c90-external-apis-monitoring
```

**Credenciales**:
- Usuario: `admin`
- Contraseña: `admin123`

O desde el menú de Grafana:
1. Click en "☰" → Dashboards
2. Click en carpeta "Rhinometric"
3. Busca "🌐 External APIs Monitoring"
4. Click para abrir

### **2. Refresh Automático**
- El dashboard se actualiza cada **30 segundos** automáticamente
- Cambia en el dropdown superior derecho si necesitas más frecuente

### **3. Time Range**
- Por defecto: **Last 1 hour**
- Puedes cambiar a:
  - Last 5 minutes (para demo rápida)
  - Last 6 hours (para análisis de tendencia)
  - Last 24 hours (para análisis diario)

### **4. Drill-Down Logs ↔ Metrics**

**Escenario 1: De Métrica a Log**
1. Identifica un pico de errores en panel "Request Success vs Errors"
2. Nota el timestamp (ej: 13:05:00)
3. Scroll down a "API Proxy Logs - Errors Only"
4. Usa el time picker para buscar ese timestamp
5. Lee el error específico

**Escenario 2: De Log a Métrica**
1. Ves un error en los logs: `✗ Error fetching coindesk_btc`
2. Nota el timestamp
3. Scroll up a "CoinDesk BTC Status" gauge
4. Verifica que está en rojo (0 = unhealthy)
5. Ve al panel "Request Success vs Errors"
6. Confirma el stack rojo de errores

---

## 🎬 DEMO SCRIPT PARA CLIENTES

### **Paso 1: Introducción (30 segundos)**
> "Este dashboard muestra cómo Rhinometric monitorea APIs externas en tiempo real. Actualmente tenemos 3 APIs configuradas: OpenWeather, GitHub Status y CoinDesk."

### **Paso 2: Health Status (45 segundos)**
> "Los gauges superiores muestran el estado instantáneo. Verde significa healthy, rojo significa problemas. Ven que CoinDesk está caído - lo detectamos automáticamente cada minuto."

### **Paso 3: Performance (1 minuto)**
> "Este gráfico muestra el request rate. OpenWeather y GitHub responden consistentemente. Abajo vemos los tiempos de respuesta: OpenWeather es súper rápido (240ms), GitHub es aceptable (280-380ms)."

### **Paso 4: Reliability (45 segundos)**
> "Aquí vemos success vs errors. El stack rojo de CoinDesk muestra 910 requests fallidos. Redis cache hit rate nos dice que estamos ahorrando ~80% de requests reales gracias al caching."

### **Paso 5: Logs (1 minuto)**
> "Los logs en tiempo real muestran cada fetch. Vean estos mensajes: 'Fetched openweather in 0.24s'. Y aquí: 'Error fetching coindesk_btc'. Esto es lo que está pasando AHORA MISMO."

### **Paso 6: Drill-Down Demo (1 minuto)**
> "Ahora la magia: veo un error en los logs a las 13:05. Click en el timestamp, scroll up, y veo exactamente cuándo el gauge cambió a rojo. Esto es el drill-down: Logs ↔ Metrics ↔ Traces, todo conectado."

### **Paso 7: Estadísticas (30 segundos)**
> "Finalmente, las estadísticas totales: 182 requests a OpenWeather, 450+ a GitHub, 910 intentos fallidos a CoinDesk. Todo esto sin escribir una línea de código de monitoreo."

**TOTAL**: ~6 minutos de demo

---

## 🧪 AGREGAR MÁS APIs PARA DEMO

### **APIs Públicas Recomendadas**:

#### **1. JSONPlaceholder (Fake REST API)**
```bash
curl -X POST http://localhost:5000/api/external-apis \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jsonplaceholder",
    "endpoint": "https://jsonplaceholder.typicode.com/posts",
    "auth_type": "none",
    "scrape_interval": 60,
    "is_active": true
  }'
```
**Esperado**: ✅ Healthy, ~100ms response time

#### **2. CatFacts API**
```bash
curl -X POST http://localhost:5000/api/external-apis \
  -H "Content-Type: application/json" \
  -d '{
    "name": "catfacts",
    "endpoint": "https://catfact.ninja/fact",
    "auth_type": "none",
    "scrape_interval": 120,
    "is_active": true
  }'
```
**Esperado**: ✅ Healthy, ~200ms response time

#### **3. Random User Generator**
```bash
curl -X POST http://localhost:5000/api/external-apis \
  -H "Content-Type: application/json" \
  -d '{
    "name": "randomuser",
    "endpoint": "https://randomuser.me/api/",
    "auth_type": "none",
    "scrape_interval": 180,
    "is_active": true
  }'
```
**Esperado**: ✅ Healthy, ~300ms response time

**Nota**: Después de agregar nuevas APIs, espera 60 segundos para que aparezcan en el dashboard.

---

## 🚨 ALERTAS SUGERIDAS

### **Alerta 1: API Unhealthy**
```yaml
alert: APIUnhealthy
expr: api_proxy_health_status == 0
for: 5m
labels:
  severity: warning
annotations:
  summary: "API {{$labels.api_name}} is unhealthy"
```

### **Alerta 2: High Response Time**
```yaml
alert: APISlowResponse
expr: histogram_quantile(0.95, sum(rate(api_proxy_request_duration_seconds_bucket[5m])) by (api_name, le)) > 3
for: 5m
labels:
  severity: warning
annotations:
  summary: "API {{$labels.api_name}} p95 latency is {{$value}}s"
```

### **Alerta 3: High Error Rate**
```yaml
alert: APIHighErrorRate
expr: rate(api_proxy_requests_total{status="0"}[5m]) > 0.1
for: 5m
labels:
  severity: critical
annotations:
  summary: "API {{$labels.api_name}} has high error rate"
```

---

## 📊 MÉTRICAS DISPONIBLES

Todas las métricas disponibles del API Proxy:

```promql
# Health status (1=healthy, 0=unhealthy)
api_proxy_health_status{api_name, url}

# Total requests counter
api_proxy_requests_total{api_name, method, status}

# Request duration histogram
api_proxy_request_duration_seconds_bucket{api_name, method, le}
api_proxy_request_duration_seconds_sum{api_name, method}
api_proxy_request_duration_seconds_count{api_name, method}

# Cache hits counter
api_proxy_cache_hits_total{api_name}
```

---

## 🔧 TROUBLESHOOTING

### **Problema: Dashboard vacío / no muestra datos**

**Causa 1**: Prometheus no está scrapeando el API Proxy
```bash
# Verificar que existe el job
curl -s http://localhost:9090/api/v1/targets | grep api-proxy
```

**Solución**: Verificar que `prometheus.yml` tiene:
```yaml
scrape_configs:
  - job_name: 'api-proxy'
    metrics_path: '/api/metrics/prometheus'
    scrape_interval: 30s
    static_configs:
      - targets: ['api-proxy:8090']
```

**Causa 2**: API Proxy no está ejecutándose
```bash
docker ps | grep api-proxy
```

**Solución**: Reiniciar contenedor
```bash
docker restart rhinometric-api-proxy
```

### **Problema: Logs no aparecen**

**Causa**: Loki no está scrapeando logs del contenedor
```bash
# Verificar que Loki ve el contenedor
curl -s "http://localhost:3100/loki/api/v1/label/container/values" | grep api-proxy
```

**Solución**: Verificar que `promtail-docker.yml` incluye api-proxy

---

## 📝 NOTAS PARA DESARROLLADORES

### **Cómo agregar más paneles**:

1. Abre Grafana UI: http://localhost:3000
2. Navega al dashboard "External APIs Monitoring"
3. Click en "⚙️" (settings) → "JSON Model"
4. Copia el JSON de un panel existente
5. Modifica el `id`, `title`, y `targets.expr`
6. Click "Save dashboard"
7. Exporta el JSON completo: "⬇️" (share) → "Export" → "Save to file"
8. Reemplaza `dashboards/external-apis.json`

### **Métricas personalizadas**:

Edita `api-proxy/server.js` para agregar nuevas métricas:
```javascript
const customMetric = new promClient.Gauge({
  name: 'api_proxy_custom_metric',
  help: 'My custom metric',
  labelNames: ['api_name']
});
```

---

## 🎓 RECURSOS ADICIONALES

- **Prometheus Query Examples**: https://prometheus.io/docs/prometheus/latest/querying/examples/
- **LogQL Tutorial**: https://grafana.com/docs/loki/latest/logql/
- **Grafana Dashboard Best Practices**: https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/

---

## ✅ CHECKLIST PARA DEMOS

Antes de hacer una demo a un cliente:

- [ ] Verificar que al menos 2 APIs están healthy (🟢)
- [ ] Time range configurado en "Last 15 minutes" para demo rápida
- [ ] Refresh configurado en "30s"
- [ ] Agregar 1-2 APIs adicionales para mostrar escalabilidad
- [ ] Preparar script de demo (5-6 minutos)
- [ ] Tener ejemplos de drill-down preparados
- [ ] Conocer valores típicos (latencia, error rate)
- [ ] Tener respuestas para preguntas frecuentes:
  - "¿Funciona con APIs privadas con auth?" → Sí
  - "¿Cuántas APIs puedo monitorear?" → Ilimitadas
  - "¿Tiene alertas?" → Sí, configurables

---

## 🚀 VERSIÓN

**Dashboard Version**: 1.0.0  
**Compatible con**: Rhinometric v2.1.0+  
**Última actualización**: 2025-10-28

**Changelog**:
- v1.0.0 (2025-10-28): Dashboard inicial con 14 paneles
  - Health status gauges
  - Performance time series
  - Reliability metrics
  - Logs integration
  - Statistics panels
