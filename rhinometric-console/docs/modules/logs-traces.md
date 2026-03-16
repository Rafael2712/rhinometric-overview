# Module: Logs & Traces

**Version:** 2.7.0
**Classification:** Internal
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

Centralized log aggregation for all monitored services and infrastructure components, with distributed tracing available as a secondary capability for instrumented applications.

---

## Logs (Core Capability)

### What It Does

- **Promtail** agents run alongside containers, collecting log output from Docker services and system components.
- Logs are shipped to **Loki** for storage and indexing.
- Log streams are labeled by: container name, service name, log level, and environment.
- The platform exposes a log search interface via Grafana Explore and optionally via the native UI.
- Correlation Engine queries Loki to enrich anomaly and incident views with relevant log entries.
- Log retention is configurable (default: 15 days in Loki).

### What It Does Not Do

- Does not parse unstructured logs into structured fields (no built-in log parsing pipeline).
- Does not provide alerting on log patterns (no log-based alert rules).
- Does not support log-to-metric conversion.
- Does not provide a full native log viewer in the frontend — relies on Grafana Explore.

---

## Traces (Available Capability)

Distributed tracing is an **available capability** within the platform. The infrastructure (Jaeger + OTel Collector) is deployed and functional, but trace data requires applications to be instrumented with OpenTelemetry SDKs. Currently, only the Rhinometric backend itself emits traces.

For most deployments, **metrics and logs provide the primary observability signals**. Traces become valuable when users instrument their own applications with OpenTelemetry.

### What It Does

- Services instrumented with OpenTelemetry SDKs export traces via OTLP protocol to the **OpenTelemetry Collector**.
- The Collector forwards trace data to **Jaeger** for storage and visualization.
- Traces capture request flow across service boundaries with span-level detail: timing, status, metadata.
- The Correlation Engine can query Jaeger to find traces related to anomaly events (when trace data is available).
- Trace data is also available through Grafana's Jaeger data source for direct exploration.

### What It Does Not Do

- Does not auto-instrument services (SDKs must be integrated by the user).
- Does not provide trace-based alerting.
- Does not perform trace analytics (aggregation, service latency maps).
- Does not support tail-based sampling.

---

## Architecture

```
┌─────────────┐         ┌──────────┐         ┌──────┐
│  Containers │──logs──▶│ Promtail │────────▶│ Loki │  ← Core
└─────────────┘         └──────────┘         └──────┘
                                                 │
                                                 ▼
                                         Grafana Explore
                                                 ▲
                                                 │
┌─────────────┐         ┌──────────────┐     ┌────────┐
│  Services   │──OTLP──▶│ OTel Collect │────▶│ Jaeger │  ← Available
│ (instrumented)        └──────────────┘     └────────┘
└─────────────┘
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
- **Correlation Engine**: Queries Loki (and optionally Jaeger) during anomaly enrichment.

## Frontend

- **Routes:** `/logs`, `/traces`
- **Key Features:** Embedded Grafana Explore panels for log and trace queries, with pre-filtered views when navigating from anomalies or incidents.

## Known Limitations

1. No native log/trace viewer — depends on Grafana.
2. No log-based alerting.
3. No automatic service instrumentation for traces.
4. Log retention limited to Loki's configured period.
5. No trace sampling configuration in the UI.
6. Trace data is only available when applications are instrumented with OpenTelemetry SDKs.

---

*Rhinometric Team — info@rhinometric.com*
