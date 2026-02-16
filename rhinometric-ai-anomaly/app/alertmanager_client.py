"""
Alertmanager Client
Sends alerts to Alertmanager
"""
import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.config import AlertmanagerConfig

logger = logging.getLogger(__name__)


class AlertmanagerError(Exception):
    """Custom exception for Alertmanager errors"""
    pass


class AlertmanagerClient:
    """Client for sending alerts to Alertmanager"""
    
    def __init__(self, config: AlertmanagerConfig):
        self.config = config
        self.enabled = config.enabled
        
        if self.enabled:
            self.client = httpx.AsyncClient(
                base_url=config.url,
                timeout=config.timeout
            )
    
    async def send_alert(
        self,
        alert_name: str,
        metric_name: str,
        current_value: float,
        anomaly_score: float,
        severity: str = "warning",
        description: Optional[str] = None,
        additional_labels: Optional[Dict[str, str]] = None,
        enriched_payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send alert to Alertmanager
        
        Args:
            alert_name: Alert name
            metric_name: Metric that triggered alert
            current_value: Current metric value
            anomaly_score: Anomaly score from model
            severity: Alert severity
            description: Alert description
            additional_labels: Additional labels to attach
            enriched_payload: Pre-built alert from AlertBuilder (takes priority)
            
        Returns:
            True if alert sent successfully
        """
        if not self.enabled:
            logger.debug("Alertmanager disabled, skipping alert")
            return False
        
        try:
            # If enriched payload provided by AlertBuilder, use it directly
            if enriched_payload:
                alert = enriched_payload
                logger.debug(f"Using enriched alert from AlertBuilder for {metric_name}")
            else:
                # Fallback: Build basic alert payload
                labels = {
                    "alertname": alert_name,
                    "metric": metric_name,
                    "severity": severity,
                    **self.config.labels
                }
                
                if additional_labels:
                    labels.update(additional_labels)
                
                annotations = {
                    "summary": f"Anomaly detected in {metric_name}",
                    "description": description or f"Anomaly score: {anomaly_score:.3f}, Current value: {current_value}",
                    "current_value": str(current_value),
                    "anomaly_score": f"{anomaly_score:.3f}"
                }
                
                alert = {
                    "labels": labels,
                    "annotations": annotations,
                    "startsAt": datetime.utcnow().isoformat() + "Z",
                    "generatorURL": "http://rhinometric-ai-anomaly:8085"
                }
            
            # Send to Alertmanager
            response = await self.client.post(
                "/api/v2/alerts",
                json=[alert]
            )
            response.raise_for_status()
            
            logger.info(f"✅ Alert sent to Alertmanager: {alert_name} (enriched={enriched_payload is not None})")
            return True
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending alert: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending alert: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """
        Test connection to Alertmanager
        
        Returns:
            True if connection successful
        """
        if not self.enabled:
            return True
        
        try:
            response = await self.client.get("/-/healthy")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Alertmanager health check failed: {e}")
            return False
    
    async def get_alerts(self) -> List[Dict[str, Any]]:
        """
        Get current alerts from Alertmanager
        
        Returns:
            List of active alerts
        """
        if not self.enabled:
            return []
        
        try:
            response = await self.client.get("/api/v2/alerts")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
            return []
    
    async def close(self):
        """Close HTTP client"""
        if self.enabled:
            await self.client.aclose()
