from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # API Settings
    API_TITLE: str = "Rhinometric Console API Gateway"
    API_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    
    # Security (CRITICAL: Change SECRET_KEY in production)
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_MIN_32_CHARS_REQUIRED"  # Override with SECRET_KEY env var
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days (sufficient for 14-day trial period)
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3002", "http://127.0.0.1:3002"]
    
    # External Services URLs
    PROMETHEUS_URL: str = "http://rhinometric-prometheus:9090"
    AI_ANOMALY_URL: str = "http://rhinometric-ai-anomaly:8085"
    LICENSE_VALIDATOR_URL: str = "http://rhinometric-license-server-v2:5000"  # License Server v2 (port 5000)
    ALERTMANAGER_URL: str = "http://rhinometric-alertmanager:9093"
    GRAFANA_URL: str = "http://rhinometric-grafana:3000"
    LOKI_URL: str = "http://rhinometric-loki:3100"
    JAEGER_URL: str = "http://rhinometric-jaeger:16686"  # Jaeger UI/API
    
    # Admin Credentials (override these in .env for production)
    ADMIN_USERNAME: str = "admin"  # Override with ADMIN_USERNAME env var
    ADMIN_PASSWORD: str = "CHANGE_ME_IN_PRODUCTION"  # Override with ADMIN_PASSWORD env var
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
