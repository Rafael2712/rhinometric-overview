# 🏗️ Rhinometric - Arquitectura Técnica

**Versión:** 2.5.1  
**Fecha:** Diciembre 2025  
**Audiencia:** Arquitectos, SRE, DevOps Engineers

---

## 📐 Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USUARIO (Browser)                            │
│                    http://host:3002 (Console)                       │
│                    http://host:3000 (Grafana)                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    RHINOMETRIC CONSOLE                              │
│  ┌──────────────────────┐         ┌──────────────────────┐         │
│  │   Frontend (React)   │◄────────┤  Backend (FastAPI)   │         │
│  │   Port: 3002         │         │   Port: 8105         │         │
│  └──────────────────────┘         └──────────┬───────────┘         │
└─────────────────────────────────────────────┼─────────────────────┘
                                              │
                   ┌──────────────────────────┼──────────────────────┐
                   │                          │                      │
                   ▼                          ▼                      ▼
         ┌─────────────────┐      ┌───────────────────┐   ┌──────────────────┐
         │   PROMETHEUS    │      │  AI ANOMALY       │   │  ALERTMANAGER    │
         │   Port: 9090    │      │  ENGINE           │   │  Port: 9093      │
         │                 │      │  Port: 8085       │   │                  │
         │ - Métricas      │      │ - ML Models       │   │ - Alert Rules    │
         │ - Time Series   │      │ - Baselines       │   │ - Routing        │
         │ - Scraping      │      │ - Detección       │   │ - Grouping       │
         └────────┬────────┘      └─────────┬─────────┘   └──────────────────┘
                  │                         │
                  │ Scrapes                 │ Queries
                  ▼                         │
    ┌─────────────────────────────┐         │
    │  MONITORED SERVICES         │         │
    │                             │         │
    │ - node-exporter (host)      │─────────┘
    │ - postgres-exporter         │
    │ - redis-exporter            │
    │ - cAdvisor (containers)     │
    │ - Custom apps (webhooks)    │
    └─────────────────────────────┘

         ┌─────────────────┐              ┌──────────────────┐
         │      LOKI       │              │     JAEGER       │
         │   Port: 3100    │              │   Port: 16686    │
         │                 │              │   Port: 14317    │
         │ - Log Storage   │              │                  │
         │ - Indexing      │              │ - Trace Storage  │
         │ - Query API     │              │ - OTLP Receiver  │
         └────────┬────────┘              └─────────┬────────┘
                  ▲                                 ▲
                  │ Logs                            │ Traces
                  │                                 │
         ┌────────┴────────┐              ┌─────────┴─────────┐
         │    PROMTAIL     │              │  OTEL COLLECTOR   │
         │                 │              │                   │
         │ - Docker Logs   │              │ - OTLP Gateway    │
         │ - Scraping      │              │ - Format Convert  │
         └─────────────────┘              └───────────────────┘
                  ▲                                 ▲
                  │                                 │
         ┌────────┴──────────────────────────────────┴────────┐
         │              DOCKER CONTAINERS                     │
         │  (Applications, Services, Databases, etc.)         │
         └────────────────────────────────────────────────────┘

                   ┌──────────────────────────────┐
                   │  LICENSE SERVER (AWS Lambda)  │
                   │  - Validación remota         │
                   │  - Check cada 24h            │
                   │  (Coming Soon)               │
                   └──────────────────────────────┘
```

---

## 🔄 Flujos de Datos Detallados

### **1. Flujo de MÉTRICAS (Metrics)**

```
Servicio/App → Prometheus Exporter → Prometheus → Grafana → Console
                                    ↓
                              AI Anomaly Engine
                                    ↓
                              Anomalías Detectadas → Alertmanager → Console
