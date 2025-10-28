#!/usr/bin/env python3
import json
import os

DASHBOARDS_DIR = "config/grafana/dashboards"

# Map of dashboard files to update with working queries
DASHBOARD_FIXES = {
    "redis.json": {
        "title": "í´´ Rhinometric - Redis Performance",
        "queries": [
            {"panel": "Connected Clients", "expr": 'container_memory_working_set_bytes{name="rhinometric-redis"}', "unit": "bytes"},
            {"panel": "CPU Usage", "expr": 'rate(container_cpu_usage_seconds_total{name="rhinometric-redis"}[5m]) * 100', "unit": "percent"},
            {"panel": "Memory Usage", "expr": 'container_memory_usage_bytes{name="rhinometric-redis"}', "unit": "bytes"},
            {"panel": "Network I/O", "expr": 'rate(container_network_receive_bytes_total{name="rhinometric-redis"}[5m])', "unit": "Bps"}
        ]
    },
    "postgres.json": {
        "title": "í°˜ Rhinometric - PostgreSQL Performance",
        "queries": [
            {"panel": "Database Up", "expr": 'pg_up', "unit": "short"},
            {"panel": "Exporter Scrapes", "expr": 'rate(pg_exporter_scrapes_total[5m])', "unit": "ops"},
            {"panel": "CPU Usage", "expr": 'rate(container_cpu_usage_seconds_total{name="rhinometric-postgres"}[5m]) * 100', "unit": "percent"},
            {"panel": "Memory Usage", "expr": 'container_memory_usage_bytes{name="rhinometric-postgres"}', "unit": "bytes"}
        ]
    },
    "nginx.json": {
        "title": "í¼ Rhinometric - Nginx Gateway",
        "queries": [
            {"panel": "Service Up", "expr": 'up{service="nginx"}', "unit": "short"},
            {"panel": "CPU Usage", "expr": 'rate(container_cpu_usage_seconds_total{name="rhinometric-nginx"}[5m]) * 100', "unit": "percent"},
            {"panel": "Memory Usage", "expr": 'container_memory_usage_bytes{name="rhinometric-nginx"}', "unit": "bytes"},
            {"panel": "Network Traffic", "expr": 'rate(container_network_receive_bytes_total{name="rhinometric-nginx"}[5m])', "unit": "Bps"}
        ]
    },
    "otel.json": {
        "title": "í³¡ Rhinometric - OTEL Collector",
        "queries": [
            {"panel": "Service Up", "expr": 'up{service="otel-collector"}', "unit": "short"},
            {"panel": "CPU Usage", "expr": 'rate(container_cpu_usage_seconds_total{name="rhinometric-otel-collector"}[5m]) * 100', "unit": "percent"},
            {"panel": "Memory Usage", "expr": 'container_memory_usage_bytes{name="rhinometric-otel-collector"}', "unit": "bytes"},
            {"panel": "Process Restarts", "expr": 'container_start_time_seconds{name="rhinometric-otel-collector"}', "unit": "short"}
        ]
    },
    "tracing.json": {
        "title": "í´ Rhinometric - Distributed Tracing",
        "queries": [
            {"panel": "Tempo Up", "expr": 'up{service="tempo"}', "unit": "short"},
            {"panel": "Spans Received", "expr": 'rate(tempo_distributor_spans_received_total[5m])', "unit": "spansps"},
            {"panel": "Bytes Received", "expr": 'rate(tempo_distributor_bytes_received_total[5m])', "unit": "Bps"},
            {"panel": "Memory Usage", "expr": 'container_memory_usage_bytes{name="rhinometric-tempo"}', "unit": "bytes"}
        ]
    },
    "api-proxy.json": {
        "title": "í´Œ Rhinometric - API Proxy",
        "queries": [
            {"panel": "Service Up", "expr": 'up{service="api-proxy"}', "unit": "short"},
            {"panel": "CPU Usage", "expr": 'rate(container_cpu_usage_seconds_total{name="rhinometric-api-proxy"}[5m]) * 100', "unit": "percent"},
            {"panel": "Memory Usage", "expr": 'container_memory_usage_bytes{name="rhinometric-api-proxy"}', "unit": "bytes"},
            {"panel": "Container Restarts", "expr": 'container_start_time_seconds{name="rhinometric-api-proxy"}', "unit": "short"}
        ]
    },
    "license-server.json": {
        "title": "í´ Rhinometric - License Server API",
        "queries": [
            {"panel": "Service Up", "expr": 'up{service="license-server"}', "unit": "short"},
            {"panel": "Request Rate", "expr": 'rate(http_requests_total{service="license-server"}[5m])', "unit": "reqps"},
            {"panel": "CPU Usage", "expr": 'rate(container_cpu_usage_seconds_total{name="rhinometric-license-server-v2"}[5m]) * 100', "unit": "percent"},
            {"panel": "Memory Usage", "expr": 'container_memory_usage_bytes{name="rhinometric-license-server-v2"}', "unit": "bytes"}
        ]
    },
    "alertmanager.json": {
        "title": "í´” Rhinometric - Alertmanager",
        "queries": [
            {"panel": "Service Up", "expr": 'up{service="alertmanager"}', "unit": "short"},
            {"panel": "Active Alerts", "expr": 'sum(alertmanager_alerts{state="active"})', "unit": "short"},
            {"panel": "CPU Usage", "expr": 'rate(container_cpu_usage_seconds_total{name="rhinometric-alertmanager"}[5m]) * 100', "unit": "percent"},
            {"panel": "Memory Usage", "expr": 'container_memory_usage_bytes{name="rhinometric-alertmanager"}', "unit": "bytes"}
        ]
    },
    "license-users.json": {
        "title": "í±¥ Rhinometric - License & Users",
        "queries": [
            {"panel": "Grafana Users", "expr": 'grafana_stat_totals_users', "unit": "short"},
            {"panel": "Active Dashboards", "expr": 'grafana_stat_totals_dashboard', "unit": "short"},
            {"panel": "Data Sources", "expr": 'grafana_stat_totals_datasource', "unit": "short"},
            {"panel": "API Requests", "expr": 'rate(grafana_api_dataproxy_request_all_milliseconds_count[5m])', "unit": "reqps"}
        ]
    }
}

