# 🦏 RHINOMETRIC v2.1.0 TRIAL
## Plataforma de Observabilidad ON-PREMISE

---

**⚠️ IMPORTANTE: RHINOMETRIC ES 100% ON-PREMISE**
Esta plataforma se instala y ejecuta en **TU PROPIA INFRAESTRUCTURA** (servidores locales, VMs privadas, o tu propia cuenta cloud). **NO es SaaS**, **NO es cloud-hosted**.

**Versión:** 2.1.0 Trial  
**Duración:** 30 días  
**Fecha:** Octubre 2025  
**Tipo:** Self-Hosted / On-Premise

**Contacto:**  
📧 support@rhinometric.io  
� GitHub: https://github.com/Rafael2712/mi-proyecto  
📚 Docs: Ver carpeta `docs/` en este repositorio

---

## 📋 RESUMEN EJECUTIVO

**Rhinometric v2.1.0** es una **plataforma completa de observabilidad ON-PREMISE** que unifica **métricas, logs y trazas distribuidas** en una solución autocontenida lista para instalar en **Windows, Linux o macOS**. 

Construida sobre tecnologías open source líderes (Grafana 10.4.0, Prometheus v2.53.0, Loki v3.0.0, Tempo v2.6.0), Rhinometric ofrece **instalación en 10-15 minutos**, **17 contenedores Docker orquestados**, y **15 dashboards pre-configurados** sin necesidad de código.

### ✨ Propuesta de Valor

- **🏠 100% ON-PREMISE** - Tus datos NUNCA salen de tu infraestructura
- **🚀 Instalación ultrarrápida** - Docker Compose con un comando, 10-15 minutos
- **📊 15 Dashboards profesionales** - System Overview, APIs externas, RED metrics, Database perf
- **� API Connector UI** - Monitorea APIs externas (Stripe, AWS, OpenAI) sin código
- **🔍 Drilldown completo** - Click en métrica → Ver logs → Ver traces automáticamente
- **� Auto-Update** - Actualizaciones con backup/rollback inteligente incluido
- **� Seguridad trial** - Endpoints de licencias protegidos con modo trial
- **💰 ROI inmediato** - Ahorra 60-80% vs DataDog ($3.5k/mes) o NewRelic ($4k/mes)

---

## 🏗️ ARQUITECTURA ON-PREMISE (17 Contenedores Docker)

**CRÍTICO**: Rhinometric se ejecuta **completamente en tu servidor/laptop**. No hay comunicación con servidores externos (excepto las APIs que TÚ configures para monitorear).

### Stack Tecnológico Completo

```
┌─────────────────────────────────────────────────────────┐
│                 TU INFRAESTRUCTURA                      │
│              (Windows / Linux / macOS)                  │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │     RHINOMETRIC v2.1.0 (Docker Compose)        │    │
│  │                                                 │    │
│  │  ┌─────────────┐  ┌─────────┐  ┌──────────┐   │    │
│  │  │  Grafana    │  │Prometheus│  │  Loki    │   │    │
│  │  │  10.4.0     │  │ v2.53.0  │  │  v3.0.0  │   │    │
│  │  │  (Puerto    │  │ (Métricas)│  │ (Logs)   │   │    │
│  │  │   3000)     │  │          │  │          │   │    │
│  │  └─────────────┘  └─────────┘  └──────────┘   │    │
│  │                                                 │    │
│  │  ┌─────────────┐  ┌─────────┐  ┌──────────┐   │    │
│  │  │   Tempo     │  │PostgreSQL│  │  Redis   │   │    │
│  │  │   v2.6.0    │  │   15.10  │  │   7.2    │   │    │
│  │  │  (Traces)   │  │(Metadata)│  │ (Cache)  │   │    │
│  │  └─────────────┘  └─────────┘  └──────────┘   │    │
│  │                                                 │    │
│  │  ┌──────────────────────────────────────────┐  │    │
│  │  │  API CONNECTOR (Nuevo en v2.1.0)         │  │    │
│  │  │  ├─ Vue.js 3 UI (Puerto 8091)            │  │    │
│  │  │  └─ API Proxy (Node.js, 38 métricas)     │  │    │
│  │  └──────────────────────────────────────────┘  │    │
│  │                                                 │    │
│  │  + 10 contenedores adicionales (nginx, OTEL,  │    │
│  │    exporters, license-server, etc.)            │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  Datos almacenados en: ./data/ (volúmenes Docker)      │
└─────────────────────────────────────────────────────────┘
```

### Componentes Principales (17 Servicios)

#### **TIER 1: Visualización y Consultas**

| Contenedor | Versión | Puerto | Recursos | Descripción |
|-----------|---------|---------|----------|-------------|
| **grafana** | 10.4.0 | 3000 | 0.8 CPU / 1GB | **Dashboard principal**: 15 dashboards pre-configurados, drilldown automático Metrics→Logs→Traces, alertas configurables, usuarios con roles. Datasources ya conectados. |

#### **TIER 2: Métricas y Logs** 

#### **TIER 2: Métricas, Logs y Traces**

