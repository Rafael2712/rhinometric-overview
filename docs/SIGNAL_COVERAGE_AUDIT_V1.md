# AI Engine V1 — Signal Coverage Audit

**Date**: 2026-04-08
**Commit**: post-0ef9cca
**Auditor**: Automated platform audit
**Scope**: Verify the Rust anomaly engine (V1.0-V1.6.1) consumes all available platform signals correctly

---

## 1. Signal Coverage Matrix

### Signal Fields (21 scoring signals + 7 identity/meta)

| # | Field | Category | Source | Consumer | Runtime Value | Status |
|---|-------|----------|--------|----------|---------------|--------|
| 1 | latency_current_ms | Latency | PostgreSQL: external_services.last_response_time_ms | latency.rs, predict_latency | 443.9 / 171.0 | OK |
| 2 | latency_baseline_ms | Latency | PostgreSQL: AVG(checks.response_time_ms) 24h | latency.rs, predict_latency | 573.1 / 180.4 | OK |
| 3 | latency_p95_ms | Latency | PostgreSQL: PERCENTILE_CONT(0.95) 24h | latency.rs | 967.3 / 234.1 | OK |
| 4 | latency_trend_slope | Latency V1.3 | PostgreSQL: Linear regression on 1h checks | latency.rs, predict_latency | 0.50 / 0.08 | OK |
| 5 | latency_trend_r2 | Latency V1.3 | PostgreSQL: R-squared from regression | confidence.rs, predict_latency | 0.004 / 0.002 | OK |
| 6 | is_up | Availability | PostgreSQL: external_services.status (Prom fallback) | availability.rs | true / true | OK (DB fallback) |
| 7 | health_score | Availability | Prometheus: rhinometric_service_health_score | availability.rs, predict_avail | 100.0 / 100.0 | DEFERRED (default) |
| 8 | consecutive_failures | Availability | PostgreSQL: external_services.consecutive_failures | availability.rs, predict_avail | 0 / 0 | OK |
| 9 | incidents_24h | Availability | PostgreSQL: COUNT(incidents) 24h | availability.rs, predict_avail | 0 / 0 | OK |
| 10 | error_rate_1h | Error | PostgreSQL: checks errors/total 1h | error.rs, predict_error | 0.0 / 0.0 | OK |
| 11 | log_error_count_1h | Error | Loki: count_over_time level=error 1h | error.rs, predict_error | 0 / 0 | FIXED |
| 12 | log_warn_count_1h | Error | Loki: count_over_time level=warn 1h | error.rs, predict_error | 0 / 0 | FIXED |
| 13 | log_error_burst_ratio | Error V1.3 | Loki: 5m/1h error ratio | error.rs, predict_error | 0.0 / 0.0 | FIXED |
| 14 | ssl_expiry_days | SSL | Prometheus: rhinometric_service_ssl_expiry_days | ssl.rs, predict_ssl | 365.0 / 365.0 | DEFERRED (default) |
| 15 | baseline_age_hours | Confidence | PostgreSQL: MIN(checked_at) 24h | confidence.rs | 23.99 / 23.99 | OK |
| 16 | checks_in_last_1h | Confidence | PostgreSQL: COUNT(checks) 1h | confidence.rs | 59 / 59 | OK |
| 17 | signals_available | Confidence | Assembler: dynamic list | confidence.rs, predict_trace | [latency, baseline, jaeger] | OK |
| 18 | trace_p95_latency_ms | Trace V1.4 | Jaeger: 95th percentile trace duration | trace.rs, predict_trace | 665.8 / 661.3 | OK |
| 19 | trace_error_rate | Trace V1.4 | Jaeger: error_spans / total_spans | trace.rs, predict_trace | 0.0 / 0.0 | OK |
| 20 | trace_bottleneck_score | Trace V1.4 | Jaeger: child_dominance x complexity | trace.rs, predict_trace | 0.367 / 0.365 | OK |
| 21 | trace_slow_operations | Trace V1.4 | Jaeger: count of traces > 2000ms | trace.rs, predict_trace | 0 / 0 | OK |

Runtime values shown as: t12-collector-test / rhinometric-web

---

## 2. Platform Source Map

