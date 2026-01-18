"""
RHINOMETRIC v2.4.0 - API Connector Backend
==========================================

FastAPI backend para el conector visual de datasources.

Features:
- Test de conexiones en tiempo real
- Validación de credenciales
- Templates pre-configurados (AWS, Azure, PostgreSQL, Redis, etc.)
- Gestión de datasources
- Integration con Grafana API
"""

from fastapi import FastAPI, HTTPException, Body, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import asyncio
import json
from datetime import datetime
import logging
import httpx
import os
from sqlalchemy import create_engine, Column, String, Integer, Boolean, JSON, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Templates
templates = Jinja2Templates(directory="templates")

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Variables de entorno
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://rhinometric-grafana:3000")
GRAFANA_API_TOKEN = os.getenv("GRAFANA_API_TOKEN", "")  # DEBE venir de secret
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://rhinometric_user:rhinometric_pass@rhinometric-postgres:5432/rhinometric_db")

# SQLAlchemy
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modelo para Datasources
class DatasourceModel(Base):
    __tablename__ = "datasources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    type = Column(String, nullable=False)  # postgresql, redis, prometheus, etc.
    config = Column(JSON, nullable=False)  # Configuración específica
    grafana_uid = Column(String, nullable=True)  # UID en Grafana
    grafana_id = Column(Integer, nullable=True)  # ID en Grafana
    enabled = Column(Boolean, default=True)
    tags = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Crear tablas
Base.metadata.create_all(bind=engine)

# Dependency para obtener DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Importar conectores
from connectors.postgresql import PostgreSQLConnector
from connectors.redis_connector import RedisConnector
from connectors.prometheus_connector import PrometheusConnector
from connectors.aws import AWSConnector
from connectors.azure import AzureConnector

# Importar conectores de messaging
from connectors.rabbitmq_connector import RabbitMQConnector
from connectors.kafka_connector import KafkaConnector
from connectors.mqtt_connector import MQTTConnector

# Configuración logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI(
    title="RHINOMETRIC API Connector",
    description="Visual connector for external datasources",
    version="2.4.0"
)

# CORS para Grafana
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# MODELS
# ============================================================================

class ConnectionTest(BaseModel):
    """Model para test de conexión."""
    datasource_type: str = Field(..., description="Tipo de datasource (postgresql, redis, prometheus, aws, azure, rabbitmq, kafka, mqtt)")
    host: Optional[str] = Field(None, description="Hostname o IP")
    port: Optional[int] = Field(None, description="Puerto")
    database: Optional[str] = Field(None, description="Nombre de base de datos")
    username: Optional[str] = Field(None, description="Usuario")
    password: Optional[str] = Field(None, description="Contraseña")
    region: Optional[str] = Field(None, description="Región (AWS/Azure)")
    access_key: Optional[str] = Field(None, description="Access Key (AWS)")
    secret_key: Optional[str] = Field(None, description="Secret Key (AWS)")
    subscription_id: Optional[str] = Field(None, description="Subscription ID (Azure)")
    tenant_id: Optional[str] = Field(None, description="Tenant ID (Azure)")
    client_id: Optional[str] = Field(None, description="Client ID (Azure/MQTT)")
    client_secret: Optional[str] = Field(None, description="Client Secret (Azure)")
    url: Optional[str] = Field(None, description="URL (Prometheus, Loki, etc.)")
    ssl: bool = Field(default=False, description="Usar SSL/TLS")
    timeout: int = Field(default=5, description="Timeout en segundos")
    
    # RabbitMQ specific
    vhost: Optional[str] = Field(None, description="Virtual host (RabbitMQ)")
    
    # Kafka specific
    bootstrap_servers: Optional[str] = Field(None, description="Bootstrap servers (Kafka)")
    security_protocol: Optional[str] = Field(None, description="Security protocol (Kafka)")
    sasl_mechanism: Optional[str] = Field(None, description="SASL mechanism (Kafka)")
    ssl_check_hostname: Optional[bool] = Field(None, description="Check SSL hostname (Kafka)")
    
    # MQTT specific
    use_tls: Optional[bool] = Field(None, description="Use TLS (MQTT)")
    keepalive: Optional[int] = Field(None, description="Keepalive interval (MQTT)")
    clean_session: Optional[bool] = Field(None, description="Clean session (MQTT)")
    test_topic: Optional[str] = Field(None, description="Test topic (MQTT)")


