# 🚀 Rhinometric v2.1.0 Enterprise Edition

**Complete observability stack with GUI-based API connectivity, pre-loaded dashboards, and multi-platform support**

---

## ✨ What's New in v2.1.0

### 🎯 Enterprise Features

- **✅ GUI-Based API Connectivity** - Connect to external APIs without editing YAML files
- **✅ Pre-Loaded Enterprise Dashboards** - 8 professional dashboards with real KPIs
- **✅ OpenTelemetry Collector** - Production-grade telemetry (replaces telemetrygen)
- **✅ FastAPI License Server** - Async/await architecture (replaces Flask)
- **✅ One-Command Installation** - Universal installer for macOS, Linux, Windows WSL2
- **✅ Optimized Resources** - 30% CPU reduction, 32% RAM reduction vs v2.0.0
- **✅ 100% Healthchecks** - All 16 services with automated health monitoring

### 🆕 New Components

| Component | Purpose | Port |
|-----------|---------|------|
| **API Proxy** | Universal connector for external APIs with Prometheus metrics | 8090 |
| **License Server v2** | FastAPI-based license management with async support | 5000 |
| **OpenTelemetry Collector** | OTLP/Jaeger receiver, exports to Tempo/Prometheus | 4319, 4320, 8889 |

---

## 📋 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     RHINOMETRIC v2.1.0 STACK                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Grafana    │  │  Prometheus  │  │     Loki     │         │
│  │   :3000      │  │    :9090     │  │    :3100     │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│         └──────────────────┴──────────────────┘                 │
│                            │                                     │
│  ┌─────────────────────────┴──────────────────────────┐        │
│  │                                                       │        │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │        │
│  │  │ License     │  │  API Proxy  │  │    OTEL     │ │        │
│  │  │ Server v2   │  │   (Node.js) │  │  Collector  │ │        │
│  │  │  (FastAPI)  │  │    :8090    │  │   :4319     │ │        │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │        │
│  │         │                 │                 │        │        │
│  └─────────┴─────────────────┴─────────────────┘        │        │
│                      │                                   │        │
│  ┌───────────────────┴─────────────────┐               │        │
│  │  Postgres   Redis   Tempo   Nginx   │               │        │
│  │   :5432     :6379   :3200    :80    │               │        │
│  └─────────────────────────────────────┘               │        │
│                                                                  │
│  Exporters: Node, cAdvisor, Blackbox, Postgres                 │
│  Logs: Promtail → Loki                                          │
│  Traces: OTEL Collector → Tempo                                │
│  Alerts: Alertmanager                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker** 20.10+ or Docker Desktop
- **Docker Compose** v2.0+
- **4 GB RAM** minimum (6 GB recommended)
- **4 CPU cores** minimum
- **20 GB disk space**

### Installation (All Platforms)

```bash
# Clone or download Rhinometric v2.1.0
cd mi-proyecto/infrastructure/mi-proyecto

# Run universal installer
./install-v2.1.sh
```

The installer will:
1. ✅ Detect your OS (macOS/Linux/WSL2)
2. ✅ Verify dependencies
3. ✅ Create data directories
4. ✅ Deploy all 16 services
5. ✅ Validate installation

### Manual Installation

```bash
# Create environment file
cp .env.example .env

# Edit passwords (optional)
nano .env

# Start services
docker compose -f docker-compose-v2.1.0.yml up -d

# Validate
./validate-v2.1.sh
```

---

## 🌐 Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **License Server** | http://localhost:5000/api/docs | - |
| **API Proxy** | http://localhost:8090/health | - |
| **Loki** | http://localhost:3100 | - |
| **Tempo** | http://localhost:3200 | - |
| **Alertmanager** | http://localhost:9093 | - |
| **Nginx** | http://localhost:80 | - |

---

## 📊 Pre-Loaded Dashboards

Grafana includes 8 enterprise-grade dashboards:

