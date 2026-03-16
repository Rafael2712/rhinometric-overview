# Module: Services

**Version:** 2.7.0
**Classification:** Internal
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

Central registry of all monitored endpoints. **Services are the primary entity around which the entire Rhinometric platform is organized.** Every other module — anomalies, alerts, incidents, SLOs, root cause analysis, service map — references services as the core unit of observation. The commercial licensing model is also based on the number of monitored services.

## What It Does

- Registers services with name, URL, protocol (HTTP/HTTPS/TCP), check interval, and expected status code.
- Executes periodic health checks via Blackbox Exporter using Prometheus `probe_success` and `probe_duration_seconds` metrics.
- Displays real-time status (UP/DOWN/DEGRADED) for each registered service.
- Provides a consolidated dashboard with sortable/filterable service list.
- Calculates availability percentage over configurable time windows (1h, 24h, 7d, 30d).
- Supports service grouping using tags.
- Exposes Grafana deep links per service for detailed metric exploration (CPU, memory, latency, HTTP errors, saturation).

## What It Does Not Do

- Does not collect application-level metrics (APM). It monitors endpoint availability only.
- Does not automatically discover services. All services must be registered manually.
- Does not support dependency mapping by itself (see Service Map module).
- Does not scale well beyond ~50 services in the current UI (pagination not yet implemented).

## Data Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `name` | String | Display name |
| `url` | String | Endpoint URL |
| `protocol` | Enum | HTTP, HTTPS, TCP |
| `check_interval` | Integer | Seconds between checks |
| `expected_status` | Integer | Expected HTTP status (default: 200) |
| `tags` | Array[String] | Grouping labels |
| `is_active` | Boolean | Whether monitoring is enabled |
| `created_at` | DateTime | Registration timestamp |
| `updated_at` | DateTime | Last modification |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/external-services` | List all services |
| POST | `/api/external-services` | Register a new service |
| GET | `/api/external-services/{service_id}` | Get service details |
| PUT | `/api/external-services/{service_id}` | Update service configuration |
| DELETE | `/api/external-services/{service_id}` | Remove a service |
| GET | `/api/external-services/{service_id}/status` | Current health status |

## Dependencies

- **Prometheus**: Scrapes Blackbox Exporter probe results.
- **Blackbox Exporter**: Performs the actual health check probes.
- **VictoriaMetrics**: Stores long-term availability data.
- **Grafana**: Renders per-service dashboards linked from the service detail view.
- **PostgreSQL**: Stores service configuration.

## Frontend

- **Route:** `/services`
- **Key Components:** Service list table, service detail drawer, add/edit modal.
- **State:** TanStack Query for data fetching with 30-second auto-refresh.

## Known Limitations

1. No bulk import/export of service definitions.
2. UI not optimized for >50 services.
3. No service dependency auto-discovery.
4. Health check only validates HTTP status codes, not response body content.

---

*Rhinometric Team — info@rhinometric.com*