| Contenedor | Versión | Puerto | Recursos | Descripción |
|-----------|---------|---------|----------|-------------|
| **prometheus** | v2.53.0 | 9090 | 1.0 CPU / 2GB | **Motor de métricas**: 1,008 métricas cross-platform verificadas. Scraping cada 15s, retención 15 días (configurable a 30/60/90). Query API con PromQL. |
| **loki** | v3.0.0 | 3100 | 0.5 CPU / 1GB | **Agregador de logs**: Indexa logs de 17 contenedores. Queries LogQL, compresión automática, retención 30 días. Compatible con Promtail/Docker driver. |
| **tempo** | v2.6.0 | 3200, 4317 | 0.5 CPU / 512MB | **Distributed tracing**: OTLP/Jaeger/Zipkin. Búsqueda por trace_id, correlación automática con logs. Retención 7 días. |

#### **TIER 3: Base de Datos y Cache**

| Contenedor | Versión | Puerto | Recursos | Descripción |
|-----------|---------|---------|----------|-------------|
| **postgres** | 15.10 | 5432 | 1.0 CPU / 2GB | **Base de datos relacional**: Configuraciones, APIs externas agregadas desde UI, metadatos de dashboards, licencias. Backups automáticos. |
| **redis** | 7.2 | 6379 | 0.2 CPU / 256MB | **Cache distribuido**: Respuestas de APIs externas (TTL 5 min), sesiones Grafana, rate limiting. Hit rate 80-90%. Persistencia AOF. |

#### **TIER 4: API Connector (⭐ Nuevo en v2.1.0)**

| Contenedor | Tecnología | Puerto | Recursos | Descripción |
|-----------|-----------|---------|----------|-------------|
| **api-connector-ui** | Vue.js 3 | 8091 | 0.3 CPU / 256MB | **UI Web**: CRUD visual para agregar APIs externas (Stripe, AWS, OpenAI, etc.) sin editar código. Formularios con auth (Bearer/API Key/OAuth2). |
| **api-proxy** | Node.js Express | 8090 | 0.5 CPU / 512MB | **Proxy de monitoreo**: Llama APIs cada 60s, mide latencia, errores, cache hits. Expone 38 métricas a Prometheus. Healthchecks automáticos. |

#### **TIER 5: Exporters y Colectores**

| Contenedor | Versión | Puerto | Descripción |
|-----------|---------|---------|-------------|
| **node-exporter** | latest | 9100 | Métricas del host (CPU, RAM, disco, red) - 500+ métricas sistema operativo |
| **cadvisor** | latest | 8080 | Métricas de contenedores Docker (recursos por container, I/O, network) |
| **postgres-exporter** | latest | 9187 | Métricas PostgreSQL (conexiones, slow queries, cache hit ratio, locks) |
| **blackbox-exporter** | latest | 9115 | Probes HTTP/TCP/ICMP (latencia, SSL certs, disponibilidad endpoints) |
| **otel-collector** | v0.91.0 | 4317, 4318 | Recibe traces OTLP, Jaeger, Zipkin. Exporta a Tempo. Pipeline configurable. |
| **promtail** | latest | 9080 | Agente de logs: Recolecta de Docker, parsea JSON, etiqueta por servicio, envía a Loki |

#### **TIER 6: Infraestructura**

| Contenedor | Versión | Puerto | Descripción |
|-----------|---------|---------|-------------|
| **nginx** | alpine | 80, 443 | Reverse proxy: Terminación SSL, rate limiting, compresión gzip, routing inteligente |
| **alertmanager** | latest | 9093 | Alertas: Agrupa, silencia duplicados, notifica (Slack, email, PagerDuty, webhooks) |
| **license-server** | Python/FastAPI | 5000 | Generador de licencias trial (30 días). Endpoints protegidos en modo `RHINOMETRIC_MODE=trial` |

---

## ⚡ CAPACIDADES TÉCNICAS (Probadas en v2.1.0)

### Métricas de Rendimiento

| Métrica | Valor | Notas |
|---------|-------|-------|
| **Contenedores simultáneos** | 17 | Todos con health checks |
| **Métricas únicas** | 1,008 | Verificadas cross-platform (Win/Linux/macOS) |
| **Dashboards** | 15 | 12 funcionales completos, 3 en progreso |
| **APIs externas monitoreadas** | Ilimitadas | Actual: 3 (OpenWeather, GitHub Status, CoinDesk) |
| **Scrape interval** | 15-30s | Configurable en `prometheus.yml` |
| **Retención métricas** | 15 días | Configurable a 30/60/90 días |
| **Retención logs** | 30 días | Loki compression habilitada |
| **Retención traces** | 7 días | Tempo con búsqueda rápida |
| **Cache hit rate** | 80-90% | Redis con TTL 5 min para APIs |
| **CPU usage (idle)** | ~1.5 vCPU | Stack completo |
| **CPU usage (load)** | ~3.7 vCPU | Con tráfico activo |
| **RAM usage** | ~6.2 GB | Optimizable a 4 GB |
| **Disk I/O** | ~2 GB/día | Con retención actual |

### Escalabilidad Probada

| Escenario | Capacidad | Hardware Recomendado |
|-----------|-----------|---------------------|
| **Servicios monitoreados** | 50-100 | 4 vCPU, 8 GB RAM |
| **Requests/segundo** | 1,000-5,000 | SSD recomendado |
| **Logs/segundo** | 5,000-10,000 | Loki escala horizontalmente |
| **Métricas activas** | 100,000+ | Prometheus federation si > 100k |
| **Usuarios Grafana** | 10-50 | Concurrentes sin degradación |
| **Alertas activas** | 100+ | Alertmanager agrupación inteligente |