class DatasourceConfig(BaseModel):
    """Model para configuración de datasource."""
    name: str = Field(..., description="Nombre del datasource")
    type: str = Field(..., description="Tipo de datasource")
    config: Dict[str, Any] = Field(..., description="Configuración específica")
    enabled: bool = Field(default=True, description="Datasource activo")
    tags: List[str] = Field(default_factory=list, description="Tags para clasificación")


class TestResult(BaseModel):
    """Model para resultado de test."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    duration_ms: float


class GrafanaDatasourceCreate(BaseModel):
    """Model para crear datasource en Grafana."""
    name: str = Field(..., description="Nombre del datasource")
    type: str = Field(..., description="Tipo de datasource")
    config: Dict[str, Any] = Field(..., description="Configuración específica")
    tags: List[str] = Field(default_factory=list, description="Tags")
    is_default: bool = Field(default=False, description="Datasource por defecto")


# ============================================================================
# TEMPLATES PRE-CONFIGURADOS
# ============================================================================

TEMPLATES = {
    "postgresql": {
        "name": "PostgreSQL Database",
        "description": "Conexión a base de datos PostgreSQL",
        "icon": "database",
        "category": "database",
        "color": "#4CAF50",
        "fields": [
            {"name": "host", "type": "text", "required": True, "default": "localhost"},
            {"name": "port", "type": "number", "required": True, "default": 5432},
            {"name": "database", "type": "text", "required": True, "default": "postgres"},
            {"name": "username", "type": "text", "required": True, "default": "postgres"},
            {"name": "password", "type": "password", "required": True},
            {"name": "ssl", "type": "boolean", "required": False, "default": False},
        ]
    },
    "redis": {
        "name": "Redis Cache",
        "description": "Conexión a Redis (cache, queue, pub/sub)",
        "icon": "memory",
        "category": "database",
        "color": "#DC382D",
        "fields": [
            {"name": "host", "type": "text", "required": True, "default": "localhost"},
            {"name": "port", "type": "number", "required": True, "default": 6379},
            {"name": "database", "type": "number", "required": False, "default": 0},
            {"name": "password", "type": "password", "required": False},
            {"name": "ssl", "type": "boolean", "required": False, "default": False},
        ]
    },
    "prometheus": {
        "name": "Prometheus",
        "description": "Prometheus metrics server",
        "icon": "trending_up",
        "category": "api",
        "color": "#E6522C",
        "fields": [
            {"name": "url", "type": "text", "required": True, "default": "http://localhost:9090"},
            {"name": "timeout", "type": "number", "required": False, "default": 30},
        ]
    },
    "aws-cloudwatch": {
        "name": "AWS CloudWatch",
        "description": "AWS CloudWatch metrics and logs",
        "icon": "cloud",
        "category": "cloud",
        "color": "#FF9900",
        "fields": [
            {"name": "region", "type": "select", "required": True, "options": ["us-east-1", "eu-west-1", "eu-central-1"], "default": "us-east-1"},
            {"name": "access_key", "type": "text", "required": True},
            {"name": "secret_key", "type": "password", "required": True},
        ]
    },
    "azure-monitor": {
        "name": "Azure Monitor",
        "description": "Azure Monitor metrics and logs",
        "icon": "cloud",
        "category": "cloud",
        "color": "#9C27B0",
        "fields": [
            {"name": "subscription_id", "type": "text", "required": True},
            {"name": "tenant_id", "type": "text", "required": True},
            {"name": "client_id", "type": "text", "required": True},
            {"name": "client_secret", "type": "password", "required": True},
        ]
    },
    "rabbitmq": {
        "name": "RabbitMQ",
        "description": "Message broker (AMQP protocol) - On-premise only",
        "icon": "message",
        "category": "messaging",
        "color": "#FF6600",
        "tooltip": "Test connection to local RabbitMQ Management API (port 15672)",
        "fields": [
            {"name": "host", "type": "text", "required": True, "default": "localhost", "placeholder": "localhost or 192.168.1.10"},
            {"name": "port", "type": "number", "required": True, "default": 15672, "placeholder": "Management API port (default: 15672)"},
            {"name": "username", "type": "text", "required": True, "default": "guest"},
            {"name": "password", "type": "password", "required": True, "default": "guest"},
            {"name": "vhost", "type": "text", "required": False, "default": "/", "placeholder": "Virtual host (default: /)"},
            {"name": "use_ssl", "type": "boolean", "required": False, "default": False},
        ]
    },
    "kafka": {
        "name": "Apache Kafka",
        "description": "Event streaming platform - On-premise only",
        "icon": "stream",
        "category": "messaging",
        "color": "#231F20",
        "tooltip": "Test connection to local Kafka cluster (port 9092)",
        "fields": [
            {"name": "bootstrap_servers", "type": "text", "required": True, "default": "localhost:9092", "placeholder": "kafka1:9092,kafka2:9092"},
            {"name": "security_protocol", "type": "select", "required": True, "options": ["PLAINTEXT", "SSL", "SASL_PLAINTEXT", "SASL_SSL"], "default": "PLAINTEXT"},
            {"name": "sasl_mechanism", "type": "select", "required": False, "options": ["PLAIN", "SCRAM-SHA-256", "SCRAM-SHA-512"], "default": "PLAIN"},
            {"name": "sasl_username", "type": "text", "required": False},
            {"name": "sasl_password", "type": "password", "required": False},
            {"name": "ssl_check_hostname", "type": "boolean", "required": False, "default": True},
        ]
    },
    "mqtt": {
        "name": "MQTT Broker",
        "description": "IoT messaging protocol (Mosquitto, EMQX) - On-premise only",
        "icon": "sensors",
        "category": "messaging",
        "color": "#660066",
        "tooltip": "Test connection to local MQTT broker (port 1883)",
        "fields": [
            {"name": "host", "type": "text", "required": True, "default": "localhost", "placeholder": "localhost or 192.168.1.10"},
            {"name": "port", "type": "number", "required": True, "default": 1883, "placeholder": "1883 (non-SSL) or 8883 (SSL)"},
            {"name": "username", "type": "text", "required": False},
            {"name": "password", "type": "password", "required": False},
            {"name": "client_id", "type": "text", "required": False, "default": "rhinometric-connector"},
            {"name": "use_tls", "type": "boolean", "required": False, "default": False},
            {"name": "keepalive", "type": "number", "required": False, "default": 60, "placeholder": "Keepalive interval (seconds)"},
            {"name": "clean_session", "type": "boolean", "required": False, "default": True},
            {"name": "test_topic", "type": "text", "required": False, "default": "rhinometric/test", "placeholder": "Topic for testing pub/sub"},
        ]
    },
}


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve API Connector UI."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "service": "RHINOMETRIC API Connector",
        "version": "2.4.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/templates")
async def get_templates():
    """Obtener templates de datasources disponibles."""
    return {
        "templates": TEMPLATES,
        "count": len(TEMPLATES)
    }


@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    """Obtener un template específico."""
    if template_id not in TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    
    return {
        "template_id": template_id,
        "template": TEMPLATES[template_id]
    }


@app.post("/api/test-connection")
async def test_connection(connection: ConnectionTest):
    """
    Testear conexión a un datasource.
    
    Retorna:
    - success: bool (True si la conexión fue exitosa)
    - message: str (mensaje descriptivo)
    - details: dict (información adicional)
    - duration_ms: float (duración del test)
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Testing connection to {connection.datasource_type}")
        
        # PostgreSQL
        if connection.datasource_type == "postgresql":
            connector = PostgreSQLConnector(
                host=connection.host,
                port=connection.port,
                database=connection.database,
                username=connection.username,
                password=connection.password,
                ssl=connection.ssl,
                timeout=connection.timeout
            )
            result = await connector.test_connection()
        
        # Redis
        elif connection.datasource_type == "redis":
            connector = RedisConnector(
                host=connection.host,
                port=connection.port,
                database=connection.database or 0,
                password=connection.password,
                ssl=connection.ssl,
                timeout=connection.timeout
            )
            result = await connector.test_connection()
        
        # Prometheus
        elif connection.datasource_type == "prometheus":
            connector = PrometheusConnector(
                url=connection.url,
                timeout=connection.timeout
            )
            result = await connector.test_connection()
        
        # AWS CloudWatch
        elif connection.datasource_type == "aws-cloudwatch":
            connector = AWSConnector(
                region=connection.region,
                access_key=connection.access_key,
                secret_key=connection.secret_key
            )
            result = await connector.test_connection()
        
        # Azure Monitor
        elif connection.datasource_type == "azure-monitor":
            connector = AzureConnector(
                subscription_id=connection.subscription_id,
                tenant_id=connection.tenant_id,
                client_id=connection.client_id,
                client_secret=connection.client_secret
            )
            result = await connector.test_connection()
        
        # RabbitMQ
        elif connection.datasource_type == "rabbitmq":
            connector = RabbitMQConnector()
            config = {
                'host': connection.host,
                'port': connection.port or 15672,
                'username': connection.username,
                'password': connection.password,
                'vhost': getattr(connection, 'vhost', '/'),
                'use_ssl': connection.ssl
            }
            result = await connector.test_connection(config)
        
        # Kafka
        elif connection.datasource_type == "kafka":
            connector = KafkaConnector()
            config = {
                'bootstrap_servers': connection.host,  # Expected format: 'host:port,host:port'
                'security_protocol': getattr(connection, 'security_protocol', 'PLAINTEXT'),
                'sasl_mechanism': getattr(connection, 'sasl_mechanism', 'PLAIN'),
                'sasl_username': connection.username,
                'sasl_password': connection.password,
                'ssl_check_hostname': getattr(connection, 'ssl_check_hostname', True)
            }
            result = await connector.test_connection(config)
        
        # MQTT
        elif connection.datasource_type == "mqtt":
            connector = MQTTConnector()
            config = {
                'host': connection.host,
                'port': connection.port or 1883,
                'username': connection.username,
                'password': connection.password,
                'client_id': getattr(connection, 'client_id', 'rhinometric-connector'),
                'use_tls': connection.ssl,
                'keepalive': getattr(connection, 'keepalive', 60),
                'clean_session': getattr(connection, 'clean_session', True),
                'test_topic': getattr(connection, 'test_topic', 'rhinometric/test')
            }
            result = await connector.test_connection(config)
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported datasource type: {connection.datasource_type}"
            )
        
        # Calcular duración
        duration = (datetime.now() - start_time).total_seconds() * 1000
        
        return TestResult(
            success=result["success"],
            message=result["message"],
            details=result.get("details"),
            duration_ms=duration
        )
    
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"Connection test failed: {str(e)}")
        
        return TestResult(
            success=False,
            message=f"Connection failed: {str(e)}",
            details={"error": str(e)},
            duration_ms=duration
        )


