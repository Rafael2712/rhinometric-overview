#!/usr/bin/env python3
"""
Dashboard Generator for RHINOMETRIC v2.2.0
Generates Grafana dashboard JSON files with proper structure
"""

import json
from datetime import datetime

def generate_executive_dashboard():
    """Executive Overview Dashboard - For management and decision makers"""
    return {
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": "-- Grafana --",
                    "enable": true,
                    "hide": true,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }
            ]
        },
        "editable": true,
        "gnetId": null,
        "graphTooltip": 0,
        "id": null,
        "links": [],
        "panels": [
            {
                "datasource": "Prometheus",
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": null},
                                {"color": "red", "value": 80}
                            ]
                        },
                        "unit": "none"
                    }
                },
                "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                "id": 1,
                "options": {
                    "orientation": "auto",
                    "reduceOptions": {
                        "values": false,
                        "calcs": ["lastNotNull"],
                        "fields": ""
                    },
                    "showThresholdLabels": false,
                    "showThresholdMarkers": true,
                    "text": {}
                },
                "pluginVersion": "10.4.0",
                "targets": [
                    {
                        "expr": "count(up == 1)",
                        "refId": "A"
                    }
                ],
                "title": "Services UP",
                "type": "gauge"
            },
            {
                "datasource": "Prometheus",
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisCenteredZero": false,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {"tooltip": false, "viz": false, "legend": false},
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": false,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": null}
                            ]
                        },
                        "unit": "percent"
                    }
                },
                "gridPos": {"h": 8, "w": 9, "x": 6, "y": 0},
                "id": 2,
                "options": {
                    "legend": {"calcs": [], "displayMode": "list", "placement": "bottom"},
                    "tooltip": {"mode": "single"}
                },
                "pluginVersion": "10.4.0",
                "targets": [
                    {
                        "expr": "100 - (avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
                        "legendFormat": "CPU Usage",
                        "refId": "A"
                    },
                    {
                        "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
                        "legendFormat": "Memory Usage",
                        "refId": "B"
                    }
                ],
                "title": "Server Resources",
                "type": "timeseries"
            },
            {
                "datasource": "Prometheus",
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [
                            {"options": {"match": "null", "result": {"text": "0"}}, "type": "special"}
                        ],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": null},
                                {"color": "yellow", "value": 1},
                                {"color": "red", "value": 5}
                            ]
                        },
                        "unit": "none"
                    }
                },
                "gridPos": {"h": 8, "w": 6, "x": 15, "y": 0},
                "id": 3,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {
                        "values": false,
                        "calcs": ["lastNotNull"],
                        "fields": ""
                    },
                    "textMode": "auto"
                },
                "pluginVersion": "10.4.0",
                "targets": [
                    {
                        "expr": "ALERTS{alertstate=\"firing\",severity=\"critical\"}",
                        "refId": "A"
                    }
                ],
                "title": "Critical Alerts (24h)",
                "type": "stat"
            },
            {
                "datasource": "Prometheus",
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "hideFrom": {"tooltip": false, "viz": false, "legend": false}
                        },
                        "mappings": []
                    }
                },
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "id": 4,
                "options": {
                    "legend": {"displayMode": "table", "placement": "right", "values": ["value"]},
                    "pieType": "donut",
                    "tooltip": {"mode": "single"}
                },
                "pluginVersion": "10.4.0",
                "targets": [
                    {
                        "expr": "count by (job) (up == 1)",
                        "legendFormat": "{{job}}",
                        "refId": "A"
                    }
                ],
                "title": "Service Distribution",
                "type": "piechart"
            },
            {
                "datasource": "Prometheus",
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "custom": {"align": "auto", "displayMode": "auto"},
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": null}
                            ]
                        }
                    }
                },
                "gridPos": {"h": 8, "w": 9, "x": 12, "y": 8},
                "id": 5,
                "options": {
                    "footer": {"fields": "", "reducer": ["sum"], "show": false},
                    "showHeader": true
                },
                "pluginVersion": "10.4.0",
                "targets": [
                    {
                        "expr": "up",
                        "format": "table",
                        "instant": true,
                        "refId": "A"
                    }
                ],
                "title": "Service Status",
                "transformations": [
                    {
                        "id": "organize",
                        "options": {
                            "excludeByName": {"Time": true},
                            "indexByName": {},
                            "renameByName": {"Value": "Status", "instance": "Instance", "job": "Service"}
                        }
                    }
                ],
                "type": "table"
            },
            {
                "datasource": "Prometheus",
                "gridPos": {"h": 4, "w": 21, "x": 0, "y": 16},
                "id": 6,
                "options": {
                    "code": {
                        "language": "plaintext",
                        "showLineNumbers": false,
                        "showMiniMap": false
                    },
                    "content": "## 🏢 On-Premise Deployment\n\n✅ **Compliance**: GDPR/ENS compliant - all data stored locally  \n✅ **Security**: No external dependencies - complete data sovereignty  \n✅ **Control**: Full infrastructure control and customization",
                    "mode": "markdown"
                },
                "pluginVersion": "10.4.0",
                "title": "Compliance Information",
                "type": "text"
            }
        ],
        "refresh": "30s",
        "schemaVersion": 38,
        "style": "dark",
        "tags": ["rhinometric", "executive", "overview"],
        "templating": {"list": []},
        "time": {"from": "now-6h", "to": "now"},
        "timepicker": {},
        "timezone": "",
        "title": "01 - Executive Overview",
        "uid": "rhinometric-executive",
        "version": 0,
        "weekStart": ""
    }

# Generate the dashboard
if __name__ == "__main__":
    dashboard = generate_executive_dashboard()
    with open("01-executive-overview.json", "w") as f:
        json.dump(dashboard, f, indent=2)
    print("✅ Generated: 01-executive-overview.json")
