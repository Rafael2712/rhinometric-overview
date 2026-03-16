# Module: SLO/SLA Management

**Version:** 2.7.0  
**Classification:** Internal  
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

Define, track, and alert on Service Level Objectives (SLOs) and Service Level Agreements (SLAs) for monitored services. Provides error-budget tracking and proactive alerting before SLA breaches occur.

## What It Does

- Users define SLOs per service with:
  - **Target metric**: Availability (%), latency (p50/p95/p99), error rate (%).
  - **Target value**: e.g., 99.9% availability.
  - **Evaluation period**: Rolling window (7d, 30d, 90d).
- Calculates current SLO compliance by querying VictoriaMetrics for actual metric values.
- Computes **error budget**: the remaining tolerance before the SLO is breached.
  - Example: 99.9% availability over 30 days = 43.2 minutes of allowed downtime.
- Displays burn-rate: how quickly the error budget is being consumed.
- Triggers alerts when error budget drops below configurable thresholds (e.g., 50%, 25%, 10%).
- SLA definitions extend SLOs with contractual metadata (customer name, penalty terms) but are tracked using the same engine.

## What It Does Not Do

- Does not generate SLA reports for external customers (no PDF export).
- Does not track business-level SLIs (e.g., transaction success rate) — limited to infrastructure metrics.
- Does not support composite SLOs (multiple metrics combined into one objective).
- Does not integrate with billing or contract management systems.

## Data Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `service_id` | UUID | Target service |
| `name` | String | SLO display name |
| `metric_type` | Enum | availability, latency_p50, latency_p95, latency_p99, error_rate |
| `target_value` | Float | Target threshold |
| `evaluation_window` | Enum | 7d, 30d, 90d |
| `error_budget_pct` | Float | Computed — remaining budget |
| `burn_rate` | Float | Computed — budget consumption rate |
| `alert_thresholds` | Array[Float] | Budget thresholds for alerts |
| `is_sla` | Boolean | Whether this carries SLA metadata |
| `sla_customer` | String | Customer name (SLA only) |
| `created_at` | DateTime | Creation timestamp |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/slo/` | List all SLOs |
| POST | `/api/slo/` | Create an SLO |
| GET | `/api/slo/{id}` | SLO detail with current compliance |
| PUT | `/api/slo/{id}` | Update SLO configuration |
| DELETE | `/api/slo/{id}` | Remove an SLO |
| GET | `/api/slo/{id}/budget` | Current error budget status |

## Dependencies

- **VictoriaMetrics**: Provides actual metric values for compliance calculation.
- **Services Module**: SLOs are linked to registered services.
- **Alert System**: Error budget exhaustion triggers alerts.
- **PostgreSQL**: Stores SLO definitions and historical compliance snapshots.

## Frontend

- **Route:** `/slo`
- **Key Features:** SLO dashboard with compliance gauges, error budget bars, burn-rate trend charts, SLA list with customer labels.

## Known Limitations

1. No composite SLO support.
2. No PDF SLA reports.
3. Limited to infrastructure-level metrics.
4. Historical compliance data has no automatic archival.
5. Burn-rate calculation is linear — no predictive modeling.

---

*Rhinometric Team — info@rhinometric.com*
