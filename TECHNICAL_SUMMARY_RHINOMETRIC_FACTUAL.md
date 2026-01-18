# RHINOMETRIC v2.5.0 "Rhino Radar"  
## Complete Technical Summary

**Date:** 17 de Diciembre, 2025  
**Version:** 2.5.0  
**Release Date:** 16 de Diciembre, 2025  
**Source:** docker-compose-v2.5.0.yml, docs/v2.5.0/RELEASE_NOTES.md, README.md

---

## General Architecture

Rhinometric v2.5.0 is a **multi-container** observability platform based on Docker Compose. All infrastructure is deployed as Docker services orchestrated in a private network.

### Docker Network
- **Name:** `rhinometric_network_v22`
- **Driver:** bridge
- **Isolation:** Services only accessible internally (except exposed ports)

---

## Service Inventory (Verified)

Based on `docker-compose-v2.5.0.yml`:

### 1. license-server-v2
- **Image:** Custom (build from `/home/ubuntu/license-server-v2`)
- **Language:** Python 3.11-slim
- **Framework:** FastAPI
- **Port:** 5000 (HTTP)
- **Resources:** No limits specified
- **Healthcheck:** `http://localhost:5000/api/health` every 30s
- **Environment variables:**
  ```
  DATABASE_URL=postgresql://rhinometric:password@postgres:5432/rhinometric_licenses
  REDIS_URL=redis://:password@redis:6379/0
  SMTP_HOST=smtp.zoho.eu
  SMTP_PORT=465
  SMTP_USER=rafael.canelon@rhinometric.com
  API_VERSION=2.5.0
  SERVER_BASE_URL=https://licensing.rhinometric.com:5000
  ```
- **Features:**
  - Gestión de licencias (CRUD)
  - Validación de licencias
  - Generación de archivos .lic
  - Envío de emails con HTML
  - Endpoints de descarga (OVA, instalador, PDFs)
  - API REST documentada (FastAPI auto-docs)

### 2. license-ui
- **Image:** Custom (build from `/home/ubuntu/license-ui`)
- **Technology:** Nginx + HTML/CSS/JavaScript
- **Port:** 8093
- **Resources:** No limits specified
- **Healthcheck:** `http://localhost:80/` every 30s
- **Function:** Interfaz web para crear/editar licencias manualmente

### 3. postgres
- **Image:** postgres:15.10-alpine
- **Port:** 5432
- **Resources:** 512 MB RAM (límite)
- **Healthcheck:** `pg_isready -U rhinometric` every 10s
- **Volume:** `rhinometric_postgres_data_v2:/var/lib/postgresql/data`
- **Databases:**
  - `rhinometric_licenses` (production)
  - Other application data
- **User:** rhinometric / (password in environment variables)

### 4. redis
- **Image:** redis:7.2-alpine
- **Port:** 6379
- **Resources:** 256 MB RAM (límite)
- **Healthcheck:** `redis-cli --no-auth-warning -a password ping` every 10s
- **Volume:** `rhinometric_redis_data_v2:/data`
- **Configuration:**
  - Password required
  - Eviction policy: LRU (allkeys-lru)
  - Persistence: RDB snapshots

### 5. prometheus
- **Image:** prom/prometheus:v2.53.0
- **Port:** 9090
- **Resources:** 1536 MB RAM (límite)
- **Healthcheck:** `http://localhost:9090/-/healthy` every 30s
- **Volumes:**
  - `rhinometric_prometheus_data_v2:/prometheus` (data)
  - `./prometheus.yml:/etc/prometheus/prometheus.yml:ro` (config)
- **Retention:** 30 días (according to flags)
- **Flags:**
  ```
  --config.file=/etc/prometheus/prometheus.yml
  --storage.tsdb.path=/prometheus
  --storage.tsdb.retention.time=30d
  --web.console.libraries=/etc/prometheus/console_libraries
  --web.console.templates=/etc/prometheus/consoles
  --web.enable-lifecycle
  ```
- **Scrape Targets:** Node Exporter, cAdvisor, Blackbox, PostgreSQL Exporter, License Server, otros servicios

### 6. loki
- **Image:** grafana/loki:3.0.0
- **Port:** 3100
- **Resources:** 1024 MB RAM (límite)
- **Healthcheck:** `http://localhost:3100/ready` every 30s
- **Volumes:**
  - `rhinometric_loki_data_v2:/loki` (data)
  - `./loki-config.yaml:/etc/loki/local-config.yaml:ro` (config)
