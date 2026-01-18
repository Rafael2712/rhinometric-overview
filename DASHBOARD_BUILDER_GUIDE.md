# RHINOMETRIC Dashboard Builder - User Guide

## Overview

RHINOMETRIC Dashboard Builder v2.4.0 is a visual dashboard creator embedded in Grafana that allows users to create, edit, and save custom dashboards using a drag-and-drop interface.

## Features

### 🎨 Visual Canvas
- **Drag-and-drop grid layout**: Resize and position panels visually
- **Real-time preview**: See your dashboard as you build it
- **Responsive grid**: 24-column grid system with flexible heights

### 📋 Template Library
4 predefined templates to get started quickly:

1. **🏗️ Infrastructure**: CPU, memory, disk, network monitoring
2. **🌐 API Monitoring**: Request rate, error rate, latency, top endpoints
3. **💬 Messaging**: Kafka/RabbitMQ throughput, lag, consumers
4. **🌱 Sustainability (VeriVerde)**: Carbon intensity, renewable energy, ESG score

### 🔧 Panel Types
- **📊 Graph**: Time-series line charts
- **🎯 Gauge**: Circular/linear gauges with thresholds
- **📋 Table**: Data tables with sorting
- **🔢 Stat**: Single value statistics
- **🌡️ Heatmap**: Time-based heatmaps
- **📈 Bar Chart**: Horizontal/vertical bars
- **🥧 Pie Chart**: Percentage distributions
- **📝 Text**: Markdown text panels

### 💾 Persistence
- **Save to backend**: Store dashboards in PostgreSQL
- **Export JSON**: Export to Grafana-compatible JSON format
- **Version control**: Automatic versioning of dashboard changes
- **Audit logging**: Track who created/modified dashboards

## Quick Start

### 1. Load a Template

Click on any template in the sidebar to load it:

```
📋 Templates
┌────────────────────┐
│ 🏗️ Infraestructura │ ← Click to load
├────────────────────┤
│ 🌐 API Monitoring   │
├────────────────────┤
│ 💬 Messaging        │
└────────────────────┘
```

### 2. Add Panels Manually

Click **"+ Add Panel"** button → Configure in sidebar:

```
✏️ Edit Panel
Title: [CPU Usage          ]
Type:  [📊 Graph           ▼]
Data:  [Prometheus         ▼]
Query: [rate(cpu_usage[5m])]
```

### 3. Drag & Resize

Click and drag panels to reposition. Drag corners to resize.

### 4. Save Dashboard

Click **"💾 Save"** → Enter title → Save to backend

### 5. Export JSON

Click **"Export JSON"** → Downloads Grafana-compatible JSON file

## API Integration

### Backend Endpoints

**Base URL**: `http://localhost:8001/api`

#### Create Dashboard
```bash
POST /dashboards
Content-Type: application/json
Authorization: Bearer <jwt-token>

{
  "dashboard": {
    "title": "My Dashboard",
    "description": "Custom monitoring dashboard",
    "tags": ["infrastructure", "production"],
    "panels": [...],
    "time_range": {"from": "now-6h", "to": "now"},
    "refresh": "30s"
  },
  "overwrite": false
}
```

#### List Dashboards
```bash
GET /dashboards?tags=infrastructure&search=cpu
Authorization: Bearer <jwt-token>
```

#### Get Dashboard
```bash
GET /dashboards/{dashboard_id}
Authorization: Bearer <jwt-token>
```

#### Update Dashboard
```bash
PUT /dashboards/{dashboard_id}
Authorization: Bearer <jwt-token>
```

#### Delete Dashboard
```bash
DELETE /dashboards/{dashboard_id}
Authorization: Bearer <jwt-token>
```

#### Export to Grafana JSON
```bash
GET /dashboards/{dashboard_id}/export
Authorization: Bearer <jwt-token>
```

## Architecture

```
┌──────────────────────────────────────────────────┐
│         Grafana Panel (React + TypeScript)       │
│  - Drag-and-drop interface                       │
│  - Template library                              │
│  - Panel editor                                  │
└─────────────────┬────────────────────────────────┘
                  │ HTTP API (port 8001)
┌─────────────────▼────────────────────────────────┐
│       Dashboard Builder Backend (FastAPI)        │
│  - CRUD operations                               │
│  - License validation                            │
│  - Audit logging                                 │
└─────────────────┬────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────┐
│         PostgreSQL Local Database                │
│  - Dashboard configurations                      │
│  - Metadata (versions, authors)                  │
│  - Audit logs                                    │
└──────────────────────────────────────────────────┘
```

## Panel Configuration

### Graph Panel
```json
{
  "type": "graph",
  "datasource": "Prometheus",
  "query": "rate(http_requests_total[5m])",
  "options": {
    "unit": "reqps",
    "color": "blue",
    "lines": true,
    "points": false
  }
}
```

