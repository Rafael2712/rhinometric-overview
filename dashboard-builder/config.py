"""
Configuration Management
"""
import os
from typing import Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class GrafanaConfig(BaseModel):
    """Grafana configuration"""
    url: str = "http://grafana:3000"
    username: str = "admin"
    password: str = "admin"
    timeout: int = 30


class PrometheusConfig(BaseModel):
    """Prometheus configuration"""
    url: str = "http://prometheus:9090"
    timeout: int = 30


class ServerConfig(BaseModel):
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8087
    workers: int = 1
    log_level: str = "info"
    cors_origins: list = ["*"]


class Config(BaseModel):
    """Main application configuration"""
    server: ServerConfig = ServerConfig()
    grafana: GrafanaConfig = GrafanaConfig()
    prometheus: PrometheusConfig = PrometheusConfig()


# Load from environment variables
config = Config(
    server=ServerConfig(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8087")),
        log_level=os.getenv("LOG_LEVEL", "info"),
    ),
    grafana=GrafanaConfig(
        url=os.getenv("GRAFANA_URL", "http://grafana:3000"),
        username=os.getenv("GRAFANA_USER", "admin"),
        password=os.getenv("GRAFANA_PASSWORD", "admin"),
    ),
    prometheus=PrometheusConfig(
        url=os.getenv("PROMETHEUS_URL", "http://prometheus:9090"),
    ),
)