- **Retention:** Configurada en loki-config.yaml
- **Ingesta:** Promtail (logs Docker), syslog

### 7. jaeger
- **Image:** jaegertracing/all-in-one:latest
- **Ports:**
  - 16686 (UI web)
  - 14317 (OTLP gRPC)
  - 14318 (OTLP HTTP)
  - 14268 (Jaeger HTTP)
  - 14250 (gRPC)
- **Resources:** No limits specified
- **Healthcheck:** `http://localhost:14269/` every 30s
- **Environment variables:**
  ```
  COLLECTOR_OTLP_ENABLED=true
  SPAN_STORAGE_TYPE=memory
  ```
- **Function:** Trazado distribuido de transacciones
- **Integration:** OpenTelemetry Collector envía traces

### 8. grafana
- **Image:** grafana/grafana:10.4.0
- **Port:** 3000
- **Resources:** 800 MB RAM (límite)
- **Healthcheck:** `http://localhost:3000/api/health` every 30s
- **Volumes:**
  - `rhinometric_grafana_data_v2:/var/lib/grafana` (data)
  - `./grafana/dashboards:/etc/grafana/provisioning/dashboards:ro`
  - `./grafana/datasources:/etc/grafana/provisioning/datasources:ro`
- **Environment variables:**
  ```
  GF_SECURITY_ADMIN_PASSWORD=rhinometric_v25
  GF_SERVER_ROOT_URL=http://localhost:3000
  GF_INSTALL_PLUGINS=grafana-clock-panel
  ```
- **Datasources precargados:**
  - Prometheus (metrics)
  - Loki (logs)
  - Jaeger (traces)
- **Dashboards:** 15+ pre-loaded dashboards

### 9. otel-collector
- **Image:** otel/opentelemetry-collector:0.91.0
- **Ports:**
  - 4317 (OTLP gRPC)
  - 4318 (OTLP HTTP)
  - 8888 (Prometheus metrics del collector)
  - 13133 (health check)
- **Resources:** No limits specified
- **Healthcheck:** `http://localhost:13133/` every 30s
- **Volume:** `./otel-collector-config.yaml:/etc/otel-collector-config.yaml:ro`
- **Function:**
  - Recibir traces OTLP
  - Exportar a Jaeger
  - Exportar metrics a Prometheus
  - Pipeline de procesamiento de telemetría

### 10. cadvisor
- **Image:** gcr.io/cadvisor/cadvisor:latest
- **Port:** 8080
- **Resources:** No limits specified
- **Healthcheck:** `http://localhost:8080/healthz` every 30s
- **Volumes:**
  - `/:/rootfs:ro`
  - `/var/run:/var/run:ro`
  - `/sys:/sys:ro`
  - `/var/lib/docker/:/var/lib/docker:ro`
- **Privileged:** true
- **Function:** Métricas de contenedores Docker (CPU, RAM, red, I/O)

### 11. node-exporter
- **Image:** prom/node-exporter:latest
- **Port:** 9100
- **Resources:** No limits specified
- **Healthcheck:** `http://localhost:9100/` every 30s
- **Volumes:**
  - `/proc:/host/proc:ro`
  - `/sys:/host/sys:ro`
  - `/:/rootfs:ro`
- **Flags:**
  ```
  --path.procfs=/host/proc
  --path.rootfs=/rootfs
  --path.sysfs=/host/sys
  --collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)
  ```
- **Function:** Métricas del sistema operativo host

### 12. blackbox-exporter
- **Image:** prom/blackbox-exporter:latest
- **Port:** 9115
- **Resources:** No limits specified
- **Healthcheck:** `http://localhost:9115/` every 30s
- **Volume:** `./blackbox.yml:/etc/blackbox_exporter/config.yml:ro`
- **Function:** Health checks HTTP/TCP de servicios

### 13. postgres-exporter
- **Image:** prometheuscommunity/postgres-exporter:latest
- **Port:** 9187
- **Resources:** No limits specified
- **Healthcheck:** `http://localhost:9187/` every 30s
- **Environment variables:**
  ```
  DATA_SOURCE_NAME=postgresql://rhinometric:password@postgres:5432/rhinometric_licenses?sslmode=disable
  ```
- **Function:** Métricas de PostgreSQL (conexiones, queries, locks)

