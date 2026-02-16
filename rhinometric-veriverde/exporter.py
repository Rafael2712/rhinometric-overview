#!/usr/bin/env python3
"""
RHINOMETRIC VeriVerde Exporter v1.0
====================================

Sustainability and Energy Monitoring Exporter
Exposes environmental and energy metrics in Prometheus format.

Metrics exposed:
- rhinometric_energy_kwh: Energy consumption in kilowatt-hours
- rhinometric_room_temperature_c: Room/rack temperature in Celsius
- rhinometric_renewable_percent: Percentage of renewable energy
- rhinometric_co2_emissions_kg: Estimated CO2 emissions in kilograms
- rhinometric_efficiency_score: Operational efficiency score (0-100)

Configuration via environment variables:
- VERIVERDE_PORT: HTTP port (default: 9200)
- VERIVERDE_ENERGY_SENSOR_URL: URL to energy sensor API (optional)
- VERIVERDE_TEMP_SENSOR_URL: URL to temperature sensor API (optional)
- VERIVERDE_RENEWABLE_PERCENT: Static renewable percentage (default: 0)
- CO2_FACTOR_KG_PER_KWH: CO2 emissions factor (default: 0.233)
"""

import os
import time
import random
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import json
import urllib.request
import urllib.error

# Configuration
PORT = int(os.getenv('VERIVERDE_PORT', 9200))
ENERGY_SENSOR_URL = os.getenv('VERIVERDE_ENERGY_SENSOR_URL')
TEMP_SENSOR_URL = os.getenv('VERIVERDE_TEMP_SENSOR_URL')
RENEWABLE_PERCENT = float(os.getenv('VERIVERDE_RENEWABLE_PERCENT', 0))
CO2_FACTOR = float(os.getenv('CO2_FACTOR_KG_PER_KWH', 0.233))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('veriverde-exporter')

