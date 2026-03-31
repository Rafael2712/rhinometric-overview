# Logs Explorer — Feature Overview

> **Module:** Logs  
> **Version:** v2.7.0  
> **Status:** Production  
> **Last updated:** 2025-07-14

---

## Summary

The **Logs Explorer** provides a unified interface for searching, filtering and analyzing log
streams from all monitored services. Logs are ingested via the OpenTelemetry Collector, stored
in Loki, and served through a backend API that automatically parses and enriches raw log entries
with structured fields.

The module is designed for operations teams who need to quickly triage issues by filtering across
multiple dimensions — severity level, HTTP method, status code, service, source type, and free-text
search — without writing LogQL queries manually.

---

## Capabilities

### Structured Log Parsing

The backend automatically classifies and extracts fields from five log formats:

| Source Type | Description | Example Fields |
|-------------|-------------|---------------|
| **HTTP Access** | Apache/Nginx combined access logs | Method, path, status code, client IP, response bytes |
| **Error Log** | Apache error log format | Module, error message, client IP |
| **Collector Cycle** | Telemetry collector cycle summaries | Cycle number, duration, signal counts |
| **Collector Signal** | Per-signal delivery results | Signal type, HTTP status, duration |
| **Application** | Generic application logs | Level (auto-detected) |

All entries receive a **normalized severity level** mapped to a five-tier scale:
`DEBUG` → `INFO` → `WARN` → `ERROR` → `FATAL`

### Multi-Dimensional Filtering

Seven server-side filters can be combined freely:

| Filter | Description | Example |
|--------|-------------|---------|
| **Search** | Free-text search across message body | `favicon`, `timeout` |
| **Service** | Filter by monitored service name | Select from dropdown |
| **Level** | Severity filter | `error`, `warn` |
| **Source Type** | Log classification filter | `access_log`, `error_log` |
| **HTTP Method** | Request method filter | `GET`, `POST`, `DELETE` |
| **Status Code** | Exact or range filter | `404`, `4xx`, `5xx` |
| **Path** | URL path substring match | `/api/`, `/health` |

Filters are applied server-side after enrichment, ensuring consistent results regardless of the
original log format.

### Time Range and Limits

- **9 time presets**: 15 minutes to 7 days
- **Configurable result limit**: 100, 200, 500, 1,000, or 2,000 entries
- **Sort direction**: Newest-first (default) or oldest-first

### Log Detail View

Clicking any log entry opens a **three-tab detail panel**:

1. **Parsed Fields** — All extracted fields displayed as key-value pairs with type indicators
2. **Raw Message** — Original log text with one-click copy to clipboard
3. **Stream Labels** — Loki stream metadata (service, environment, source)

### Data Export

Results can be exported in two formats:
- **CSV** — Spreadsheet-compatible, includes all fields and timestamps
- **JSON** — Full structured data with nested fields and stream labels

Exported files are automatically named with the current date/time.

### Keyboard Navigation

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate between log entries |
| `Enter` | Open/close detail panel |
| `Escape` | Close detail panel |

### Statistics Bar

A live statistics bar shows:
- Total entries returned
- Entries before/after filtering
- Active filter badges (click to remove individual filters)

---

## Internal Platform Isolation

The Logs Explorer automatically excludes internal platform infrastructure logs (monitoring stack,
database, proxy, etc.) from the results. Only logs from customer-monitored services are displayed,
ensuring a clean operational view.

---

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/logs` | Raw log proxy with internal filtering |
| `GET /api/logs/enriched` | Parsed, enriched and filtered log entries |
| `GET /api/logs/fields` | Schema documentation of all available fields |

The enriched endpoint returns both the log entries and the set of **available filter options**
dynamically computed from the current result set, enabling the frontend to populate dropdown
menus without additional API calls.

---

## Architecture

```
Browser  →  React Frontend (FilterBar + LogRow + DetailPanel)
                ↓ fetch /api/logs/enriched
         FastAPI Backend (parse + enrich + filter)
                ↓ HTTP
         Loki (log storage, LogQL pre-filtering)
                ↑
         OTel Collector (log ingestion from customer services)
```

---

## Screenshots

*Coming soon — the module is in active production use.*

---

## Roadmap

| Feature | Priority | Status |
|---------|----------|--------|
| Cursor-based pagination | Medium | Planned |
| Real-time tail (WebSocket) | Medium | Planned |
| Saved filter presets | Low | Planned |
| LogQL push-down optimization | Low | Planned |
| Alert integration (link logs to alerts) | Medium | Planned |
