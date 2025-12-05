# 🧪 RHINOMETRIC v2.1.0 ENTERPRISE - TESTING GUIDE

**Purpose:** Validate package execution in real environment  
**Date:** October 27, 2025  
**Status:** ⏳ **PENDING USER EXECUTION**

---

## ⚠️ IMPORTANT NOTICE

**This guide must be executed by the user** in an environment with:
- ✅ Docker Desktop running (or Docker Engine + Docker Compose)
- ✅ Ports available: 80, 443, 3000, 3100, 3200, 4317-4320, 5000, 8090, 9090, etc.
- ✅ Terminal with bash (WSL2, macOS, Linux, or Git Bash with Docker access)

The AI assistant **CANNOT** execute Docker commands or HTTP requests from Windows Git Bash without Docker Desktop running.

---

## 📋 STEP-BY-STEP EXECUTION PLAN

### STEP 1: Extract Package

```bash
# Navigate to package location
cd ~/mi-proyecto/infrastructure/mi-proyecto

# Extract package
tar -xzf rhinometric-trial-v2.1.0-universal.tar.gz

# Enter directory
cd rhinometric-trial-v2.1.0-universal

# Verify contents
ls -la
```

**Expected output:**
```
total 120
drwxr-xr-x  8 user user  4096 Oct 27 14:00 .
drwxr-xr-x 12 user user  4096 Oct 27 14:00 ..
-rw-r--r--  1 user user  1234 Oct 27 14:00 .env.example
-rw-r--r--  1 user user  2048 Oct 27 14:00 CHECKSUMS.txt
-rw-r--r--  1 user user 15360 Oct 27 14:00 README.md
-rw-r--r--  1 user user 18432 Oct 27 14:00 docker-compose-v2.1.0.yml
-rwxr-xr-x  1 user user 12288 Oct 27 14:00 install-v2.1.sh
-rwxr-xr-x  1 user user  4096 Oct 27 14:00 validate-v2.1.sh
-rw-r--r--  1 user user  3072 Oct 27 14:00 nginx.conf
drwxr-xr-x  2 user user  4096 Oct 27 14:00 api-proxy
drwxr-xr-x  2 user user  4096 Oct 27 14:00 config
drwxr-xr-x  3 user user  4096 Oct 27 14:00 grafana
drwxr-xr-x  2 user user  4096 Oct 27 14:00 init-db
drwxr-xr-x  2 user user  4096 Oct 27 14:00 license-server-v2
```

---

### STEP 2: Verify Checksums

```bash
# Verify package integrity
sha256sum --check CHECKSUMS.txt
```

**Expected output:**
```
rhinometric-trial-v2.1.0-universal.tar.gz: OK
```

---

### STEP 3: Configure Environment (Optional)

```bash
# Copy environment template
cp .env.example .env

# Edit with custom passwords (optional, has secure defaults)
nano .env

# Or use defaults:
cat .env.example
```

**Default `.env` content:**
```bash
# Passwords (CHANGE IN PRODUCTION)
POSTGRES_PASSWORD=rhinometric_postgres_2024
REDIS_PASSWORD=rhinometric_redis_2024
GRAFANA_PASSWORD=rhinometric_grafana_2024

# Database
DB_NAME=rhinometric_v2

# License Server
JWT_SECRET=rhinometric_jwt_secret_change_in_production
LICENSE_ENCRYPTION_KEY=rhinometric_license_key_32_chars_change

# Grafana
GRAFANA_SECRET_KEY=rhinometric_grafana_secret_key_change

# Domain (for SSL in production)
DOMAIN=rhinometric.local
GRAFANA_DOMAIN=monitor.rhinometric.local
```

---

### STEP 4: Run Universal Installer

```bash
# Make installer executable (if not already)
chmod +x install-v2.1.sh

# Run installer
./install-v2.1.sh
```