# Metrics state
class MetricsCollector:
    def __init__(self):
        self.energy_kwh = 0.0
        self.temperature_c = 20.0
        self.renewable_percent = RENEWABLE_PERCENT
        self.last_update = time.time()
        self.baseline_energy = random.uniform(2.0, 4.0)  # Baseline for simulation
        
    def fetch_energy_kwh(self):
        """Fetch energy consumption from sensor or simulate"""
        if ENERGY_SENSOR_URL:
            try:
                with urllib.request.urlopen(ENERGY_SENSOR_URL, timeout=5) as response:
                    data = json.loads(response.read())
                    return float(data.get('energy_kwh', 0))
            except (urllib.error.URLError, json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to fetch energy from sensor: {e}")
        
        # Simulation: fluctuating consumption based on time of day
        hour = datetime.now().hour
        if 9 <= hour <= 18:  # Business hours
            load_factor = random.uniform(0.8, 1.2)
        else:  # Night/weekend
            load_factor = random.uniform(0.3, 0.6)
        
        self.energy_kwh = self.baseline_energy * load_factor
        return self.energy_kwh
    
    def fetch_temperature_c(self):
        """Fetch temperature from sensor or simulate"""
        if TEMP_SENSOR_URL:
            try:
                with urllib.request.urlopen(TEMP_SENSOR_URL, timeout=5) as response:
                    data = json.loads(response.read())
                    return float(data.get('temperature_c', 20))
            except (urllib.error.URLError, json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to fetch temperature from sensor: {e}")
        
        # Simulation: temperature between 18-28°C with some variation
        self.temperature_c = random.uniform(18, 28)
        return self.temperature_c
    
    def calculate_co2_emissions_kg(self, energy_kwh):
        """Calculate CO2 emissions based on energy consumption"""
        # Only non-renewable energy contributes to emissions
        non_renewable_factor = (100 - self.renewable_percent) / 100
        return energy_kwh * CO2_FACTOR * non_renewable_factor
    
    def calculate_efficiency_score(self, energy_kwh, temperature_c):
        """Calculate operational efficiency score (0-100)"""
        # Optimal: low energy, optimal temperature (20-24°C)
        energy_penalty = min(energy_kwh / 10, 1.0) * 50  # Max 50 points penalty
        
        optimal_temp_range = (20, 24)
        if optimal_temp_range[0] <= temperature_c <= optimal_temp_range[1]:
            temp_penalty = 0
        else:
            temp_deviation = min(
                abs(temperature_c - optimal_temp_range[0]),
                abs(temperature_c - optimal_temp_range[1])
            )
            temp_penalty = min(temp_deviation * 5, 50)  # Max 50 points penalty
        
        score = 100 - energy_penalty - temp_penalty
        return max(0, min(100, score))
    
    def update_metrics(self):
        """Update all metrics"""
        self.fetch_energy_kwh()
        self.fetch_temperature_c()
        self.last_update = time.time()
        logger.debug(f"Metrics updated: energy={self.energy_kwh:.2f}kWh, temp={self.temperature_c:.1f}°C")

metrics_collector = MetricsCollector()

class MetricsHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        if self.path == '/metrics':
            self.send_metrics()
        elif self.path == '/health':
            self.send_health()
        else:
            self.send_response(404)
            self.end_headers()
    
    def send_health(self):
        """Health check endpoint"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'sensors': {
                'energy': 'connected' if ENERGY_SENSOR_URL else 'simulated',
                'temperature': 'connected' if TEMP_SENSOR_URL else 'simulated'
            }
        }
        self.wfile.write(json.dumps(health).encode())
    
    def send_metrics(self):
        """Expose metrics in Prometheus format"""
        # Update metrics
        metrics_collector.update_metrics()
        
        energy = metrics_collector.energy_kwh
        temperature = metrics_collector.temperature_c
        renewable = metrics_collector.renewable_percent
        co2 = metrics_collector.calculate_co2_emissions_kg(energy)
        efficiency = metrics_collector.calculate_efficiency_score(energy, temperature)
        
        # Build Prometheus-formatted response
        metrics = f"""# HELP rhinometric_energy_kwh Current energy consumption in kilowatt-hours
# TYPE rhinometric_energy_kwh gauge
rhinometric_energy_kwh {energy:.4f}

# HELP rhinometric_room_temperature_c Current room or rack temperature in Celsius
# TYPE rhinometric_room_temperature_c gauge
rhinometric_room_temperature_c {temperature:.2f}

# HELP rhinometric_renewable_percent Percentage of renewable energy being used
# TYPE rhinometric_renewable_percent gauge
rhinometric_renewable_percent {renewable:.2f}

# HELP rhinometric_co2_emissions_kg Estimated CO2 emissions in kilograms
# TYPE rhinometric_co2_emissions_kg gauge
rhinometric_co2_emissions_kg {co2:.4f}

# HELP rhinometric_efficiency_score Operational efficiency score (0-100)
# TYPE rhinometric_efficiency_score gauge
rhinometric_efficiency_score {efficiency:.2f}

# HELP rhinometric_veriverde_info VeriVerde exporter information
# TYPE rhinometric_veriverde_info gauge
rhinometric_veriverde_info{{version="1.0",mode="{'connected' if ENERGY_SENSOR_URL else 'simulated'}"}} 1
"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; version=0.0.4')
        self.end_headers()
        self.wfile.write(metrics.encode())

def run_server():
    """Start the HTTP server"""
    server = HTTPServer(('0.0.0.0', PORT), MetricsHandler)
    logger.info(f"VeriVerde Exporter started on port {PORT}")
    logger.info(f"Metrics endpoint: http://0.0.0.0:{PORT}/metrics")
    logger.info(f"Health endpoint: http://0.0.0.0:{PORT}/health")
    logger.info(f"Energy sensor: {'Connected' if ENERGY_SENSOR_URL else 'Simulated'}")
    logger.info(f"Temperature sensor: {'Connected' if TEMP_SENSOR_URL else 'Simulated'}")
    logger.info(f"Renewable energy: {RENEWABLE_PERCENT}%")
    logger.info(f"CO2 factor: {CO2_FACTOR} kg/kWh")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        server.shutdown()

if __name__ == '__main__':
    run_server()