@app.post("/api/datasources")
async def create_datasource(datasource: DatasourceConfig, db: Session = Depends(get_db)):
    """Crear un nuevo datasource (solo en PostgreSQL, NO en Grafana)."""
    logger.info(f"Creating datasource: {datasource.name}")
    
    # Verificar si ya existe
    existing = db.query(DatasourceModel).filter(DatasourceModel.name == datasource.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Datasource '{datasource.name}' already exists")
    
    datasource_db = DatasourceModel(
        name=datasource.name,
        type=datasource.type,
        config=datasource.config,
        enabled=datasource.enabled,
        tags=datasource.tags
    )
    
    db.add(datasource_db)
    db.commit()
    db.refresh(datasource_db)
    
    return {
        "success": True,
        "message": f"Datasource '{datasource.name}' created successfully",
        "datasource_id": datasource_db.id
    }


@app.get("/api/datasources")
async def list_datasources(db: Session = Depends(get_db)):
    """Listar todos los datasources configurados."""
    datasources = db.query(DatasourceModel).all()
    
    return {
        "datasources": [
            {
                "id": ds.id,
                "name": ds.name,
                "type": ds.type,
                "enabled": ds.enabled,
                "grafana_uid": ds.grafana_uid,
                "grafana_id": ds.grafana_id,
                "tags": ds.tags,
                "created_at": ds.created_at.isoformat() if ds.created_at else None
            }
            for ds in datasources
        ],
        "count": len(datasources)
    }


@app.get("/api/datasources/{datasource_id}")
async def get_datasource(datasource_id: int, db: Session = Depends(get_db)):
    """Obtener un datasource específico."""
    datasource = db.query(DatasourceModel).filter(DatasourceModel.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="Datasource not found")
    
    return {
        "id": datasource.id,
        "name": datasource.name,
        "type": datasource.type,
        "config": datasource.config,
        "enabled": datasource.enabled,
        "grafana_uid": datasource.grafana_uid,
        "grafana_id": datasource.grafana_id,
        "tags": datasource.tags,
        "created_at": datasource.created_at.isoformat() if datasource.created_at else None,
        "updated_at": datasource.updated_at.isoformat() if datasource.updated_at else None
    }


@app.put("/api/datasources/{datasource_id}")
async def update_datasource(datasource_id: int, datasource: DatasourceConfig, db: Session = Depends(get_db)):
    """Actualizar un datasource existente."""
    datasource_db = db.query(DatasourceModel).filter(DatasourceModel.id == datasource_id).first()
    if not datasource_db:
        raise HTTPException(status_code=404, detail="Datasource not found")
    
    datasource_db.name = datasource.name
    datasource_db.type = datasource.type
    datasource_db.config = datasource.config
    datasource_db.enabled = datasource.enabled
    datasource_db.tags = datasource.tags
    datasource_db.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Datasource '{datasource_id}' updated successfully"
    }


