"""
Data Aggregation Service
Fetches metrics, anomalies, and dashboard data from Prometheus, AI Anomaly API, and Grafana
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
from app.config import config_manager

logger = logging.getLogger(__name__)


class DataAggregator:
    """Aggregates data from multiple sources for report generation"""
    
    def __init__(self):
        self.config = config_manager.config
        self.prometheus_url = self.config.prometheus.url
        self.grafana_url = self.config.grafana.url
        self.timeout = self.config.prometheus.timeout
    
    async def _fetch_prometheus_query(
        self,
        query: str,
        time_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """Execute Prometheus query"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if time_range:
                    start, end = time_range
                    params = {
                        "query": query,
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                        "step": "5m"
                    }
                    url = f"{self.prometheus_url}/api/v1/query_range"
                else:
                    params = {"query": query}
                    url = f"{self.prometheus_url}/api/v1/query"
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                if data.get("status") == "success":
                    return data.get("data", {})
                else:
                    logger.error(f"Prometheus query failed: {data.get('error')}")
                    return {}
        
        except Exception as e:
            logger.error(f"Error fetching Prometheus data: {e}")
            return {}
    
    async def get_system_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get system-level metrics summary"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        time_range = (start_time, end_time)
        
        metrics = {}
        
        # CPU Usage
        cpu_query = 'avg(rate(node_cpu_seconds_total{mode!="idle"}[5m])) * 100'
        cpu_data = await self._fetch_prometheus_query(cpu_query, time_range)
        metrics["cpu"] = self._extract_metric_summary(cpu_data)
        
        # Memory Usage
        mem_query = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
        mem_data = await self._fetch_prometheus_query(mem_query, time_range)
        metrics["memory"] = self._extract_metric_summary(mem_data)
        
        # Disk Usage
        disk_query = '(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100'
        disk_data = await self._fetch_prometheus_query(disk_query, time_range)
        metrics["disk"] = self._extract_metric_summary(disk_data)
        
        # Network Traffic
        net_rx_query = 'sum(rate(node_network_receive_bytes_total[5m]))'
        net_tx_query = 'sum(rate(node_network_transmit_bytes_total[5m]))'
        
        net_rx_data = await self._fetch_prometheus_query(net_rx_query, time_range)
        net_tx_data = await self._fetch_prometheus_query(net_tx_query, time_range)
        
        metrics["network"] = {
            "receive": self._extract_metric_summary(net_rx_data),
            "transmit": self._extract_metric_summary(net_tx_data)
        }
        
        return metrics
    
    async def get_application_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get application-level metrics"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        time_range = (start_time, end_time)
        
        metrics = {}
        
        # HTTP Request Rate
        http_rate_query = 'sum(rate(http_requests_total[5m]))'
        http_data = await self._fetch_prometheus_query(http_rate_query, time_range)
        metrics["http_request_rate"] = self._extract_metric_summary(http_data)
        
        # HTTP Error Rate
        http_error_query = 'sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))'
        error_data = await self._fetch_prometheus_query(http_error_query, time_range)
        metrics["http_error_rate"] = self._extract_metric_summary(error_data)
        
        # API Latency
        latency_query = 'histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))'
        latency_data = await self._fetch_prometheus_query(latency_query, time_range)
        metrics["api_latency_p95"] = self._extract_metric_summary(latency_data)
        
        # Database Connections
        db_conn_query = 'sum(pg_stat_activity_count{state="active"})'
        db_data = await self._fetch_prometheus_query(db_conn_query, time_range)
        metrics["db_connections"] = self._extract_metric_summary(db_data)
        
        return metrics
    
    async def get_anomalies(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Fetch detected anomalies from AI Anomaly API"""
        try:
            ai_anomaly_url = "http://rhinometric-ai-anomaly:8085"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get recent anomalies
                response = await client.get(
                    f"{ai_anomaly_url}/api/v1/anomalies",
                    params={"hours": hours}
                )
                response.raise_for_status()
                
                anomalies = response.json().get("anomalies", [])
                
                # Get anomaly statistics
                stats_response = await client.get(f"{ai_anomaly_url}/api/v1/statistics")
                stats_response.raise_for_status()
                stats = stats_response.json()
                
                return {
                    "anomalies": anomalies,
                    "statistics": stats,
                    "count": len(anomalies)
                }
        
        except Exception as e:
            logger.error(f"Error fetching anomalies: {e}")
            return {"anomalies": [], "statistics": {}, "count": 0}
    
    async def get_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Fetch active alerts from Alertmanager"""
        try:
            alertmanager_url = "http://alertmanager:9093"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{alertmanager_url}/api/v2/alerts")
                response.raise_for_status()
                
                all_alerts = response.json()
                
                # Filter by time
                cutoff_time = datetime.now() - timedelta(hours=hours)
                recent_alerts = [
                    alert for alert in all_alerts
                    if self._parse_alert_time(alert.get("startsAt", "")) >= cutoff_time
                ]
                
                return {
                    "alerts": recent_alerts,
                    "count": len(recent_alerts),
                    "active": len([a for a in recent_alerts if a.get("status", {}).get("state") == "active"])
                }
        
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
            return {"alerts": [], "count": 0, "active": 0}
    
    async def get_dashboard_snapshot(self, dashboard_uid: str) -> Optional[str]:
        """Get Grafana dashboard snapshot URL"""
        try:
            auth = (self.config.grafana.username, self.config.grafana.password)
            
            async with httpx.AsyncClient(timeout=self.timeout, auth=auth) as client:
                # Create snapshot
                snapshot_data = {
                    "dashboard": {"uid": dashboard_uid},
                    "expires": 86400  # 24 hours
                }
                
                response = await client.post(
                    f"{self.grafana_url}/api/snapshots",
                    json=snapshot_data
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("url")
        
        except Exception as e:
            logger.error(f"Error creating dashboard snapshot: {e}")
            return None
    
    async def aggregate_report_data(
        self,
        report_type: str = "executive",
        hours: int = 24
    ) -> Dict[str, Any]:
        """Aggregate all data needed for report generation"""
        logger.info(f"Aggregating data for {report_type} report (last {hours}h)")
        
        # Fetch all data in parallel
        system_metrics_task = self.get_system_metrics(hours)
        app_metrics_task = self.get_application_metrics(hours)
        anomalies_task = self.get_anomalies(hours)
        alerts_task = self.get_alerts(hours)
        
        system_metrics, app_metrics, anomalies, alerts = await asyncio.gather(
            system_metrics_task,
            app_metrics_task,
            anomalies_task,
            alerts_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(system_metrics, Exception):
            logger.error(f"System metrics error: {system_metrics}")
            system_metrics = {}
        
        if isinstance(app_metrics, Exception):
            logger.error(f"App metrics error: {app_metrics}")
            app_metrics = {}
        
        if isinstance(anomalies, Exception):
            logger.error(f"Anomalies error: {anomalies}")
            anomalies = {"anomalies": [], "statistics": {}, "count": 0}
        
        if isinstance(alerts, Exception):
            logger.error(f"Alerts error: {alerts}")
            alerts = {"alerts": [], "count": 0, "active": 0}
        
        # Build report data structure
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "period_hours": hours,
            "report_type": report_type,
            "system_metrics": system_metrics,
            "application_metrics": app_metrics,
            "anomalies": anomalies,
            "alerts": alerts,
            "summary": self._generate_summary(
                system_metrics,
                app_metrics,
                anomalies,
                alerts
            )
        }
        
        logger.info("Data aggregation complete")
        return report_data
    
    def _extract_metric_summary(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract summary statistics from Prometheus result"""
        result = data.get("result", [])
        
        if not result:
            return {"current": 0, "avg": 0, "min": 0, "max": 0}
        
        values = []
        for series in result:
            if "values" in series:
                values.extend([float(v[1]) for v in series["values"]])
            elif "value" in series:
                values.append(float(series["value"][1]))
        
        if not values:
            return {"current": 0, "avg": 0, "min": 0, "max": 0}
        
        return {
            "current": values[-1] if values else 0,
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "count": len(values)
        }
    
    def _parse_alert_time(self, time_str: str) -> datetime:
        """Parse alert timestamp"""
        try:
            return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except:
            return datetime.min
    
    def _generate_summary(
        self,
        system_metrics: Dict,
        app_metrics: Dict,
        anomalies: Dict,
        alerts: Dict
    ) -> Dict[str, Any]:
        """Generate executive summary"""
        return {
            "health_score": self._calculate_health_score(system_metrics, app_metrics),
            "total_anomalies": anomalies.get("count", 0),
            "active_alerts": alerts.get("active", 0),
            "cpu_avg": system_metrics.get("cpu", {}).get("avg", 0),
            "memory_avg": system_metrics.get("memory", {}).get("avg", 0),
            "error_rate": app_metrics.get("http_error_rate", {}).get("avg", 0),
            "status": self._determine_status(anomalies, alerts)
        }
    
    def _calculate_health_score(
        self,
        system_metrics: Dict,
        app_metrics: Dict
    ) -> float:
        """Calculate overall system health score (0-100)"""
        score = 100.0
        
        # Deduct points for high resource usage
        cpu_avg = system_metrics.get("cpu", {}).get("avg", 0)
        if cpu_avg > 80:
            score -= 20
        elif cpu_avg > 60:
            score -= 10
        
        mem_avg = system_metrics.get("memory", {}).get("avg", 0)
        if mem_avg > 90:
            score -= 20
        elif mem_avg > 70:
            score -= 10
        
        # Deduct points for errors
        error_rate = app_metrics.get("http_error_rate", {}).get("avg", 0)
        if error_rate > 0.05:  # > 5%
            score -= 30
        elif error_rate > 0.01:  # > 1%
            score -= 15
        
        return max(0, min(100, score))
    
    def _determine_status(self, anomalies: Dict, alerts: Dict) -> str:
        """Determine overall system status"""
        active_alerts = alerts.get("active", 0)
        anomaly_count = anomalies.get("count", 0)
        
        if active_alerts > 5 or anomaly_count > 10:
            return "critical"
        elif active_alerts > 0 or anomaly_count > 5:
            return "warning"
        else:
            return "healthy"


# Global data aggregator instance
data_aggregator = DataAggregator()
