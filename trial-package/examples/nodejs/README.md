# Node.js Integration Example

## Overview
Complete example showing how to send **Metrics**, **Logs**, and **Traces** to Rhinometric platform using Node.js.

## Installation

```bash
npm install
```

## Usage

### Quick Start
```bash
npm start
```

This will:
1. ✅ Send 20 sample metrics to Prometheus
2. ✅ Send 15 log entries to Loki
3. ✅ Send 10 distributed traces to Tempo

### Environment Variables

```bash
export RHINOMETRIC_HOST=localhost  # Default: localhost
node send-observability.js
```

## What Gets Sent

**Metrics (Prometheus)**
- `http_requests_total{method, endpoint, status}` - Counter
- `active_connections` - Gauge
- `http_request_duration_seconds` - Histogram

**Logs (Loki)**
- Structured logs with levels: info, warn, error, debug
- Labels: service_name, level, environment

**Traces (Tempo)**
- Distributed traces with nested spans
- HTTP → Database → Cache pattern

## Integration in Your Express App

```javascript
const express = require('express');
const { trace } = require('@opentelemetry/api');
const prom = require('prom-client');

const app = express();

// Metrics
const httpRequests = new prom.Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'route', 'status']
});

// Middleware for tracing
app.use((req, res, next) => {
  const tracer = trace.getTracer('my-app');
  const span = tracer.startSpan(`${req.method} ${req.path}`);
  
  res.on('finish', () => {
    httpRequests.inc({ method: req.method, route: req.path, status: res.statusCode });
    span.end();
  });
  
  next();
});

app.get('/api/users', (req, res) => {
  res.json({ users: [] });
});

app.listen(3000);
```

## Viewing Data

Visit http://localhost:3000 and login with:
- **User:** admin
- **Password:** admin_secure_2024

Then navigate to:
- **Dashboards** → Rhinometric - Overview
- **Explore** → Select datasource (Loki/Tempo/Prometheus)

## Troubleshooting

**Connection refused:**
```bash
# Check if Rhinometric is running
docker ps | grep rhinometric
```

**Traces not appearing:**
```bash
# Wait 30 seconds for batch flush, then check:
curl http://localhost:3200/api/search
```

**Logs missing:**
```bash
# Verify Loki is ready
curl http://localhost:3100/ready
```

## Production Best Practices

1. **Use Sampling** for traces (don't trace every request)
2. **Add Context** with labels and attributes
3. **Handle Errors** gracefully
4. **Monitor Exporter Health**
5. **Use Batching** for better performance

## Learn More

📚 [OpenTelemetry Node.js Docs](https://opentelemetry.io/docs/instrumentation/js/)  
📚 [Prom-Client GitHub](https://github.com/siimon/prom-client)  
📚 [Grafana Loki](https://grafana.com/docs/loki/latest/)
