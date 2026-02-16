"""
Dynamic Baseline Manager
Manages time-aware baselines for anomaly detection

Version: 2.6.0
Features:
- Hourly and daily patterns
- Exponential Moving Average updates
- Percentile-based bands (p10-p90)
- Configurable refresh intervals
"""
import numpy as np
import json
import logging
import os
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from collections import defaultdict

from app.database import db

logger = logging.getLogger(__name__)


class BaselineStats:
    """Container for baseline statistical values"""
    
    def __init__(
        self,
        mean: float,
        std_dev: float,
        p10: float,
        p50: float,
        p90: float,
        min_val: float,
        max_val: float,
        sample_count: int,
        last_updated: datetime
    ):
        self.mean = mean
        self.std_dev = std_dev
        self.p10 = p10
        self.p50 = p50
        self.p90 = p90
        self.min_val = min_val
        self.max_val = max_val
        self.sample_count = sample_count
        self.last_updated = last_updated
    
    @property
    def lower_bound(self) -> float:
        """Conservative lower bound (p10)"""
        return self.p10
    
    @property
    def upper_bound(self) -> float:
        """Conservative upper bound (p90)"""
        return self.p90
    
    @property
    def expected_range(self) -> Tuple[float, float]:
        """Expected value range"""
        return (self.p10, self.p90)
    
    def is_anomalous(self, value: float, sensitivity: str = "medium") -> bool:
        """
        Check if value is anomalous based on sensitivity
        
        Args:
            value: Value to check
            sensitivity: "low", "medium", "high"
        
        Returns:
            True if value is outside expected range
        """
        # Adjust bounds based on sensitivity
        if sensitivity == "low":
            # Use mean ± 3*std (99.7% confidence)
            lower = self.mean - 3 * self.std_dev
            upper = self.mean + 3 * self.std_dev
        elif sensitivity == "high":
            # Use mean ± 1.5*std (~86% confidence)
            lower = self.mean - 1.5 * self.std_dev
            upper = self.mean + 1.5 * self.std_dev
        else:  # medium
            # Use mean ± 2*std (95% confidence)
            lower = self.mean - 2 * self.std_dev
            upper = self.mean + 2 * self.std_dev
        
        return value < lower or value > upper
    
    def deviation_percent(self, value: float) -> float:
        """Calculate percentage deviation from expected mean"""
        if self.mean == 0:
            return 0.0
        return ((value - self.mean) / abs(self.mean)) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "mean": self.mean,
            "std_dev": self.std_dev,
            "p10": self.p10,
            "p50": self.p50,
            "p90": self.p90,
            "min": self.min_val,
            "max": self.max_val,
            "sample_count": self.sample_count,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "expected_range": [self.p10, self.p90]
        }