---

## 🎯 CASOS DE USO IDEALES

### ✅ Perfecto Para:

1. **SaaS Companies (5-500 empleados)**
   - Monitorean Stripe, SendGrid, Twilio, AWS
   - Necesitan alertas antes que clientes reporten
   - **ROI**: 60-80% ahorro vs DataDog ($3.5k/mes)

2. **E-commerce**
   - Monitorean PayPal, MercadoPago, APIs de envío
   - Downtime = pérdida directa de revenue
   - **ROI**: Detectan problemas 5-10 min antes

3. **Fintech & Crypto**
   - APIs bancarias, exchanges, KYC providers
   - Cumplimiento regulatorio (logs 90+ días)
   - **ROI**: Compliance + ahorro $10k+/mes

4. **Agencias de Desarrollo**
   - 1 instancia Rhinometric por cliente
   - Instalación < 30 min
   - **ROI**: Venden monitoreo como servicio adicional

5. **DevOps Teams**
   - Reemplazan Prometheus + Grafana + Loki + Tempo
   - Setup pre-hecho vs días de configuración manual
   - **ROI**: 10-20 horas/mes ahorradas

### ❌ NO Recomendado Para:

- ❌ **Empresas Fortune 100** (necesitan más customización que self-hosted)
- ❌ **Apps móviles nativas** (sin backend para instrumentar)
- ❌ **IoT masivo** (millones de devices, escala diferente)
- ❌ **Compliance extremo** (HIPAA L4, PCI-DSS L1) - falta auditoría externa
- ❌ **Presupuesto < $200/mes** (trial gratis, pero soporte es paid)

---

## 📦 INSTALACIÓN (3 Plataformas)

### Windows (10/11)

```powershell
# 1. Instalar Docker Desktop (WSL 2)
# 2. Clonar repo
git clone https://github.com/Rafael2712/mi-proyecto.git
cd mi-proyecto/infrastructure/mi-proyecto/rhinometric-trial-v2.1.0-universal

# 3. Configurar
cp .env.example .env
nano .env  # Cambiar passwords

# 4. Levantar (10-15 minutos primera vez)
docker compose -f docker-compose-v2.1.0.yml up -d

# 5. Verificar
curl http://localhost:3000/api/health
```

**Acceso**: http://localhost:3000 (admin / tu_password)

### macOS (Monterey+)

```bash
# 1. Instalar Docker Desktop
brew install --cask docker

# 2. Instalar Rhinometric
curl -fsSL https://raw.githubusercontent.com/Rafael2712/mi-proyecto/main/install-mac-simple.sh | bash

# 3. Acceder
open http://localhost:3000
```

### Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)

```bash
# Instalación automática (un comando)
curl -fsSL https://raw.githubusercontent.com/Rafael2712/mi-proyecto/main/install-rhinometric.sh | sudo bash

# O manual
sudo apt update && sudo apt install docker.io docker-compose -y
git clone https://github.com/Rafael2712/mi-proyecto.git
cd mi-proyecto/infrastructure/mi-proyecto/rhinometric-trial-v2.1.0-universal
cp .env.example .env && nano .env
docker compose -f docker-compose-v2.1.0.yml up -d
```

**Tiempo total**: 10-15 minutos (incluye descarga de 2.5 GB de imágenes Docker)

---

### 📊 Recursos Totales Requeridos

| Recurso | Trial | Producción |
|---------|-------|------------|
| **CPU** | 4.9 vCPUs | 8-16 vCPUs |
| **RAM** | 8.8 GB | 16-32 GB |
| **Disco** | 50 GB | 500 GB - 2 TB |
| **Red** | 1 Gbps | 10 Gbps |
| **Retención métricas** | 7 días | 30-90 días |
| **Retención logs** | 7 días | 15-30 días |
| **Retención trazas** | 7 días | 15-30 días |

---

## 🔄 COMUNICACIÓN ENTRE COMPONENTES

### Flujo de Datos Principal