### 14. console-v3
- **Image:** Custom (build from contexto con Dockerfile.console-v3)
- **Port:** 3002
- **Resources:** No limits specified
- **Healthcheck:** `http://localhost:3002/health` every 30s
- **Technology:** Vue.js (frontend) + FastAPI (backend)
- **Function:** Consola administrativa moderna

### 15. ai-anomaly-engine
- **Image:** Custom (build from contexto con Dockerfile.ai-anomaly)
- **Port:** 8085
- **Resources:** No limits specified
- **Healthcheck:** `http://localhost:8085/health` every 30s
- **Technology:** Python + Prophet + IsolationForest
- **Environment variables:**
  ```
  PROMETHEUS_URL=http://prometheus:9090
  DETECTION_INTERVAL=300
  ```
- **Function:** Detección de anomalies con machine learning

### Servicios Legacy (Estado Incierto)
Según análisis, puede haber servicios legacy adicionales no verificados en `docker-compose-v2.5.0.yml` actual.

---

## Platform Capabilities

### Metrics Collection
**Sources:**
- Operating system (Node Exporter)
- Docker containers (cAdvisor)
- Base de data (PostgreSQL Exporter)
- Applications (FastAPI endpoints /metrics)
- Health checks (Blackbox Exporter)

**Retention:**
- Prometheus: 30 días
- Loki: Configurado en loki-config.yaml
- Jaeger: En memoria (no persistente por defecto)

### Log Collection
**Sources:**
- Docker container logs (vía Promtail)
- System logs (varlog)

**Centralization:**
- Loki 3.0.0 as central store
- Query via Grafana Explore
- LogQL for queries

### Distributed Tracing
**Tool:** Jaeger (all-in-one)
**Supported protocols:**
- OTLP (OpenTelemetry Protocol) vía gRPC/HTTP
- Jaeger Thrift vía HTTP
- Zipkin (compatible)

**Pipeline:**
1. Applications envían traces → OpenTelemetry Collector
2. Collector processes and exports → Jaeger
3. Query via Jaeger UI (puerto 16686)
4. Integration with Grafana

### Dashboards and Visualization
**Grafana 10.4.0:**
- 15+ pre-loaded dashboards
- Datasources:
  - Prometheus (metrics)
  - Loki (logs)
  - Jaeger (traces)
- Dynamic dashboard variables
- Alert panels

**Documented dashboards:**
- System overview
- Docker Containers
- Prometheus Metrics
- Loki Logs
- Jaeger Traces
- (Complete list in provisioning files)

### Anomaly Detection
**AI Anomaly Engine:**
- **Algorithms:** Prophet (forecasting) + IsolationForest (anomalies)
- **Fuente de data:** Prometheus metrics
- **Interval:** Configurable (default 300s = 5 min)
- **Output:** Métricas de anomalies → Prometheus → Dashboards

**Use cases:**
- CPU spike prediction
- Abnormal behavior detection
- Proactive alerts

### Sistema de Licencias
**License Server v2:**
- **Technology:** FastAPI (migrado desde Flask)
- **Performance:** 10x más rápido que v1 (según release notes)
- **Endpoints REST:**
  - `POST /api/admin/licenses` - Crear licencia
  - `GET /api/admin/licenses` - Listar licencias
  - `GET /api/admin/licenses/{key}` - Obtener licencia
  - `PUT /api/admin/licenses/{key}` - Actualizar licencia
  - `DELETE /api/admin/licenses/{key}` - Eliminar licencia
  - `POST /api/licenses/validate` - Validar licencia
  - `POST /api/licenses/activate` - Activar licencia
  - `GET /api/health` - Health check

**Tipos de licencia:**
- `demo_cloud` - 4 horas
- `trial` - 14 días, 5 hosts
- `annual_standard` - 1 año, hosts configurables
- `enterprise` - Personalizable

**Almacenamiento:**
- PostgreSQL (tabla `licenses`)
- Redis (caché de validaciones)

**Email System:**
- **Proveedor:** Zoho SMTP (smtp.zoho.eu:465)
- **Templates:** HTML con estilos inline
- **Contenido:** Información de licencia, enlaces de descarga, manuales
- **Attachments:** Archivos .lic (binarios firmados)

### Endpoints de Descarga
Según `DOWNLOAD_ENDPOINTS.md`:
- `GET /downloads/demo-ova` - Descarga OVA (streaming, ~3 GB)
- `GET /downloads/trial-installer` - Descarga script Linux (~50 KB)
- `GET /docs/installation-guide?lang=es|en` - Manual instalación PDF
- `GET /docs/user-manual?lang=es|en` - Manual usuario PDF
- `GET /downloads/info` - Metadata de todos los archivos (JSON)