class DynamicBaselineManager:
    """
    Manages dynamic baselines with temporal context
    
    Features:
    - Time-aware baselines (hour of day, day of week)
    - Exponential Moving Average for updates
    - Persistent storage via SQLite
    - Configurable refresh intervals
    """
    
    def __init__(
        self,
        alpha: float = 0.1,
        min_samples: int = 20,
        refresh_interval_hours: int = 1
    ):
        """
        Initialize baseline manager
        
        Args:
            alpha: EMA smoothing factor (0-1), lower = slower adaptation
            min_samples: Minimum samples required for baseline
            refresh_interval_hours: Hours between baseline recalculations
        """
        self.alpha = alpha
        self.min_samples = min_samples
        self.refresh_interval = timedelta(hours=refresh_interval_hours)
        
        # In-memory cache: {metric_key: BaselineStats}
        self._cache: Dict[str, BaselineStats] = {}
        
        # Load configuration from env
        self._load_config()
        
        logger.info(
            f"DynamicBaselineManager initialized "
            f"(alpha={self.alpha}, min_samples={self.min_samples}, "
            f"refresh_interval={refresh_interval_hours}h)"
        )
    
    def _load_config(self):
        """Load configuration from environment variables"""
        # Exponential Moving Average alpha
        if alpha_env := os.getenv("BASELINE_EMA_ALPHA"):
            try:
                self.alpha = float(alpha_env)
                logger.info(f"Loaded BASELINE_EMA_ALPHA={self.alpha}")
            except ValueError:
                logger.warning(f"Invalid BASELINE_EMA_ALPHA: {alpha_env}, using default")
        
        # Minimum samples
        if min_env := os.getenv("BASELINE_MIN_SAMPLES"):
            try:
                self.min_samples = int(min_env)
                logger.info(f"Loaded BASELINE_MIN_SAMPLES={self.min_samples}")
            except ValueError:
                logger.warning(f"Invalid BASELINE_MIN_SAMPLES: {min_env}, using default")
        
        # Refresh interval
        if interval_env := os.getenv("BASELINE_REFRESH_INTERVAL"):
            try:
                # Parse interval string (e.g., "1h", "30m", "2h30m")
                hours = self._parse_interval(interval_env)
                self.refresh_interval = timedelta(hours=hours)
                logger.info(f"Loaded BASELINE_REFRESH_INTERVAL={interval_env} ({hours}h)")
            except ValueError:
                logger.warning(f"Invalid BASELINE_REFRESH_INTERVAL: {interval_env}, using default")
    
    def _parse_interval(self, interval_str: str) -> float:
        """Parse interval string to hours"""
        # Simple parser: "1h", "30m", "1h30m"
        hours = 0.0
        
        if 'h' in interval_str:
            h_part = interval_str.split('h')[0]
            hours += float(h_part)
            interval_str = interval_str.split('h')[1]
        
        if 'm' in interval_str:
            m_part = interval_str.rstrip('m')
            if m_part:
                hours += float(m_part) / 60
        
        return hours
    
    def _make_cache_key(
        self,
        metric_name: str,
        metric_labels: Dict[str, str],
        hour: int,
        day: int
    ) -> str:
        """Generate cache key"""
        labels_str = json.dumps(metric_labels, sort_keys=True)
        return f"{metric_name}|{labels_str}|{hour}|{day}"
    
    def _make_labels_str(self, metric_labels: Dict[str, str]) -> str:
        """Convert labels dict to sorted JSON string"""
        return json.dumps(metric_labels, sort_keys=True)
    
    def get_expected_value(
        self,
        metric_name: str,
        metric_labels: Dict[str, str],
        timestamp: Optional[datetime] = None
    ) -> Optional[BaselineStats]:
        """
        Get expected baseline for metric at given time
        
        Args:
            metric_name: Metric name
            metric_labels: Metric labels (e.g., {"service": "api", "host": "prod-1"})
            timestamp: Target timestamp (defaults to now)
        
        Returns:
            BaselineStats or None if not found
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        hour = timestamp.hour
        day = timestamp.weekday()  # 0=Monday, 6=Sunday
        
        # Check cache first
        cache_key = self._make_cache_key(metric_name, metric_labels, hour, day)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            # Check if cache is fresh
            if datetime.now() - cached.last_updated < self.refresh_interval:
                return cached
        
        # Load from database
        labels_str = self._make_labels_str(metric_labels)
        baseline_data = db.get_baseline(metric_name, labels_str, hour, day)
        
        if baseline_data:
            baseline = BaselineStats(
                mean=baseline_data['mean_value'],
                std_dev=baseline_data['std_dev'],
                p10=baseline_data['p10'],
                p50=baseline_data['p50'],
                p90=baseline_data['p90'],
                min_val=baseline_data['min_value'],
                max_val=baseline_data['max_value'],
                sample_count=baseline_data['sample_count'],
                last_updated=datetime.fromisoformat(baseline_data['last_updated'])
            )
            
            # Update cache
            self._cache[cache_key] = baseline
            return baseline
        
        return None
    
    def update_baseline(
        self,
        metric_name: str,
        metric_labels: Dict[str, str],
        values,  # Accept list or np.ndarray
        timestamp: Optional[datetime] = None
    ) -> BaselineStats:
        """
        Update baseline with new data
        
        Args:
            metric_name: Metric name
            metric_labels: Metric labels
            values: Array or list of recent metric values
            timestamp: Timestamp for temporal context
        
        Returns:
            Updated BaselineStats
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        hour = timestamp.hour
        day = timestamp.weekday()
        
        # Ensure values is a flat numpy array
        if not isinstance(values, np.ndarray):
            values = np.array(values, dtype=np.float64)
        values = values.flatten()
        
        # Calculate statistics from new data
        logger.info(f"🔍 BASELINE_DEBUG {metric_name}: len(values)={len(values)}, min_samples={self.min_samples}")
        
        if len(values) < self.min_samples:
            logger.warning(
                f"Insufficient samples for {metric_name}: "
                f"{len(values)}/{self.min_samples}"
            )
            # Return existing baseline if available
            existing = self.get_expected_value(metric_name, metric_labels, timestamp)
            if existing:
                logger.info(f"🔍 BASELINE_DEBUG {metric_name}: Returning existing baseline (early exit)")
                return existing
            # Otherwise, create initial baseline with available data
            logger.info(f"🔍 BASELINE_DEBUG {metric_name}: No existing baseline, continuing with {len(values)} samples")
            pass
        
        # Calculate new statistics
        logger.info(f"🔍 BASELINE_DEBUG {metric_name}: Calculating statistics...")
        new_mean = float(np.mean(values))
        new_std = float(np.std(values))
        new_p10 = float(np.percentile(values, 10))
        new_p50 = float(np.percentile(values, 50))
        new_p90 = float(np.percentile(values, 90))
        new_min = float(np.min(values))
        new_max = float(np.max(values))
        sample_count = len(values)
        
        # Get existing baseline
        existing = self.get_expected_value(metric_name, metric_labels, timestamp)
        logger.info(f"🔍 BASELINE_DEBUG {metric_name}: existing={existing is not None}, mean={new_mean:.2f}, std={new_std:.2f}")
        
        if existing:
            # Apply Exponential Moving Average
            logger.info(f"🔍 BASELINE_DEBUG {metric_name}: Applying EMA (alpha={self.alpha})")
            mean = self.alpha * new_mean + (1 - self.alpha) * existing.mean
            std_dev = self.alpha * new_std + (1 - self.alpha) * existing.std_dev
            p10 = self.alpha * new_p10 + (1 - self.alpha) * existing.p10
            p50 = self.alpha * new_p50 + (1 - self.alpha) * existing.p50
            p90 = self.alpha * new_p90 + (1 - self.alpha) * existing.p90
            min_val = min(new_min, existing.min_val)
            max_val = max(new_max, existing.max_val)
            total_samples = existing.sample_count + sample_count
        else:
            # First baseline for this context
            logger.info(f"🔍 BASELINE_DEBUG {metric_name}: First baseline for hour={hour}, day={day}")
            mean = new_mean
            std_dev = new_std
            p10 = new_p10
            p50 = new_p50
            p90 = new_p90
            min_val = new_min
            max_val = new_max
            total_samples = sample_count
        
        # Save to database
        labels_str = self._make_labels_str(metric_labels)
        logger.info(f"🔍 BASELINE_DEBUG {metric_name}: About to save baseline (hour={hour}, day={day}, samples={total_samples})")
        try:
            db.upsert_baseline(
                metric_name=metric_name,
                metric_labels=labels_str,
                hour_of_day=hour,
                day_of_week=day,
                mean_value=mean,
                std_dev=std_dev,
                p10=p10,
                p50=p50,
                p90=p90,
                min_value=min_val,
                max_value=max_val,
                sample_count=total_samples
            )
            logger.info(f"✅ BASELINE_DEBUG {metric_name}: Baseline saved successfully!")
        except Exception as e:
            logger.error(f"❌ BASELINE_DEBUG {metric_name}: Failed to save baseline: {e}")
            raise
        
        # Create and cache new baseline
        baseline = BaselineStats(
            mean=mean,
            std_dev=std_dev,
            p10=p10,
            p50=p50,
            p90=p90,
            min_val=min_val,
            max_val=max_val,
            sample_count=total_samples,
            last_updated=timestamp
        )
        
        cache_key = self._make_cache_key(metric_name, metric_labels, hour, day)
        self._cache[cache_key] = baseline
        
        logger.debug(
            f"Updated baseline for {metric_name} "
            f"(hour={hour}, day={day}, mean={mean:.2f}, samples={total_samples})"
        )
        
        return baseline
    
    def recalculate_all_baselines(
        self,
        metric_name: str,
        metric_labels: Dict[str, str],
        historical_data: List[Tuple[datetime, float]]
    ) -> int:
        """
        Recalculate all time-context baselines from historical data
        
        Args:
            metric_name: Metric name
            metric_labels: Metric labels
            historical_data: List of (timestamp, value) tuples
        
        Returns:
            Number of baselines updated
        """
        if len(historical_data) < self.min_samples:
            logger.warning(
                f"Insufficient historical data for {metric_name}: "
                f"{len(historical_data)}/{self.min_samples}"
            )
            return 0
        
        # Group data by (hour, day_of_week)
        grouped: Dict[Tuple[int, int], List[float]] = defaultdict(list)
        
        for timestamp, value in historical_data:
            hour = timestamp.hour
            day = timestamp.weekday()
            grouped[(hour, day)].append(value)
        
        # Update each group
        updated_count = 0
        for (hour, day), values in grouped.items():
            if len(values) >= self.min_samples:
                # Create fake timestamp with correct hour/day
                fake_timestamp = datetime.now().replace(
                    hour=hour,
                    minute=0,
                    second=0,
                    microsecond=0
                )
                # Adjust to correct day of week
                days_ahead = day - fake_timestamp.weekday()
                if days_ahead < 0:
                    days_ahead += 7
                fake_timestamp += timedelta(days=days_ahead)
                
                self.update_baseline(
                    metric_name,
                    metric_labels,
                    np.array(values),
                    fake_timestamp
                )
                updated_count += 1
        
        logger.info(
            f"Recalculated {updated_count} baselines for {metric_name} "
            f"from {len(historical_data)} samples"
        )
        
        return updated_count
    
    def get_all_metrics(self) -> List[str]:
        """Get list of all metrics with baselines"""
        baselines = db.get_all_baselines()
        unique_metrics = set(b['metric_name'] for b in baselines)
        return sorted(unique_metrics)
    
    def get_metric_baselines(self, metric_name: str) -> List[Dict[str, Any]]:
        """Get all baselines for a specific metric"""
        baselines = db.get_all_baselines(metric_name)
        return [
            {
                "metric_name": b['metric_name'],
                "metric_labels": json.loads(b['metric_labels']),
                "hour_of_day": b['hour_of_day'],
                "day_of_week": b['day_of_week'],
                "mean": b['mean_value'],
                "std_dev": b['std_dev'],
                "p10": b['p10'],
                "p50": b['p50'],
                "p90": b['p90'],
                "sample_count": b['sample_count'],
                "last_updated": b['last_updated']
            }
            for b in baselines
        ]
    
    def clear_cache(self):
        """Clear in-memory cache"""
        self._cache.clear()
        logger.info("Baseline cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get baseline manager statistics"""
        return {
            "cached_baselines": len(self._cache),
            "alpha": self.alpha,
            "min_samples": self.min_samples,
            "refresh_interval_hours": self.refresh_interval.total_seconds() / 3600,
            **db.get_stats()
        }


# Global baseline manager instance
baseline_manager = DynamicBaselineManager(
    alpha=float(os.getenv("BASELINE_EMA_ALPHA", "0.1")),
    min_samples=int(os.getenv("BASELINE_MIN_SAMPLES", "20")),
    refresh_interval_hours=int(os.getenv("BASELINE_REFRESH_INTERVAL", "1").rstrip('h'))
)