**Expected output (summarized):**
```
═══════════════════════════════════════════════════════════════════════════
  RHINOMETRIC v2.1.0 ENTERPRISE - INSTALLATION
═══════════════════════════════════════════════════════════════════════════

▶ Detecting OS...
  ✓ macOS detected (or Linux/WSL2)

▶ Checking Docker...
  ✓ Docker version: 24.0.6
  ✓ Docker Compose version: v2.23.0

▶ Creating data directories...
  ✓ ~/rhinometric_data_v2.1/postgres
  ✓ ~/rhinometric_data_v2.1/redis
  ... (all directories)

▶ Generating .env file...
  ✓ Environment configured

▶ Building custom images...
  ✓ API Proxy image built
  ✓ License Server v2 image built

▶ Starting services...
  ✓ 16/16 containers starting

▶ Waiting for health checks (timeout: 5 minutes)...
  ⏳ postgres: starting
  ⏳ redis: starting
  ⏳ license-server-v2: starting
  ...
  ✓ All services healthy (time: 2m 34s)

═══════════════════════════════════════════════════════════════════════════
  INSTALLATION COMPLETE!
═══════════════════════════════════════════════════════════════════════════

Access URLs:
  • Grafana:            http://localhost:3000
    Username: admin
    Password: rhinometric_grafana_2024

  • Prometheus:         http://localhost:9090
  • Loki:               http://localhost:3100
  • Tempo:              http://localhost:3200
  • License Server:     http://localhost:5000/api/docs
  • API Proxy:          http://localhost:8090/health

Data Persistence:
  • Location: ~/rhinometric_data_v2.1
  • Backups: Configure external backup strategy

Next Steps:
  1. Access Grafana: http://localhost:3000
  2. Run validation: ./validate-v2.1.sh
  3. View logs: docker compose -f docker-compose-v2.1.0.yml logs -f

═══════════════════════════════════════════════════════════════════════════
```

---

### STEP 5: Verify Containers

```bash
# List all containers
docker compose -f docker-compose-v2.1.0.yml ps
```

**Expected output:**

```
NAME                           STATUS                   PORTS
rhinometric-alertmanager       Up 2 minutes (healthy)   0.0.0.0:9093->9093/tcp
rhinometric-api-proxy          Up 2 minutes (healthy)   0.0.0.0:8090->8090/tcp
rhinometric-blackbox-exporter  Up 2 minutes (healthy)   0.0.0.0:9115->9115/tcp
rhinometric-cadvisor           Up 2 minutes (healthy)   0.0.0.0:8080->8080/tcp
rhinometric-grafana            Up 2 minutes (healthy)   0.0.0.0:3000->3000/tcp
rhinometric-license-server-v2  Up 2 minutes (healthy)   0.0.0.0:5000->5000/tcp
rhinometric-loki               Up 2 minutes (healthy)   0.0.0.0:3100->3100/tcp
rhinometric-nginx              Up 2 minutes (healthy)   0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
rhinometric-node-exporter      Up 2 minutes (healthy)   0.0.0.0:9100->9100/tcp
rhinometric-otel-collector     Up 2 minutes (healthy)   0.0.0.0:4317->4317/tcp, 0.0.0.0:4318->4318/tcp, ...
rhinometric-postgres           Up 2 minutes (healthy)   0.0.0.0:5432->5432/tcp
rhinometric-postgres-exporter  Up 2 minutes (healthy)   0.0.0.0:9187->9187/tcp
rhinometric-prometheus         Up 2 minutes (healthy)   0.0.0.0:9090->9090/tcp
rhinometric-promtail           Up 2 minutes (healthy)   0.0.0.0:9080->9080/tcp
rhinometric-redis              Up 2 minutes (healthy)   0.0.0.0:6379->6379/tcp
rhinometric-tempo              Up 2 minutes (healthy)   0.0.0.0:3200->3200/tcp, 0.0.0.0:14268->14268/tcp
```

**✅ VALIDATION CRITERIA:**
- All containers: `Up X minutes (healthy)`
- No `Restarting` or `Exited` status
- 16/16 containers running

---

### STEP 6: Check Logs (Last 20 Lines)

#### 6.1 Prometheus Logs

```bash
docker compose -f docker-compose-v2.1.0.yml logs prometheus --tail 20
```

