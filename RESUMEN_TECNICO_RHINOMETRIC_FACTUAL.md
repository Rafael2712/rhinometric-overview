# RHINOMETRIC v2.5.0 "Rhino Radar"  
## Resumen Técnico Completo

**Fecha:** 17 de Diciembre, 2025  
**Versión:** 2.5.0  
**Release Date:** 16 de Diciembre, 2025  
**Fuente:** docker-compose-v2.5.0.yml, docs/v2.5.0/RELEASE_NOTES.md, README.md

---

## Arquitectura General

Rhinometric v2.5.0 es una plataforma de observabilidad **multi-contenedor** basada en Docker Compose. Toda la infraestructura se despliega como servicios Docker orquestados en una red privada.

### Red Docker
- **Nombre:** `rhinometric_network_v22`
- **Driver:** bridge
- **Aislamiento:** Servicios solo accesibles internamente (excepto puertos expuestos)

---

## Inventario de Servicios (Verificado)

Basado en `docker-compose-v2.5.0.yml`:

### 1. license-server-v2
- **Imagen:** Custom (build desde `/home/ubuntu/license-server-v2`)
- **Lenguaje:** Python 3.11-slim
- **Framework:** FastAPI
- **Puerto:** 5000 (HTTP)
- **Recursos:** Sin límites especificados
- **Healthcheck:** `http://localhost:5000/api/health` cada 30s
- **Variables de entorno:**
  ```
  DATABASE_URL=postgresql://rhinometric:password@postgres:5432/rhinometric_licenses
  REDIS_URL=redis://:password@redis:6379/0
  SMTP_HOST=smtp.zoho.eu
  SMTP_PORT=465
  SMTP_USER=rafael.canelon@rhinometric.com
  API_VERSION=2.5.0
  SERVER_BASE_URL=https://licensing.rhinometric.com:5000
  ```
- **Funcionalidades:**
  - Gestión de licencias (CRUD)
  - Validación de licencias
  - Generación de archivos .lic
  - Envío de emails con HTML
  - Endpoints de descarga (OVA, instalador, PDFs)
  - API REST documentada (FastAPI auto-docs)

### 2. license-ui
- **Imagen:** Custom (build desde `/home/ubuntu/license-ui`)
- **Tecnología:** Nginx + HTML/CSS/JavaScript
- **Puerto:** 8093
- **Recursos:** Sin límites especificados
- **Healthcheck:** `http://localhost:80/` cada 30s
- **Función:** Interfaz web para crear/editar licencias manualmente

### 3. postgres
- **Imagen:** postgres:15.10-alpine
- **Puerto:** 5432
- **Recursos:** 512 MB RAM (límite)
- **Healthcheck:** `pg_isready -U rhinometric` cada 10s
- **Volumen:** `rhinometric_postgres_data_v2:/var/lib/postgresql/data`
- **Bases de datos:**
  - `rhinometric_licenses` (producción)
  - Otros datos de aplicación
- **Usuario:** rhinometric / (password en variables de entorno)

### 4. redis
- **Imagen:** redis:7.2-alpine
- **Puerto:** 6379
- **Recursos:** 256 MB RAM (límite)
- **Healthcheck:** `redis-cli --no-auth-warning -a password ping` cada 10s
- **Volumen:** `rhinometric_redis_data_v2:/data`
- **Configuración:**
  - Contraseña requerida
  - Política de evicción: LRU (allkeys-lru)
  - Persistencia: RDB snapshots

### 5. prometheus
- **Imagen:** prom/prometheus:v2.53.0
- **Puerto:** 9090
- **Recursos:** 1536 MB RAM (límite)
- **Healthcheck:** `http://localhost:9090/-/healthy` cada 30s
- **Volúmenes:**
  - `rhinometric_prometheus_data_v2:/prometheus` (datos)
  - `./prometheus.yml:/etc/prometheus/prometheus.yml:ro` (config)
- **Retención:** 30 días (según flags)
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
- **Imagen:** grafana/loki:3.0.0
- **Puerto:** 3100
- **Recursos:** 1024 MB RAM (límite)
- **Healthcheck:** `http://localhost:3100/ready` cada 30s
- **Volúmenes:**
  - `rhinometric_loki_data_v2:/loki` (datos)
  - `./loki-config.yaml:/etc/loki/local-config.yaml:ro` (config)
- **Retención:** Configurada en loki-config.yaml
- **Ingesta:** Promtail (logs Docker), syslog

### 7. jaeger
- **Imagen:** jaegertracing/all-in-one:latest
- **Puertos:**
  - 16686 (UI web)
  - 14317 (OTLP gRPC)
  - 14318 (OTLP HTTP)
  - 14268 (Jaeger HTTP)
  - 14250 (gRPC)
- **Recursos:** Sin límites especificados
- **Healthcheck:** `http://localhost:14269/` cada 30s
- **Variables de entorno:**
  ```
  COLLECTOR_OTLP_ENABLED=true
  SPAN_STORAGE_TYPE=memory
  ```
- **Función:** Trazado distribuido de transacciones
- **Integración:** OpenTelemetry Collector envía trazas

