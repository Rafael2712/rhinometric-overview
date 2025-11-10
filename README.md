# ��� Rhinometric Enterprise v2.5.0

[![Version](https://img.shields.io/badge/version-2.5.0-blue.svg)](https://github.com/Rafael2712/rhinometric-overview/releases/tag/v2.5.0-public)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-complete-green.svg)](docs/)
[![Status](https://img.shields.io/badge/status-production%20ready-success.svg)]()

**Plataforma integral de observabilidad empresarial con IA local**

Rhinometric Enterprise combina las mejores herramientas open-source (Prometheus, Grafana, Loki, Tempo) con módulos propietarios de inteligencia artificial, generación de informes y gestión de licencias, todo desplegable on-premise en minutos.

---

## ✨ Qué hay de nuevo en v2.5.0

### ��� **Enterprise Branding**
- ✅ Landing page personalizable con branding corporativo
- ✅ Temas visuales para Grafana
- ✅ Logos SVG vectoriales de alta calidad
- ✅ Email templates branded (Alertmanager)
- ✅ MOTD personalizado para SSH/consola

### ��� **AI Anomaly Detection**
- ✅ Motor de detección de anomalías con Machine Learning (Isolation Forest)
- ✅ Métricas Prometheus nativas (`rhinometric_anomaly_*`)
- ✅ Dashboard Grafana dedicado con 4 paneles especializados
- ✅ Queries PromQL optimizadas para anomalías

### ��� **Dashboard Builder UI**
- ✅ Interfaz web para crear dashboards sin código
- ✅ Backend API REST (puerto 8001)
- ✅ Integración directa con Grafana API

### ��� **OVA Demo Appliance**
- ✅ Imagen OVA lista para importar en VirtualBox/VMware/Proxmox
- ✅ Build automatizado con Packer
- ✅ First-boot automation
- ✅ Stack completo pre-configurado (15+ servicios Docker)

### ��� **License Server Mejorado**
- ✅ Licencias trial de 30 días
- ✅ Envío automático por email
- ✅ Validación offline

---

## ��� Inicio Rápido

### Opción 1: OVA Demo Appliance (Recomendado para POCs)

1. **Descargar OVA** desde [Releases](https://github.com/Rafael2712/rhinometric-overview/releases)
2. **Importar** en VirtualBox/VMware/Proxmox
3. **Iniciar VM** y esperar ~5 minutos (first-boot automation)
4. **Acceder**: `https://<VM_IP>` (usuario: `admin`, contraseña: `rhinometric_v22`)

**Incluye**:
- ✅ Grafana con 10+ dashboards pre-configurados
- ✅ Prometheus + Loki + Tempo + Alertmanager
- ✅ AI Anomaly Detection activado
- ✅ Dashboard Builder UI
- ✅ Licencia trial de 30 días

### Opción 2: Docker Compose (Manual)

```bash
# Clonar repositorio
git clone https://github.com/Rafael2712/rhinometric-overview.git
cd rhinometric-overview

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Iniciar stack
docker compose up -d

# Verificar servicios
docker compose ps

# Acceder a Grafana
# https://localhost (admin/rhinometric_v22)
```

**Requisitos**:
- Docker Engine 24.0+
- Docker Compose v2.20+
- 4 CPU, 8 GB RAM mínimo
- 50 GB disco

---

## ��� Documentación

### Manuales de Usuario
- ��� [Manual de Usuario (Español)](docs/user-guides/MANUAL_DE_USUARIO.md) - 217 líneas, 11 secciones
- ��� [User Manual (English)](docs/user-guides/USER_MANUAL_EN.md) - 217 líneas, 11 secciones

### Documentación Técnica
- ��� [Resumen de Características](FEATURES_OVERVIEW.md) - Comparativa de ediciones
- ���️ [Arquitectura del Sistema](docs/architecture/SYSTEM_ARCHITECTURE_ES.md) - Diagramas y flujos de datos
- ��� [Guía de Instalación Linux](INSTALACION_LINUX.md)
- ��� [Guía de Instalación macOS](INSTALACION_MACOS.md)
- ��� [Guía de Instalación Windows](INSTALACION_WINDOWS.md)

---

## ���️ Stack Tecnológico

| Componente | Versión | Puerto | Propósito |
|------------|---------|--------|-----------|
| **Grafana** | 10.2.0 | 3000 | Visualización y UI |
| **Prometheus** | 2.48.0 | 9090 | Métricas y TSDB |
| **Loki** | 2.9.3 | 3100 | Agregación de logs |
| **Tempo** | 2.3.1 | 3200 | Trazas distribuidas |
| **Alertmanager** | 0.26.0 | 9093 | Routing de alertas |
| **PostgreSQL** | 16 | 5432 | Metadata storage |
| **Redis** | 7.2 | 6379 | Cache y sesiones |
| **Traefik** | 2.10 | 80/443 | Reverse proxy + TLS |
| **AI Anomaly Engine** | Custom | 8085 | Detección de anomalías |
| **Dashboard Builder** | Custom | 8001 | Constructor de dashboards |
| **License Server** | Custom | 8000 | Validación de licencias |

---

## ��� Comparativa de Ediciones

| Característica | Starter | Professional | Enterprise |
|----------------|---------|--------------|------------|
| **Precio** | $49/mes | $199/mes | Personalizado |
| **Hosts Monitoreados** | 10 | 50 | Ilimitado |
| **Métricas (Prometheus)** | ✅ | ✅ | ✅ |
| **Logs (Loki)** | ✅ | ✅ | ✅ |
| **Trazas (Tempo)** | ❌ | ✅ | ✅ |
| **Dashboards Pre-configurados** | 5 | 10+ | 20+ |
| **AI Anomaly Detection** | ❌ | ✅ Básico | ✅ Avanzado |
| **Dashboard Builder UI** | ❌ | ✅ | ✅ |
| **Report Generator** | ❌ | ✅ | ✅ |
| **Branding Personalizado** | Logo | Logo + Colores | White-label |
| **Retención de Datos** | 7 días | 15 días | 90+ días |
| **Alertas por Email** | ✅ | ✅ | ✅ |
| **Alta Disponibilidad (HA)** | ❌ | ❌ | ✅ (99.9% SLA) |
| **Soporte** | Community | Email (48h) | Teléfono + SLA |

**Trial Gratuito**: 30 días con todas las funcionalidades desbloqueadas

---

## ��� Características Principales

### ��� Monitoreo Unificado
- **Métricas**: Prometheus con scraping cada 15 segundos
- **Logs**: Loki con agregación centralizada y LogQL
- **Trazas**: Tempo con distributed tracing (OpenTelemetry)
- **Dashboards**: 10+ pre-configurados (System, App Performance, AI Anomalies, etc.)

### ��� Inteligencia Artificial (v2.5.0)
- **Detección de Anomalías**: Isolation Forest (implementado y funcional)
- **Métricas Monitorizadas**: CPU, memoria, disco, red, errores HTTP
- **Alertas Automáticas**: Basadas en anomalías detectadas
- **Dashboard Dedicado**: 4 paneles (detecciones totales, anomalías activas, modelos entrenados, score)

**En Roadmap** (Q1 2025):
- ⏳ ARIMA para forecasting de capacidad
- ⏳ Auto-tuning de umbrales
- ⏳ Modelos personalizables por métrica

### ��� Alertas y Notificaciones (v2.5.0)
**Implementado**:
- ✅ **Email**: SMTP configurado con templates HTML branded

**En Roadmap** (Q1 2025):
- ⏳ Slack integration
- ⏳ PagerDuty integration
- ⏳ Microsoft Teams integration
- ⏳ Webhooks personalizados

**Funcionalidades Actuales**:
- ✅ Agrupamiento inteligente de alertas
- ✅ Silences para mantenimiento programado
- ✅ Templates reutilizables
- ✅ Routing básico por severidad

### ��� Seguridad y Autenticación (v2.5.0)
**Implementado**:
- ✅ TLS 1.3 end-to-end (Traefik)
- ✅ Autenticación básica Grafana (usuario/contraseña)
- ✅ API keys para servicios
- ✅ Secrets en variables de entorno
- ✅ Network isolation (Docker networks)

**En Roadmap** (Q1-Q2 2025):
- ⏳ RBAC (Role-Based Access Control)
- ⏳ LDAP/Active Directory integration
- ⏳ SSO (SAML, OAuth 2.0)
- ⏳ Audit logs avanzados
- ⏳ Compliance dashboards (SOC 2, ISO 27001)

### ��� Report Generator (v2.5.0)
- ✅ Generación de reportes ejecutivos en PDF/HTML
- ✅ Programación automática (semanal/mensual)
- ✅ Métricas clave: uptime, incidencias, tendencias
- ✅ Distribución por email

### ��� Enterprise Branding (v2.5.0)
**Personalización Disponible**:
- ✅ Landing page (logo, colores, texto)
- ✅ Grafana theme (logo sidebar, colores)
- ✅ Email templates (Alertmanager)
- ✅ MOTD (SSH/console login)
- ✅ HTTP headers (`X-Powered-By`)

**Niveles por Edición**:
- **Starter**: Logo únicamente
- **Professional**: Logo + paleta de colores
- **Enterprise**: White-label completo (sin referencias a "Rhinometric")

---

## ��� Despliegue

### Requisitos Mínimos
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disco**: 50 GB SSD
- **Red**: 1 Gbps
- **OS**: Ubuntu 22.04 LTS, Debian 12, RHEL 9

### Despliegue en Producción
```bash
# Clonar repo privado (acceso requerido)
git clone https://github.com/Rafael2712/mi-proyecto.git
cd mi-proyecto/deploy/prod

# Configurar entorno
cp .env.prod.example .env.prod
# Editar .env.prod con valores de producción

# Iniciar stack
docker compose -f docker-compose-prod.yml up -d

# Verificar despliegue
./scripts/verify-prod.sh

# Ver logs
docker compose -f docker-compose-prod.yml logs -f
```

**Incluye**:
- ✅ HAProxy para load balancing
- ✅ PostgreSQL con replicación
- ✅ Backups automáticos
- ✅ TLS con certificados Let's Encrypt
- ✅ Monitoreo del stack de monitoreo

---

## �� Configuración

### Variables de Entorno Clave
```bash
# Grafana
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=changeme

# PostgreSQL
POSTGRES_PASSWORD=strongpassword

# Prometheus
PROMETHEUS_RETENTION_TIME=15d

# AI Anomaly Detection
AI_ANOMALY_ENABLED=true
AI_ANOMALY_MODEL=isolation_forest

# License
LICENSE_KEY=TRIAL-30DAYS-XXXXX
```

### Personalización de Branding
```bash
# Logo (SVG recomendado)
cp /path/to/logo.svg nginx/html/assets/logo.svg

# Colores (variables CSS)
# Editar nginx/html/index.html
--brand-primary: #1E3A8A;
--brand-secondary: #10B981;
```

---

## ��� Testing

### Smoke Test (Demo Stack)
```bash
cd deploy/demo/scripts
./smoke-test.sh
```

**Verifica**:
- ✅ Todos los containers running
- ✅ Prometheus targets UP
- ✅ Grafana datasources conectados
- ✅ AI Anomaly metrics expuestas
- ✅ Dashboards accesibles

### Verification (Producción)
```bash
cd deploy/prod/scripts
./verify-prod.sh
```

---

## ��� Soporte

### Canales Oficiales

| Canal | Uso | Tiempo de Respuesta |
|-------|-----|---------------------|
| **Email** | rafael.canelon@rhinometric.com | Todas las ediciones | < 48h (Pro/Enterprise: < 4h) |
| **GitHub Issues** | https://github.com/Rafael2712/rhinometric-overview/issues | Community | Mejor esfuerzo |
| **Documentación** | https://docs.rhinometric.com | 24/7 | Inmediato |

### Recursos Adicionales
- ��� **Documentación Completa**: https://docs.rhinometric.com (próximamente)
- ��� **Community Forum**: https://community.rhinometric.com (próximamente)
- ��� **Blog Técnico**: https://blog.rhinometric.com (próximamente)
- ��� **Bug Reports**: GitHub Issues

---

## ��� Licencia

**Rhinometric Enterprise** es software propietario.

- ✅ **Trial**: 30 días gratuitos (todas las features)
- ��� **Licencia Comercial**: Requerida para uso en producción
- ��� **Contacto Comercial**: rafael.canelon@rhinometric.com

**Licenciamiento**:
- Por número de hosts monitorizados
- Soporte incluido según edición
- Actualizaciones de seguridad garantizadas
- Sin vendor lock-in (exportación de datos garantizada)

---

## ���️ Roadmap

### Q1 2025
- ⏳ RBAC y control de acceso granular
- ⏳ LDAP/Active Directory integration
- ⏳ Slack + PagerDuty + Teams integrations
- ⏳ ARIMA forecasting para capacidad
- ⏳ Mobile app (iOS + Android)

### Q2 2025
- ⏳ SSO (SAML, OAuth 2.0, Okta)
- ⏳ APM (Application Performance Monitoring)
- ⏳ RUM (Real User Monitoring)
- ⏳ Network Performance Monitoring
- ⏳ Kubernetes operator

### Q3 2025
- ⏳ Multi-cloud monitoring (AWS, Azure, GCP)
- ⏳ Chaos engineering integration
- ⏳ Auto-remediation workflows
- ⏳ Compliance dashboards (SOC 2, ISO 27001, HIPAA)

---

## ��� Contribuciones

Este es un proyecto propietario. Las contribuciones son bienvenidas mediante:
1. Pull Requests al repo público (documentación, ejemplos)
2. Issues con bugs reports o feature requests
3. Discusiones en GitHub Discussions

**Guías de Contribución**: Ver [CONTRIBUTING.md](CONTRIBUTING.md) (próximamente)

---

## ��� Casos de Uso

### 1. Infraestructura On-Premise
- Monitorizar 50+ servidores físicos/virtuales
- Alertas de capacidad (disco, CPU, memoria)
- Dashboards ejecutivos para IT managers

### 2. Microservicios en Kubernetes
- Distributed tracing entre servicios
- Log aggregation de pods
- Anomaly detection en request rates

### 3. DevOps CI/CD
- Monitorizar pipelines Jenkins/GitLab CI
- Métricas de deployment frequency
- Alertas de builds fallidos

### 4. Compliance & Auditoría
- Retención de logs (90+ días)
- Audit trails de cambios
- Reportes ejecutivos mensuales

---

## ❓ FAQ

**P: ¿Rhinometric es open source?**  
R: No. Rhinometric Enterprise es software propietario. Utilizamos componentes open source (Prometheus, Grafana, Loki, Tempo) pero nuestros módulos de IA, branding y licencias son propietarios.

**P: ¿Puedo usar Rhinometric en producción sin licencia?**  
R: Solo con la licencia trial de 30 días. Después requieres licencia comercial.

**P: ¿Qué datos envía Rhinometric a servidores externos?**  
R: **Ninguno**. Rhinometric es 100% on-premise. Solo se conecta a internet para validación inicial de licencia (opcional modo offline disponible).

**P: ¿Soportan alta disponibilidad (HA)?**  
R: Sí, en la edición Enterprise. Incluye HAProxy, PostgreSQL con replicación y Grafana cluster.

**P: ¿Puedo exportar mis datos si cambio de plataforma?**  
R: Sí. Todos los datos están en formatos estándar (Prometheus TSDB, PostgreSQL). Garantizamos exportación completa.

**P: ¿Funciona la IA sin conexión a internet?**  
R: Sí. El motor de AI Anomaly Detection es 100% local, no requiere APIs externas.

---

## �� Contacto

**Contacto Comercial**: rafael.canelon@rhinometric.com  
**Soporte Técnico**: rafael.canelon@rhinometric.com  
**Licencias**: rafael.canelon@rhinometric.com

**GitHub**: https://github.com/Rafael2712/rhinometric-overview  
**Documentación**: https://docs.rhinometric.com (próximamente)

---

<p align="center">
  <strong>��� Desarrollado por el equipo Rhinometric</strong><br>
  <sub>Plataforma de observabilidad empresarial líder en IA y automatización</sub>
</p>

<p align="center">
  <a href="mailto:rafael.canelon@rhinometric.com">Contacto Comercial</a> •
  <a href="https://github.com/Rafael2712/rhinometric-overview/issues">Reportar Bug</a> •
  <a href="https://github.com/Rafael2712/rhinometric-overview/discussions">Discusiones</a>
</p>

---

**© 2024 Rhinometric Team - Todos los derechos reservados**
