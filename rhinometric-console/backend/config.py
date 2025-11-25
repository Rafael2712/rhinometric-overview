from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # API Settings
    API_TITLE: str = "Rhinometric Console API Gateway"
    API_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3002", "http://127.0.0.1:3002"]
    
    # External Services URLs
    PROMETHEUS_URL: str = "http://localhost:9090"
    AI_ANOMALY_URL: str = "http://localhost:8085"
    LICENSE_VALIDATOR_URL: str = "http://localhost:8091"
    ALERTMANAGER_URL: str = "http://localhost:9093"
    GRAFANA_URL: str = "http://localhost:3000"
    
    # Admin Credentials (temporary - move to DB later)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"  # In production: use hashed password
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
