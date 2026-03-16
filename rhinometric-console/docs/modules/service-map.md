# Module: Service Map

**Version:** 2.7.0  
**Classification:** Internal  
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

Visualize the dependency topology of monitored services and display real-time health status and anomaly propagation across the graph.

## What It Does

- Renders an interactive graph of services as nodes and their dependencies as directed edges.
- Node color indicates health status: green (healthy), yellow (degraded), red (down/anomalous).
- Edge thickness indicates traffic volume or latency between connected services.
- Dependencies are defined manually via the UI or inferred from trace data when available.
- Highlights active anomaly groups by animating affected nodes.
- Selecting a node shows: service details, current anomalies, recent alerts, and Grafana deep link.
- The graph is used by the Root Cause module to traverse dependencies during analysis.

## What It Does Not Do

- Does not auto-discover dependencies from network traffic.
- Does not support multiple map views or saved layouts.
- Does not show historical topology changes over time.
- Does not integrate with infrastructure-as-code definitions.

## Data Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `source_service_id` | UUID | FK — upstream service |
| `target_service_id` | UUID | FK — downstream service |
| `dependency_type` | Enum | http, grpc, database, queue, custom |
| `created_at` | DateTime | When dependency was registered |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/service-map/` | Full dependency graph |
| POST | `/api/service-map/edges` | Add a dependency edge |
| DELETE | `/api/service-map/edges/{id}` | Remove a dependency edge |
| GET | `/api/service-map/neighbors/{service_id}` | Get immediate dependencies |

## Dependencies

- **Services Module**: Provides registered service nodes.
- **AI Anomaly Detector**: Colors nodes by anomaly status.
- **Root Cause Module**: Consumes the graph for dependency traversal.
- **PostgreSQL**: Stores dependency edges.

## Frontend

- **Route:** `/service-map`
- **Key Features:** Force-directed graph layout (D3.js or similar), zoom/pan, node selection, anomaly animation, health status overlay.

## Known Limitations

1. Dependencies are mostly manual — no auto-discovery.
2. No layout persistence (graph re-renders on each page load).
3. Performance degrades beyond ~100 nodes.
4. No historical view of topology changes.

---

*Rhinometric Team — info@rhinometric.com*
