"""
Alert Builder - Rhinometric AI Anomaly Detection v2.2

Purpose:
    Enrich anomaly detections with context and format them for Alertmanager.
    
Key features:
    - Calculate deviation percentage from baseline
    - Generate consistent fingerprint for deduplication
    - Add dashboard and runbook links dynamically
    - Format for Alertmanager JSON API
    - Track metrics (built, dropped, latency)

Author: Rhinometric Team
Last updated: 2025-11-19
"""

import hashlib
import os
import yaml
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from prometheus_client import Counter, Histogram

# Prometheus metrics for alert system health
ALERTS_BUILT_TOTAL = Counter(
    'rhinometric_alerts_built_total',
    'Total number of alerts built by AlertBuilder',
    ['channel', 'severity', 'status']
)

ALERTS_DROPPED_TOTAL = Counter(
    'rhinometric_alerts_dropped_total',
    'Total number of alerts dropped',
    ['reason']
)

ALERT_DELIVERY_LATENCY = Histogram(
    'rhinometric_alert_delivery_latency_seconds',
    'Time from anomaly detection to alert delivery',
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0]
)


class AlertBuilder:
    """
    Builds enriched alerts from anomaly detections.
    
    Responsibilities:
        - Load alert mappings from YAML config
        - Calculate deviation percentage
        - Generate fingerprint for deduplication
        - Format alerts for Alertmanager
        - Track internal metrics
    """
    
    def __init__(self, mappings_file: str = "alert_mappings.yaml"):
        """
        Initialize AlertBuilder with mappings configuration.
        
        Args:
            mappings_file: Path to alert_mappings.yaml
        """
        self.mappings_file = Path(__file__).parent.parent / mappings_file
        self.mappings = self._load_mappings()
        
        # Load base URLs from config or env vars
        # Priority: ENV VAR > YAML config > Default
        grafana_from_yaml = self.mappings.get('base', {}).get('grafana_url', 'http://grafana:3000')
        docs_from_yaml = self.mappings.get('base', {}).get('docs_url', 'https://docs.rhinometric.com')
        
        self.grafana_url = os.getenv('GRAFANA_PUBLIC_URL') or os.getenv('GRAFANA_URL') or self._parse_env_var(grafana_from_yaml)
        self.docs_url = os.getenv('DOCS_BASE_URL') or self._parse_env_var(docs_from_yaml)
        
        # Feature flags
        self.features = self.mappings.get('features', {})
        
        print(f"[AlertBuilder] Initialized with {len(self.mappings.get('alerts', {}))} metric mappings")
        print(f"[AlertBuilder] Grafana URL: {self.grafana_url}")
        print(f"[AlertBuilder] Features: slack={self.features.get('enable_slack')}, "
              f"email={self.features.get('enable_email')}, "
              f"grouping={self.features.get('enable_grouping')}")
    
    def _load_mappings(self) -> Dict[str, Any]:
        """Load alert mappings from YAML file."""
        try:
            with open(self.mappings_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"[AlertBuilder] WARNING: {self.mappings_file} not found, using defaults")
            return {}
        except Exception as e:
            print(f"[AlertBuilder] ERROR loading mappings: {e}")
            return {}
    
    def _parse_env_var(self, value: str) -> str:
        """
        Parse environment variable syntax from YAML.
        Supports: ${VAR_NAME:default_value}
        
        Example: "${GRAFANA_URL:http://localhost:3000}" → os.getenv('GRAFANA_URL') or 'http://localhost:3000'
        """
        if not isinstance(value, str) or not value.startswith('${'):
            return value
        
        # Extract ${VAR_NAME:default}
        try:
            content = value[2:-1]  # Remove ${ and }
            if ':' in content:
                var_name, default = content.split(':', 1)
                return os.getenv(var_name, default)
            else:
                return os.getenv(content, value)
        except Exception as e:
            print(f"[AlertBuilder] WARNING: Failed to parse env var '{value}': {e}")
            return value
    
    def build_alert(
        self,
        metric_name: str,
        current_value: float,
        expected_value: float,
        anomaly_score: float,
        severity: str,
        timestamp: datetime,
        detection_timestamp: Optional[datetime] = None,
        additional_labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Build enriched alert from anomaly detection.
        
        Args:
            metric_name: Name of the metric (e.g., 'http_latency_p99')
            current_value: Current metric value
            expected_value: Baseline/expected value
            anomaly_score: ML model score
            severity: 'critical', 'high', 'medium', 'low'
            timestamp: When anomaly was detected
            detection_timestamp: Optional timestamp of detection start (for latency calculation)
            additional_labels: Optional extra labels (host, container, etc.)
        
        Returns:
            Alert payload formatted for Alertmanager JSON API
        """
        start_time = datetime.now()
        
        try:
            # Get metric mapping (or use default)
            mapping = self.mappings.get('alerts', {}).get(
                metric_name,
                self.mappings.get('default', {})
            )
            
            # Calculate deviation percentage
            deviation_percent = self._calculate_deviation(current_value, expected_value)
            
            # Generate fingerprint for deduplication
            fingerprint = self._generate_fingerprint(metric_name, severity, additional_labels)
            
            # Build URLs with variable substitution
            dashboard_url = self._build_url(
                mapping.get('dashboard_url', ''),
                metric_name,
                additional_labels
            )
            runbook_url = self._build_url(
                mapping.get('runbook_url', ''),
                metric_name,
                additional_labels
            )
            
            # Determine service from mapping or labels
            service = mapping.get('service', 'unknown')
            if additional_labels and 'service' in additional_labels:
                service = additional_labels['service']
            
            # Build alert payload (Alertmanager format)
            alert = {
                "labels": {
                    "alertname": f"AnomalyDetected_{metric_name}",
                    "severity": severity,
                    "metric": metric_name,
                    "service": service,
                    "team": "platform",
                    "component": "ai-anomaly",
                    "fingerprint": fingerprint
                },
                "annotations": {
                    "summary": self._build_summary(metric_name, severity),
                    "description": self._build_description(
                        metric_name,
                        current_value,
                        expected_value,
                        deviation_percent
                    ),
                    "current_value": self._format_value(current_value, metric_name),
                    "baseline_value": self._format_value(expected_value, metric_name),
                    "deviation_percent": f"{deviation_percent:+.1f}%",
                    "anomaly_score": f"{anomaly_score:.3f}",
                    "confidence": self._calculate_confidence(anomaly_score),
                    "dashboard_url": dashboard_url,
                    "runbook_url": runbook_url,
                    "detected_at": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
                },
                "startsAt": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "endsAt": "0001-01-01T00:00:00Z",  # Active alert (no end time)
                "generatorURL": f"https://anomaly.rhinometric.com/anomalies?metric={metric_name}&from=now-6h&to=now"
            }
            
            # Add additional labels if provided
            if additional_labels:
                alert["labels"].update(additional_labels)
            
            # Track metrics
            ALERTS_BUILT_TOTAL.labels(
                channel="alertmanager",
                severity=severity,
                status="success"
            ).inc()
            
            # Calculate and track delivery latency
            if detection_timestamp:
                latency = (datetime.now() - detection_timestamp).total_seconds()
                ALERT_DELIVERY_LATENCY.observe(latency)
            
            build_duration = (datetime.now() - start_time).total_seconds()
            print(f"[AlertBuilder] Built alert for {metric_name} ({severity}) in {build_duration:.3f}s")
            print(f"[AlertBuilder] URLs → Dashboard: {dashboard_url} | Runbook: {runbook_url} | Generator: {alert['generatorURL']}")
            
            return alert
            
        except Exception as e:
            print(f"[AlertBuilder] ERROR building alert for {metric_name}: {e}")
            ALERTS_BUILT_TOTAL.labels(
                channel="alertmanager",
                severity=severity,
                status="error"
            ).inc()
            ALERTS_DROPPED_TOTAL.labels(reason="build_error").inc()
            raise
    
    def _calculate_deviation(self, current: float, expected: float) -> float:
        """
        Calculate percentage deviation from baseline.
        
        Args:
            current: Current value
            expected: Expected/baseline value
        
        Returns:
            Deviation percentage (e.g., +350.0 for 350% above baseline)
        """
        if expected == 0:
            # Avoid division by zero
            return 0.0 if current == 0 else float('inf')
        
        deviation = ((current - expected) / abs(expected)) * 100
        return deviation
    
    def _generate_fingerprint(
        self,
        metric_name: str,
        severity: str,
        additional_labels: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate consistent fingerprint for alert deduplication.
        
        Fingerprint = hash(metric + service + severity)
        
        Args:
            metric_name: Metric name
            severity: Alert severity
            additional_labels: Optional labels (for extracting service)
        
        Returns:
            8-character hex fingerprint
        """
        # Build fingerprint components
        components = [metric_name, severity]
        
        # Add service if available
        if additional_labels and 'service' in additional_labels:
            components.append(additional_labels['service'])
        
        # Create hash
        fingerprint_str = "|".join(components)
        hash_obj = hashlib.md5(fingerprint_str.encode())
        fingerprint = hash_obj.hexdigest()[:8]
        
        return fingerprint
    
    def _build_url(
        self,
        template: str,
        metric_name: str,
        additional_labels: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Build URL with variable substitution.
        
        Variables:
            {grafana_url} - Base Grafana URL
            {docs_url} - Base docs URL
            {metric} - Metric name
            {service} - Service name
            {host} - Host name
            {container} - Container name
        
        Args:
            template: URL template from mappings
            metric_name: Metric name
            additional_labels: Optional labels
        
        Returns:
            Fully resolved URL
        """
        # Parse template if it contains env var syntax
        template = self._parse_env_var(template)
        
        # Replace placeholders with actual values
        url = template.replace('{grafana_url}', self.grafana_url)
        url = url.replace('{docs_url}', self.docs_url)
        url = url.replace('{metric}', metric_name)
        
        if additional_labels:
            for key, value in additional_labels.items():
                url = url.replace(f'{{{key}}}', value)
        
        return url
    
    def _build_summary(self, metric_name: str, severity: str) -> str:
        """Build alert summary text."""
        emoji_map = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🔵'
        }
        emoji = emoji_map.get(severity, '⚪')
        
        # Humanize metric name
        human_name = metric_name.replace('_', ' ').title()
        
        return f"{emoji} {severity.upper()} - {human_name} Anomaly Detected"
    
    def _build_description(
        self,
        metric_name: str,
        current: float,
        expected: float,
        deviation: float
    ) -> str:
        """Build alert description text."""
        human_name = metric_name.replace('_', ' ').title()
        
        direction = "above" if current > expected else "below"
        
        return (
            f"{human_name} is {abs(deviation):.1f}% {direction} baseline "
            f"({self._format_value(current, metric_name)} vs "
            f"{self._format_value(expected, metric_name)} expected)"
        )
    
    def _format_value(self, value: float, metric_name: str) -> str:
        """
        Format metric value with appropriate unit.
        
        Args:
            value: Raw value
            metric_name: Metric name (to infer unit)
        
        Returns:
            Formatted string (e.g., "0.45s", "85.3%", "1.2GB")
        """
        # Time metrics (latency, duration)
        if 'latency' in metric_name or 'duration' in metric_name:
            if value < 1:
                return f"{value*1000:.0f}ms"
            return f"{value:.2f}s"
        
        # Rate metrics (requests/sec, transactions/sec)
        if 'rate' in metric_name or 'requests' in metric_name:
            return f"{value:.1f}/s"
        
        # Byte metrics (memory, disk) - Check if value is in bytes (large numbers)
        if ('memory' in metric_name or 'disk' in metric_name) and value > 1000:
            # If value > 1KB, likely bytes not percentage
            if value > 1e9:
                return f"{value/1e9:.2f}GB"
            elif value > 1e6:
                return f"{value/1e6:.2f}MB"
            elif value > 1e3:
                return f"{value/1e3:.2f}KB"
            return f"{value:.0f}B"
        
        # Percentage metrics (CPU, memory usage %, hit ratio)
        if 'usage' in metric_name or 'ratio' in metric_name or 'hit' in metric_name:
            # Only if value looks like percentage (0-100 range)
            if value <= 100:
                return f"{value:.1f}%"
        
        # Byte metrics fallthrough (if not caught above)
        if 'memory' in metric_name or 'disk' in metric_name:
            if value > 1e9:
                return f"{value/1e9:.2f}GB"
            elif value > 1e6:
                return f"{value/1e6:.2f}MB"
            elif value > 1e3:
                return f"{value/1e3:.2f}KB"
            return f"{value:.0f}B"
        
        # Count metrics (connections, errors)
        if 'count' in metric_name or 'connections' in metric_name:
            return f"{int(value)}"
        
        # Default: 2 decimal places
        return f"{value:.2f}"
    
    def _calculate_confidence(self, anomaly_score: float) -> str:
        """
        Calculate confidence level from anomaly score.
        
        Args:
            anomaly_score: ML model score (typically negative, more negative = more anomalous)
        
        Returns:
            Confidence string (e.g., "95%", "80%")
        """
        # IsolationForest scores are typically in range [-1, 1]
        # More negative = more anomalous = higher confidence
        
        if anomaly_score < -1.5:
            return "99%"
        elif anomaly_score < -1.0:
            return "95%"
        elif anomaly_score < -0.7:
            return "90%"
        elif anomaly_score < -0.5:
            return "85%"
        else:
            return "80%"
    
    def should_send_alert(self, severity: str, fingerprint: str) -> bool:
        """
        Determine if alert should be sent based on throttling rules.
        
        Args:
            severity: Alert severity
            fingerprint: Alert fingerprint
        
        Returns:
            True if alert should be sent, False if throttled
        """
        # TODO: Implement in-memory cache with TTL for throttling
        # For now, always send (Alertmanager handles grouping)
        
        if not self.features.get('enable_throttling', True):
            return True
        
        # Future: Check cache for recent alerts with same fingerprint
        # If found within throttle window, return False
        
        return True
    
    def get_routing_config(self, severity: str) -> Dict[str, Any]:
        """
        Get Alertmanager routing configuration for severity.
        
        Args:
            severity: Alert severity
        
        Returns:
            Routing config dict
        """
        routing = self.mappings.get('routing', {})
        
        if severity == 'critical':
            return routing.get('critical', {})
        elif severity == 'high':
            return routing.get('high', {})
        else:
            return routing.get('medium_low', {})


# Singleton instance
_alert_builder = None


def get_alert_builder() -> AlertBuilder:
    """Get or create singleton AlertBuilder instance."""
    global _alert_builder
    if _alert_builder is None:
        _alert_builder = AlertBuilder()
    return _alert_builder
