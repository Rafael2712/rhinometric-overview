# 🦏 Rhinometric v2.5.0 - Enterprise Observability Platform

[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.5.0-green.svg)](https://github.com/Rafael2712/rhinometric-overview/releases/tag/v2.5.0)
[![Docker](https://img.shields.io/badge/docker-24.0+-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)

**Plataforma completa de observabilidad y AIOps** que centraliza métricas, logs, traces y detección de anomalías con inteligencia artificial.

---

## ✨ Novedades v2.5.0

🎯 **Console v3** → Dashboard visual de gestión (Vue.js + FastAPI)  
🤖 **AI Anomaly Engine** → Detección inteligente con Prophet + IsolationForest  
📦 **3 Formatos de Distribución** → Demo OVA (4h), Trial Installer (14d), Annual License  
🌐 **WordPress Landing Pages** → 3 páginas HTML profesionales listas para publicar  
📧 **Sistema de Emails** → Templates responsive con descargas dinámicas  
📚 **Docs Multilanguage** → Guías completas en ES + EN

Ver [RELEASE_NOTES.md](docs/v2.5.0/RELEASE_NOTES.md) para changelog completo.

---

## 🚀 Inicio Rápido

### Opción 1: Demo OVA (⏱️ 5 minutos)

**Ideal para:** Evaluación rápida sin instalación

```bash
# 1. Descargar OVA
https://rhinometric.com/demo

# 2. Importar en VirtualBox
VirtualBox → Archivo → Importar servicio virtualizado → rhinometric-demo-2.5.0.ova

# 3. Iniciar VM

# 4. Acceder
http://localhost:3000  → Grafana (admin/admin)
http://localhost:3002  → Console v3
http://localhost:8085  → AI Anomaly Engine
```

**Características:**
- ✅ 4 horas de evaluación
- ✅ Hasta 20 hosts
- ✅ Stack completo incluido
- ✅ Sin configuración

---

### Opción 2: Trial Installer (⏱️ 15 minutos)

**Ideal para:** Evaluación en tu propio servidor Linux

```bash
# 1. Descargar installer
wget https://licensing.rhinometric.com:5000/downloads/trial-installer -O install.sh

# 2. Ejecutar
chmod +x install.sh
sudo ./install.sh

# 3. Seguir wizard interactivo
# El script detecta tu OS, verifica requisitos, instala Docker si es necesario,
# y configura todo automáticamente.
```

**Características:**
- ✅ 14 días de evaluación
- ✅ Hasta 5 hosts
- ✅ Instalación automática
- ✅ Ubuntu, Debian, CentOS, RHEL compatible

**Requisitos:**
- Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- 8 GB RAM mínimo
- 50 GB disco
- Docker 24.0+ (se instala automáticamente si falta)

---

### Opción 3: Instalación Completa (⏱️ 30 minutos)

**Ideal para:** Producción con Annual License

```bash
# 1. Clonar repositorio
git clone https://github.com/Rafael2712/rhinometric-overview.git
cd rhinometric-overview

# 2. Configurar licencia
cp .env.example .env
nano .env
# Añadir LICENSE_KEY=RHINO-ANNU-2025-XXXXXXXXXXXXX

# 3. Iniciar stack
docker compose -f docker-compose-v2.5.0.yml up -d

# 4. Esperar health checks (1-2 minutos)
docker compose -f docker-compose-v2.5.0.yml ps
```

**Accesos:**
```
http://localhost:3000   → Grafana (Dashboards)
http://localhost:3002   → Console v3 (Management)
http://localhost:9090   → Prometheus (Metrics)
http://localhost:3100   → Loki (Logs)
http://localhost:16686  → Jaeger (Traces)
http://localhost:9093   → Alertmanager (Alerts)
http://localhost:5000   → License Server API
http://localhost:8085   → AI Anomaly Engine
```

---

## 🏗️ Arquitectura del Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                      RHINOMETRIC v2.5.0                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │  Console v3  │  │  AI Anomaly  │  │  License Server v2 │   │
│  │  (Vue.js)   │  │   Engine     │  │    (FastAPI)       │   │
│  │  Port 3002  │  │  Port 8085   │  │    Port 5000       │   │
│  └──────┬──────┘  └──────┬───────┘  └─────────┬──────────┘   │
│         │                │                     │               │
│  ┌──────▼────────────────▼─────────────────────▼──────────┐   │
│  │              PostgreSQL 16 + Redis 7.2                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │   Grafana    │  │  Prometheus  │  │      Loki        │    │
│  │  Port 3000   │  │  Port 9090   │  │   Port 3100      │    │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬────────┘    │
│         │                 │                     │              │
│  ┌──────▼─────────────────▼─────────────────────▼────────┐   │
│  │            Tempo (Traces) + Jaeger UI                 │   │
│  │              Port 3200   +  Port 16686                │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  Exporters: node, cadvisor, postgres, redis, etc.    │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Componentes Principales

| Componente | Versión | Descripción | Puerto |
|------------|---------|-------------|--------|
| **Grafana** | 11.x | Visualización y Dashboards | 3000 |
| **Prometheus** | 2.48 | Storage de métricas | 9090 |
| **Loki** | 2.9 | Aggregation de logs | 3100 |
| **Tempo** | 2.3 | Distributed tracing | 3200 |
| **Jaeger** | 1.52 | Tracing UI | 16686 |
| **Alertmanager** | 0.26 | Gestión de alertas | 9093 |
| **PostgreSQL** | 16 | Base de datos | 5432 |
| **Redis** | 7.2 | Cache y queues | 6379 |
| **Console v3** | - | Dashboard management (Vue.js) | 3002 |
| **AI Anomaly Engine** | - | ML anomaly detection | 8085 |
| **License Server v2** | - | Licensing & downloads (FastAPI) | 5000 |

---

## 📋 Casos de Uso

### 1. Monitorización de Infraestructura

- ✅ Servidores Linux/Windows
- ✅ Containers Docker
- ✅ Kubernetes clusters
- ✅ VMs (VMware, Hyper-V, KVM)
- ✅ Cloud (AWS, Azure, GCP)

### 2. Monitorización de Aplicaciones

- ✅ APIs REST
- ✅ Microservicios
- ✅ Bases de datos (PostgreSQL, MySQL, MongoDB, Redis)
- ✅ Message queues (RabbitMQ, Kafka)
- ✅ Web servers (Nginx, Apache)

### 3. Detección de Anomalías

- ✅ CPU/RAM/Disco con ML
- ✅ Patrones de tráfico anómalos
- ✅ Latencias inesperadas
- ✅ Errores 5xx en APIs

### 4. Compliance y Auditoría

- ✅ Logs centralizados 30 días
- ✅ GDPR compliant
- ✅ Traces de todas las requests
- ✅ Alertas de eventos críticos

---

## 🎯 Dashboards Incluidos (15+)

1. **Overview Dashboard** → Vista general del sistema
2. **Services Deep Dive** → Análisis detallado por servicio
3. **AI Anomalies Timeline** → Anomalías detectadas por ML
4. **Infrastructure Monitoring** → CPU, RAM, Disco, Red
5. **PostgreSQL Performance** → Queries, connections, locks
6. **Redis Monitoring** → Memory, commands, hit rate
7. **API Performance** → Latency, throughput, errores
8. **License Server Metrics** → Licencias creadas, emails sent
9. **Console Usage Analytics** → Usuarios activos, acciones
10. **Loki Logs Explorer** → Búsqueda y análisis de logs
11. **Jaeger Tracing** → Distributed traces visualization
12. **Alertmanager Status** → Alertas activas y resueltas
13. **Container Monitoring** → Docker containers stats
14. **Network Traffic** → In/Out por host
15. **Custom Metrics** → API Connectors externos

---

## 📚 Documentación

### Guías de Usuario

- [Installation Guide (ES)](docs/v2.5.0/DEPLOYMENT_CHECKLIST.md)
- [Installation Guide (EN)](docs/v2.5.0/DOWNLOAD_ENDPOINTS.md)
- [User Manual (ES/EN)](https://rhinometric.com/documentation)
- [API Reference](http://localhost:5000/docs) (OpenAPI)

### Guías Técnicas

- [Download Endpoints](docs/v2.5.0/DOWNLOAD_ENDPOINTS.md) - REST API para descargas
- [Email Testing](docs/v2.5.0/EMAIL_TESTING.md) - Probar emails transaccionales
- [WordPress Publishing](docs/v2.5.0/PUBLISHING_GUIDE.md) - Publicar landing pages
- [Release Notes v2.5.0](docs/v2.5.0/RELEASE_NOTES.md) - Changelog completo
- [Release Checklist](docs/v2.5.0/RELEASE_CHECKLIST.md) - Deployment a producción

---

## 🔑 Licenciamiento

### Tipos de Licencia

| Tipo | Duración | Hosts | Precio | Uso |
|------|----------|-------|--------|-----|
| **Demo Cloud** | 4 horas | Hasta 20 | Gratis | Evaluación rápida (OVA) |
| **Trial** | 14 días | Hasta 5 | Gratis | Evaluación en servidor propio |
| **Annual Standard** | 1 año | Hasta 20 | $1,999/año | Producción PYME |
| **Enterprise** | Custom | Ilimitado | Contactar | Grandes corporaciones |

### Solicitar Licencia

**Demo (4h):**
```
https://rhinometric.com/demo
```

**Trial (14d):**
```
https://rhinometric.com/trial
```

**Annual/Enterprise:**
```
Email: rafael.canelon@rhinometric.com
Web: https://rhinometric.com/contacto
```

---

## 🛠️ Requisitos del Sistema

### Mínimos (Trial)

- **CPU:** 4 cores @ 2.0 GHz
- **RAM:** 8 GB
- **Disco:** 50 GB libres
- **OS:** Ubuntu 20.04+, Debian 11+, CentOS 8+, RHEL 8+
- **Docker:** 24.0+
- **Network:** 100 Mbps

### Recomendados (Producción)

- **CPU:** 8 cores @ 3.0 GHz
- **RAM:** 16 GB
- **Disco:** 200 GB SSD NVMe
- **OS:** Ubuntu 22.04 LTS
- **Docker:** Latest stable
- **Network:** 1 Gbps

---

## 🧪 Testing

### Test de Endpoints

```bash
# Descargar script
chmod +x test-download-endpoints.sh

# Ejecutar
./test-download-endpoints.sh http://localhost:5000
```

### Test de Emails

```bash
# Configurar email de prueba
export TEST_EMAIL="tu-email@example.com"

# Ejecutar
chmod +x scripts/test_license_emails.sh
./scripts/test_license_emails.sh http://localhost:5000
```

Ver [EMAIL_TESTING.md](docs/v2.5.0/EMAIL_TESTING.md) para guía completa.

---

## 🤝 Contribuir

Rhinometric es software propietario. Para reportar bugs o sugerir features:

📧 Email: rafael.canelon@rhinometric.com  
🐛 Issues: GitHub Issues (solo para bugs públicos)

---

## 📞 Soporte

**Soporte Técnico:**
- Email: rafael.canelon@rhinometric.com
- Horario: Lunes a viernes, 9:00-18:00 CET
- SLA: < 4 horas (Annual/Enterprise), < 24 horas (Trial)

**Recursos:**
- Web: https://rhinometric.com
- Docs: https://rhinometric.com/documentation
- GitHub: https://github.com/Rafael2712/rhinometric-overview

---

## 📄 Licencia

Copyright © 2025 Rhinometric. Todos los derechos reservados.

Este software es propietario y requiere una licencia válida para su uso.

---

**Última actualización:** 16 Diciembre 2025  
**Versión actual:** 2.5.0  
**Autor:** Rafael Canelón
- Validación de entrada con Joi
- Headers de seguridad con Helmet
- Hashing de contraseñas con bcrypt

## 📈 Monitoreo

- **Health checks** en `/api/v1/health`
- **Métricas Prometheus** en Puerto 9090
- **Dashboards Grafana** en Puerto 3000
- **Logs centralizados** con Loki

## 🚢 Despliegue

Ver documentación en `/docs/deployment/` para instrucciones detalladas de despliegue en:

- Oracle Cloud Infrastructure
- Docker Compose
- Kubernetes

## 🤝 Contribución

1. Fork del proyecto
2. Crear branch de feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -m 'Añadir nueva funcionalidad'`
4. Push al branch: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## 📝 Licencia

**Rhinometric v2.5.0** es software propietario y requiere una licencia válida para su uso. Para información sobre licencias, contacte a:

- **Email**: rafael.canelon@rhinometric.com

## 📞 Soporte

- **Email**: soporte@rhinometric.com
- **Documentación**: https://docs.rhinometric.com
- **Issues**: GitHub Issues en este repositorio – Observabilidad

## Resumen
Traefik → NGINX (web). PgBouncer → PostgreSQL.
Prometheus recolecta métricas (node-exporter, cAdvisor, nginx-exporter, postgres-exporter, pgbouncer-exporter, Traefik).
Logs con Promtail → Loki. Grafana visualiza (dashboards provisionados).
