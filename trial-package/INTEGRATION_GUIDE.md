# 🔌 Rhinometric Trial - Client Integration Guide

## Overview

This guide shows you how to integrate YOUR application with Rhinometric's observability platform. After following this guide, you'll be able to send **metrics**, **logs**, and **traces** from your application to Rhinometric.

---

## ✅ What You Get

### 15 Running Containers
- **Prometheus** (port 9090) - Metrics storage
- **Loki** (port 3100) - Log aggregation  
- **Tempo** (ports 4317/4318) - Distributed tracing
- **Grafana** (port 3000) - Visualization
- **PostgreSQL 15** (port 5432) - Application database
- **Redis** (port 6379) - Caching layer
- Plus 9 exporters for system/container monitoring

### 6 Pre-configured Dashboards
1. **Rhinometric - Overview** - System metrics (CPU, RAM, uptime)
2. **Rhinometric - Docker Containers** - Container health
3. **Rhinometric - System Monitoring** - Detailed node metrics
4. **Rhinometric - Logs Explorer** - Real-time log search
5. **Rhinometric - License Status** - Trial info (180 days)
6. **Rhinometric - Distributed Tracing** - Request traces

### Complete Observability
- ✅ **Metrics**: Send custom app metrics via Prometheus
- ✅ **Logs**: Send structured logs via Loki
- ✅ **Traces**: Send distributed traces via Tempo/OTLP
- ✅ **Database**: PostgreSQL ready for your app data
- ✅ **Examples**: Python & Node.js integration code included

---

## 🎯 Quick Start Integration

### 1. Python Application

```bash
cd examples/python
pip install -r requirements.txt
python send_metrics_logs_traces.py
```

This will send 10 metrics, 15 logs, and 10 traces to Rhinometric.

**View results in Grafana:**
- http://localhost:3000/d/rhinometric-logs (Logs)
- http://localhost:3000/d/rhinometric-tracing (Traces)
- http://localhost:3000/explore (Prometheus metrics)

### 2. Node.js Application

```bash
cd examples/nodejs
npm install
npm start
```

Sends 20 metrics, 15 logs, and 10 traces.

---

## 📊 Integration Endpoints

| Service | Purpose | Endpoint | Protocol |
|---------|---------|----------|----------|
| **Prometheus** | Send metrics | `localhost:9090/api/v1/write` | HTTP POST |
| **Loki** | Send logs | `localhost:3100/loki/api/v1/push` | HTTP POST (JSON) |
| **Tempo** | Send traces | `localhost:4317` | gRPC (OTLP) |
| **Tempo** | Send traces | `localhost:4318/v1/traces` | HTTP POST (OTLP) |
| **Grafana** | Visualize | `localhost:3000` | HTTP (Web UI) |
| **PostgreSQL** | App database | `localhost:5432` | PostgreSQL protocol |

---

## 🔧 Integration Examples

### A) METRICS - Prometheus

#### Python (prometheus_client)
```python
from prometheus_client import Counter, Gauge, push_to_gateway

# Define metrics
requests = Counter('app_requests_total', 'Total requests', ['method'])
cpu_usage = Gauge('app_cpu_usage', 'CPU usage %')

# Use in your code
requests.labels(method='GET').inc()
cpu_usage.set(45.2)
```

#### Node.js (prom-client)
```javascript
const prom = require('prom-client');

const httpRequests = new prom.Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'status']
});

httpRequests.inc({ method: 'GET', status: '200' });
```

**Verify in Prometheus:**
```bash
curl http://localhost:9090/api/v1/query?query=app_requests_total
```

---

### B) LOGS - Loki

#### Python (requests)
```python
import requests, time

loki_url = "http://localhost:3100/loki/api/v1/push"
log_data = {
    "streams": [{
        "stream": {
            "service_name": "my-app",
            "level": "info",
            "environment": "production"
        },
        "values": [
            [str(int(time.time() * 1e9)), "My log message"]
        ]
    }]
}
requests.post(loki_url, json=log_data)
```

#### Node.js (axios)
```javascript
const axios = require('axios');

const logEntry = {
  streams: [{
    stream: { service_name: 'my-app', level: 'info' },
    values: [[Date.now() * 1e6 + '', 'My log message']]
  }]
};

axios.post('http://localhost:3100/loki/api/v1/push', logEntry);
```

**View in Grafana:**
- Go to Explore → Select "Loki" datasource
- Query: `{service_name="my-app"}`

---

### C) TRACES - Tempo (OpenTelemetry)

#### Python
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Setup
trace.set_tracer_provider(TracerProvider())
exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(exporter))

# Use
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("my_operation"):
    # Your code here
    pass
```

#### Node.js
```javascript
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');

const provider = new NodeTracerProvider();
const exporter = new OTLPTraceExporter({ url: 'localhost:4317' });
provider.addSpanProcessor(new BatchSpanProcessor(exporter));
provider.register();