---

## Persistence de Datos

### Volúmenes Docker
Según `docker-compose-v2.5.0.yml`:
- `rhinometric_postgres_data_v2` - PostgreSQL
- `rhinometric_redis_data_v2` - Redis
- `rhinometric_prometheus_data_v2` - Métricas de Prometheus
- `rhinometric_loki_data_v2` - Logs de Loki
- `rhinometric_grafana_data_v2` - Configuración de Grafana

**Backup:** Según `PENDIENTES_DESARROLLO_RHINOMETRIC.md`, backup automático está en roadmap (prioridad crítica).

---

## Security

### Autenticación
- Grafana: `admin / rhinometric_v25`
- PostgreSQL: `rhinometric / password` (variable de entorno)
- Redis: Password requerido (variable de entorno)

### Red Privada
- Servicios en red bridge privada
- Solo puertos necesarios expuestos al host
- Sin acceso directo entre servicios no relacionados

### Datos
- PostgreSQL con password
- Redis con requirepass
- Variables sensibles en archivos .env (no commiteados según .gitignore)

**Pendiente (según documentación):**
- HTTPS/TLS para todos los servicios
- Certificados SSL
- Enterprise SSO (SAML, OAuth) - roadmap 2026

---

## Deployment Requirements

### Sistema Operativo
- Ubuntu 20.04/22.04 LTS
- Debian 11/12
- CentOS 7/8
- RHEL 7/8

### Software Necesario
- Docker Engine 24+
- Docker Compose 2.0+
- Mínimo 20 GB espacio libre

### Puertos Requeridos
Based on `docker-compose-v2.5.0.yml`:
- 3000 - Grafana
- 3002 - Console v3
- 3100 - Loki
- 4317 - OTLP gRPC
- 4318 - OTLP HTTP
- 5000 - License Server
- 8080 - cAdvisor
- 8085 - AI Anomaly Engine
- 8093 - License UI
- 9090 - Prometheus
- 9100 - Node Exporter
- 9115 - Blackbox Exporter
- 9187 - PostgreSQL Exporter
- 16686 - Jaeger UI

---

## Capacity Analysis

### Servidor Actual (Producción)
Según archivos de análisis:
- **Proveedor:** AWS Lightsail
- **IP:** 54.197.192.198
- **RAM:** 914 MB disponible
- **CPU:** 2 vCPUs
- **Disco:** 40 GB
- **Uso:** Actualmente se utiliza en entornos reales de prueba y producción interna. Las cifras concretas de licencias/hosts se gestionan fuera de esta documentación técnica

### Estimación de Capacidad
Based on límites de recursos en `docker-compose-v2.5.0.yml`:

**Servicios con límites de RAM:**
- postgres: 512 MB
- redis: 256 MB
- prometheus: 1536 MB
- loki: 1024 MB
- grafana: 800 MB

**Total RAM asignada:** ~4.1 GB solo en servicios limitados

**Otros servicios sin límite:** +2-3 GB estimados

**Total estimado:** 6-7 GB RAM para stack completo

**Conclusión:** Para ejecutar el stack completo con margen razonable, se recomienda un mínimo de 8 GB de RAM y 4 vCPUs.

El número máximo de hosts soportados dependerá del patrón de uso y de las metrics recolectadas; actualmente no existe una cifra oficial de capacidad por hosts en la documentación, pero el diseño está pensado para empezar en escenarios de 10-30 hosts con esa configuración.

### Recomendaciones de Escalado (Estimaciones)
- **10-30 hosts:** 8 GB RAM, 4 vCPUs, 50 GB disco
- **30-100 hosts:** 16 GB RAM, 8 vCPUs, 100 GB disco
- **100-500 hosts:** 32 GB RAM, 16 vCPUs, 250 GB disco, considerar replicación de PostgreSQL

---

## Development Roadmap

Según `PENDIENTES_DESARROLLO_RHINOMETRIC.md`:

### Prioridad Crítica (2 semanas)
- ❌ Corregir enlaces del email annual
- ❌ Implementar backup automático de PostgreSQL
- ❌ Migrar stack legacy y eliminar containers crasheando

### Prioridad Alta (4 semanas)
- ❌ Monitoreo completo (ya parcialmente implementado)
- ❌ Notificaciones automáticas de expiración
- ❌ Portal de cliente self-service
- ❌ Sistema de facturación integrado (Stripe)