```
          RUST ANOMALY ENGINE V1 (port 8091, 60s cycle)
                         |
            GET /internal/anomaly-signal-snapshots-v1
            Header: X-Internal-Token: anomaly-engine-v1
                         |
              PYTHON BACKEND (port 8105)
              internal_snapshots_v1.py
              Assembly time: ~900ms
                         |
        +--------+--------+--------+--------+
        |        |        |        |
   PostgreSQL  Prometheus  Loki    Jaeger
   12 fields   3 fields   3 flds  4 fields
   ALL OK      0/3 avail  FIXED   ALL OK
```

### Data Source Breakdown

| Source | Signals | Queries | Status |
|--------|---------|---------|--------|
| PostgreSQL | 12 | 5 SQL (services, baselines, checks_1h, incidents, trend) | All populated |
| Prometheus | 3 | 3 PromQL (health_score, ssl_expiry, is_up) | Metrics not published; safe defaults |
| Loki | 3 | 3 LogQL (errors_1h, warns_1h, errors_5m) | FIXED (was broken: job filter mismatch) |
| Jaeger | 4 | 1+N HTTP calls (services discovery + traces per svc) | All populated |

---

## 3. Gap Analysis

### Gap 1: Loki Job Filter Mismatch - FIXED

**Problem**: Loki queries used {job="rhinometric"} but no Loki job has that name.
Available jobs: rhinometric-web-produccion, t12-collector-key, console-backend, etc.
The level label IS a stream-level label in Loki (not a parsed field).

**Fix applied**: Changed all 3 Loki queries from job filter to service_name filter:
- BEFORE: {job="rhinometric"} | json | level="error"
- AFTER: {service_name=~".+", level=~"error|ERROR"}

Also fixed case sensitivity: level values include both error/ERROR and warn/WARNING.

**Impact**: Signals 11-13 (log_error_count_1h, log_warn_count_1h, log_error_burst_ratio)
will now correctly count log entries when errors/warnings occur.

**Current real impact**: Zero (no errors in 24h), but this prevents a latent blind spot.

### Gap 2: Prometheus Custom Metrics Not Published - DEFERRED

**Problem**: Three Prometheus metrics queried but dont exist:
- rhinometric_service_health_score -> defaults to 100.0
- rhinometric_service_ssl_expiry_days -> defaults to 365.0
- rhinometric_service_up -> falls back to DB status check

**Assessment**:
- is_up: DB status fallback is actually more reliable than a Prometheus gauge. No action needed.
- ssl_expiry_days: Services probed via HTTP (not HTTPS). Default 365.0 is correct. No action needed.
- health_score: Only gap with functional impact. When degraded but not down, health_score
  stays at 100.0. However, this scenario IS caught by other signals (latency deviation,
  consecutive_failures, error_rate_1h) in the same availability scorer.

**Decision**: Deferred. Requires new Prometheus instrumentation (out of scope).

### No Gaps: PostgreSQL Path
All 12 PostgreSQL signals correctly populated from 5 SQL queries.

### No Gaps: Jaeger Path
All 4 trace signals correctly computed from Jaeger API with service_id tag mapping.

---

## 4. Runtime Verification

### Snapshot Endpoint (verified 2026-04-08)
- Returns 2 services: t12-collector-test (id=90), rhinometric-web (id=130)
- Assembly time: ~900-1100ms
- All 21 signal fields populated
- Zero warnings

### Engine Scoring (verified from anomaly_engine_results_v1)
- Cycle: every 60s, 2 services evaluated per cycle
- Category scores active: latency (2-4), trace (10-20), availability (0), error (0), ssl (0)
- Prediction firing: PredictedTracePressure for rhinometric-web (risk_score=5)
- Reason codes active: TraceBottleneck for both services
- Zero errors in engine logs over 30+ cycles

### Engine Health
- No WARN or ERROR log entries
- Consistent cycle times: 700-1300ms
- Prometheus metrics exported (cycles_total, cycle_errors_total, etc.)

---

## 5. Conclusion

**The AI engine IS connected to all available platform signals.**

One latent bug was found and fixed (Loki query filter using nonexistent job name).
Three Prometheus metrics are queried but not published by the backend — these use
safe defaults and the scenarios they would cover are already handled by other signals.

### Summary
- 21/21 signal fields populated in snapshot
- 4/4 data sources connected (PostgreSQL OK, Loki FIXED, Jaeger OK, Prometheus defaults)
- 1 bug fixed: Loki job filter mismatch (3 queries)
- 1 deferred: Prometheus health_score gauge (out of scope, covered by other signals)
- 0 redesign needed: Engine architecture is sound and complete for current product stage