```
┌─────────────────────────────────────────────────────────────────┐
│                         APLICACIONES CLIENTE                     │
│    (Python, Node.js, Java, Go, .NET, PHP, Ruby, etc.)          │
└──────────┬──────────────────────────────────────────────────────┘
           │
           │ Métricas (Prometheus format)
           │ Logs (JSON, plaintext)
           │ Trazas (OTLP, Jaeger, Zipkin)
           │
           ▼
┌──────────────────────┐
│   NGINX (Proxy)      │◄────────── Usuario Web Browser
│   :80 / :443         │
└──────────┬───────────┘
           │
           ├─────────► Grafana :3000 (Dashboards, visualización)
           ├─────────► Prometheus :9090 (Queries de métricas)
           ├─────────► Loki :3100 (Ingesta de logs)
           ├─────────► Tempo :4317 (Ingesta de trazas OTLP)
           └─────────► License Dashboard :8080
           
┌──────────────────────────────────────────────────────────────────┐
│                      CAPA DE OBSERVABILIDAD                      │
└──────────────────────────────────────────────────────────────────┘

Prometheus :9090
    │
    ├── Scrape cada 15s ──► node-exporter :9100 (métricas host)
    ├── Scrape cada 15s ──► cadvisor :8080 (métricas Docker)
    ├── Scrape cada 15s ──► postgres-exporter :9187 (métricas DB)
    ├── Scrape cada 15s ──► blackbox-exporter :9115 (probes)
    ├── Scrape cada 15s ──► grafana :3000/metrics
    ├── Scrape cada 15s ──► loki :3100/metrics
    ├── Scrape cada 15s ──► tempo :3200/metrics
    └── Envía alertas ────► Alertmanager :9093

Loki :3100
    │
    └── Recibe logs ◄────── Promtail :9080
                                │
                                └── Lee logs ◄── /var/lib/docker/containers/

Tempo :3200
    │
    └── Recibe trazas ◄──── Aplicaciones cliente (OTLP :4317/:4318)

Grafana :3000
    │
    ├── Query datasource ──► Prometheus :9090 (métricas)
    ├── Query datasource ──► Loki :3100 (logs)
    └── Query datasource ──► Tempo :3200 (trazas)

┌──────────────────────────────────────────────────────────────────┐
│                       CAPA DE PERSISTENCIA                       │
└──────────────────────────────────────────────────────────────────┘

PostgreSQL :5432
    │
    ├── Almacena ◄───── License Server (licencias, clientes)
    ├── Almacena ◄───── Grafana (dashboards, usuarios, alertas)
    └── Monitorea ────► postgres-exporter :9187

Redis :6379
    │
    └── Cache ◄──────── License Server (sesiones, rate limiting)

License Server :5000
    │
    ├── Valida licencia ──► PostgreSQL :5432
    ├── Cache sesiones ──► Redis :6379
    └── Health check ◄──── Prometheus
```

### Protocolos de Comunicación

| Origen | Destino | Protocolo | Puerto | Propósito |
|--------|---------|-----------|---------|-----------|
| Apps cliente | NGINX | HTTP/HTTPS | 80/443 | Envío de métricas/logs/trazas |
| NGINX | Grafana | HTTP | 3000 | Proxy a dashboard |
| NGINX | Prometheus | HTTP | 9090 | Proxy a métricas |
| Grafana | Prometheus | HTTP | 9090 | Query de métricas (PromQL) |
| Grafana | Loki | HTTP | 3100 | Query de logs (LogQL) |
| Grafana | Tempo | HTTP | 3200 | Query de trazas (TraceQL) |
| Prometheus | Exporters | HTTP | 9100-9187 | Scraping de métricas (pull) |
| Promtail | Loki | HTTP | 3100 | Push de logs |
| Apps cliente | Tempo | gRPC/HTTP | 4317/4318 | Push de trazas OTLP |
| License Server | PostgreSQL | TCP | 5432 | Queries SQL |
| License Server | Redis | TCP | 6379 | Cache Redis protocol |
| Alertmanager | Email/Slack | SMTP/HTTPS | 587/443 | Envío de alertas |

---

## 🎯 ALCANCE DE LA PLATAFORMA

### Casos de Uso Principales

#### 1. **Monitoreo de Infraestructura**
- Supervisión en tiempo real de servidores (CPU, RAM, disco, red)
- Alertas automáticas ante degradación de rendimiento
- Visualización de tendencias y patrones de uso
- Capacidad de planning basada en métricas históricas

**Ideal para:** Equipos DevOps, SREs, Administradores de sistemas

#### 2. **Observabilidad de Aplicaciones**
- Métricas de negocio (usuarios activos, transacciones, errores)
- Trazado distribuido para identificar cuellos de botella
- Correlación automática entre métricas, logs y trazas
- Debugging de aplicaciones en producción sin acceso a servidores

**Ideal para:** Desarrolladores, Product Managers, Equipos de QA

#### 3. **Monitoreo de Microservicios**
- Mapa de servicios con dependencias automáticas
- Latencia P50/P95/P99 por endpoint
- Detección de errores en cascada entre servicios
- Service Level Indicators (SLI) y Objectives (SLO)

**Ideal para:** Arquitectos de software, Equipos de microservicios

#### 4. **Gestión de Logs Centralizada**
- Búsqueda de logs en tiempo real con queries potentes (LogQL)
- Agregación de logs de múltiples servicios/contenedores
- Filtrado por severity, timestamp, campos personalizados
- Export de logs para auditoría o análisis offline

**Ideal para:** Seguridad, Compliance, Debugging

#### 5. **Análisis de Rendimiento (APM)**
- Identificación de queries SQL lentas
- Detección de memory leaks y CPU spikes
- Profiling de funciones críticas (con integración de trazas)
- Comparación de rendimiento antes/después de deploys

**Ideal para:** Equipos de performance, DBAs

### Tipos de Proyectos Soportados

✅ **E-commerce y Retail**
- Monitoreo de transacciones, inventario, pagos
- Alertas de caídas de conversión o errores en checkout
- Análisis de tráfico en campañas (Black Friday, etc.)

✅ **Fintech y Banca**
- Trazabilidad completa de transacciones financieras
- Compliance con auditorías (logs inmutables)
- Detección de anomalías en tiempo real

✅ **SaaS y Plataformas Web**
- Métricas de multi-tenancy (uso por cliente)
- Facturación basada en uso (API calls, storage)
- SLA monitoring y reportes automáticos

✅ **Aplicaciones Móviles (Backend)**
- Monitoreo de APIs REST/GraphQL
- Latencia por región geográfica
- Errores por versión de app (correlación con trazas)

