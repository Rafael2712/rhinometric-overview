# 🔀 Rhinometric Hybrid Architecture Guide
## On-Premise + Cloud Integration v2.1.0

**Versión**: 2.1.0  
**Fecha**: Octubre 2025  
**Autor**: Rafael Canel  
**Repositorio**: https://github.com/Rafael2712/rhinometric-overview

---

## 📋 Tabla de Contenidos

1. [¿Qué es Arquitectura Híbrida?](#qué-es-arquitectura-híbrida)
2. [Casos de Uso](#casos-de-uso)
3. [Modelo 1: Datos Local + Visualización Cloud](#modelo-1-datos-local--visualización-cloud)
4. [Modelo 2: Multi-Sede Federada](#modelo-2-multi-sede-federada)
5. [Modelo 3: Cloud Bursting](#modelo-3-cloud-bursting)
6. [Seguridad y Conectividad](#seguridad-y-conectividad)
7. [Costos y ROI](#costos-y-roi)
8. [Implementación Paso a Paso](#implementación-paso-a-paso)

---

## 🎯 ¿Qué es Arquitectura Híbrida?

Combinar lo mejor de ambos mundos:

- **On-Premise**: Control total, cumplimiento regulatorio, latencia baja
- **Cloud**: Escalabilidad, alta disponibilidad, disaster recovery

### Ventajas Híbrido

| Aspecto | On-Premise | Cloud | Híbrido |
|---------|------------|-------|---------|
| **Costo inicial** | Alto | Bajo | Medio |
| **Escalabilidad** | Limitada | Infinita | ✅ Flexible |
| **Cumplimiento** | ✅ GDPR/HIPAA | Variable | ✅ Datos local |
| **Disponibilidad** | 99.5% | 99.9% | ✅ 99.95% |
| **Mantenimiento** | Alto | Bajo | Medio |
| **Latencia** | ✅ < 1ms | 10-50ms | ✅ Mixta |

---

## 💼 Casos de Uso

### 1. Banca y Finanzas (PCI-DSS)

**Requisito**: Transacciones y datos sensibles NO pueden salir del país.

**Solución Híbrida**:
- **On-Premise**: PostgreSQL con transacciones, Redis cache
- **Cloud**: Dashboards ejecutivos, reportes, alertas

```
┌─────────────────────────────────┐
│  Data Center Banco (España)     │
│  ├── PostgreSQL (transacciones) │
│  ├── Redis (cache)              │
│  ├── Prometheus (métricas)      │
│  └── Remote Write ─────────┐    │
└─────────────────────────────┼───┘
                              │
                              │ TLS 1.3
                              ↓
┌─────────────────────────────────┐
│  Oracle Cloud (eu-madrid-1)     │
│  ├── Prometheus (agregador)     │
│  ├── Grafana (dashboards)       │
│  └── Acceso ejecutivos          │
└─────────────────────────────────┘
```

**Beneficios**:
- ✅ Cumple PCI-DSS (datos en España)
- ✅ Dashboards accesibles desde cualquier lugar
- ✅ Sin infraestructura adicional para visualización
- ✅ Backup automático en cloud

### 2. Healthcare (HIPAA)

**Requisito**: Historiales médicos protegidos (PHI).

**Solución Híbrida**:
- **On-Premise**: Base de datos pacientes
- **Cloud**: Analytics, ML, investigación (datos anonimizados)

```
Hospital Local                      Cloud (Investigación)
├── PostgreSQL (PHI)                ├── Prometheus (métricas)
├── Redis                           ├── Grafana
├── Prometheus                      └── ML Models
└── Anonimización ───────────────→  (datos sin PII)
```

### 3. Retail Multi-Sede

**Requisito**: 50 tiendas, dashboard centralizado.

**Solución Híbrida**:
- **On-Premise**: Cada tienda con stack completo
- **Cloud**: Dashboard CEO con todas las tiendas

```
Tienda Madrid       Tienda Barcelona    Tienda Valencia
├── Rhinometric ───┐ ├── Rhinometric ───┤ ├── Rhinometric ───┐
└── Inventario     │ └── Ventas         │ └── Logística      │
                   │                    │                    │
                   └────────────────────┴────────────────────┘
                                        │
                         Prometheus Federation
                                        ↓
                   ┌─────────────────────────────────────┐
                   │   Oracle Cloud (Dashboard CEO)      │
                   │   ├── Ventas totales: 50 tiendas    │
                   │   ├── Inventario consolidado        │
                   │   └── KPIs globales                 │
                   └─────────────────────────────────────┘
```

---

## 📊 Modelo 1: Datos Local + Visualización Cloud

### Arquitectura

```
┌───────────────────────────────────────────────────────┐
│              ON-PREMISE (Cliente)                      │
├───────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ PostgreSQL   │  │ Redis        │  │ Aplicaciones│ │
│  │ (datos)      │  │ (cache)      │  │ (APIs)      │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
│         │                 │                  │        │
│         └─────────────────┴──────────────────┘        │
│                           ↓                           │
│  ┌────────────────────────────────────────────────┐   │
│  │         Prometheus Agent (local)               │   │
│  │  - Scrape: postgres-exporter, redis-exporter  │   │
│  │  - Retention: 7 días local                    │   │
│  │  - Remote Write: Cloud                        │   │
│  └─────────────────────┬──────────────────────────┘   │
│                        │                              │
└────────────────────────┼──────────────────────────────┘
                         │
                         │ HTTPS + TLS 1.3
                         │ Remote Write API
                         ↓
┌───────────────────────────────────────────────────────┐
│              ORACLE CLOUD / AWS / AZURE                │
├───────────────────────────────────────────────────────┤
│                                                        │
│  ┌────────────────────────────────────────────────┐   │
│  │         Prometheus (agregador central)         │   │
│  │  - Recibe métricas de todas las sedes         │   │
│  │  - Retention: 90 días                         │   │
│  │  - Almacenamiento: Object Storage             │   │
│  └─────────────────────┬──────────────────────────┘   │
│                        │                              │
│  ┌────────────────────────────────────────────────┐   │
│  │         Grafana (visualización)                │   │
│  │  - Dashboards multi-tenant                    │   │
│  │  - Alertas centralizadas                      │   │
│  │  - Acceso HTTPS público                       │   │
│  └────────────────────────────────────────────────┘   │
│                                                        │
│  ┌────────────────────────────────────────────────┐   │
│  │         Loki + Tempo (opcional)                │   │
│  │  - Logs centralizados                         │   │
│  │  - Distributed tracing                        │   │
│  └────────────────────────────────────────────────┘   │
│                                                        │
└───────────────────────────────────────────────────────┘
```

### Implementación

#### 1. Setup On-Premise

**Archivo**: `docker-compose-hybrid-local.yml`

```yaml
version: '3.8'

services:
  # Base de datos local
  postgres:
    image: postgres:15
    container_name: rhinometric-postgres
    environment:
      POSTGRES_DB: rhinometric
      POSTGRES_USER: rhino
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - rhinometric-local
    restart: unless-stopped

  # Cache local
  redis:
    image: redis:7-alpine
    container_name: rhinometric-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - rhinometric-local
    restart: unless-stopped

  # Exporters
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: postgres-exporter
    environment:
      DATA_SOURCE_NAME: "postgresql://rhino:${POSTGRES_PASSWORD}@postgres:5432/rhinometric?sslmode=disable"
    networks:
      - rhinometric-local
    restart: unless-stopped

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: redis-exporter
    environment:
      REDIS_ADDR: "redis:6379"
      REDIS_PASSWORD: ${REDIS_PASSWORD}
    networks:
      - rhinometric-local
    restart: unless-stopped

  # Prometheus con Remote Write
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus-agent
    user: "0:0"
    volumes:
      - ./prometheus-hybrid.yml:/etc/prometheus/prometheus.yml:ro
      - ./certs:/etc/prometheus/certs:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=7d'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    networks:
      - rhinometric-local
    restart: unless-stopped

  # Grafana local (opcional, para desarrollo)
  grafana:
    image: grafana/grafana:latest
    container_name: grafana-local
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_INSTALL_PLUGINS: "grafana-piechart-panel"
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    networks:
      - rhinometric-local
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  rhinometric-local:
    driver: bridge
```

**Archivo**: `prometheus-hybrid.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    site: 'madrid-datacenter'
    environment: 'production'
    customer: 'acme-corp'

# Remote Write a Cloud
remote_write:
  - url: "https://prometheus.rhinometric-cloud.com/api/v1/write"
    basic_auth:
      username: "acme-corp"
      password_file: /etc/prometheus/certs/remote-write-password.txt
    
    # Configuración de cola
    queue_config:
      capacity: 10000
      max_shards: 10
      min_shards: 1
      max_samples_per_send: 1000
      batch_send_deadline: 5s
      min_backoff: 30ms
      max_backoff: 5s
    
    # TLS
    tls_config:
      cert_file: /etc/prometheus/certs/client.crt
      key_file: /etc/prometheus/certs/client.key
      ca_file: /etc/prometheus/certs/ca.crt
      insecure_skip_verify: false
    
    # Retry
    write_relabel_configs:
      # Solo enviar métricas importantes
      - source_labels: [__name__]
        regex: 'up|node_.*|postgres_.*|redis_.*|http_.*'
        action: keep

# Scrape local
scrape_configs:
  # PostgreSQL
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
        labels:
          service: 'database'
          db_type: 'postgresql'

  # Redis
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
        labels:
          service: 'cache'
          cache_type: 'redis'

  # Node Exporter (hardware)
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
        labels:
          service: 'infrastructure'

  # cAdvisor (containers)
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
        labels:
          service: 'containers'

# Reglas de alertas locales
rule_files:
  - "/etc/prometheus/alerts/*.yml"
```

#### 2. Setup Cloud (Receptor)

**Archivo**: `docker-compose-cloud.yml`

```yaml
version: '3.8'

services:
  # Prometheus Cloud (recibe remote_write)
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus-cloud
    volumes:
      - ./prometheus-cloud.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_cloud_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=90d'
      - '--web.enable-remote-write-receiver'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    networks:
      - rhinometric-cloud
    restart: unless-stopped

  # Grafana Cloud
  grafana:
    image: grafana/grafana:latest
    container_name: grafana-cloud
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_AUTH_ANONYMOUS_ENABLED: false
      GF_SERVER_ROOT_URL: https://grafana.rhinometric-cloud.com
      GF_INSTALL_PLUGINS: "grafana-piechart-panel,grafana-clock-panel"
    volumes:
      - grafana_cloud_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3000:3000"
    networks:
      - rhinometric-cloud
    restart: unless-stopped

  # Loki para logs (opcional)
  loki:
    image: grafana/loki:latest
    container_name: loki-cloud
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yaml
      - loki_data:/loki
    networks:
      - rhinometric-cloud
    restart: unless-stopped

  # Tempo para tracing (opcional)
  tempo:
    image: grafana/tempo:latest
    container_name: tempo-cloud
    ports:
      - "3200:3200"   # Tempo HTTP
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
    volumes:
      - ./tempo-config.yml:/etc/tempo/config.yml
      - tempo_data:/var/tempo
    networks:
      - rhinometric-cloud
    restart: unless-stopped

  # Nginx reverse proxy + SSL
  nginx:
    image: nginx:alpine
    container_name: nginx-cloud
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./html:/usr/share/nginx/html:ro
    ports:
      - "80:80"
      - "443:443"
    networks:
      - rhinometric-cloud
    restart: unless-stopped

volumes:
  prometheus_cloud_data:
  grafana_cloud_data:
  loki_data:
  tempo_data:

networks:
  rhinometric-cloud:
    driver: bridge
```

**Archivo**: `prometheus-cloud.yml`

```yaml
global:
  scrape_interval: 30s
  evaluation_interval: 30s
  external_labels:
    cluster: 'cloud-aggregator'
    environment: 'production'

# Habilitar recepción remote_write
# Ya está habilitado con --web.enable-remote-write-receiver

# Alertmanager
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

# Reglas de alertas
rule_files:
  - "/etc/prometheus/alerts/*.yml"

# Scrape propio monitoreo cloud
scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'grafana'
    static_configs:
      - targets: ['grafana:3000']
```

#### 3. Configurar TLS Certificates

```bash
# Generar CA
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt \
  -subj "/C=ES/ST=Madrid/L=Madrid/O=Rhinometric/CN=Rhinometric CA"

# Generar certificado cliente (on-premise)
openssl genrsa -out client.key 4096
openssl req -new -key client.key -out client.csr \
  -subj "/C=ES/ST=Madrid/L=Madrid/O=Rhinometric/CN=acme-corp"
openssl x509 -req -days 365 -in client.csr -CA ca.crt -CAkey ca.key \
  -set_serial 01 -out client.crt

# Copiar archivos
cp ca.crt client.crt client.key ~/mi-proyecto/certs/

# Permisos
chmod 600 ~/mi-proyecto/certs/client.key
```

#### 4. Deploy

```bash
# On-Premise
cd ~/on-premise
docker compose -f docker-compose-hybrid-local.yml up -d

# Cloud (Oracle/AWS/Azure)
cd ~/cloud
docker compose -f docker-compose-cloud.yml up -d
```

### Verificación

```bash
# 1. Check Prometheus local está enviando
curl http://localhost:9090/api/v1/status/config | jq '.data.yaml' | grep remote_write

# 2. Check métricas en cloud
curl https://prometheus.rhinometric-cloud.com/api/v1/label/__name__/values | jq

# 3. Query cross-site
curl -G https://prometheus.rhinometric-cloud.com/api/v1/query \
  --data-urlencode 'query=up{site="madrid-datacenter"}' | jq
```

---

## 🏢 Modelo 2: Multi-Sede Federada

### Arquitectura

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Sede Madrid     │  │  Sede Barcelona  │  │  Sede Valencia   │
│  (HQ Principal)  │  │  (Oficina 2)     │  │  (Oficina 3)     │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│ Stack Completo:  │  │ Stack Completo:  │  │ Stack Completo:  │
│ ├── PostgreSQL   │  │ ├── PostgreSQL   │  │ ├── PostgreSQL   │
│ ├── Redis        │  │ ├── Redis        │  │ ├── Redis        │
│ ├── Prometheus   │  │ ├── Prometheus   │  │ ├── Prometheus   │
│ ├── Grafana      │  │ ├── Grafana      │  │ ├── Grafana      │
│ ├── Loki         │  │ ├── Loki         │  │ ├── Loki         │
│ └── Tempo        │  │ └── Tempo        │  │ └── Tempo        │
│                  │  │                  │  │                  │
│ Federation: /federate endpoint          │                  │
│ http://madrid.local:9090/federate       │                  │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                   Prometheus Federation
                   (cada 60 segundos)
                               ↓
              ┌────────────────────────────────────────┐
              │   Oracle Cloud (Dashboard Central)     │
              ├────────────────────────────────────────┤
              │ Prometheus Federated:                  │
              │ ├── /federate de Madrid                │
              │ ├── /federate de Barcelona             │
              │ ├── /federate de Valencia              │
              │                                         │
              │ Grafana Multi-Tenant:                   │
              │ ├── Dashboard CEO (3 sedes)            │
              │ ├── Dashboard por sede                 │
              │ ├── Comparativas                       │
              │ └── KPIs consolidados                  │
              │                                         │
              │ Alertmanager:                           │
              │ └── Alertas centralizadas              │
              └────────────────────────────────────────┘
```

### Configuración Federation

**Prometheus Cloud** (`prometheus-federation.yml`):

```yaml
global:
  scrape_interval: 60s  # Más lento para federation
  evaluation_interval: 60s
  external_labels:
    cluster: 'cloud-federation'

scrape_configs:
  # Federar Sede Madrid
  - job_name: 'federate-madrid'
    scrape_interval: 60s
    scrape_timeout: 55s
    honor_labels: true
    metrics_path: '/federate'
    
    params:
      'match[]':
        # Métricas específicas importantes
        - '{job=~"postgres|redis|node"}'
        - '{__name__=~"up|http_.*|postgres_.*|redis_.*"}'
    
    static_configs:
      - targets:
          - 'madrid.rhinometric.local:9090'
        labels:
          site: 'madrid'
          region: 'centro'
    
    basic_auth:
      username: 'federation-user'
      password_file: /etc/prometheus/federation-password.txt

  # Federar Sede Barcelona
  - job_name: 'federate-barcelona'
    scrape_interval: 60s
    scrape_timeout: 55s
    honor_labels: true
    metrics_path: '/federate'
    
    params:
      'match[]':
        - '{job=~"postgres|redis|node"}'
        - '{__name__=~"up|http_.*|postgres_.*|redis_.*"}'
    
    static_configs:
      - targets:
          - 'barcelona.rhinometric.local:9090'
        labels:
          site: 'barcelona'
          region: 'cataluna'
    
    basic_auth:
      username: 'federation-user'
      password_file: /etc/prometheus/federation-password.txt

  # Federar Sede Valencia
  - job_name: 'federate-valencia'
    scrape_interval: 60s
    scrape_timeout: 55s
    honor_labels: true
    metrics_path: '/federate'
    
    params:
      'match[]':
        - '{job=~"postgres|redis|node"}'
        - '{__name__=~"up|http_.*|postgres_.*|redis_.*"}'
    
    static_configs:
      - targets:
          - 'valencia.rhinometric.local:9090'
        labels:
          site: 'valencia'
          region: 'comunidad-valenciana'
    
    basic_auth:
      username: 'federation-user'
      password_file: /etc/prometheus/federation-password.txt

# Alertas consolidadas
rule_files:
  - "/etc/prometheus/alerts/federation-alerts.yml"
```

**Alertas Federation** (`alerts/federation-alerts.yml`):

```yaml
groups:
  - name: multi-site-alerts
    interval: 60s
    rules:
      # Alerta si alguna sede está caída
      - alert: SiteDown
        expr: up{job=~"federate-.*"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Sede {{ $labels.site }} está DOWN"
          description: "La sede {{ $labels.site }} no responde desde hace 5 minutos"

      # Alerta si latencia alta en alguna sede
      - alert: HighLatency
        expr: |
          avg(rate(http_request_duration_seconds_sum[5m])) by (site) 
          / 
          avg(rate(http_request_duration_seconds_count[5m])) by (site) 
          > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Latencia alta en {{ $labels.site }}"
          description: "Latencia promedio: {{ $value }}s en {{ $labels.site }}"

      # Alerta comparativa de performance
      - alert: PerformanceDegradation
        expr: |
          (
            avg(rate(http_requests_total[5m])) by (site)
            /
            avg(avg_over_time(rate(http_requests_total[5m])[1h:5m])) by (site)
          ) < 0.7
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Performance degradada en {{ $labels.site }}"
          description: "Tráfico 30% menor al promedio horario"
```

### Dashboards Multi-Sede

**Dashboard CEO** (Grafana JSON):

```json
{
  "dashboard": {
    "title": "Rhinometric - Vista Consolidada CEO",
    "panels": [
      {
        "title": "Sedes Operativas",
        "type": "stat",
        "targets": [
          {
            "expr": "count(up{job=~\"federate-.*\"} == 1)",
            "legendFormat": "Sedes Online"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 2, "color": "yellow"},
                {"value": 3, "color": "green"}
              ]
            }
          }
        }
      },
      {
        "title": "Transacciones Totales (Todas las sedes)",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (site)",
            "legendFormat": "{{ site }}"
          }
        ]
      },
      {
        "title": "Latencia Promedio por Sede",
        "type": "graph",
        "targets": [
          {
            "expr": "avg(rate(http_request_duration_seconds_sum[5m])) by (site) / avg(rate(http_request_duration_seconds_count[5m])) by (site)",
            "legendFormat": "{{ site }}"
          }
        ]
      },
      {
        "title": "Top Sede por Performance",
        "type": "table",
        "targets": [
          {
            "expr": "topk(3, sum(rate(http_requests_total[5m])) by (site))",
            "format": "table"
          }
        ]
      }
    ]
  }
}
```

---

## ⚡ Modelo 3: Cloud Bursting

**Caso de uso**: Black Friday, campañas marketing, picos de tráfico.

### Arquitectura

```
NORMAL (100% On-Premise)
┌─────────────────────────────────┐
│   Data Center                   │
│   ├── 5 servidores              │
│   ├── PostgreSQL (HA)           │
│   ├── Redis Cluster             │
│   └── Prometheus/Grafana        │
│   Carga: 60% CPU                │
└─────────────────────────────────┘

PICO DE TRÁFICO (Híbrido)
┌─────────────────────────────────┐
│   Data Center                   │
│   ├── 5 servidores              │
│   └── Carga: 95% CPU ───────┐   │
└──────────────────────────────┼──┘
                               │
                    Auto-scaling trigger
                               ↓
                ┌──────────────────────────┐
                │   Oracle Cloud (burst)   │
                │   ├── +10 instancias     │
                │   ├── Load Balancer      │
                │   └── Auto-scaling       │
                │   Carga: maneja overflow │
                └──────────────────────────┘
```

### Implementación Kubernetes (K8s)

**HPA (Horizontal Pod Autoscaler)**:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rhinometric-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rhinometric-api
  minReplicas: 5   # On-premise baseline
  maxReplicas: 50  # Cloud burst max
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 60
        - type: Pods
          value: 10
          periodSeconds: 60
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
```

**Deployment multi-cloud**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rhinometric-api
  namespace: production
spec:
  replicas: 5
  selector:
    matchLabels:
      app: rhinometric-api
  template:
    metadata:
      labels:
        app: rhinometric-api
    spec:
      # Affinity: preferir on-premise
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              preference:
                matchExpressions:
                  - key: location
                    operator: In
                    values:
                      - on-premise
            - weight: 50
              preference:
                matchExpressions:
                  - key: location
                    operator: In
                    values:
                      - cloud
      
      containers:
        - name: api
          image: rhinometric/api:2.1.0
          ports:
            - containerPort: 8091
          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"
          env:
            - name: POSTGRES_HOST
              valueFrom:
                configMapKeyRef:
                  name: db-config
                  key: host
            - name: REDIS_HOST
              valueFrom:
                configMapKeyRef:
                  name: cache-config
                  key: host
```

---

## 🔒 Seguridad y Conectividad

### VPN WireGuard (On-Premise ↔ Cloud)

**Servidor WireGuard (Cloud)**:

```ini
# /etc/wireguard/wg0.conf
[Interface]
PrivateKey = <SERVER_PRIVATE_KEY>
Address = 10.100.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT

# Cliente On-Premise Madrid
[Peer]
PublicKey = <MADRID_PUBLIC_KEY>
AllowedIPs = 10.100.0.10/32
PersistentKeepalive = 25

# Cliente On-Premise Barcelona
[Peer]
PublicKey = <BARCELONA_PUBLIC_KEY>
AllowedIPs = 10.100.0.11/32
PersistentKeepalive = 25
```

**Cliente WireGuard (On-Premise)**:

```ini
# /etc/wireguard/wg0.conf
[Interface]
PrivateKey = <CLIENT_PRIVATE_KEY>
Address = 10.100.0.10/32
DNS = 8.8.8.8

[Peer]
PublicKey = <SERVER_PUBLIC_KEY>
Endpoint = cloud.rhinometric.com:51820
AllowedIPs = 10.100.0.0/24, 192.168.1.0/24
PersistentKeepalive = 25
```

### Firewall Rules

**On-Premise Firewall**:

```bash
# Permitir solo tráfico VPN
iptables -A INPUT -i wg0 -j ACCEPT
iptables -A OUTPUT -o wg0 -j ACCEPT

# Bloquear acceso directo a PostgreSQL desde internet
iptables -A INPUT -p tcp --dport 5432 ! -s 10.100.0.0/24 -j DROP

# Permitir Prometheus remote_write solo via VPN
iptables -A OUTPUT -p tcp --dport 9090 -d 10.100.0.1 -j ACCEPT
```

**Cloud Firewall** (Oracle Cloud Security List):

```hcl
# terraform/oracle-cloud/network.tf
resource "oci_core_security_list" "hybrid_security_list" {
  # ...

  # WireGuard VPN
  ingress_security_rules {
    protocol = "17" # UDP
    source   = "0.0.0.0/0"
    udp_options {
      min = 51820
      max = 51820
    }
    description = "WireGuard VPN"
  }

  # Prometheus remote_write (solo desde VPN)
  ingress_security_rules {
    protocol = "6" # TCP
    source   = "10.100.0.0/24"
    tcp_options {
      min = 9090
      max = 9090
    }
    description = "Prometheus remote write (VPN only)"
  }

  # Grafana (público HTTPS)
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 443
      max = 443
    }
    description = "Grafana HTTPS"
  }
}
```

---

## 💰 Costos y ROI

### Comparativa Costos (3 sedes, 50 empleados por sede)

| Escenario | Infraestructura | Costo Mensual | Costo Anual |
|-----------|-----------------|---------------|-------------|
| **100% On-Premise** | 3 servidores físicos + licencias | $2,500 | $30,000 |
| **100% Cloud** | Oracle Cloud Always Free | $0 | $0 |
| **100% Cloud** | AWS (3 instancias t3.medium) | $153 | $1,836 |
| **Híbrido (Modelo 1)** | On-premise + Oracle Free | $1,200 | $14,400 |
| **Híbrido (Modelo 2)** | 3 sedes + Oracle Cloud | $1,800 | $21,600 |
| **Cloud Bursting** | On-premise + burst AWS | $1,500 + $500 picos | $18,000 |

### ROI Arquitectura Híbrida

**Ejemplo: Empresa 150 empleados, 3 sedes**

| Métrica | On-Premise | Híbrido | Ahorro |
|---------|------------|---------|--------|
| **CAPEX inicial** | $50,000 | $15,000 | **70%** |
| **OPEX anual** | $30,000 | $18,000 | **40%** |
| **Downtime/año** | 8 horas | 2 horas | **75%** |
| **Costo downtime** | $40,000 | $10,000 | **$30,000** |
| **Total 3 años** | $140,000 | $69,000 | **$71,000** |

**ROI = (71,000 - 15,000) / 15,000 = 373% en 3 años**

---

## 🚀 Implementación Paso a Paso

### Día 1: Preparación

1. **Inventario**:
   ```bash
   # ¿Qué tienes on-premise?
   - Servidores: ___
   - Bases de datos: ___
   - Aplicaciones: ___
   - Sedes: ___
   ```

2. **Decisión arquitectura**:
   - ¿Modelo 1, 2 o 3?
   - ¿Qué proveedor cloud?
   - ¿VPN o internet público?

3. **Permisos**:
   - Acceso root on-premise
   - Cuenta cloud (Oracle/AWS/Azure)
   - Certificados SSL

### Día 2-3: Setup Cloud

```bash
# 1. Clonar repositorio
git clone https://github.com/Rafael2712/rhinometric-overview.git
cd rhinometric-overview

# 2. Deploy cloud (Oracle/AWS/Azure)
cd terraform/oracle-cloud  # o aws, azure
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars

terraform init
terraform plan
terraform apply -auto-approve

# 3. Verificar
curl http://<PUBLIC_IP>:3000/api/health
```

### Día 4-5: Setup On-Premise

```bash
# 1. Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. Configurar .env
cp .env.example .env
nano .env  # Editar passwords

# 3. Deploy híbrido
docker compose -f docker-compose-hybrid-local.yml up -d

# 4. Verificar
docker ps
curl http://localhost:9090/-/healthy
```

### Día 6-7: Conectividad

```bash
# 1. Generar certificados
./generate-certs.sh

# 2. Configurar VPN (opcional)
sudo apt install wireguard
sudo wg-quick up wg0

# 3. Test conectividad
ping 10.100.0.1  # Cloud
curl https://prometheus-cloud.com/api/v1/write

# 4. Verificar remote_write
curl http://localhost:9090/api/v1/status/config | grep remote_write
```

### Día 8-10: Testing

```bash
# 1. Generar tráfico
python trace-generator.py --interval=5

# 2. Verificar métricas en cloud
curl https://prometheus-cloud.com/api/v1/query?query=up

# 3. Dashboards Grafana
# Abrir: https://grafana-cloud.com:3000
# Usuario: admin
# Password: <GRAFANA_PASSWORD>
```

### Día 11-14: Producción

1. **Migración gradual**: 10% tráfico → Cloud
2. **Monitoreo**: Latencia, errors, throughput
3. **Ajustes**: Tunning Prometheus, Grafana
4. **Documentación**: Runbooks, escalación

---

## 📚 Recursos Adicionales

- **Código Terraform**: https://github.com/Rafael2712/mi-proyecto/tree/dev/terraform
- **Documentación**: https://github.com/Rafael2712/rhinometric-overview
- **Soporte**: https://github.com/Rafael2712/rhinometric-overview/issues

---

**Última actualización**: 28 de Octubre 2025  
**Versión**: 2.1.0  
**Autor**: Rafael Canel