### Prioridad Media (2-3 meses)
- ❌ API pública documentada (Swagger existe, falta publicación)
- ❌ Alertas inteligentes y webhooks
- ❌ Multi-región (EU datacenter)
- ❌ Mobile app (iOS + Android)
- ❌ Kubernetes monitoring nativo

### Prioridad Baja (6+ meses)
- ❌ White-label solution
- ❌ Enterprise SSO (SAML, OAuth)
- ❌ Cloud cost optimization
- ❌ Compliance automation (SOC 2, ISO 27001)
- ❌ On-premise installer air-gapped
- ❌ Multi-tenancy completo

**Total estimado:** ~900 horas de desarrollo (~22-26 semanas con 1 developer)

---

## Breaking Changes since v2.1.0

Según `RELEASE_NOTES.md` v2.5.0:

1. **License Server migrado a FastAPI** (era Flask)
   - Nueva estructura de endpoints
   - Cambios en validación de licencias

2. **Console v3 reemplaza Console v2**
   - Nueva UI en Vue.js
   - API backend separado

3. **Jaeger reemplaza a Tempo** (en algunas versiones intermedias)
   - Endpoints de traces cambiados
   - OTLP ahora es protocolo principal

4. **PostgreSQL schema actualizado**
   - Nuevas columnas en tabla `licenses`
   - Migración automática en startup

---

## Installation

### Método 1: Docker Compose (Manual)
```bash
# Clonar repositorio
git clone https://github.com/rhinometric/rhinometric.git
cd rhinometric

# Configurar variables
cp .env.example .env
nano .env  # Editar credenciales

# Levantar stack
docker compose -f docker-compose-v2.5.0.yml up -d

# Verificar
docker compose ps
```

### Método 2: Trial Installer (Automatizado)
```bash
# Descargar instalador
curl -O https://licensing.rhinometric.com:5000/downloads/trial-installer

# Ejecutar
chmod +x rhinometric-trial-2.5.0-install.sh
sudo ./rhinometric-trial-2.5.0-install.sh

# Esperar 2-3 minutos
# Acceder a http://localhost:3000 (Grafana)
```

### Método 3: Demo OVA (VirtualBox)
```bash
# Descargar OVA
curl -O https://licensing.rhinometric.com:5000/downloads/demo-ova

# Importar en VirtualBox
# Iniciar VM
# Acceder a http://<IP-VM>:3000
```

---

## Post-Installation Verification

### Health Checks
```bash
# Todos los servicios
docker compose ps

# License Server
curl http://localhost:5000/api/health

# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3000/api/health

# Jaeger
curl http://localhost:14269/
```

### Validación de Datos
```bash
# Métricas en Prometheus
curl http://localhost:9090/api/v1/query?query=up

# Logs en Loki
curl http://localhost:3100/ready

# Trazas en Jaeger
curl http://localhost:16686/api/services
```

---

## Troubleshooting

### Containers restarting
```bash
# Ver logs
docker logs rhinometric-license-server-v2

# Verificar recursos
docker stats

# Reiniciar servicio específico
docker compose restart prometheus
```

### No hay metrics en Grafana
```bash
# Verificar datasources
curl http://localhost:3000/api/datasources

# Verificar targets en Prometheus
curl http://localhost:9090/api/v1/targets

# Verificar scrape config
cat prometheus.yml
```

### No hay logs en Loki
```bash
# Verificar Promtail
docker logs rhinometric-promtail

# Query directo a Loki
curl -G -s "http://localhost:3100/loki/api/v1/query" --data-urlencode 'query={job="varlogs"}'
```

---

## Additional Documentation

### Archivos de Referencia
- `docker-compose-v2.5.0.yml` - Configuración completa
- `docs/v2.5.0/RELEASE_NOTES.md` - Changelog de v2.5.0
- `docs/v2.5.0/DEPLOYMENT_CHECKLIST.md` - Checklist de deployment
- `docs/v2.5.0/DOWNLOAD_ENDPOINTS.md` - Guía de endpoints de descarga
- `docs/v2.5.0/EMAIL_TESTING.md` - Testing del sistema de emails
- `PENDIENTES_DESARROLLO_RHINOMETRIC.md` - Roadmap de desarrollo

---

**Document generated from verifiable repository files.**  
**Last update:** 17 de Diciembre, 2025  
**Document version:** 1.0
