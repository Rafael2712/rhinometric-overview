"""
Tests for Alert Builder
Validates enriched alert generation, fingerprinting, and URL mapping
"""

import pytest
from datetime import datetime
from pathlib import Path
import yaml

# Adjust import path if needed
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.alert_builder import AlertBuilder, get_alert_builder


class TestAlertBuilder:
    """Test suite for AlertBuilder"""
    
    @pytest.fixture
    def alert_builder(self):
        """Create AlertBuilder instance"""
        return AlertBuilder()
    
    @pytest.fixture
    def sample_anomaly(self):
        """Sample anomaly data"""
        return {
            "metric_name": "http_latency_p99",
            "current_value": 0.85,
            "expected_value": 0.20,
            "anomaly_score": -1.456,
            "severity": "critical",
            "timestamp": datetime(2025, 11, 19, 16, 45, 30)
        }
    
    def test_alert_builder_initialization(self, alert_builder):
        """Test AlertBuilder loads mappings correctly"""
        assert alert_builder.mappings is not None
        assert "alerts" in alert_builder.mappings
        assert "base" in alert_builder.mappings
        assert "features" in alert_builder.mappings
    
    def test_build_alert_structure(self, alert_builder, sample_anomaly):
        """Test alert has correct structure"""
        alert = alert_builder.build_alert(**sample_anomaly)
        
        # Verify top-level keys
        assert "labels" in alert
        assert "annotations" in alert
        assert "startsAt" in alert
        assert "endsAt" in alert
        assert "generatorURL" in alert
        
        # Verify labels
        assert alert["labels"]["alertname"] == "AnomalyDetected_http_latency_p99"
        assert alert["labels"]["severity"] == "critical"
        assert alert["labels"]["metric"] == "http_latency_p99"
        assert "fingerprint" in alert["labels"]
        
        # Verify annotations
        assert "summary" in alert["annotations"]
        assert "description" in alert["annotations"]
        assert "current_value" in alert["annotations"]
        assert "baseline_value" in alert["annotations"]
        assert "deviation_percent" in alert["annotations"]
        assert "anomaly_score" in alert["annotations"]
        assert "confidence" in alert["annotations"]
        assert "dashboard_url" in alert["annotations"]
        assert "runbook_url" in alert["annotations"]
    
    def test_deviation_calculation(self, alert_builder, sample_anomaly):
        """Test deviation percentage calculation"""
        alert = alert_builder.build_alert(**sample_anomaly)
        
        # Expected: (0.85 - 0.20) / 0.20 * 100 = +325%
        deviation = alert["annotations"]["deviation_percent"]
        assert "+325" in deviation or "+325.0" in deviation
    
    def test_fingerprint_generation(self, alert_builder):
        """Test fingerprint is consistent"""
        data = {
            "metric_name": "http_latency_p99",
            "current_value": 0.85,
            "expected_value": 0.20,
            "anomaly_score": -1.456,
            "severity": "critical",
            "timestamp": datetime.now()
        }
        
        # Generate fingerprint twice with same data
        alert1 = alert_builder.build_alert(**data)
        alert2 = alert_builder.build_alert(**data)
        
        # Should be identical
        assert alert1["labels"]["fingerprint"] == alert2["labels"]["fingerprint"]
        
        # Should be 8 characters (MD5 truncated)
        assert len(alert1["labels"]["fingerprint"]) == 8
    
    def test_fingerprint_uniqueness(self, alert_builder):
        """Test different anomalies get different fingerprints"""
        base_data = {
            "current_value": 0.85,
            "expected_value": 0.20,
            "anomaly_score": -1.456,
            "timestamp": datetime.now()
        }
        
        # Same metric, different severity
        alert1 = alert_builder.build_alert(
            metric_name="http_latency_p99",
            severity="critical",
            **base_data
        )
        alert2 = alert_builder.build_alert(
            metric_name="http_latency_p99",
            severity="high",
            **base_data
        )
        
        # Different metric, same severity
        alert3 = alert_builder.build_alert(
            metric_name="node_cpu_usage",
            severity="critical",
            **base_data
        )
        
        # All should have different fingerprints
        fingerprints = [
            alert1["labels"]["fingerprint"],
            alert2["labels"]["fingerprint"],
            alert3["labels"]["fingerprint"]
        ]
        assert len(fingerprints) == len(set(fingerprints))
    
    def test_url_generation(self, alert_builder, sample_anomaly):
        """Test dashboard and runbook URLs are generated"""
        alert = alert_builder.build_alert(**sample_anomaly)
        
        dashboard_url = alert["annotations"]["dashboard_url"]
        runbook_url = alert["annotations"]["runbook_url"]
        
        # Should contain base URLs
        assert "grafana" in dashboard_url.lower()
        assert "docs" in runbook_url.lower() or "rhinometric.com" in runbook_url
        
        # Should contain metric name
        assert "http_latency" in dashboard_url or "http_latency_p99" in dashboard_url
        assert "http" in runbook_url.lower() and "latency" in runbook_url.lower()
    
    def test_confidence_calculation(self, alert_builder):
        """Test confidence levels based on anomaly score"""
        test_cases = [
            (-2.0, "99%"),   # Very anomalous
            (-1.2, "95%"),   # High anomaly
            (-0.8, "90%"),   # Medium-high
            (-0.6, "85%"),   # Medium
            (-0.3, "80%")    # Low anomaly
        ]
        
        for score, expected_confidence in test_cases:
            confidence = alert_builder._calculate_confidence(score)
            assert confidence == expected_confidence
    
    def test_value_formatting_time(self, alert_builder):
        """Test time value formatting"""
        # Milliseconds
        assert "500ms" in alert_builder._format_value(0.5, "http_latency_p95")
        
        # Seconds
        assert "1.50s" in alert_builder._format_value(1.5, "http_latency_p99")
    
    def test_value_formatting_percentage(self, alert_builder):
        """Test percentage value formatting"""
        formatted = alert_builder._format_value(85.3, "node_cpu_usage")
        assert "85.3" in formatted
        assert "%" in formatted
    
    def test_value_formatting_rate(self, alert_builder):
        """Test rate value formatting"""
        formatted = alert_builder._format_value(1250.5, "http_request_rate")
        assert "1250.5" in formatted
        assert "/s" in formatted
    
    def test_value_formatting_bytes(self, alert_builder):
        """Test byte value formatting"""
        # GB
        assert "1.50GB" in alert_builder._format_value(1.5e9, "node_memory_usage")
        
        # MB
        assert "256.00MB" in alert_builder._format_value(256e6, "container_memory_usage")
        
        # KB
        assert "512.00KB" in alert_builder._format_value(512e3, "node_disk_usage")
    
    def test_additional_labels(self, alert_builder, sample_anomaly):
        """Test additional labels are included"""
        additional_labels = {
            "host": "prod-server-01",
            "priority": "high",
            "environment": "production"
        }
        
        alert = alert_builder.build_alert(
            **sample_anomaly,
            additional_labels=additional_labels
        )
        
        # Labels should be merged
        for key, value in additional_labels.items():
            assert alert["labels"][key] == value
    
    def test_summary_emoji(self, alert_builder):
        """Test summary contains correct emoji by severity"""
        severities = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵"
        }
        
        for severity, emoji in severities.items():
            alert = alert_builder.build_alert(
                metric_name="test_metric",
                current_value=100,
                expected_value=50,
                anomaly_score=-1.0,
                severity=severity,
                timestamp=datetime.now()
            )
            
            assert emoji in alert["annotations"]["summary"]
    
    def test_description_direction(self, alert_builder):
        """Test description indicates direction (above/below)"""
        # Above baseline
        alert_above = alert_builder.build_alert(
            metric_name="test_metric",
            current_value=100,
            expected_value=50,
            anomaly_score=-1.0,
            severity="high",
            timestamp=datetime.now()
        )
        assert "above" in alert_above["annotations"]["description"]
        
        # Below baseline
        alert_below = alert_builder.build_alert(
            metric_name="test_metric",
            current_value=30,
            expected_value=50,
            anomaly_score=-1.0,
            severity="high",
            timestamp=datetime.now()
        )
        assert "below" in alert_below["annotations"]["description"]
    
    def test_singleton_pattern(self):
        """Test get_alert_builder returns same instance"""
        builder1 = get_alert_builder()
        builder2 = get_alert_builder()
        
        assert builder1 is builder2
    
    def test_unmapped_metric_uses_default(self, alert_builder):
        """Test unmapped metric uses default mapping"""
        alert = alert_builder.build_alert(
            metric_name="unknown_metric_xyz",
            current_value=100,
            expected_value=50,
            anomaly_score=-1.0,
            severity="medium",
            timestamp=datetime.now()
        )
        
        # Should still have URLs (using default)
        assert alert["annotations"]["dashboard_url"]
        assert alert["annotations"]["runbook_url"]
        assert "unknown" in alert["labels"]["service"].lower() or "ai-anomaly" in alert["annotations"]["dashboard_url"]
    
    def test_timestamp_formatting(self, alert_builder, sample_anomaly):
        """Test timestamps are ISO 8601 formatted"""
        alert = alert_builder.build_alert(**sample_anomaly)
        
        # Should be ISO format: YYYY-MM-DDTHH:MM:SSZ
        starts_at = alert["startsAt"]
        assert "T" in starts_at
        assert "Z" in starts_at or starts_at.endswith("Z")
        
        detected_at = alert["annotations"]["detected_at"]
        assert "T" in detected_at
        assert "Z" in detected_at or detected_at.endswith("Z")


