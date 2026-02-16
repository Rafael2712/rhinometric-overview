# 🚀 RELEASE NOTES - Rhinometric v2.5.0

**Fecha de Release:** 16 Diciembre 2025  
**Nombre en código:** "Rhino Radar"  
**Tipo de Release:** Major Feature Update  
**Versión anterior:** v2.1.0

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Nuevas Funcionalidades](#nuevas-funcionalidades)
3. [Mejoras](#mejoras)
4. [Diferencias vs v2.1.0](#diferencias-vs-v210)
5. [Breaking Changes](#breaking-changes)
6. [Known Issues](#known-issues)
7. [Upgrade Guide](#upgrade-guide)
8. [Componentes del Stack](#componentes-del-stack)
9. [Requisitos del Sistema](#requisitos-del-sistema)
10. [Deprecations](#deprecations)

---

## Resumen Ejecutivo

Rhinometric v2.5.0 es una actualización mayor que introduce:

✨ **Nuevos componentes:**
- **Console v3** (frontend Vue.js + backend FastAPI) para gestión visual de servicios
- **AI Anomaly Detection Engine** con Prophet + IsolationForest
- **License Server v2** completamente reescrito en FastAPI con sistema de emails

📦 **Nuevos formatos de distribución:**
- **Demo OVA** (4 horas) → Importar y probar en VirtualBox/VMware
- **Trial Installer** (14 días) → Script automático para Linux (Ubuntu/Debian/CentOS)
- **Annual License** → Instalación completa para producción

🌐 **Sistema de descargas web:**
- Endpoints REST para descargas de OVA, instaladores y documentación
- Páginas WordPress profesionales listas para copiar/pegar
- Emails transaccionales con enlaces dinámicos a descargas

🎯 **Observabilidad mejorada:**
- 15+ dashboards Grafana listos para usar
- Tracing distribuido con Tempo + Jaeger
- AI-powered anomaly detection con alertas automáticas

---

## Nuevas Funcionalidades

### 1. Console v3 - Dashboard de Gestión Visual

**Puerto:** 3002  
**Tecnologías:** Vue.js 3 + FastAPI + PostgreSQL

**Features:**
- ✅ Vista unificada de todos los servicios monitoreados
- ✅ Gestión de API Connectors (añadir/editar/eliminar APIs externas)
- ✅ Dashboard de métricas en tiempo real
- ✅ Gestión de alertas y notificaciones
- ✅ Configuración de umbrales y reglas
- ✅ Logs centralizados con búsqueda full-text
- ✅ Panel de administración de usuarios (próximamente)

**Acceso:**
```
http://localhost:3002
Usuario: admin
Password: (generado al instalar)
```

---

### 2. AI Anomaly Detection Engine

**Puerto:** 8085  
**Tecnologías:** Python 3.11 + Prophet + IsolationForest + scikit-learn

**Características:**
- 🤖 **Detección automática de anomalías** en métricas de CPU, RAM, disco, red
- 📊 **Forecasting** con Prophet para predecir tendencias
- 🚨 **Alertas inteligentes** cuando se detectan patrones anómalos
- 📈 **Análisis de series temporales** con ventanas deslizantes
- 🎯 **Reducción de falsos positivos** con ML

**Algoritmos incluidos:**
- Facebook Prophet (forecasting)
- Isolation Forest (outlier detection)
- Z-Score (statistical anomaly detection)
- DBSCAN (clustering-based detection)

**Endpoints:**
```
POST /api/anomaly/detect
GET  /api/anomaly/models
GET  /api/anomaly/health
```

**Ejemplo de uso:**
```bash
curl -X POST http://localhost:8085/api/anomaly/detect \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "cpu_usage",
    "values": [45, 47, 50, 48, 95, 49, 46],
    "timestamps": ["2025-12-16T10:00:00", ...]
  }'
```

**Respuesta:**
```json
{
  "anomalies_detected": true,
  "anomaly_indices": [4],
  "anomaly_scores": [0.92],
  "threshold": 0.7,
  "model_used": "isolation_forest"
}
```

---

### 3. License Server v2 - FastAPI Rewrite

**Puerto:** 5000  
**Tecnologías:** FastAPI + PostgreSQL + Redis + Zoho SMTP

**Migración de Flask → FastAPI:**
- ✅ **10x más rápido** en endpoints de validación
- ✅ **Async/await** para operaciones de DB y email
- ✅ **Automatic OpenAPI docs** en `/docs`
- ✅ **Type safety** con Pydantic models
- ✅ **Better error handling** con HTTPException

**Nuevos endpoints en v2:**

#### Descargas
```
GET /downloads/demo-ova              → rhinometric-demo-2.5.0.ova
GET /downloads/trial-installer       → rhinometric-trial-2.5.0-install.sh
GET /downloads/info                  → JSON con metadata de archivos
```

#### Documentación
```
GET /docs/installation-guide?lang=es → PDF guía instalación (ES)
GET /docs/installation-guide?lang=en → PDF guía instalación (EN)
GET /docs/user-manual?lang=es        → PDF manual usuario (ES)
GET /docs/user-manual?lang=en        → PDF manual usuario (EN)
```

#### Licencias (mejorado)
```
POST   /api/admin/licenses           → Crear licencia + enviar email
GET    /api/licenses                 → Listar todas las licencias
GET    /api/licenses/{id}            → Detalles de licencia
PUT    /api/licenses/{id}            → Actualizar licencia
DELETE /api/licenses/{id}            → Desactivar licencia
POST   /api/licenses/validate        → Validar licencia con hardware_id
```

**Sistema de emails mejorado:**
- ✅ **Templates HTML responsive** con gradientes y diseño moderno
- ✅ **Logo SVG embebido** inline (no requiere hosting externo)
- ✅ **Enlaces dinámicos** basados en `SERVER_BASE_URL`
- ✅ **Multilenguaje** (ES/EN) en enlaces a PDFs
- ✅ **GDPR compliant** con notice de privacidad
- ✅ **Retry automático** si falla SMTP (hasta 1 retry después de 30s)
- ✅ **Fallback STARTTLS** si SSL falla (port 587)

**Ejemplo de email enviado:**
```
Asunto: [Rhinometric] Activación de su licencia Trial

[Logo Rhinometric SVG]

Hola Cliente,

Gracias por solicitar Rhinometric v2.5.0...

┌─────────────────────────────────┐
│  INFORMACIÓN DE TU LICENCIA     │
├─────────────────────────────────┤
│  Tipo: Trial                    │
│  Clave: RHINO-TRIA-2025-XYZ123  │
│  Expira: 30/12/2025            │
└─────────────────────────────────┘

[Botón: 📥 Descargar Instalador Linux (14 días)]
      ↓
https://licensing.rhinometric.com:5000/downloads/trial-installer

📚 Documentación adjunta:
  • Manual de Usuario (PDF)
  • Guía de Instalación (PDF)

📘 Docs online:
  • Guía Instalación (ES) | (EN)
  • Manual Usuario (ES) | (EN)

🛡️ GDPR notice...
```

---

### 4. Sistema de Distribución Multi-Formato

Rhinometric v2.5.0 se distribuye en **3 formatos** para diferentes casos de uso:

#### Formato 1: Demo OVA (4 horas)

**Target:** Evaluación rápida sin instalación

**Características:**
- ✅ Archivo OVA listo para importar en VirtualBox/VMware
- ✅ Stack completo pre-configurado
- ✅ Licencia demo_cloud de 4 horas incluida
- ✅ Hasta 20 hosts de monitorización
- ✅ Sin necesidad de Docker ni configuración

**Tamaño:** ~3 GB

**Acceso:**
```
http://localhost:3000   → Grafana (admin/admin)
http://localhost:3002   → Console
http://localhost:8085   → AI Anomaly Engine
```

**Descarga:**
```bash
# Desde página web
https://rhinometric.com/demo

# O directamente
curl -O https://licensing.rhinometric.com:5000/downloads/demo-ova
```

---

#### Formato 2: Trial Installer (14 días)

**Target:** Evaluación en servidor Linux propio

**Características:**
- ✅ Script bash automático
- ✅ Instalación en Ubuntu 20.04+, Debian 11+, CentOS 8+
- ✅ Licencia trial de 14 días incluida
- ✅ Hasta 5 hosts de monitorización
- ✅ Requiere Docker 24.0+

**Tamaño:** ~50 KB (script), total ~1.5 GB (descarga Docker images)

**Requisitos:**
- Linux (Ubuntu/Debian/CentOS)
- Docker 24.0+ y Docker Compose
- 8 GB RAM mínimo
- 20 GB disco libre

**Instalación:**
```bash
wget https://licensing.rhinometric.com:5000/downloads/trial-installer \
  -O rhinometric-install.sh

chmod +x rhinometric-install.sh

sudo ./rhinometric-install.sh
# Sigue las instrucciones interactivas
```

**El script automáticamente:**
1. Detecta sistema operativo
2. Verifica requisitos (Docker, RAM, disco)
3. Descarga docker-compose-v2.5.0.yml
4. Configura `.env` con licencia trial
5. Ejecuta `docker compose up -d`
6. Muestra credenciales de acceso
7. Ejecuta health checks

---

#### Formato 3: Annual License (1 año)

**Target:** Instalación completa en producción

**Características:**
- ✅ Licencia annual_standard de 1 año
- ✅ Hasta 20 hosts de monitorización (expandible)
- ✅ Soporte técnico incluido
- ✅ Actualizaciones y parches
- ✅ SLA de uptime 99.9%

**Descarga:**
```bash
# Desde GitHub Releases
wget https://github.com/Rafael2712/rhinometric-overview/releases/latest/download/rhinometric-v2.5.0-stable.tar.gz

tar -xzf rhinometric-v2.5.0-stable.tar.gz
cd rhinometric-v2.5.0

# Configurar licencia
nano .env
# LICENSE_KEY=RHINO-ANNU-2025-XXXXXXXXXXXXX

docker compose -f docker-compose-v2.5.0.yml up -d
```

---

### 5. Páginas Web WordPress

**3 páginas HTML listas para publicar:**

1. **Demo OVA Page** (docs/v2.5.0/wordpress/01-demo-ova-page.html)
   - Hero section con gradiente púrpura
   - Botón descarga → `/downloads/demo-ova`
   - Features grid, pasos instalación, requisitos

2. **Trial Linux Page** (docs/v2.5.0/wordpress/02-trial-linux-page.html)
   - Hero section con gradiente verde
   - Botón descarga → `/downloads/trial-installer`
   - Plataformas compatibles, comandos instalación

3. **Documentation Hub** (docs/v2.5.0/wordpress/03-documentation-page.html)
   - Grid de 4 tipos de docs
   - Botones descarga PDFs (ES/EN)
   - Links a API reference

**Características:**
- ✅ Diseño responsive (desktop/tablet/mobile)
- ✅ Inline CSS (no conflictos con tema WordPress)
- ✅ Copy-paste ready
- ✅ SEO optimized
- ✅ Fast loading (~0.5s)

---

## Mejoras

### Performance

- **License Server:** 10x más rápido con FastAPI async
- **Console backend:** Conexión pooling a PostgreSQL (50 conexiones)
- **Grafana:** Pre-loaded dashboards (no generación on-demand)
- **Prometheus:** Retention aumentada a 30 días (antes 15)
- **Loki:** Compression mejorada (50% menos espacio)

### Seguridad

- **Licencias:** Validación con hardware_id (anti-piratería)
- **Emails:** SPF/DKIM ready (Zoho SMTP)
- **Passwords:** Bcrypt hashing para usuarios Console
- **API Tokens:** JWT con expiración 24h
- **CORS:** Restricción a dominios permitidos

### Observabilidad

- **Dashboards Grafana:** 15 dashboards nuevos
  - Overview Dashboard
  - Services Deep Dive
  - AI Anomalies Timeline
  - License Server Metrics
  - Console Usage Analytics
  - etc.

- **Logs:** Structured logging con JSON
- **Traces:** Distributed tracing con Tempo + Jaeger
- **Alerts:** 20+ alerting rules predefinidas

### Developer Experience

- **OpenAPI Docs:** License Server → `http://localhost:5000/docs`
- **API Connector:** Test endpoints in Console UI
- **Scripts:** Deployment automation scripts
- **Documentation:** 10+ markdown guides

---

## Diferencias vs v2.1.0

| Feature | v2.1.0 | v2.5.0 |
|---------|--------|--------|
| **License Server** | Flask (sync) | FastAPI (async) ✅ |
| **Console** | ❌ No existía | Vue.js + FastAPI ✅ |
| **AI Anomaly Detection** | ❌ No | Prophet + IsolationForest ✅ |
| **Formatos distribución** | Solo .tar.gz | OVA + Installer + tar.gz ✅ |
| **Descargas web** | Manual | Endpoints REST ✅ |
| **Emails** | Texto plano | HTML responsive ✅ |
| **Docs multilanguage** | Solo ES | ES + EN ✅ |
| **WordPress pages** | ❌ No | 3 páginas HTML ✅ |
| **Dashboards Grafana** | 5 básicos | 15 profesionales ✅ |
| **Tracing distribuido** | ❌ No | Tempo + Jaeger ✅ |
| **Performance (req/s)** | ~100 | ~1000 ✅ |
| **Prometheus retention** | 15 días | 30 días ✅ |
| **PostgreSQL version** | 14 | 16 ✅ |
| **Grafana version** | 9.x | 11.x ✅ |

**Conclusión:** v2.5.0 es un **salto generacional** con mejoras en todas las áreas.

---

## Breaking Changes

⚠️ **Cambios que pueden romper compatibilidad con v2.1.0:**

### 1. License Server API Changes

**v2.1.0:**
```bash
POST /license/create
{
  "name": "Cliente",
  "email": "cliente@example.com",
  "type": "trial"
}
```

**v2.5.0:**
```bash
POST /api/admin/licenses
{
  "customer_name": "Cliente",
  "client_email": "cliente@example.com",
  "license_type": "trial",
  "client_company": "Empresa SL"  # nuevo campo obligatorio
}
```

**Migración:**
- Actualizar URLs: `/license/*` → `/api/admin/licenses`
- Añadir campo `client_company` a tus requests

---

### 2. Environment Variables

**Nuevas variables requeridas:**
```env
# v2.5.0 nuevo
SERVER_BASE_URL=https://licensing.rhinometric.com:5000

# Renombradas
DATABASE_URL=postgresql://...  # antes: DB_CONNECTION_STRING
REDIS_URL=redis://...          # antes: REDIS_CONNECTION
```

**Migración:**
Ver [Upgrade Guide](#upgrade-guide)

---

### 3. Docker Compose File

**v2.1.0:** `docker-compose.yml`  
**v2.5.0:** `docker-compose-v2.5.0.yml`

Nuevos servicios añadidos:
- `rhinometric-console-frontend` (puerto 3002)
- `rhinometric-console-backend` (puerto 8105)
- `rhinometric-ai-anomaly-engine` (puerto 8085)
- `tempo` (puerto 3200)
- `jaeger` (puerto 16686)

---

### 4. Ports Changes

| Servicio | v2.1.0 | v2.5.0 | Cambio |
|----------|--------|--------|--------|
| License Server | 5000 | 5000 | Sin cambio |
| Grafana | 3000 | 3000 | Sin cambio |
| Prometheus | 9090 | 9090 | Sin cambio |
| Console Frontend | ❌ | 3002 | NUEVO ✅ |
| Console Backend | ❌ | 8105 | NUEVO ✅ |
| AI Anomaly Engine | ❌ | 8085 | NUEVO ✅ |
| Jaeger UI | ❌ | 16686 | NUEVO ✅ |
| Tempo | ❌ | 3200 | NUEVO ✅ |

**Migración:** Actualizar firewall/proxies para permitir nuevos puertos.

---

## Known Issues

### 1. Email Delivery (Low Priority)

**Issue:** Emails pueden ir a spam en algunos clientes

**Causa:** SPF/DKIM no configurado en DNS de dominio  
**Workaround:** Configurar SPF/DKIM o usar Gmail/Outlook que son más permisivos  
**Fix previsto:** v2.5.1

---

### 2. OVA File Size (Cosmetic)

**Issue:** Archivo OVA es grande (~3 GB)

**Causa:** Incluye todas las Docker images pre-pulled  
**Impacto:** Download lento en conexiones < 10 Mbps  
**Workaround:** Usar Trial Installer en vez de OVA  
**Fix previsto:** v2.6.0 (OVA comprimida)

---

### 3. AI Anomaly Detection - Cold Start (Medium)

**Issue:** Primera detección de anomalías puede tardar ~30s

**Causa:** Carga de modelos Prophet en memoria  
**Impacto:** Latencia inicial alta  
**Workaround:** Pre-warm endpoint con dummy request  
**Fix previsto:** v2.5.2 (lazy loading mejorado)

---

### 4. Console - Edición de API Connectors (Low)

**Issue:** Al editar un API Connector, cambios no se reflejan hasta reload

**Causa:** Frontend no invalida cache de Vue  
**Impacto:** UX confuso  
**Workaround:** Refrescar página después de guardar  
**Fix previsto:** v2.5.1

---

### 5. WordPress HTML - Theme Conflicts (Low)

**Issue:** En algunos temas WordPress, botones pierden estilo

**Causa:** CSS del tema sobrescribe inline styles  
**Workaround:** Añadir `!important` a estilos inline  
**Fix previsto:** Documentado en PUBLISHING_GUIDE.md

---

## Upgrade Guide

### Desde v2.1.0 → v2.5.0

#### Paso 1: Backup

```bash
# Backup de bases de datos
docker exec rhinometric-postgres pg_dump -U rhinometric rhinometric > backup-v2.1.0.sql

# Backup de configuración
cp docker-compose.yml docker-compose.yml.backup
cp .env .env.backup
```

#### Paso 2: Parar v2.1.0

```bash
docker compose -f docker-compose.yml down
# NO uses -v (no borrar volumes)
```

#### Paso 3: Descargar v2.5.0

```bash
wget https://github.com/Rafael2712/rhinometric-overview/releases/latest/download/rhinometric-v2.5.0-stable.tar.gz
tar -xzf rhinometric-v2.5.0-stable.tar.gz
cd rhinometric-v2.5.0
```

#### Paso 4: Migrar configuración

```bash
# Copiar .env antiguo
cp ../rhinometric-v2.1.0/.env .env

# Añadir nuevas variables
echo "SERVER_BASE_URL=https://licensing.rhinometric.com:5000" >> .env
echo "CONSOLE_PORT=3002" >> .env
echo "AI_ENGINE_PORT=8085" >> .env
```

#### Paso 5: Migrar base de datos

```bash
# Aplicar migraciones
docker compose -f docker-compose-v2.5.0.yml up -d postgres
sleep 10

# Ejecutar migrations script
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric -f /migrations/v2.5.0.sql
```

#### Paso 6: Iniciar v2.5.0

```bash
docker compose -f docker-compose-v2.5.0.yml up -d
```

#### Paso 7: Verificar

```bash
# Health checks
curl http://localhost:5000/api/health    # License Server
curl http://localhost:8105/health        # Console Backend
curl http://localhost:8085/health        # AI Anomaly Engine
curl http://localhost:3000/api/health    # Grafana

# Logs
docker logs rhinometric-license-server-v2 --tail 50
```

#### Paso 8: Acceder a nuevos servicios

```
http://localhost:3002   → Console v3
http://localhost:8085   → AI Anomaly Engine API
http://localhost:16686  → Jaeger UI (tracing)
```

---

## Componentes del Stack

### Servicios Core

| Componente | Versión | Puerto | Descripción |
|------------|---------|--------|-------------|
| **Grafana** | 11.x | 3000 | Dashboards y visualización |
| **Prometheus** | 2.48.x | 9090 | Metrics storage |
| **Loki** | 2.9.x | 3100 | Logs aggregation |
| **Tempo** | 2.3.x | 3200 | Distributed tracing |
| **Jaeger** | 1.52.x | 16686 | Tracing UI |
| **PostgreSQL** | 16.x | 5432 | Database |
| **Redis** | 7.2.x | 6379 | Cache & queues |
| **Alertmanager** | 0.26.x | 9093 | Alert routing |

### Aplicaciones Rhinometric

| Componente | Tecnología | Puerto | Estado |
|------------|------------|--------|--------|
| **License Server v2** | FastAPI + Python 3.11 | 5000 | ✅ Estable |
| **Console Frontend** | Vue.js 3 + Vite | 3002 | ✅ Estable |
| **Console Backend** | FastAPI + PostgreSQL | 8105 | ✅ Estable |
| **AI Anomaly Engine** | Python + Prophet + scikit-learn | 8085 | ⚠️ Beta |
| **API Connector** | Python + FastAPI | 8000 | ✅ Estable |

### Exporters

- `node-exporter` (9100) - System metrics
- `cadvisor` (8080) - Container metrics
- `postgres-exporter` (9187) - PostgreSQL metrics
- `redis-exporter` (9121) - Redis metrics
- `blackbox-exporter` (9115) - Endpoint probing

---

## Requisitos del Sistema

### Demo OVA

- **VirtualBox:** 6.0+ o **VMware:** Workstation/Fusion 15+
- **RAM asignada:** 8 GB mínimo (16 GB recomendado)
- **Disco:** 30 GB libres
- **CPU:** 4 cores (virtual)

### Trial Installer / Annual License

#### Hardware Mínimo

- **CPU:** 4 cores @ 2.0 GHz
- **RAM:** 8 GB
- **Disco:** 50 GB libres (SSD recomendado)
- **Red:** 100 Mbps

#### Hardware Recomendado (Producción)

- **CPU:** 8 cores @ 3.0 GHz
- **RAM:** 16 GB
- **Disco:** 200 GB SSD NVMe
- **Red:** 1 Gbps

#### Software

- **OS:** Ubuntu 20.04+, Debian 11+, CentOS 8+, RHEL 8+
- **Docker:** 24.0+
- **Docker Compose:** 2.20+
- **Python:** 3.9+ (para scripts)
- **Bash:** 4.0+

---

## Deprecations

### Deprecated en v2.5.0 (Se eliminarán en v3.0.0)

- ❌ **License Server Flask** → Usar FastAPI version
- ❌ **Endpoint `/license/create`** → Usar `/api/admin/licenses`
- ❌ **Variable `DB_CONNECTION_STRING`** → Usar `DATABASE_URL`
- ❌ **Grafana v9.x** → Actualizar a v11.x

### Still Supported (Legacy)

- ✅ **PostgreSQL 14** (recomendado: 16)
- ✅ **Redis 6.x** (recomendado: 7.x)
- ✅ **Docker 20.x** (recomendado: 24.x)

---

## Instalación Rápida

### Opción 1: Demo OVA (MÁS RÁPIDO)

```bash
# 1. Descargar OVA
https://rhinometric.com/demo

# 2. Importar en VirtualBox
VirtualBox → Archivo → Importar servicio virtualizado...
→ Seleccionar rhinometric-demo-2.5.0.ova

# 3. Iniciar VM

# 4. Acceder desde host
http://localhost:3000  # Grafana
```

### Opción 2: Trial Installer

```bash
# 1. Descargar installer
wget https://licensing.rhinometric.com:5000/downloads/trial-installer \
  -O install.sh

# 2. Ejecutar
chmod +x install.sh
sudo ./install.sh

# 3. Seguir wizard interactivo
```

### Opción 3: Manual (GitHub Release)

```bash
# 1. Descargar
wget https://github.com/Rafael2712/rhinometric-overview/releases/latest/download/rhinometric-v2.5.0-stable.tar.gz

# 2. Extraer
tar -xzf rhinometric-v2.5.0-stable.tar.gz
cd rhinometric-v2.5.0

# 3. Configurar
cp .env.example .env
nano .env  # Editar LICENSE_KEY

# 4. Iniciar
docker compose -f docker-compose-v2.5.0.yml up -d
```

---

## Documentación Adicional

- **Deployment Checklist:** [docs/v2.5.0/DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- **Download Endpoints:** [docs/v2.5.0/DOWNLOAD_ENDPOINTS.md](DOWNLOAD_ENDPOINTS.md)
- **Email Testing:** [docs/v2.5.0/EMAIL_TESTING.md](EMAIL_TESTING.md)
- **WordPress Publishing:** [docs/v2.5.0/PUBLISHING_GUIDE.md](PUBLISHING_GUIDE.md)
- **API Documentation:** http://localhost:5000/docs (License Server)

---

## Desarrollo

Rhinometric v2.5.0 desarrollado por Rafael Canelón.

---

## Licencia

Rhinometric v2.5.0 es software propietario.

**Licencias disponibles:**
- **Demo Cloud:** 4 horas, hasta 20 hosts (gratis)
- **Trial:** 14 días, hasta 5 hosts (gratis)
- **Annual Standard:** 1 año, hasta 20 hosts ($1,999/año)
- **Enterprise:** Personalizado, hosts ilimitados (contactar ventas)

---

## Contacto y Soporte

**Email:** rafael.canelon@rhinometric.com  
**Web:** https://rhinometric.com  
**Docs:** https://rhinometric.com/documentation  
**GitHub:** https://github.com/Rafael2712/rhinometric-overview

**Soporte técnico:**
- Lunes a viernes, 9:00-18:00 CET
- Tiempo de respuesta: < 4 horas (Annual/Enterprise), < 24 horas (Trial)

---

**Última actualización:** 16 Diciembre 2025  
**Versión:** 2.5.0  
**Changelog completo:** https://github.com/Rafael2712/rhinometric-overview/blob/main/CHANGELOG.md