```

**Paso a paso:**

1. **Recopilación:**
   - `node-exporter` (9100): Expone métricas del host (CPU, RAM, disco, red)
   - `postgres-exporter` (9187): Métricas de PostgreSQL
   - `redis-exporter` (9121): Métricas de Redis
   - `cAdvisor` (8090): Métricas de contenedores Docker
   - Apps custom: Exponen `/metrics` en formato Prometheus

2. **Scraping:**
   - Prometheus hace **scrape** cada 15 segundos de todos los targets configurados
   - Almacena series temporales en base de datos TSDB local
   - Retención: 15 días por defecto

3. **Consulta:**
   - Grafana consulta Prometheus vía API `/api/v1/query` y `/api/v1/query_range`
   - Console Backend consulta Prometheus para KPIs
   - AI Anomaly Engine consulta Prometheus cada 10 minutos para entrenar modelos

4. **Detección de Anomalías:**
   - AI Engine obtiene últimas 24h de cada métrica (288 puntos con step=5m)
   - Entrena 3 modelos ML: Isolation Forest, LOF, Statistical
   - Compara valor actual vs baseline esperado
   - Si deviation > threshold → genera anomalía
   - Expone anomalías vía API `/api/anomalies`

5. **Alertas:**
   - Prometheus evalúa reglas en `config/rules/alerts.yml` cada 15s
   - Si condición cumplida (ej: `up{job="redis"} == 0`) → dispara alerta
   - Alerta enviada a Alertmanager
   - Alertmanager agrupa, deduplica y (futuro) enruta a Slack/Email
   - Console muestra alertas activas vía `/api/v2/alerts`

---

### **2. Flujo de LOGS**

```
App (Docker) → stdout/stderr → Promtail → Loki → Console / Grafana
```

**Paso a paso:**

1. **Generación:**
   - Aplicaciones escriben logs a `stdout`/`stderr` (buena práctica Docker)
   - Docker captura logs automáticamente

2. **Recopilación:**
   - **Promtail** lee logs de Docker vía API del Docker daemon
   - Etiqueta cada log con `container_name`, `container_id`, `job`
   - Configuración: `config/promtail-config.yml`

3. **Envío:**
   - Promtail envía logs a Loki vía HTTP (puerto 3100)
   - Loki indexa logs por etiquetas (no por contenido completo)

4. **Consulta:**
   - Console consulta Loki vía LogQL: `{container_name=~"rhinometric.*"} |= "error"`
   - Grafana muestra logs en dashboard "Logs Explorer"

5. **Integración con Trazas:**
   - Si log contiene `trace_id`, se puede correlacionar con Jaeger
   - Click en log → abre traza correspondiente en Jaeger

---

### **3. Flujo de TRAZAS (Distributed Tracing)**

```
App (instrumentada) → OTLP → OTEL Collector → Jaeger → Console
```

**Paso a paso:**

1. **Instrumentación:**
   - App debe estar instrumentada con OpenTelemetry SDK
   - Ejemplo Python:
     ```python
     from opentelemetry import trace
     tracer = trace.get_tracer(__name__)
     
     with tracer.start_as_current_span("my_operation"):
         # código aquí
     ```

2. **Exportación:**
   - App exporta trazas vía OTLP (OpenTelemetry Protocol)
   - Destino: `otel-collector:4317` (gRPC) o `4318` (HTTP)

3. **Procesamiento:**
   - **OTEL Collector** recibe trazas
   - Aplica transformaciones (sampling, filtros)
   - Reenvía a Jaeger

4. **Almacenamiento:**
   - **Jaeger** almacena trazas en memoria (modo all-in-one)
   - Indexa por `service_name`, `operation_name`, `trace_id`

5. **Visualización:**
   - Console tiene botón "View Traces" que abre Jaeger UI
   - Jaeger muestra timeline de spans (latencias, errores, dependencias)

---

### **4. Flujo de ANOMALÍAS (AI Detection)**

```
Prometheus → AI Engine (fetch_metrics) → ML Training → Anomaly Detection → API → Console
```

**Paso a paso:**

1. **Recopilación de datos históricos:**
   - AI Engine consulta Prometheus cada 10 minutos
   - Query: `node_cpu_seconds_total`, `node_memory_MemAvailable_bytes`, etc.
   - Range: Últimas 24 horas con step=5min (288 puntos)

2. **Entrenamiento de modelos:**
   ```python
   # Isolation Forest: detecta outliers en distribución
   iso_forest = IsolationForest(contamination=0.1)
   iso_forest.fit(values)
   
   # LOF: detecta puntos anómalos vs vecinos
   lof = LocalOutlierFactor(n_neighbors=20)
   lof.fit_predict(values)
   
   # Statistical: desviación estándar > 3σ
   baseline_mean = np.mean(values)
   baseline_std = np.std(values)
   if abs(current - baseline_mean) > 3 * baseline_std:
       anomaly_detected = True
   ```

3. **Cálculo de baselines:**
   - **Hourly baseline:** Media de la misma hora en días anteriores
   - **Daily baseline:** Media de todo el día anterior
   - Ejemplo: CPU esperado a las 14:00 = promedio(CPU 14:00 últimos 7 días)

4. **Detección:**
   - Compara valor actual vs baseline
   - Calcula % de desviación
   - Asigna severity:
     - Low: deviation < 20%
     - Medium: 20% ≤ deviation < 50%
     - High: 50% ≤ deviation < 100%
     - Critical: deviation ≥ 100%

5. **Exposición:**
   - Anomalías se exponen vía API: `http://ai-anomaly:8085/api/anomalies`
   - Console consulta esta API cada 30s
   - Muestra anomalías en página "AI Anomalies"

