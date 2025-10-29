# ��� Rhinometric - Enterprise Observability Platform

> ��� **Languages:** [Español](README.md) | [English](README_EN.md)

![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)
![License](https://img.shields.io/badge/license-Proprietary-red.svg)
![Status](https://img.shields.io/badge/status-Production%20Ready-green.svg)
![Docker](https://img.shields.io/badge/docker-required-blue.svg)
[![CI](https://github.com/Rafael2712/rhinometric-overview/actions/workflows/ci.yml/badge.svg)](https://github.com/Rafael2712/rhinometric-overview/actions/workflows/ci.yml)

**100% Containerized Enterprise Observability Platform**

Rhinometric is a complete monitoring solution for metrics, logs, and distributed traces designed for on-premise, cloud, or hybrid deployment.

---

## ��� Table of Contents

- [Quick Start](#-quick-start)
- [Features](#-features)
- [Requirements](#-requirements)
- [Detailed Installation](#-detailed-installation)
- [Supported Architectures](#-supported-architectures)
- [Documentation](#-documentation)
- [Support](#-support)

---

## ��� Quick Start

### Fast Installation (Recommended)

#### Linux/macOS
```bash
# 1. Download latest version
wget https://github.com/Rafael2712/rhinometric-overview/releases/latest/download/rhinometric-v2.1.0-stable.tar.gz

# 2. Extract
tar -xzf rhinometric-v2.1.0-stable.tar.gz
cd rhinometric-overview

# 3. Configure credentials
cp .env.example .env
nano .env  # Edit GF_SECURITY_ADMIN_PASSWORD, POSTGRES_PASSWORD, LICENSE_KEY

# 4. Install
chmod +x scripts/install.sh
./scripts/install.sh
```

#### Windows (PowerShell)
```powershell
# 1. Download from Releases
# https://github.com/Rafael2712/rhinometric-overview/releases/latest

# 2. Extract .zip
Expand-Archive rhinometric-v2.1.0-stable.zip -DestinationPath .
cd rhinometric-overview

# 3. Configure credentials
Copy-Item .env.example .env
notepad .env  # Edit passwords

# 4. Install
.\scripts\install.ps1
```

### System Access

Once installed (3-5 minutes):

- **Grafana**: http://localhost:3000
  - User: `admin`
  - Password: **Defined in your `.env` file** (`GF_SECURITY_ADMIN_PASSWORD`)
  - ⚠️ **Change password on first login**

- **API Connector**: http://localhost:8091
  - External API management

- **Prometheus**: http://localhost:9090
  - Direct metrics queries

**Trial License**: 30 days automatic from installation

---

## ✨ Features

### Complete Observability (3 Pillars)

- **��� Metrics**: Prometheus + 15 pre-configured Grafana Dashboards
- **��� Logs**: Loki + Promtail for centralized aggregation
- **��� Traces**: Tempo for distributed tracing
- **��� Correlation**: Automatic drilldown metrics → logs → traces

### Tech Stack

| Component | Technology | Port | Description |
|-----------|------------|------|-------------|
| **Visualization** | Grafana 10.x | 3000 | Dashboards + Alerts |
| **Metrics** | Prometheus 2.x | 9090 | Time-series DB |
| **Logs** | Loki + Promtail | 3100 | Log aggregation |
| **Traces** | Tempo | 3200 | Distributed tracing |
| **Database** | PostgreSQL 15 | 5432 | Persistence |
| **Cache** | Redis 7 | 6379 | High performance |
| **API Connector** | Vue.js 3 | 8091 | API management UI |
| **License Server** | FastAPI | 8090 | License system |
| **Exporters** | 8+ exporters | various | System metrics |

### v2.1.0 New Features

- ✅ **15 Dashboards** production-ready
- ✅ **API Connector UI**: Vue.js interface for external API management
- ✅ **Complete Drilldown**: Prometheus → Loki → Tempo
- ✅ **License Server**: License system with automatic emails (PDFs)
- ✅ **Multi-platform Installers**: bash/PowerShell scripts
- ✅ **CI/CD Pipeline**: Automatic configuration validation
- ✅ **Terraform IaC**: Deploy Oracle Cloud/AWS/Azure/GCP
- ✅ **Hybrid Architecture**: On-premise + Cloud
- ✅ **High Availability**: 99.9% uptime

---

## ��� Requirements

### Minimum Hardware
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 50 GB SSD

### Recommended Hardware (Production)
- **CPU**: 8+ cores
- **RAM**: 16+ GB
- **Disk**: 200+ GB SSD (NVMe preferred)

### Software
- **Docker**: 24.0+ ([Install Docker](https://docs.docker.com/engine/install/))
- **Docker Compose**: v2.20+ (included with Docker Desktop)
- **OS**: Linux, macOS, Windows 10/11

### Required Ports
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

## �� Detailed Installation

### 1. Clone Repository (Development)

```bash
git clone https://github.com/Rafael2712/rhinometric-overview.git
cd rhinometric-overview
```

### 2. Configure Environment Variables

The `.env.example` file contains all necessary configurations:

```bash
cp .env.example .env
```

**Critical variables to modify**:

```ini
# GRAFANA - Change password
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=YourSecurePassword2025!

# POSTGRESQL - Change password
POSTGRES_PASSWORD=YourDBPassword2025!

# LICENSE (provided upon registration)
LICENSE_KEY=RHINO-TRIAL-2025-XXXXXXXXXXXX

# SMTP (Optional - for email notifications)
SMTP_HOST=smtp.zoho.eu
SMTP_USER=rafael.canelon@rhinometric.com
SMTP_FROM=rafael.canelon@rhinometric.com
SMTP_PASSWORD=YourAppPassword
```

### 3. Run Installer

The installer:
- ✅ Validates Docker/Compose installed
- ✅ Creates data directories
- ✅ Deploys services
- ✅ Verifies installation

```bash
# Linux/macOS
./scripts/install.sh

# Windows
.\scripts\install.ps1
```

### 4. Verify Installation

```bash
# View active containers
docker ps

# Service logs
docker compose -f deploy/docker-compose.yml logs -f

# Grafana health
curl http://localhost:3000/api/health
```

---

## ���️ Supported Architectures

### 1️⃣ On-Premise (100% Local)

```
┌─────────────────────────────────────┐
│   Rhinometric Stack (1 server)      │
│  Grafana + Prometheus + Loki + DB   │
│         localhost:3000              │
└─────────────────────────────────────┘
```

**Use case**: Development, demos, proof of concept

### 2️⃣ Cloud (Oracle/AWS/Azure/GCP)

```
┌─────────────────────────────────────┐
│      Oracle Cloud Always Free       │
│   VM.Standard.A1.Flex (4 OCPU)      │
│  Rhinometric + SSL/TLS (Let's Enc.) │
│    https://monitoring.yourdomain.com │
└─────────────────────────────────────┘
```

**Use case**: Small/medium enterprise production

��� [Complete Cloud Deployment Guide](CLOUD_DEPLOYMENT_GUIDE.md)

### 3️⃣ Hybrid (On-Prem + Cloud)

```
┌──────────────┐         ┌──────────────┐
│    Office    │◄───────►│    Cloud     │
│  Prometheus  │   VPN   │   Grafana    │
│   (local)    │         │ (centralize) │
└──────────────┘         └──────────────┘
```

**Use case**: Multi-site, high availability, regulatory compliance

��� [Hybrid Architecture Guide](HYBRID_ARCHITECTURE_GUIDE.md)

---

## ��� Documentation

### Installation Guides by Operating System
- [��� Linux](INSTALACION_LINUX.md) - Ubuntu, Debian, RHEL, CentOS
- [��� macOS](INSTALACION_MACOS.md) - Intel and Apple Silicon (M1/M2)
- [��� Windows](INSTALACION_WINDOWS.md) - Windows 10/11 Pro/Enterprise

### Bilingual Guides (Spanish/English)
- [��� Technical Guide for Connecting Applications](docs/USER_GUIDE_CONNECT_APPS.md) - DevOps, Integrators, IT Administrators
- [��� Institutional Public Sector Guide](docs/GUIDE_PUBLIC_SECTOR.md) - Municipalities, Public Companies, Institutions

### Technical Guides
- [��� Complete Documentation v2.1.0](README_v2.1.0.md)
- [☁️ Cloud Deployment (Oracle/AWS/Azure)](CLOUD_DEPLOYMENT_GUIDE.md)
- [��� Hybrid Architecture](HYBRID_ARCHITECTURE_GUIDE.md)
- [��� License System](LICENSE_SERVER_CLARIFICATION.md)
- [��� v2.1.0 Execution Report](EXECUTION-TEST-REPORT-v2.1.0.md)

### Changelog
- [��� v2.1.0 New Features](CHANGELOG-v2.1.md)

---

## ��� Use Cases

### Development/Staging
- Microservices monitoring in development
- Debugging with distributed traces
- SLO validation before production

### Production (SMB)
- 24/7 critical application monitoring
- Proactive alerts (email/Slack/PagerDuty)
- Executive dashboards

### Enterprise
- Multi-site federation (offices/DCs)
- GDPR/SOC2 compliance (auditable logs)
- ITSM integration (ServiceNow/Jira)

---

## ��� Support

### Technical Support
- ��� **Email**: rafael.canelon@rhinometric.com
- ⏰ **Schedule**: Monday-Friday, 9:00-18:00 CET
- ��� **Report Issues**: [GitHub Issues](https://github.com/Rafael2712/rhinometric-overview/issues)

### Commercial Licenses
- ��� **Sales**: rafael.canelon@rhinometric.com
- ��� **Trial**: 30 days automatic
- ��� **Enterprise**: Perpetual/annual licenses available

---

## ��� License

**Proprietary** - Rhinometric® is a registered trademark.

- ✅ **Trial**: 30 days full use without restrictions
- ✅ **Development**: Non-commercial use allowed
- ❌ **Redistribution**: Prohibited without authorization
- ❌ **Commercial**: Requires paid license

Contact: rafael.canelon@rhinometric.com

---

## ��� Links

- [��� Quick Start](#-quick-start)
- [��� Download Latest Version](https://github.com/Rafael2712/rhinometric-overview/releases/latest)
- [��� Complete Documentation](README_v2.1.0.md)
- [☁️ Cloud Guide](CLOUD_DEPLOYMENT_GUIDE.md)
- [��� Report Issues](https://github.com/Rafael2712/rhinometric-overview/issues)

---

**Last update**: October 29, 2025  
**Version**: 2.1.0-stable  
**Author**: Rafael Canel  
**GitHub**: https://github.com/Rafael2712/rhinometric-overview