**Expected output:**
```
rhinometric-prometheus | ts=2025-10-27T14:05:23.456Z caller=main.go:1234 level=info msg="Server is ready to receive web requests."
rhinometric-prometheus | ts=2025-10-27T14:05:24.789Z caller=main.go:1456 level=info msg="Starting Prometheus" version="2.53.0"
rhinometric-prometheus | ts=2025-10-27T14:05:25.012Z caller=main.go:1567 level=info msg="Completed loading of configuration file"
rhinometric-prometheus | ts=2025-10-27T14:05:30.234Z caller=scrape.go:1234 level=info component=scrape target=prometheus job=prometheus msg="Appended" samples=187
rhinometric-prometheus | ts=2025-10-27T14:05:30.456Z caller=scrape.go:1234 level=info component=scrape target=grafana job=grafana msg="Appended" samples=423
rhinometric-prometheus | ts=2025-10-27T14:05:31.123Z caller=scrape.go:1234 level=info component=scrape target=license-server-v2 job=license-server-v2 msg="Appended" samples=34
rhinometric-prometheus | ts=2025-10-27T14:05:32.456Z caller=scrape.go:1234 level=info component=scrape target=api-proxy job=api-proxy msg="Appended" samples=12
...
```

**✅ VALIDATION:** Look for `msg="Appended" samples=X` (confirms metrics ingestion)

---

#### 6.2 Loki Logs

```bash
docker compose -f docker-compose-v2.1.0.yml logs loki --tail 20
```

**Expected output:**
```
rhinometric-loki | level=info ts=2025-10-27T14:05:23.456Z caller=loki.go:234 msg="Loki started"
rhinometric-loki | level=info ts=2025-10-27T14:05:24.789Z caller=server.go:345 msg="server listening on addresses" http=[::]:3100
rhinometric-loki | level=info ts=2025-10-27T14:05:30.123Z caller=ingester.go:456 msg="flushing chunks" streams=8
rhinometric-loki | level=info ts=2025-10-27T14:05:35.456Z caller=distributor.go:789 msg="push request received" entries=23 size=4KB
rhinometric-loki | level=info ts=2025-10-27T14:05:40.234Z caller=compactor.go:567 msg="compaction complete" blocks=3
...
```

**✅ VALIDATION:** Look for `msg="push request received"` (confirms log ingestion from Promtail)

---

#### 6.3 Tempo Logs

```bash
docker compose -f docker-compose-v2.1.0.yml logs tempo --tail 20
```

**Expected output:**
```
rhinometric-tempo | level=info ts=2025-10-27T14:05:23.456Z caller=tempo.go:123 msg="Tempo starting"
rhinometric-tempo | level=info ts=2025-10-27T14:05:24.789Z caller=server.go:234 msg="HTTP server listening" addr=0.0.0.0:3200
rhinometric-tempo | level=info ts=2025-10-27T14:05:25.012Z caller=receiver.go:345 msg="Starting OTLP receiver" transport=grpc endpoint=0.0.0.0:4317
rhinometric-tempo | level=info ts=2025-10-27T14:05:25.234Z caller=receiver.go:456 msg="Starting OTLP receiver" transport=http endpoint=0.0.0.0:4318
rhinometric-tempo | level=info ts=2025-10-27T14:05:26.456Z caller=metrics_generator.go:567 msg="Metrics generator enabled"
...
```

**✅ VALIDATION:** Look for `msg="Starting OTLP receiver"` and `msg="Metrics generator enabled"`

---

#### 6.4 License Server v2 Logs

```bash
docker compose -f docker-compose-v2.1.0.yml logs license-server-v2 --tail 20
```

**Expected output:**
```
rhinometric-license-server-v2 | INFO:     Started server process [1]
rhinometric-license-server-v2 | INFO:     Waiting for application startup.
rhinometric-license-server-v2 | INFO:     Application startup complete.
rhinometric-license-server-v2 | INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
rhinometric-license-server-v2 | INFO:     Connected to PostgreSQL: rhinometric_v2@postgres:5432
rhinometric-license-server-v2 | INFO:     Connected to Redis: redis:6379
rhinometric-license-server-v2 | INFO:     Prometheus metrics enabled at /api/metrics
rhinometric-license-server-v2 | INFO:     127.0.0.1:45678 - "GET /api/health HTTP/1.1" 200 OK
...
```

**✅ VALIDATION:** Look for `Application startup complete` and `Connected to PostgreSQL/Redis`

---

#### 6.5 API Proxy Logs

```bash
docker compose -f docker-compose-v2.1.0.yml logs api-proxy --tail 20
```

