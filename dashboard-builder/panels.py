"""
Panel Types and Configurations
Defines all available panel types for dashboard building
"""
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel


class PanelType(str, Enum):
    """Available panel types"""
    GRAPH = "graph"
    STAT = "stat"
    GAUGE = "gauge"
    TABLE = "table"
    HEATMAP = "heatmap"
    BAR_CHART = "barchart"
    PIE_CHART = "piechart"
    TEXT = "text"
    ALERT_LIST = "alertlist"
    LOGS = "logs"


class PanelConfig(BaseModel):
    """Panel configuration"""
    id: int
    title: str
    type: PanelType
    query: str
    gridPos: Dict[str, int]  # x, y, w, h
    datasource: str = "Prometheus"
    options: Dict[str, Any] = {}
    fieldConfig: Dict[str, Any] = {}


class PanelBuilder:
    """Build Grafana panel JSON from simple parameters"""
    
    @staticmethod
    def create_graph_panel(
        panel_id: int,
        title: str,
        query: str,
        x: int = 0,
        y: int = 0,
        width: int = 12,
        height: int = 8,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a time series graph panel"""
        return {
            "id": panel_id,
            "title": title,
            "type": "timeseries",
            "gridPos": {"x": x, "y": y, "w": width, "h": height},
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "targets": [{
                "expr": query,
                "refId": "A",
                "legendFormat": kwargs.get("legend", ""),
            }],
            "options": {
                "tooltip": {"mode": "multi"},
                "legend": {"displayMode": "list", "placement": "bottom"},
            },
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "palette-classic"},
                    "custom": {
                        "lineInterpolation": "linear",
                        "lineWidth": 1,
                        "fillOpacity": 10,
                        "showPoints": "auto",
                    },
                    "unit": kwargs.get("unit", "short"),
                },
            },
        }
    
    @staticmethod
    def create_stat_panel(
        panel_id: int,
        title: str,
        query: str,
        x: int = 0,
        y: int = 0,
        width: int = 6,
        height: int = 4,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a stat panel"""
        return {
            "id": panel_id,
            "title": title,
            "type": "stat",
            "gridPos": {"x": x, "y": y, "w": width, "h": height},
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "targets": [{
                "expr": query,
                "refId": "A",
            }],
            "options": {
                "reduceOptions": {
                    "values": False,
                    "calcs": [kwargs.get("calculation", "lastNotNull")],
                },
                "orientation": "auto",
                "textMode": "auto",
                "colorMode": kwargs.get("colorMode", "value"),
                "graphMode": kwargs.get("graphMode", "area"),
            },
            "fieldConfig": {
                "defaults": {
                    "unit": kwargs.get("unit", "short"),
                    "thresholds": {
                        "mode": "absolute",
                        "steps": kwargs.get("thresholds", [
                            {"value": None, "color": "green"},
                            {"value": 80, "color": "yellow"},
                            {"value": 90, "color": "red"},
                        ]),
                    },
                },
            },
        }
    
    @staticmethod
    def create_gauge_panel(
        panel_id: int,
        title: str,
        query: str,
        x: int = 0,
        y: int = 0,
        width: int = 6,
        height: int = 6,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a gauge panel"""
        return {
            "id": panel_id,
            "title": title,
            "type": "gauge",
            "gridPos": {"x": x, "y": y, "w": width, "h": height},
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "targets": [{
                "expr": query,
                "refId": "A",
            }],
            "options": {
                "showThresholdLabels": True,
                "showThresholdMarkers": True,
            },
            "fieldConfig": {
                "defaults": {
                    "unit": kwargs.get("unit", "percent"),
                    "min": kwargs.get("min", 0),
                    "max": kwargs.get("max", 100),
                    "thresholds": {
                        "mode": "absolute",
                        "steps": kwargs.get("thresholds", [
                            {"value": 0, "color": "green"},
                            {"value": 70, "color": "yellow"},
                            {"value": 90, "color": "red"},
                        ]),
                    },
                },
            },
        }
    
    @staticmethod
    def create_table_panel(
        panel_id: int,
        title: str,
        query: str,
        x: int = 0,
        y: int = 0,
        width: int = 24,
        height: int = 8,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a table panel"""
        return {
            "id": panel_id,
            "title": title,
            "type": "table",
            "gridPos": {"x": x, "y": y, "w": width, "h": height},
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "targets": [{
                "expr": query,
                "refId": "A",
                "format": "table",
                "instant": True,
            }],
            "options": {
                "showHeader": True,
                "footer": {"show": False},
            },
            "fieldConfig": {
                "defaults": {
                    "custom": {
                        "align": "auto",
                        "displayMode": "auto",
                    },
                },
            },
        }
    
    @staticmethod
    def create_pie_chart_panel(
        panel_id: int,
        title: str,
        query: str,
        x: int = 0,
        y: int = 0,
        width: int = 12,
        height: int = 8,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a pie chart panel"""
        return {
            "id": panel_id,
            "title": title,
            "type": "piechart",
            "gridPos": {"x": x, "y": y, "w": width, "h": height},
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "targets": [{
                "expr": query,
                "refId": "A",
                "legendFormat": "{{__name__}}",
            }],
            "options": {
                "legend": {"displayMode": "list", "placement": "right"},
                "pieType": kwargs.get("pieType", "pie"),
                "tooltip": {"mode": "single"},
            },
        }


# Panel builder instance
panel_builder = PanelBuilder()
