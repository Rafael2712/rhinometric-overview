"""
Configuration Management
Loads configuration from environment variables and YAML files
"""
import os
import yaml
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)


class PrometheusConfig(BaseModel):
    """Prometheus configuration"""
    url: str = "http://prometheus:9090"
    timeout: int = 30


class GrafanaConfig(BaseModel):
    """Grafana configuration"""
    url: str = "http://grafana:3000"
    username: str = "admin"
    password: str = "admin"
    timeout: int = 30


class SMTPConfig(BaseModel):
    """SMTP email configuration"""
    enabled: bool = True
    host: str = "smtp.gmail.com"
    port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    from_email: str = "rhinometric@example.com"
    from_name: str = "RhinoMetric Reports"


class ReportSchedule(BaseModel):
    """Report scheduling configuration"""
    enabled: bool = True
    cron: str = "0 8 * * *"  # Daily at 8 AM
    timezone: str = "UTC"


class ReportConfig(BaseModel):
    """Individual report configuration"""
    name: str
    display_name: str
    enabled: bool = True
    type: str = "executive"  # executive, technical, anomaly
    format: List[str] = ["pdf", "html"]
    recipients: List[str] = []
    schedule: Optional[ReportSchedule] = None
    include_charts: bool = True
    include_anomalies: bool = True
    include_metrics: bool = True
    lookback_hours: int = 24


class ServerConfig(BaseModel):
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8086
    workers: int = 1
    log_level: str = "info"


class StorageConfig(BaseModel):
    """Storage configuration"""
    reports_dir: str = "/app/reports"
    temp_dir: str = "/app/temp"
    max_age_days: int = 30
    max_size_mb: int = 1000


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = "INFO"
    format: str = "json"  # json or text


class Config(BaseModel):
    """Main application configuration"""
    server: ServerConfig = ServerConfig()
    prometheus: PrometheusConfig = PrometheusConfig()
    grafana: GrafanaConfig = GrafanaConfig()
    smtp: SMTPConfig = SMTPConfig()
    storage: StorageConfig = StorageConfig()
    logging: LoggingConfig = LoggingConfig()
    reports: List[ReportConfig] = []


class ConfigManager:
    """Configuration manager with environment variable substitution"""
    
    def __init__(self, config_path: str = "/app/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _substitute_env_vars(self, value: Any) -> Any:
        """Recursively substitute environment variables in config values"""
        if isinstance(value, str):
            # Handle ${VAR:default} syntax
            if value.startswith("${") and "}" in value:
                var_expr = value[2:-1]  # Remove ${ and }
                
                if ":" in var_expr:
                    var_name, default = var_expr.split(":", 1)
                    return os.getenv(var_name, default)
                else:
                    return os.getenv(var_expr, value)
            return value
        
        elif isinstance(value, dict):
            return {k: self._substitute_env_vars(v) for k, v in value.items()}
        
        elif isinstance(value, list):
            return [self._substitute_env_vars(item) for item in value]
        
        return value
    
    def _load_config(self) -> Config:
        """Load and parse configuration from YAML file"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Config file not found: {self.config_path}, using defaults")
                return Config()
            
            with open(self.config_path, 'r') as f:
                raw_config = yaml.safe_load(f)
            
            if not raw_config:
                logger.warning("Empty config file, using defaults")
                return Config()
            
            # Substitute environment variables
            config_dict = self._substitute_env_vars(raw_config)
            
            # Parse with Pydantic
            config = Config(**config_dict)
            
            logger.info(f"Configuration loaded: {len(config.reports)} reports configured")
            return config
        
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return Config()
    
    def reload(self) -> bool:
        """Reload configuration from file"""
        try:
            new_config = self._load_config()
            self.config = new_config
            logger.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error reloading config: {e}")
            return False


# Global config manager instance
config_manager = ConfigManager()
