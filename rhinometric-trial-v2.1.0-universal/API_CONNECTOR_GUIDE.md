# 🔌 RHINOMETRIC API CONNECTOR - GUÍA COMPLETA
## Cómo Funciona el Conector de APIs Externas

**Fecha**: 2025-10-28  
**Versión**: 2.1.0 Trial

---

## 📋 RESPUESTA A TUS PREGUNTAS

### **1. ¿Open Meteo ya está conectado a nuestra versión trial?**

**✅ SÍ, CONFIRMADO**

Actualmente tienes **3 APIs externas conectadas**:

| API | Estado | URL | Scrape Interval |
|-----|--------|-----|-----------------|
| **openweather** | ✅ Healthy | https://api.openweathermap.org | 60s |
| **github_status** | ✅ Healthy | https://www.githubstatus.com/api/v2/status.json | 60s |
| **coindesk_btc** | ❌ Unhealthy | https://api.coindesk.com/v1/bpi/currentprice.json | 60s |

**Nota**: CoinDesk da error de DNS (`ENOTFOUND api.coindesk.com`) - puede estar bloqueado o caído temporalmente.

---

## 🔄 ARQUITECTURA DEL CONECTOR

### Componentes Involucrados:

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUJO COMPLETO                            │
└─────────────────────────────────────────────────────────────┘

[API Externa]  ←────┐
  openweather       │
  github_status     │  (HTTP Fetch cada 60s)
  coindesk_btc      │
                    │
                    ↓
┌──────────────────────────────────────────────────────┐
│  API PROXY (Puerto 8090)                             │
│  - Hace fetch a APIs externas                        │
│  - Cachea respuestas en Redis (5 min)               │
│  - Expone métricas en /api/metrics/prometheus        │
│  - Health checks cada minuto                         │
└──────────────────────────────────────────────────────┘
                    │
                    ↓ (scrape cada 30s)
┌──────────────────────────────────────────────────────┐
│  PROMETHEUS (Puerto 9090)                            │
│  - Scrapea métricas del API Proxy                   │
│  - Almacena series temporales                        │
│  - Métricas disponibles:                             │
│    * api_proxy_requests_total                        │
│    * api_proxy_request_duration_seconds              │
│    * api_proxy_health_status                         │
│    * api_proxy_cache_hits_total                      │
└──────────────────────────────────────────────────────┘
                    │
                    ↓ (queries)
┌──────────────────────────────────────────────────────┐
│  GRAFANA (Puerto 3000)                               │
│  - Dashboards visualizan métricas                    │
│  - Alertas sobre health status                       │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  API CONNECTOR UI (Puerto 8091)                      │
│  - Interfaz web para agregar/eliminar APIs          │
│  - Muestra estado en tiempo real                     │
│  - Permite test de conectividad                      │
└──────────────────────────────────────────────────────┘
```

---

## 📊 ¿QUÉ PUEDES VER DE LAS CONEXIONES?

### **1. Métricas en Prometheus**

Actualmente el API Proxy **NO está exponiendo métricas correctamente** a Prometheus. Necesitamos verificar la configuración.

**Métricas esperadas**:
```prometheus
# Health status (1=healthy, 0=unhealthy)
api_proxy_health_status{api_name="openweather"}

# Request count
api_proxy_requests_total{api_name="openweather", method="GET", status="200"}

# Request duration
api_proxy_request_duration_seconds{api_name="openweather"}

# Cache hits
api_proxy_cache_hits_total{api_name="openweather"}
```

### **2. Logs en Loki**

**Comando para ver logs**:
```bash
# Logs del API Proxy
docker logs rhinometric-api-proxy --tail 50

# Logs de APIs exitosas
docker logs rhinometric-api-proxy | grep "✓ Fetched"