**Expected output:**
```
rhinometric-api-proxy | 2025-10-27 14:05:23 [INFO] API Proxy starting on port 8090
rhinometric-api-proxy | 2025-10-27 14:05:24 [INFO] Connected to Redis: redis:6379
rhinometric-api-proxy | 2025-10-27 14:05:25 [INFO] Pre-configured APIs loaded: coindesk_btc, github_status, openweather
rhinometric-api-proxy | 2025-10-27 14:05:26 [INFO] Prometheus metrics exposed at /api/metrics/prometheus
rhinometric-api-proxy | 2025-10-27 14:05:27 [INFO] Server listening on http://0.0.0.0:8090
rhinometric-api-proxy | 2025-10-27 14:05:30 [INFO] GET /health 200 - 5ms
rhinometric-api-proxy | 2025-10-27 14:05:45 [INFO] GET /api/fetch/coindesk_btc 200 - 234ms (cache miss)
rhinometric-api-proxy | 2025-10-27 14:06:00 [INFO] GET /api/fetch/coindesk_btc 200 - 3ms (cache hit)
...
```

**✅ VALIDATION:** Look for `Server listening`, `Pre-configured APIs loaded`, and successful requests

---

### STEP 7: HTTP Health Checks

#### 7.1 Prometheus Targets

```bash
curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[].labels.job' | sort -u
```

**Expected output (17 scrape jobs):**
```
alertmanager
api-proxy
blackbox-exporter
blackbox-http
cadvisor
external-apis
grafana
license-server-v2
loki
node-exporter
otel-collector
postgres-exporter
prometheus
promtail
tempo
```

**✅ VALIDATION:** Should list 15-17 unique job names

---

#### 7.2 Loki Ready

```bash
curl -s http://localhost:3100/ready
```

**Expected output:**
```
ready
```

**Alternative check (with labels):**
```bash
curl -s "http://localhost:3100/loki/api/v1/labels" | jq .
```

**Expected output:**
```json
{
  "status": "success",
  "data": [
    "container",
    "service",
    "project",
    "stream",
    "level",
    "environment",
    "version"
  ]
}
```

---

#### 7.3 Tempo Search

```bash
curl -s "http://localhost:3200/api/search?limit=5" | jq .
```

**Expected output (if traces exist):**
```json
{
  "traces": [
    {
      "traceID": "abc123def456...",
      "rootServiceName": "api-proxy",
      "rootTraceName": "GET /api/fetch/coindesk_btc"
    },
    ...
  ],
  "metrics": {
    "totalTraces": 42
  }
}
```

**Note:** If no traces yet, run this to generate one:
```bash
# Send test trace via OTEL Collector
curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{
    "resourceSpans": [{
      "resource": {
        "attributes": [
          {"key": "service.name", "value": {"stringValue": "test-service"}},
          {"key": "environment", "value": {"stringValue": "trial"}},
          {"key": "version", "value": {"stringValue": "2.1.0"}}
        ]
      },
      "scopeSpans": [{
        "scope": {"name": "manual-test"},
        "spans": [{
          "traceId": "0123456789abcdef0123456789abcdef",
          "spanId": "0123456789abcdef",
          "name": "manual-test-span",
          "kind": 1,
          "startTimeUnixNano": "1698418923000000000",
          "endTimeUnixNano": "1698418924000000000",
          "attributes": [
            {"key": "http.method", "value": {"stringValue": "GET"}},
            {"key": "http.status_code", "value": {"intValue": "200"}}
          ]
        }]
      }]
    }]
  }'

# Wait 5 seconds
sleep 5

# Query again
curl -s "http://localhost:3200/api/search?limit=5" | jq .
```

---

#### 7.4 API Proxy Health

```bash
curl -s http://localhost:8090/health | jq .
```

**Expected output:**
```json
{
  "status": "healthy",
  "service": "api-proxy",
  "version": "2.1.0",
  "redis": "connected",
  "uptime": "120.45s",
  "timestamp": "2025-10-27T14:07:23.456Z"
}
```

---

#### 7.5 License Server v2 Health

```bash
curl -s http://localhost:5000/api/health | jq .
```

**Expected output:**
```json
{
  "status": "healthy",
  "service": "license-server-v2",
  "version": "2.1.0",
  "database": "connected",
  "redis": "connected",
  "uptime": "125.67s",
  "timestamp": "2025-10-27T14:07:28.789Z"
}
```

