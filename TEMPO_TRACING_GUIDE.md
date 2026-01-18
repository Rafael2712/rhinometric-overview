# 🔍 RHINOMETRIC v2.4.0 - Tempo Distributed Tracing Guide

## 📋 Overview

Tempo está completamente configurado y listo para recibir trazas distribuidas. El dashboard "Rhinometric - Distributed Tracing" mostrará datos una vez que las aplicaciones envíen trazas.

---

## ✅ Estado Actual

### Servicios Configurados:
- ✅ **Tempo**: Corriendo en puerto 3200 (HTTP), 4317 (gRPC)
- ✅ **OTEL Collector**: Configurado para recibir y enviar trazas a Tempo
- ✅ **Grafana**: Datasource de Tempo configurado
- ✅ **Dashboard**: "Rhinometric - Distributed Tracing" listo

### Endpoints Disponibles:
```
OTEL Collector (para enviar trazas):
  - gRPC: localhost:4317
  - HTTP: localhost:4318

Tempo (consulta directa):
  - HTTP: localhost:3200
  - Grafana datasource: http://rhinometric-tempo:3200
```

---

## 🚀 Cómo Generar Trazas de Prueba

### Opción 1: Generador Simple de Python

1. **Instalar dependencias**:
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
```

2. **Ejecutar generador**:
```bash
python3 generate-traces-simple.py
```

Esto generará trazas simuladas cada 2-5 segundos.

3. **Verificar en Grafana**:
   - Ir a http://localhost:80
   - Abrir dashboard "Rhinometric - Distributed Tracing"
   - Esperar 30-60 segundos para ver las trazas

---

### Opción 2: Instrumentar una Aplicación Real

#### Python (FastAPI/Flask):
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Configure tracer
trace.set_tracer_provider(TracerProvider())
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

tracer = trace.get_tracer(__name__)

# Use in your code
with tracer.start_as_current_span("my-operation"):
    # Your code here
    pass
```

#### Node.js (Express):
```javascript
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({
    url: 'http://localhost:4317'
  })
});

sdk.start();
```

#### Java (Spring Boot):
```yaml
# application.yml
otel:
  exporter:
    otlp:
      endpoint: http://localhost:4317
  traces:
    exporter: otlp
```

---

### Opción 3: Usar cURL para Trazas HTTP

```bash
# Enviar traza simple via HTTP (JSON)
curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{
    "resourceSpans": [{
      "resource": {
        "attributes": [{
          "key": "service.name",
          "value": {"stringValue": "test-service"}
        }]
      },
      "scopeSpans": [{
        "spans": [{
          "traceId": "5B8EFFF798038103D269B633813FC60C",
          "spanId": "EEE19B7EC3C1B174",
          "name": "test-operation",
          "kind": 1,
          "startTimeUnixNano": "1544712660000000000",
          "endTimeUnixNano": "1544712661000000000"
        }]
      }]
    }]
  }'
```

---

## 🔧 Troubleshooting

### Dashboard no muestra trazas

1. **Verificar que OTEL Collector recibe trazas**:
```bash
docker logs rhinometric-otel-collector --tail 50 | grep -i trace
```

2. **Verificar que Tempo recibe trazas**:
```bash
docker logs rhinometric-tempo --tail 50 | grep -i span
```

3. **Verificar conectividad**:
```bash
curl http://localhost:4317
curl http://localhost:3200/ready
```

### OTEL Collector no acepta trazas

Verificar configuración:
```bash
docker exec rhinometric-otel-collector cat /etc/otel-collector-config.yml | grep -A 10 receivers
```

Debería mostrar:
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
```

---

## 📊 Consultar Trazas en Grafana

### Vía Dashboard:
1. Abrir http://localhost:80
2. Buscar dashboard "Rhinometric - Distributed Tracing"
3. Ajustar rango de tiempo (últimos 15 minutos)

### Vía Explore:
1. Ir a Explore (ícono de brújula)
2. Seleccionar datasource "Tempo"
3. Consultar con TraceQL:
```
{service.name="rhinometric-trace-generator"}
```

### TraceQL Queries Útiles:

```traceql
# Todas las trazas con errores
{status=error}

# Trazas lentas (>1s)
{duration>1s}

# Trazas de un servicio específico
{service.name="api-gateway"}

# Trazas con HTTP 500
{http.status_code=500}

# Trazas de operaciones de base de datos
{span.kind=client && db.system="postgresql"}
```

---

## 🎯 Métricas desde Trazas

OTEL Collector genera métricas automáticamente desde las trazas:

```
# Prometheus metrics endpoint
http://localhost:8889/metrics
```

Métricas disponibles:
- `traces_receiver_accepted_spans` - Trazas recibidas
- `traces_exporter_sent_spans` - Trazas enviadas a Tempo
- `traces_processor_batch_batch_send_size` - Tamaño de batches

---

## 📚 Referencias

- **OpenTelemetry Docs**: https://opentelemetry.io/docs/
- **Tempo Docs**: https://grafana.com/docs/tempo/latest/
- **TraceQL**: https://grafana.com/docs/tempo/latest/traceql/
- **OTEL Collector**: https://opentelemetry.io/docs/collector/

---

## ✅ Checklist de Configuración

- [x] Tempo corriendo y saludable
- [x] OTEL Collector configurado
- [x] Endpoints expuestos (4317, 4318, 3200)
- [x] Grafana datasource Tempo configurado
- [x] Dashboard "Distributed Tracing" disponible
- [ ] Aplicación instrumentada enviando trazas
- [ ] Trazas visibles en dashboard

**Estado**: Infraestructura lista. Necesita aplicaciones instrumentadas para generar trazas.

---

**Rhinometric v2.4.0** - Powered by Tempo + OpenTelemetry