def update_dashboard_with_working_queries(filename, config):
    filepath = os.path.join(DASHBOARDS_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"[SKIP] {filename} not found")
        return
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            dashboard = json.load(f)
        
        # Update title
        dashboard["title"] = config["title"]
        
        # Recreate panels with working queries
        panels = []
        y = 0
        
        # Create stat panels in top row
        for i, query_config in enumerate(config["queries"][:4]):
            x = (i % 4) * 6
            if i > 0 and i % 4 == 0:
                y += 4
                x = 0
            
            panel = {
                "type": "stat",
                "title": query_config["panel"],
                "gridPos": {"x": x, "y": y, "w": 6, "h": 4},
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "targets": [{
                    "expr": query_config["expr"],
                    "refId": "A"
                }],
                "options": {
                    "graphMode": "area",
                    "colorMode": "value"
                },
                "fieldConfig": {
                    "defaults": {
                        "unit": query_config.get("unit", "short"),
                        "color": {"mode": "thresholds"}
                    }
                }
            }
            panels.append(panel)
        
        # Create time series panels for bottom row
        y = 4
        for i, query_config in enumerate(config["queries"]):
            if i < 2:
                x = i * 12
                panel = {
                    "type": "timeseries",
                    "title": query_config["panel"] + " (Time Series)",
                    "gridPos": {"x": x, "y": y, "w": 12, "h": 8},
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "targets": [{
                        "expr": query_config["expr"],
                        "refId": "A",
                        "legendFormat": "{{name}}"
                    }],
                    "options": {
                        "legend": {"displayMode": "table", "placement": "right"},
                        "tooltip": {"mode": "multi"}
                    },
                    "fieldConfig": {
                        "defaults": {
                            "unit": query_config.get("unit", "short"),
                            "custom": {"lineWidth": 2, "fillOpacity": 10}
                        }
                    }
                }
                panels.append(panel)
        
        dashboard["panels"] = panels
        
        # Save updated dashboard
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Updated: {filename}")
        
    except Exception as e:
        print(f"[ERROR] {filename}: {e}")

def main():
    print("=" * 70)
    print("UPDATING DASHBOARDS WITH REAL METRICS")
    print("=" * 70)
    print("")
    
    for filename, config in DASHBOARD_FIXES.items():
        update_dashboard_with_working_queries(filename, config)
    
    print("")
    print(f"[OK] Updated {len(DASHBOARD_FIXES)} dashboards")
    print("")
    print("Restart Grafana: docker restart rhinometric-grafana")

if __name__ == "__main__":
    main()
