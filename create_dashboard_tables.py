#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create Grafana dashboard for rhinometric-postgres-tables collector
"""
import requests
import json

# Grafana API
GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "demo123"

# Dashboard configuration
DASHBOARD_UID = "database-rhinometric-postgres-tables"
DASHBOARD_TITLE = "DATABASE - rhinometric-postgres-tables"

dashboard = {
    "dashboard": {
        "uid": DASHBOARD_UID,
        "title": DASHBOARD_TITLE,
        "timezone": "browser",
        "schemaVersion": 16,
        "version": 0,
        "refresh": "5s",
        "tags": ["database", "postgresql", "tables"],
        "panels": [
            # Panel 1: Connection Status
            {
                "id": 1,
                "gridPos": {"h": 4, "w": 4, "x": 0, "y": 0},
                "type": "stat",
                "title": "Database Connection",
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "targets": [{
                    "expr": "db_connection_status{container_name=~\".*postgres-tables.*\"}",
                    "refId": "A"
                }],
                "options": {
                    "colorMode": "background",
                    "graphMode": "none",
                    "justifyMode": "center",
                    "textMode": "value_and_name",
                    "reduceOptions": {
                        "values": False,
                        "calcs": ["lastNotNull"]
                    }
                },
                "fieldConfig": {
                    "defaults": {
                        "mappings": [
                            {"type": "value", "value": "0", "text": "Disconnected"},
                            {"type": "value", "value": "1", "text": "Connected"}
                        ],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"value": 0, "color": "red"},
                                {"value": 1, "color": "green"}
                            ]
                        }
                    }
                }
            },
            
            # Panel 2: Total Queries
            {
                "id": 2,
                "gridPos": {"h": 4, "w": 4, "x": 4, "y": 0},
                "type": "stat",
                "title": "Total Queries",
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "targets": [{
                    "expr": "db_queries_total{container_name=~\".*postgres-tables.*\", status=\"success\"}",
                    "refId": "A"
                }],
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "textMode": "auto",
                    "reduceOptions": {
                        "values": False,
                        "calcs": ["lastNotNull"]
                    }
                },
                "fieldConfig": {
                    "defaults": {
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"value": 0, "color": "blue"}
                            ]
                        }
                    }
                }
            },
            
            # Panel 3: Success Rate
            {
                "id": 3,
                "gridPos": {"h": 4, "w": 4, "x": 8, "y": 0},
                "type": "stat",
                "title": "Success Rate",
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "targets": [{
                    "expr": "(sum(db_queries_total{container_name=~\".*postgres-tables.*\", status=\"success\"}) / sum(db_queries_total{container_name=~\".*postgres-tables.*\"})) * 100",
                    "refId": "A"
                }],
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "textMode": "auto",
                    "reduceOptions": {
                        "values": False,
                        "calcs": ["lastNotNull"]
                    }
                },
                "fieldConfig": {
                    "defaults": {
                        "unit": "percent",
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"value": 0, "color": "red"},
                                {"value": 80, "color": "yellow"},
                                {"value": 95, "color": "green"}
                            ]
                        }
                    }
                }
            },
            
            # Panel 4: Query Rate
            {
                "id": 4,
                "gridPos": {"h": 4, "w": 4, "x": 12, "y": 0},
                "type": "stat",
                "title": "Query Rate (queries/min)",
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "targets": [{
                    "expr": "rate(db_queries_total{container_name=~\".*postgres-tables.*\", status=\"success\"}[5m]) * 60",
                    "refId": "A"
                }],
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "textMode": "auto",
                    "reduceOptions": {
                        "values": False,
                        "calcs": ["lastNotNull"]
                    }
                },
                "fieldConfig": {
                    "defaults": {
                        "unit": "short",
                        "decimals": 2,
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"value": 0, "color": "blue"}
                            ]
                        }
                    }
                }
            },
            
            # Panel 5: Query Duration
            {
                "id": 5,
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4},
                "type": "timeseries",
                "title": "Query Duration",
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "targets": [{
                    "expr": "rate(db_query_duration_seconds_sum{container_name=~\".*postgres-tables.*\"}[1m]) / rate(db_query_duration_seconds_count{container_name=~\".*postgres-tables.*\"}[1m])",
                    "legendFormat": "Avg Duration",
                    "refId": "A"
                }],
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "drawStyle": "line",
                            "lineInterpolation": "smooth",
                            "fillOpacity": 10
                        },
                        "unit": "s",
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"value": 0, "color": "green"},
                                {"value": 1, "color": "yellow"},
                                {"value": 5, "color": "red"}
                            ]
                        }
                    }
                }
            },
            
            # Panel 6: Connection Pool
            {
                "id": 6,
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4},
                "type": "timeseries",
                "title": "Connection Pool Status",
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "targets": [
                    {
                        "expr": "db_connections_active{container_name=~\".*postgres-tables.*\"}",
                        "legendFormat": "Active",
                        "refId": "A"
                    },
                    {
                        "expr": "db_connections_idle{container_name=~\".*postgres-tables.*\"}",
                        "legendFormat": "Idle",
                        "refId": "B"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "drawStyle": "line",
                            "lineInterpolation": "smooth",
                            "fillOpacity": 10
                        },
                        "unit": "short",
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"value": 0, "color": "green"}
                            ]
                        }
                    }
                }
            }
        ]
    },
    "overwrite": True
}

# Delete old dashboard if exists
try:
    delete_url = f"{GRAFANA_URL}/api/dashboards/uid/{DASHBOARD_UID}"
    requests.delete(delete_url, auth=(GRAFANA_USER, GRAFANA_PASSWORD))
    print(f"Old dashboard deleted")
except Exception as e:
    print(f"No previous dashboard to delete")

# Create new dashboard
try:
    create_url = f"{GRAFANA_URL}/api/dashboards/db"
    response = requests.post(
        create_url,
        json=dashboard,
        auth=(GRAFANA_USER, GRAFANA_PASSWORD),
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        dashboard_url = f"{GRAFANA_URL}{result['url']}"
        print(f"Dashboard created with 6 panels: {dashboard_url}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Error creating dashboard: {e}")
