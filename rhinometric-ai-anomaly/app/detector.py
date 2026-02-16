"""
Anomaly Detector Engine
Core detection logic coordinating all components
"""
import os
import numpy as np
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque
from pathlib import Path

from app.config import config_manager, MetricConfig
from app.prom_client import PrometheusClient
from app.alertmanager_client import AlertmanagerClient
from app.models import ModelEnsemble
from app.baseline_manager import baseline_manager, BaselineStats
from app.alert_builder import get_alert_builder

logger = logging.getLogger(__name__)


class AnomalyResult:
    """Represents an anomaly detection result"""
    
    def __init__(
        self,
        metric_name: str,
        timestamp: datetime,
        is_anomaly: bool,
        current_value: float,
        expected_value: float,
        anomaly_score: float,
        confidence: float,
        severity: str,
        models_used: List[str],
        model_scores: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None,
        deviation_percent: Optional[float] = None,
        baseline_explanation: Optional[str] = None,
        status: str = "active",
        resolved_at: Optional[datetime] = None
    ):
        self.metric_name = metric_name
        self.timestamp = timestamp
        self.is_anomaly = is_anomaly
        self.current_value = current_value
        self.expected_value = expected_value
        self.anomaly_score = anomaly_score
        self.confidence = confidence
        self.severity = severity
        self.models_used = models_used
        self.model_scores = model_scores
        self.metadata = metadata or {}
        self.deviation_percent = deviation_percent
        self.baseline_explanation = baseline_explanation
        self.status = status  # 'active' or 'resolved'
        self.resolved_at = resolved_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "metric_name": self.metric_name,
            "timestamp": self.timestamp.isoformat(),
            "is_anomaly": self.is_anomaly,
            "current_value": self.current_value,
            "expected_value": self.expected_value,
            "anomaly_score": self.anomaly_score,
            "confidence": self.confidence,
            "severity": self.severity,
            "models_used": self.models_used,
            "model_scores": self.model_scores,
            "metadata": self.metadata,
            "status": self.status
        }
        
        # Add resolved_at if present
        if self.resolved_at:
            result["resolved_at"] = self.resolved_at.isoformat()
        
        # Add baseline fields if available
        if self.deviation_percent is not None:
            result["deviation_percent"] = self.deviation_percent
        if self.baseline_explanation:
            result["baseline_explanation"] = self.baseline_explanation
        
        return result