@app.delete("/api/datasources/{datasource_id}")
async def delete_datasource(datasource_id: str, db: Session = Depends(get_db)):
    """Eliminar un datasource."""
    datasource = db.query(DatasourceModel).filter(DatasourceModel.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="Datasource not found")
    
    # TODO: También eliminar de Grafana si existe grafana_id
    
    db.delete(datasource)
    db.commit()
    
    return {
        "success": True,
        "message": f"Datasource '{datasource.name}' deleted successfully"
    }


@app.post("/api/datasources/grafana/create")
async def create_grafana_datasource(payload: GrafanaDatasourceCreate, db: Session = Depends(get_db)):
    """
    ENDPOINT CRÍTICO: Crear datasource en Grafana y PostgreSQL.
    
    Este endpoint:
    1. Valida la configuración
    2. Crea el datasource en Grafana via API
    3. Guarda la referencia en PostgreSQL
    4. Retorna el datasource creado
    
    Requiere: GRAFANA_API_TOKEN configurado
    """
    if not GRAFANA_API_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="GRAFANA_API_TOKEN not configured. Please set environment variable."
        )
    
    logger.info(f"Creating datasource '{payload.name}' in Grafana")
    
    try:
        # Mapear tipo a tipo de Grafana
        grafana_type_map = {
            "postgresql": "postgres",
            "redis": "redis-datasource",  # Requiere plugin
            "prometheus": "prometheus",
            "aws-cloudwatch": "cloudwatch",
            "azure-monitor": "grafana-azure-monitor-datasource",
            "rabbitmq": "simpod-json-datasource",  # Requiere plugin JSON
            "kafka": "hamedkarbasi93-kafka-datasource",  # Requiere plugin
            "mqtt": "simpod-json-datasource"  # Via JSON datasource
        }
        
        grafana_type = grafana_type_map.get(payload.type, payload.type)
        
        # Preparar payload para Grafana
        grafana_payload = {
            "name": payload.name,
            "type": grafana_type,
            "access": "proxy",
            "isDefault": payload.is_default,
            "jsonData": {},
            "secureJsonData": {}
        }
        
        # Configuración específica por tipo
        if payload.type == "postgresql":
            grafana_payload["url"] = f"{payload.config.get('host', 'localhost')}:{payload.config.get('port', 5432)}"
            grafana_payload["database"] = payload.config.get("database", "")
            grafana_payload["user"] = payload.config.get("username", "")
            grafana_payload["secureJsonData"]["password"] = payload.config.get("password", "")
            grafana_payload["jsonData"]["sslmode"] = "require" if payload.config.get("ssl", False) else "disable"
            grafana_payload["jsonData"]["postgresVersion"] = 1400  # PostgreSQL 14+
        
        elif payload.type == "prometheus":
            grafana_payload["url"] = payload.config.get("url", "http://localhost:9090")
            grafana_payload["jsonData"]["timeInterval"] = "30s"
        
        elif payload.type == "redis":
            grafana_payload["url"] = f"redis://{payload.config.get('host', 'localhost')}:{payload.config.get('port', 6379)}"
            if payload.config.get("password"):
                grafana_payload["secureJsonData"]["password"] = payload.config["password"]
        
        elif payload.type == "aws-cloudwatch":
            grafana_payload["jsonData"]["authType"] = "keys"
            grafana_payload["jsonData"]["defaultRegion"] = payload.config.get("region", "us-east-1")
            grafana_payload["secureJsonData"]["accessKey"] = payload.config.get("access_key", "")
            grafana_payload["secureJsonData"]["secretKey"] = payload.config.get("secret_key", "")
        
        elif payload.type == "azure-monitor":
            grafana_payload["jsonData"]["subscriptionId"] = payload.config.get("subscription_id", "")
            grafana_payload["jsonData"]["tenantId"] = payload.config.get("tenant_id", "")
            grafana_payload["jsonData"]["clientId"] = payload.config.get("client_id", "")
            grafana_payload["secureJsonData"]["clientSecret"] = payload.config.get("client_secret", "")
        
        # Para messaging (RabbitMQ, Kafka, MQTT) usar JSON datasource genérico
        elif payload.type in ["rabbitmq", "kafka", "mqtt"]:
            # Estos requieren plugins especializados o JSON datasource
            grafana_payload["type"] = "simpod-json-datasource"
            grafana_payload["url"] = f"http://localhost:8000/api/datasources/{payload.type}/proxy"
            logger.warning(f"{payload.type} requires specialized plugin or JSON datasource")
        
        # Llamar a Grafana API
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {GRAFANA_API_TOKEN}",
                "Content-Type": "application/json"
            }
            
            response = await client.post(
                f"{GRAFANA_URL}/api/datasources",
                json=grafana_payload,
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                grafana_response = response.json()
                
                # Guardar en PostgreSQL
                datasource_db = DatasourceModel(
                    name=payload.name,
                    type=payload.type,
                    config=payload.config,
                    grafana_uid=grafana_response.get("datasource", {}).get("uid"),
                    grafana_id=grafana_response.get("datasource", {}).get("id"),
                    enabled=True,
                    tags=payload.tags
                )
                
                db.add(datasource_db)
                db.commit()
                db.refresh(datasource_db)
                
                logger.info(f"✅ Datasource '{payload.name}' created successfully in Grafana (ID: {grafana_response.get('id')})")
                
                return {
                    "success": True,
                    "message": f"Datasource '{payload.name}' created successfully in Grafana",
                    "grafana_response": grafana_response,
                    "datasource_id": datasource_db.id,
                    "grafana_uid": datasource_db.grafana_uid
                }
            
            else:
                error_detail = response.json() if response.text else {}
                logger.error(f"❌ Grafana API error: {response.status_code} - {error_detail}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Grafana API error: {error_detail.get('message', response.text)}"
                )
    
    except httpx.HTTPError as e:
        logger.error(f"HTTP error calling Grafana API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error connecting to Grafana: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error creating datasource: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating datasource: {str(e)}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