### 8. grafana
- **Imagen:** grafana/grafana:10.4.0
- **Puerto:** 3000
- **Recursos:** 800 MB RAM (límite)
- **Healthcheck:** `http://localhost:3000/api/health` cada 30s
- **Volúmenes:**
  - `rhinometric_grafana_data_v2:/var/lib/grafana` (datos)
  - `./grafana/dashboards:/etc/grafana/provisioning/dashboards:ro`
  - `./grafana/datasources:/etc/grafana/provisioning/datasources:ro`
- **Variables de entorno:**
  ```
  GF_SECURITY_ADMIN_PASSWORD=rhinometric_v25
  GF_SERVER_ROOT_URL=http://localhost:3000
  GF_INSTALL_PLUGINS=grafana-clock-panel
  ```
- **Datasources precargados:**
  - Prometheus (métricas)
  - Loki (logs)
  - Jaeger (trazas)
- **Dashboards:** 15+ dashboards precargados

### 9. otel-collector
- **Imagen:** otel/opentelemetry-collector:0.91.0
- **Puertos:**
  - 4317 (OTLP gRPC)
  - 4318 (OTLP HTTP)
  - 8888 (Prometheus métricas del collector)
  - 13133 (health check)
- **Recursos:** Sin límites especificados
- **Healthcheck:** `http://localhost:13133/` cada 30s
- **Volumen:** `./otel-collector-config.yaml:/etc/otel-collector-config.yaml:ro`
- **Función:**
  - Recibir trazas OTLP
  - Exportar a Jaeger
  - Exportar métricas a Prometheus
  - Pipeline de procesamiento de telemetría

### 10. cadvisor
- **Imagen:** gcr.io/cadvisor/cadvisor:latest
- **Puerto:** 8080
- **Recursos:** Sin límites especificados
- **Healthcheck:** `http://localhost:8080/healthz` cada 30s
- **Volúmenes:**
  - `/:/rootfs:ro`
  - `/var/run:/var/run:ro`
  - `/sys:/sys:ro`
  - `/var/lib/docker/:/var/lib/docker:ro`
- **Privileged:** true
- **Función:** Métricas de contenedores Docker (CPU, RAM, red, I/O)

### 11. node-exporter
- **Imagen:** prom/node-exporter:latest
- **Puerto:** 9100
- **Recursos:** Sin límites especificados
- **Healthcheck:** `http://localhost:9100/` cada 30s
- **Volúmenes:**
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
- **Función:** Métricas del sistema operativo host

### 12. blackbox-exporter
- **Imagen:** prom/blackbox-exporter:latest
- **Puerto:** 9115
- **Recursos:** Sin límites especificados
- **Healthcheck:** `http://localhost:9115/` cada 30s
- **Volumen:** `./blackbox.yml:/etc/blackbox_exporter/config.yml:ro`
- **Función:** Health checks HTTP/TCP de servicios

### 13. postgres-exporter
- **Imagen:** prometheuscommunity/postgres-exporter:latest
- **Puerto:** 9187
- **Recursos:** Sin límites especificados
- **Healthcheck:** `http://localhost:9187/` cada 30s
- **Variables de entorno:**
  ```
  DATA_SOURCE_NAME=postgresql://rhinometric:password@postgres:5432/rhinometric_licenses?sslmode=disable
  ```
- **Función:** Métricas de PostgreSQL (conexiones, queries, locks)

### 14. console-v3
- **Imagen:** Custom (build desde contexto con Dockerfile.console-v3)
- **Puerto:** 3002
- **Recursos:** Sin límites especificados
- **Healthcheck:** `http://localhost:3002/health` cada 30s
- **Tecnología:** Vue.js (frontend) + FastAPI (backend)
- **Función:** Consola administrativa moderna

### 15. ai-anomaly-engine
- **Imagen:** Custom (build desde contexto con Dockerfile.ai-anomaly)
- **Puerto:** 8085
- **Recursos:** Sin límites especificados
- **Healthcheck:** `http://localhost:8085/health` cada 30s
- **Tecnología:** Python + Prophet + IsolationForest
- **Variables de entorno:**
  ```
  PROMETHEUS_URL=http://prometheus:9090
  DETECTION_INTERVAL=300
  ```
- **Función:** Detección de anomalías con machine learning

### Servicios Legacy (Estado Incierto)
Según análisis, puede haber servicios legacy adicionales no verificados en `docker-compose-v2.5.0.yml` actual.

---

## Capacidades de la Plataforma

### Recolección de Métricas
**Fuentes:**
- Sistema operativo (Node Exporter)
- Contenedores Docker (cAdvisor)
- Base de datos (PostgreSQL Exporter)
- Aplicaciones (FastAPI endpoints /metrics)
- Health checks (Blackbox Exporter)

**Retención:**
- Prometheus: 30 días
- Loki: Configurado en loki-config.yaml
- Jaeger: En memoria (no persistente por defecto)

### Recolección de Logs
**Fuentes:**
- Logs de contenedores Docker (vía Promtail)
- Logs del sistema (varlog)