const tracer = trace.getTracer('my-app');
const span = tracer.startSpan('operation_name');
// ... do work
span.end();
```

**View in Grafana:**
- Go to Explore → Select "Tempo" datasource
- Search by service name or trace ID

---

## 🗄️ PostgreSQL Database

### Purpose
PostgreSQL is included for **YOUR APPLICATION DATA**, not for Rhinometric internals.
Rhinometric stores metrics/logs/traces in local filesystem storage.

### Connection Details
- **Host**: localhost
- **Port**: 5432
- **Database**: rhinometric_trial
- **User**: postgres
- **Password**: trial_rhinometric_2024 (changeable in `.env`)

### Sample Schema
A complete example schema is provided in `init-db/init-schema.sql` with:
- Users table
- Sessions table
- Audit events table
- Application metrics table
- Helper views for reporting

### Connect from Your App

**Python (psycopg2):**
```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="rhinometric_trial",
    user="postgres",
    password="trial_rhinometric_2024"
)
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
```

**Node.js (pg):**
```javascript
const { Pool } = require('pg');

const pool = new Pool({
    host: 'localhost',
    database: 'rhinometric_trial',
    user: 'postgres',
    password: 'trial_rhinometric_2024'
});

const result = await pool.query('SELECT * FROM users');
```

### Initialize Schema
```bash
docker exec -i rhinometric-postgres psql -U postgres -d rhinometric_trial < init-db/init-schema.sql
```

---

## 📊 Full Integration Example

### Python Flask App with Complete Observability

```python
from flask import Flask
from prometheus_client import Counter, generate_latest
from opentelemetry import trace
import requests, time

app = Flask(__name__)

# Metrics
request_counter = Counter('http_requests_total', 'Total requests', ['endpoint'])

# Tracing
tracer = trace.get_tracer(__name__)

@app.route('/api/users')
def get_users():
    # Count request
    request_counter.labels(endpoint='/api/users').inc()
    
    # Trace
    with tracer.start_as_current_span("get_users"):
        # Log to Loki
        log_data = {
            "streams": [{
                "stream": {"service_name": "flask-app", "level": "info"},
                "values": [[str(int(time.time() * 1e9)), "GET /api/users"]]
            }]
        }
        requests.post('http://localhost:3100/loki/api/v1/push', json=log_data)
        
        return {'users': []}

@app.route('/metrics')
def metrics():
    return generate_latest()

app.run(port=5000)
```

**Access:**
- App: http://localhost:5000/api/users
- Metrics: http://localhost:5000/metrics
- Grafana: http://localhost:3000

---

## ✅ Verification Checklist

### 1. Verify Services Running
```bash
docker ps | grep rhinometric
# Should show 15 containers
```

### 2. Test Metrics
```bash
curl http://localhost:9090/api/v1/query?query=up
# Should return JSON with "status": "success"
```

### 3. Test Logs
```bash
curl -X POST http://localhost:3100/loki/api/v1/push \
  -H "Content-Type: application/json" \
  -d '{"streams":[{"stream":{"test":"true"},"values":[["'$(date +%s)000000000'","test log"]]}]}'
# Should return 204 No Content
```

### 4. Test Traces
```bash
cd examples/python
python send_metrics_logs_traces.py
# Should show "✅ ALL DATA SENT SUCCESSFULLY"
```

### 5. Verify in Grafana
1. Open http://localhost:3000
2. Login: admin / admin_secure_2024
3. Go to Dashboards → Check all 6 dashboards have data
4. Go to Explore → Test Loki, Tempo, Prometheus datasources

---

## 🚨 Troubleshooting

### Metrics Not Appearing
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

### Logs Not Showing
```bash
# Verify Loki is ready
curl http://localhost:3100/ready
# Should return "ready"

# Check recent logs
curl 'http://localhost:3100/loki/api/v1/query_range?query={service_name=~".+"}' | jq
```

### Traces Missing
```bash
# Check Tempo health
curl http://localhost:3200/ready
# Should return "ready"

# Search traces
curl http://localhost:3200/api/search | jq
# Should list recent traces
```

### Database Connection Failed
```bash
# Verify PostgreSQL is running
docker exec rhinometric-postgres pg_isready
# Should return "accepting connections"

# Test connection
docker exec -it rhinometric-postgres psql -U postgres -d rhinometric_trial -c "SELECT version();"
```

---

## 📚 Additional Resources

- **Examples folder**: `examples/python/` and `examples/nodejs/`
- **Database schema**: `init-db/init-schema.sql`
- **Environment config**: `.env` file
- **Docker logs**: `docker compose logs -f <service_name>`

### Documentation Links
- OpenTelemetry: https://opentelemetry.io/docs/
- Prometheus: https://prometheus.io/docs/
- Grafana Loki: https://grafana.com/docs/loki/
- Grafana Tempo: https://grafana.com/docs/tempo/

---

## 💡 Best Practices

1. **Use Labels/Tags** - Add context to metrics, logs, traces
2. **Sample Traces** - Don't trace every request in production
3. **Structured Logs** - Use JSON format for better parsing
4. **Monitor Exporters** - Check if data is being sent
5. **Secure Credentials** - Change default passwords in `.env`

---

## 📧 Support

**Trial Support:**
- Email: support@rhinometric.com
- Response time: 24-48 hours

**Upgrade to Full Version:**
- Email: sales@rhinometric.com
- Website: https://rhinometric.com/pricing

---

## ⚖️ Trial Limitations

- **Duration**: 180 days (6 months)
- **Data Retention**: Traces 24h, Logs 7d, Metrics 1d
- **Concurrent Users**: 5 Grafana users max
- **No Production Support**: Trial support only

**Upgrade for:**
- ✅ Unlimited duration
- ✅ Extended data retention (configurable)
- ✅ Unlimited users
- ✅ 24/7 production support
- ✅ High-availability setup
- ✅ Custom integrations

---

**Happy Monitoring! 📊🔍📝**
