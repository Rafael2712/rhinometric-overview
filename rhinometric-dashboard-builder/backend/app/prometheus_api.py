"""
Prometheus Query Builder
Visual query builder for non-technical users
"""
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
import httpx
from app.config import config

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Common metric types"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    HTTP = "http"
    DATABASE = "database"
    CUSTOM = "custom"


class Aggregation(str, Enum):
    """Aggregation functions"""
    AVG = "avg"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    RATE = "rate"
    INCREASE = "increase"


class PrometheusQueryBuilder:
    """Build Prometheus queries from simple parameters"""
    
    # Predefined query templates
    TEMPLATES = {
        MetricType.CPU: {
            "usage": 'avg(rate(node_cpu_seconds_total{mode!="idle"}[5m])) * 100',
            "usage_by_cpu": 'rate(node_cpu_seconds_total{mode!="idle"}[5m]) * 100',
            "usage_by_mode": 'rate(node_cpu_seconds_total[5m]) * 100',
        },
        MetricType.MEMORY: {
            "usage": '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
            "available": 'node_memory_MemAvailable_bytes',
            "total": 'node_memory_MemTotal_bytes',
            "used": 'node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes',
        },
        MetricType.DISK: {
            "usage": '(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100',
            "io_read": 'rate(node_disk_read_bytes_total[5m])',
            "io_write": 'rate(node_disk_written_bytes_total[5m])',
        },
        MetricType.NETWORK: {
            "receive": 'rate(node_network_receive_bytes_total[5m])',
            "transmit": 'rate(node_network_transmit_bytes_total[5m])',
            "errors": 'rate(node_network_receive_errs_total[5m]) + rate(node_network_transmit_errs_total[5m])',
        },
        MetricType.HTTP: {
            "request_rate": 'rate(http_requests_total[5m])',
            "error_rate": 'rate(http_requests_total{status=~"5.."}[5m])',
            "latency_p95": 'histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))',
            "latency_p99": 'histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))',
        },
        MetricType.DATABASE: {
            "connections": 'pg_stat_activity_count',
            "active_connections": 'pg_stat_activity_count{state="active"}',
            "slow_queries": 'rate(pg_stat_database_blks_read[5m])',
        },
    }
    
    def __init__(self):
        self.prometheus_url = config.prometheus.url
        self.timeout = config.prometheus.timeout
    
    def build_query(
        self,
        metric_type: MetricType,
        subtype: str,
        aggregation: Optional[Aggregation] = None,
        filters: Optional[Dict[str, str]] = None,
        group_by: Optional[List[str]] = None
    ) -> str:
        """Build Prometheus query from parameters"""
        
        # Get base query from template
        if metric_type in self.TEMPLATES and subtype in self.TEMPLATES[metric_type]:
            query = self.TEMPLATES[metric_type][subtype]
        else:
            raise ValueError(f"Unknown metric: {metric_type}.{subtype}")
        
        # Apply filters
        if filters:
            filter_str = ", ".join([f'{k}="{v}"' for k, v in filters.items()])
            # Insert filters into query (basic implementation)
            query = query.replace("}", f", {filter_str}}}")
        
        # Apply aggregation
        if aggregation:
            if aggregation == Aggregation.RATE:
                query = f"rate({query}[5m])"
            elif aggregation == Aggregation.INCREASE:
                query = f"increase({query}[5m])"
            elif aggregation in [Aggregation.AVG, Aggregation.SUM, Aggregation.MIN, Aggregation.MAX]:
                query = f"{aggregation.value}({query})"
        
        # Apply grouping
        if group_by:
            group_str = ", ".join(group_by)
            query = f"{query} by ({group_str})"
        
        return query
    
    def get_metric_options(self, metric_type: MetricType) -> List[str]:
        """Get available subtypes for a metric type"""
        if metric_type in self.TEMPLATES:
            return list(self.TEMPLATES[metric_type].keys())
        return []
    
    async def validate_query(self, query: str) -> bool:
        """Validate Prometheus query"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={"query": query}
                )
                response.raise_for_status()
                result = response.json()
                return result.get("status") == "success"
        except Exception as e:
            logger.error(f"Query validation failed: {e}")
            return False
    
    async def get_metric_labels(self, metric_name: str) -> List[str]:
        """Get available labels for a metric"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.prometheus_url}/api/v1/label/__name__/values"
                )
                response.raise_for_status()
                result = response.json()
                return result.get("data", [])
        except Exception as e:
            logger.error(f"Failed to get labels: {e}")
            return []
    
    async def get_label_values(self, label: str) -> List[str]:
        """Get available values for a label"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.prometheus_url}/api/v1/label/{label}/values"
                )
                response.raise_for_status()
                result = response.json()
                return result.get("data", [])
        except Exception as e:
            logger.error(f"Failed to get label values: {e}")
            return []
    
    async def test_connection(self) -> bool:
        """Test connection to Prometheus"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.prometheus_url}/-/ready")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Prometheus connection failed: {e}")
            return False


# Global query builder instance
query_builder = PrometheusQueryBuilder()
