"""
Background Detection Service
Runs periodic anomaly detection checks and baseline recalculation
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta

from app.config import config_manager
from app.detector import AnomalyDetector
from app.baseline_manager import baseline_manager
from app.prom_client import PrometheusClient

logger = logging.getLogger(__name__)


class DetectionService:
    """Background service for periodic anomaly detection"""
    
    def __init__(self, detector: AnomalyDetector):
        self.detector = detector
        self.config = config_manager.config.detection
        self.persistence_config = config_manager.config.persistence
        self.running = False
        self.task = None
        self.last_model_save: datetime = datetime.now()
        self.last_baseline_update: datetime = datetime.now()
        
        # Baseline refresh configuration
        self.baseline_refresh_interval = self._parse_baseline_interval(
            os.getenv("BASELINE_REFRESH_INTERVAL", "1h")
        )
        
        # Stats
        self.baseline_update_count = 0
    
    def _parse_baseline_interval(self, interval_str: str) -> timedelta:
        """Parse baseline refresh interval from env var"""
        try:
            # Parse "1h", "30m", "1h30m"
            hours = 0.0
            
            if 'h' in interval_str:
                h_part = interval_str.split('h')[0]
                hours += float(h_part)
                interval_str = interval_str.split('h')[1] if 'h' in interval_str else ""
            
            if 'm' in interval_str:
                m_part = interval_str.rstrip('m')
                if m_part:
                    hours += float(m_part) / 60
            
            return timedelta(hours=hours)
        except Exception as e:
            logger.warning(f"Invalid BASELINE_REFRESH_INTERVAL: {interval_str}, using 1h default")
            return timedelta(hours=1)
    
    async def start(self):
        """Start background detection service"""
        if self.running:
            logger.warning("Detection service already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._detection_loop())
        logger.info("✓ Background detection service started")
        logger.info(f"  Check interval: {self.config.check_interval}s")
        logger.info(f"  Baseline refresh: {self.baseline_refresh_interval.total_seconds() / 3600:.1f}h")
        
        # Start model persistence task
        if self.persistence_config.enabled:
            asyncio.create_task(self._model_persistence_loop())
        
        # Start baseline recalculation task
        asyncio.create_task(self._baseline_refresh_loop())
    
    async def stop(self):
        """Stop background detection service"""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("✓ Background detection service stopped")
    
    async def _detection_loop(self):
        """Main detection loop"""
        logger.info("Starting detection loop...")
        
        # Initial delay to allow services to stabilize
        await asyncio.sleep(10)
        
        while self.running:
            try:
                logger.info("=" * 50)
                logger.info(f"Detection cycle started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Run detection
                start_time = datetime.now()
                await self.detector.check_all_metrics()
                duration = (datetime.now() - start_time).total_seconds()
                
                # UPDATE EXPORT METRICS AFTER DETECTION (CORE FIX)
                try:
                    from app.api import update_anomaly_export_metrics
                    update_anomaly_export_metrics()
                    logger.debug("Anomaly export metrics updated after detection cycle")
                except Exception as e:
                    logger.error(f"Error updating anomaly export metrics: {e}")
                
                # Resolve stale anomalies (TTL-based)
                resolved_count = await self.detector.resolve_stale_anomalies()
                if resolved_count > 0:
                    logger.info(f"Resolved {resolved_count} stale anomalies")
                
                logger.info(f"Detection cycle completed in {duration:.2f}s")
                logger.info(f"Next check in {self.config.check_interval}s")
                logger.info("=" * 50)
                
                # Wait for next cycle
                await asyncio.sleep(self.config.check_interval)
            
            except asyncio.CancelledError:
                logger.info("Detection loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in detection loop: {e}", exc_info=True)
                # Continue after error with exponential backoff
                await asyncio.sleep(60)
    
    async def _model_persistence_loop(self):
        """Periodic model saving"""
        while self.running:
            try:
                await asyncio.sleep(self.persistence_config.save_interval)
                
                if self.running:
                    logger.info("Saving models (periodic)...")
                    await self.detector.save_models()
                    self.last_model_save = datetime.now()
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in model persistence loop: {e}")
    
    async def _baseline_refresh_loop(self):
        """Periodic baseline recalculation"""
        logger.info(f"Baseline refresh loop starting (interval: {self.baseline_refresh_interval})")
        
        # Initial delay
        await asyncio.sleep(60)
        
        while self.running:
            try:
                interval_seconds = self.baseline_refresh_interval.total_seconds()
                await asyncio.sleep(interval_seconds)
                
                if not self.running:
                    break
                
                logger.info("=" * 50)
                logger.info("Baseline refresh cycle started")
                start_time = datetime.now()
                
                # Get all enabled metrics
                enabled_metrics = config_manager.get_enabled_metrics()
                
                # Create temporary Prometheus client for historical data
                prometheus = PrometheusClient(config_manager.config.prometheus)
                
                updated_count = 0
                for metric_config in enabled_metrics:
                    try:
                        # Fetch extended historical data for baseline
                        values = await prometheus.fetch_metric_values(
                            metric_config.query,
                            hours=self.config.lookback_hours
                        )
                        
                        if len(values) >= baseline_manager.min_samples:
                            # Update baseline
                            metric_labels = {"metric": metric_config.name}
                            baseline_manager.update_baseline(
                                metric_name=metric_config.name,
                                metric_labels=metric_labels,
                                values=values
                            )
                            updated_count += 1
                        else:
                            logger.debug(
                                f"Skipping baseline update for {metric_config.name}: "
                                f"insufficient data ({len(values)} points)"
                            )
                    
                    except Exception as e:
                        logger.error(f"Error updating baseline for {metric_config.name}: {e}")
                
                await prometheus.close()
                
                duration = (datetime.now() - start_time).total_seconds()
                self.last_baseline_update = datetime.now()
                self.baseline_update_count += updated_count
                
                logger.info(f"Baseline refresh completed in {duration:.2f}s")
                logger.info(f"Updated {updated_count}/{len(enabled_metrics)} baselines")
                logger.info(f"Total baseline updates: {self.baseline_update_count}")
                logger.info(f"Next baseline refresh in {interval_seconds / 3600:.1f}h")
                logger.info("=" * 50)
            
            except asyncio.CancelledError:
                logger.info("Baseline refresh loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in baseline refresh loop: {e}", exc_info=True)
                # Continue after error
                await asyncio.sleep(300)  # 5 min backoff
