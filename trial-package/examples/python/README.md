# Python Integration Example

## Overview
Complete example showing how to send **Metrics**, **Logs**, and **Traces** to Rhinometric platform.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Quick Start
```bash
python send_metrics_logs_traces.py
```

This will:
1. ✅ Send 10 sample metrics to Prometheus
2. ✅ Send 15 log entries to Loki
3. ✅ Send 10 distributed traces to Tempo

### What Gets Sent

**Metrics (Prometheus)**
- `http_requests_total` - Counter with labels (method, endpoint)
- `active_users` - Gauge showing concurrent users
- `http_request_duration_seconds` - Histogram of request latency

**Logs (Loki)**
- Structured logs with levels: info, warn, error, debug
- Labels: service_name, level, environment
- Includes request IDs and timestamps

**Traces (Tempo)**
- Distributed traces with parent/child spans
- HTTP request → Database query → Cache lookup
- Includes attributes: http.method, http.url, http.status_code

## Viewing Data in Grafana

1. **Open Grafana**: http://localhost:3000
   - User: `admin`
   - Password: `admin_secure_2024`

2. **View Dashboards**:
   - Overview: http://localhost:3000/d/rhinometric-overview
   - Logs Explorer: http://localhost:3000/d/rhinometric-logs
   - Distributed Tracing: http://localhost:3000/d/rhinometric-tracing

3. **Explore Data**:
   - **Logs**: Go to Explore → Select "Loki" → Query: `{service_name="demo-python-app"}`
   - **Traces**: Go to Explore → Select "Tempo" → Search by service name
   - **Metrics**: Go to Explore → Select "Prometheus" → Query: `http_requests_total`

## Integration in Your Application

### 1. Metrics (Prometheus)

```python
from prometheus_client import Counter, Gauge

# Define metrics
requests = Counter('my_app_requests_total', 'Total requests')
cpu_usage = Gauge('my_app_cpu_usage', 'CPU usage percentage')

# Use in your code
requests.inc()
cpu_usage.set(45.2)
```

### 2. Logs (Loki)

```python
import requests, time

loki_url = "http://localhost:3100/loki/api/v1/push"
log_data = {
    "streams": [{
        "stream": {"service_name": "my-app", "level": "info"},
        "values": [[str(int(time.time() * 1e9)), "My log message"]]
    }]
}
requests.post(loki_url, json=log_data)
```

### 3. Traces (Tempo)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Setup
trace.set_tracer_provider(TracerProvider())
otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

# Use in your code
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("my_operation"):
    # Your code here
    pass
```

## Endpoints

| Service | Protocol | Endpoint | Purpose |
|---------|----------|----------|---------|
| Prometheus | HTTP | `localhost:9090` | Metrics storage & queries |
| Loki | HTTP | `localhost:3100` | Log aggregation |
| Tempo | gRPC | `localhost:4317` | Trace ingestion (OTLP) |
| Tempo | HTTP | `localhost:4318` | Trace ingestion (OTLP/HTTP) |
| Grafana | HTTP | `localhost:3000` | Visualization |

## Troubleshooting

**Metrics not appearing:**
- Verify Prometheus is running: `curl http://localhost:9090/-/healthy`
- Check Prometheus targets: http://localhost:9090/targets

**Logs not showing:**
- Verify Loki is running: `curl http://localhost:3100/ready`
- Check Grafana datasource: Settings → Data Sources → Loki

**Traces not visible:**
- Verify Tempo is running: `curl http://localhost:3200/ready`
- Wait 30 seconds for trace flush
- Search in Explore with service name filter

## Production Recommendations

1. **Use Environment Variables** for endpoints
2. **Add Authentication** (API keys, mTLS)
3. **Batch Operations** for better performance
4. **Error Handling** with retries
5. **Rate Limiting** to avoid overwhelming the system

## Support

📧 Email: support@rhinometric.com  
📚 Docs: https://docs.rhinometric.com  
💬 Community: https://community.rhinometric.com
