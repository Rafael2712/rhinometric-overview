# ��� Rhinometric - Enterprise Observability Platform

![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)
![License](https://img.shields.io/badge/license-Proprietary-red.svg)
![Status](https://img.shields.io/badge/status-Production%20Ready-green.svg)
![Docker](https://img.shields.io/badge/docker-required-blue.svg)
[![CI](https://github.com/Rafael2712/rhinometric-overview/actions/workflows/ci.yml/badge.svg)](https://github.com/Rafael2712/rhinometric-overview/actions/workflows/ci.yml)

**Plataforma de Observabilidad Empresarial 100% Containerizada**

Rhinometric es una solución completa de monitoreo, métricas, logs y trazas distribuidas diseñada para despliegue on-premise, cloud o híbrido.

---

## ��� Tabla de Contenidos

- [Quick Start](#-quick-start)
- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalación Detallada](#-instalación-detallada)
- [Arquitecturas Soportadas](#-arquitecturas-soportadas)
- [Documentación](#-documentación)
- [Soporte](#-soporte)

---

## ��� Quick Start

### Instalación Rápida (Recomendada)

#### Linux/macOS
```bash
# 1. Descargar última versión
wget https://github.com/Rafael2712/rhinometric-overview/releases/latest/download/rhinometric-v2.1.0-stable.tar.gz

# 2. Extraer
tar -xzf rhinometric-v2.1.0-stable.tar.gz
cd rhinometric-overview

# 3. Configurar credenciales
cp .env.example .env
nano .env  # Editar GF_SECURITY_ADMIN_PASSWORD, POSTGRES_PASSWORD, LICENSE_KEY

# 4. Instalar
chmod +x scripts/install.sh
./scripts/install.sh
```

#### Windows (PowerShell)
```powershell
# 1. Descargar desde Releases
# https://github.com/Rafael2712/rhinometric-overview/releases/latest

# 2. Extraer .zip
Expand-Archive rhinometric-v2.1.0-stable.zip -DestinationPath .
cd rhinometric-overview

# 3. Configurar credenciales
Copy-Item .env.example .env
notepad .env  # Editar passwords

# 4. Instalar
.\scripts\install.ps1
```

### Acceso al Sistema

Una vez instalado (3-5 minutos):

- **Grafana**: http://localhost:3000
  - Usuario: `admin`
  - Password: **Definido en tu archivo `.env`** (`GF_SECURITY_ADMIN_PASSWORD`)
  - ⚠️ **Cambie la contraseña en el primer acceso**

- **API Connector**: http://localhost:8091
  - Gestión de APIs externas

- **Prometheus**: http://localhost:9090
  - Queries y métricas directas

**Licencia Trial**: 15 días automáticos desde instalación

---

## ✨ Características

### Observabilidad Completa (3 Pilares)

- **��� Métricas**: Prometheus + 15 Dashboards Grafana pre-configurados
- **��� Logs**: Loki + Promtail para agregación centralizada
- **��� Trazas**: Tempo para distributed tracing
- **��� Correlación**: Drilldown automático métricas → logs → traces

### Stack Tecnológico

| Componente | Tecnología | Puerto | Descripción |
|------------|------------|--------|-------------|
| **Visualización** | Grafana 10.x | 3000 | Dashboards + Alertas |
| **Métricas** | Prometheus 2.x | 9090 | Time-series DB |
| **Logs** | Loki + Promtail | 3100 | Agregación logs |
| **Trazas** | Tempo | 3200 | Distributed tracing |
| **Base Datos** | PostgreSQL 15 | 5432 | Persistencia |
| **Cache** | Redis 7 | 6379 | Alto rendimiento |
| **API Connector** | Vue.js 3 | 8091 | UI gestión APIs |
| **License Server** | FastAPI | 8090 | Sistema licencias |
| **Exporters** | 8+ exporters | varios | Métricas sistema |

### Novedades v2.1.0

- ✅ **15 Dashboards** listos para producción
- ✅ **API Connector UI**: Interfaz Vue.js para gestión de APIs externas
- ✅ **Drilldown Completo**: Prometheus → Loki → Tempo
- ✅ **License Server**: Sistema de licencias con emails automáticos (PDFs)
- ✅ **Instaladores Multiplataforma**: Scripts bash/PowerShell
- ✅ **CI/CD Pipeline**: Validación automática de configuraciones
- ✅ **Terraform IaC**: Deploy Oracle Cloud/AWS/Azure/GCP
- ✅ **Arquitectura Híbrida**: On-premise + Cloud
- ✅ **Alta Disponibilidad**: 99.9% uptime

---

## ��� Requisitos

### Hardware Mínimo
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disco**: 50 GB SSD

### Hardware Recomendado (Producción)
- **CPU**: 8+ cores
- **RAM**: 16+ GB
- **Disco**: 200+ GB SSD (NVMe preferido)

### Software
- **Docker**: 24.0+ ([Instalar Docker](https://docs.docker.com/engine/install/))
- **Docker Compose**: v2.20+ (incluido con Docker Desktop)
- **SO**: Linux, macOS, Windows 10/11

### Puertos Necesarios
```
3000  - Grafana
8091  - API Connector UI
8090  - License Server
9090  - Prometheus
3100  - Loki
3200  - Tempo
5432  - PostgreSQL
6379  - Redis
```

---

## ��� Instalación Detallada

### 1. Clonar Repositorio (Desarrollo)

```bash
git clone https://github.com/Rafael2712/rhinometric-overview.git
cd rhinometric-overview
```

### 2. Configurar Variables de Entorno

El archivo `.env.example` contiene todas las configuraciones necesarias:

```bash
cp .env.example .env
```

**Variables críticas a modificar**:

```ini
# GRAFANA - Cambiar password
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=TuPasswordSeguro2025!

# POSTGRESQL - Cambiar password
POSTGRES_PASSWORD=TuPasswordDB2025!

# LICENCIA (proporcionada al registrarse)
LICENSE_KEY=RHINO-TRIAL-2025-XXXXXXXXXXXX

# SMTP (Opcional - para notificaciones email)
SMTP_HOST=smtp.zoho.eu
SMTP_USER=rafael.canelon@rhinometric.com
SMTP_FROM=rafael.canelon@rhinometric.com
SMTP_PASSWORD=YourAppPassword
```

### 3. Ejecutar Instalador

El instalador:
- ✅ Valida Docker/Compose instalados
- ✅ Crea directorios de datos
- ✅ Despliega servicios
- ✅ Verifica instalación

```bash
# Linux/macOS
./scripts/install.sh

# Windows
.\scripts\install.ps1
```

### 4. Verificar Instalación

```bash
# Ver contenedores activos
docker ps

# Logs de servicios
docker compose -f deploy/docker-compose.yml logs -f

# Salud de Grafana
curl http://localhost:3000/api/health
```

---

## ���️ Arquitecturas Soportadas

### 1️⃣ On-Premise (100% Local)

```
┌─────────────────────────────────────┐
│   Rhinometric Stack (1 servidor)    │
│  Grafana + Prometheus + Loki + DB   │
│         localhost:3000              │
└─────────────────────────────────────┘
```

**Uso**: Desarrollo, demos, pruebas de concepto

### 2️⃣ Cloud (Oracle/AWS/Azure/GCP)

```
┌─────────────────────────────────────┐
│      Oracle Cloud Always Free       │
│   VM.Standard.A1.Flex (4 OCPU)      │
│  Rhinometric + SSL/TLS (Let's Enc.) │
│    https://monitoring.tudominio.com │
└─────────────────────────────────────┘
```

**Uso**: Producción pequeña/mediana empresa

��� [Guía Completa Cloud Deployment](CLOUD_DEPLOYMENT_GUIDE.md)

### 3️⃣ Híbrido (On-Prem + Cloud)

```
┌──────────────┐         ┌──────────────┐
│   Oficina    │◄───────►│    Cloud     │
│  Prometheus  │  VPN    │   Grafana    │
│   (local)    │         │ (centraliza) │
└──────────────┘         └──────────────┘
```

**Uso**: Multi-sede, alta disponibilidad, cumplimiento normativo

��� [Guía Arquitectura Híbrida](HYBRID_ARCHITECTURE_GUIDE.md)

---

## ��� Documentación

### Guías de Instalación por Sistema Operativo
- [��� Linux](INSTALACION_LINUX.md) - Ubuntu, Debian, RHEL, CentOS
- [��� macOS](INSTALACION_MACOS.md) - Intel y Apple Silicon (M1/M2)
- [��� Windows](INSTALACION_WINDOWS.md) - Windows 10/11 Pro/Enterprise

### Guías Técnicas
- [��� Documentación Completa v2.1.0](README_v2.1.0.md)
- [☁️ Cloud Deployment (Oracle/AWS/Azure)](CLOUD_DEPLOYMENT_GUIDE.md)
- [��� Arquitectura Híbrida](HYBRID_ARCHITECTURE_GUIDE.md)
- [��� Sistema de Licencias](LICENSE_SERVER_CLARIFICATION.md)
- [��� Informe Ejecución v2.1.0](EXECUTION-TEST-REPORT-v2.1.0.md)

### Changelog
- [��� Novedades v2.1.0](CHANGELOG-v2.1.md)

---

## ��� Casos de Uso

### Desarrollo/Staging
- Monitoreo de microservicios en desarrollo
- Depuración con trazas distribuidas
- Validación de SLOs antes de producción

### Producción (PyME)
- Monitoreo 24/7 de aplicaciones críticas
- Alertas proactivas (email/Slack/PagerDuty)
- Dashboards ejecutivos

### Enterprise
- Federación multi-sede (oficinas/DCs)
- Cumplimiento GDPR/SOC2 (logs auditables)
- Integración ITSM (ServiceNow/Jira)

---

## ��� Soporte

### Soporte Técnico
- ��� **Email**: rafael.canelon@rhinometric.com
- ⏰ **Horario**: Lunes-Viernes, 9:00-18:00 CET
- ��� **Reportar Issues**: [GitHub Issues](https://github.com/Rafael2712/rhinometric-overview/issues)

### Licencias Comerciales
- ��� **Ventas**: rafael.canelon@rhinometric.com
- ��� **Trial**: 15 días automáticos
- ��� **Empresas**: Licencias perpetuas/anuales disponibles

---

## ��� Licencia

**Propietaria** - Rhinometric® es una marca registrada.

- ✅ **Trial**: 15 días uso completo sin restricciones
- ✅ **Desarrollo**: Permitido uso no comercial
- ❌ **Redistribución**: Prohibida sin autorización
- ❌ **Comercial**: Requiere licencia de pago

Contactar: rafael.canelon@rhinometric.com

---

## ��� Enlaces

- [��� Quick Start](#-quick-start)
- [��� Descargar Última Versión](https://github.com/Rafael2712/rhinometric-overview/releases/latest)
- [��� Documentación Completa](README_v2.1.0.md)
- [☁️ Guía Cloud](CLOUD_DEPLOYMENT_GUIDE.md)
- [��� Reportar Issues](https://github.com/Rafael2712/rhinometric-overview/issues)

---

**Última actualización**: 29 de Octubre 2025  
**Versión**: 2.1.0-stable  
**Autor**: Rafael Canel  
**GitHub**: https://github.com/Rafael2712/rhinometric-overview
