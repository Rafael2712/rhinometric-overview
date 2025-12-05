# 🚀 RHINOMETRIC v2.2.0 - Enterprise Observability Platform

**Plataforma completa de observabilidad on-premise con dashboards enterprise, sostenibilidad, IA y reportes automáticos**

[![Version](https://img.shields.io/badge/version-2.2.0-blue)](https://github.com/Rafael2712/rhinometric-overview)
[![License](https://img.shields.io/badge/license-Enterprise-green)](LICENSE)
[![GDPR](https://img.shields.io/badge/GDPR-Compliant-success)](https://gdpr.eu/)
[![ENS](https://img.shields.io/badge/ENS-Compatible-success)](https://www.ccn-cert.cni.es/es/series-ccn-stic/800-guia-esquema-nacional-de-seguridad.html)

---

## 📋 Índice

- [Novedades v2.2.0](#-novedades-v220)
- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Instalación Rápida](#-instalación-rápida)
- [Dashboards Enterprise](#-dashboards-enterprise)
- [VeriVerde: Monitoreo de Sostenibilidad](#-veriverde-monitoreo-de-sostenibilidad)
- [Backup y Restauración](#-backup-y-restauración)
- [IA: Detección de Anomalías](#-ia-detección-de-anomalías)
- [Reportes Automáticos](#-reportes-automáticos)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Documentación](#-documentación)
- [Requisitos](#-requisitos)
- [Soporte](#-soporte)

---

## 🎉 Novedades v2.2.0

### ✨ Nuevas Características Principales

1. **🎨 4 Dashboards Enterprise Pre-cargados**
   - **Executive Overview:** Métricas clave para directivos
   - **Infrastructure & Containers:** Monitoreo técnico de recursos
   - **Applications & APIs:** Latencia, errores y rendimiento
   - **VeriVerde Insights:** Sostenibilidad y eficiencia energética

2. **🌱 VeriVerde: Monitoreo de Sostenibilidad (ESG)**
   - Consumo energético en tiempo real
   - Cálculo de emisiones de CO₂
   - Porcentaje de energía renovable
   - Score de eficiencia operacional
   - Compatible con certificaciones verdes

3. **💾 Sistema de Backup Automático**
   - CLI `rmetricctl` para gestión de backups
   - Backups programados (diarios/semanales)
   - Restauración selectiva por componente
   - Validación de integridad (checksums)

4. **🤖 Detección de Anomalías con IA (Local)**
   - Machine Learning on-premise (sin nube)
   - Algoritmos: Isolation Forest, Z-score
   - Análisis de CPU, memoria, latencia, errores
   - Alertas automáticas

5. **📊 Reportes Ejecutivos Automáticos**
   - Generación de PDF profesionales
   - Envío automático por email
   - Resúmenes ejecutivos narrativos
   - Recomendaciones inteligentes

### 🔧 Mejoras Técnicas

- **20 servicios** (4 nuevos en v2.2.0)
- **Recursos optimizados:** ~4.0 vCPUs, ~7GB RAM
- **Red actualizada:** `172.22.0.0/16`
- **Prometheus v2.2:** Scraping de nuevos servicios
- **100% GDPR/ENS compliant:** Sin dependencias cloud

---

## ✅ Características

### Core Observability

- ✅ **Métricas:** Prometheus 2.53.0 (retención 7 días)
- ✅ **Logs:** Loki 3.0.0
- ✅ **Traces:** Tempo 2.6.0
- ✅ **Visualización:** Grafana 10.4.0 con dashboards enterprise
- ✅ **Alertas:** Alertmanager 0.27.0

### Infraestructura

- ✅ **Licencias:** FastAPI v2 + PostgreSQL 15 + Redis 7.2
- ✅ **UI de Licencias:** Vue.js 3 (puerto 8092)
- ✅ **Telemetría:** OpenTelemetry Collector 0.91.0
- ✅ **API Proxy:** Conector universal para APIs externas

### Exporters

- ✅ **Sistema:** node-exporter 1.7.0, cAdvisor 0.49.1
- ✅ **Red:** blackbox-exporter 0.25.0
- ✅ **Base de Datos:** postgres-exporter 0.15.0
- ✅ **Sostenibilidad:** VeriVerde Exporter (nuevo v2.2.0)

### Nuevos en v2.2.0

- ✅ **rhinometric-veriverde:** Métricas de energía y CO₂
- ✅ **rhinometric-ai-anomaly:** Detección ML local
- ✅ **rhinometric-backup:** Backups automatizados
- ✅ **rhinometric-report:** Reportes PDF/Email

### Compliance & Seguridad

- ✅ **100% On-Premise:** No hay llamadas a servicios cloud
- ✅ **GDPR:** Soberanía de datos en servidor propio
- ✅ **ENS:** Compatible con Esquema Nacional de Seguridad (España)
- ✅ **Backups encriptados:** Opcional con `rmetricctl`

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    RHINOMETRIC v2.2.0 ENTERPRISE                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  TIER 1: LICENSE & DATA                                         │
│  ├─ license-server-v2 (FastAPI + PostgreSQL + Redis)            │
│  └─ license-ui (Vue.js 3)                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  TIER 2: OBSERVABILITY CORE                                     │
│  ├─ Prometheus 2.53.0 (métricas)                                │
│  ├─ Loki 3.0.0 (logs)                                           │
│  ├─ Tempo 2.6.0 (traces)                                        │
│  └─ Grafana 10.4.0 (visualización + 4 dashboards)               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  TIER 3: TELEMETRY & CONNECTIVITY                               │
│  ├─ OpenTelemetry Collector                                     │
│  └─ API Proxy (conector universal)                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  TIER 4: EXPORTERS                                              │
│  ├─ node-exporter (sistema)                                     │
│  ├─ cAdvisor (contenedores)                                     │
│  ├─ blackbox-exporter (endpoints HTTP)                          │
│  └─ postgres-exporter (base de datos)                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  TIER 5: NEW v2.2.0 SERVICES ✨                                 │
│  ├─ rhinometric-veriverde (sostenibilidad/energía)              │
│  ├─ rhinometric-ai-anomaly (ML local)                           │
│  ├─ rhinometric-backup (backups automáticos)                    │
│  └─ rhinometric-report (reportes PDF)                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  TIER 6: FRONTEND                                               │
│  ├─ Grafana UI (http://localhost:3000)                          │
│  ├─ License UI (http://localhost:8092)                          │
│  └─ Nginx reverse proxy                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de Datos

```
Aplicación → OTEL Collector → Prometheus/Loki/Tempo → Grafana
                                     ↓
                              AI Anomaly Detector
                                     ↓
                              Report Generator → Email PDF
```

---

## 🚀 Instalación Rápida

### Prerrequisitos

- Docker 24.0+ y Docker Compose 2.20+
- 8 GB RAM mínimo (16 GB recomendado)
- 50 GB espacio en disco
- Linux/macOS/Windows con WSL2

### Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/Rafael2712/rhinometric-overview.git
cd rhinometric-overview/infrastructure/mi-proyecto

# 2. (Opcional) Configurar variables de entorno
cp .env.example .env
nano .env

# 3. Iniciar stack
docker compose -f docker-compose-v2.2.0.yml up -d

# 4. Verificar
docker compose ps
```

**Tiempo de inicio:** ~2 minutos

### Acceso

| Servicio | URL | Usuario | Password |
|----------|-----|---------|----------|
| **Grafana** | http://localhost:3000 | `admin` | `admin` |
| **Prometheus** | http://localhost:9090 | - | - |
| **License UI** | http://localhost:8092 | - | - |
| **Alertmanager** | http://localhost:9093 | - | - |

### Verificación Post-Instalación

```bash
# Todos los servicios deben estar "healthy"
docker compose ps

# Ver logs
docker compose logs -f

# Verificar Grafana (debe mostrar 4 dashboards)
curl http://localhost:3000/api/search
```

---

## 🎨 Dashboards Enterprise

RHINOMETRIC v2.2.0 incluye **4 dashboards profesionales pre-cargados** al instalar.

### 1. Executive Overview

**Audiencia:** CTO, Directores, Management

**Contenido:**
- 📊 Servicios activos (gauge)
- 🚨 Alertas activas (contador)
- 💻 Uso de recursos (CPU/memoria)
- 📋 Estado de servicios (tabla)
- ℹ️ Información de compliance GDPR/ENS

**Acceso:** Grafana → Dashboards → Rhinometric → `01 - Executive Overview`

### 2. Infrastructure & Containers

**Audiencia:** SysAdmins, DevOps, Ingenieros

**Contenido:**
- 🖥️ CPU por core
- 💾 Memoria (total/disponible)
- 💿 Espacio en disco
- 🌐 Tráfico de red (RX/TX)
- 🐳 Uso de CPU/memoria por contenedor

**Acceso:** Grafana → Dashboards → Rhinometric → `02 - Infrastructure & Containers`

### 3. Applications & APIs

**Audiencia:** Desarrolladores, QA, Product Owners

**Contenido:**
- ⏱️ Latencia de APIs (P95/P99)
- 🔢 Request rate por endpoint
- ❌ Tasa de errores (4xx/5xx)
- 📈 SLA/disponibilidad

**Acceso:** Grafana → Dashboards → Rhinometric → `03 - Applications & APIs`

### 4. VeriVerde Insights ⭐

**Audiencia:** Responsables de Sostenibilidad, ESG Officers

**Contenido:**
- ⚡ Consumo energético actual (kWh)
- 🌡️ Temperatura de sala/rack (°C)
- 🌿 Porcentaje de energía renovable
- 🏭 Emisiones de CO₂ (kg)
- 📊 Score de eficiencia (0-100)
- 📉 Tendencias históricas

**Acceso:** Grafana → Dashboards → Rhinometric → `04 - VeriVerde Insights`

---

## 🌱 VeriVerde: Monitoreo de Sostenibilidad

### ¿Por qué VeriVerde?

- **Compliance ESG:** Reporting obligatorio para empresas grandes
- **Certificaciones verdes:** ISO 14001, Carbon Neutral, etc.
- **Ahorro de costos:** Identificar ineficiencias energéticas
- **Imagen corporativa:** Transparencia en políticas verdes

### Métricas Exportadas

| Métrica | Descripción | Unidad |
|---------|-------------|--------|
| `rhinometric_energy_kwh` | Consumo energético | kWh |
| `rhinometric_room_temperature_c` | Temperatura ambiente | °C |
| `rhinometric_renewable_percent` | Energía renovable | % |
| `rhinometric_co2_emissions_kg` | Emisiones CO₂ | kg |
| `rhinometric_efficiency_score` | Score de eficiencia | 0-100 |

### Configuración

En `docker-compose-v2.2.0.yml`:

```yaml
rhinometric-veriverde:
  environment:
    # Porcentaje de energía renovable de tu proveedor
    VERIVERDE_RENEWABLE_PERCENT: "35"  # España: ~35% renovable
    
    # Factor de emisiones por región
    CO2_FACTOR_KG_PER_KWH: "0.200"  # España: 0.200 kg/kWh
    
    # (Opcional) URLs de sensores reales
    VERIVERDE_ENERGY_SENSOR_URL: "http://sensor.local/energy"
    VERIVERDE_TEMP_SENSOR_URL: "http://sensor.local/temp"
```

**Factores de CO₂ por región:**

| País | Factor (kg/kWh) |
|------|----------------|
| 🇪🇸 España | 0.200 |
| 🇩🇪 Alemania | 0.350 |
| 🇫🇷 Francia | 0.055 |
| 🇵🇱 Polonia | 0.650 |
| 🇳🇴 Noruega | 0.020 |

### Integración con Sensores Reales

VeriVerde soporta APIs de sensores externos:

**Formato JSON esperado (energía):**
```json
{
  "energy_kwh": 3.45,
  "timestamp": "2025-01-30T12:00:00Z"
}
```

**Formato JSON esperado (temperatura):**
```json
{
  "temperature_celsius": 22.5,
  "timestamp": "2025-01-30T12:00:00Z"
}
```

---

## 💾 Backup y Restauración

### CLI: rmetricctl

**Instalar globalmente:**

```bash
sudo ln -s $(pwd)/scripts/rmetricctl /usr/local/bin/rmetricctl
chmod +x /usr/local/bin/rmetricctl
```

### Comandos Principales

```bash
# Crear backup completo
rmetricctl backup

# Backup selectivo
rmetricctl backup --component prometheus grafana

# Listar backups
rmetricctl list

# Restaurar
rmetricctl restore backup_20250130_120000 --yes

# Limpiar backups antiguos (>30 días)
rmetricctl clean
```

### Backup Automático

El servicio `rhinometric-backup` ejecuta backups programados:

- **Horario por defecto:** Diario a las 2 AM
- **Retención:** 30 días
- **Componentes:** Prometheus, Loki, Tempo, Grafana, PostgreSQL

**Configuración:**

```yaml
rhinometric-backup:
  environment:
    BACKUP_SCHEDULE: "0 2 * * *"  # Cron expression
    BACKUP_RETENTION_DAYS: 30
    BACKUP_COMPONENTS: "prometheus,loki,tempo,grafana,postgres"
```

**Verificar logs:**

```bash
docker logs -f rhinometric-backup
```

**Más información:** Ver [`docs/BACKUP_AND_RESTORE.md`](docs/BACKUP_AND_RESTORE.md)

---

## 🤖 IA: Detección de Anomalías

### Características

- **100% Local:** Sin envío de datos a la nube
- **Algoritmos ML:** Isolation Forest, Z-score
- **Métricas analizadas:** CPU, memoria, latencia, errores
- **Actualización:** Cada 5 minutos
- **Lookback:** 24 horas de datos históricos

### API de Anomalías

**Endpoint:** `http://localhost:8085/anomalies`

**Respuesta:**
```json
{
  "anomalies": [
    {
      "timestamp": "2025-01-30T14:23:45",
      "metric": "CPU Usage",
      "current_value": 95.3,
      "mean_value": 45.2,
      "std_dev": 12.4,
      "anomaly_score": -0.87,
      "severity": "high",
      "message": "Anomaly detected in CPU Usage: 8/10 recent points"
    }
  ],
  "count": 1,
  "last_check": "2025-01-30T14:25:00"
}
```

### Configuración

```yaml
rhinometric-ai-anomaly:
  environment:
    PROMETHEUS_URL: "http://prometheus:9090"
    CHECK_INTERVAL_SECONDS: "300"  # 5 minutos
    LOOKBACK_HOURS: "24"
    ANOMALY_THRESHOLD: "0.7"
```

### Integración con Grafana

Las anomalías se pueden visualizar en Grafana usando:

1. **Datasource:** Loki (anomalías se envían como logs)
2. **Query:** `{container="rhinometric-ai-anomaly"} |= "anomaly_detected"`
3. **Panel tipo:** Table o Logs

---

## 📊 Reportes Automáticos

### Características

- **Formatos:** PDF y HTML
- **Entrega:** Email automático
- **Frecuencias:** Diaria, semanal, mensual
- **Contenido:**
  - Resumen ejecutivo narrativo
  - Métricas clave (servicios, alertas, disponibilidad)
  - Estado detallado de servicios
  - Anomalías detectadas por IA
  - Recomendaciones automáticas

### Configuración de Email

```yaml
rhinometric-report:
  environment:
    REPORT_SCHEDULE: "weekly"  # daily, weekly, monthly
    
    # SMTP Configuration
    SMTP_HOST: "smtp.zoho.eu"
    SMTP_PORT: "587"
    SMTP_USER: "rafael.canelon@rhinometric.com"
    SMTP_PASSWORD: "${SMTP_PASSWORD}"
    
    # Destinatarios (separados por coma)
    REPORT_RECIPIENTS: "cto@empresa.com,ops@empresa.com"
```

### Ejemplo de Reporte

**Asunto:** `RHINOMETRIC - Informe Semanal - 30/01/2025`

**Contenido PDF:**
1. **Header:** Logo RHINOMETRIC + fecha
2. **Resumen Ejecutivo:** Párrafo narrativo del estado
3. **Métricas Clave:** 3 tarjetas (servicios, alertas, disponibilidad)
4. **Estado de Servicios:** Tabla con CPU/memoria
5. **Anomalías IA:** Lista de anomalías detectadas
6. **Recomendaciones:** Acciones sugeridas
7. **Footer:** Versión + compliance

**Más información:** Ver [`docs/REPORTS.md`](docs/REPORTS.md)

---

## ⚙️ Configuración

### Variables de Entorno

Crear archivo `.env`:

```bash
# PostgreSQL
POSTGRES_PASSWORD=rhinometric_secure_password

# Redis
REDIS_PASSWORD=redis_secure_password

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin_secure_password

# SMTP (para reportes)
SMTP_PASSWORD=your_smtp_password
REPORT_RECIPIENTS=ops@empresa.com,cto@empresa.com

# VeriVerde (sostenibilidad)
RENEWABLE_PERCENT=35
CO2_FACTOR=0.233

# Reportes
REPORT_SCHEDULE=weekly
```

### Personalización de Recursos

Si tienes limitaciones de recursos, ajustar `docker-compose-v2.2.0.yml`:

```yaml
services:
  prometheus:
    deploy:
      resources:
        limits:
          cpus: '0.5'  # Reducir de 0.8 a 0.5
          memory: 1024M  # Reducir de 1536M a 1024M
```

### Añadir APIs Externas

Ver documentación del módulo `api-proxy` (heredado de v2.1.0).

---

## 🎯 Uso

### 1. Acceder a Grafana

```bash
# Abrir navegador
open http://localhost:3000

# Login
Usuario: admin
Password: admin

# Navegar a:
Dashboards → Rhinometric → [Elegir dashboard]
```

### 2. Ver Métricas en Prometheus

```bash
open http://localhost:9090

# Ejemplo de queries:
up  # Estado de servicios
rhinometric_energy_kwh  # Consumo energético
rate(http_requests_total[5m])  # Request rate
```

### 3. Gestionar Licencias

```bash
open http://localhost:8092

# UI de gestión de licencias
# - Crear licencias trial (30 días)
# - Activar licencias permanentes
# - Ver estadísticas de uso
```

### 4. Crear Backup Manual

```bash
cd ~/mi-proyecto/infrastructure/mi-proyecto
./scripts/rmetricctl backup

# Salida:
# ✅ Backup complete: 6/6 components
# 📊 Total size: 5563.37 MB
# 📍 Location: ~/rhinometric_backups/backup_20250130_120000
```

### 5. Generar Reporte Manual

```bash
docker exec rhinometric-report python reporter.py

# Reporte se enviará por email a destinatarios configurados
```

### 6. Ver Anomalías Detectadas

```bash
curl http://localhost:8085/anomalies | jq .

# O en Grafana:
# Explore → Loki → {container="rhinometric-ai-anomaly"}
```

---

## 📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| [`README.md`](README.md) | Este archivo (visión general) |
| [`docs/BACKUP_AND_RESTORE.md`](docs/BACKUP_AND_RESTORE.md) | Guía completa de backups |
| [`docs/REPORTS.md`](docs/REPORTS.md) | Configuración de reportes |
| [`rhinometric-veriverde/README.md`](rhinometric-veriverde/README.md) | Documentación VeriVerde |
| [`CHANGELOG-v2.2.md`](CHANGELOG-v2.2.md) | Notas de la versión |

---

## 💻 Requisitos

### Mínimos

- **CPU:** 4 cores
- **RAM:** 8 GB
- **Disco:** 50 GB
- **SO:** Linux/macOS/Windows con WSL2
- **Docker:** 24.0+
- **Docker Compose:** 2.20+

### Recomendados (Producción)

- **CPU:** 8 cores
- **RAM:** 16 GB
- **Disco:** 200 GB SSD
- **Red:** 1 Gbps
- **Backup externo:** NAS o almacenamiento remoto

### Puertos Utilizados

| Puerto | Servicio |
|--------|----------|
| 80, 443 | Nginx |
| 3000 | Grafana |
| 3100 | Loki |
| 3200, 4317, 4318 | Tempo |
| 5000 | License Server |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 8080 | cAdvisor |
| 8081 | API Proxy |
| 8085 | AI Anomaly |
| 8092 | License UI |
| 9090 | Prometheus |
| 9093 | Alertmanager |
| 9100 | Node Exporter |
| 9115 | Blackbox Exporter |
| 9187 | Postgres Exporter |
| 9200 | VeriVerde |

---

## 🆘 Soporte

### Contacto

- **Email:** rafael.canelon@rhinometric.com
- **GitHub:** [Rafael2712/rhinometric-overview](https://github.com/Rafael2712/rhinometric-overview)

### Troubleshooting Rápido

**Problema: Servicios no arrancan**

```bash
# Ver logs
docker compose logs

# Verificar recursos
docker stats

# Reiniciar
docker compose down
docker compose up -d
```

**Problema: Grafana vacío (sin dashboards)**

```bash
# Verificar provisioning
docker exec rhinometric-grafana ls -la /etc/grafana/provisioning/dashboards/json

# Debe mostrar:
# 01-executive-overview.json
# 02-infrastructure-containers.json
# 03-applications-apis.json
# 04-veriverde-insights.json
```

**Problema: Backup falla**

```bash
# Verificar permisos
ls -la ~/rhinometric_data_v2.2/

# Corregir ownership
sudo chown -R $(whoami):$(whoami) ~/rhinometric_data_v2.2/
```

**Problema: No llegan reportes por email**

```bash
# Verificar logs
docker logs rhinometric-report

# Test SMTP
telnet smtp.zoho.eu 587
```

---

## 📈 Roadmap

### v2.3.0 (Q2 2025)

- [ ] Panel de control centralizado (Web UI)
- [ ] Integración con Slack/Teams
- [ ] Multi-tenancy (múltiples clientes)
- [ ] Dashboards personalizables sin código
- [ ] Exportación de métricas a Excel/CSV

### v3.0.0 (Q3 2025)

- [ ] Clustering de Prometheus (HA)
- [ ] Distributed tracing mejorado
- [ ] AI predictiva (forecasting)
- [ ] Mobile app (iOS/Android)
- [ ] SSO/SAML support

---

## 📄 Licencia

RHINOMETRIC v2.2.0 Enterprise Edition

Copyright © 2025 Rafael Canelón

**Licencia de uso:** Enterprise (ver `LICENSE`)

---

## 🙏 Agradecimientos

- **Prometheus:** The Prometheus Authors
- **Grafana:** Grafana Labs
- **Loki & Tempo:** Grafana Labs
- **OpenTelemetry:** CNCF
- **FastAPI:** Sebastián Ramírez
- **Vue.js:** Evan You

---

## 🎯 Quick Start Commands

```bash
# Clonar e instalar
git clone https://github.com/Rafael2712/rhinometric-overview.git
cd rhinometric-overview/infrastructure/mi-proyecto
docker compose -f docker-compose-v2.2.0.yml up -d

# Acceder
open http://localhost:3000  # Grafana (admin/admin)
open http://localhost:8092  # License UI

# Backup
./scripts/rmetricctl backup

# Ver logs
docker compose logs -f

# Detener
docker compose down
```

---

**RHINOMETRIC v2.2.0 Enterprise Edition**  
Plataforma Completa de Observabilidad On-Premise  
✅ GDPR Compliant | ✅ ENS Compatible | ✅ 100% Open Source Core

**Made with ❤️ by Rafael Canelón**