# Logs de APIs fallidas
docker logs rhinometric-api-proxy | grep "✗ Error"
```

**Lo que verás**:
```
info: ✓ Fetched openweather in 0.24s
info: ✓ Fetched github_status in 0.28s
error: ✗ Error fetching coindesk_btc
```

### **3. Trazas en Tempo**

Actualmente **NO hay instrumentación de tracing** en el API Proxy. Esto es un enhancement para v2.2.0.

### **4. Health Status en UI**

Accede a: **http://localhost:8091**

Verás:
- 🟢 **openweather** - healthy
- 🟢 **github_status** - healthy  
- 🔴 **coindesk_btc** - unhealthy

---

## 🧪 NUEVAS APIs PARA PROBAR

Te proporciono **5 APIs públicas** para que agregues y pruebes:

### **API 1: JSONPlaceholder (Posts)**
```json
{
  "name": "jsonplaceholder_posts",
  "endpoint": "https://jsonplaceholder.typicode.com/posts",
  "authType": "none",
  "scrapeInterval": 60,
  "enabled": true
}
```
**Qué hace**: API de prueba con posts de ejemplo  
**Esperado**: ✅ Healthy

### **API 2: JSONPlaceholder (Users)**
```json
{
  "name": "jsonplaceholder_users",
  "endpoint": "https://jsonplaceholder.typicode.com/users",
  "authType": "none",
  "scrapeInterval": 120,
  "enabled": true
}
```
**Qué hace**: API de prueba con usuarios de ejemplo  
**Esperado**: ✅ Healthy

### **API 3: CatFacts API**
```json
{
  "name": "catfacts",
  "endpoint": "https://catfact.ninja/fact",
  "authType": "none",
  "scrapeInterval": 300,
  "enabled": true
}
```
**Qué hace**: Devuelve hechos aleatorios sobre gatos  
**Esperado**: ✅ Healthy

### **API 4: IP API (GeoIP)**
```json
{
  "name": "ipapi",
  "endpoint": "https://ipapi.co/json/",
  "authType": "none",
  "scrapeInterval": 300,
  "enabled": true
}
```
**Qué hace**: Devuelve información de geolocalización de tu IP  
**Esperado**: ✅ Healthy

### **API 5: Random User Generator**
```json
{
  "name": "randomuser",
  "endpoint": "https://randomuser.me/api/",
  "authType": "none",
  "scrapeInterval": 180,
  "enabled": true
}
```
**Qué hace**: Genera usuarios aleatorios con datos ficticios  
**Esperado**: ✅ Healthy

---

## 🔧 CÓMO AGREGAR NUEVAS APIs

### **Método 1: Desde la UI (Puerto 8091)**

1. Abre **http://localhost:8091**
2. Click en "➕ Agregar Nueva API"
3. Llena el formulario:
   - **Nombre**: `jsonplaceholder_posts`
   - **Endpoint**: `https://jsonplaceholder.typicode.com/posts`
   - **Auth Type**: `none`
   - **Intervalo**: `60` (segundos)
4. Click en "🧪 Test Connection" (opcional)
5. Click en "💾 Guardar API"

### **Método 2: Desde CLI (curl)**

```bash
curl -X POST http://localhost:5000/api/external-apis \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jsonplaceholder_posts",
    "endpoint": "https://jsonplaceholder.typicode.com/posts",
    "auth_type": "none",
    "scrape_interval": 60,
    "is_active": true
  }'
```

### **Método 3: Desde PostgreSQL (directo)**

```bash
docker exec -it rhinometric-postgres psql -U rhinometric -d rhinometric_trial -c "
INSERT INTO external_apis (name, endpoint, auth_type, scrape_interval, is_active)
VALUES ('jsonplaceholder_posts', 'https://jsonplaceholder.typicode.com/posts', 'none', 60, true);
"
```

---

## 📈 VERIFICAR QUE FUNCIONA

### **1. Check Health Status**
```bash
curl http://localhost:8090/api/health/all | python3 -m json.tool
```

**Esperado**:
```json
{
  "openweather": {"status": "healthy", "lastCheck": "..."},
  "github_status": {"status": "healthy", "lastCheck": "..."},
  "jsonplaceholder_posts": {"status": "healthy", "lastCheck": "..."}
}
```

### **2. Check Logs**
```bash
docker logs rhinometric-api-proxy --tail 20 | grep "jsonplaceholder"
```

**Esperado**:
```
info: ✓ Fetched jsonplaceholder_posts in 0.15s
```

### **3. Check Prometheus Metrics** (cuando esté funcionando)
```bash
curl http://localhost:9090/api/v1/query?query=api_proxy_health_status | python3 -m json.tool
```

### **4. Check en Grafana**

Dashboard recomendado: **API Proxy** dashboard

Verás:
- Total de APIs conectadas
- Health status de cada API
- Request rate por API
- Response time por API
- Cache hit rate

---

## 🐛 PROBLEMA ACTUAL DETECTADO

### **Issue**: API Proxy NO está exponiendo métricas a Prometheus

**Síntomas**:
```bash
$ curl http://localhost:9090/api/v1/query?query=api_proxy_health_status
# Result: []  # ← Vacío, no hay datos
```

**Causa probable**:
1. Prometheus no está scrapeando el endpoint `/api/metrics/prometheus`
2. El API Proxy no está registrando las métricas correctamente

**Solución**: Verificar configuración de Prometheus (próximo paso)

---

## 📝 RESUMEN EJECUTIVO

### **¿Open Meteo está conectado?**
✅ **SÍ** - Configurado como "openweather" y funcionando correctamente

### **¿Qué puedo ver?**
- ✅ **Logs**: En `docker logs rhinometric-api-proxy`
- ⚠️ **Métricas**: Deben configurarse en Prometheus
- ❌ **Trazas**: No implementado aún (v2.2.0)
- ✅ **Health Status**: En UI http://localhost:8091

### **APIs para probar**:
1. ✅ jsonplaceholder_posts - Posts de prueba
2. ✅ jsonplaceholder_users - Usuarios de prueba
3. ✅ catfacts - Hechos sobre gatos
4. ✅ ipapi - Geolocalización
5. ✅ randomuser - Generador de usuarios

---

## 🚀 PRÓXIMOS PASOS

1. **Agregar las 5 APIs de prueba** (tú)
2. **Verificar configuración de Prometheus** para scraping del API Proxy (yo)
3. **Confirmar funcionalidad completa** antes de pasar a Oracle Cloud

¿Quieres que primero arregle la configuración de Prometheus para que veas las métricas, o prefieres agregar tú las APIs de prueba primero?