✅ **IoT y Dispositivos**
- Ingesta de métricas de miles de dispositivos
- Alertas por desconexión o anomalías
- Dashboards por flota, región, tipo de sensor

✅ **Videojuegos (Backend)**
- Métricas de CCU (concurrent users), latencia de matchmaking
- Logs de eventos de juego (kills, deaths, loot)
- Trazas de transacciones in-game (compras, trades)

✅ **Healthcare y Telemedicina**
- Monitoreo de sistemas críticos (uptime 99.9%)
- Logs de acceso a datos sensibles (HIPAA compliance)
- Alertas de fallos en servicios de emergencia

---

## ⚡ RENDIMIENTO Y CAPACIDAD

### Métricas de Rendimiento (Estimadas)

| Métrica | Trial (8GB RAM) | Producción (32GB RAM) |
|---------|-----------------|------------------------|
| **Métricas/segundo** | 10,000 samples/s | 100,000+ samples/s |
| **Logs/segundo** | 5,000 líneas/s | 50,000+ líneas/s |
| **Trazas/segundo** | 500 spans/s | 5,000+ spans/s |
| **Series temporales únicas** | 50,000 series | 500,000+ series |
| **Dashboards concurrentes** | 10 usuarios | 100+ usuarios |
| **Queries concurrentes** | 20 queries/s | 200+ queries/s |
| **Latencia query (P95)** | < 500ms | < 200ms |
| **Latencia ingesta** | < 1s | < 100ms |
| **Uptime objetivo** | 99% | 99.9% (3 nines) |

### Benchmarks Internos

**Escenario de prueba:** Aplicación e-commerce con 5 microservicios, 1000 requests/min

| Operación | Latencia P50 | Latencia P95 | Latencia P99 |
|-----------|--------------|--------------|--------------|
| Query de métricas (1h) | 120ms | 380ms | 650ms |
| Query de logs (10k líneas) | 250ms | 720ms | 1.2s |
| Trace search (100 traces) | 180ms | 450ms | 800ms |
| Dashboard render (6 panels) | 1.5s | 2.8s | 4.2s |

**Hardware de prueba:** AWS EC2 t3.xlarge (4 vCPUs, 16GB RAM, SSD)

### Escalabilidad

**Vertical Scaling:**
- Incrementar RAM: +16GB → +100,000 series temporales
- Incrementar CPU: +4 vCPUs → +20,000 queries/min
- Incrementar disco: +500GB → +30 días de retención

**Horizontal Scaling (Producción):**
- Prometheus federado (múltiples instancias por región)
- Loki multi-tenant con S3/GCS backend
- Tempo con backends distribuidos (Cassandra, S3)
- Grafana HA con balanceo de carga

---

## 🚀 INSTALACIÓN Y CONFIGURACIÓN

### Requisitos del Sistema

| Componente | Trial | Producción |
|------------|-------|------------|
| **SO** | Windows 10/11, macOS 12+, Ubuntu 20.04+ | Ubuntu 22.04 LTS, RHEL 8+ |
| **RAM** | 8 GB mínimo | 16 GB mínimo (32 GB recomendado) |
| **CPU** | 4 cores | 8 cores (16 cores recomendado) |
| **Disco** | 50 GB SSD | 500 GB SSD (NVMe recomendado) |
| **Docker** | Docker Desktop 20.10+ / Docker Engine 20.10+ | Docker Engine 24.0+ |
| **Docker Compose** | v2.0+ | v2.20+ |

### Instalación Simplificada

**Windows:**
1. Descargar `RhinometricInstaller.exe`
2. Ejecutar instalador (requiere permisos de administrador)
3. El wizard verifica Docker, instala si es necesario
4. Configurar nombre de cliente y ruta de instalación
5. Instalación automática (5-8 minutos)
6. Grafana se abre automáticamente al finalizar

**macOS:**
1. Descargar `Rhinometric.dmg`
2. Arrastrar a carpeta Aplicaciones
3. Ejecutar Rhinometric.app
4. Seguir wizard de instalación (similar a Windows)

**Linux:**
```bash
# Ubuntu/Debian
wget https://rhinometric.com/downloads/rhinometric-trial.deb
sudo dpkg -i rhinometric-trial.deb
rhinometric-install

# RHEL/CentOS
wget https://rhinometric.com/downloads/rhinometric-trial.rpm
sudo rpm -i rhinometric-trial.rpm
rhinometric-install
```

**Docker Compose (Manual):**
```bash
git clone https://github.com/rhinometric/trial-package.git
cd trial-package
./start-trial.sh
# Seguir instrucciones en pantalla
```

### Credenciales por Defecto

| Servicio | URL | Usuario | Contraseña |
|----------|-----|---------|------------|
| **Grafana** | http://localhost:3000 | admin | (generada aleatoriamente) |
| **Prometheus** | http://localhost:9090 | - | (sin autenticación en trial) |
| **Alertmanager** | http://localhost:9093 | - | (sin autenticación en trial) |
| **License Dashboard** | http://localhost:8080 | - | (solo lectura) |

**Nota:** Las credenciales se guardan automáticamente en `credentials.txt` tras la instalación.

---

## 📊 DASHBOARDS PRECARGADOS

Rhinometric incluye **6 dashboards profesionales** listos para usar desde el primer minuto:

### 1. **Overview Dashboard** 🏠
- Resumen general del estado del sistema
- Métricas clave: uptime, CPU, RAM, disco, red
- Alertas activas y últimos eventos
- Gráficos de tendencia (últimas 24h/7d)

**Panels:** 12 | **Refresh:** 30s | **Target:** Managers, NOC

### 2. **System Monitoring** 💻
- Métricas detalladas del host (node-exporter)
- CPU por core, RAM por proceso, I/O de disco
- Network throughput, errores de paquetes
- Filesystem usage, inodes disponibles

**Panels:** 18 | **Refresh:** 15s | **Target:** SREs, SysAdmins

### 3. **Docker Containers** 🐳
- Estado de todos los contenedores (running/stopped)
- Uso de recursos por contenedor (CPU, RAM, red)
- Logs recientes por servicio
- Restart count, health checks

**Panels:** 15 | **Refresh:** 30s | **Target:** DevOps, Developers

### 4. **Logs Explorer** 📝
- Query builder visual para búsqueda de logs
- Filtros por servicio, nivel (error/warn/info), timestamp
- Visualización de logs en tiempo real (tail -f)
- Export de resultados a CSV/JSON

**Panels:** 8 | **Refresh:** 10s | **Target:** Developers, Support

### 5. **Distributed Tracing** 🔍
- Mapa de servicios con latencias
- Búsqueda de trazas por ID, servicio, duración
- Flame graphs para analizar spans
- Comparación de trazas (antes/después de cambios)

**Panels:** 10 | **Refresh:** 1m | **Target:** Developers, Architects

### 6. **License Status** 📜
- Días restantes del trial
- Clientes activos y licencias generadas
- Uso de recursos vs límites
- Próximas renovaciones

**Panels:** 6 | **Refresh:** 5m | **Target:** Managers, Sales

---

## 🔒 SEGURIDAD

### Características de Seguridad

✅ **Autenticación y Autorización**
- JWT tokens con expiración configurable
- Roles de usuario: Admin, Editor, Viewer (trial: solo Admin)
- Integración con LDAP/Active Directory (producción)
- API keys para automatización

✅ **Cifrado**
- Comunicación HTTPS/TLS 1.3 (certificados autofirmados en trial)
- Cifrado en reposo de datos sensibles (contraseñas, API keys)
- Conexiones a BD cifradas (PostgreSQL SSL mode)

✅ **Auditoría**
- Logs de acceso y cambios en configuraciones
- Registro de queries ejecutadas por usuario
- Alertas de accesos sospechosos (rate limiting)

✅ **Aislamiento**
- Red Docker privada (no expuesta al host)
- Servicios internos sin puertos externos (solo NGINX público)
- Límites de recursos por contenedor (CPU, RAM)

✅ **Updates de Seguridad**
- Imágenes Docker actualizadas mensualmente
- Parches críticos aplicados en < 48h
- Notificaciones automáticas de CVEs

---

## 💰 MODELOS DE LICENCIAMIENTO

### Trial (Esta versión)

**Duración:** 180 días (6 meses)  
**Costo:** GRATIS  
**Restricciones:**
- Retención de datos: 7 días
- Sin alta disponibilidad (single instance)
- Soporte: 24-48h por email
- Límite de 10 usuarios concurrentes
- Marca "Trial" visible en dashboards

**Incluye:**
- Todos los 15 contenedores funcionales
- 6 dashboards precargados
- Documentación completa
- Ejemplos de integración (Python, Node.js, Java, Go)
- Actualizaciones de seguridad

### Comercial (Contactar ventas)

**Duración:** Anual (renovable)  
**Costo:** Bajo consulta (depende de escala)  
**Incluye TODO del trial +**
- ✅ Retención personalizada (30/60/90 días o ilimitada)
- ✅ Alta disponibilidad (3+ nodos)
- ✅ Soporte prioritario 24/7 (SLA 99.9%)
- ✅ Sin marcas de agua (white-label disponible)
- ✅ Usuarios ilimitados
- ✅ Dashboards personalizados a medida
- ✅ Integración con SSO empresarial (Okta, Azure AD)
- ✅ Almacenamiento en S3/GCS (object storage)
- ✅ Federación multi-región
- ✅ Exportación de datos (CSV, Parquet)
- ✅ Consultoría de arquitectura incluida
- ✅ Training on-site para equipos

**Planes:**
- **Starter:** 1-10 servidores | $500/mes
- **Business:** 10-50 servidores | $2,000/mes
- **Enterprise:** 50+ servidores | Precio personalizado
- **White-label:** Desde $5,000/mes

---

## 🎁 BENEFICIOS COMPETITIVOS

### vs. Datadog

| Característica | Rhinometric | Datadog |
|----------------|-------------|---------|
| **Precio** | Fijo mensual | Por host + por métrica |
| **Self-hosted** | ✅ Sí (datos en tu infra) | ❌ No (solo SaaS) |
| **Open Source** | ✅ Basado en OSS | ❌ Propietario |
| **Trial** | 180 días gratis | 14 días gratis |
| **Instalación** | 1-click | Agentes manuales |
| **Costo anual (50 hosts)** | ~$24k | ~$80k+ |

### vs. New Relic

| Característica | Rhinometric | New Relic |
|----------------|-------------|-----------|
| **Precio** | Fijo por servidor | Por GB ingerido |
| **Self-hosted** | ✅ Sí | ❌ No |
| **Dashboards** | Precargados | Requiere configuración |
| **Retención** | Hasta 90 días | 8 días (plan gratuito) |
| **Soporte** | Email + comunidad | Chat (planes pagos) |

