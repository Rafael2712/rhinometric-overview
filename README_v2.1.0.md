# 🦏 RHINOMETRIC v2.1.0 - Plataforma de Observabilidad ON-PREMISE

[![License](https://img.shields.io/badge/license-Trial%2030%20días-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.1.0-green.svg)](CHANGELOG.md)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

---

## ⚠️ ACLARACIÓN IMPORTANTE: 100% ON-PREMISE

**Rhinometric NO ES una solución cloud/SaaS**. Es una plataforma **self-hosted** que se instala y ejecuta **completamente en TU infraestructura**:

- ✅ **Tus servidores locales** (on-premise físicos)
- ✅ **Tus máquinas virtuales** (VMware, Hyper-V, VirtualBox)
- ✅ **Tu propia cuenta cloud** (AWS EC2, Azure VM, Google Compute, Oracle Cloud - que TÚ pagas y controlas)
- ✅ **Tu laptop/PC de desarrollo** (Windows, Linux, macOS)

**❌ NO ES:**
- ❌ **SaaS** (no hay rhinometric.com con login)
- ❌ **Cloud-hosted** (no hospedamos nada por ti)
- ❌ **Managed service** (no gestionamos tu infraestructura)

**TUS DATOS NUNCA SALEN DE TU INFRAESTRUCTURA**. Rhinometric es código que ejecutas tú mismo usando Docker Compose.

---

## 📊 ¿Qué es Rhinometric?

Plataforma **completa de observabilidad** que unifica **métricas + logs + traces** en una solución autocontenida, lista para instalar en **10-15 minutos**.

### ✨ Características Principales v2.1.0

- 🏠 **100% Self-Hosted** - Cero dependencias externas
- 📦 **17 Contenedores Docker** - Stack completo pre-configurado
- 📊 **15 Dashboards Grafana** - System Overview, APIs externas, RED metrics, Database perf
- 🔌 **API Connector UI** - Monitorea APIs externas (Stripe, AWS, OpenAI) sin código (Vue.js 3)
- 🔍 **Drilldown Completo** - Click en métrica → Ver logs → Ver traces automáticamente
- 🔄 **Auto-Update** - Script de actualización con backup/rollback inteligente
- 🔒 **Modo Trial** - 30 días, endpoints de licencias protegidos
- 🌍 **Cross-Platform** - Windows 10/11, Linux (Ubuntu/Debian/CentOS), macOS Monterey+

---

## 🚀 Instalación Rápida (10-15 minutos)

### Opción A: Un Comando (Linux/macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/Rafael2712/mi-proyecto/main/install-rhinometric.sh | sudo bash
```

### Opción B: Manual (Windows/Linux/macOS)

```bash
# 1. Requisitos previos
# - Docker Desktop 4.25+ (Windows/macOS) o Docker Engine 24+ (Linux)
# - 4 GB RAM disponible (8 GB recomendado)
# - 20 GB disco libre

# 2. Clonar repositorio
git clone https://github.com/Rafael2712/mi-proyecto.git
cd mi-proyecto/infrastructure/mi-proyecto/rhinometric-trial-v2.1.0-universal

# 3. Configurar credenciales
cp .env.example .env
nano .env  # Cambiar GRAFANA_PASSWORD, POSTGRES_PASSWORD, REDIS_PASSWORD

# 4. Levantar stack (primera vez descarga 2.5 GB de imágenes Docker)
docker compose -f docker-compose-v2.1.0.yml up -d

# 5. Esperar 2 minutos y verificar
docker ps | grep rhinometric
# Debes ver 17 contenedores con estado "Up" o "Up (healthy)"

# 6. Acceder
curl http://localhost:3000/api/health
# Respuesta: {"database":"ok","version":"10.4.0"}
```

**Acceso Web**:
- 🎨 **Grafana**: http://localhost:3000 (admin / tu_password)
- 🔌 **API Connector**: http://localhost:8091
- 📊 **Prometheus**: http://localhost:9090

---

## 📚 Documentación Completa

| Documento | Descripción | Idiomas |
|-----------|-------------|---------|
| [**RESUMEN_EJECUTIVO_v2.1.0.md**](docs/RESUMEN_EJECUTIVO_v2.1.0.md) | Visión general, arquitectura, casos de uso, ROI | 🇪🇸 🇬🇧 🇵🇹 🇮🇹 |
| [**MANUAL_INSTALACION_WINDOWS_v2.1.0.md**](docs/MANUAL_INSTALACION_WINDOWS_v2.1.0.md) | Guía paso a paso para Windows 10/11 | 🇪🇸 🇬🇧 🇵🇹 🇮🇹 |
| [**MANUAL_INSTALACION_MACOS_v2.1.0.md**](docs/MANUAL_INSTALACION_MACOS_v2.1.0.md) | Guía paso a paso para macOS Monterey+ | 🇪🇸 🇬🇧 🇵🇹 🇮🇹 |
| [**MANUAL_INSTALACION_LINUX_v2.1.0.md**](docs/MANUAL_INSTALACION_LINUX_v2.1.0.md) | Guía para Ubuntu/Debian/CentOS/Fedora | 🇪🇸 🇬🇧 🇵🇹 🇮🇹 |
| [**MANUAL_USUARIO_v2.1.0.md**](docs/MANUAL_USUARIO_v2.1.0.md) | Uso completo de dashboards, API Connector, alertas, drilldown | 🇪🇸 🇬🇧 🇵🇹 🇮🇹 |

---

## 🏗️ Arquitectura ON-PREMISE (17 Contenedores)

```
┌─────────────────────────────────────────────────────────────┐
│            TU INFRAESTRUCTURA LOCAL/PRIVADA                 │
│         (NO hay comunicación con servidores externos)       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         RHINOMETRIC v2.1.0 (Docker Compose)          │  │
│  │                                                       │  │
│  │  TIER 1: Visualización                               │  │
│  │    └─ Grafana 10.4.0 (Puerto 3000)                   │  │
│  │                                                       │  │
│  │  TIER 2: Observabilidad Core                         │  │
│  │    ├─ Prometheus v2.53.0 (Métricas)                  │  │
│  │    ├─ Loki v3.0.0 (Logs agregados)                   │  │
│  │    └─ Tempo v2.6.0 (Traces distribuidos)             │  │
│  │                                                       │  │
│  │  TIER 3: Bases de Datos                              │  │
│  │    ├─ PostgreSQL 15.10 (Metadatos, configuración)    │  │
│  │    └─ Redis 7.2 (Cache, sesiones)                    │  │
│  │                                                       │  │
│  │  TIER 4: API Connector ⭐ NUEVO v2.1.0                │  │
│  │    ├─ API Connector UI (Vue.js 3, Puerto 8091)       │  │
│  │    └─ API Proxy (Node.js Express, 38 métricas)       │  │
│  │                                                       │  │
│  │  TIER 5: Exporters & Collectors (7 contenedores)     │  │
│  │    ├─ node-exporter (Host metrics)                   │  │
│  │    ├─ cadvisor (Container metrics)                   │  │
│  │    ├─ postgres-exporter (DB metrics)                 │  │
│  │    ├─ blackbox-exporter (Endpoint probes)            │  │
│  │    ├─ otel-collector (Traces collector)              │  │
│  │    ├─ promtail (Log shipper)                         │  │
│  │    └─ alertmanager (Alert routing)                   │  │
│  │                                                       │  │
│  │  TIER 6: Infraestructura                             │  │
│  │    ├─ Nginx (Reverse proxy, SSL termination)         │  │
│  │    └─ License Server (Trial validation)              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  📁 Datos persistidos en: ./data/ (volúmenes Docker)        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 Capacidades Probadas

| Métrica | Valor | Contexto |
|---------|-------|----------|
| **Métricas recolectadas** | 1,008 | Cross-platform verificadas (Win/Linux/macOS) |
| **Dashboards** | 15 | 12 completamente funcionales |
| **APIs externas** | Ilimitadas | Monitorea Stripe, AWS, OpenAI, etc. |
| **Scrape interval** | 15-30s | Configurable |
| **Retención métricas** | 15 días | Configurable a 30/60/90 días |
| **Retención logs** | 30 días | Configurable |
| **Retención traces** | 7 días | Configurable |
| **Cache hit rate** | 80-90% | Redis TTL 5 min |
| **CPU usage (idle)** | ~1.5 vCPU | Stack completo |
| **CPU usage (load)** | ~3.7 vCPU | Con tráfico activo |
| **RAM usage** | ~6.2 GB | Optimizable a 4 GB |
| **Disk I/O** | ~2 GB/día | Con retención actual |

---

## 🎯 Casos de Uso Ideales

### ✅ Perfecto Para:

1. **SaaS Companies (5-500 empleados)**
   - Monitorean integraciones críticas (Stripe, SendGrid, Twilio, AWS)
   - **ROI**: 60-80% ahorro vs DataDog ($3.5k/mes) o NewRelic ($4k/mes)

2. **E-commerce (Shopify, WooCommerce, Magento)**
   - Vigilan pasarelas de pago (PayPal, Stripe, MercadoPago)
   - Downtime = pérdida directa de revenue
   - **ROI**: Detectan problemas 5-10 minutos antes

3. **Fintech & Crypto**
   - APIs financieras (bancos, exchanges, KYC providers)
   - Cumplimiento regulatorio (logs 90+ días configurables)
   - **ROI**: Compliance + ahorro $10k+/mes

4. **Agencias de Desarrollo**
   - 1 instancia Rhinometric por cliente
   - Instalación < 30 min, dashboards white-label
   - **ROI**: Venden monitoreo como servicio adicional

5. **DevOps Teams**
   - Reemplazan stack Prometheus + Grafana + Loki + Tempo (días de setup manual)
   - **ROI**: 10-20 horas/mes ahorradas en mantenimiento

### ❌ NO Recomendado Para:

- ❌ Empresas Fortune 100 con equipos 50+ SREs (necesitan más customización)
- ❌ Aplicaciones móviles nativas iOS/Android (sin backend para instrumentar)
- ❌ IoT masivo (millones de dispositivos, escala diferente)
- ❌ Compliance extremo (HIPAA Nivel 4, PCI-DSS Nivel 1) - falta auditoría externa
- ❌ Presupuesto < $200/mes (trial gratis, pero soporte es paid)

---

## 🔧 Comandos Útiles

```bash
# Ver estado de contenedores
docker ps | grep rhinometric

# Ver logs de Grafana
docker logs rhinometric-grafana --tail 100 -f

# Reiniciar todos los servicios
docker compose -f docker-compose-v2.1.0.yml restart

# Detener (datos se conservan)
docker compose -f docker-compose-v2.1.0.yml stop

# Iniciar después de detener
docker compose -f docker-compose-v2.1.0.yml start

# Verificar health
curl http://localhost:3000/api/health
curl http://localhost:9090/-/healthy
curl http://localhost:3100/ready

# Ver uso de recursos
docker stats --no-stream | grep rhinometric
```

---

## 🔄 Auto-Update (Con Backup Automático)

```bash
# Verificar si hay actualizaciones
./auto-update.sh --check-only

# Actualizar (crea backup antes, rollback si falla)
./auto-update.sh

# Actualizar a versión específica
./auto-update.sh --version=2.2.0

# Rollback manual
./auto-update.sh --rollback
```

---

## 🐛 Troubleshooting

### ❌ "Cannot connect to Docker daemon"

```bash
# Windows: Abre Docker Desktop y espera 30s
# Linux: sudo systemctl start docker
# macOS: open -a Docker
```

### ❌ "Port already in use"

```bash
# Ver qué proceso usa el puerto
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows

# Cambiar puerto en docker-compose-v2.1.0.yml
```

### ❌ Dashboards muestran "No Data"

```bash
# Espera 2-3 minutos después de docker compose up
# Genera tráfico de prueba
./generate-api-activity.sh

# Verifica que Prometheus scrape funciona
curl http://localhost:9090/api/v1/query?query=up
```

---

## 📊 15 Dashboards Incluidos

1. **System Overview** - Estado general de 17 contenedores, CPU, RAM, disco
2. **External APIs Monitoring** ⭐ - Health, latency, cache hits de APIs externas
3. **Application Performance (RED)** - Request rate, error rate, duration
4. **Database Performance** - PostgreSQL slow queries, connections, cache hit ratio
5. **Redis Performance** - Hit rate, commands/sec, memory usage
6. **Nginx Performance** - Requests/sec, response time, active connections
7. **OTEL Collector Metrics** - Traces recibidos/exportados, logs procesados
8. **Node Exporter** - CPU, RAM, disco, network del host
9. **Docker Containers** - Detalle de todos los containers
10. **Logs Explorer** - Búsqueda LogQL en tiempo real
11. **Traces Explorer** - Visualización de traces distribuidos
12. **Alerts Overview** - Todas las alertas configuradas
13. **License Server** - Uso de licencias (solo admin)
14. **Blackbox Exporter** - Monitoring de endpoints externos
15. **Demo Drilldown** - Ejemplo completo Metrics → Logs → Traces

---

## 🆘 Soporte

- 📖 **Documentación**: Carpeta `docs/` en este repositorio
- 🐙 **Issues**: https://github.com/Rafael2712/mi-proyecto/issues
- 📧 **Email comercial**: support@rhinometric.io
- 💬 **Discussions**: https://github.com/Rafael2712/mi-proyecto/discussions

---

## 📝 Licencia

**Trial**: 30 días gratuitos, todas las funcionalidades habilitadas  
**Comercial**: Contactar support@rhinometric.io para licencia permanente

---

## 🗂️ Estructura del Repositorio

```
mi-proyecto/
├── infrastructure/
│   └── mi-proyecto/
│       ├── rhinometric-trial-v2.1.0-universal/
│       │   ├── docker-compose-v2.1.0.yml   # ⭐ Stack completo
│       │   ├── .env.example                # Configuración
│       │   ├── config/
│       │   │   ├── grafana/
│       │   │   │   ├── dashboards/         # 15 dashboards JSON
│       │   │   │   └── provisioning/
│       │   │   ├── prometheus/
│       │   │   │   └── prometheus.yml      # Scrape configs
│       │   │   ├── loki/
│       │   │   └── tempo/
│       │   ├── api-proxy/
│       │   │   ├── server.js               # Node.js API monitoring
│       │   │   ├── Dockerfile
│       │   │   └── package.json
│       │   ├── api-connector-ui/           # Vue.js 3 UI
│       │   ├── auto-update.sh              # Update con backup
│       │   ├── validate-v2.1.sh            # Health checks
│       │   └── generate-api-activity.sh    # Test data generator
│       └── docs/
│           ├── RESUMEN_EJECUTIVO_v2.1.0.md
│           ├── MANUAL_INSTALACION_WINDOWS_v2.1.0.md
│           ├── MANUAL_INSTALACION_MACOS_v2.1.0.md
│           ├── MANUAL_INSTALACION_LINUX_v2.1.0.md
│           ├── MANUAL_USUARIO_v2.1.0.md
│           ├── en/                         # English translations
│           ├── pt/                         # Portuguese translations
│           └── it/                         # Italian translations
└── README_v2.1.0.md                        # ⭐ Este archivo
```

---

**✅ Rhinometric v2.1.0 - 100% ON-PREMISE, 0% Cloud Dependencia**

**Instalación**: 10-15 minutos | **Containers**: 17 | **Dashboards**: 15 | **Métricas**: 1,008

---

*Última actualización: Octubre 28, 2025*