---

### STEP 8: Grafana Dashboard Verification

#### 8.1 Access Grafana

```bash
# Open in browser
open http://localhost:3000  # macOS
xdg-open http://localhost:3000  # Linux
start http://localhost:3000  # Windows
```

**Credentials:**
- Username: `admin`
- Password: `rhinometric_grafana_2024` (or from your `.env`)

---

#### 8.2 Verify Datasources

Navigate to: **Configuration → Data sources**

**Expected datasources (3):**
1. ✅ Prometheus (default) - `http://prometheus:9090`
2. ✅ Loki - `http://loki:3100`
3. ✅ Tempo - `http://tempo:3200`

**Test each datasource** (click "Save & test" button)

---

#### 8.3 List Dashboards

Navigate to: **Dashboards → Browse**

**Expected dashboards (6):**
1. ✅ Overview
2. ✅ System Monitoring
3. ✅ Docker Containers
4. ✅ Logs Explorer
5. ✅ Distributed Tracing
6. ✅ License Status

---

#### 8.4 Export Dashboard JSON (Example: Overview)

Navigate to: **Dashboards → Overview → Share → Export**

Click "Save to file" or copy JSON:

```bash
# Or via API
curl -s -u admin:rhinometric_grafana_2024 \
  "http://localhost:3000/api/dashboards/uid/overview" | jq . > overview-exported.json

# View file
cat overview-exported.json
```

**Expected output:** JSON file with dashboard definition (~20KB)

---

#### 8.5 Take Screenshot (Manual)

Open dashboard "Overview" and take screenshot showing:
- ✅ Panels with real data (not "No data")
- ✅ Time series graphs with metrics
- ✅ Service status indicators
- ✅ Resource usage gauges

Save as: `grafana-overview-screenshot.png`

---

### STEP 9: Run Validation Script

```bash
# Run automated validation
./validate-v2.1.sh
```

**Expected output:**
```
═══════════════════════════════════════════════════════════════════════════
  RHINOMETRIC v2.1.0 - SYSTEM VALIDATION
═══════════════════════════════════════════════════════════════════════════

▶ Validating Container Health (16 services)
  ✓ rhinometric-postgres: healthy
  ✓ rhinometric-redis: healthy
  ✓ rhinometric-license-server-v2: healthy
  ✓ rhinometric-api-proxy: healthy
  ✓ rhinometric-prometheus: healthy
  ✓ rhinometric-loki: healthy
  ✓ rhinometric-tempo: healthy
  ✓ rhinometric-grafana: healthy
  ✓ rhinometric-otel-collector: healthy
  ✓ rhinometric-alertmanager: healthy
  ✓ rhinometric-promtail: healthy
  ✓ rhinometric-node-exporter: healthy
  ✓ rhinometric-cadvisor: healthy
  ✓ rhinometric-blackbox-exporter: healthy
  ✓ rhinometric-postgres-exporter: healthy
  ✓ rhinometric-nginx: healthy

▶ Validating Endpoint Accessibility
  ✓ Grafana:          http://localhost:3000 (200 OK)
  ✓ Prometheus:       http://localhost:9090 (200 OK)
  ✓ Loki:             http://localhost:3100/ready (200 OK)
  ✓ Tempo:            http://localhost:3200/ready (200 OK)
  ✓ License Server:   http://localhost:5000/api/health (200 OK)
  ✓ API Proxy:        http://localhost:8090/health (200 OK)

▶ Validating Prometheus Targets
  ✓ Active targets: 17/17

▶ Validating Data Persistence
  ✓ Data directory:   ~/rhinometric_data_v2.1 (exists)
  ✓ Postgres data:    512 MB
  ✓ Prometheus data:  128 MB
  ✓ Grafana data:     64 MB
  ✓ Loki data:        32 MB
  ✓ Tempo data:       16 MB

═══════════════════════════════════════════════════════════════════════════
  ✓ All validation checks passed!
═══════════════════════════════════════════════════════════════════════════

Exit code: 0
```

---

### STEP 10: Document Results

Create a file with all outputs:

