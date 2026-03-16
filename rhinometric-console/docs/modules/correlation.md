# Module: Correlation Engine

**Version:** 2.7.0  
**Classification:** Internal  
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

Link signals across metrics, logs, and traces to provide context-enriched views of operational events. When an anomaly or alert fires, the correlation engine identifies related data points from complementary observability pillars.

## What It Does

- Accepts a trigger context (service ID, time window, metric name) and searches for related signals.
- Correlates three signal types:
  - **Metrics** (from VictoriaMetrics/Prometheus): Identifies co-occurring metric deviations across related services.
  - **Logs** (from Loki): Searches for error-level log entries within the trigger time window for the affected service.
  - **Traces** (from Jaeger): Finds traces with elevated latency or error status during the anomaly period.
- Results are ranked by temporal proximity and relevance score.
- Correlation results are attached to anomaly group views and incident timelines.

## What It Does Not Do

- Does not perform causal analysis (see Root Cause module).
- Does not create new alerts from correlated data.
- Does not support user-defined correlation rules.
- Does not correlate across external data sources (only Prometheus/Loki/Jaeger).

## Architecture

```
Anomaly Event / Alert
        │
        ▼
Correlation Engine
   ├──▶ VictoriaMetrics (co-occurring metric anomalies)
   ├──▶ Loki (error logs in time window)
   └──▶ Jaeger (high-latency / error traces)
        │
        ▼
Enriched Context → Anomaly Detail / Incident Timeline
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/correlation/` | Query correlations for a service + time range |
| GET | `/api/correlation/{anomaly_group_id}` | Correlations linked to a specific anomaly group |

## Dependencies

- **VictoriaMetrics**: Metric time-series queries.
- **Loki**: Log queries via LogQL.
- **Jaeger**: Trace queries via Jaeger API.
- **AI Anomaly Detector**: Provides trigger context.
- **Incident Module**: Displays correlated data in incident timeline.

## Frontend

- **Route:** `/correlation`
- **Key Features:** Unified view of metrics + logs + traces for a selected time window and service. Expandable signal cards with links to Grafana, Loki, and Jaeger UIs.

## Known Limitations

1. No user-defined correlation rules.
2. Performance degrades with large time windows (>6 hours).
3. Log correlation depends on structured logging with service labels.
4. Trace correlation requires proper span propagation (OpenTelemetry).

---

*Rhinometric Team — info@rhinometric.com*