1. **📈 System Overview** - CPU, RAM, Disk, Network
2. **🗄️ Database Health** - PostgreSQL metrics, connections, query time
3. **🐳 Container Metrics** - Docker container stats via cAdvisor
4. **🌐 API Monitoring** - External API health, response times, status codes
5. **📝 Logs Explorer** - Log aggregation with severity filters
6. **🔍 Distributed Tracing** - Service graph, latency heatmap
7. **📋 License Management** - Active licenses, expiration timeline
8. **🚨 Alerting Dashboard** - Active alerts, alert history

All dashboards use dynamic variables: `${DS_PROMETHEUS}`, `${DS_LOKI}`, `${DS_TEMPO}`

---

## 🔌 Connecting External APIs

### Method 1: API Proxy (Automatic)

The API Proxy pre-configures these APIs:

- **CoinDesk** - Bitcoin price (https://api.coindesk.com/v1/bpi/currentprice.json)
- **GitHub Status** - GitHub uptime (https://www.githubstatus.com/api/v2/status.json)
- **Open-Meteo** - Weather data (https://api.open-meteo.com/v1/forecast)

**No configuration needed** - metrics appear automatically in Prometheus!

### Method 2: License Server UI

Add custom APIs via REST API:

```bash
curl -X POST http://localhost:5000/api/external-apis \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_api",
    "endpoint": "https://api.example.com/metrics",
    "auth_type": "bearer",
    "auth_token": "your-token-here",
    "scrape_interval": 60,
    "is_active": true
  }'
```

### Method 3: Direct Prometheus Config

Edit `config/prometheus-v2.1.yml`:

```yaml
scrape_configs:
  - job_name: 'my_custom_api'
    static_configs:
      - targets: ['api-proxy:8090']
    params:
      api: ['my_api']
```

---

## 📡 Sending Telemetry Data

### OpenTelemetry Collector

Send traces via OTLP:

```bash
# gRPC (port 4319)
curl -X POST http://localhost:4319 \
  -H "Content-Type: application/json" \
  -d '{
    "resourceSpans": [{
      "resource": {
        "attributes": [
          {"key": "service.name", "value": {"stringValue": "my-service"}},
          {"key": "environment", "value": {"stringValue": "production"}}
        ]
      },
      "scopeSpans": [{
        "spans": [{
          "traceId": "abc123",
          "spanId": "def456",
          "name": "HTTP GET /api/users",
          "startTimeUnixNano": "1698400000000000000",
          "endTimeUnixNano": "1698400001000000000",
          "attributes": [
            {"key": "http.method", "value": {"stringValue": "GET"}},
            {"key": "http.status_code", "value": {"intValue": 200}}
          ]
        }]
      }]
    }]
  }'

# HTTP (port 4320)
# Same payload to http://localhost:4320
```

### Direct to Tempo (Jaeger format)

```bash
curl -X POST http://localhost:14268/api/traces \
  -H "Content-Type: application/json" \
  -d '{
    "data": [{
      "traceID": "abc123",
      "spans": [{
        "traceID": "abc123",
        "spanID": "def456",
        "operationName": "HTTP GET",
        "startTime": 1698400000000000,
        "duration": 1000000
      }]
    }]
  }'
```

---

## 🛠️ Management Commands

### Service Control

```bash
# Status
docker compose -f docker-compose-v2.1.0.yml ps

# Logs (all services)
docker compose -f docker-compose-v2.1.0.yml logs -f

# Logs (specific service)
docker compose -f docker-compose-v2.1.0.yml logs -f grafana

# Restart all
docker compose -f docker-compose-v2.1.0.yml restart

# Restart specific service
docker compose -f docker-compose-v2.1.0.yml restart prometheus

# Stop all
docker compose -f docker-compose-v2.1.0.yml down

# Stop and remove volumes
docker compose -f docker-compose-v2.1.0.yml down -v
```

### Validation

```bash
# Quick validation
./validate-v2.1.sh

# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

---

## 📦 Resource Usage

| Component | CPU | Memory | Disk |
|-----------|-----|--------|------|
| **License Server v2** | 0.4 | 512 MB | 100 MB |
| **Postgres** | 0.5 | 512 MB | 2 GB |
| **Redis** | 0.2 | 256 MB | 500 MB |
| **API Proxy** | 0.3 | 256 MB | 100 MB |
| **Prometheus** | 0.8 | 1.5 GB | 5 GB |
| **Loki** | 0.5 | 512 MB | 2 GB |
| **Tempo** | 0.5 | 512 MB | 2 GB |
| **Grafana** | 0.6 | 800 MB | 1 GB |
| **OTEL Collector** | 0.3 | 512 MB | 200 MB |
| **Other Services** | 1.4 | 1.6 GB | 1 GB |
| **TOTAL** | **~3.5 vCPUs** | **~6 GB** | **~15 GB** |

**Optimization Tips:**
- Reduce Prometheus retention: `--storage.tsdb.retention.time=3d`
- Disable unused exporters
- Adjust scrape intervals in `config/prometheus-v2.1.yml`

---

## 🐛 Troubleshooting

### Service Not Starting

```bash
# Check logs
docker compose -f docker-compose-v2.1.0.yml logs -f [service-name]

# Check health
docker inspect rhinometric-[service-name] | jq '.[].State.Health'

# Restart service
docker compose -f docker-compose-v2.1.0.yml restart [service-name]
```

### Grafana Dashboards Empty

1. Check datasources: http://localhost:3000/datasources
2. Verify Prometheus targets: http://localhost:9090/targets
3. Check Prometheus query: http://localhost:9090/graph

### No Logs in Loki

```bash
# Check Promtail
docker logs rhinometric-promtail

# Verify Loki
curl http://localhost:3100/ready

# Check Docker socket
ls -la /var/run/docker.sock
```

### No Traces in Tempo

```bash
# Check OTEL Collector
curl http://localhost:13133

# Send test trace
curl -X POST http://localhost:4320/v1/traces \
  -H "Content-Type: application/json" \
  -d '{"resourceSpans":[]}'

# Query Tempo
curl http://localhost:3200/api/search
```

### High CPU Usage

```bash
# Check resource usage
docker stats

# Adjust Prometheus scrape interval
# Edit config/prometheus-v2.1.yml: scrape_interval: 30s

# Reload Prometheus
curl -X POST http://localhost:9090/-/reload
```

---

## 🔒 Security Notes

**Default Credentials (CHANGE IN PRODUCTION):**

```bash
# Edit .env file
POSTGRES_PASSWORD=your-secure-password
REDIS_PASSWORD=your-secure-password
GRAFANA_USER=admin
GRAFANA_PASSWORD=your-secure-password
```

**Network Security:**
- All services run on `172.21.0.0/16` network
- Only essential ports exposed to host
- Consider using Nginx for SSL/TLS termination

---

## 📚 Documentation

- **API Docs**: http://localhost:5000/api/docs (FastAPI Swagger UI)
- **Prometheus Query**: http://localhost:9090/graph
- **Grafana Docs**: http://localhost:3000/docs
- **Tempo TraceQL**: http://localhost:3000/explore

---

## 🆚 v2.1.0 vs v2.0.0

| Feature | v2.0.0 | v2.1.0 |
|---------|--------|--------|
| **Installation** | Manual, complex | One command (`./install-v2.1.sh`) |
| **API Connectivity** | json_exporter (broken) | API Proxy (working) |
| **Telemetry** | telemetrygen (no traces) | OpenTelemetry Collector |
| **License Server** | Flask (unstable) | FastAPI (production-ready) |
| **Dashboards** | Empty, slow | 8 pre-loaded, optimized |
| **Platform Support** | Linux only | macOS/Linux/WSL2 |
| **Resource Usage** | 4.9 vCPUs, 8.8 GB | 3.5 vCPUs, 6 GB (-30%) |
| **Healthchecks** | 12/16 (75%) | 16/16 (100%) |

---

## 🤝 Support

For issues or questions:

1. Check logs: `docker compose -f docker-compose-v2.1.0.yml logs -f`
2. Run validation: `./validate-v2.1.sh`
3. Review documentation: http://localhost:5000/api/docs

---

## 📄 License

Rhinometric v2.1.0 Enterprise Edition - Trial License

---

**🎉 Enjoy Rhinometric v2.1.0 Enterprise!**