class TestAlertBuilderMetrics:
    """Test Prometheus metrics tracking"""
    
    def test_metrics_are_exposed(self):
        """Test that Prometheus metrics are defined"""
        from app.alert_builder import (
            ALERTS_BUILT_TOTAL,
            ALERTS_DROPPED_TOTAL,
            ALERT_DELIVERY_LATENCY
        )
        
        assert ALERTS_BUILT_TOTAL is not None
        assert ALERTS_DROPPED_TOTAL is not None
        assert ALERT_DELIVERY_LATENCY is not None


class TestAlertBuilderEdgeCases:
    """Test edge cases and error handling"""
    
    def test_division_by_zero_baseline(self):
        """Test handling when baseline is zero"""
        builder = AlertBuilder()
        
        alert = builder.build_alert(
            metric_name="test_metric",
            current_value=100,
            expected_value=0,  # Division by zero!
            anomaly_score=-1.0,
            severity="high",
            timestamp=datetime.now()
        )
        
        # Should not crash, deviation should be inf or 0
        deviation = alert["annotations"]["deviation_percent"]
        assert deviation is not None
    
    def test_negative_values(self):
        """Test handling negative metric values"""
        builder = AlertBuilder()
        
        alert = builder.build_alert(
            metric_name="test_metric",
            current_value=-50,
            expected_value=-10,
            anomaly_score=-1.0,
            severity="high",
            timestamp=datetime.now()
        )
        
        # Should calculate deviation correctly
        # (-50 - -10) / |-10| * 100 = -40 / 10 * 100 = -400%
        deviation = alert["annotations"]["deviation_percent"]
        assert "-" in deviation or "400" in deviation


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
