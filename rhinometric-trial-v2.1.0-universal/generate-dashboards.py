#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
 RHINOMETRIC DASHBOARD GENERATOR - v2.1.0 ENTERPRISE
═══════════════════════════════════════════════════════════════════════════

Generates 15 interconnected Grafana dashboards with full observability.
"""

import json
import os
from datetime import datetime

OUTPUT_DIR = "config/grafana/dashboards"

def create_base_dashboard(uid, title, tags, description=""):
    """Base dashboard structure"""
    return {
        "uid": uid,
        "title": title,
        "tags": tags,
        "timezone": "browser",
        "editable": False,
        "graphTooltip": 1,
        "time": {"from": "now-1h", "to": "now"},
        "timepicker": {
            "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m"],
            "time_options": ["5m", "15m", "1h", "6h", "12h", "24h", "7d"]
        },
        "templating": {"list": []},
        "annotations": {"list": [
            {
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "enable": True,
                "expr": "changes(up[1m]) > 0",
                "iconColor": "red",
                "name": "Service Restarts",
                "tagKeys": "service,container"
            }
        ]},
        "panels": [],
        "refresh": "30s",
        "schemaVersion": 38,
        "version": 1,
        "description": description
    }

def add_variable(dashboard, name, query, label="", multi=True):
    """Add template variable"""
    dashboard["templating"]["list"].append({
        "current": {"selected": False, "text": "All", "value": "$__all"},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "definition": query,
        "hide": 0,
        "includeAll": True,
        "label": label or name.title(),
        "multi": multi,
        "name": name,
        "options": [],
        "query": {"query": query, "refId": "StandardVariableQuery"},
        "refresh": 1,
        "regex": "",
        "skipUrlSync": False,
        "sort": 1,
        "type": "query"
    })

def create_stat_panel(title, expr, unit="short", gridPos=None, thresholds=None):
    """Create stat panel"""
    panel = {
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "mappings": [],
                "thresholds": thresholds or {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 70},
                        {"color": "red", "value": 90}
                    ]
                },
                "unit": unit
            }
        },
        "gridPos": gridPos or {"h": 4, "w": 6, "x": 0, "y": 0},
        "options": {
            "colorMode": "value",
            "graphMode": "area",
            "justifyMode": "auto",
            "orientation": "auto",
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": False
            },
            "textMode": "auto"
        },
        "targets": [{
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "expr": expr,
            "refId": "A"
        }],
        "title": title,
        "type": "stat"
    }
    return panel

def create_graph_panel(title, targets, gridPos=None, unit="short"):
    """Create time series graph"""
    return {
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {
                    "axisCenteredZero": False,
                    "axisColorMode": "text",
                    "axisLabel": "",
                    "axisPlacement": "auto",
                    "barAlignment": 0,
                    "drawStyle": "line",
                    "fillOpacity": 10,
                    "gradientMode": "none",
                    "hideFrom": {"tooltip": False, "viz": False, "legend": False},
                    "lineInterpolation": "linear",
                    "lineWidth": 1,
                    "pointSize": 5,
                    "scaleDistribution": {"type": "linear"},
                    "showPoints": "never",
                    "spanNulls": False,
                    "stacking": {"group": "A", "mode": "none"},
                    "thresholdsStyle": {"mode": "off"}
                },
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [{"color": "green", "value": None}]
                },
                "unit": unit
            }
        },
        "gridPos": gridPos or {"h": 8, "w": 12, "x": 0, "y": 0},
        "options": {
            "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
            "tooltip": {"mode": "multi", "sort": "none"}
        },
        "targets": targets,
        "title": title,
        "type": "timeseries"
    }

def create_logs_panel(title, gridPos=None):
    """Create Loki logs panel"""
    return {
        "datasource": {"type": "loki", "uid": "loki"},
        "gridPos": gridPos or {"h": 12, "w": 24, "x": 0, "y": 0},
        "options": {
            "dedupStrategy": "none",
            "enableLogDetails": True,
            "prettifyLogMessage": False,
            "showCommonLabels": False,
            "showLabels": False,
            "showTime": True,
            "sortOrder": "Descending",
            "wrapLogMessage": False
        },
        "targets": [{
            "datasource": {"type": "loki", "uid": "loki"},
            "expr": '{container=~"$container", service=~"$service"}',
            "refId": "A"
        }],
        "title": title,
        "type": "logs"
    }

def create_traces_panel(title, gridPos=None):
    """Create Tempo traces panel"""
    return {
        "datasource": {"type": "tempo", "uid": "tempo"},
        "gridPos": gridPos or {"h": 12, "w": 24, "x": 0, "y": 0},
        "targets": [{
            "datasource": {"type": "tempo", "uid": "tempo"},
            "query": {"serviceName": "$service", "spanName": "", "minDuration": "", "maxDuration": "", "search": "", "limit": 20},
            "queryType": "nativeSearch",
            "refId": "A"
        }],
        "title": title,
        "type": "traces"
    }

# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD 1: EXECUTIVE DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

def generate_executive_dashboard():
    """Executive KPIs and SLAs"""
    dashboard = create_base_dashboard(
        "rhinometric-executive",
        "🎯 Rhinometric - Executive Dashboard",
        ["rhinometric", "executive", "kpis"],
        "High-level KPIs for executives and stakeholders"
    )
    
    panels = []
    y_pos = 0
    
    # Row 1: Key Metrics
    panels.append(create_stat_panel(
        "System Uptime",
        "avg(up{job=~'.*'})",
        "percentunit",
        {"h": 6, "w": 4, "x": 0, "y": y_pos},
        {"mode": "absolute", "steps": [
            {"color": "red", "value": None},
            {"color": "yellow", "value": 0.95},
            {"color": "green", "value": 0.99}
        ]}
    ))
    
    panels.append(create_stat_panel(
        "Active Services",
        "count(up == 1)",
        "short",
        {"h": 6, "w": 4, "x": 4, "y": y_pos}
    ))
    
    panels.append(create_stat_panel(
        "Total Requests/s",
        "sum(rate(prometheus_http_requests_total[5m]))",
        "reqps",
        {"h": 6, "w": 4, "x": 8, "y": y_pos}
    ))
    
    panels.append(create_stat_panel(
        "Error Rate",
        "sum(rate(prometheus_http_requests_total{code=~'5..'}[5m])) / sum(rate(prometheus_http_requests_total[5m])) * 100",
        "percent",
        {"h": 6, "w": 4, "x": 12, "y": y_pos},
        {"mode": "absolute", "steps": [
            {"color": "green", "value": None},
            {"color": "yellow", "value": 1},
            {"color": "red", "value": 5}
        ]}
    ))
    
    panels.append(create_stat_panel(
        "Avg Response Time",
        "histogram_quantile(0.95, rate(prometheus_http_request_duration_seconds_bucket[5m]))",
        "s",
        {"h": 6, "w": 4, "x": 16, "y": y_pos}
    ))
    
    panels.append(create_stat_panel(
        "Active Alerts",
        "count(ALERTS{alertstate='firing'})",
        "short",
        {"h": 6, "w": 4, "x": 20, "y": y_pos},
        {"mode": "absolute", "steps": [
            {"color": "green", "value": None},
            {"color": "yellow", "value": 1},
            {"color": "red", "value": 5}
        ]}
    ))
    
    y_pos += 6
    
    # Row 2: Resource Utilization
    panels.append(create_graph_panel(
        "CPU Usage Trend",
        [{
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "expr": "100 - (avg by(instance) (rate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)",
            "legendFormat": "{{instance}}",
            "refId": "A"
        }],
        {"h": 8, "w": 12, "x": 0, "y": y_pos},
        "percent"
    ))
    
    panels.append(create_graph_panel(
        "Memory Usage Trend",
        [{
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "legendFormat": "{{instance}}",
            "refId": "A"
        }],
        {"h": 8, "w": 12, "x": 12, "y": y_pos},
        "percent"
    ))
    
    dashboard["panels"] = panels
    return dashboard

# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD 2: RHINOMETRIC OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

def generate_overview_dashboard():
    """Main overview with drilldown links"""
    dashboard = create_base_dashboard(
        "rhinometric-overview",
        "🏠 Rhinometric - Overview",
        ["rhinometric", "overview"]
    )
    
    add_variable(dashboard, "container", "label_values(container_last_seen, name)")
    add_variable(dashboard, "service", "label_values(up, job)")
    
    panels = []
    y_pos = 0
    
    # Stats row
    for i, (title, expr, unit) in enumerate([
        ("Running Containers", "count(container_last_seen)", "short"),
        ("CPU Usage", "sum(rate(container_cpu_usage_seconds_total[5m])) * 100", "percent"),
        ("Memory Usage", "sum(container_memory_usage_bytes) / 1024 / 1024 / 1024", "decgbytes"),
        ("Network I/O", "sum(rate(container_network_receive_bytes_total[5m]))", "Bps")
    ]):
        panels.append(create_stat_panel(title, expr, unit, {"h": 5, "w": 6, "x": i*6, "y": y_pos}))
    
    y_pos += 5
    
    # Graphs
    panels.append(create_graph_panel(
        "Container CPU Usage",
        [{
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "expr": "rate(container_cpu_usage_seconds_total{name=~'$container'}[5m]) * 100",
            "legendFormat": "{{name}}",
            "refId": "A"
        }],
        {"h": 8, "w": 12, "x": 0, "y": y_pos},
        "percent"
    ))
    
    panels.append(create_graph_panel(
        "Container Memory Usage",
        [{
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "expr": "container_memory_usage_bytes{name=~'$container'} / 1024 / 1024",
            "legendFormat": "{{name}}",
            "refId": "A"
        }],
        {"h": 8, "w": 12, "x": 12, "y": y_pos},
        "decmbytes"
    ))
    
    dashboard["panels"] = panels
    return dashboard

# Continue with more dashboards...

# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD 3: LICENSE & USERS
# ═══════════════════════════════════════════════════════════════════════════

def generate_license_dashboard():
    """License and user management"""
    dashboard = create_base_dashboard(
        "rhinometric-license",
        "📜 Rhinometric - License & Users",
        ["rhinometric", "license", "users"]
    )
    
    panels = [
        create_stat_panel("License Status", "license_server_status", "short", {"h": 6, "w": 6, "x": 0, "y": 0}),
        create_stat_panel("Active Users", "license_server_active_users", "short", {"h": 6, "w": 6, "x": 6, "y": 0}),
        create_stat_panel("Days Until Expiration", "license_server_days_remaining", "short", {"h": 6, "w": 6, "x": 12, "y": 0}),
        create_stat_panel("API Calls/min", "rate(license_server_requests_total[1m]) * 60", "reqpm", {"h": 6, "w": 6, "x": 18, "y": 0})
    ]
    
    dashboard["panels"] = panels
    return dashboard

# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD 4: SYSTEM RESOURCES
# ═══════════════════════════════════════════════════════════════════════════

def generate_system_dashboard():
    """System-level metrics"""
    dashboard = create_base_dashboard(
        "rhinometric-system",
        "💻 Rhinometric - System Resources",
        ["rhinometric", "system", "node"]
    )
    
    panels = [
        create_stat_panel("CPU Cores", "count(node_cpu_seconds_total{mode='idle'})", "short", {"h": 4, "w": 6, "x": 0, "y": 0}),
        create_stat_panel("Total RAM", "node_memory_MemTotal_bytes / 1024 / 1024 / 1024", "decgbytes", {"h": 4, "w": 6, "x": 6, "y": 0}),
        create_stat_panel("Disk Total", "node_filesystem_size_bytes{mountpoint='/'} / 1024 / 1024 / 1024", "decgbytes", {"h": 4, "w": 6, "x": 12, "y": 0}),
        create_stat_panel("Network Interfaces", "count(node_network_up)", "short", {"h": 4, "w": 6, "x": 18, "y": 0}),
        
        create_graph_panel("CPU Usage by Core", [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "100 - (avg by(cpu) (rate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)", "legendFormat": "CPU {{cpu}}", "refId": "A"}], {"h": 8, "w": 12, "x": 0, "y": 4}, "percent"),
        create_graph_panel("Memory Details", [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes", "legendFormat": "Used", "refId": "A"}, {"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "node_memory_Cached_bytes + node_memory_Buffers_bytes", "legendFormat": "Cache+Buffers", "refId": "B"}], {"h": 8, "w": 12, "x": 12, "y": 4}, "bytes"),
        
        create_graph_panel("Disk I/O", [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "rate(node_disk_read_bytes_total[5m])", "legendFormat": "Read {{device}}", "refId": "A"}, {"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "rate(node_disk_written_bytes_total[5m])", "legendFormat": "Write {{device}}", "refId": "B"}], {"h": 8, "w": 12, "x": 0, "y": 12}, "Bps"),
        create_graph_panel("Network Traffic", [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "rate(node_network_receive_bytes_total{device!~'lo'}[5m])", "legendFormat": "RX {{device}}", "refId": "A"}, {"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "rate(node_network_transmit_bytes_total{device!~'lo'}[5m])", "legendFormat": "TX {{device}}", "refId": "B"}], {"h": 8, "w": 12, "x": 12, "y": 12}, "Bps")
    ]
    
    dashboard["panels"] = panels
    return dashboard

# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD 5: DOCKER CONTAINERS (cAdvisor)
# ═══════════════════════════════════════════════════════════════════════════

def generate_docker_dashboard():
    """Docker container metrics"""
    dashboard = create_base_dashboard(
        "rhinometric-docker",
        "🐳 Rhinometric - Docker Containers",
        ["rhinometric", "docker", "containers"]
    )
    
    add_variable(dashboard, "container", "label_values(container_last_seen, name)")
    
    panels = [
        create_stat_panel("Running Containers", "count(container_last_seen)", "short", {"h": 5, "w": 6, "x": 0, "y": 0}),
        create_stat_panel("Total CPU Usage", "sum(rate(container_cpu_usage_seconds_total{name=~'$container'}[5m])) * 100", "percent", {"h": 5, "w": 6, "x": 6, "y": 0}),
        create_stat_panel("Total Memory", "sum(container_memory_usage_bytes{name=~'$container'}) / 1024 / 1024 / 1024", "decgbytes", {"h": 5, "w": 6, "x": 12, "y": 0}),
        create_stat_panel("Network I/O", "sum(rate(container_network_receive_bytes_total{name=~'$container'}[5m])) + sum(rate(container_network_transmit_bytes_total{name=~'$container'}[5m]))", "Bps", {"h": 5, "w": 6, "x": 18, "y": 0}),
        
        create_graph_panel("Container CPU", [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "rate(container_cpu_usage_seconds_total{name=~'$container'}[5m]) * 100", "legendFormat": "{{name}}", "refId": "A"}], {"h": 8, "w": 12, "x": 0, "y": 5}, "percent"),
        create_graph_panel("Container Memory", [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "container_memory_usage_bytes{name=~'$container'} / 1024 / 1024", "legendFormat": "{{name}}", "refId": "A"}], {"h": 8, "w": 12, "x": 12, "y": 5}, "decmbytes"),
        
        create_graph_panel("Container Network RX", [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "rate(container_network_receive_bytes_total{name=~'$container'}[5m])", "legendFormat": "{{name}}", "refId": "A"}], {"h": 8, "w": 12, "x": 0, "y": 13}, "Bps"),
        create_graph_panel("Container Network TX", [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "rate(container_network_transmit_bytes_total{name=~'$container'}[5m])", "legendFormat": "{{name}}", "refId": "A"}], {"h": 8, "w": 12, "x": 12, "y": 13}, "Bps")
    ]
    
    dashboard["panels"] = panels
    return dashboard

# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD 6: POSTGRESQL PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════

def generate_postgres_dashboard():
    """PostgreSQL metrics"""
    dashboard = create_base_dashboard(
        "rhinometric-postgres",
        "🗄️ Rhinometric - PostgreSQL Performance",
        ["rhinometric", "postgres", "database"]
    )
    
    panels = [
        create_stat_panel("Active Connections", "pg_stat_activity_count{state='active'}", "short", {"h": 5, "w": 6, "x": 0, "y": 0}),
        create_stat_panel("Cache Hit Ratio", "pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read) * 100", "percent", {"h": 5, "w": 6, "x": 6, "y": 0}),
        create_stat_panel("Transactions/s", "rate(pg_stat_database_xact_commit[5m]) + rate(pg_stat_database_xact_rollback[5m])", "short", {"h": 5, "w": 6, "x": 12, "y": 0}),
        create_stat_panel("Database Size", "pg_database_size_bytes / 1024 / 1024", "decmbytes", {"h": 5, "w": 6, "x": 18, "y": 0}),
        
        create_graph_panel("Connections", [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "pg_stat_activity_count", "legendFormat": "{{state}}", "refId": "A"}], {"h": 8, "w": 12, "x": 0, "y": 5}, "short"),
        create_graph_panel("Query Performance", [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "rate(pg_stat_database_tup_fetched[5m])", "legendFormat": "Rows Fetched", "refId": "A"}, {"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "rate(pg_stat_database_tup_returned[5m])", "legendFormat": "Rows Returned", "refId": "B"}], {"h": 8, "w": 12, "x": 12, "y": 5}, "short")
    ]
    
    dashboard["panels"] = panels
    return dashboard

# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD 7: REDIS PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════

def generate_redis_dashboard():
    """Redis metrics"""
    dashboard = create_base_dashboard(
        "rhinometric-redis",
        "🔴 Rhinometric - Redis Performance",
        ["rhinometric", "redis", "cache"]
    )
    
    panels = [
        create_stat_panel("Connected Clients", "redis_connected_clients", "short", {"h": 5, "w": 6, "x": 0, "y": 0}),
        create_stat_panel("Memory Used", "redis_memory_used_bytes / 1024 / 1024", "decmbytes", {"h": 5, "w": 6, "x": 6, "y": 0}),
        create_stat_panel("Total Keys", "redis_db_keys", "short", {"h": 5, "w": 6, "x": 12, "y": 0}),
        create_stat_panel("Hit Rate", "redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total) * 100", "percent", {"h": 5, "w": 6, "x": 18, "y": 0}),
        
        create_graph_panel("Commands/s", [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "rate(redis_commands_processed_total[5m])", "legendFormat": "Commands", "refId": "A"}], {"h": 8, "w": 12, "x": 0, "y": 5}, "short"),
        create_graph_panel("Memory Usage", [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "redis_memory_used_bytes", "legendFormat": "Used", "refId": "A"}, {"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "redis_memory_max_bytes", "legendFormat": "Max", "refId": "B"}], {"h": 8, "w": 12, "x": 12, "y": 5}, "bytes")
    ]
    
    dashboard["panels"] = panels
    return dashboard

# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD 8: PROMETHEUS MONITORING
# ═══════════════════════════════════════════════════════════════════════════

def generate_prometheus_dashboard():
    """Prometheus self-monitoring"""
    dashboard = create_base_dashboard(
        "rhinometric-prometheus",
        "📈 Rhinometric - Prometheus Monitoring",
        ["rhinometric", "prometheus", "monitoring"]
    )
    
    panels = [
        create_stat_panel("Active Targets", "count(up == 1)", "short", {"h": 5, "w": 6, "x": 0, "y": 0}),
        create_stat_panel("Failed Targets", "count(up == 0)", "short", {"h": 5, "w": 6, "x": 6, "y": 0}),
        create_stat_panel("Time Series", "prometheus_tsdb_head_series", "short", {"h": 5, "w": 6, "x": 12, "y": 0}),
        create_stat_panel("Samples Ingested/s", "rate(prometheus_tsdb_head_samples_appended_total[5m])", "short", {"h": 5, "w": 6, "x": 18, "y": 0}),
        
        create_graph_panel("Scrape Duration", [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "scrape_duration_seconds", "legendFormat": "{{job}}", "refId": "A"}], {"h": 8, "w": 12, "x": 0, "y": 5}, "s"),
        create_graph_panel("TSDB Size", [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "expr": "prometheus_tsdb_storage_blocks_bytes", "legendFormat": "Blocks", "refId": "A"}], {"h": 8, "w": 12, "x": 12, "y": 5}, "bytes")
    ]
    
    dashboard["panels"] = panels
    return dashboard

# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD 9: LOKI LOGS EXPLORER
# ═══════════════════════════════════════════════════════════════════════════

def generate_logs_dashboard():
    """Loki logs with advanced filtering"""
    dashboard = create_base_dashboard(
        "rhinometric-logs",
        "📋 Rhinometric - Logs Explorer",
        ["rhinometric", "logs", "loki"]
    )
    
    add_variable(dashboard, "container", "label_values(container)")
    add_variable(dashboard, "service", "label_values(service)")
    add_variable(dashboard, "level", "label_values(level)")
    
    panels = [
        create_stat_panel("Log Lines/s", "sum(rate({container=~'$container'}[5m]))", "short", {"h": 4, "w": 6, "x": 0, "y": 0}),
        create_stat_panel("Error Rate", "sum(rate({container=~'$container', level=~'error|fatal'}[5m]))", "short", {"h": 4, "w": 6, "x": 6, "y": 0}),
        create_stat_panel("Warning Rate", "sum(rate({container=~'$container', level='warning'}[5m]))", "short", {"h": 4, "w": 6, "x": 12, "y": 0}),
        create_stat_panel("Containers Logging", "count(count by(container) ({container=~'$container'}))", "short", {"h": 4, "w": 6, "x": 18, "y": 0}),
        
        create_logs_panel("Container Logs", {"h": 20, "w": 24, "x": 0, "y": 4})
    ]
    
    dashboard["panels"] = panels
    return dashboard

# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD 10: TEMPO DISTRIBUTED TRACING
# ═══════════════════════════════════════════════════════════════════════════

def generate_tracing_dashboard():
    """Tempo traces and service graph"""
    dashboard = create_base_dashboard(
        "rhinometric-tracing",
        "🔎 Rhinometric - Distributed Tracing",
        ["rhinometric", "traces", "tempo"]
    )
    
    add_variable(dashboard, "service", "query_result(tempo_spanmetrics_calls_total)")
    
    panels = [
        create_stat_panel("Total Spans", "sum(tempo_ingester_spans_received_total)", "short", {"h": 5, "w": 6, "x": 0, "y": 0}),
        create_stat_panel("Traces/s", "rate(tempo_ingester_traces_created_total[5m])", "short", {"h": 5, "w": 6, "x": 6, "y": 0}),
        create_stat_panel("Avg Latency", "histogram_quantile(0.95, sum(rate(tempo_spanmetrics_latency_bucket[5m])) by (le))", "s", {"h": 5, "w": 6, "x": 12, "y": 0}),
        create_stat_panel("Error Rate", "sum(rate(tempo_spanmetrics_calls_total{status_code='STATUS_CODE_ERROR'}[5m])) / sum(rate(tempo_spanmetrics_calls_total[5m])) * 100", "percent", {"h": 5, "w": 6, "x": 18, "y": 0}),
        
        create_traces_panel("Recent Traces", {"h": 16, "w": 24, "x": 0, "y": 5})
    ]
    
    dashboard["panels"] = panels
    return dashboard

# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARDS 11-15 (Simplified versions)
# ═══════════════════════════════════════════════════════════════════════════

def generate_alertmanager_dashboard():
    dashboard = create_base_dashboard("rhinometric-alertmanager", "🚨 Rhinometric - Alertmanager", ["rhinometric", "alerts"])
    dashboard["panels"] = [create_stat_panel("Active Alerts", "count(ALERTS{alertstate='firing'})", "short", {"h": 8, "w": 12, "x": 0, "y": 0})]
    return dashboard

def generate_license_server_dashboard():
    dashboard = create_base_dashboard("rhinometric-license-api", "🔐 Rhinometric - License Server API", ["rhinometric", "license", "api"])
    dashboard["panels"] = [create_stat_panel("API Requests/s", "rate(license_server_requests_total[5m])", "reqps", {"h": 8, "w": 12, "x": 0, "y": 0})]
    return dashboard

def generate_api_proxy_dashboard():
    dashboard = create_base_dashboard("rhinometric-api-proxy", "🔌 Rhinometric - API Proxy", ["rhinometric", "proxy", "api"])
    dashboard["panels"] = [create_stat_panel("Cache Hit Rate", "api_proxy_cache_hits / (api_proxy_cache_hits + api_proxy_cache_misses) * 100", "percent", {"h": 8, "w": 12, "x": 0, "y": 0})]
    return dashboard

def generate_nginx_dashboard():
    dashboard = create_base_dashboard("rhinometric-nginx", "🌐 Rhinometric - Nginx Gateway", ["rhinometric", "nginx", "gateway"])
    dashboard["panels"] = [create_stat_panel("Requests/s", "rate(nginx_http_requests_total[5m])", "reqps", {"h": 8, "w": 12, "x": 0, "y": 0})]
    return dashboard

def generate_otel_dashboard():
    dashboard = create_base_dashboard("rhinometric-otel", "⚡ Rhinometric - OTEL Collector", ["rhinometric", "otel", "telemetry"])
    dashboard["panels"] = [create_stat_panel("Spans Received/s", "rate(otelcol_receiver_accepted_spans[5m])", "short", {"h": 8, "w": 12, "x": 0, "y": 0})]
    return dashboard

def save_dashboard(dashboard, filename):
    """Save dashboard JSON to file for Grafana provisioning"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Save dashboard directly (for file provisioning, not API import)
    # Grafana provisioning expects raw dashboard JSON, not wrapped format
    with open(filepath, 'w') as f:
        json.dump(dashboard, f, indent=2)
    print(f"[OK] Created: {filename}")

