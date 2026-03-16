# Module: AI Anomaly Detection

**Version:** 2.7.0  
**Classification:** Internal  
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

Automatically detect abnormal metric behavior across all monitored services without requiring manual threshold configuration. The module groups related anomalies and assigns severity scores.

## What It Does

- Runs as a standalone Python container (`ai-anomaly`) that connects to VictoriaMetrics via PromQL.
- Pulls metric time-series for all active services at configurable intervals (default: 5 minutes).
- Applies an IsolationForest ensemble model to each metric series.
- Scores each data point with an anomaly probability (0.0–1.0).
- Groups co-occurring anomalies by service and time window into **anomaly groups**.
- Assigns severity (Low, Medium, High, Critical) based on anomaly score distribution.
- Applies a **30% MAD threshold guard**: groups where fewer than 30% of data points exceed the Median Absolute Deviation threshold are discarded as noise.
- Stores detected anomaly groups in PostgreSQL for frontend consumption.
- Generates machine-readable anomaly events consumed by the Alert Rules engine.

## What It Does Not Do

- Does not learn from user feedback (no reinforcement loop).
- Does not perform root cause analysis (see Root Cause module).
- Does not generate natural-language explanations (see AI Insights module).
- Does not replace rule-based alerting — it complements it.
- Does not support custom model parameters per service (global config only).

## Architecture

```
VictoriaMetrics ──PromQL──▶ ai-anomaly container ──PostgreSQL──▶ Backend API ──▶ Frontend
                                    │
                                    └──▶ anomaly_events table ──▶ Alert Rules Engine
```

## Data Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `service_id` | UUID | FK to services |
| `metric_name` | String | e.g., `cpu_usage`, `latency_p99` |
| `anomaly_score` | Float | 0.0–1.0 |
| `severity` | Enum | Low, Medium, High, Critical |
| `group_id` | UUID | Groups co-occurring anomalies |
| `data_points` | Integer | Number of samples in the analysis window |
| `mad_exceedance_pct` | Float | Percentage of points above MAD threshold |
| `detected_at` | DateTime | Detection timestamp |
| `resolved_at` | DateTime | Null until anomaly subsides |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/anomalies/` | List anomaly groups with filters |
| GET | `/api/anomalies/{group_id}` | Detail for a specific group |
| GET | `/api/anomalies/active` | Currently unresolved groups |
| GET | `/api/anomalies/stats` | Aggregated statistics |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ANOMALY_CHECK_INTERVAL` | `300` | Seconds between analysis runs |
| `ANOMALY_SCORE_THRESHOLD` | `0.7` | Minimum score to flag as anomaly |
| `MAD_THRESHOLD_PCT` | `0.3` | Minimum data point exceedance ratio |
| `ISOLATION_FOREST_ESTIMATORS` | `100` | Number of trees in the ensemble |
| `LOOKBACK_WINDOW` | `3600` | Seconds of history to analyze |

## Dependencies

- **VictoriaMetrics**: Source of metric time-series data.
- **PostgreSQL**: Stores anomaly groups and scores.
- **Backend API**: Serves anomaly data to the frontend.
- **Alert Rules Engine**: Consumes anomaly events to trigger alerts.

## Frontend

- **Route:** `/anomalies`
- **Key Features:** Group-level view with expandable detail, severity badges, time-range filter, Grafana deep links per group.
- **Error Handling:** Graceful 401 redirect if authentication expires mid-session.

## Known Limitations

1. Single global model — no per-service tuning.
2. Cold-start: needs ~24 hours of metric data to produce reliable results.
3. No feedback mechanism to mark false positives.
4. Analysis runs are sequential (one service at a time), limiting throughput at scale.

---

*Rhinometric Team — info@rhinometric.com*
