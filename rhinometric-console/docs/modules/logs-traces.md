# Module: Logs & Traces

**Version:** 2.7.0  
**Classification:** Internal  
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

Centralized log aggregation and distributed tracing for all monitored services and infrastructure components. These two observability pillars complement metrics to provide full-stack visibility.

## Logs — What It Does

- **Promtail** agents run on each node, collecting log files from Docker containers and system services.
- Logs are shipped to **Loki** for storage and indexing.
- Log streams are labeled by: container name, service name, log level, and host.
- The platform exposes a log search interface via Grafana Explore and optionally via the native UI.
- Correlation Engine queries Loki to enrich anomaly and incident views with relevant log entries.
- Log retention is configurable (default: 15 days in Loki).

## Traces — What It Does

- Services instrumented with OpenTelemetry SDKs export traces via OTLP protocol to the **OpenTelemetry Collector**.
- The Collector forwards trace data to **Jaeger** for storage and visualization.
- Traces capture request flow across service boundaries with span-level detail: timing, status, metadata.
- The Correlation Engine queries Jaeger to find traces related to anomaly events.
- Trace data is also available through Grafana's Jaeger data source for direct exploration.

## What It Does Not Do

### Logs
- Does not parse unstructured logs into structured fields (no built-in log parsing pipeline).
- Does not provide alerting on log patterns (no log-based alert rules).
- Does not support log-to-metric conversion.
- Does not provide a full native log viewer in the frontend — relies on Grafana Explore.

### Traces
- Does not auto-instrument services (SDKs must be integrated by the user).
- Does not provide trace-based alerting.
- Does not perform trace analytics (aggregation, service latency maps).
- Does not support tail-based sampling.

## Architecture

```
┌─────────────┐         ┌──────────┐         ┌──────┐
│  Containers │──logs──▶│ Promtail │────────▶│ Loki │
└─────────────┘         └──────────┘         └──────┘
                                                 │
                                                 ▼
                                         Grafana Explore
                                                 ▲
                                                 │
┌─────────────┐         ┌──────────────┐     ┌────────┐
│  Services   │──OTLP──▶│ OTel Collect │────▶│ Jaeger │
└─────────────┘         └──────────────┘     └────────┘
```

## Infrastructure Components

| Component | Container | Port | Role |
|-----------|-----------|------|------|
| Promtail | `promtail` | — | Log collection agent |
| Loki | `loki` | 3100 | Log storage and query engine |
| OTel Collector | `otel-collector` | 4317 (gRPC), 4318 (HTTP) | Telemetry pipeline |
| Jaeger | `jaeger` | 16686 (UI), 14250 (gRPC) | Trace storage and query |

## API Endpoints

These modules are primarily accessed through Grafana data sources. The backend provides proxy endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/logs/query` | Proxy to Loki LogQL query |
| GET | `/api/traces/search` | Proxy to Jaeger trace search |
| GET | `/api/traces/{trace_id}` | Proxy to Jaeger trace detail |

## Dependencies

- **Promtail**: Collects and ships logs from containers.
- **Loki**: Stores and indexes log data.
- **OpenTelemetry Collector**: Receives and routes trace data.
- **Jaeger**: Stores and serves trace data.
- **Grafana**: Primary UI for log and trace exploration.
- **Correlation Engine**: Queries both Loki and Jaeger during anomaly enrichment.

## Frontend

- **Routes:** `/logs`, `/traces`
- **Key Features:** Embedded Grafana Explore panels for log and trace queries, with pre-filtered views when navigating from anomalies or incidents.

## Known Limitations

1. No native log/trace viewer — depends on Grafana.
2. No log-based alerting.
3. No automatic service instrumentation for traces.
4. Log retention limited to Loki's configured period.
5. No trace sampling configuration in the UI.

---

*Rhinometric Team — info@rhinometric.com*