**Centralización:**
- Loki 3.0.0 como almacén central
- Consulta vía Grafana Explore
- LogQL para queries

### Trazado Distribuido
**Herramienta:** Jaeger (all-in-one)
**Protocolos soportados:**
- OTLP (OpenTelemetry Protocol) vía gRPC/HTTP
- Jaeger Thrift vía HTTP
- Zipkin (compatible)

**Pipeline:**
1. Aplicaciones envían trazas → OpenTelemetry Collector
2. Collector procesa y exporta → Jaeger
3. Consulta vía Jaeger UI (puerto 16686)
4. Integración con Grafana

### Dashboards y Visualización
**Grafana 10.4.0:**
- 15+ dashboards precargados
- Datasources:
  - Prometheus (métricas)
  - Loki (logs)
  - Jaeger (trazas)
- Variables de dashboard dinámicas
- Paneles de alertas

**Dashboards documentados:**
- Overview del sistema
- Docker Containers
- Prometheus Metrics
- Loki Logs
- Jaeger Traces
- (Lista completa en archivos de provisioning)

### Detección de Anomalías
**AI Anomaly Engine:**
- **Algoritmos:** Prophet (forecasting) + IsolationForest (anomalías)
- **Fuente de datos:** Prometheus metrics
- **Intervalo:** Configurable (default 300s = 5 min)
- **Salida:** Métricas de anomalías → Prometheus → Dashboards

**Casos de uso:**
- Predicción de picos de CPU
- Detección de comportamiento anormal
- Alertas proactivas

### Sistema de Licencias
**License Server v2:**
- **Tecnología:** FastAPI (migrado desde Flask)
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

## Persistencia de Datos

### Volúmenes Docker
Según `docker-compose-v2.5.0.yml`:
- `rhinometric_postgres_data_v2` - PostgreSQL
- `rhinometric_redis_data_v2` - Redis
- `rhinometric_prometheus_data_v2` - Métricas de Prometheus
- `rhinometric_loki_data_v2` - Logs de Loki
- `rhinometric_grafana_data_v2` - Configuración de Grafana

**Backup:** Según `PENDIENTES_DESARROLLO_RHINOMETRIC.md`, backup automático está en roadmap (prioridad crítica).

---

## Seguridad

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

## Requisitos de Deployment

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
Basado en `docker-compose-v2.5.0.yml`:
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

## Análisis de Capacidad

### Servidor Actual (Producción)
Según archivos de análisis:
- **Proveedor:** AWS Lightsail
- **IP:** 54.197.192.198
- **RAM:** 914 MB disponible
- **CPU:** 2 vCPUs
- **Disco:** 40 GB
- **Uso:** Actualmente se utiliza en entornos reales de prueba y producción interna. Las cifras concretas de licencias/hosts se gestionan fuera de esta documentación técnica

### Estimación de Capacidad
Basado en límites de recursos en `docker-compose-v2.5.0.yml`:

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

El número máximo de hosts soportados dependerá del patrón de uso y de las métricas recolectadas; actualmente no existe una cifra oficial de capacidad por hosts en la documentación, pero el diseño está pensado para empezar en escenarios de 10-30 hosts con esa configuración.

### Recomendaciones de Escalado (Estimaciones)
- **10-30 hosts:** 8 GB RAM, 4 vCPUs, 50 GB disco
- **30-100 hosts:** 16 GB RAM, 8 vCPUs, 100 GB disco
- **100-500 hosts:** 32 GB RAM, 16 vCPUs, 250 GB disco, considerar replicación de PostgreSQL

---

## Roadmap de Desarrollo

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

## Breaking Changes desde v2.1.0

Según `RELEASE_NOTES.md` v2.5.0:

1. **License Server migrado a FastAPI** (era Flask)
   - Nueva estructura de endpoints
   - Cambios en validación de licencias

2. **Console v3 reemplaza Console v2**
   - Nueva UI en Vue.js
   - API backend separado

3. **Jaeger reemplaza a Tempo** (en algunas versiones intermedias)
   - Endpoints de trazas cambiados
   - OTLP ahora es protocolo principal

4. **PostgreSQL schema actualizado**
   - Nuevas columnas en tabla `licenses`
   - Migración automática en startup

---

## Instalación

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

## Verificación Post-Instalación

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

### No hay métricas en Grafana
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

## Documentación Adicional

### Archivos de Referencia
- `docker-compose-v2.5.0.yml` - Configuración completa
- `docs/v2.5.0/RELEASE_NOTES.md` - Changelog de v2.5.0
- `docs/v2.5.0/DEPLOYMENT_CHECKLIST.md` - Checklist de deployment
- `docs/v2.5.0/DOWNLOAD_ENDPOINTS.md` - Guía de endpoints de descarga
- `docs/v2.5.0/EMAIL_TESTING.md` - Testing del sistema de emails
- `PENDIENTES_DESARROLLO_RHINOMETRIC.md` - Roadmap de desarrollo

---

**Documento generado a partir de archivos verificables del repositorio.**  
**Última actualización:** 17 de Diciembre, 2025  
**Versión del documento:** 1.0
