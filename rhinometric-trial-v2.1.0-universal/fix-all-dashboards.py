#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix All Rhinometric Dashboards - Complete Rebuild
Regenerates all 15 dashboards with correct datasource configurations and queries
"""

import json
import os
from datetime import datetime

DASHBOARDS_DIR = "config/grafana/dashboards"

# Template variables that work with actual Prometheus labels
COMMON_TEMPLATE_VARS = [
    {
        "current": {"selected": False, "text": "All", "value": "$__all"},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "definition": "label_values(service)",
        "hide": 0,
        "includeAll": True,
        "label": "Service",
        "multi": True,
        "name": "service",
        "options": [],
        "query": {"query": "label_values(service)", "refId": "StandardVariableQuery"},
        "refresh": 1,
        "regex": "",
        "skipUrlSync": False,
        "sort": 1,
        "type": "query"
    },
    {
        "current": {"selected": False, "text": "All", "value": "$__all"},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "definition": "label_values(job)",
        "hide": 0,
        "includeAll": True,
        "label": "Job",
        "multi": True,
        "name": "job",
        "options": [],
        "query": {"query": "label_values(job)", "refId": "StandardVariableQuery"},
        "refresh": 1,
        "regex": "",
        "skipUrlSync": False,
        "sort": 1,
        "type": "query"
    }
]

# Loki template variable for logs dashboards
LOKI_TEMPLATE_VAR = {
    "current": {"selected": False, "text": "All", "value": "$__all"},
    "datasource": {"type": "loki", "uid": "loki"},
    "definition": "label_values(container)",
    "hide": 0,
    "includeAll": True,
    "label": "Container",
    "multi": True,
    "name": "container",
    "options": [],
    "query": "label_values(container)",
    "refresh": 1,
    "regex": "",
    "skipUrlSync": False,
    "sort": 1,
    "type": "query"
}

def create_base_dashboard(uid, title, tags, description=""):
    """Create base dashboard structure"""
    return {
        "uid": uid,
        "title": title,
        "tags": tags,
        "timezone": "browser",
        "editable": False,
        "graphTooltip": 1,
        "description": description,
        "time": {"from": "now-1h", "to": "now"},
        "timepicker": {
            "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m"],
            "time_options": ["5m", "15m", "1h", "6h", "12h", "24h", "7d"]
        },
        "refresh": "30s",
        "schemaVersion": 39,
        "version": 1,
        "panels": []
    }

def create_timeseries_panel(title, expr, legend_format, grid_pos, datasource_type="prometheus"):
    """Create a time series panel"""
    return {
        "type": "timeseries",
        "title": title,
        "gridPos": grid_pos,
        "datasource": {"type": datasource_type, "uid": datasource_type},
        "targets": [{
            "expr": expr,
            "legendFormat": legend_format,
            "refId": "A",
            "datasource": {"type": datasource_type, "uid": datasource_type}
        }],
        "options": {
            "legend": {"displayMode": "table", "placement": "right", "calcs": ["last", "mean"]},
            "tooltip": {"mode": "multi", "sort": "desc"}
        },
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"lineWidth": 2, "fillOpacity": 10, "gradientMode": "opacity"},
                "unit": "short"
            }
        }
    }

def create_stat_panel(title, expr, grid_pos, unit="short", datasource_type="prometheus"):
    """Create a stat panel"""
    return {
        "type": "stat",
        "title": title,
        "gridPos": grid_pos,
        "datasource": {"type": datasource_type, "uid": datasource_type},
        "targets": [{
            "expr": expr,
            "refId": "A",
            "datasource": {"type": datasource_type, "uid": datasource_type}
        }],
        "options": {
            "graphMode": "area",
            "colorMode": "value",
            "textMode": "value_and_name"
        },
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "unit": unit,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"value": None, "color": "green"},
                        {"value": 80, "color": "yellow"},
                        {"value": 90, "color": "red"}
                    ]
                }
            }
        }
    }

def create_logs_panel(title, expr, grid_pos):
    """Create a logs panel"""
    return {
        "type": "logs",
        "title": title,
        "gridPos": grid_pos,
        "datasource": {"type": "loki", "uid": "loki"},
        "targets": [{
            "expr": expr,
            "refId": "A",
            "datasource": {"type": "loki", "uid": "loki"}
        }],
        "options": {
            "showTime": True,
            "showLabels": True,
            "wrapLogMessage": True,
            "prettifyLogMessage": True,
            "enableLogDetails": True,
            "dedupStrategy": "none",
            "sortOrder": "Descending"
        }
    }

# Dashboard 1: Executive
def create_executive_dashboard():
    dash = create_base_dashboard(
        "rhinometric-executive",
        "🎯 Rhinometric - Executive Dashboard",
        ["rhinometric", "executive", "overview"]
    )
    dash["templating"] = {"list": COMMON_TEMPLATE_VARS}
    
    panels = [
        create_stat_panel("Total Services", 'count(up{service=~"$service"})', {"x": 0, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Services Up", 'count(up{service=~"$service"} == 1)', {"x": 6, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Total Requests (1h)", 'sum(increase(http_requests_total{service=~"$service"}[1h]))', {"x": 12, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Error Rate", 'sum(rate(http_requests_total{service=~"$service",status=~"5.."}[5m])) / sum(rate(http_requests_total{service=~"$service"}[5m])) * 100', {"x": 18, "y": 0, "w": 6, "h": 4}, "percent"),
        create_timeseries_panel("Service Health", 'up{service=~"$service"}', '{{service}}', {"x": 0, "y": 4, "w": 12, "h": 8}),
        create_timeseries_panel("Request Rate", 'sum by (service) (rate(http_requests_total{service=~"$service"}[5m]))', '{{service}}', {"x": 12, "y": 4, "w": 12, "h": 8})
    ]
    dash["panels"] = panels
    return dash

# Dashboard 2: Overview  
def create_overview_dashboard():
    dash = create_base_dashboard(
        "rhinometric-overview",
        "📊 Rhinometric - System Overview",
        ["rhinometric", "overview", "monitoring"]
    )
    dash["templating"] = {"list": COMMON_TEMPLATE_VARS}
    
    panels = [
        create_stat_panel("CPU Usage", '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)', {"x": 0, "y": 0, "w": 6, "h": 4}, "percent"),
        create_stat_panel("Memory Usage", '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100', {"x": 6, "y": 0, "w": 6, "h": 4}, "percent"),
        create_stat_panel("Active Containers", 'count(container_last_seen{name=~"rhinometric.*"})', {"x": 12, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Network In", 'sum(rate(node_network_receive_bytes_total[5m]))', {"x": 18, "y": 0, "w": 6, "h": 4}, "Bps"),
        create_timeseries_panel("CPU Usage by Service", 'sum by (name) (rate(container_cpu_usage_seconds_total{name=~"rhinometric.*"}[5m])) * 100', '{{name}}', {"x": 0, "y": 4, "w": 12, "h": 8}),
        create_timeseries_panel("Memory Usage by Service", 'sum by (name) (container_memory_usage_bytes{name=~"rhinometric.*"})', '{{name}}', {"x": 12, "y": 4, "w": 12, "h": 8})
    ]
    dash["panels"] = panels
    return dash

# Dashboard 3: Prometheus Monitoring
def create_prometheus_dashboard():
    dash = create_base_dashboard(
        "rhinometric-prometheus",
        "📈 Rhinometric - Prometheus Monitoring",
        ["rhinometric", "prometheus", "metrics"]
    )
    dash["templating"] = {"list": COMMON_TEMPLATE_VARS}
    
    panels = [
        create_stat_panel("Total Targets", 'count(up)', {"x": 0, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Up Targets", 'count(up == 1)', {"x": 6, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Failed Targets", 'count(up == 0)', {"x": 12, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("TSDB Size", 'prometheus_tsdb_storage_blocks_bytes', {"x": 18, "y": 0, "w": 6, "h": 4}, "bytes"),
        create_timeseries_panel("Query Rate", 'rate(prometheus_http_requests_total[5m])', '{{handler}}', {"x": 0, "y": 4, "w": 12, "h": 8}),
        create_timeseries_panel("Ingestion Rate", 'rate(prometheus_tsdb_head_samples_appended_total[5m])', 'Samples/sec', {"x": 12, "y": 4, "w": 12, "h": 8})
    ]
    dash["panels"] = panels
    return dash

# Dashboard 4: Logs Explorer
def create_logs_dashboard():
    dash = create_base_dashboard(
        "rhinometric-logs",
        "📋 Rhinometric - Logs Explorer",
        ["rhinometric", "logs", "loki"]
    )
    dash["templating"] = {"list": [LOKI_TEMPLATE_VAR]}
    
    panels = [
        create_logs_panel("All Logs", '{container=~"$container"}', {"x": 0, "y": 0, "w": 24, "h": 12}),
        create_logs_panel("Error Logs", '{container=~"$container"} |= "error" or "ERROR" or "Error"', {"x": 0, "y": 12, "w": 24, "h": 12})
    ]
    dash["panels"] = panels
    return dash

# Dashboard 5: Distributed Tracing
def create_tracing_dashboard():
    dash = create_base_dashboard(
        "rhinometric-tracing",
        "🔍 Rhinometric - Distributed Tracing",
        ["rhinometric", "tracing", "tempo"]
    )
    dash["templating"] = {"list": COMMON_TEMPLATE_VARS}
    
    panels = [
        create_stat_panel("Total Traces (1h)", 'sum(increase(tempo_ingester_traces_created_total[1h]))', {"x": 0, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Trace Rate", 'rate(tempo_ingester_traces_created_total[5m])', {"x": 6, "y": 0, "w": 6, "h": 4}, "tps"),
        create_stat_panel("Total Spans", 'tempo_ingester_live_traces', {"x": 12, "y": 0, "w": 6, "h": 4}),
        create_timeseries_panel("Traces Ingested", 'rate(tempo_distributor_spans_received_total[5m])', '{{service_name}}', {"x": 0, "y": 4, "w": 12, "h": 8}),
        create_timeseries_panel("Trace Duration", 'histogram_quantile(0.95, sum(rate(tempo_request_duration_seconds_bucket[5m])) by (le, route))', '{{route}} (p95)', {"x": 12, "y": 4, "w": 12, "h": 8})
    ]
    dash["panels"] = panels
    return dash

# Dashboard 6: Redis Performance
def create_redis_dashboard():
    dash = create_base_dashboard(
        "rhinometric-redis",
        "🔴 Rhinometric - Redis Performance",
        ["rhinometric", "redis", "cache"]
    )
    
    panels = [
        create_stat_panel("Connected Clients", 'redis_connected_clients{service="redis"}', {"x": 0, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Used Memory", 'redis_memory_used_bytes{service="redis"}', {"x": 6, "y": 0, "w": 6, "h": 4}, "bytes"),
        create_stat_panel("Total Keys", 'sum(redis_db_keys{service="redis"})', {"x": 12, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Hit Rate", 'rate(redis_keyspace_hits_total{service="redis"}[5m]) / (rate(redis_keyspace_hits_total{service="redis"}[5m]) + rate(redis_keyspace_misses_total{service="redis"}[5m])) * 100', {"x": 18, "y": 0, "w": 6, "h": 4}, "percent"),
        create_timeseries_panel("Commands/sec", 'rate(redis_commands_processed_total{service="redis"}[5m])', 'Commands', {"x": 0, "y": 4, "w": 12, "h": 8}),
        create_timeseries_panel("Memory Usage", 'redis_memory_used_bytes{service="redis"}', 'Used Memory', {"x": 12, "y": 4, "w": 12, "h": 8})
    ]
    dash["panels"] = panels
    return dash

# Dashboard 7: PostgreSQL Performance
def create_postgres_dashboard():
    dash = create_base_dashboard(
        "rhinometric-postgres",
        "🐘 Rhinometric - PostgreSQL Performance",
        ["rhinometric", "postgres", "database"]
    )
    
    panels = [
        create_stat_panel("Active Connections", 'pg_stat_activity_count{state="active"}', {"x": 0, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Database Size", 'pg_database_size_bytes{datname="rhinometric_trial"}', {"x": 6, "y": 0, "w": 6, "h": 4}, "bytes"),
        create_stat_panel("Transactions/sec", 'rate(pg_stat_database_xact_commit{datname="rhinometric_trial"}[5m])', {"x": 12, "y": 0, "w": 6, "h": 4}, "tps"),
        create_stat_panel("Cache Hit Rate", 'pg_stat_database_blks_hit{datname="rhinometric_trial"} / (pg_stat_database_blks_hit{datname="rhinometric_trial"} + pg_stat_database_blks_read{datname="rhinometric_trial"}) * 100', {"x": 18, "y": 0, "w": 6, "h": 4}, "percent"),
        create_timeseries_panel("Connections", 'pg_stat_activity_count', '{{state}}', {"x": 0, "y": 4, "w": 12, "h": 8}),
        create_timeseries_panel("Query Duration", 'rate(pg_stat_statements_mean_exec_time{datname="rhinometric_trial"}[5m])', '{{queryid}}', {"x": 12, "y": 4, "w": 12, "h": 8})
    ]
    dash["panels"] = panels
    return dash

# Dashboard 8: API Proxy
def create_api_proxy_dashboard():
    dash = create_base_dashboard(
        "rhinometric-api-proxy",
        "🔌 Rhinometric - API Proxy",
        ["rhinometric", "api-proxy", "apis"]
    )
    
    panels = [
        create_stat_panel("Total Requests", 'sum(http_requests_total{service="api-proxy"})', {"x": 0, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Request Rate", 'rate(http_requests_total{service="api-proxy"}[5m])', {"x": 6, "y": 0, "w": 6, "h": 4}, "reqps"),
        create_stat_panel("Success Rate", 'sum(rate(http_requests_total{service="api-proxy",status=~"2.."}[5m])) / sum(rate(http_requests_total{service="api-proxy"}[5m])) * 100', {"x": 12, "y": 0, "w": 6, "h": 4}, "percent"),
        create_stat_panel("Error Rate", 'sum(rate(http_requests_total{service="api-proxy",status=~"5.."}[5m])) / sum(rate(http_requests_total{service="api-proxy"}[5m])) * 100', {"x": 18, "y": 0, "w": 6, "h": 4}, "percent"),
        create_timeseries_panel("Request Rate by Endpoint", 'sum by (method, path) (rate(http_requests_total{service="api-proxy"}[5m]))', '{{method}} {{path}}', {"x": 0, "y": 4, "w": 12, "h": 8}),
        create_timeseries_panel("Response Time", 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{service="api-proxy"}[5m])) by (le))', 'p95', {"x": 12, "y": 4, "w": 12, "h": 8})
    ]
    dash["panels"] = panels
    return dash

# Dashboard 9: License Server API
def create_license_server_dashboard():
    dash = create_base_dashboard(
        "rhinometric-license-server",
        "🔐 Rhinometric - License Server API",
        ["rhinometric", "license-server", "api"]
    )
    
    panels = [
        create_stat_panel("API Requests", 'sum(increase(http_requests_total{service="license-server"}[1h]))', {"x": 0, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Request Rate", 'rate(http_requests_total{service="license-server"}[5m])', {"x": 6, "y": 0, "w": 6, "h": 4}, "reqps"),
        create_stat_panel("Active Licenses", 'license_active_count', {"x": 12, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("API Health", 'up{service="license-server"}', {"x": 18, "y": 0, "w": 6, "h": 4}),
        create_timeseries_panel("Request Rate by Endpoint", 'sum by (path) (rate(http_requests_total{service="license-server"}[5m]))', '{{path}}', {"x": 0, "y": 4, "w": 12, "h": 8}),
        create_timeseries_panel("Response Time", 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{service="license-server"}[5m])) by (le))', 'p95', {"x": 12, "y": 4, "w": 12, "h": 8})
    ]
    dash["panels"] = panels
    return dash

# Dashboard 10: System Resources
def create_system_dashboard():
    dash = create_base_dashboard(
        "rhinometric-system",
        "💻 Rhinometric - System Resources",
        ["rhinometric", "system", "resources"]
    )
    
    panels = [
        create_stat_panel("CPU Cores", 'count(node_cpu_seconds_total{mode="idle"})', {"x": 0, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Total Memory", 'node_memory_MemTotal_bytes', {"x": 6, "y": 0, "w": 6, "h": 4}, "bytes"),
        create_stat_panel("Disk Total", 'node_filesystem_size_bytes{mountpoint="/"}', {"x": 12, "y": 0, "w": 6, "h": 4}, "bytes"),
        create_stat_panel("Network Interfaces", 'count(node_network_up)', {"x": 18, "y": 0, "w": 6, "h": 4}),
        create_timeseries_panel("CPU Usage", '100 - (avg by (cpu) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)', 'CPU {{cpu}}', {"x": 0, "y": 4, "w": 12, "h": 8}),
        create_timeseries_panel("Memory Usage", 'node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes', 'Used Memory', {"x": 12, "y": 4, "w": 12, "h": 8})
    ]
    dash["panels"] = panels
    return dash

# Dashboard 11: Nginx Gateway
def create_nginx_dashboard():
    dash = create_base_dashboard(
        "rhinometric-nginx",
        "🌐 Rhinometric - Nginx Gateway",
        ["rhinometric", "nginx", "gateway"]
    )
    
    panels = [
        create_stat_panel("Active Connections", 'nginx_connections_active{service="nginx"}', {"x": 0, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Total Requests", 'nginx_http_requests_total{service="nginx"}', {"x": 6, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Request Rate", 'rate(nginx_http_requests_total{service="nginx"}[5m])', {"x": 12, "y": 0, "w": 6, "h": 4}, "reqps"),
        create_stat_panel("Nginx Health", 'up{service="nginx"}', {"x": 18, "y": 0, "w": 6, "h": 4}),
        create_timeseries_panel("Connection States", 'nginx_connections_active{service="nginx"}', 'Active', {"x": 0, "y": 4, "w": 12, "h": 8}),
        create_timeseries_panel("Request Rate", 'rate(nginx_http_requests_total{service="nginx"}[5m])', 'Requests/sec', {"x": 12, "y": 4, "w": 12, "h": 8})
    ]
    dash["panels"] = panels
    return dash

# Dashboard 12: OTEL Collector
def create_otel_dashboard():
    dash = create_base_dashboard(
        "rhinometric-otel",
        "📡 Rhinometric - OTEL Collector",
        ["rhinometric", "otel", "telemetry"]
    )
    
    panels = [
        create_stat_panel("Spans Received", 'sum(increase(otelcol_receiver_accepted_spans[1h]))', {"x": 0, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Metrics Received", 'sum(increase(otelcol_receiver_accepted_metric_points[1h]))', {"x": 6, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Logs Received", 'sum(increase(otelcol_receiver_accepted_log_records[1h]))', {"x": 12, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("OTEL Health", 'up{service="otel-collector"}', {"x": 18, "y": 0, "w": 6, "h": 4}),
        create_timeseries_panel("Span Ingestion Rate", 'rate(otelcol_receiver_accepted_spans[5m])', '{{receiver}}', {"x": 0, "y": 4, "w": 12, "h": 8}),
        create_timeseries_panel("Processor Queue", 'otelcol_processor_batch_batch_send_size', '{{processor}}', {"x": 12, "y": 4, "w": 12, "h": 8})
    ]
    dash["panels"] = panels
    return dash

# Dashboard 13: Alertmanager
def create_alertmanager_dashboard():
    dash = create_base_dashboard(
        "rhinometric-alertmanager",
        "🔔 Rhinometric - Alertmanager",
        ["rhinometric", "alertmanager", "alerts"]
    )
    
    panels = [
        create_stat_panel("Active Alerts", 'sum(alertmanager_alerts{state="active"})', {"x": 0, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Suppressed Alerts", 'sum(alertmanager_alerts{state="suppressed"})', {"x": 6, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Notifications Sent", 'sum(increase(alertmanager_notifications_total[1h]))', {"x": 12, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Alertmanager Health", 'up{service="alertmanager"}', {"x": 18, "y": 0, "w": 6, "h": 4}),
        create_timeseries_panel("Alert Rate", 'sum by (alertname) (rate(alertmanager_alerts_received_total[5m]))', '{{alertname}}', {"x": 0, "y": 4, "w": 12, "h": 8}),
        create_timeseries_panel("Notification Rate", 'sum by (integration) (rate(alertmanager_notifications_total[5m]))', '{{integration}}', {"x": 12, "y": 4, "w": 12, "h": 8})
    ]
    dash["panels"] = panels
    return dash

# Dashboard 14: License & Users
def create_license_users_dashboard():
    dash = create_base_dashboard(
        "rhinometric-license-users",
        "👥 Rhinometric - License & Users",
        ["rhinometric", "license", "users"]
    )
    
    panels = [
        create_stat_panel("Active Licenses", 'license_active_count', {"x": 0, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Expired Licenses", 'license_expired_count', {"x": 6, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Active Users", 'grafana_stat_totals_users', {"x": 12, "y": 0, "w": 6, "h": 4}),
        create_stat_panel("Active Sessions", 'grafana_stat_active_users', {"x": 18, "y": 0, "w": 6, "h": 4}),
        create_timeseries_panel("License Validation Rate", 'rate(license_validations_total[5m])', '{{result}}', {"x": 0, "y": 4, "w": 12, "h": 8}),
        create_timeseries_panel("User Activity", 'grafana_api_user_signup_completed_total', 'Signups', {"x": 12, "y": 4, "w": 12, "h": 8})
    ]
    dash["panels"] = panels
    return dash

def save_dashboard(dashboard, filename):
    """Save dashboard to file"""
    filepath = os.path.join(DASHBOARDS_DIR, filename)
    os.makedirs(DASHBOARDS_DIR, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Created: {filename}")

def main():
    print("=" * 70)
    print("RHINOMETRIC DASHBOARD REGENERATION")
    print("=" * 70)
    print("")
    
    dashboards = [
        (create_executive_dashboard(), "executive.json"),
        (create_overview_dashboard(), "overview.json"),
        (create_prometheus_dashboard(), "prometheus.json"),
        (create_logs_dashboard(), "logs.json"),
        (create_tracing_dashboard(), "tracing.json"),
        (create_redis_dashboard(), "redis.json"),
        (create_postgres_dashboard(), "postgres.json"),
        (create_api_proxy_dashboard(), "api-proxy.json"),
        (create_license_server_dashboard(), "license-server.json"),
        (create_system_dashboard(), "system.json"),
        (create_nginx_dashboard(), "nginx.json"),
        (create_otel_dashboard(), "otel.json"),
        (create_alertmanager_dashboard(), "alertmanager.json"),
        (create_license_users_dashboard(), "license-users.json")
    ]
    
    for dashboard, filename in dashboards:
        save_dashboard(dashboard, filename)
    
    print("")
    print(f"[OK] Regenerated {len(dashboards)} dashboards successfully!")
    print("")
    print("Next steps:")
    print("1. Restart Grafana: docker restart rhinometric-grafana")
    print("2. Wait 30 seconds for provisioning")
    print("3. Verify dashboards at http://localhost:3000")
    print("")

if __name__ == "__main__":
    main()