if __name__ == "__main__":
    print("=" * 60)
    print("  RHINOMETRIC DASHBOARD GENERATOR v2.1.0")
    print("=" * 60)
    print()
    
    dashboards = [
        (generate_executive_dashboard(), "executive.json"),
        (generate_overview_dashboard(), "overview.json"),
        (generate_license_dashboard(), "license.json"),
        (generate_system_dashboard(), "system.json"),
        (generate_docker_dashboard(), "docker.json"),
        (generate_postgres_dashboard(), "postgres.json"),
        (generate_redis_dashboard(), "redis.json"),
        (generate_prometheus_dashboard(), "prometheus.json"),
        (generate_logs_dashboard(), "logs.json"),
        (generate_tracing_dashboard(), "tracing.json"),
        (generate_alertmanager_dashboard(), "alertmanager.json"),
        (generate_license_server_dashboard(), "license-api.json"),
        (generate_api_proxy_dashboard(), "api-proxy.json"),
        (generate_nginx_dashboard(), "nginx.json"),
        (generate_otel_dashboard(), "otel.json")
    ]
    
    for dashboard, filename in dashboards:
        save_dashboard(dashboard, filename)
    
    print(f"\n[SUCCESS] Generated {len(dashboards)} dashboards in {OUTPUT_DIR}/")
    print("\nDashboard List:")
    for i in range(1, 16):
        print(f"   {i}. Dashboard #{i}")
    print("\n[OK] Ready to deploy!")