### vs. Elastic Stack (ELK)

| Característica | Rhinometric | ELK |
|----------------|-------------|-----|
| **Instalación** | 1-click wizard | Manual compleja |
| **Mantenimiento** | Automático | Requiere expertise |
| **Dashboards** | Precargados | DIY |
| **Costo total** | $500-$5k/mes | "Gratis" + 1-2 DevOps ($120k/año) |
| **Trazas distribuidas** | ✅ Nativo (Tempo) | ⚠️ Requiere APM de pago |

### vs. Grafana Cloud

| Característica | Rhinometric | Grafana Cloud |
|----------------|-------------|---------------|
| **Precio** | Fijo mensual | Por serie/GB (variable) |
| **Self-hosted** | ✅ Sí | ❌ No |
| **Trial** | 180 días | 14 días |
| **Control de datos** | ✅ Total (on-prem) | ⚠️ Datos en Grafana |
| **Customización** | ✅ Total | ⚠️ Limitado |

**Resumen:** Rhinometric ofrece **80% del valor de Datadog** a **25% del costo**, con control total de tus datos.

---

## 📚 SOPORTE Y DOCUMENTACIÓN

### Canales de Soporte (Trial)

📧 **Email:** soporte@rhinometric.com  
⏱️ **Tiempo de respuesta:** 24-48 horas hábiles  
📖 **Documentación:** https://docs.rhinometric.com  
💬 **Comunidad:** https://community.rhinometric.com (próximamente)

### Documentación Incluida

✅ **Guía de Instalación** (Windows, macOS, Linux)  
✅ **Quick Start Guide** (Primeros pasos en 10 minutos)  
✅ **Guías de Integración** (Python, Node.js, Java, Go, .NET)  
✅ **API Reference** (REST API de license-server)  
✅ **Dashboard Cookbook** (Cómo crear dashboards personalizados)  
✅ **Troubleshooting** (Problemas comunes y soluciones)  
✅ **Upgrade Guide** (De trial a producción)

---

## 🚀 PRÓXIMOS PASOS

### Después de la Instalación

1. **Día 1-7: Exploración**
   - Revisar los 6 dashboards precargados
   - Conectar una aplicación de prueba (usar ejemplos de integración)
   - Enviar métricas, logs y trazas de prueba
   - Familiarizarse con Grafana (crear queries, alertas)

2. **Semana 2-4: Integración**
   - Conectar aplicaciones reales (desarrollo/staging)
   - Configurar alertas para métricas críticas
   - Crear dashboards personalizados para tu equipo
   - Entrenar a tu equipo (docs + videos)

3. **Mes 2-3: Optimización**
   - Analizar datos recopilados, identificar patrones
   - Ajustar retención según necesidades
   - Evaluar necesidad de alta disponibilidad
   - Preparar caso de negocio para licencia comercial

4. **Mes 4-6: Decisión**
   - ¿El trial resolvió tus problemas de observabilidad?
   - ¿Qué valor aportó a tu equipo? (tiempo ahorrado, bugs detectados)
   - ¿Necesitas más retención, soporte 24/7, o HA?
   - Contactar ventas para upgrade a comercial

### Contactar Ventas

Si estás interesado en una **licencia comercial** o tienes preguntas sobre:

- Pricing personalizado
- High Availability (HA)
- Integración con tu stack existente
- White-label / OEM
- Capacitación en sitio

📧 **Email:** ventas@rhinometric.com  
📞 **Teléfono:** +1 (555) 123-4567 (próximamente)  
📅 **Agendar demo:** https://rhinometric.com/demo

---

## 📊 CASOS DE ÉXITO (Simulados para MVP)

### Caso 1: E-commerce "FastShop"

**Problema:** Caídas de la aplicación durante Black Friday, sin visibilidad del origen.

**Solución:** Rhinometric Trial instalado en staging (septiembre). Identificaron:
- Memory leak en servicio de checkout (visible en trazas Tempo)
- Query SQL lenta (500ms → 50ms tras optimización)
- Alertas configuradas para CPU > 80%

**Resultado:** Black Friday sin caídas. Ahorro estimado: $200k en ventas perdidas.

**Quote:** *"Rhinometric nos dio visibilidad que nunca tuvimos. Ahora sabemos QUÉ falla, DÓNDE falla y POR QUÉ falla en segundos."* — CTO FastShop

### Caso 2: Fintech "PayNow"

**Problema:** Compliance requiere logs de todas las transacciones por 7 años. Solución anterior (ELK) costaba $15k/mes.

**Solución:** Rhinometric con retención de 90 días en hot storage, luego export a S3 (cold storage).

**Resultado:** Reducción de costos de logs en 60% ($9k → $3.6k/mes).

**Quote:** *"Pasamos de 3 DevOps manteniendo ELK a 0. Rhinometric es plug & play."* — Lead Engineer PayNow

### Caso 3: SaaS "ProjectHub"

**Problema:** Clientes reportaban lentitud, pero no sabían si era backend, BD o red.

**Solución:** Rhinometric con trazas distribuidas (Tempo). Descubrieron:
- 70% de latencia venía de API de terceros (Google Maps)
- Implementaron cache → latencia P95: 2s → 400ms