---

### **5. Flujo de ALERTAS (Alert Management)**

```
Prometheus → AlertManager → (Futuro: Slack/Email) → Console
```

**Paso a paso:**

1. **Definición de reglas:**
   - Reglas definidas en `config/rules/alerts.yml`
   - Ejemplo:
     ```yaml
     - alert: RedisDown
       expr: up{job="redis"} == 0
       for: 2m
       labels:
         severity: critical
       annotations:
         summary: "Redis está caído"
     ```

2. **Evaluación:**
   - Prometheus evalúa reglas cada 15 segundos
   - Si condición `expr` es `true` durante tiempo `for` → dispara alerta

3. **Envío a Alertmanager:**
   - Prometheus envía alerta a Alertmanager (puerto 9093)
   - Include: labels, annotations, timestamp

4. **Procesamiento en Alertmanager:**
   - **Grouping:** Agrupa alertas similares (ej: múltiples contenedores caídos)
   - **Inhibition:** Suprime alertas de bajo nivel si hay una de alto nivel (ej: si Prometheus cae, no alertar de "no métricas")
   - **Silencing:** Usuario puede silenciar alertas manualmente
   - **Routing:** (Futuro) Envía a Slack, Email, PagerDuty según configuración

5. **Visualización:**
   - Console consulta `/api/v2/alerts` de Alertmanager
   - Muestra alertas activas en página "Alerts"
   - Colorea por severity (yellow=warning, red=critical)

---

### **6. Flujo de LICENCIAS (Coming Soon)**

```
Console → License Server (AWS Lambda) → DynamoDB → Respuesta → Console
```

**Diseño planificado:**

1. **Primera validación (instalación):**
   - Usuario introduce license key en Console
   - Console envía `POST /validate` a License Server
   - Server verifica en DynamoDB: ¿existe? ¿expirada? ¿revocada?
   - Respuesta: `valid` / `expired` / `invalid`

2. **Revalidación periódica:**
   - Cada 24h, Console hace check automático
   - Si no hay internet → continúa funcionando 7 días (grace period)
   - Después de 7 días sin validación → modo read-only

3. **Tipos de licencia:**
   - **Trial:** 15 días, todas las features
   - **Annual:** 1 año, renovable, por instancia/host
   - **Perpetual:** Sin caducidad, por instancia/host
   - **Enterprise:** Custom (múltiples hosts, soporte prioritario)