class AnomalyDetector:
    """Main anomaly detection engine"""
    
    def __init__(self):
        self.config = config_manager.config
        self.prometheus = PrometheusClient(self.config.prometheus)
        self.alertmanager = AlertmanagerClient(self.config.alertmanager)
        self.ensemble = ModelEnsemble(self.config.models)
        
        # Storage
        self.anomalies: deque = deque(
            maxlen=self.config.detection.max_anomalies
        )
        self.detection_history: Dict[str, List[Dict]] = {}
        
        # Model persistence
        if self.config.persistence.enabled:
            self.model_dir = Path(self.config.persistence.directory)
            self.model_dir.mkdir(parents=True, exist_ok=True)
            # Load existing models
            self.ensemble.load_models(self.model_dir)
        
        # Stats
        self.stats = {
            "total_checks": 0,
            "total_anomalies": 0,
            "checks_by_metric": {},
            "anomalies_by_metric": {},
            "last_check": None,
            "uptime_start": datetime.now()
        }
    
    async def initialize(self):
        """Initialize detector and verify connections"""
        logger.info("Initializing AI Anomaly Detector...")
        
        # Test Prometheus connection
        prometheus_ok = await self.prometheus.test_connection()
        if not prometheus_ok:
            logger.error("Failed to connect to Prometheus")
            raise ConnectionError("Prometheus connection failed")
        logger.info("✓ Prometheus connection OK")
        
        # Test Alertmanager connection
        if self.config.alertmanager.enabled:
            alertmanager_ok = await self.alertmanager.test_connection()
            if not alertmanager_ok:
                logger.warning("Failed to connect to Alertmanager")
            else:
                logger.info("✓ Alertmanager connection OK")
        
        logger.info("Initialization complete")
    
    async def detect_metric_anomalies(
        self,
        metric_config: MetricConfig
    ) -> Optional[AnomalyResult]:
        """
        Detect anomalies in a single metric
        
        Args:
            metric_config: Metric configuration
            
        Returns:
            AnomalyResult if anomaly detected, None otherwise
        """
        metric_name = metric_config.name
        
        try:
            # Fetch metric data
            lookback_hours = self.config.detection.lookback_hours
            values = await self.prometheus.fetch_metric_values(
                metric_config.query,
                hours=lookback_hours
            )
            
            # DEBUG: Log what fetch returned
            logger.info(f"FETCH DEBUG {metric_name}: type={type(values)}, len={len(values) if values else 0}, first={values[0] if values else None}")
            if values and len(values) > 0:
                logger.info(f"  first_type={type(values[0])}, has_nested={any(isinstance(v, (list, tuple)) for v in values[:10])}")
            
            if len(values) < self.config.detection.min_data_points:
                logger.debug(
                    f"Insufficient data for {metric_name}: "
                    f"{len(values)}/{self.config.detection.min_data_points} points"
                )
                return None
            
            # Convert to numpy array - ensure 1D and handle nested lists
            # Prometheus can return nested structures, flatten aggressively
            def recursive_flatten(lst):
                """Recursively flatten any nested list/array structure"""
                result = []
                for item in lst:
                    if isinstance(item, (list, tuple, np.ndarray)):
                        result.extend(recursive_flatten(item))
                    else:
                        try:
                            result.append(float(item))
                        except (ValueError, TypeError):
                            continue
                return result
            
            try:
                # Try direct conversion first
                X = np.array(values, dtype=np.float64)
                
                # Check if conversion succeeded with correct shape
                if X.ndim > 1:
                    logger.warning(f"Multidimensional array detected for {metric_name}: shape {X.shape}, flattening...")
                    X = X.flatten()
                    
            except (ValueError, TypeError) as e:
                # Direct conversion failed - likely nested lists
                logger.warning(f"Direct array conversion failed for {metric_name}: {e}. Using recursive flatten...")
                try:
                    flattened = recursive_flatten(values)
                    X = np.array(flattened, dtype=np.float64)
                    logger.info(f"Successfully flattened {metric_name}: {len(flattened)} values")
                except Exception as e2:
                    logger.error(f"Failed to flatten values for {metric_name}: {e2}")
                    return None
            
            # Log final shape for debugging
            logger.info(f"POST-CONVERT {metric_name}: X.shape={X.shape}, X.dtype={X.dtype}, X.ndim={X.ndim}")
            
            # Update baseline with historical data
            # Extract metric labels from query (simplified - assumes no complex labels)
            metric_labels = {"metric": metric_name}
            baseline_manager.update_baseline(
                metric_name=metric_name,
                metric_labels=metric_labels,
                values=X
            )
            
            logger.info(f"POST-BASELINE {metric_name}: X.shape still={X.shape}")
            
            # Train models if needed
            if self.config.detection.auto_retrain:
                # ML models expect 2D array: (n_samples, n_features)
                # Reshape 1D time series to 2D with single feature
                X_train = X.reshape(-1, 1) if X.ndim == 1 else X
                logger.info(f"PRE-TRAIN {metric_name}: reshaped X from {X.shape} to {X_train.shape}")
                train_results = self.ensemble.train_all(X_train)
                logger.debug(f"Training results for {metric_name}: {train_results}")
            
            # Detect anomalies using specified models
            model_names = metric_config.models if metric_config.models else None
            # Reshape for anomaly detection (same as training)
            X_detect = X.reshape(-1, 1) if X.ndim == 1 else X
            predictions, model_scores = self.ensemble.detect_anomalies(
                X_detect, model_names=model_names, voting="soft"
            )
            
            # Analyze recent window
            window_size = max(1, len(values) // 10)  # Last 10%
            recent_predictions = predictions[-window_size:]
            recent_values = values[-window_size:]
            
            # Check for anomalies in recent data
            anomaly_count = np.sum(recent_predictions == -1)
            
            if anomaly_count > 0 or metric_config.alert_on_any_anomaly:
                # Calculate metrics
                current_value = float(recent_values[-1])
                
                # Get dynamic baseline
                metric_labels = {"metric": metric_name}
                baseline = baseline_manager.get_expected_value(
                    metric_name=metric_name,
                    metric_labels=metric_labels
                )
                
                if baseline:
                    # Use baseline expected value
                    expected_value = baseline.mean
                    deviation_percent = baseline.deviation_percent(current_value)
                    
                    # Generate baseline explanation
                    baseline_explanation = (
                        f"Current: {current_value:.2f}, "
                        f"Expected: {expected_value:.2f} "
                        f"(range: {baseline.p10:.2f}-{baseline.p90:.2f}), "
                        f"Deviation: {deviation_percent:+.1f}%"
                    )
                else:
                    # Fallback to simple mean
                    expected_value = float(np.mean(values[:-window_size]))
                    deviation_percent = ((current_value - expected_value) / abs(expected_value) * 100) if expected_value != 0 else 0
                    baseline_explanation = None
                
                # Aggregate model scores
                score_values = {
                    name: float(scores[-1])
                    for name, scores in model_scores.items()
                }
                avg_score = np.mean(list(score_values.values()))
                
                # Determine severity based on score and sensitivity
                severity = self._calculate_severity(
                    avg_score,
                    metric_config.sensitivity,
                    anomaly_count,
                    window_size
                )
                
                # Calculate confidence
                confidence = anomaly_count / window_size
                
                # Check thresholds if defined
                threshold_breach = self._check_thresholds(
                    current_value,
                    metric_config.thresholds,
                    metric_config.invert_threshold
                )
                
                # Create result
                result = AnomalyResult(
                    metric_name=metric_name,
                    timestamp=datetime.now(),
                    is_anomaly=True,
                    current_value=current_value,
                    expected_value=expected_value,
                    anomaly_score=avg_score,
                    confidence=confidence,
                    severity=severity,
                    models_used=list(model_scores.keys()),
                    model_scores=score_values,
                    deviation_percent=deviation_percent,
                    baseline_explanation=baseline_explanation,
                    metadata={
                        "anomaly_count": int(anomaly_count),
                        "window_size": window_size,
                        "total_points": len(values),
                        "threshold_breach": threshold_breach,
                        "query": metric_config.query,
                        "priority": metric_config.priority,
                        "baseline_available": baseline is not None
                    }
                )
                
                # Store anomaly
                self.anomalies.append(result)
                
                # Update stats
                self.stats["total_anomalies"] += 1
                self.stats["anomalies_by_metric"][metric_name] = \
                    self.stats["anomalies_by_metric"].get(metric_name, 0) + 1
                
                # 🔥 EXPORT TO PROMETHEUS (FIX BUG)
                try:
                    from app.api import prom_anomalies_detected
                    prom_anomalies_detected.labels(
                        metric=metric_name,
                        severity=severity
                    ).inc()
                except Exception as e:
                    logger.error(f"Error updating Prometheus metrics: {e}")
                
                # Send alert
                if self.config.features.enable_notifications:
                    await self._send_alert(result, metric_config)
                
                logger.warning(
                    f"⚠️  Anomaly detected: {metric_name} | "
                    f"Value: {current_value:.2f} | "
                    f"Score: {avg_score:.3f} | "
                    f"Severity: {severity}"
                )
                
                return result
            
            return None
        
        except Exception as e:
            import traceback
            logger.error(f"Error detecting anomalies in {metric_name}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _calculate_severity(
        self,
        score: float,
        sensitivity: str,
        anomaly_count: int,
        window_size: int
    ) -> str:
        """Calculate anomaly severity"""
        # Thresholds based on sensitivity (configurable via env vars)
        thresholds = {
            "low": {
                "critical": float(os.getenv("ANOMALY_SEVERITY_LOW_CRITICAL", "-1.5")),
                "high": float(os.getenv("ANOMALY_SEVERITY_LOW_HIGH", "-1.0")),
                "medium": float(os.getenv("ANOMALY_SEVERITY_LOW_MEDIUM", "-0.5"))
            },
            "medium": {
                "critical": float(os.getenv("ANOMALY_SEVERITY_MEDIUM_CRITICAL", "-1.0")),
                "high": float(os.getenv("ANOMALY_SEVERITY_MEDIUM_HIGH", "-0.7")),
                "medium": float(os.getenv("ANOMALY_SEVERITY_MEDIUM_MEDIUM", "-0.4"))
            },
            "high": {
                "critical": float(os.getenv("ANOMALY_SEVERITY_HIGH_CRITICAL", "-0.7")),
                "high": float(os.getenv("ANOMALY_SEVERITY_HIGH_HIGH", "-0.5")),
                "medium": float(os.getenv("ANOMALY_SEVERITY_HIGH_MEDIUM", "-0.3"))
            }
        }
        
        t = thresholds.get(sensitivity, thresholds["medium"])
        
        # Also consider percentage of anomalous points
        anomaly_ratio = anomaly_count / window_size
        
        if score < t["critical"] or anomaly_ratio > 0.5:
            return "critical"
        elif score < t["high"] or anomaly_ratio > 0.3:
            return "high"
        elif score < t["medium"] or anomaly_ratio > 0.1:
            return "medium"
        else:
            return "low"
    
    def _check_thresholds(
        self,
        value: float,
        thresholds: Dict[str, float],
        invert: bool = False
    ) -> Optional[str]:
        """Check if value breaches thresholds"""
        if not thresholds:
            return None
        
        critical = thresholds.get("critical")
        warning = thresholds.get("warning")
        
        if invert:
            # Alert when below threshold (e.g., hit rate)
            if critical is not None and value < critical:
                return "critical"
            if warning is not None and value < warning:
                return "warning"
        else:
            # Alert when above threshold
            if critical is not None and value > critical:
                return "critical"
            if warning is not None and value > warning:
                return "warning"
        
        return None
    
    async def _send_alert(
        self,
        result: AnomalyResult,
        metric_config: MetricConfig
    ):
        """Send enriched alert to Alertmanager via AlertBuilder"""
        try:
            # Get AlertBuilder singleton
            alert_builder = get_alert_builder()
            
            # Build enriched alert with context
            enriched_alert = alert_builder.build_alert(
                metric_name=result.metric_name,
                current_value=result.current_value,
                expected_value=result.expected_value,
                anomaly_score=result.anomaly_score,
                severity=result.severity,
                timestamp=result.timestamp,
                detection_timestamp=result.timestamp,  # For latency tracking
                additional_labels={
                    "priority": metric_config.priority,
                    "metric_type": "anomaly"
                }
            )
            
            # Send enriched alert to Alertmanager
            # Note: AlertmanagerClient will be updated to accept full alert payload
            await self.alertmanager.send_alert(
                alert_name=enriched_alert["labels"]["alertname"],
                metric_name=result.metric_name,
                current_value=result.current_value,
                anomaly_score=result.anomaly_score,
                severity=result.severity,
                description=enriched_alert["annotations"]["description"],
                additional_labels=enriched_alert["labels"],
                enriched_payload=enriched_alert  # Pass full enriched alert
            )
            
            logger.info(
                f"Enriched alert sent: {result.metric_name} | "
                f"Severity: {result.severity} | "
                f"Deviation: {enriched_alert['annotations']['deviation_percent']} | "
                f"Fingerprint: {enriched_alert['labels']['fingerprint']}"
            )
            
        except Exception as e:
            logger.error(f"Error sending enriched alert for {result.metric_name}: {e}")
    
    async def check_all_metrics(self):
        """Check all enabled metrics for anomalies"""
        enabled_metrics = config_manager.get_enabled_metrics()
        
        if not enabled_metrics:
            logger.warning("No metrics enabled for detection")
            return
        
        logger.info(f"Checking {len(enabled_metrics)} metrics for anomalies...")
        
        # Update stats
        self.stats["total_checks"] += 1
        self.stats["last_check"] = datetime.now()
        
        # Check each metric
        for metric_config in enabled_metrics:
            self.stats["checks_by_metric"][metric_config.name] = \
                self.stats["checks_by_metric"].get(metric_config.name, 0) + 1
            
            result = await self.detect_metric_anomalies(metric_config)
            
            # Store in history
            if metric_config.name not in self.detection_history:
                self.detection_history[metric_config.name] = []
            
            self.detection_history[metric_config.name].append({
                "timestamp": datetime.now().isoformat(),
                "anomaly_detected": result is not None,
                "value": result.current_value if result else None
            })
            
            # Keep only last 100 checks per metric
            if len(self.detection_history[metric_config.name]) > 100:
                self.detection_history[metric_config.name] = \
                    self.detection_history[metric_config.name][-100:]
        
        # 🔥 UPDATE PROMETHEUS METRICS AFTER CYCLE
        try:
            from app.api import prom_active_anomalies, prom_models_trained, update_baseline_metrics
            
            # Update active anomalies count
            prom_active_anomalies.set(len(self.anomalies))
            
            # Update models trained metrics
            for model_name, model in self.ensemble.models.items():
                if model.trained:
                    prom_models_trained.labels(model=model_name).set(1)
                else:
                    prom_models_trained.labels(model=model_name).set(0)
            
            # Update baseline metrics every cycle
            update_baseline_metrics()
            
            logger.debug(f"Prometheus metrics updated: {len(self.anomalies)} anomalies, {len([m for m in self.ensemble.models.values() if m.trained])} models trained")
        except Exception as e:
            logger.error(f"Error updating Prometheus gauges: {e}")
    
    async def save_models(self):
        """Save trained models to disk"""
        if not self.config.persistence.enabled:
            return
        
        try:
            self.ensemble.save_models(
                self.model_dir,
                compression=self.config.persistence.compression
            )
            logger.info("Models saved successfully")
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def get_recent_anomalies(
        self,
        limit: int = 100,
        metric_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent anomalies"""
        anomalies = list(self.anomalies)
        
        if metric_name:
            anomalies = [
                a for a in anomalies
                if a.metric_name == metric_name
            ]
        
        return [a.to_dict() for a in anomalies[-limit:]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get detector statistics"""
        uptime = datetime.now() - self.stats["uptime_start"]
        
        return {
            **self.stats,
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_hours": uptime.total_seconds() / 3600,
            "anomaly_rate": (
                self.stats["total_anomalies"] / self.stats["total_checks"]
                if self.stats["total_checks"] > 0 else 0
            ),
            "models_loaded": {
                name: model.trained
                for name, model in self.ensemble.models.items()
            }
        }
    
    async def resolve_stale_anomalies(self, ttl_minutes: int = 30) -> int:
        """
        Resolve anomalies that haven't been re-detected in TTL period
        
        Args:
            ttl_minutes: Time-to-live in minutes for anomalies
            
        Returns:
            Number of anomalies resolved
        """
        from app.api import prom_resolved_anomalies
        
        now = datetime.now()
        cutoff_time = now - timedelta(minutes=ttl_minutes)
        resolved_count = 0
        
        for anomaly in self.anomalies:
            # Only process active anomalies
            if anomaly.status != "active":
                continue
            
            # Check if anomaly is older than TTL
            if anomaly.timestamp < cutoff_time:
                anomaly.status = "resolved"
                anomaly.resolved_at = now
                resolved_count += 1
                
                # Update metrics
                prom_resolved_anomalies.labels(
                    metric=anomaly.metric_name,
                    severity=anomaly.severity
                ).inc()
                
                logger.debug(
                    f"Anomaly resolved (TTL): {anomaly.metric_name} | "
                    f"Age: {(now - anomaly.timestamp).total_seconds() / 60:.1f}m | "
                    f"Severity: {anomaly.severity}"
                )
        
        return resolved_count
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.prometheus.close()
        await self.alertmanager.close()
        
        # Save models before exit
        await self.save_models()
