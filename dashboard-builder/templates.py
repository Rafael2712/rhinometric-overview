"""
Dashboard Templates
Pre-built dashboard templates for common use cases
"""
from typing import Dict, List, Any
from enum import Enum
from panels import panel_builder
from prometheus_api import MetricType


class TemplateType(str, Enum):
    """Available template types"""
    SYSTEM_OVERVIEW = "system-overview"
    APPLICATION_PERFORMANCE = "application-performance"
    DATABASE_MONITORING = "database-monitoring"
    NETWORK_TRAFFIC = "network-traffic"
    CONTAINER_MONITORING = "container-monitoring"
    ANOMALY_DETECTION = "anomaly-detection"
    CUSTOM = "custom"


class DashboardTemplates:
    """Pre-built dashboard templates"""
    
    @staticmethod
    def create_system_overview() -> Dict[str, Any]:
        """System Overview dashboard template"""
        panels = [
            # Row 1: Key metrics
            panel_builder.create_stat_panel(
                panel_id=1,
                title="CPU Usage",
                query='avg(rate(node_cpu_seconds_total{mode!="idle"}[5m])) * 100',
                x=0, y=0, width=6, height=4,
                unit="percent",
                thresholds=[
                    {"value": 0, "color": "green"},
                    {"value": 70, "color": "yellow"},
                    {"value": 90, "color": "red"},
                ],
            ),
            panel_builder.create_stat_panel(
                panel_id=2,
                title="Memory Usage",
                query='(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
                x=6, y=0, width=6, height=4,
                unit="percent",
            ),
            panel_builder.create_stat_panel(
                panel_id=3,
                title="Disk Usage",
                query='(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100',
                x=12, y=0, width=6, height=4,
                unit="percent",
            ),
            panel_builder.create_stat_panel(
                panel_id=4,
                title="Uptime",
                query='time() - node_boot_time_seconds',
                x=18, y=0, width=6, height=4,
                unit="s",
            ),
            
            # Row 2: CPU Details
            panel_builder.create_graph_panel(
                panel_id=5,
                title="CPU Usage Over Time",
                query='avg(rate(node_cpu_seconds_total{mode!="idle"}[5m])) * 100',
                x=0, y=4, width=12, height=8,
                unit="percent",
                legend="CPU",
            ),
            panel_builder.create_graph_panel(
                panel_id=6,
                title="CPU by Core",
                query='rate(node_cpu_seconds_total{mode!="idle"}[5m]) * 100',
                x=12, y=4, width=12, height=8,
                unit="percent",
                legend="{{cpu}}",
            ),
            
            # Row 3: Memory & Disk
            panel_builder.create_graph_panel(
                panel_id=7,
                title="Memory Usage",
                query='node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes',
                x=0, y=12, width=12, height=8,
                unit="bytes",
                legend="Used Memory",
            ),
            panel_builder.create_graph_panel(
                panel_id=8,
                title="Disk I/O",
                query='rate(node_disk_read_bytes_total[5m]) + rate(node_disk_written_bytes_total[5m])',
                x=12, y=12, width=12, height=8,
                unit="Bps",
                legend="Total I/O",
            ),
            
            # Row 4: Network
            panel_builder.create_graph_panel(
                panel_id=9,
                title="Network Traffic",
                query='rate(node_network_receive_bytes_total[5m]) + rate(node_network_transmit_bytes_total[5m])',
                x=0, y=20, width=24, height=8,
                unit="Bps",
                legend="Total Traffic",
            ),
        ]
        
        return {
            "title": "System Overview",
            "tags": ["system", "overview", "template"],
            "timezone": "browser",
            "editable": True,
            "panels": panels,
            "refresh": "30s",
            "time": {"from": "now-6h", "to": "now"},
        }
    
    @staticmethod
    def create_application_performance() -> Dict[str, Any]:
        """Application Performance dashboard template"""
        panels = [
            # Row 1: Request metrics
            panel_builder.create_stat_panel(
                panel_id=1,
                title="Request Rate",
                query='sum(rate(http_requests_total[5m]))',
                x=0, y=0, width=6, height=4,
                unit="reqps",
            ),
            panel_builder.create_stat_panel(
                panel_id=2,
                title="Error Rate",
                query='sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100',
                x=6, y=0, width=6, height=4,
                unit="percent",
                thresholds=[
                    {"value": 0, "color": "green"},
                    {"value": 1, "color": "yellow"},
                    {"value": 5, "color": "red"},
                ],
            ),
            panel_builder.create_stat_panel(
                panel_id=3,
                title="Avg Response Time",
                query='histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))',
                x=12, y=0, width=6, height=4,
                unit="s",
            ),
            panel_builder.create_stat_panel(
                panel_id=4,
                title="Active Users",
                query='sum(http_concurrent_requests)',
                x=18, y=0, width=6, height=4,
                unit="short",
            ),
            
            # Row 2: Request rate over time
            panel_builder.create_graph_panel(
                panel_id=5,
                title="Request Rate Over Time",
                query='sum(rate(http_requests_total[5m])) by (method)',
                x=0, y=4, width=24, height=8,
                unit="reqps",
                legend="{{method}}",
            ),
            
            # Row 3: Response time
            panel_builder.create_graph_panel(
                panel_id=6,
                title="Response Time (P50, P95, P99)",
                query='histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))',
                x=0, y=12, width=12, height=8,
                unit="s",
                legend="P95",
            ),
            panel_builder.create_graph_panel(
                panel_id=7,
                title="Error Rate by Status",
                query='sum(rate(http_requests_total{status=~"[45].."}[5m])) by (status)',
                x=12, y=12, width=12, height=8,
                unit="reqps",
                legend="{{status}}",
            ),
        ]
        
        return {
            "title": "Application Performance",
            "tags": ["application", "performance", "template"],
            "timezone": "browser",
            "editable": True,
            "panels": panels,
            "refresh": "30s",
            "time": {"from": "now-1h", "to": "now"},
        }
    
    @staticmethod
    def create_database_monitoring() -> Dict[str, Any]:
        """Database Monitoring dashboard template"""
        panels = [
            panel_builder.create_stat_panel(
                panel_id=1,
                title="Active Connections",
                query='sum(pg_stat_activity_count{state="active"})',
                x=0, y=0, width=6, height=4,
                unit="short",
            ),
            panel_builder.create_stat_panel(
                panel_id=2,
                title="Total Connections",
                query='sum(pg_stat_activity_count)',
                x=6, y=0, width=6, height=4,
                unit="short",
            ),
            panel_builder.create_graph_panel(
                panel_id=3,
                title="Connection Pool",
                query='pg_stat_activity_count by (state)',
                x=0, y=4, width=24, height=8,
                unit="short",
                legend="{{state}}",
            ),
        ]
        
        return {
            "title": "Database Monitoring",
            "tags": ["database", "postgresql", "template"],
            "timezone": "browser",
            "editable": True,
            "panels": panels,
            "refresh": "30s",
            "time": {"from": "now-1h", "to": "now"},
        }
    
    @staticmethod
    def get_template(template_type: TemplateType) -> Dict[str, Any]:
        """Get dashboard template by type"""
        templates = {
            TemplateType.SYSTEM_OVERVIEW: DashboardTemplates.create_system_overview,
            TemplateType.APPLICATION_PERFORMANCE: DashboardTemplates.create_application_performance,
            TemplateType.DATABASE_MONITORING: DashboardTemplates.create_database_monitoring,
        }
        
        if template_type in templates:
            return templates[template_type]()
        
        raise ValueError(f"Unknown template type: {template_type}")
    
    @staticmethod
    def list_templates() -> List[Dict[str, Any]]:
        """List all available templates"""
        return [
            {
                "id": TemplateType.SYSTEM_OVERVIEW,
                "name": "System Overview",
                "description": "Complete system monitoring with CPU, Memory, Disk, Network",
                "panels": 9,
                "category": "Infrastructure",
            },
            {
                "id": TemplateType.APPLICATION_PERFORMANCE,
                "name": "Application Performance",
                "description": "Monitor API performance, request rates, errors, latency",
                "panels": 7,
                "category": "Application",
            },
            {
                "id": TemplateType.DATABASE_MONITORING,
                "name": "Database Monitoring",
                "description": "PostgreSQL monitoring with connections, queries, performance",
                "panels": 3,
                "category": "Database",
            },
            {
                "id": TemplateType.NETWORK_TRAFFIC,
                "name": "Network Traffic",
                "description": "Network monitoring with bandwidth, errors, packets",
                "panels": 6,
                "category": "Network",
            },
            {
                "id": TemplateType.CONTAINER_MONITORING,
                "name": "Container Monitoring",
                "description": "Docker/K8s monitoring with resource usage per container",
                "panels": 8,
                "category": "Containers",
            },
            {
                "id": TemplateType.ANOMALY_DETECTION,
                "name": "AI Anomaly Detection",
                "description": "View anomalies detected by ML models",
                "panels": 10,
                "category": "AI/ML",
            },
        ]


# Global templates instance
dashboard_templates = DashboardTemplates()