---

## 🌐 Puertos y Servicios

| **Servicio** | **Puerto Externo** | **Puerto Interno** | **Protocolo** | **Descripción** |
|--------------|-------------------|--------------------|---------------|-----------------|
| **Console Frontend** | 3002 | 3002 | HTTP | Interfaz web React |
| **Console Backend** | 8105 | 8105 | HTTP | API FastAPI |
| **Prometheus** | 9090 | 9090 | HTTP | API de métricas |
| **Grafana** | 3000 | 3000 | HTTP | Dashboards |
| **Loki** | 3100 | 3100 | HTTP | API de logs |
| **Jaeger UI** | 16686 | 16686 | HTTP | UI de trazas |
| **Jaeger OTLP gRPC** | 14317 | 4317 | gRPC | Recepción de trazas |
| **Jaeger OTLP HTTP** | 14318 | 4318 | HTTP | Recepción de trazas |
| **Alertmanager** | 9093 | 9093 | HTTP | API de alertas |
| **AI Anomaly Engine** | 8085 | 8085 | HTTP | API de anomalías |
| **node-exporter** | 9100 | 9100 | HTTP | Métricas del host |
| **postgres-exporter** | 9187 | 9187 | HTTP | Métricas PostgreSQL |
| **redis-exporter** | 9121 | 9121 | HTTP | Métricas Redis |
| **cAdvisor** | 8090 | 8080 | HTTP | Métricas contenedores |

**Nota:** Los puertos internos son usados dentro de la red Docker. Los externos son accesibles desde el host.

---

## 💾 Requisitos de Hardware

### **Instalación Mínima (10-50 hosts monitorizados)**

| **Componente** | **CPU** | **RAM** | **Disco** | **Red** |
|----------------|---------|---------|-----------|---------|
| **Host total** | 4 vCPUs | 8 GB | 100 GB SSD | 100 Mbps |

**Desglose por servicio:**
- Prometheus: 1 vCPU, 2 GB RAM, 50 GB disco (retención 15 días)
- Grafana: 0.5 vCPU, 512 MB RAM, 1 GB disco
- Loki: 1 vCPU, 1 GB RAM, 20 GB disco
- Jaeger: 0.5 vCPU, 512 MB RAM, 10 GB disco
- AI Engine: 1 vCPU, 2 GB RAM, 1 GB disco
- Console: 0.5 vCPU, 1 GB RAM, 1 GB disco
- Resto: 0.5 vCPU, 1 GB RAM, 17 GB disco

### **Instalación Media (50-200 hosts)**

| **Componente** | **CPU** | **RAM** | **Disco** | **Red** |
|----------------|---------|---------|-----------|---------|
| **Host total** | 8 vCPUs | 16 GB | 500 GB SSD | 1 Gbps |

### **Instalación Grande (200-500 hosts)**

| **Componente** | **CPU** | **RAM** | **Disco** | **Red** |
|----------------|---------|---------|-----------|---------|
| **Host total** | 16 vCPUs | 32 GB | 1 TB SSD | 1 Gbps |

**Recomendaciones adicionales:**
- **OS:** Ubuntu 22.04 LTS, Debian 11/12, Rocky Linux 8/9
- **Docker:** >= 24.0
- **Docker Compose:** >= 2.20
- **Disco:** SSD recomendado (IOPS alto para Prometheus/Loki)
- **Red:** Baja latencia entre servicios (<1ms ideal)

---

## 🗂️ Estructura de Directorios

