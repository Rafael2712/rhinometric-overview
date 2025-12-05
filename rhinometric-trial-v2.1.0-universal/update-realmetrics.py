#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update dashboards with metrics that actually exist"""

import json
import os

DASHBOARDS_DIR = "config/grafana/dashboards"

# Working metric queries verified to exist in Prometheus
FIXES = {
    "redis.json": [
        ("Service Health", 'up{service="redis"}', "short"),
        ("CPU Usage", 'rate(container_cpu_usage_seconds_total{name="rhinometric-redis"}[5m]) * 100', "percent"),
        ("Memory Usage", 'container_memory_usage_bytes{name="rhinometric-redis"}', "bytes"),
        ("Network RX", 'rate(container_network_receive_bytes_total{name="rhinometric-redis"}[5m])', "Bps")
    ],
    "postgres.json": [
        ("Database Up", 'pg_up', "short"),
        ("Scrapes/sec", 'rate(pg_exporter_scrapes_total[5m])', "ops"),
        ("CPU Usage", 'rate(container_cpu_usage_seconds_total{name="rhinometric-postgres"}[5m]) * 100', "percent"),
        ("Memory Usage", 'container_memory_usage_bytes{name="rhinometric-postgres"}', "bytes")
    ],
    "nginx.json": [
        ("Service Up", 'up{service="nginx"}', "short"),
        ("CPU Usage", 'rate(container_cpu_usage_seconds_total{name="rhinometric-nginx"}[5m]) * 100', "percent"),
        ("Memory Usage", 'container_memory_usage_bytes{name="rhinometric-nginx"}', "bytes"),
        ("Network Traffic", 'rate(container_network_receive_bytes_total{name="rhinometric-nginx"}[5m])', "Bps")
    ],
    "otel.json": [
        ("Service Up", 'up{service="otel-collector"}', "short"),
        ("CPU Usage", 'rate(container_cpu_usage_seconds_total{name="rhinometric-otel-collector"}[5m]) * 100', "percent"),
        ("Memory Usage", 'container_memory_usage_bytes{name="rhinometric-otel-collector"}', "bytes"),
        ("Container Start Time", 'container_start_time_seconds{name="rhinometric-otel-collector"}', "dateTimeAsSystem")
    ],
    "tracing.json": [
        ("Tempo Up", 'up{service="tempo"}', "short"),
        ("Spans Received/s", 'rate(tempo_distributor_spans_received_total[5m])', "spansps"),
        ("Bytes Received/s", 'rate(tempo_distributor_bytes_received_total[5m])', "Bps"),
        ("Memory Usage", 'container_memory_usage_bytes{name="rhinometric-tempo"}', "bytes")
    ],
    "api-proxy.json": [
        ("Service Up", 'up{service="api-proxy"}', "short"),
        ("CPU Usage", 'rate(container_cpu_usage_seconds_total{name="rhinometric-api-proxy"}[5m]) * 100', "percent"),
        ("Memory Usage", 'container_memory_usage_bytes{name="rhinometric-api-proxy"}', "bytes"),
        ("Network I/O", 'rate(container_network_transmit_bytes_total{name="rhinometric-api-proxy"}[5m])', "Bps")
    ],
    "license-server.json": [
        ("Service Up", 'up{service="license-server"}', "short"),
        ("Request Rate", 'rate(http_requests_total{service="license-server"}[5m])', "reqps"),
        ("CPU Usage", 'rate(container_cpu_usage_seconds_total{name="rhinometric-license-server-v2"}[5m]) * 100', "percent"),
        ("Memory Usage", 'container_memory_usage_bytes{name="rhinometric-license-server-v2"}', "bytes")
    ],
    "alertmanager.json": [
        ("Service Up", 'up{service="alertmanager"}', "short"),
        ("Active Alerts", 'sum(alertmanager_alerts{state="active"})', "short"),
        ("CPU Usage", 'rate(container_cpu_usage_seconds_total{name="rhinometric-alertmanager"}[5m]) * 100', "percent"),
        ("Memory Usage", 'container_memory_usage_bytes{name="rhinometric-alertmanager"}', "bytes")
    ],
    "license-users.json": [
        ("Total Users", 'grafana_stat_totals_users', "short"),
        ("Total Dashboards", 'grafana_stat_totals_dashboard', "short"),
        ("Data Sources", 'grafana_stat_totals_datasource', "short"),
        ("API Request Rate", 'rate(grafana_api_dataproxy_request_all_milliseconds_count[5m])', "reqps")
    ]
}

def update_dashboard(filename, queries):
    filepath = os.path.join(DASHBOARDS_DIR, filename)
    if not os.path.exists(filepath):
        print(f"[SKIP] {filename}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        dash = json.load(f)
    
    # Create new panels
    panels = []
    
    # Top row: stat panels
    for i, (title, expr, unit) in enumerate(queries[:4]):
        panels.append({
            "type": "stat",
            "title": title,
            "gridPos": {"x": i * 6, "y": 0, "w": 6, "h": 4},
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "targets": [{"expr": expr, "refId": "A"}],
            "options": {"graphMode": "area", "colorMode": "value"},
            "fieldConfig": {"defaults": {"unit": unit, "color": {"mode": "thresholds"}}}
        })
    
    # Bottom row: timeseries
    for i, (title, expr, unit) in enumerate(queries[:2]):
        panels.append({
            "type": "timeseries",
            "title": title + " Over Time",
            "gridPos": {"x": i * 12, "y": 4, "w": 12, "h": 8},
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "targets": [{"expr": expr, "refId": "A", "legendFormat": "{{name}}"}],
            "options": {"legend": {"displayMode": "table", "placement": "right"}},
            "fieldConfig": {"defaults": {"unit": unit, "custom": {"lineWidth": 2}}}
        })
    
    dash["panels"] = panels
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(dash, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] {filename}")

def main():
    print("Updating dashboards with real metrics...")
    for filename, queries in FIXES.items():
        update_dashboard(filename, queries)
    print(f"\n[DONE] Updated {len(FIXES)} dashboards")

if __name__ == "__main__":
    main()