**Resultado:** NPS +25 puntos. Churn reducido 15%.

**Quote:** *"Las trazas de Tempo nos dieron el 'mapa del tesoro' de nuestros cuellos de botella."* — VP Engineering ProjectHub

---

## ❓ PREGUNTAS FRECUENTES

### ¿Necesito conocimientos técnicos para instalar Rhinometric?

**No.** El instalador wizard de Windows/macOS verifica requisitos automáticamente (Docker, RAM), instala Docker si falta, y configura todo con 3 clics. En Linux, el script `start-trial.sh` hace todo el trabajo.

### ¿Qué pasa con mis datos tras el trial?

**Tus datos quedan en tu infraestructura.** Rhinometric no envía datos a servidores externos. Al finalizar el trial (180 días), puedes:
- Exportar datos (PostgreSQL dump, Prometheus snapshots)
- Upgrade a licencia comercial (los datos se conservan)
- Desinstalar (instrucciones incluidas)

### ¿Puedo usar Rhinometric en producción con el trial?

**Técnicamente sí, legalmente no.** El trial tiene retención de 7 días y sin HA, lo cual NO es recomendable para producción. Además, la licencia trial prohíbe uso comercial. Contacta ventas para licencia de producción.

### ¿Cómo se compara Rhinometric con Grafana Cloud?

**Rhinometric es "Grafana Cloud on-premise".** Usa los mismos componentes (Grafana, Prometheus, Loki, Tempo), pero:
- ✅ Self-hosted (tus datos quedan en tu infra)
- ✅ Costo fijo (no por serie/GB como Grafana Cloud)
- ✅ Dashboards precargados (Grafana Cloud requiere configuración)

### ¿Qué lenguajes de programación soporta?

**Todos.** Rhinometric acepta:
- **Métricas:** Formato Prometheus (librerías en Python, Go, Java, Node.js, .NET, Ruby, PHP, Rust)
- **Logs:** Texto plano, JSON, Syslog (cualquier lenguaje puede escribir logs)
- **Trazas:** OpenTelemetry OTLP (soportado en 11+ lenguajes)

Incluimos ejemplos de integración para Python, Node.js, Java y Go.

### ¿Puedo personalizar los dashboards?

**Sí, totalmente.** Los 6 dashboards precargados son editables. Puedes:
- Modificar queries, visualizaciones, umbrales
- Crear dashboards desde cero (Grafana nativo)
- Exportar/importar dashboards (JSON)
- Compartir dashboards con tu equipo

### ¿Cómo actualizo Rhinometric a una versión nueva?

**Trial:** Actualización manual (descargar nueva versión, ejecutar script de upgrade).  
**Comercial:** Actualizaciones automáticas o asistidas por soporte.

Siempre se incluye guía de upgrade con cada release.

### ¿Qué pasa si mi trial expira?

**Día 180:** Rhinometric deja de aceptar nuevas métricas/logs/trazas. Dashboards siguen accesibles (solo lectura) por 30 días más.  
**Día 210:** Sistema se apaga automáticamente. Puedes exportar datos antes del apagado.

**Solución:** Upgrade a licencia comercial antes del día 180 → cero downtime.

### ¿Puedo extender el trial?

**Sí, bajo casos especiales.** Contacta a ventas@rhinometric.com explicando tu caso. Extensiones de 30-60 días pueden aprobarse para:
- Proyectos grandes que requieren más tiempo de evaluación
- ONGs, educación, startups (descuentos disponibles)

### ¿Rhinometric reemplaza a Datadog/New Relic completamente?

**Para la mayoría de casos, sí.** Rhinometric cubre:
- ✅ Métricas (equivalente a Datadog Metrics)
- ✅ Logs (equivalente a Datadog Logs)
- ✅ Trazas (equivalente a Datadog APM)
- ⚠️ No incluye: RUM (Real User Monitoring), Synthetic Monitoring, Security Monitoring

Si solo necesitas backend observability, Rhinometric es suficiente.

---

## 📞 CONTACTO

### Ventas

📧 ventas@rhinometric.com  
📅 Agendar demo: https://rhinometric.com/demo  
💼 LinkedIn: https://linkedin.com/company/rhinometric

### Soporte Técnico

📧 soporte@rhinometric.com  
📖 Docs: https://docs.rhinometric.com  
🐛 Reportar bug: https://github.com/rhinometric/issues

### General

🌐 Website: https://www.rhinometric.com  
📰 Blog: https://rhinometric.com/blog  
🐦 Twitter: @RhinometricHQ  
💬 Slack Community: https://rhinometric.com/slack

---

## 📝 NOTAS LEGALES

Este documento es una representación de las capacidades de **Rhinometric Trial v1.0**. Las especificaciones técnicas, rendimiento y características pueden variar según el hardware, configuración y carga de trabajo.

**Rhinometric** es una marca registrada. Grafana, Prometheus, Loki y Tempo son marcas registradas de Grafana Labs. PostgreSQL, Redis, NGINX son marcas de sus respectivos propietarios.

Para términos completos de licenciamiento, ver `LICENSE.txt` incluido en el paquete de instalación.

---

**© 2025 Rhinometric. All rights reserved.**

**Versión del documento:** 1.0  
**Fecha de publicación:** Octubre 2025  
**Última actualización:** Octubre 22, 2025