### Gauge Panel
```json
{
  "type": "gauge",
  "datasource": "Prometheus",
  "query": "cpu_usage_percent",
  "options": {
    "unit": "percent",
    "thresholds": [50, 80, 90],
    "max": 100
  }
}
```

### Table Panel
```json
{
  "type": "table",
  "datasource": "Prometheus",
  "query": "topk(10, http_requests_total)",
  "options": {
    "sort": "desc",
    "columns": ["endpoint", "requests"]
  }
}
```

## Datasource Support

| Datasource    | Query Language | Example                                    |
|---------------|----------------|--------------------------------------------|
| **Prometheus**| PromQL         | `rate(cpu_usage[5m])`                      |
| **Loki**      | LogQL          | `{app="api"} |= "error"`                   |
| **Tempo**     | TraceQL        | `{service.name="auth"}`                    |
| **PostgreSQL**| SQL            | `SELECT * FROM metrics WHERE ts > now()-1h`|
| **Redis**     | Redis CLI      | `GET active_sessions`                      |

## Security

### License Validation
All API calls require valid RHINOMETRIC license:
```python
Authorization: Bearer <jwt-token>
```

### On-Premise Only
- ✅ All data stored locally (PostgreSQL)
- ✅ No external API calls
- ✅ No telemetry or tracking
- ✅ Air-gapped deployment supported

### Role-Based Access Control (Future)
```
Admin:  CREATE, READ, UPDATE, DELETE dashboards
Editor: CREATE, READ, UPDATE own dashboards
Viewer: READ dashboards only
```

## Troubleshooting

### Backend Not Responding
```bash
# Check if backend is running
curl http://localhost:8001/

# Expected response:
{
  "service": "RHINOMETRIC Dashboard Builder",
  "version": "2.4.0",
  "status": "healthy"
}
```

### Templates Not Loading
```bash
# Check templates endpoint
curl http://localhost:8001/api/templates

# Should return 4 templates
```

### Save Fails
```
Error: "Missing or invalid authorization header"
Solution: Ensure valid JWT token in Authorization header
```

### Panels Not Rendering
```
Error: Datasource not found
Solution: Check datasource name matches Grafana datasources
```

## Best Practices

### Dashboard Design
1. **Use templates as starting point**: Customize pre-built templates instead of starting from scratch
2. **Organize with tags**: Tag dashboards by category (infrastructure, api, messaging, esg)
3. **Clear naming**: Use descriptive titles (e.g., "Production API Performance" vs "Dashboard 1")
4. **Consistent time ranges**: Use standard ranges (6h, 24h, 7d) for consistency

### Panel Layout
1. **Most important metrics first**: Place critical gauges/stats at top
2. **Group related panels**: CPU/Memory together, Network separate
3. **Use appropriate visualizations**: Gauges for thresholds, graphs for trends, tables for lists
4. **Avoid overcrowding**: Max 6-8 panels per dashboard for readability

### Performance
1. **Optimize queries**: Use `rate()` instead of `increase()` for better performance
2. **Set appropriate refresh**: 30s-1m for production, 5s for troubleshooting
3. **Limit table rows**: Use `topk()` to show only top 10-20 results
4. **Use variables**: Create dashboard variables for dynamic filtering

## Example Dashboards

### Production Infrastructure
```json
{
  "title": "Production Infrastructure",
  "tags": ["infrastructure", "production"],
  "template": "infrastructure",
  "refresh": "30s",
  "time_range": {"from": "now-6h", "to": "now"}
}
```

### API Health Dashboard
```json
{
  "title": "API Health Dashboard",
  "tags": ["api", "monitoring"],
  "template": "api-monitoring",
  "panels": [
    {"title": "Request Rate", "type": "stat", "query": "sum(rate(http_requests[5m]))"},
    {"title": "Error Rate", "type": "gauge", "query": "error_rate_percentage"},
    {"title": "P95 Latency", "type": "graph", "query": "histogram_quantile(0.95, latency)"}
  ]
}
```

### ESG Compliance Dashboard
```json
{
  "title": "VeriVerde ESG Compliance",
  "tags": ["esg", "sustainability"],
  "template": "sustainability",
  "description": "Carbon intensity and renewable energy tracking"
}
```

## Future Enhancements (v2.5)

- [ ] **Real-time collaboration**: Multiple users editing same dashboard
- [ ] **Dashboard folders**: Organize dashboards in hierarchical folders
- [ ] **Snapshot sharing**: Create read-only snapshots with expiration
- [ ] **Alert integration**: Add alert rules directly from panels
- [ ] **Custom panel types**: Plugin system for custom visualizations
- [ ] **Dashboard versioning UI**: View and restore previous versions
- [ ] **Export to PDF**: Generate PDF reports from dashboards

## Support

For issues or feature requests, contact RHINOMETRIC support:
- Email: support@rhinometric.local
- Documentation: http://localhost:3000/docs/dashboard-builder

---

**Version**: 2.4.0  
**Last Updated**: January 2024  
**License**: RHINOMETRIC Proprietary
