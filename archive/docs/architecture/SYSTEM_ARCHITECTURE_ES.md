# ���️ Arquitectura del Sistema - Rhinometric Enterprise v2.5.0

**Versión**: 2.5.0  
**Fecha**: Noviembre 2024  
**Idioma**: Español

---

## ��� Vista General

**Rhinometric Enterprise** es una plataforma de observabilidad que proporciona:
- Monitoreo unificado (métricas, logs, trazas)
- Detección proactiva con IA
- Visualización rica con dashboards
- Alertas inteligentes multi-canal

---

## ���️ Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────┐
│                CAPA DE PRESENTACIÓN                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Grafana  │  │ Landing  │  │Dashboard │          │
│  │   3000   │  │   Page   │  │ Builder  │          │
│  └─────┬────┘  └──────────┘  └─────┬────┘          │
└────────┼───────────────────────────┼────────────────┘
         │                           │
┌────────┼───────────────────────────┼────────────────┐
│        │      CAPA DE APLICACIÓN   │                │
│  ┌─────▼────┐  ┌──────────┐  ┌────▼─────┐          │
│  │Prometheus│  │Alertmgr  │  │ Node.js  │          │
│  │   9090   │  │   9093   │  │   API    │          │
│  └─────┬────┘  └──────────┘  └──────────┘          │
│  ┌─────▼────┐  ┌──────────┐  ┌──────────┐          │
│  │   Loki   │  │  Tempo   │  │AI Engine │          │
│  │   3100   │  │   3200   │  │   8001   │          │
│  └──────────┘  └──────────┘  └──────────┘          │
└─────────────────────────────────────────────────────┘
         │
┌────────┼─────────────────────────────────────────────┐
│        │         CAPA DE DATOS                       │
│  ┌─────▼────┐  ┌──────────┐  ┌──────────┐          │
│  │PostgreSQL│  │  Redis   │  │Filesystem│          │
│  │   5432   │  │   6379   │  │ Storage  │          │
│  └──────────┘  └──────────┘  └──────────┘          │
└─────────────────────────────────────────────────────┘
```

---

## ��� Componentes del Sistema

### 1. Grafana (Visualización)
**Puerto**: 3000  
**Función**: Interfaz principal para dashboards y consultas

**Características**:
- Dashboards interactivos
- Explorador de métricas/logs/trazas
- Gestión de alertas
- Control de acceso (RBAC)

**Base de Datos**: PostgreSQL

### 2. Prometheus (Métricas)
**Puerto**: 9090  
**Función**: Recolección y almacenamiento de métricas

**Características**:
- Scraping cada 15 segundos
- TSDB optimizado
- PromQL para consultas
- Retención: 15 días (configurable)

**Targets Monitoreados**:
- Node Exporter (métricas OS)
- Postgres Exporter (DB)
- Nginx Exporter (web server)
- cAdvisor (containers)

### 3. Loki (Logs)
**Puerto**: 3100  
**Función**: Agregación de logs

**Características**:
- Indexación solo de etiquetas
- Compresión eficiente
- Compatible con Grafana
- LogQL para queries

**Agente**: Promtail

### 4. Tempo (Trazas)
**Puerto**: 3200  
**Función**: Trazas distribuidas

**Características**:
- OpenTelemetry compatible
- Búsqueda por trace ID
- Visualización waterfall
- Bajo overhead (<1%)

### 5. PostgreSQL (Base de Datos)
**Puerto**: 5432  
**Función**: Almacenamiento persistente

**Datos**:
- Usuarios y permisos
- Dashboards (JSON)
- Configuración de alertas
- Licencias

### 6. Redis (Cache)
**Puerto**: 6379  
**Función**: Cache y sesiones

**Uso**:
- Cache de queries
- Sesiones de usuario
- Rate limiting

### 7. Node.js API (Backend)
**Puerto**: 5000  
**Función**: API REST

**Endpoints**:
- Dashboard Builder
- License Server
- Custom services

### 8. Python AI Engine (IA)
**Puerto**: 8001  
**Función**: Detección de anomalías

**Algoritmos**:
- Isolation Forest
- ARIMA
- Z-Score

---

## ��� Flujo de Datos

### Métricas
```
Server → Node Exporter → Prometheus → Grafana → Usuario
```

### Logs
```
App → Promtail → Loki → Grafana → Usuario
```

### Trazas
```
App → OTEL Collector → Tempo → Grafana → Usuario
```

---

## ��� Despliegue

### Docker Compose (Single Node)

```yaml
services:
  grafana:
    image: grafana/grafana:10.2.0
    ports: ["3000:3000"]
    
  prometheus:
    image: prom/prometheus:v2.48.0
    ports: ["9090:9090"]
    
  loki:
    image: grafana/loki:2.9.0
    ports: ["3100:3100"]
    
  postgres:
    image: postgres:16
    
  redis:
    image: redis:7-alpine
```

### Kubernetes (Multi-Node)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:10.2.0
```

---

## ��� Alta Disponibilidad

### Arquitectura HA

```
        ┌─────────┐
        │ HAProxy │ (Load Balancer)
        └────┬────┘
             │
    ┌────────┼────────┐
    │        │        │
┌───▼──┐ ┌──▼───┐ ┌──▼───┐
│Grafana│Grafana│Grafana│
│ Node1 │ Node2 │ Node3 │
└───┬──┘ └──┬───┘ └──┬───┘
    └────┬──┴──┬─────┘
         │     │
    ┌────▼─────▼────┐
    │ PostgreSQL HA │
    │ Master+Replicas│
    └────────────────┘
```

**Componentes HA**:
- HAProxy: Load balancer con health checks
- Grafana: 3+ nodos sin estado
- PostgreSQL: Master + réplicas (Patroni)
- Prometheus: Federation

**SLA**: 99.9% uptime (Enterprise)

---

## ��� Seguridad

### TLS/SSL
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /certs/cert.pem;
    ssl_certificate_key /certs/key.pem;
}
```

### Autenticación
- LDAP/Active Directory
- OAuth 2.0
- SAML
- API Keys

### RBAC
- Viewer: Solo lectura
- Editor: Crear/editar dashboards
- Admin: Acceso completo

---

## ��� Escalabilidad

| Hosts | Configuración Recomendada |
|-------|---------------------------|
| 1-10 | Docker Compose: 4 CPU, 8GB RAM |
| 10-50 | Docker Compose: 8 CPU, 16GB RAM |
| 50-200 | Kubernetes 3 nodos |
| 200+ | Kubernetes + Prometheus Federation |

---

## ��� Monitoreo del Monitoreo

### Métricas Clave
```promql
# Prometheus ingest rate
rate(prometheus_tsdb_head_samples_appended_total[5m])

# Grafana requests/s
rate(grafana_http_request_duration_seconds_count[5m])

# Loki ingest rate
rate(loki_distributor_lines_received_total[5m])
```

---

## ��� Disaster Recovery

### Backup
```bash
# PostgreSQL
pg_dump rhinometric | gzip > backup.sql.gz

# Prometheus (opcional)
tar czf prometheus.tar.gz /prometheus/data

# Grafana dashboards
grafana-cli admin export-dashboards /tmp/backup
```

### Restore
```bash
gunzip < backup.sql.gz | psql rhinometric
docker compose restart
```

---

## ��� Contacto Técnico

- Email: info@rhinometric.com
- Docs: https://docs.rhinometric.com/architecture
- GitHub: https://github.com/Rafael2712/rhinometric-overview

---

**Documento**: Arquitectura del Sistema  
**Versión**: 2.5.0  
**Actualización**: Noviembre 2024