```
rhinometric/
├── docker-compose.yml              # Orquestación principal
├── config/
│   ├── prometheus-v2.2.yml         # Config Prometheus + scrape targets
│   ├── promtail-config.yml         # Config Promtail (logs)
│   ├── loki-config-limited.yml     # Config Loki
│   ├── rules/
│   │   └── alerts.yml              # Reglas de alertas
│   └── datasources/
│       └── datasources.yml         # Datasources de Grafana
├── grafana/
│   └── provisioning/
│       └── dashboards/
│           └── json/               # 8 dashboards .json
├── rhinometric-console/
│   ├── frontend/                   # React app
│   ├── backend/                    # FastAPI app
│   └── Dockerfile
├── rhinometric-ai-anomaly/         # AI Engine Python
├── data/                           # Volúmenes persistentes
│   ├── prometheus/                 # TSDB de métricas
│   ├── grafana/                    # Dashboards + config
│   ├── loki/                       # Índices de logs
│   └── postgres/                   # BBDD para Console
└── docs/                           # Documentación (este archivo)
```

---

## 🔐 Seguridad

### **Autenticación**
- **Console:** Login con usuario/contraseña (almacenado en PostgreSQL con hash bcrypt)
- **Grafana:** Login independiente (admin/admin por defecto - **cambiar obligatorio**)
- **Prometheus/Loki/Jaeger:** Sin autenticación (acceso solo desde red interna Docker)

### **Autorización**
- **Console:** 2 roles: `admin` (full access), `viewer` (read-only)
- **Grafana:** Roles nativos (Admin, Editor, Viewer)

### **Red**
- Todos los servicios en red Docker privada (`rhinometric_network_v22`)
- Solo Console, Grafana, Prometheus, Jaeger exponen puertos al host
- Recomendación: Firewall para bloquear puertos excepto 3002 (Console) y 3000 (Grafana)

### **Datos**
- No se envía información fuera del host (100% on-premise)
- Logs/métricas nunca exportados a cloud
- License Server (futuro): Solo envía hash de license key, no datos operacionales

---

## 🚀 Escalabilidad

### **Vertical Scaling**
- Aumentar CPU/RAM del host
- Configurar retención de Prometheus/Loki según espacio disponible

### **Horizontal Scaling (Futuro)**
- **Prometheus:** Usar federation o Thanos
- **Loki:** Distribuir ingesters
- **Kubernetes:** Helm chart planificado para v3.0

---

## 📦 Dependencias Externas

| **Servicio** | **Imagen Docker** | **Versión** |
|--------------|------------------|-------------|
| Prometheus | `prom/prometheus` | v2.53.0 |
| Grafana | `grafana/grafana` | 11.0.0 |
| Loki | `grafana/loki` | 2.9.3 |
| Promtail | `grafana/promtail` | 2.9.3 |
| Jaeger | `jaegertracing/all-in-one` | latest |
| OTEL Collector | `otel/opentelemetry-collector-contrib` | 0.104.0 |
| Node Exporter | `prom/node-exporter` | latest |
| Postgres Exporter | `quay.io/prometheuscommunity/postgres-exporter` | latest |
| Redis Exporter | `oliver006/redis_exporter` | latest |
| cAdvisor | `gcr.io/cadvisor/cadvisor` | latest |
| PostgreSQL | `postgres` | 15-alpine |
| Redis | `redis` | 7-alpine |

---

## 🔄 Actualizaciones

### **Proceso de actualización:**
1. Backup de volúmenes (`data/`)
2. Pull de nuevas imágenes: `docker-compose pull`
3. Recrear contenedores: `docker-compose up -d`
4. Verificar logs: `docker-compose logs -f`

### **Rollback:**
1. `docker-compose down`
2. Restaurar backup
3. `docker-compose up -d` con versión anterior

---

## 📚 Recursos Adicionales

- **Prometheus Query Language (PromQL):** https://prometheus.io/docs/prometheus/latest/querying/basics/
- **LogQL (Loki):** https://grafana.com/docs/loki/latest/query/
- **OpenTelemetry Docs:** https://opentelemetry.io/docs/
- **Grafana Dashboards:** https://grafana.com/grafana/dashboards/

---

**Próximo documento:** [Guía de Instalación](./INSTALACION_RHINOMETRIC_ONPREM.md)

---

**© 2025 Rhinometric - Arquitectura diseñada para observabilidad on-premise escalable**