```bash
# Create results file
cat > TESTING_RESULTS_v2.1.0.txt << 'EOF'
# RHINOMETRIC v2.1.0 ENTERPRISE - TESTING RESULTS
# Date: $(date)
# Environment: $(uname -s) $(uname -r)

## 1. Container Status
$(docker compose -f docker-compose-v2.1.0.yml ps)

## 2. Prometheus Targets
$(curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[].labels.job' | sort -u)

## 3. Loki Labels
$(curl -s http://localhost:3100/loki/api/v1/labels | jq .)

## 4. Tempo Traces
$(curl -s "http://localhost:3200/api/search?limit=5" | jq .)

## 5. API Proxy Health
$(curl -s http://localhost:8090/health | jq .)

## 6. License Server Health
$(curl -s http://localhost:5000/api/health | jq .)

## 7. Validation Script Result
$(./validate-v2.1.sh)

EOF

# Execute and capture output
bash TESTING_RESULTS_v2.1.0.txt > TESTING_RESULTS_v2.1.0_output.txt 2>&1

# View results
cat TESTING_RESULTS_v2.1.0_output.txt
```

---

## 📊 EXPECTED ACCESS URLS

After successful deployment, these URLs should be accessible:

| Service | URL | Credentials | Notes |
|---------|-----|-------------|-------|
| **Grafana** | http://localhost:3000 | admin / rhinometric_grafana_2024 | Main UI |
| **Prometheus** | http://localhost:9090 | None | Metrics query |
| **Loki** | http://localhost:3100 | None | Logs API |
| **Tempo** | http://localhost:3200 | None | Traces API |
| **License Server API Docs** | http://localhost:5000/api/docs | None | Swagger UI |
| **License Server Metrics** | http://localhost:5000/api/metrics | None | Prometheus format |
| **API Proxy Health** | http://localhost:8090/health | None | Health status |
| **API Proxy Metrics** | http://localhost:8090/api/metrics/prometheus | None | Prometheus format |
| **Alertmanager** | http://localhost:9093 | None | Alert management |
| **Node Exporter** | http://localhost:9100/metrics | None | Host metrics |
| **cAdvisor** | http://localhost:8080/metrics | None | Container metrics |
| **Blackbox Exporter** | http://localhost:9115/metrics | None | Endpoint probes |
| **Postgres Exporter** | http://localhost:9187/metrics | None | DB metrics |
| **Promtail** | http://localhost:9080/ready | None | Log shipper status |
| **OTEL Collector** | http://localhost:13133 | None | Health check |
| **Nginx** | http://localhost:80 | None | Reverse proxy |

---

## ✅ SUCCESS CRITERIA

Mark as **READY FOR PRODUCTION** only if ALL criteria are met:

### Containers
- [ ] 16/16 containers status: `Up X minutes (healthy)`
- [ ] No restarts or failures in logs
- [ ] All healthchecks passing

### Metrics (Prometheus)
- [ ] 17 scrape jobs active
- [ ] Sample count > 0 for all jobs
- [ ] Query `up` returns 1 for all targets

### Logs (Loki)
- [ ] Promtail pushing logs (`msg="push request received"`)
- [ ] `/loki/api/v1/labels` returns 7+ labels
- [ ] Query `{container="api-proxy"}` returns results

### Traces (Tempo)
- [ ] OTLP receivers listening (ports 4317, 4318)
- [ ] Metrics generator enabled
- [ ] At least 1 trace ingested (after sending test span)

### Services
- [ ] License Server: `/api/health` returns `{"status": "healthy"}`
- [ ] API Proxy: `/health` returns `{"status": "healthy"}`
- [ ] Grafana: Login successful, 6 dashboards visible
- [ ] Datasources: 3/3 connected (Prometheus, Loki, Tempo)

### Data
- [ ] Grafana dashboards showing real metrics (not "No data")
- [ ] At least 1 panel per dashboard with data points
- [ ] Time series graphs rendering correctly

### Persistence
- [ ] Data directory `~/rhinometric_data_v2.1` exists
- [ ] Postgres data persisted (check with `ls -lh ~/rhinometric_data_v2.1/postgres`)
- [ ] Stop/start cycle preserves data

---

## 🐛 TROUBLESHOOTING

### Issue: Containers not starting

```bash
# Check Docker resources
docker system df

# Check for port conflicts
sudo lsof -i :3000
sudo lsof -i :9090

# Check logs
docker compose -f docker-compose-v2.1.0.yml logs --tail 50
```

