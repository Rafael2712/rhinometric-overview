"""
RHINOMETRIC v2.5.0 - Dashboard Generator Service
=================================================

Auto-generates Grafana dashboards from templates.
Based on working MQTT dashboard structure.
"""

import json
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """
    Generates Grafana dashboards for different collector types.
    Returns dashboard object directly (not wrapped in API format).
    """
    
    def __init__(self, templates_dir: str = None):
        """
        Initialize dashboard generator.
        
        Args:
            templates_dir: Deprecated, kept for compatibility. Dashboards are code-based now.
        """
        # Ignore templates_dir - dashboards are embedded in code based on working MQTT dashboard
        pass
    
    def generate_dashboard(
        self,
        connector_type: str,
        datasource_name: str,
        datasource_uid: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate Grafana dashboard JSON.
        
        Args:
            connector_type: "rest", "mqtt", "database", "webhook"
            datasource_name: Name of the connector
            datasource_uid: UID for the dashboard (e.g. "rest-api-name")
            config: Additional configuration
        
        Returns:
            Grafana dashboard JSON object (direct, not wrapped)
        """
        if connector_type == "rest":
            return self._generate_rest_dashboard(datasource_name, datasource_uid, config)
        elif connector_type == "mqtt":
            return self._generate_mqtt_dashboard(datasource_name, datasource_uid, config)
        elif connector_type == "database":
            return self._generate_database_dashboard(datasource_name, datasource_uid, config)
        elif connector_type == "webhook":
            return self._generate_webhook_dashboard(datasource_name, datasource_uid, config)
        else:
            raise ValueError(f"Unsupported connector type: {connector_type}")
    
    def _generate_rest_dashboard(
        self,
        name: str,
        uid: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate REST API monitoring dashboard.
        Based on working MQTT dashboard structure.
        """
        return {
            "annotations": {
                "list": []
            },
            "editable": True,
            "fiscalYearStartMonth": 0,
            "graphTooltip": 0,
            "id": None,
            "links": [],
            "liveNow": False,
            "panels": [
                {
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "red", "value": None},
                                    {"color": "yellow", "value": 90},
                                    {"color": "green", "value": 95}
                                ]
                            },
                            "unit": "percent"
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    "id": 1,
                    "options": {
                        "orientation": "auto",
                        "reduceOptions": {
                            "values": False,
                            "calcs": ["lastNotNull"],
                            "fields": ""
                        },
                        "showThresholdLabels": False,
                        "showThresholdMarkers": True
                    },
                    "pluginVersion": "9.5.0",
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": "sum(rate(api_requests_total{status=~\"2..\"}[5m])) / sum(rate(api_requests_total[5m])) * 100",
                            "refId": "A"
                        }
                    ],
                    "title": "API Success Rate",
                    "type": "gauge"
                },
                {
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
                                "showPoints": "auto",
                                "spanNulls": False,
                                "stacking": {"group": "A", "mode": "none"},
                                "thresholdsStyle": {"mode": "off"}
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [{"color": "green", "value": None}]
                            },
                            "unit": "reqps"
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    "id": 2,
                    "options": {
                        "legend": {"calcs": [], "displayMode": "list", "placement": "bottom"},
                        "tooltip": {"mode": "single", "sort": "none"}
                    },
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": "rate(api_requests_total[1m])",
                            "legendFormat": "{{status}}",
                            "refId": "A"
                        }
                    ],
                    "title": "Request Rate by Status",
                    "type": "timeseries"
                },
                {
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
                                "lineInterpolation": "smooth",
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {"type": "linear"},
                                "showPoints": "auto",
                                "spanNulls": False,
                                "stacking": {"group": "A", "mode": "none"},
                                "thresholdsStyle": {"mode": "off"}
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [{"color": "green", "value": None}]
                            },
                            "unit": "ms"
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    "id": 3,
                    "options": {
                        "legend": {"calcs": [], "displayMode": "list", "placement": "bottom"},
                        "tooltip": {"mode": "single", "sort": "none"}
                    },
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": "rate(api_response_time_seconds_sum[5m]) / rate(api_response_time_seconds_count[5m]) * 1000",
                            "legendFormat": "Response Time",
                            "refId": "A"
                        }
                    ],
                    "title": "Average Response Time",
                    "type": "timeseries"
                },
                {
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [{"color": "green", "value": None}]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    "id": 4,
                    "options": {
                        "colorMode": "value",
                        "graphMode": "area",
                        "justifyMode": "auto",
                        "orientation": "auto",
                        "reduceOptions": {
                            "values": False,
                            "calcs": ["lastNotNull"],
                            "fields": ""
                        },
                        "textMode": "auto"
                    },
                    "pluginVersion": "9.5.0",
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": "sum(api_requests_total)",
                            "refId": "A"
                        }
                    ],
                    "title": "Total Requests",
                    "type": "stat"
                }
            ],
            "refresh": "10s",
            "schemaVersion": 38,
            "style": "dark",
            "tags": ["rest", "api", "auto-generated"],
            "templating": {"list": []},
            "time": {"from": "now-1h", "to": "now"},
            "timepicker": {},
            "timezone": "",
            "title": f"RHINOMETRIC - {name} API Monitoring",
            "uid": uid,
            "version": 0,
            "weekStart": ""
        }
    
    def _generate_mqtt_dashboard(
        self,
        name: str,
        uid: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate MQTT IoT monitoring dashboard with 10 complete panels."""  
        panels = [
            # Panel 1: MQTT Broker Connection Status (timeseries)
            {
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisCenteredZero": False, "axisColorMode": "text", "axisLabel": "",
                            "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "line",
                            "fillOpacity": 0, "gradientMode": "none",
                            "hideFrom": {"tooltip": False, "viz": False, "legend": False},
                            "lineInterpolation": "linear", "lineWidth": 1, "pointSize": 5,
                            "scaleDistribution": {"type": "linear"}, "showPoints": "auto",
                            "spanNulls": False, "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "red", "value": 80}]}
                    }
                },
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "id": 1,
                "options": {
                    "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "single", "sort": "none"}
                },
                "targets": [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "editorMode": "code", "expr": "mqtt_connection_status", "legendFormat": "{{broker}}:{{port}}", "range": True, "refId": "A"}],
                "title": "MQTT Broker Connection Status",
                "type": "timeseries"
            },
            # Panel 2: MQTT Messages Rate (gauge)
            {
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"color": {"mode": "thresholds"}, "mappings": [], "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]}, "unit": "short"}},
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                "id": 2,
                "options": {"orientation": "auto", "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""}, "showThresholdLabels": False, "showThresholdMarkers": True},
                "pluginVersion": "10.2.0",
                "targets": [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "editorMode": "code", "expr": "sum(rate(mqtt_messages_received_total[5m]))", "legendFormat": "__auto", "range": True, "refId": "A"}],
                "title": "MQTT Messages Rate (msg/s)",
                "type": "gauge"
            },
            # Panel 3: IoT Temperature Sensors
            {
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"axisCenteredZero": False, "axisColorMode": "text", "axisLabel": "", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "line", "fillOpacity": 10, "gradientMode": "none", "hideFrom": {"tooltip": False, "viz": False, "legend": False}, "lineInterpolation": "linear", "lineWidth": 1, "pointSize": 5, "scaleDistribution": {"type": "linear"}, "showPoints": "auto", "spanNulls": False, "stacking": {"group": "A", "mode": "none"}, "thresholdsStyle": {"mode": "off"}},
                        "mappings": [], "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]}, "unit": "celsius"
                    }
                },
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "id": 3,
                "options": {"legend": {"calcs": ["last", "max", "min"], "displayMode": "table", "placement": "bottom", "showLegend": True}, "tooltip": {"mode": "multi", "sort": "none"}},
                "targets": [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "editorMode": "code", "expr": "iot_sensor_temperature_celsius", "legendFormat": "{{sensor_id}} ({{location}})", "range": True, "refId": "A"}],
                "title": "IoT Temperature Sensors",
                "type": "timeseries"
            },
            # Panel 4: IoT Humidity Sensors
            {
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"axisCenteredZero": False, "axisColorMode": "text", "axisLabel": "", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "line", "fillOpacity": 10, "gradientMode": "none", "hideFrom": {"tooltip": False, "viz": False, "legend": False}, "lineInterpolation": "linear", "lineWidth": 1, "pointSize": 5, "scaleDistribution": {"type": "linear"}, "showPoints": "auto", "spanNulls": False, "stacking": {"group": "A", "mode": "none"}, "thresholdsStyle": {"mode": "off"}},
                        "mappings": [], "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]}, "unit": "percent"
                    }
                },
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                "id": 4,
                "options": {"legend": {"calcs": ["last", "max", "min"], "displayMode": "table", "placement": "bottom", "showLegend": True}, "tooltip": {"mode": "multi", "sort": "none"}},
                "targets": [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "editorMode": "code", "expr": "iot_sensor_humidity_percent", "legendFormat": "{{sensor_id}} ({{location}})", "range": True, "refId": "A"}],
                "title": "IoT Humidity Sensors",
                "type": "timeseries"
            },
            # Panel 5: Top 10 MQTT Topics by Message Count
            {
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"axisCenteredZero": False, "axisColorMode": "text", "axisLabel": "", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "bars", "fillOpacity": 100, "gradientMode": "none", "hideFrom": {"tooltip": False, "viz": False, "legend": False}, "lineInterpolation": "linear", "lineWidth": 1, "pointSize": 5, "scaleDistribution": {"type": "linear"}, "showPoints": "auto", "spanNulls": False, "stacking": {"group": "A", "mode": "none"}, "thresholdsStyle": {"mode": "off"}},
                        "mappings": [], "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]}
                    }
                },
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                "id": 5,
                "options": {"legend": {"calcs": ["sum"], "displayMode": "table", "placement": "bottom", "showLegend": True}, "tooltip": {"mode": "multi", "sort": "desc"}},
                "targets": [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "editorMode": "code", "expr": "topk(10, mqtt_messages_received_total)", "legendFormat": "{{topic}}", "range": True, "refId": "A"}],
                "title": "Top 10 MQTT Topics by Message Count",
                "type": "timeseries"
            },
            # Panel 6: IoT Devices by Type (piechart)
            {
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"color": {"mode": "palette-classic"}, "custom": {"hideFrom": {"tooltip": False, "viz": False, "legend": False}}, "mappings": []}},
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                "id": 6,
                "options": {"legend": {"displayMode": "table", "placement": "right", "showLegend": True, "values": ["value"]}, "pieType": "pie", "tooltip": {"mode": "single", "sort": "none"}},
                "targets": [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "editorMode": "code", "expr": "sum by (device_type) (iot_device_status)", "legendFormat": "{{device_type}}", "range": True, "refId": "A"}],
                "title": "IoT Devices by Type",
                "type": "piechart"
            },
            # Panel 7: Total MQTT Topics (stat)
            {
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"color": {"mode": "thresholds"}, "mappings": [], "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]}}},
                "gridPos": {"h": 4, "w": 6, "x": 0, "y": 24},
                "id": 7,
                "options": {"colorMode": "value", "graphMode": "area", "justifyMode": "auto", "orientation": "auto", "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""}, "textMode": "auto"},
                "pluginVersion": "10.2.0",
                "targets": [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "editorMode": "code", "expr": "count(count by (topic) (mqtt_messages_received_total))", "legendFormat": "__auto", "range": True, "refId": "A"}],
                "title": "Total MQTT Topics",
                "type": "stat"
            },
            # Panel 8: Total Messages Received (stat)
            {
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"color": {"mode": "thresholds"}, "mappings": [], "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]}}},
                "gridPos": {"h": 4, "w": 6, "x": 6, "y": 24},
                "id": 8,
                "options": {"colorMode": "value", "graphMode": "area", "justifyMode": "auto", "orientation": "auto", "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""}, "textMode": "auto"},
                "pluginVersion": "10.2.0",
                "targets": [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "editorMode": "code", "expr": "sum(mqtt_messages_received_total)", "legendFormat": "__auto", "range": True, "refId": "A"}],
                "title": "Total Messages Received",
                "type": "stat"
            },
            # Panel 9: Total Bytes Received (stat)
            {
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"color": {"mode": "thresholds"}, "mappings": [], "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]}, "unit": "bytes"}},
                "gridPos": {"h": 4, "w": 6, "x": 12, "y": 24},
                "id": 9,
                "options": {"colorMode": "value", "graphMode": "area", "justifyMode": "auto", "orientation": "auto", "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""}, "textMode": "auto"},
                "pluginVersion": "10.2.0",
                "targets": [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "editorMode": "code", "expr": "sum(mqtt_messages_bytes_total)", "legendFormat": "__auto", "range": True, "refId": "A"}],
                "title": "Total Bytes Received",
                "type": "stat"
            },
            # Panel 10: Broker Status (stat with mapping)
            {
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"color": {"mode": "thresholds"}, "mappings": [{"options": {"0": {"color": "red", "index": 1, "text": "Offline"}, "1": {"color": "green", "index": 0, "text": "Online"}}, "type": "value"}], "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]}}},
                "gridPos": {"h": 4, "w": 6, "x": 18, "y": 24},
                "id": 10,
                "options": {"colorMode": "background", "graphMode": "none", "justifyMode": "auto", "orientation": "auto", "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""}, "textMode": "auto"},
                "pluginVersion": "10.2.0",
                "targets": [{"datasource": {"type": "prometheus", "uid": "prometheus"}, "editorMode": "code", "expr": "mqtt_connection_status", "legendFormat": "__auto", "range": True, "refId": "A"}],
                "title": "Broker Status",
                "type": "stat"
            }
        ]
        
        return {
            "annotations": {"list": []},
            "editable": True,
            "fiscalYearStartMonth": 0,
            "graphTooltip": 0,
            "id": None,
            "links": [],
            "liveNow": False,
            "panels": panels,
            "refresh": "5s",
            "schemaVersion": 38,
            "style": "dark",
            "tags": ["mqtt", "iot", "rhinometric"],
            "templating": {"list": []},
            "time": {"from": "now-15m", "to": "now"},
            "timepicker": {},
            "timezone": "",
            "title": f"RHINOMETRIC - {name} MQTT Monitoring",
            "uid": uid,
            "version": 0,
            "weekStart": ""
        }

    def _generate_database_dashboard(
        self,
        name: str,
        uid: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate Database monitoring dashboard."""
        return {
            "annotations": {"list": []},
            "editable": True,
            "fiscalYearStartMonth": 0,
            "graphTooltip": 0,
            "id": None,
            "links": [],
            "liveNow": False,
            "panels": [
                # Panel 1: Connection Status
                {
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "mappings": [
                                {"type": "value", "value": "0", "text": "Disconnected"},
                                {"type": "value", "value": "1", "text": "Connected"}
                            ],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "red", "value": None},
                                    {"color": "green", "value": 1}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 6, "w": 8, "x": 0, "y": 0},
                    "id": 1,
                    "options": {
                        "colorMode": "background",
                        "graphMode": "none",
                        "justifyMode": "center",
                        "orientation": "auto",
                        "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""},
                        "textMode": "value_and_name"
                    },
                    "pluginVersion": "9.5.0",
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": f"db_connection_status{{job=\"database-{name}\"}}",
                            "refId": "A"
                        }
                    ],
                    "title": "Database Connection",
                    "type": "stat"
                },
                # Panel 2: Total Queries
                {
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [{"color": "blue", "value": None}]
                            },
                            "unit": "short"
                        }
                    },
                    "gridPos": {"h": 6, "w": 8, "x": 8, "y": 0},
                    "id": 2,
                    "options": {
                        "colorMode": "value",
                        "graphMode": "area",
                        "justifyMode": "auto",
                        "orientation": "auto",
                        "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""},
                        "textMode": "auto"
                    },
                    "pluginVersion": "9.5.0",
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": f"sum(db_queries_total{{job=\"database-{name}\"}})",
                            "refId": "A"
                        }
                    ],
                    "title": "Total Queries Executed",
                    "type": "stat"
                },
                # Panel 3: Success Rate
                {
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "red", "value": None},
                                    {"color": "yellow", "value": 90},
                                    {"color": "green", "value": 95}
                                ]
                            },
                            "unit": "percent"
                        }
                    },
                    "gridPos": {"h": 6, "w": 8, "x": 16, "y": 0},
                    "id": 3,
                    "options": {
                        "colorMode": "value",
                        "graphMode": "area",
                        "justifyMode": "auto",
                        "orientation": "auto",
                        "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""},
                        "textMode": "auto"
                    },
                    "pluginVersion": "9.5.0",
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": f"sum(db_queries_total{{job=\"database-{name}\",status=\"success\"}}) / sum(db_queries_total{{job=\"database-{name}\"}}) * 100",
                            "refId": "A"
                        }
                    ],
                    "title": "Query Success Rate",
                    "type": "stat"
                },
                # Panel 4: Query Rate
                {
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "custom": {
                                "axisCenteredZero": False,
                                "axisColorMode": "text",
                                "axisLabel": "Queries/second",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 20,
                                "gradientMode": "none",
                                "hideFrom": {"tooltip": False, "viz": False, "legend": False},
                                "lineInterpolation": "smooth",
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {"type": "linear"},
                                "showPoints": "auto",
                                "spanNulls": False,
                                "stacking": {"group": "A", "mode": "none"},
                                "thresholdsStyle": {"mode": "off"}
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [{"color": "green", "value": None}]
                            },
                            "unit": "reqps"
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 6},
                    "id": 4,
                    "options": {
                        "legend": {"calcs": ["mean", "max"], "displayMode": "table", "placement": "bottom"},
                        "tooltip": {"mode": "multi", "sort": "desc"}
                    },
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": f"rate(db_queries_total{{job=\"database-{name}\",status=\"success\"}}[1m])",
                            "legendFormat": "Success",
                            "refId": "A"
                        },
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": f"rate(db_queries_total{{job=\"database-{name}\",status=\"error\"}}[1m])",
                            "legendFormat": "Error",
                            "refId": "B"
                        }
                    ],
                    "title": "Query Rate (Success vs Error)",
                    "type": "timeseries"
                },
                # Panel 5: Query Duration
                {
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "custom": {
                                "axisCenteredZero": False,
                                "axisColorMode": "text",
                                "axisLabel": "Duration (ms)",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 10,
                                "gradientMode": "none",
                                "hideFrom": {"tooltip": False, "viz": False, "legend": False},
                                "lineInterpolation": "smooth",
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {"type": "linear"},
                                "showPoints": "auto",
                                "spanNulls": False,
                                "stacking": {"group": "A", "mode": "none"},
                                "thresholdsStyle": {"mode": "off"}
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [{"color": "green", "value": None}]
                            },
                            "unit": "ms"
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 6},
                    "id": 5,
                    "options": {
                        "legend": {"calcs": ["mean", "max"], "displayMode": "table", "placement": "bottom"},
                        "tooltip": {"mode": "multi", "sort": "none"}
                    },
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": f"rate(db_query_duration_seconds_sum{{job=\"database-{name}\"}}[5m]) / rate(db_query_duration_seconds_count{{job=\"database-{name}\"}}[5m]) * 1000",
                            "legendFormat": "Avg Duration",
                            "refId": "A"
                        }
                    ],
                    "title": "Average Query Duration",
                    "type": "timeseries"
                },
                # Panel 6: Connection Pool Status
                {
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "custom": {
                                "axisCenteredZero": False,
                                "axisColorMode": "text",
                                "axisLabel": "Connections",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 30,
                                "gradientMode": "none",
                                "hideFrom": {"tooltip": False, "viz": False, "legend": False},
                                "lineInterpolation": "linear",
                                "lineWidth": 1,
                                "pointSize": 5,
                                "scaleDistribution": {"type": "linear"},
                                "showPoints": "auto",
                                "spanNulls": False,
                                "stacking": {"group": "A", "mode": "normal"},
                                "thresholdsStyle": {"mode": "off"}
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [{"color": "green", "value": None}]
                            },
                            "unit": "short"
                        }
                    },
                    "gridPos": {"h": 8, "w": 24, "x": 0, "y": 14},
                    "id": 6,
                    "options": {
                        "legend": {"calcs": ["mean", "max"], "displayMode": "table", "placement": "right"},
                        "tooltip": {"mode": "multi", "sort": "none"}
                    },
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": f"db_connections_active{{job=\"database-{name}\"}}",
                            "legendFormat": "Active Connections",
                            "refId": "A"
                        },
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": f"db_connections_idle{{job=\"database-{name}\"}}",
                            "legendFormat": "Idle Connections",
                            "refId": "B"
                        }
                    ],
                    "title": "Connection Pool Status (Active vs Idle)",
                    "type": "timeseries"
                }
            ],
            "refresh": "30s",
            "schemaVersion": 38,
            "style": "dark",
            "tags": ["database", "sql", "auto-generated"],
            "templating": {"list": []},
            "time": {"from": "now-6h", "to": "now"},
            "timepicker": {},
            "timezone": "",
            "title": f"RHINOMETRIC - {name} Database Monitoring",
            "uid": uid,
            "version": 0,
            "weekStart": ""
        }
    
    def _generate_webhook_dashboard(
        self,
        name: str,
        uid: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate Webhook monitoring dashboard with 6 panels."""
        return {
            "annotations": {"list": []},
            "editable": True,
            "fiscalYearStartMonth": 0,
            "graphTooltip": 0,
            "id": None,
            "links": [],
            "liveNow": False,
            "panels": [
                # Panel 1: Total Events Received
                {
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [{"color": "green", "value": None}]
                            }
                        }
                    },
                    "gridPos": {"h": 6, "w": 8, "x": 0, "y": 0},
                    "id": 1,
                    "options": {
                        "colorMode": "value",
                        "graphMode": "area",
                        "justifyMode": "auto",
                        "orientation": "auto",
                        "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""},
                        "textMode": "auto"
                    },
                    "pluginVersion": "9.5.0",
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": "sum(webhook_events_received_total)",
                            "refId": "A"
                        }
                    ],
                    "title": "Total Events Received",
                    "type": "stat"
                },
                # Panel 2: Success Rate
                {
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "red", "value": None},
                                    {"color": "yellow", "value": 90},
                                    {"color": "green", "value": 95}
                                ]
                            },
                            "unit": "percent"
                        }
                    },
                    "gridPos": {"h": 6, "w": 8, "x": 8, "y": 0},
                    "id": 2,
                    "options": {
                        "orientation": "auto",
                        "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""},
                        "showThresholdLabels": False,
                        "showThresholdMarkers": True
                    },
                    "pluginVersion": "9.5.0",
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": "sum(rate(webhook_events_received_total{status=\"success\"}[5m])) / sum(rate(webhook_events_received_total[5m])) * 100",
                            "refId": "A"
                        }
                    ],
                    "title": "Success Rate",
                    "type": "gauge"
                },
                # Panel 3: Last Event Timestamp
                {
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [{"color": "green", "value": None}]
                            },
                            "unit": "dateTimeAsIso"
                        }
                    },
                    "gridPos": {"h": 6, "w": 8, "x": 16, "y": 0},
                    "id": 3,
                    "options": {
                        "colorMode": "value",
                        "graphMode": "none",
                        "justifyMode": "auto",
                        "orientation": "auto",
                        "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""},
                        "textMode": "auto"
                    },
                    "pluginVersion": "9.5.0",
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": "max(webhook_last_event_timestamp) * 1000",
                            "refId": "A"
                        }
                    ],
                    "title": "Last Event",
                    "type": "stat"
                },
                # Panel 4: Event Rate by Type
                {
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
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {"type": "linear"},
                                "showPoints": "auto",
                                "spanNulls": False,
                                "stacking": {"group": "A", "mode": "none"},
                                "thresholdsStyle": {"mode": "off"}
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [{"color": "green", "value": None}]
                            },
                            "unit": "eventsps"
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 6},
                    "id": 4,
                    "options": {
                        "legend": {"calcs": ["last", "max"], "displayMode": "table", "placement": "bottom"},
                        "tooltip": {"mode": "multi", "sort": "desc"}
                    },
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": "rate(webhook_events_received_total[1m])",
                            "legendFormat": "{{event_type}} ({{status}})",
                            "refId": "A"
                        }
                    ],
                    "title": "Event Rate by Type",
                    "type": "timeseries"
                },
                # Panel 5: Processing Duration
                {
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
                                "fillOpacity": 20,
                                "gradientMode": "opacity",
                                "hideFrom": {"tooltip": False, "viz": False, "legend": False},
                                "lineInterpolation": "smooth",
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {"type": "linear"},
                                "showPoints": "auto",
                                "spanNulls": False,
                                "stacking": {"group": "A", "mode": "none"},
                                "thresholdsStyle": {"mode": "off"}
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [{"color": "green", "value": None}]
                            },
                            "unit": "ms"
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 6},
                    "id": 5,
                    "options": {
                        "legend": {"calcs": ["mean", "max"], "displayMode": "table", "placement": "bottom"},
                        "tooltip": {"mode": "multi", "sort": "none"}
                    },
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": "rate(webhook_processing_duration_seconds_sum[5m]) / rate(webhook_processing_duration_seconds_count[5m]) * 1000",
                            "legendFormat": "{{event_type}}",
                            "refId": "A"
                        }
                    ],
                    "title": "Average Processing Duration",
                    "type": "timeseries"
                },
                # Panel 6: Payload Size (Average over time)
                {
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
                                "fillOpacity": 20,
                                "gradientMode": "opacity",
                                "hideFrom": {"tooltip": False, "viz": False, "legend": False},
                                "lineInterpolation": "smooth",
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {"type": "linear"},
                                "showPoints": "auto",
                                "spanNulls": False,
                                "stacking": {"group": "A", "mode": "none"},
                                "thresholdsStyle": {"mode": "off"}
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [{"color": "green", "value": None}]
                            },
                            "unit": "bytes"
                        }
                    },
                    "gridPos": {"h": 8, "w": 24, "x": 0, "y": 14},
                    "id": 6,
                    "options": {
                        "legend": {"calcs": ["mean", "last", "max"], "displayMode": "table", "placement": "bottom"},
                        "tooltip": {"mode": "multi", "sort": "desc"}
                    },
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "expr": "rate(webhook_payload_size_bytes_sum[5m]) / rate(webhook_payload_size_bytes_count[5m])",
                            "legendFormat": "{{event_type}} - avg size",
                            "refId": "A"
                        }
                    ],
                    "title": "Average Payload Size",
                    "type": "timeseries"
                }
            ],
            "refresh": "10s",
            "schemaVersion": 38,
            "style": "dark",
            "tags": ["webhook", "events", "auto-generated"],
            "templating": {"list": []},
            "time": {"from": "now-1h", "to": "now"},
            "timepicker": {},
            "timezone": "",
            "title": f"RHINOMETRIC - {name} Webhook Monitoring",
            "uid": uid,
            "version": 0,
            "weekStart": ""
        }
