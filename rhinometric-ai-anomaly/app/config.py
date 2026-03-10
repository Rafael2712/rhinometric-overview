"""
Configuration Manager
Loads and validates configuration from YAML file
"""
import os
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)


class ServerConfig(BaseModel):
    """API Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8085
    workers: int = 2
    log_level: str = "INFO"
    cors_enabled: bool = True
    cors_origins: List[str] = ["*"]


class PrometheusConfig(BaseModel):
    """Prometheus connection configuration"""
    url: str = "http://prometheus:9090"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5


class AlertmanagerConfig(BaseModel):
    """Alertmanager configuration"""
    enabled: bool = True  # Internal connection enabled
    alerts_enabled: bool = False  # AI alerts globally enabled (default OFF)
    url: str = "http://alertmanager:9093"
    timeout: int = 10
    labels: Dict[str, str] = Field(default_factory=dict)


class DetectionConfig(BaseModel):
    """Anomaly detection configuration"""
    check_interval: int = 300
    lookback_hours: int = 24
    min_data_points: int = 20
    max_anomalies: int = 500
    auto_retrain: bool = True
    retrain_interval: int = 6


class ModelConfig(BaseModel):
    """Machine learning model configuration"""
    isolation_forest: Dict[str, Any] = Field(default_factory=dict)
    lof: Dict[str, Any] = Field(default_factory=dict)
    ocsvm: Dict[str, Any] = Field(default_factory=dict)
    statistical: Dict[str, Any] = Field(default_factory=dict)


class MetricConfig(BaseModel):
    """Individual metric configuration"""
    name: str
    display_name: str
    description: str
    query: str
    enabled: bool = True
    priority: str = "medium"
    check_interval: Optional[int] = None
    models: List[str] = Field(default_factory=list)
    thresholds: Dict[str, float] = Field(default_factory=dict)
    sensitivity: str = "medium"
    alert_on_any_anomaly: bool = False
    invert_threshold: bool = False
    group_by: str = ""
    entity_type: str = ""
    source: str = ""


class PersistenceConfig(BaseModel):
    """Model persistence configuration"""
    enabled: bool = True
    directory: str = "/app/models"
    save_interval: int = 3600
    max_model_age: int = 604800
    compression: bool = True


class MetricsExportConfig(BaseModel):
    """Metrics export configuration"""
    enabled: bool = True
    port: int = 9090
    path: str = "/metrics"
    prefix: str = "rhinometric_anomaly_"


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = "INFO"
    format: str = "json"
    output: str = "stdout"
    log_anomalies: bool = True
    log_predictions: bool = False


class FeaturesConfig(BaseModel):
    """Feature flags"""
    enable_api: bool = True
    enable_web_ui: bool = False
    enable_notifications: bool = True
    enable_auto_remediation: bool = False
    enable_model_explanation: bool = True


class Config(BaseModel):
    """Main configuration model"""
    server: ServerConfig
    prometheus: PrometheusConfig
    alertmanager: AlertmanagerConfig
    detection: DetectionConfig
    models: ModelConfig
    metrics: List[MetricConfig]
    persistence: PersistenceConfig
    metrics_export: MetricsExportConfig
    logging: LoggingConfig
    features: FeaturesConfig

    @validator("metrics")
    def validate_metrics(cls, v):
        """Ensure at least one metric is enabled"""
        if not any(m.enabled for m in v):
            raise ValueError("At least one metric must be enabled")
        return v


class ConfigManager:
    """Configuration manager with environment variable substitution"""
    
    def __init__(self, config_path: str = "/app/config.yaml"):
        self.config_path = Path(config_path)
        self._config: Optional[Config] = None
    
    def _substitute_env_vars(self, value: Any) -> Any:
        """Recursively substitute environment variables in config values"""
        if isinstance(value, str):
            # Handle ${VAR:default} syntax
            if value.startswith("${") and value.endswith("}"):
                var_def = value[2:-1]
                if ":" in var_def:
                    var_name, default = var_def.split(":", 1)
                    return os.getenv(var_name, default)
                else:
                    return os.getenv(var_def, value)
            return value
        elif isinstance(value, dict):
            return {k: self._substitute_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._substitute_env_vars(item) for item in value]
        return value
    
    def load(self) -> Config:
        """Load and parse configuration file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        logger.info(f"Loading configuration from {self.config_path}")
        
        with open(self.config_path, "r") as f:
            raw_config = yaml.safe_load(f)
        
        # Substitute environment variables
        processed_config = self._substitute_env_vars(raw_config)
        
        # Validate and parse
        self._config = Config(**processed_config)
        
        logger.info(f"Configuration loaded successfully")
        logger.info(f"  - {len(self._config.metrics)} metrics defined")
        logger.info(f"  - {sum(1 for m in self._config.metrics if m.enabled)} metrics enabled")
        logger.info(f"  - Check interval: {self._config.detection.check_interval}s")
        logger.info(f"  - Lookback hours: {self._config.detection.lookback_hours}h")
        
        return self._config
    
    @property
    def config(self) -> Config:
        """Get loaded configuration"""
        if self._config is None:
            self._config = self.load()
        return self._config
    
    def get_enabled_metrics(self) -> List[MetricConfig]:
        """Get list of enabled metrics"""
        return [m for m in self.config.metrics if m.enabled]
    
    def get_metric(self, name: str) -> Optional[MetricConfig]:
        """Get specific metric configuration by name"""
        for metric in self.config.metrics:
            if metric.name == name:
                return metric
        return None
    
    def reload(self) -> Config:
        """Reload configuration from file"""
        logger.info("Reloading configuration...")
        self._config = None
        return self.load()


# Global configuration instance
config_manager = ConfigManager(
    config_path=os.getenv("CONFIG_PATH", "/app/config.yaml")
)