**Fix:** Stop conflicting services or change ports in `docker-compose-v2.1.0.yml`

---

### Issue: Healthchecks failing

```bash
# Check specific service
docker inspect rhinometric-prometheus | jq '.[0].State.Health'

# View healthcheck logs
docker logs rhinometric-prometheus 2>&1 | grep -i health
```

**Fix:** Wait 2-3 minutes for services to initialize. If still failing, check service logs.

---

### Issue: No data in Grafana

**Check datasource connectivity:**
```bash
# Grafana → Configuration → Data sources → Prometheus → Test
curl -s http://localhost:3000/api/datasources/proxy/1/api/v1/query?query=up \
  -u admin:rhinometric_grafana_2024 | jq .
```

**Expected:** `{"status":"success","data":{"resultType":"vector","result":[...]}}`

**Fix:** Verify Prometheus is scraping: http://localhost:9090/targets

---

### Issue: No logs in Loki

**Check Promtail:**
```bash
# Verify Promtail is running
docker logs rhinometric-promtail --tail 50

# Check Loki ingestion
curl -s "http://localhost:3100/loki/api/v1/label/container/values" | jq .
```

**Expected:** List of container names

**Fix:** Verify Promtail config, check Docker socket mount

---

### Issue: No traces in Tempo

**Send test trace:**
```bash
# Manual span injection
curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{
    "resourceSpans": [{
      "resource": {"attributes": [
        {"key": "service.name", "value": {"stringValue": "test-manual"}}
      ]},
      "scopeSpans": [{
        "spans": [{
          "traceId": "12345678901234567890123456789012",
          "spanId": "1234567890123456",
          "name": "test-span",
          "kind": 1,
          "startTimeUnixNano": "1698418923000000000",
          "endTimeUnixNano": "1698418924000000000"
        }]
      }]
    }]
  }'

# Wait 5 seconds
sleep 5

# Query Tempo
curl -s "http://localhost:3200/api/search?limit=1" | jq .
```

**Expected:** Trace with ID `12345678901234567890123456789012`

---

### Issue: High resource usage

```bash
# Check resource consumption
docker stats --no-stream

# Limit specific service
docker update rhinometric-prometheus --cpus="0.5" --memory="1g"
```

**Expected:** Total < 4 CPU cores, < 6 GB RAM

---

## 📋 FINAL CHECKLIST

Before marking as **PRODUCTION READY**, verify:

- [ ] Package extracted successfully
- [ ] Checksums validated (SHA256 match)
- [ ] Installer completed without errors
- [ ] 16/16 containers healthy
- [ ] All HTTP endpoints responding (200 OK)
- [ ] Prometheus: 17 scrape jobs active
- [ ] Loki: Logs visible with 7+ labels
- [ ] Tempo: At least 1 trace ingested
- [ ] Grafana: Login successful, 6 dashboards with data
- [ ] License Server: Health endpoint returns `{"status": "healthy"}`
- [ ] API Proxy: Health endpoint returns `{"status": "healthy"}`
- [ ] Validation script: Exit code 0
- [ ] Dashboard JSON exported successfully
- [ ] Screenshot captured showing real data
- [ ] Data persists after stop/start cycle

---

## 🚀 NEXT STEPS AFTER VALIDATION

Once all criteria are met:

1. **Document Results:**
   - Save `TESTING_RESULTS_v2.1.0_output.txt`
   - Export dashboard JSONs
   - Take screenshots of all 6 dashboards

2. **Create GitHub Release:**
   ```bash
   git tag -a v2.1.0 -m "Rhinometric v2.1.0 Enterprise - Production Ready"
   git push origin dev --tags
   ```

3. **Upload Package:**
   - Upload `rhinometric-trial-v2.1.0-universal.tar.gz` to release
   - Include `rhinometric-v2.1.0-enterprise_checksums.txt`
   - Attach `RELEASE-VERIFICATION-v2.1.0.md`

4. **Update Documentation:**
   - Add screenshots to README
   - Create demo video
   - Write installation tutorial

---

**END OF TESTING GUIDE**

**Status:** ⏳ Awaiting user execution  
**Next Action:** User must run commands and share outputs
