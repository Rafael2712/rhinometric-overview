"""
Rhino Core - Correlation Engine v2.0
Dynamic correlation engine for observability events.
Builds PromQL and LogQL queries from actual anomaly event data.
NO hardcoded queries. Metrics + Logs only. Traces out of scope.

Author: Rhinometric.com
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
from config import settings

logger = logging.getLogger(__name__)


# -- AI config name -> actual Prometheus metric name ----------------
CONFIG_NAME_TO_METRIC: Dict[str, str] = {
    "external_service_availability": "external_service_up",
    "external_service_health": "external_service_health_score",
    "external_service_latency": "external_service_latency_ms",
    "cpu_usage": "node_cpu_usage",
    "memory_usage": "node_memory_usage",
    "disk_usage": "node_disk_usage",
    "disk_io": "node_disk_io",
    "network_receive": "node_network_receive",
    "network_transmit": "node_network_transmit",
    "website_response_time": "rhinometric_website_response_time",
    "website_availability": "rhinometric_website_availability",
    "website_dns_time": "rhinometric_website_dns_time",
    "website_ssl_expiry": "rhinometric_website_ssl_expiry",
}


# -- Dynamic Query Registry ----------------------------------------
METRIC_QUERY_TEMPLATES: Dict[str, Dict[str, str]] = {
    "service": {
        "external_service_latency_ms":
            'external_service_latency_ms{{service_name="{entity_name}"}}',
        "external_service_health_score":
            'external_service_health_score{{service_name="{entity_name}"}}',
        "external_service_up":
            'external_service_up{{service_name="{entity_name}"}}',
    },
    "infrastructure": {
        "node_cpu_usage":
            '100 - (avg by (instance) (rate(node_cpu_seconds_total{{mode="idle",job="node-exporter"}}[5m])) * 100)',
        "node_memory_usage":
            '(1 - (node_memory_MemAvailable_bytes{{job="node-exporter"}} / node_memory_MemTotal_bytes{{job="node-exporter"}})) * 100',
        "node_disk_usage":
            '(node_filesystem_size_bytes{{job="node-exporter"}} - node_filesystem_avail_bytes{{job="node-exporter"}}) / node_filesystem_size_bytes{{job="node-exporter"}} * 100',
        "node_disk_io":
            'rate(node_disk_io_time_seconds_total{{job="node-exporter"}}[5m])',
        "node_network_receive":
            'rate(node_network_receive_bytes_total{{job="node-exporter"}}[5m])',
        "node_network_transmit":
            'rate(node_network_transmit_bytes_total{{job="node-exporter"}}[5m])',
    },
    "website": {
        "rhinometric_website_response_time": 'rhinometric_website_response_time',
        "rhinometric_website_availability": 'rhinometric_website_availability',
        "rhinometric_website_dns_time": 'rhinometric_website_dns_time',
        "rhinometric_website_ssl_expiry": 'rhinometric_website_ssl_expiry',
    },
}

LOG_QUERY_TEMPLATES: Dict[str, str] = {
    "service":
        '{{job="console-backend"}} |= "{entity_name}" |~ "(?i)(error|warn|fail|timeout|exception)"',
    "infrastructure":
        '{{job="docker_logs"}} |~ "(?i)(error|warn|fail|oom|exception)"',
    "website":
        '{{job="console-backend"}} |~ "(?i)(website|ssl|dns|response_time)" |~ "(?i)(error|warn|fail)"',
}


class CorrelationEngine:
    """
    Dynamic correlation engine for observability events.
    Builds queries from anomaly entity_type / entity_name / metric_name / source.
    Never falls back to hardcoded catch-all queries.
    Traces are out of scope.
    """

    def __init__(self):
        self.prometheus_url = settings.PROMETHEUS_URL or "http://prometheus:9090"
        self.victoria_metrics_url = settings.PROMETHEUS_URL or "http://rhinometric-prometheus:9090"
        self.loki_url = settings.LOKI_URL or "http://loki:3100"
        self.ai_anomaly_url = settings.AI_ANOMALY_URL or "http://rhinometric-ai-anomaly:8085"
        self.correlation_window = 300
        self.use_victoria_metrics = True

        logger.info("CorrelationEngine v2.0 initialized (dynamic queries, no traces)")
        logger.info(f"  VictoriaMetrics: {self.victoria_metrics_url}")
        logger.info(f"  Prometheus: {self.prometheus_url}")
        logger.info(f"  Loki: {self.loki_url}")
        logger.info(f"  Correlation window: +/-{self.correlation_window}s")

    async def correlate_event(self, event_id: str, event_timestamp: datetime, event_type: str, event_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        logger.info(f"Correlating event: {event_id} (type={event_type}, metadata={event_metadata})")
        window_start = event_timestamp - timedelta(seconds=self.correlation_window)
        window_end = event_timestamp + timedelta(seconds=self.correlation_window)

        correlation_result = {
            "event_id": event_id,
            "timestamp": event_timestamp.isoformat(),
            "event_type": event_type,
            "correlation_window": {
                "start": window_start.isoformat(),
                "end": window_end.isoformat(),
                "duration_seconds": self.correlation_window * 2
            },
            "metadata": event_metadata or {},
            "metrics": [],
            "logs": [],
            "traces": [],
            "related_anomalies": []
        }

        try:
            metrics = await self._fetch_metrics_in_window(window_start, window_end, event_metadata)
            correlation_result["metrics"] = metrics
            logs = await self._fetch_logs_in_window(window_start, window_end, event_metadata)
            correlation_result["logs"] = logs
            related_anomalies = await self._fetch_anomalies_in_window(window_start, window_end, event_metadata)
            correlation_result["related_anomalies"] = related_anomalies
            logger.info(f"Correlation complete for {event_id}: {len(metrics)} metrics, {len(logs)} logs, {len(related_anomalies)} anomalies")
        except Exception as e:
            logger.error(f"Error correlating event {event_id}: {e}", exc_info=True)
            correlation_result["error"] = str(e)

        return correlation_result

    @staticmethod
    def _normalize_metric_name(metric_name: str) -> str:
        if not metric_name:
            return ""
        base = metric_name.split("::")[0].strip()
        return CONFIG_NAME_TO_METRIC.get(base, base)

    def _build_metric_queries(self, metadata: Optional[Dict[str, Any]]) -> Dict[str, str]:
        queries: Dict[str, str] = {}
        if not metadata:
            logger.warning("No metadata provided - cannot build metric queries")
            return queries

        entity_type = metadata.get("entity_type", "").lower()
        raw_metric_name = metadata.get("metric_name", "")
        metric_name = self._normalize_metric_name(raw_metric_name)
        entity_name = metadata.get("entity_name", "")
        if raw_metric_name != metric_name:
            logger.info(f"Normalized metric_name: {raw_metric_name!r} -> {metric_name!r}")

        if not entity_type and not metric_name:
            logger.warning("No entity_type or metric_name in metadata - cannot build queries")
            return queries

        if not entity_type:
            entity_type = self._infer_entity_type(metric_name)

        templates = METRIC_QUERY_TEMPLATES.get(entity_type, {})

        if metric_name and metric_name in templates:
            query = templates[metric_name].format(entity_name=entity_name)
            queries[metric_name] = query
            for sibling_name, sibling_tmpl in templates.items():
                if sibling_name != metric_name:
                    queries[sibling_name] = sibling_tmpl.format(entity_name=entity_name)
        elif metric_name:
            if entity_name and entity_type == "service":
                queries[metric_name] = f'{metric_name}{{service_name="{entity_name}"}}'
            else:
                queries[metric_name] = metric_name
            logger.info(f"Using raw metric_name as PromQL: {metric_name}")
        elif entity_type in METRIC_QUERY_TEMPLATES:
            for name, tmpl in templates.items():
                queries[name] = tmpl.format(entity_name=entity_name)

        return queries

    def _build_log_query(self, metadata: Optional[Dict[str, Any]]) -> Optional[str]:
        if not metadata:
            logger.warning("No metadata - cannot build log query")
            return None

        entity_type = metadata.get("entity_type", "").lower()
        entity_name = metadata.get("entity_name", "")
        metric_name = self._normalize_metric_name(metadata.get("metric_name", ""))

        if not entity_type:
            entity_type = self._infer_entity_type(metric_name)

        if not entity_type:
            logger.warning("Cannot determine entity_type for log query")
            return None

        template = LOG_QUERY_TEMPLATES.get(entity_type)
        if template:
            return template.format(entity_name=entity_name)

        logger.warning(f"No log query template for entity_type={entity_type}")
        return None

    @staticmethod
    def _infer_entity_type(metric_name: str) -> str:
        if not metric_name:
            return ""
        if metric_name.startswith("external_service_"):
            return "service"
        if metric_name.startswith("node_"):
            return "infrastructure"
        if metric_name.startswith("rhinometric_website_"):
            return "website"
        return ""

    async def _fetch_metrics_in_window(self, start: datetime, end: datetime, metadata: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        metrics_data = []
        tsdb_url = self.victoria_metrics_url if self.use_victoria_metrics else self.prometheus_url
        queries = self._build_metric_queries(metadata)

        if not queries:
            logger.info("No metric queries generated - skipping metrics fetch")
            return metrics_data

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for query_name, query in queries.items():
                    try:
                        params = {"query": query, "start": start.timestamp(), "end": end.timestamp(), "step": "30s"}
                        response = await client.get(f"{tsdb_url}/api/v1/query_range", params=params)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("status") == "success":
                                results = data.get("data", {}).get("result", [])
                                for result in results:
                                    metrics_data.append({
                                        "query_name": query_name,
                                        "metric": result.get("metric", {}),
                                        "values": result.get("values", []),
                                        "source": "victoria-metrics" if self.use_victoria_metrics else "prometheus"
                                    })
                        else:
                            logger.warning(f"Metrics query failed: {query_name} (status={response.status_code})")
                    except Exception as e:
                        logger.error(f"Error fetching metric {query_name}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error connecting to TSDB: {e}")
        return metrics_data

    async def _fetch_logs_in_window(self, start: datetime, end: datetime, metadata: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logs_data = []
        logql_query = self._build_log_query(metadata)

        if not logql_query:
            logger.info("No log query generated - skipping logs fetch")
            return logs_data

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {"query": logql_query, "start": int(start.timestamp() * 1e9), "end": int(end.timestamp() * 1e9), "limit": 500}
                response = await client.get(f"{self.loki_url}/loki/api/v1/query_range", params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        results = data.get("data", {}).get("result", [])
                        for result in results:
                            stream_labels = result.get("stream", {})
                            values = result.get("values", [])
                            for timestamp_ns, log_line in values:
                                logs_data.append({"timestamp": int(timestamp_ns) / 1e9, "labels": stream_labels, "line": log_line})
                else:
                    logger.warning(f"Loki query failed (status={response.status_code})")
        except Exception as e:
            logger.error(f"Error fetching logs from Loki: {e}")
        return logs_data

    async def _fetch_anomalies_in_window(self, start: datetime, end: datetime, metadata: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        anomalies_data = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {"start": start.isoformat(), "end": end.isoformat()}
                response = await client.get(f"{self.ai_anomaly_url}/anomalies", params=params)
                if response.status_code == 200:
                    anomalies_data = response.json().get("anomalies", [])
                else:
                    logger.warning(f"AI Anomaly query failed (status={response.status_code})")
        except Exception as e:
            logger.error(f"Error fetching anomalies from IA: {e}")
        return anomalies_data


_correlation_engine: Optional[CorrelationEngine] = None


def get_correlation_engine() -> CorrelationEngine:
    global _correlation_engine
    if _correlation_engine is None:
        _correlation_engine = CorrelationEngine()
    return _correlation_engine
