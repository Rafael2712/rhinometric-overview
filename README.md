# 🚀 Rhinometric - Enterprise Observability Platform

![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)
![License](https://img.shields.io/badge/license-Proprietary-red.svg)
![Status](https://img.shields.io/badge/status-Production%20Ready-green.svg)
![Docker](https://img.shields.io/badge/docker-required-blue.svg)

**Plataforma de Observabilidad Empresarial 100% Containerizada**

Rhinometric es una solución completa de monitoreo, métricas, logs y trazas distribuidas diseñada para despliegue on-premise, cloud o híbrido.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Quick Start](#-quick-start)
- [Arquitecturas Soportadas](#-arquitecturas-soportadas)
- [Documentación](#-documentación)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Casos de Uso](#-casos-de-uso)
- [Soporte](#-soporte)

---

## ✨ Características

### Observabilidad Completa (3 Pilares)

- **📊 Métricas**: Prometheus + 15 Dashboards Grafana pre-configurados
- **📝 Logs**: Loki + Promtail para agregación centralizada
- **🔍 Trazas**: Tempo para distributed tracing
- **🔗 Correlación**: Drilldown automático métricas → logs → traces

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
| **Exporters** | 8+ exporters | varios | Métricas sistema |

### Características v2.1.0

- ✅ **15 Dashboards** listos para producción
- ✅ **API Connector UI**: Interfaz Vue.js para gestión de APIs externas
- ✅ **Drilldown Completo**: Prometheus → Loki → Tempo
- ✅ **Auto-Updates**: Actualización automática con rollback
- ✅ **License Server**: Sistema de licencias trial (15 días)
- ✅ **Terraform IaC**: Deploy Oracle Cloud/AWS/Azure/GCP
- ✅ **Arquitectura Híbrida**: On-premise + Cloud
- ✅ **Multi-Sede**: Federación de métricas
- ✅ **Alta Disponibilidad**: 99.9% uptime

---

## 🚀 Quick Start

### Instalación 1-Comando (Linux/macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/Rafael2712/rhinometric-overview/main/install.sh | bash
```

### Instalación Manual

```bash
# 1. Descargar paquete trial
wget https://github.com/Rafael2712/rhinometric-overview/releases/download/v2.1.0/rhinometric-trial-v2.1.0-universal.tar.gz

# 2. Extraer
tar -xzf rhinometric-trial-v2.1.0-universal.tar.gz
cd rhinometric-trial-v2.1.0-universal

# 3. Configurar
cp .env.example .env
nano .env  # Editar passwords

# 4. Desplegar
docker compose -f docker-compose-v2.1.0.yml up -d

# 5. Verificar
docker ps
curl http://localhost:3000/api/health
```

### Acceso

- **Grafana**: http://localhost:3000
  - Usuario: `admin`
  - Password: `RhinometricSecure2025!`
  
- **API Connector**: http://localhost:8091
  - Gestión de APIs externas
  
- **Prometheus**: http://localhost:9090
  - Queries y métricas

**Licencia Trial**: 15 días automáticos desde instalación

---

## 🏗️ Arquitecturas Soportadas

### 1️⃣ On-Premise (100% Local)

```
┌─────────────────────────────────┐
│   Tu Data Center                │
│   ├── PostgreSQL (datos)        │
│   ├── Redis (cache)             │
│   ├── 17 contenedores Docker    │
│   └── Todo en tu infraestructura│
└─────────────────────────────────┘
```

**Caso de uso**: Cumplimiento GDPR, HIPAA, datos sensibles

**Documentación**: [README_v2.1.0.md](README_v2.1.0.md)

### 2️⃣ Cloud (100% Nube)

```
┌─────────────────────────────────┐
│   Oracle Cloud / AWS / Azure    │
│   ├── VM (2 vCPU, 4-12 GB)      │
│   ├── Stack completo            │
│   └── IP pública                │
│   Costo: $0-58/mes              │
└─────────────────────────────────┘
```

**Caso de uso**: Startups, SaaS, multi-región

**Proveedores soportados**:
- ✅ **Oracle Cloud**: FREE TIER ($0/mes, 12 GB RAM ARM)
- ✅ **AWS**: t3.medium (~$51/mes)
- ✅ **Azure**: Standard_B2s (~$58/mes)
- ✅ **GCP**: e2-medium (~$49/mes)

**Documentación**: [CLOUD_DEPLOYMENT_GUIDE.md](CLOUD_DEPLOYMENT_GUIDE.md)

### 3️⃣ Híbrido (On-Premise + Cloud)

#### Modelo A: Datos Local + Visualización Cloud

```
On-Premise (Datos)       →  Cloud (Dashboards)
├── PostgreSQL              ├── Grafana
├── Redis                   ├── Prometheus (agregador)
└── Prometheus Agent        └── Loki + Tempo
    └─ Remote Write ────────────→
```

**Caso de uso**: Banca, Healthcare (PCI-DSS, HIPAA)

#### Modelo B: Multi-Sede Federada

```
Sede Madrid      Sede Barcelona    Sede Valencia
├── Stack ──┐    ├── Stack ──┐     ├── Stack ──┐
            │                 │                 │
            └─────────────────┴─────────────────┘
                            ↓
                    Cloud (Dashboard CEO)
                    ├── Prometheus Federation
                    └── Grafana Multi-Tenant
```

**Caso de uso**: Retail (50 tiendas), Hospitales multi-sede

#### Modelo C: Cloud Bursting

```
Normal: 100% On-Premise (60% CPU)
Pico:   On-Premise + Cloud (auto-scaling)
```

**Caso de uso**: Black Friday, campañas marketing

**Documentación**: [HYBRID_ARCHITECTURE_GUIDE.md](HYBRID_ARCHITECTURE_GUIDE.md)

---

## 📚 Documentación

### Guías de Deployment

| Documento | Descripción | Tamaño |
|-----------|-------------|--------|
| [CLOUD_DEPLOYMENT_GUIDE.md](CLOUD_DEPLOYMENT_GUIDE.md) | Deploy en Oracle/AWS/Azure/GCP | 32 KB |
| [HYBRID_ARCHITECTURE_GUIDE.md](HYBRID_ARCHITECTURE_GUIDE.md) | Arquitecturas híbridas detalladas | 37 KB |
| [ORACLE_CLOUD_DEPLOYMENT.md](ORACLE_CLOUD_DEPLOYMENT.md) | Validación Oracle Cloud IaC | 15 KB |
| [README_v2.1.0.md](README_v2.1.0.md) | Documentación técnica completa | 15 KB |

### Reportes Técnicos

| Documento | Descripción |
|-----------|-------------|
| [CHANGELOG-v2.1.md](CHANGELOG-v2.1.md) | Novedades v2.1.0 |
| [EXECUTION-TEST-REPORT-v2.1.0.md](EXECUTION-TEST-REPORT-v2.1.0.md) | Pruebas de validación |

### Terraform Infrastructure as Code

```bash
terraform/
├── oracle-cloud/    # Oracle Cloud Infrastructure (OCI)
├── aws/            # Amazon Web Services
├── azure/          # Microsoft Azure
└── gcp/            # Google Cloud Platform
```

**Características Terraform**:
- ✅ Multi-cloud (Oracle, AWS, Azure, GCP)
- ✅ Auto-instalación (cloud-init)
- ✅ Networking completo (VPC, subnets, firewall)
- ✅ SSL/TLS pre-configurado
- ✅ 1 comando: `terraform apply`

---

## ⚙️ Requisitos

### Hardware Mínimo

| Componente | On-Premise | Cloud VM |
|------------|------------|----------|
| **CPU** | 2 cores | 2 vCPU |
| **RAM** | 4 GB | 4-12 GB |
| **Disco** | 50 GB SSD | 100 GB |
| **Red** | 100 Mbps | 1 Gbps |

### Software

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **OS**: Ubuntu 22.04 / Debian 11 / RHEL 8+ / macOS / Windows WSL2

### Puertos

| Puerto | Servicio | Firewall |
|--------|----------|----------|
| 3000 | Grafana | Público |
| 8091 | API Connector | Público |
| 9090 | Prometheus | Interno |
| 5432 | PostgreSQL | Interno |
| 6379 | Redis | Interno |

---

## 📦 Instalación

### Opción 1: Instalador Automático

```bash
# Linux/macOS
curl -fsSL https://raw.githubusercontent.com/Rafael2712/rhinometric-overview/main/install.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/Rafael2712/rhinometric-overview/main/install.ps1 | iex
```

### Opción 2: Docker Compose

```bash
# 1. Clonar
git clone https://github.com/Rafael2712/rhinometric-overview.git
cd rhinometric-overview

# 2. Configurar
cp .env.example .env
nano .env

# 3. Deploy
docker compose up -d

# 4. Verificar
docker ps
curl http://localhost:3000/api/health
```

### Opción 3: Terraform (Cloud)

```bash
# Oracle Cloud
cd terraform/oracle-cloud
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Configurar credenciales OCI

terraform init
terraform plan
terraform apply -auto-approve

# Output: Public IP + URLs
```

**Tiempo estimado**: 5-15 minutos

---

## 💼 Casos de Uso

### 1. Banca y Finanzas

**Requisito**: PCI-DSS, transacciones en España

**Solución**: Híbrido (PostgreSQL local + Dashboards cloud)

**Beneficios**:
- ✅ Cumplimiento regulatorio
- ✅ Dashboards ejecutivos desde cualquier lugar
- ✅ Backup automático cloud

### 2. Healthcare (Hospitales)

**Requisito**: HIPAA, datos médicos protegidos

**Solución**: Multi-Sede federada

**Beneficios**:
- ✅ Historiales médicos 100% on-premise
- ✅ Analytics centralizados (datos anonimizados)
- ✅ Dashboard consolidado 3 hospitales

### 3. Retail Multi-Tienda

**Requisito**: 50 tiendas, inventario real-time

**Solución**: Federation (cada tienda + cloud CEO)

**Beneficios**:
- ✅ KPIs consolidados
- ✅ Comparativas Madrid vs Barcelona
- ✅ Alertas centralizadas

### 4. SaaS Startup

**Requisito**: Costos bajos, escalable

**Solución**: 100% Oracle Cloud Free Tier

**Beneficios**:
- ✅ $0/mes durante 12 meses
- ✅ 12 GB RAM ARM
- ✅ Deploy en 15 minutos

---

## 💰 Costos

### Comparativa Mensual

| Proveedor | Instancia | Costo/Mes | Free Tier |
|-----------|-----------|-----------|-----------|
| **Oracle Cloud** | VM.Standard.A1.Flex (ARM) | **$0** | 12 meses |
| **GCP** | e2-medium | $49 | $300 crédito |
| **AWS** | t3.medium | $51 | 12 meses t2.micro |
| **Azure** | Standard_B2s | $58 | $200 crédito |
| **On-Premise** | Servidor físico | $2,500* | - |

\* *CAPEX inicial + OPEX anual*

### ROI Híbrido (3 sedes, 3 años)

- **100% On-Premise**: $140,000
- **Híbrido**: $69,000
- **Ahorro**: **$71,000 (51%)**

---

## 🔒 Seguridad

### Características de Seguridad

- ✅ **Passwords**: Variables de entorno (`.env`)
- ✅ **TLS/SSL**: Certificados auto-firmados incluidos
- ✅ **Firewall**: Security Groups Terraform
- ✅ **VPN**: WireGuard para híbrido
- ✅ **Backup**: Automático diario
- ✅ **RBAC**: Grafana multi-tenant

### Cumplimiento Regulatorio

- ✅ **GDPR**: Datos en UE (eu-madrid-1)
- ✅ **HIPAA**: PHI on-premise
- ✅ **PCI-DSS**: Transacciones locales
- ✅ **SOC 2**: Logs inmutables (Loki)

---

## 📊 Performance

### Benchmarks

| Métrica | Valor | Configuración |
|---------|-------|---------------|
| **Métricas/seg** | 10,000 | Prometheus |
| **Logs/seg** | 5,000 | Loki |
| **Traces/seg** | 1,000 | Tempo |
| **Dashboards** | 15 | Grafana |
| **Retention** | 90 días | Default |
| **Latencia** | < 100ms | Queries |

### Escalabilidad

| Sedes | Métricas Totales | RAM Requerida | Costo Cloud |
|-------|------------------|---------------|-------------|
| 1 | 10K/seg | 4 GB | $49/mes |
| 3 | 30K/seg | 8 GB | $98/mes |
| 10 | 100K/seg | 16 GB | $196/mes |
| 50 | 500K/seg | 64 GB | $784/mes |

---

## 🛠️ Soporte

### Canales de Soporte

- **Documentación**: Este repositorio
- **Issues**: https://github.com/Rafael2712/rhinometric-overview/issues
- **Email**: rafael.canel@rhinometric.com
- **Licencias**: Contactar para licencia comercial

### Licencia Trial

- **Duración**: 15 días desde instalación
- **Limitaciones**: Marcas de agua en dashboards
- **Conversión**: Licencia comercial disponible
- **Renovación**: Contactar soporte

### Licencia Comercial

| Plan | Usuarios | Sedes | Precio/Mes |
|------|----------|-------|------------|
| **Startup** | 1-25 | 1 | $199 |
| **Business** | 26-100 | 3 | $499 |
| **Enterprise** | 101-500 | 10 | $999 |
| **Corporate** | 500+ | Ilimitado | Custom |

**Incluye**:
- ✅ Soporte 24/7
- ✅ Actualizaciones
- ✅ Dashboards custom
- ✅ Integración APIs
- ✅ Capacitación

---

## 📈 Roadmap

### v2.2.0 (Q1 2026)

- [ ] Multi-tenancy completo
- [ ] API GraphQL
- [ ] ML Anomaly Detection
- [ ] Kubernetes Operator
- [ ] Mobile App (iOS/Android)

### v3.0.0 (Q2 2026)

- [ ] eBPF tracing
- [ ] Edge computing
- [ ] Real-time AI insights
- [ ] Blockchain audit trail

---

## 🤝 Contribuir

Este es un repositorio **solo lectura** (documentación pública).

Para reportar bugs o solicitar features:
1. Abrir issue en: https://github.com/Rafael2712/rhinometric-overview/issues
2. Email: rafael.canel@rhinometric.com

---

## 📜 Licencia

**Propietario** - Rafael Canel © 2025

- ✅ Trial gratuito 15 días
- ✅ Uso comercial requiere licencia
- ✅ Documentación: MIT License
- ✅ Código fuente: Propietario

---

## 🎯 Quick Links

- [🚀 Quick Start](#-quick-start)
- [📚 Documentación Completa](README_v2.1.0.md)
- [☁️ Guía Cloud](CLOUD_DEPLOYMENT_GUIDE.md)
- [🔀 Arquitectura Híbrida](HYBRID_ARCHITECTURE_GUIDE.md)
- [🐛 Reportar Issues](https://github.com/Rafael2712/rhinometric-overview/issues)
- [💼 Licencias Comerciales](mailto:rafael.canel@rhinometric.com)

---

**Última actualización**: 28 de Octubre 2025  
**Versión**: 2.1.0  
**Autor**: Rafael Canel  
**GitHub**: https://github.com/Rafael2712/rhinometric-overview
