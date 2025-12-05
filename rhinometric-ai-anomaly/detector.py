#!/usr/bin/env python3
"""
RHINOMETRIC AI Anomaly Detection Service
On-premise anomaly detection using local ML models
"""
import os
import json
import logging
import time
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from datetime import datetime, timedelta
from typing import List, Dict, Any
import numpy as np
from sklearn.ensemble import IsolationForest
from collections import deque

# Configuration
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "300"))  # 5 minutes
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "24"))
ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "0.7"))
PORT = int(os.getenv("PORT", "8080"))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Global anomaly storage
anomalies = deque(maxlen=100)


class AnomalyDetector:
    """Machine Learning anomaly detector"""
    
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.trained = False
    
    def fetch_metric(self, query: str) -> List[float]:
        """Fetch metric values from Prometheus"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=LOOKBACK_HOURS)
            
            params = {
                "query": query,
                "start": start_time.timestamp(),
                "end": end_time.timestamp(),
                "step": "5m"
            }
            
            response = requests.get(
                f"{PROMETHEUS_URL}/api/v1/query_range",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            if data["status"] != "success":
                logger.error(f"Prometheus query failed: {data}")
                return []
            
            # Extract values
            result = data["data"]["result"]
            if not result:
                return []
            
            values = [float(v[1]) for v in result[0]["values"]]
            return values
        
        except Exception as e:
            logger.error(f"Error fetching metric: {e}")
            return []
    
    def detect_anomalies(self, metric_name: str, query: str) -> Dict[str, Any]:
        """Detect anomalies in a metric"""
        values = self.fetch_metric(query)
        
        if len(values) < 10:
            logger.warning(f"Not enough data for {metric_name}: {len(values)} points")
            return {"metric": metric_name, "status": "insufficient_data"}
        
        # Reshape for sklearn
        X = np.array(values).reshape(-1, 1)
        
        # Train model if needed
        if not self.trained or len(values) > 50:
            self.model.fit(X)
            self.trained = True
        
        # Predict anomalies (-1 = anomaly, 1 = normal)
        predictions = self.model.predict(X)
        scores = self.model.score_samples(X)
        
        # Find recent anomalies (last 10% of data)
        recent_window = max(1, len(values) // 10)
        recent_predictions = predictions[-recent_window:]
        recent_scores = scores[-recent_window:]
        recent_values = values[-recent_window:]
        
        # Check if recent data has anomalies
        anomaly_count = np.sum(recent_predictions == -1)
        
        if anomaly_count > 0:
            # Calculate severity
            avg_score = np.mean(recent_scores)
            severity = "high" if avg_score < -0.5 else "medium"
            
            anomaly_info = {
                "timestamp": datetime.now().isoformat(),
                "metric": metric_name,
                "query": query,
                "current_value": float(recent_values[-1]),
                "mean_value": float(np.mean(values[:-recent_window])),
                "std_dev": float(np.std(values[:-recent_window])),
                "anomaly_score": float(avg_score),
                "severity": severity,
                "anomaly_count": int(anomaly_count),
                "total_points": len(recent_predictions),
                "message": f"Anomaly detected in {metric_name}: {anomaly_count}/{len(recent_predictions)} recent points"
            }
            
            return anomaly_info
        
        return {"metric": metric_name, "status": "normal"}
    
    def check_all_metrics(self):
        """Check all defined metrics for anomalies"""
        metrics = [
            {
                "name": "CPU Usage",
                "query": '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
            },
            {
                "name": "Memory Usage",
                "query": '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
            },
            {
                "name": "Error Rate",
                "query": 'sum(rate(http_requests_total{status=~"5.."}[5m]))'
            },
            {
                "name": "Request Latency",
                "query": 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))'
            }
        ]
        
        logger.info(f"Checking {len(metrics)} metrics for anomalies...")
        
        for metric_config in metrics:
            result = self.detect_anomalies(metric_config["name"], metric_config["query"])
            
            if result.get("status") != "normal" and result.get("status") != "insufficient_data":
                logger.warning(f"⚠️  Anomaly detected: {result['message']}")
                anomalies.append(result)


class HTTPHandler(BaseHTTPRequestHandler):
    """HTTP endpoint handler"""
    
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        
        elif self.path == "/anomalies":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {
                "anomalies": list(anomalies),
                "count": len(anomalies),
                "last_check": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress default logging


def detection_loop(detector: AnomalyDetector):
    """Main detection loop"""
    logger.info("Starting anomaly detection loop...")
    
    while True:
        try:
            detector.check_all_metrics()
        except Exception as e:
            logger.error(f"Detection error: {e}")
        
        time.sleep(CHECK_INTERVAL)


def main():
    logger.info("=" * 60)
    logger.info("RHINOMETRIC AI Anomaly Detection v2.2.0")
    logger.info("=" * 60)
    logger.info(f"Prometheus: {PROMETHEUS_URL}")
    logger.info(f"Check interval: {CHECK_INTERVAL}s")
    logger.info(f"Lookback: {LOOKBACK_HOURS}h")
    logger.info(f"HTTP API: http://0.0.0.0:{PORT}")
    logger.info("=" * 60)
    
    # Initialize detector
    detector = AnomalyDetector()
    
    # Start detection thread
    detection_thread = Thread(target=detection_loop, args=(detector,), daemon=True)
    detection_thread.start()
    
    # Start HTTP server
    server = HTTPServer(("0.0.0.0", PORT), HTTPHandler)
    logger.info(f"HTTP server listening on port {PORT}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
