"""
Rhino Core - Correlation Engine v1.0
Motor de correlación automática para eventos de observabilidad
Integra métricas (VictoriaMetrics/Prometheus), logs (Loki), trazas (Jaeger) y anomalías (IA)

Autor: Rhinometric.com
Fecha: 09 de febrero de 2026
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
from config import settings

logger = logging.getLogger(__name__)


class CorrelationEngine:
    """
    Motor de correlación de eventos de observabilidad.
    
    Nivel 1 (MVP): Correlación por timestamp (ventana de ±5 minutos)
    Nivel 2 (Futuro): Correlación por topología (host, servicio, pod)
    Nivel 3 (Futuro): Correlación por trace_id (OTLP)
    """
    
    def __init__(self):
        self.prometheus_url = settings.PROMETHEUS_URL or "http://prometheus:9090"
        self.victoria_metrics_url = "http://victoria-metrics:8428"
        self.loki_url = settings.LOKI_URL or "http://loki:3100"
        self.jaeger_url = settings.JAEGER_URL or "http://jaeger:16686"
        self.ai_anomaly_url = settings.AI_ANOMALY_URL or "http://rhinometric-ai-anomaly:8085"
        
        # Configuración de ventana de correlación (en segundos)
        self.correlation_window = 300  # ±5 minutos por defecto
        
        # Preferencia de TSDB (VictoriaMetrics first, fallback a Prometheus)
        self.use_victoria_metrics = True
        
        logger.info("CorrelationEngine initialized")
        logger.info(f"  • VictoriaMetrics: {self.victoria_metrics_url}")
        logger.info(f"  • Prometheus: {self.prometheus_url}")
        logger.info(f"  • Loki: {self.loki_url}")
        logger.info(f"  • Correlation window: ±{self.correlation_window}s")
    
    async def correlate_event(
        self, 
        event_id: str,
        event_timestamp: datetime,
        event_type: str,  # "anomaly", "alert", "log", "trace"
        event_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Correlaciona un evento con datos de observabilidad en una ventana de tiempo.
        
        Args:
            event_id: ID único del evento (ej. anomaly_12345)
            event_timestamp: Timestamp del evento
            event_type: Tipo de evento (anomaly, alert, log, trace)
            event_metadata: Metadatos adicionales (host, service, labels, etc.)
        
        Returns:
            Dict con datos correlacionados:
            {
                "event_id": "...",
                "timestamp": "...",
                "correlation_window": {"start": "...", "end": "..."},
                "metrics": [...],  # Métricas relevantes en ventana
                "logs": [...],     # Logs relacionados
                "traces": [...],   # Trazas relacionadas (futuro)
                "related_anomalies": [...]  # Otras anomalías en ventana
            }
        """
        logger.info(f"Correlating event: {event_id} (type={event_type})")
        
        # Calcular ventana de correlación
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
        
        # 🔍 Nivel 1: Correlación por timestamp
        try:
            # Buscar métricas relevantes
            metrics = await self._fetch_metrics_in_window(
                window_start, 
                window_end, 
                event_metadata
            )
            correlation_result["metrics"] = metrics
            
            # Buscar logs relacionados
            logs = await self._fetch_logs_in_window(
                window_start,
                window_end,
                event_metadata
            )
            correlation_result["logs"] = logs
            
            # Buscar anomalías relacionadas (de IA Anomaly)
            related_anomalies = await self._fetch_anomalies_in_window(
                window_start,
                window_end,
                event_metadata
            )
            correlation_result["related_anomalies"] = related_anomalies
            
            # TODO: Nivel 2 - Correlación por topología (host, service, pod)
            # TODO: Nivel 3 - Correlación por trace_id (OTLP)
            
            logger.info(f"Correlation complete for {event_id}: " +
                       f"{len(metrics)} metrics, {len(logs)} logs, " +
                       f"{len(related_anomalies)} anomalies")
            
        except Exception as e:
            logger.error(f"Error correlating event {event_id}: {e}", exc_info=True)
            correlation_result["error"] = str(e)
        
        return correlation_result
    
    async def _fetch_metrics_in_window(
        self, 
        start: datetime, 
        end: datetime,
        metadata: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Busca métricas relevantes en VictoriaMetrics/Prometheus en ventana de tiempo.
        
        Estrategia:
        - Si metadata tiene 'host', buscar métricas de ese host
        - Si metadata tiene 'metric_name', buscar esa métrica específica
        - Si no, buscar métricas comunes (CPU, memory, disk)
        """
        metrics_data = []
        
        # Seleccionar TSDB (VictoriaMetrics preferido)
        tsdb_url = self.victoria_metrics_url if self.use_victoria_metrics else self.prometheus_url
        
        try:
            # Construir queries PromQL basadas en metadata
            queries = self._build_metric_queries(metadata)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for query_name, query in queries.items():
                    try:
                        # Query range para ventana de tiempo
                        params = {
                            "query": query,
                            "start": start.timestamp(),
                            "end": end.timestamp(),
                            "step": "30s"  # Resolución 30s
                        }
                        
                        response = await client.get(
                            f"{tsdb_url}/api/v1/query_range",
                            params=params
                        )
                        
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
    
    async def _fetch_logs_in_window(
        self, 
        start: datetime, 
        end: datetime,
        metadata: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Busca logs relacionados en Loki en ventana de tiempo.
        
        Estrategia:
        - Si metadata tiene 'host', buscar logs de ese host
        - Si metadata tiene 'service', buscar logs de ese servicio
        - Si metadata tiene 'level', filtrar por nivel (error, warning)
        """
        logs_data = []
        
        try:
            # Construir LogQL query basada en metadata
            logql_query = self._build_log_query(metadata)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "query": logql_query,
                    "start": int(start.timestamp() * 1e9),  # Nanosegundos
                    "end": int(end.timestamp() * 1e9),
                    "limit": 500  # Límite de logs
                }
                
                response = await client.get(
                    f"{self.loki_url}/loki/api/v1/query_range",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        results = data.get("data", {}).get("result", [])
                        
                        for result in results:
                            stream_labels = result.get("stream", {})
                            values = result.get("values", [])
                            
                            for timestamp_ns, log_line in values:
                                logs_data.append({
                                    "timestamp": int(timestamp_ns) / 1e9,  # Convertir a segundos
                                    "labels": stream_labels,
                                    "line": log_line
                                })
                else:
                    logger.warning(f"Loki query failed (status={response.status_code})")
        
        except Exception as e:
            logger.error(f"Error fetching logs from Loki: {e}")
        
        return logs_data
    
    async def _fetch_anomalies_in_window(
        self, 
        start: datetime, 
        end: datetime,
        metadata: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Busca anomalías detectadas por IA Anomaly en ventana de tiempo.
        """
        anomalies_data = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Llamar al endpoint de IA Anomaly (asumiendo que tiene uno para búsqueda)
                params = {
                    "start": start.isoformat(),
                    "end": end.isoformat()
                }
                
                # TODO: Ajustar endpoint real de IA Anomaly cuando esté disponible
                response = await client.get(
                    f"{self.ai_anomaly_url}/api/anomalies",
                    params=params
                )
                
                if response.status_code == 200:
                    anomalies_data = response.json().get("anomalies", [])
                else:
                    logger.warning(f"AI Anomaly query failed (status={response.status_code})")
        
        except Exception as e:
            logger.error(f"Error fetching anomalies from IA: {e}")
        
        return anomalies_data
    
    def _build_metric_queries(self, metadata: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """
        Construye queries PromQL relevantes basadas en metadata del evento.
        """
        queries = {}
        
        # Filtro de host si está disponible
        host_filter = ""
        if metadata and "host" in metadata:
            host_filter = f'instance=~".*{metadata["host"]}.*"'
        elif metadata and "instance" in metadata:
            host_filter = f'instance="{metadata["instance"]}"'
        
        # Si hay métrica específica en metadata, buscarla
        if metadata and "metric_name" in metadata:
            queries["specific_metric"] = metadata["metric_name"]
            if host_filter:
                queries["specific_metric"] += f"{{{host_filter}}}"
        else:
            # Métricas comunes por defecto
            queries["cpu_usage"] = f'100 - (avg by (instance) (rate(node_cpu_seconds_total{{mode="idle",{host_filter}}}[5m])) * 100)'
            queries["memory_usage"] = f'(1 - (node_memory_MemAvailable_bytes{{{host_filter}}} / node_memory_MemTotal_bytes{{{host_filter}}})) * 100'
            queries["disk_usage"] = f'(node_filesystem_size_bytes{{{host_filter}}} - node_filesystem_avail_bytes{{{host_filter}}}) / node_filesystem_size_bytes{{{host_filter}}} * 100'
            queries["network_receive"] = f'rate(node_network_receive_bytes_total{{{host_filter}}}[5m])'
        
        return queries
    
    def _build_log_query(self, metadata: Optional[Dict[str, Any]]) -> str:
        """
        Construye query LogQL basada en metadata del evento.
        """
        # Query básico (todos los logs)
        query = '{job=~".+"}'
        
        # Filtros adicionales basados en metadata
        if metadata:
            if "host" in metadata:
                query = f'{{instance=~".*{metadata["host"]}.*"}}'
            elif "service" in metadata:
                query = f'{{job="{metadata["service"]}"}}'
            
            # Filtrar por nivel de error si se especifica
            if "level" in metadata:
                query += f' |~ "{metadata["level"]}"'
            else:
                # Por defecto, buscar errores y warnings
                query += ' |~ "(?i)(error|warn|fail|exception)"'
        
        return query


# Singleton para uso global
_correlation_engine: Optional[CorrelationEngine] = None


def get_correlation_engine() -> CorrelationEngine:
    """
    Obtiene la instancia singleton del motor de correlación.
    """
    global _correlation_engine
    if _correlation_engine is None:
        _correlation_engine = CorrelationEngine()
    return _correlation_engine
