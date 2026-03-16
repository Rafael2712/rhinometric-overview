# Module: Correlation Engine

**Version:** 2.7.0
**Classification:** Internal
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

Link signals across metrics, logs, and optionally traces to provide context-enriched views of operational events. When an anomaly or alert fires, the correlation engine identifies related data points from complementary observability sources.

## What It Does

- Accepts a trigger context (service ID, time window, metric name) and searches for related signals.
- Correlates multiple signal types:
  - **Metrics** (from VictoriaMetrics/Prometheus): Identifies co-occurring metric deviations across related services.
  - **Logs** (from Loki): Searches for error-level log entries within the trigger time window for the affected service.
  - **Traces** (from Jaeger, when available): Finds traces with elevated latency or error status during the anomaly period. Trace correlation requires applications to be instrumented with OpenTelemetry SDKs.
- Results are ranked by temporal proximity and relevance score.
- Correlation results are attached to anomaly group views and incident timelines.

## What It Does Not Do

- Does not perform causal analysis (see Root Cause module).
- Does not create new alerts from correlated data.
- Does not support user-defined correlation rules.
- Does not correlate across external data sources (only VictoriaMetrics/Loki, and optionally Jaeger).

## Architecture

```
Anomaly Event / Alert
        │
        ▼
Correlation Engine
   ├──▶ VictoriaMetrics (co-occurring metric anomalies)
   ├──▶ Loki (error logs in time window)
   └──▶ Jaeger (traces, when instrumented apps are available)
        │
        ▼
Enriched Context → Anomaly Detail / Incident Timeline
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/correlation/correlate` | Correlate an event with observability data in a time window |
| GET | `/api/correlation/health` | Correlation engine health check |
| GET | `/api/correlation/config` | Current correlation engine configuration |

## Dependencies

- **VictoriaMetrics**: Metric time-series queries.
- **Loki**: Log queries via LogQL.
- **Jaeger**: Trace queries via Jaeger API (when trace data is available).
- **AI Anomaly Detection**: Provides trigger context.
- **Incident Module**: Displays correlated data in incident timeline.

## Frontend

- **Route:** `/correlation`
- **Key Features:** Unified view of metrics + logs (+ traces when available) for a selected time window and service. Expandable signal cards with links to Grafana and Loki UIs.

## Known Limitations

1. No user-defined correlation rules.
2. Performance degrades with large time windows (>6 hours).
3. Log correlation depends on structured logging with service labels.
4. Trace correlation requires proper span propagation (OpenTelemetry) and is only available when applications emit trace data.

---

*Rhinometric Team — info@rhinometric.com*
