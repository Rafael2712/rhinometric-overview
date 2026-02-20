from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://rhinometric:rhinometric@postgres:5432/rhinometric"
    
    # API Settings
    API_TITLE: str = "Rhinometric Console API Gateway"
    API_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    
    # Security (CRITICAL: Change SECRET_KEY in production)
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_MIN_32_CHARS_REQUIRED"  # Override with SECRET_KEY env var
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
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

    # Deployment Mode (populated from license at runtime)
    # ON_PREMISE = self-hosted customer installation
    # SAAS_SINGLE_TENANT = cloud-hosted single-tenant deployment
    DEPLOYMENT_MODE: str = "ON_PREMISE"
    
    # Grafana Credentials
    GRAFANA_USER: str = "admin"  # Override with GRAFANA_USER env var
    GRAFANA_PASSWORD: str = "admin"  # Override with GRAFANA_PASSWORD env var
    
    # Admin Credentials (override these in .env for production)
    ADMIN_USERNAME: str = "admin"  # Override with ADMIN_USERNAME env var
    ADMIN_PASSWORD: str = "CHANGE_ME_IN_PRODUCTION"  # Override with ADMIN_PASSWORD env var
    
    # Bootstrap Admin User (IMMORTAL ADMIN - always recreated on startup if missing)
    RHINO_ADMIN_USER: str = "admin"  # Override with RHINO_ADMIN_USER env var
    RHINO_ADMIN_PASSWORD: str = "271211Rc"  # Override with RHINO_ADMIN_PASSWORD env var
    RHINO_ADMIN_EMAIL: str = "admin@rhinometric.local"  # Override with RHINO_ADMIN_EMAIL env var
    
    # Email Configuration (Zoho SMTP)
    MAIL_USERNAME: str = ""  # Email username
    MAIL_PASSWORD: str = ""  # Email password
    MAIL_FROM: str = ""  # From address
    MAIL_PORT: int = 587  # SMTP port
    MAIL_SERVER: str = "smtp.zoho.com"  # SMTP server
    MAIL_STARTTLS: bool = True  # Use STARTTLS
    MAIL_SSL_TLS: bool = False  # Use SSL/TLS
    MAIL_FROM_NAME: str = "Rhinometric Platform"  # From name
    
    # Frontend URL (for password reset links)
    FRONTEND_URL: str = "http://localhost:3002"
    
    # Rate Limiting
    RATE_LIMIT_FORGOT_PASSWORD: str = "3/hour"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
