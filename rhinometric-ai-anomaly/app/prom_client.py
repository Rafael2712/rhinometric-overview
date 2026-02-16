"""
Prometheus Client
Handles all interactions with Prometheus API
"""
import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import PrometheusConfig

logger = logging.getLogger(__name__)


class PrometheusError(Exception):
    """Custom exception for Prometheus-related errors"""
    pass


class PrometheusClient:
    """Client for querying Prometheus metrics"""
    
    def __init__(self, config: PrometheusConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.url,
            timeout=config.timeout,
            follow_redirects=True
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def query(self, query: str) -> Dict[str, Any]:
        """
        Execute instant query
        
        Args:
            query: PromQL query string
            
        Returns:
            Query result data
        """
        try:
            response = await self.client.get(
                "/api/v1/query",
                params={"query": query}
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "success":
                error_msg = data.get("error", "Unknown error")
                raise PrometheusError(f"Query failed: {error_msg}")
            
            return data.get("data", {})
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error querying Prometheus: {e}")
            raise PrometheusError(f"Failed to query Prometheus: {e}")
        except Exception as e:
            logger.error(f"Unexpected error querying Prometheus: {e}")
            raise PrometheusError(f"Prometheus query error: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "5m"
    ) -> Dict[str, Any]:
        """
        Execute range query
        
        Args:
            query: PromQL query string
            start: Start time
            end: End time
            step: Query resolution step
            
        Returns:
            Query result data
        """
        try:
            response = await self.client.get(
                "/api/v1/query_range",
                params={
                    "query": query,
                    "start": start.timestamp(),
                    "end": end.timestamp(),
                    "step": step
                }
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "success":
                error_msg = data.get("error", "Unknown error")
                raise PrometheusError(f"Range query failed: {error_msg}")
            
            return data.get("data", {})
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in range query: {e}")
            raise PrometheusError(f"Failed to execute range query: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in range query: {e}")
            raise PrometheusError(f"Range query error: {e}")
    
    async def fetch_metric_values(
        self,
        query: str,
        hours: int = 24,
        step: str = "5m"
    ) -> List[float]:
        """
        Fetch metric values for anomaly detection
        
        Args:
            query: PromQL query
            hours: Hours of historical data
            step: Query step
            
        Returns:
            List of metric values
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        try:
            data = await self.query_range(query, start_time, end_time, step)
            
            result = data.get("result", [])
            if not result:
                logger.warning(f"No data returned for query: {query}")
                return []
            
            # Extract values from result series
            # If multiple series, aggregate by averaging at each timestamp
            values = []
            
            if len(result) == 1:
                # Single series - simple case
                values = [float(v[1]) for v in result[0].get("values", [])]
            else:
                # Multiple series - aggregate by timestamp
                timestamp_values = {}
                for series in result:
                    for timestamp, value in series.get("values", []):
                        if timestamp not in timestamp_values:
                            timestamp_values[timestamp] = []
                        try:
                            timestamp_values[timestamp].append(float(value))
                        except (ValueError, TypeError):
                            continue
                
                # Average values at each timestamp and sort by timestamp
                sorted_timestamps = sorted(timestamp_values.keys())
                values = [
                    sum(timestamp_values[ts]) / len(timestamp_values[ts])
                    for ts in sorted_timestamps
                ]
            
            # Remove NaN and Inf values - ensure flat list
            values = [float(v) for v in values if isinstance(v, (int, float)) and not (v != v or v == float('inf') or v == float('-inf'))]
            
            # Final safety check - ensure truly flat
            if values and isinstance(values[0], (list, tuple)):
                logger.error(f"BUG: values is nested! First element type: {type(values[0])}, len: {len(values)}")
                # Emergency flatten
                flat_values = []
                for v in values:
                    if isinstance(v, (list, tuple)):
                        flat_values.extend([float(x) for x in v if isinstance(x, (int, float))])
                    else:
                        flat_values.append(float(v))
                values = flat_values
                logger.warning(f"Applied emergency flatten, result: {len(values)} values")
            
            logger.debug(f"Fetched {len(values)} values for query")
            return values
        
        except PrometheusError as e:
            logger.error(f"Error fetching metric values: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching values: {e}")
            return []
    
    async def fetch_metric_with_labels(
        self,
        query: str,
        hours: int = 24,
        step: str = "5m"
    ) -> Dict[str, List[float]]:
        """
        Fetch metric values grouped by labels
        
        Args:
            query: PromQL query
            hours: Hours of data
            step: Query step
            
        Returns:
            Dictionary mapping label combinations to value lists
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        try:
            data = await self.query_range(query, start_time, end_time, step)
            
            result = data.get("result", [])
            if not result:
                return {}
            
            # Group by label combination
            grouped = {}
            for series in result:
                # Create label key
                labels = series.get("metric", {})
                label_key = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
                
                # Extract values
                values = [float(v[1]) for v in series.get("values", [])]
                values = [v for v in values if not (
                    isinstance(v, float) and (v != v or v == float('inf') or v == float('-inf'))
                )]
                
                grouped[label_key] = values
            
            return grouped
        
        except Exception as e:
            logger.error(f"Error fetching metric with labels: {e}")
            return {}
    
    async def test_connection(self) -> bool:
        """
        Test connection to Prometheus
        
        Returns:
            True if connection successful
        """
        try:
            response = await self.client.get("/-/healthy")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Prometheus health check failed: {e}")
            return False
    
    async def get_targets(self) -> List[Dict[str, Any]]:
        """
        Get Prometheus targets
        
        Returns:
            List of target information
        """
        try:
            response = await self.client.get("/api/v1/targets")
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") == "success":
                return data.get("data", {}).get("activeTargets", [])
            return []
        except Exception as e:
            logger.error(f"Error fetching targets: {e}")
            return []
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
