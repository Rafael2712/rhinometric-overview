#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
 RHINOMETRIC LICENSE SERVER v2.1.0 - FASTAPI EDITION
═══════════════════════════════════════════════════════════════════════════

Rewritten from Flask to FastAPI for:
- Async/await support
- Better performance
- Automatic OpenAPI docs
- Type safety with Pydantic
- Production-ready features

Endpoints:
  GET  /api/health          - Health check
  GET  /api/metrics         - Prometheus metrics
  GET  /api/licenses        - List all licenses
  POST /api/licenses        - Create license
  GET  /api/licenses/{id}   - Get license details
  GET  /api/external-apis   - List configured APIs
  POST /api/external-apis   - Add new API connection

═══════════════════════════════════════════════════════════════════════════
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from prometheus_fastapi_instrumentator import Instrumentator
import asyncpg
import redis.asyncio as aioredis
import httpx
import os
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from pathlib import Path
import asyncio

# Import email utilities
from utils.email_sender import send_license_email_with_attachments, generate_license_key

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Create logs directory if it doesn't exist
LOG_DIR = Path("/app/logs")
LOG_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "license_mail.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("rhinometric.email")

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rhinometric:rhinometric@postgres:5432/rhinometric_trial"
)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Server base URL for download links in emails
SERVER_BASE_URL = os.getenv("SERVER_BASE_URL", "http://licensing.rhinometric.com:5000")

# Security: Determine if running in trial mode
RHINOMETRIC_MODE = os.getenv("RHINOMETRIC_MODE", "trial")
IS_TRIAL = RHINOMETRIC_MODE == "trial"

# Email Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.zoho.eu")  # Zoho Europe
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))  # SSL port
SMTP_USER = os.getenv("SMTP_USER", "rafael.canelon@rhinometric.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # App password from Zoho
SMTP_FROM = os.getenv("SMTP_FROM", "rafael.canelon@rhinometric.com")

# PDF Documentation paths
DOCS_DIR = Path("/app/docs")
PDF_MANUAL_USER = DOCS_DIR / "manual_usuario.pdf"
PDF_PRIVACY_GDPR = DOCS_DIR / "politica_privacidad_GDPR.pdf"  # PENDIENTE: Legal review
PDF_INSTALL_GUIDE = DOCS_DIR / "guia_instalacion.pdf"

# Download files paths
DOWNLOADS_DIR = Path("/app/static/downloads")
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

DEMO_OVA_FILE = DOWNLOADS_DIR / "rhinometric-demo-2.5.0.ova"
TRIAL_INSTALLER_FILE = DOWNLOADS_DIR / "rhinometric-trial-2.5.0-install.sh"

# Documentation PDFs (ES/EN)
DOCS_DIR_ES = Path("/app/static/docs/es")
DOCS_DIR_EN = Path("/app/static/docs/en")
DOCS_DIR_ES.mkdir(parents=True, exist_ok=True)
DOCS_DIR_EN.mkdir(parents=True, exist_ok=True)

INSTALL_GUIDE_ES = DOCS_DIR_ES / "rhinometric-installation-guide-es.pdf"
INSTALL_GUIDE_EN = DOCS_DIR_EN / "rhinometric-installation-guide-en.pdf"
USER_MANUAL_ES = DOCS_DIR_ES / "rhinometric-user-manual-es.pdf"
USER_MANUAL_EN = DOCS_DIR_EN / "rhinometric-user-manual-en.pdf"

# ═══════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════

class HealthResponse(BaseModel):
    status: str
    version: str
    service: str
    timestamp: datetime
    database: str
    redis: str

class License(BaseModel):
    id: Optional[int] = None
    customer_name: str = Field(..., min_length=1, max_length=255)
    license_key: str = Field(..., min_length=10)
    created_at: Optional[datetime] = None
    expires_at: datetime
    is_active: bool = True

class ExternalAPI(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    endpoint: str = Field(..., min_length=10)
    auth_type: Optional[str] = "none"
    auth_token: Optional[str] = None
    scrape_interval: int = Field(default=60, ge=10, le=3600)
    is_active: bool = True
    created_at: Optional[datetime] = None

class LicenseCreateRequest(BaseModel):
    """Model for creating a new license with full client details"""
    customer_name: str = Field(..., min_length=1)
    client_email: EmailStr
    client_company: Optional[str] = ""  # Opcional
    client_phone: Optional[str] = None
    client_country: Optional[str] = None
    client_city: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    servers_count: Optional[int] = None
    services_count: Optional[int] = None
    infrastructure_type: Optional[str] = None
    notes: Optional[str] = None
    license_type: str = Field(..., pattern="^(trial|annual|permanent)$")

class LicenseResponse(BaseModel):
    """Response model with full license details"""
    id: int
    customer_name: str
    license_key: str
    license_type: str
    client_email: str
    client_company: str
    status: str
    created_at: datetime
    expires_at: Optional[datetime]
    days_remaining: Optional[int]
    is_active: bool
    email_sent: bool = False

class LicenseValidateRequest(BaseModel):
    """Request model for license validation"""
    license_key: str = Field(..., min_length=10)
    hardware_id: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    client_info: Optional[dict] = {}

class LicenseValidateResponse(BaseModel):
    """Response model for license validation"""
    valid: bool
    license_id: Optional[int] = None
    customer_name: Optional[str] = None
    license_type: Optional[str] = None
    expires_at: Optional[datetime] = None
    days_remaining: Optional[int] = None
    download_allowed: bool = False
    download_url: Optional[str] = None
    activation_id: Optional[int] = None
    message: str
    deployment_mode: str = "ON_PREMISE"  # ON_PREMISE or SAAS_SINGLE_TENANT

class LicenseActivation(BaseModel):
    """License activation record"""
    id: int
    license_id: int
    license_key: str
    activated_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    hardware_id: Optional[str]
    hostname: Optional[str]
    download_allowed: bool
    download_completed: bool
    validation_status: str
    error_message: Optional[str]

# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Rhinometric License Server",
    description="FastAPI-based license management and API connector for Rhinometric v2.1.0",
    version="2.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/api/metrics")

# ═══════════════════════════════════════════════════════════════════════════
# DATABASE CONNECTION
# ═══════════════════════════════════════════════════════════════════════════

db_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[aioredis.Redis] = None

@app.on_event("startup")
async def startup():
    global db_pool, redis_client
    
    # Connect to PostgreSQL
    try:
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=10
        )
        print("✓ Connected to PostgreSQL")
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        db_pool = None
    
    # Connect to Redis
    try:
        redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        print("✓ Connected to Redis")
    except Exception as e:
        print(f"⚠ Redis connection failed: {e}")
        redis_client = None

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()

# ═══════════════════════════════════════════════════════════════════════════
# DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════════════

async def get_db():
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    async with db_pool.acquire() as connection:
        yield connection

async def require_admin_mode():
    """Dependency to check if admin features are available (not in trial mode)"""
    if IS_TRIAL:
        raise HTTPException(
            status_code=403,
            detail="This feature is not available in trial mode. License management is reserved for administrators."
        )

# ═══════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    
    # Check database
    db_status = "connected"
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
        else:
            db_status = "disconnected"
    except Exception:
        db_status = "error"
    
    # Check Redis
    redis_status = "connected"
    try:
        if redis_client:
            await redis_client.ping()
        else:
            redis_status = "disconnected"
    except Exception:
        redis_status = "error"
    
    return HealthResponse(
        status="healthy",
        version="2.1.0",
        service="license-server",
        timestamp=datetime.utcnow(),
        database=db_status,
        redis=redis_status
    )

# ═══════════════════════════════════════════════════════════════════════════
# LICENSE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/licenses", response_model=List[License], dependencies=[Depends(require_admin_mode)])
async def list_licenses(conn = Depends(get_db)):
    """List all licenses (Admin only - disabled in trial mode)"""
    
    rows = await conn.fetch("""
        SELECT id, customer_name, license_key, created_at, expires_at, is_active
        FROM licenses
        ORDER BY created_at DESC
    """)
    
    return [License(**dict(row)) for row in rows]

@app.post("/api/licenses", response_model=License, status_code=201, dependencies=[Depends(require_admin_mode)])
async def create_license(license: License, conn = Depends(get_db)):
    """Create a new license (Admin only - disabled in trial mode)"""
    
    row = await conn.fetchrow("""
        INSERT INTO licenses (customer_name, license_key, expires_at, is_active)
        VALUES ($1, $2, $3, $4)
        RETURNING id, customer_name, license_key, created_at, expires_at, is_active
    """, license.customer_name, license.license_key, license.expires_at, license.is_active)
    
    return License(**dict(row))

@app.get("/api/licenses/{license_id}", response_model=License, dependencies=[Depends(require_admin_mode)])
async def get_license(license_id: int, conn = Depends(get_db)):
    """Get license details (Admin only - disabled in trial mode)"""
    
    row = await conn.fetchrow("""
        SELECT id, customer_name, license_key, created_at, expires_at, is_active
        FROM licenses
        WHERE id = $1
    """, license_id)
    
    if not row:
        raise HTTPException(status_code=404, detail="License not found")
    
    return License(**dict(row))

@app.get("/api/license/status")
async def get_trial_status():
    """Get current license status (Read-only, available in trial mode)"""
    
    if IS_TRIAL:
        return {
            "mode": "trial",
            "expires_at": "2025-11-28",
            "days_remaining": 14,
            "features": {
                "monitoring": True,
                "api_connector": True,
                "alerting": True,
                "drilldown": True,
                "auto_updates": True,
                "license_management": False
            },
            "message": "You are using Rhinometric v2.1.0 Trial Edition"
        }
    else:
        return {
            "mode": "enterprise",
            "features": {
                "monitoring": True,
                "api_connector": True,
                "alerting": True,
                "drilldown": True,
                "auto_updates": True,
                "license_management": True
            },
            "message": "Rhinometric Enterprise Edition"
        }

# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def generate_license_key(license_type: str) -> str:
    """Generate a unique license key"""
    prefix = {
        "trial": "TRIAL",
        "annual": "ANNUAL",
        "permanent": "PERM"
    }.get(license_type, "TRIAL")
    
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
    return f"RHINO-{prefix}-{datetime.now().year}-{random_part}"

def get_installation_instructions(license_type: str, license_key: str) -> str:
    """Generate installation instructions based on license type"""
    duration_text = {
        "trial": "30 días",
        "annual": "1 año",
        "permanent": "permanente (sin expiración)"
    }.get(license_type, "30 días")
    
    return f"""
╔══════════════════════════════════════════════════════════════════╗
║          RHINOMETRIC v2.1.0 - LICENCIA {license_type.upper()}           ║
╚══════════════════════════════════════════════════════════════════╝

Gracias por elegir Rhinometric, la plataforma completa de monitoreo
observability para tu infraestructura.

📋 TU LICENCIA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tipo de licencia: {license_type.upper()}
Duración: {duration_text}
Clave de licencia: {license_key}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 INSTALACIÓN RÁPIDA:

1. Descarga el paquete de instalación:
   wget https://releases.rhinometric.com/v2.1.0/rhinometric-trial-v2.1.0-universal.tar.gz

2. Extrae el archivo:
   tar -xzf rhinometric-trial-v2.1.0-universal.tar.gz
   cd rhinometric-trial-v2.1.0-universal

3. Crea tu archivo de licencia:
   echo "{license_key}" > license.lic

4. Inicia Rhinometric:
   docker compose -f docker-compose-v2.1.0.yml up -d

5. Accede a la plataforma:
   • Grafana: http://localhost:3000 (admin/rhinometric)
   • API Connector: http://localhost:8091
   • License Management: http://localhost:8092
   • Prometheus: http://localhost:9090
   • Loki: http://localhost:3100
   • Tempo: http://localhost:3200

📦 COMPONENTES INCLUIDOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Grafana con dashboards pre-configurados
✅ Prometheus para métricas
✅ Loki para logs centralizados
✅ Tempo para trazas distribuidas
✅ Drilldown completo (métricas → logs → trazas)
✅ API Connector para integraciones externas
✅ Alertas automáticas
✅ PostgreSQL + Redis optimizados
✅ High Availability (HA)

📚 DOCUMENTACIÓN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Guía de inicio rápido: docs/QUICK_START.md
• Instalación Windows: docs/INSTALACION_WINDOWS_SIMPLE.md
• Instalación Linux/Mac: docs/INSTALACION_LINUX_MAC.md
• Arquitectura: docs/RESUMEN_EJECUTIVO_v2.1.0.md
• Dashboards: docs/DASHBOARDS_QUICKSTART.md

🆘 SOPORTE TÉCNICO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Email: rafael.canelon@rhinometric.com
Respuesta en 24-48 horas

⚙️ REQUISITOS DEL SISTEMA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Docker 24.0+ y Docker Compose v2
• 4 GB RAM mínimo (8 GB recomendado)
• 10 GB espacio en disco
• Puertos: 3000, 8091, 8092, 9090, 3100, 3200, 5000

🎯 PRÓXIMOS PASOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Completa la instalación siguiendo los pasos anteriores
2. Explora los dashboards pre-configurados en Grafana
3. Conecta tus APIs externas desde el API Connector
4. Configura alertas personalizadas
5. Revisa la documentación para funciones avanzadas

¿Necesitas ayuda? Contáctanos en rafael.canelon@rhinometric.com

Saludos,
El equipo de Rhinometric
"""

async def send_license_email(to_email: str, customer_name: str, license_key: str, license_type: str) -> bool:
    """Send license email to customer via Zoho Mail"""
    if not SMTP_PASSWORD:
        print("⚠️  SMTP_PASSWORD no configurado. Email no enviado.")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Tu licencia Rhinometric {license_type.upper()} está lista"
        msg['From'] = SMTP_FROM
        msg['To'] = to_email
        
        instructions = get_installation_instructions(license_type, license_key)
        
        text_part = MIMEText(instructions, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # Try STARTTLS first (port 587)
        try:
            print(f"🔄 Intentando enviar email a {to_email} via STARTTLS...")
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.set_debuglevel(0)
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"✅ Email enviado exitosamente a {to_email}")
            return True
            
        except Exception as e1:
            print(f"⚠️  STARTTLS falló: {e1}")
            
            # Try SSL/TLS (port 465) as fallback
            print(f"🔄 Intentando con SSL/TLS (puerto 465)...")
            with smtplib.SMTP_SSL(SMTP_HOST, 465, timeout=30) as server:
                server.set_debuglevel(0)
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"✅ Email enviado exitosamente a {to_email} (SSL/TLS)")
            return True
        
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        print(f"   Host: {SMTP_HOST}, Port: {SMTP_PORT}, User: {SMTP_USER}")
        return False

# ═══════════════════════════════════════════════════════════════════════════
# DEMO LICENSE MANAGEMENT (Available in Trial Mode for UI Testing)
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/demo/licenses")
async def demo_list_licenses():
    """Demo endpoint: Returns sample licenses for UI testing (trial mode only)"""
    if not IS_TRIAL:
        return {"message": "Use /api/licenses for production"}
    
    return [
        {
            "id": 1,
            "customer_name": "Empresa Demo S.A.",
            "license_key": "DEMO-TRIAL-2025-ABC123",
            "license_type": "trial",
            "status": "active",
            "created_at": "2025-10-01T10:00:00Z",
            "expires_at": "2025-10-31T23:59:59Z",
            "days_remaining": 30,
            "client_email": "demo@empresa.com",
            "client_company": "Empresa Demo S.A.",
            "is_active": True
        },
        {
            "id": 2,
            "customer_name": "Tech Solutions Corp",
            "license_key": "DEMO-ANNUAL-2025-XYZ789",
            "license_type": "annual",
            "status": "active",
            "created_at": "2025-01-10T08:00:00Z",
            "expires_at": "2026-01-10T23:59:59Z",
            "days_remaining": 74,
            "client_email": "contact@techsolutions.com",
            "client_company": "Tech Solutions Corp",
            "is_active": True
        },
        {
            "id": 3,
            "customer_name": "Global Services Inc",
            "license_key": "DEMO-PERMANENT-2024-PQR456",
            "license_type": "permanent",
            "status": "active",
            "created_at": "2024-06-01T12:00:00Z",
            "expires_at": None,
            "days_remaining": None,
            "client_email": "admin@globalservices.com",
            "client_company": "Global Services Inc",
            "is_active": True
        }
    ]

@app.post("/api/demo/licenses")
async def demo_create_license(license_data: dict):
    """Demo endpoint: Simulates license creation (trial mode only)"""
    if not IS_TRIAL:
        return {"message": "Use /api/licenses for production"}
    
    return {
        "success": True,
        "message": "Licencia demo creada exitosamente",
        "license": {
            "id": 999,
            "customer_name": license_data.get("customer_name", "Cliente Demo"),
            "license_key": f"DEMO-{license_data.get('license_type', 'trial').upper()}-2025-XXXYYY",
            "license_type": license_data.get("license_type", "trial"),
            "status": "active",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z" if license_data.get("license_type") != "permanent" else None,
            "client_email": license_data.get("client_email", "demo@ejemplo.com"),
            "client_company": license_data.get("client_company", "Empresa Demo"),
            "is_active": True
        }
    }

@app.get("/api/demo/licenses/stats")
async def demo_license_stats():
    """Demo endpoint: Returns sample statistics (trial mode only)"""
    if not IS_TRIAL:
        return {"message": "Use /api/admin/licenses/stats for production"}
    
    return {
        "total_licenses": 3,
        "active_licenses": 3,
        "expiring_soon": 1,
        "active_trials": 1,
        "permanent_licenses": 1,
        "revenue_annual": "A consultar",
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }

# ═══════════════════════════════════════════════════════════════════════════
# REAL LICENSE MANAGEMENT (Works in ALL modes - no trial restriction)
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/admin/licenses", response_model=LicenseResponse, status_code=201)
async def create_real_license(request: LicenseCreateRequest, conn = Depends(get_db)):
    """
    Create a new license (Works in trial AND production mode)
    Generates license key, saves to database, sends email to customer
    """
    
    # Generate unique license key
    license_key = generate_license_key(request.license_type)
    
    # Calculate expiry date
    if request.license_type == "trial":
        expires_at = datetime.utcnow() + timedelta(days=30)
    elif request.license_type == "annual":
        expires_at = datetime.utcnow() + timedelta(days=365)
    else:  # permanent
        expires_at = datetime.utcnow() + timedelta(days=365 * 100)  # 100 años
    
    # Insert into database
    try:
        row = await conn.fetchrow("""
            INSERT INTO licenses (customer_name, license_key, expires_at, is_active)
            VALUES ($1, $2, $3, $4)
            RETURNING id, customer_name, license_key, created_at, expires_at, is_active
        """, request.customer_name, license_key, expires_at, True)
        
        # Send email with PDF attachments (don't block on failure)
        email_sent = await send_license_email_with_attachments(
            to_email=request.client_email,
            customer_name=request.customer_name,
            license_key=license_key,
            license_type=request.license_type,
            expires_at=expires_at,
            smtp_host=SMTP_HOST,
            smtp_port=SMTP_PORT,
            smtp_user=SMTP_USER,
            smtp_password=SMTP_PASSWORD,
            smtp_from=SMTP_FROM,
            client_company=request.client_company,
            docs_dir=DOCS_DIR,
            server_base_url=SERVER_BASE_URL
        )
        
        # Calculate days remaining
        days_remaining = None
        if request.license_type != "permanent":
            days_remaining = (expires_at - datetime.utcnow()).days
        
        return LicenseResponse(
            id=row['id'],
            customer_name=row['customer_name'],
            license_key=row['license_key'],
            license_type=request.license_type,
            client_email=request.client_email,
            client_company=request.client_company,
            status="active",
            created_at=row['created_at'],
            expires_at=row['expires_at'] if request.license_type != "permanent" else None,
            days_remaining=days_remaining,
            is_active=row['is_active'],
            email_sent=email_sent
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating license: {str(e)}")

@app.get("/api/admin/licenses", response_model=List[LicenseResponse])
async def list_real_licenses(conn = Depends(get_db)):
    """List all licenses from database (Works in all modes)"""
    
    try:
        rows = await conn.fetch("""
            SELECT id, customer_name, license_key, created_at, expires_at, is_active
            FROM licenses
            ORDER BY created_at DESC
        """)
        
        licenses = []
        for row in rows:
            # Intentar determinar el tipo por el prefijo de la clave
            license_key = row['license_key']
            if 'TRIAL' in license_key:
                license_type = 'trial'
            elif 'ANNUAL' in license_key:
                license_type = 'annual'
            elif 'PERM' in license_key:
                license_type = 'permanent'
            else:
                license_type = 'trial'  # default
            
            # Calculate status and days remaining
            expires_at = row['expires_at']
            is_active = row['is_active']
            
            if license_type == 'permanent':
                status = 'active' if is_active else 'revoked'
                days_remaining = None
            else:
                days_remaining = (expires_at - datetime.utcnow()).days
                if not is_active:
                    status = 'revoked'
                elif days_remaining < 0:
                    status = 'expired'
                elif days_remaining <= 7:
                    status = 'expiring'
                else:
                    status = 'active'
            
            licenses.append(LicenseResponse(
                id=row['id'],
                customer_name=row['customer_name'],
                license_key=row['license_key'],
                license_type=license_type,
                client_email="",  # No guardado en DB actual
                client_company="",
                status=status,
                created_at=row['created_at'],
                expires_at=expires_at if license_type != 'permanent' else None,
                days_remaining=days_remaining,
                is_active=is_active,
                email_sent=False
            ))
        
        return licenses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching licenses: {str(e)}")

@app.get("/api/admin/licenses/stats")
async def get_real_license_stats(conn = Depends(get_db)):
    """
    Get comprehensive license statistics including activation metrics.
    
    Returns:
    - Total licenses created
    - Active/expired/revoked counts
    - Activation statistics (total, unique IPs, unique hardware)
    - Failed validation attempts
    - Revenue estimates
    """
    
    try:
        # License counts
        total = await conn.fetchval("SELECT COUNT(*) FROM licenses")
        active = await conn.fetchval("SELECT COUNT(*) FROM licenses WHERE is_active = true AND expires_at > NOW()")
        expired = await conn.fetchval("SELECT COUNT(*) FROM licenses WHERE expires_at < NOW()")
        revoked = await conn.fetchval("SELECT COUNT(*) FROM licenses WHERE is_active = false")
        expiring_soon = await conn.fetchval("""
            SELECT COUNT(*) FROM licenses 
            WHERE is_active = true AND expires_at BETWEEN NOW() AND NOW() + INTERVAL '7 days'
        """)
        
        # License types (estimate from key prefix)
        trial_count = await conn.fetchval("SELECT COUNT(*) FROM licenses WHERE license_key LIKE '%TRIAL%'")
        annual_count = await conn.fetchval("SELECT COUNT(*) FROM licenses WHERE license_key LIKE '%ANNUAL%'")
        permanent_count = await conn.fetchval("SELECT COUNT(*) FROM licenses WHERE license_key LIKE '%PERM%'")
        
        # Activation statistics
        total_activations = await conn.fetchval("SELECT COUNT(*) FROM license_activations") or 0
        unique_ips = await conn.fetchval("SELECT COUNT(DISTINCT ip_address) FROM license_activations") or 0
        unique_hardware = await conn.fetchval("SELECT COUNT(DISTINCT hardware_id) FROM license_activations WHERE hardware_id IS NOT NULL") or 0
        activations_today = await conn.fetchval("""
            SELECT COUNT(*) FROM license_activations 
            WHERE activated_at > NOW() - INTERVAL '24 hours'
        """) or 0
        
        # Failed attempts (security)
        failed_attempts_today = await conn.fetchval("""
            SELECT COUNT(*) FROM license_validation_failures
            WHERE attempted_at > NOW() - INTERVAL '24 hours'
        """) or 0
        
        failed_attempts_total = await conn.fetchval("SELECT COUNT(*) FROM license_validation_failures") or 0
        
        # Most active licenses (top 5)
        top_licenses = await conn.fetch("""
            SELECT 
                l.license_key,
                l.customer_name,
                COUNT(la.id) as activation_count
            FROM licenses l
            LEFT JOIN license_activations la ON l.id = la.license_id
            GROUP BY l.id, l.license_key, l.customer_name
            ORDER BY activation_count DESC
            LIMIT 5
        """)
        
        return {
            "licenses": {
                "total": total,
                "active": active,
                "expired": expired,
                "revoked": revoked,
                "expiring_soon": expiring_soon,
                "by_type": {
                    "trial": trial_count,
                    "annual": annual_count,
                    "permanent": permanent_count
                }
            },
            "activations": {
                "total": total_activations,
                "unique_ips": unique_ips,
                "unique_hardware": unique_hardware,
                "today": activations_today,
                "avg_per_license": round(total_activations / total, 2) if total > 0 else 0
            },
            "security": {
                "failed_attempts_today": failed_attempts_today,
                "failed_attempts_total": failed_attempts_total,
                "success_rate": round((total_activations / (total_activations + failed_attempts_total) * 100), 2) if (total_activations + failed_attempts_total) > 0 else 100
            },
            "top_licenses": [
                {
                    "license_key": row['license_key'],
                    "customer_name": row['customer_name'],
                    "activations": row['activation_count']
                }
                for row in top_licenses
            ],
            "revenue_estimate": {
                "annual": f"${annual_count * 1999} USD/year (estimate)",
                "note": "Based on $1999/license standard pricing"
            },
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════
# EXTERNAL API MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/external-apis", response_model=List[ExternalAPI])
async def list_external_apis(conn = Depends(get_db)):
    """List all configured external APIs"""
    
    rows = await conn.fetch("""
        SELECT id, name, endpoint, auth_type, auth_token, scrape_interval, is_active, created_at
        FROM external_apis
        ORDER BY created_at DESC
    """)
    
    return [ExternalAPI(**dict(row)) for row in rows]

@app.post("/api/external-apis", response_model=ExternalAPI, status_code=201)
async def create_external_api(api: ExternalAPI, conn = Depends(get_db)):
    """Add new external API connection"""
    
    # Test connectivity
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(api.endpoint)
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=400,
                    detail=f"API returned status {response.status_code}"
                )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot connect to API: {str(e)}"
        )
    
    # Save to database
    row = await conn.fetchrow("""
        INSERT INTO external_apis (name, endpoint, auth_type, auth_token, scrape_interval, is_active)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, name, endpoint, auth_type, auth_token, scrape_interval, is_active, created_at
    """, api.name, api.endpoint, api.auth_type, api.auth_token, api.scrape_interval, api.is_active)
    
    # Notify API proxy to reload config
    if redis_client:
        await redis_client.publish("api_config_reload", api.name)
    
    return ExternalAPI(**dict(row))

@app.delete("/api/external-apis/{api_id}", status_code=204)
async def delete_external_api(api_id: int, conn = Depends(get_db)):
    """Delete external API connection"""
    
    result = await conn.execute("DELETE FROM external_apis WHERE id = $1", api_id)
    
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="API not found")
    
    return None

# ═══════════════════════════════════════════════════════════════════════════
# LICENSE VALIDATION AND ACTIVATION CONTROL
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/licenses/validate", response_model=LicenseValidateResponse)
async def validate_license(request: LicenseValidateRequest, conn = Depends(get_db)):
    """
    Validate a license key and register activation attempt.
    
    This endpoint controls who can download/activate Rhinometric:
    - Validates license exists and is active
    - Checks expiration date
    - Records activation in audit log
    - Returns download URL if valid
    - Blocks invalid/expired licenses
    
    Security: All attempts (success and failure) are logged.
    """
    
    try:
        # Query license details
        license_row = await conn.fetchrow("""
            SELECT id, customer_name, license_key, expires_at, is_active, client_email
            FROM licenses
            WHERE license_key = $1
        """, request.license_key)
        
        # License not found
        if not license_row:
            # Log failed attempt
            await conn.execute("""
                INSERT INTO license_validation_failures 
                (license_key, ip_address, user_agent, reason, hardware_id)
                VALUES ($1, $2, $3, $4, $5)
            """, request.license_key, request.ip_address, request.user_agent, 
                "License key not found", request.hardware_id)
            
            return LicenseValidateResponse(
                valid=False,
                download_allowed=False,
                message="Invalid license key. Please contact support@rhinometric.com"
            )
        
        # Check if license is active
        if not license_row['is_active']:
            await conn.execute("""
                INSERT INTO license_validation_failures 
                (license_key, ip_address, user_agent, reason, hardware_id)
                VALUES ($1, $2, $3, $4, $5)
            """, request.license_key, request.ip_address, request.user_agent,
                "License revoked", request.hardware_id)
            
            return LicenseValidateResponse(
                valid=False,
                license_id=license_row['id'],
                customer_name=license_row['customer_name'],
                download_allowed=False,
                message="This license has been revoked. Contact support for assistance."
            )
        
        # Check expiration
        expires_at = license_row['expires_at']
        now = datetime.utcnow()
        
        if expires_at < now:
            await conn.execute("""
                INSERT INTO license_validation_failures 
                (license_key, ip_address, user_agent, reason, hardware_id)
                VALUES ($1, $2, $3, $4, $5)
            """, request.license_key, request.ip_address, request.user_agent,
                "License expired", request.hardware_id)
            
            return LicenseValidateResponse(
                valid=False,
                license_id=license_row['id'],
                customer_name=license_row['customer_name'],
                expires_at=expires_at,
                days_remaining=0,
                download_allowed=False,
                message=f"License expired on {expires_at.strftime('%Y-%m-%d')}. Renew at rhinometric.com"
            )
        
        # ✅ LICENSE IS VALID - Register activation
        days_remaining = (expires_at - now).days
        
        # Determine license type from key prefix
        license_key = license_row['license_key']
        if 'TRIAL' in license_key:
            license_type = 'trial'
        elif 'ANNUAL' in license_key:
            license_type = 'annual'
        elif 'PERM' in license_key:
            license_type = 'permanent'
        else:
            license_type = 'unknown'
        
        # Generate download URL (you can customize this)
        download_url = f"https://github.com/Rafael2712/rhinometric-overview/releases/latest/download/rhinometric-v2.1.0-stable.tar.gz"
        
        # Register successful activation
        import json as json_module
        activation_row = await conn.fetchrow("""
            INSERT INTO license_activations 
            (license_id, license_key, ip_address, user_agent, hardware_id, hostname,
             download_allowed, download_url, validation_status, client_info)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb)
            RETURNING id
        """, license_row['id'], request.license_key, request.ip_address, 
            request.user_agent, request.hardware_id, request.hostname,
            True, download_url, 'success', json_module.dumps(request.client_info or {}))
        
        # Update last_check in licenses table
        await conn.execute("""
            UPDATE licenses SET last_check = NOW() WHERE id = $1
        """, license_row['id'])
        
        logger.info(f"✅ License validated: {request.license_key} for {license_row['customer_name']}")
        
        return LicenseValidateResponse(
            valid=True,
            license_id=license_row['id'],
            customer_name=license_row['customer_name'],
            license_type=license_type,
            expires_at=expires_at,
            days_remaining=days_remaining if license_type != 'permanent' else None,
            download_allowed=True,
            download_url=download_url,
            activation_id=activation_row['id'],
            message=f"License valid. {days_remaining} days remaining." if license_type != 'permanent' else "Permanent license - no expiration."
        )
        
    except Exception as e:
        logger.error(f"❌ Error validating license: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

@app.get("/api/licenses/{license_key}/activations", response_model=List[LicenseActivation])
async def get_license_activations(license_key: str, conn = Depends(get_db)):
    """
    Get activation history for a specific license.
    
    Returns all activation attempts including:
    - Successful activations
    - IP addresses used
    - Hardware IDs
    - Download status
    """
    
    rows = await conn.fetch("""
        SELECT 
            id, license_id, license_key, activated_at,
            ip_address, user_agent, hardware_id, hostname,
            download_allowed, download_completed,
            validation_status, error_message
        FROM license_activations
        WHERE license_key = $1
        ORDER BY activated_at DESC
        LIMIT 100
    """, license_key)
    
    if not rows:
        raise HTTPException(status_code=404, detail="No activations found for this license")
    
    return [LicenseActivation(**dict(row)) for row in rows]

@app.get("/api/admin/licenses/security")
async def get_security_alerts(conn = Depends(get_db)):
    """
    Get security alerts for suspicious license activity.
    
    Detects:
    - Multiple IPs using same license
    - Multiple hardware IDs
    - Excessive activation attempts
    - Failed validation patterns
    """
    
    # Suspicious activations (from view)
    suspicious = await conn.fetch("""
        SELECT 
            license_key,
            COUNT(DISTINCT ip_address) as distinct_ips,
            COUNT(DISTINCT hardware_id) as distinct_hardware,
            COUNT(*) as total_activations,
            MAX(activated_at) as last_activation
        FROM license_activations
        WHERE activated_at > NOW() - INTERVAL '7 days'
        GROUP BY license_key
        HAVING COUNT(DISTINCT ip_address) > 5 
            OR COUNT(DISTINCT hardware_id) > 3 
            OR COUNT(*) > 10
        ORDER BY total_activations DESC
    """)
    
    # Failed attempts (potential attacks)
    failures = await conn.fetch("""
        SELECT 
            license_key,
            reason,
            COUNT(*) as attempt_count,
            COUNT(DISTINCT ip_address) as distinct_ips,
            MAX(attempted_at) as last_attempt
        FROM license_validation_failures
        WHERE attempted_at > NOW() - INTERVAL '24 hours'
        GROUP BY license_key, reason
        HAVING COUNT(*) > 5
        ORDER BY attempt_count DESC
        LIMIT 20
    """)
    
    return {
        "suspicious_activations": [dict(row) for row in suspicious],
        "failed_attempts": [dict(row) for row in failures],
        "alert_count": len(suspicious) + len(failures),
        "generated_at": datetime.utcnow().isoformat()
    }

@app.post("/api/admin/licenses/{license_key}/revoke")
async def revoke_license(license_key: str, reason: Optional[str] = None, conn = Depends(get_db)):
    """
    Revoke a license (set is_active = false).
    
    This will prevent future activations/downloads.
    Existing installations will continue working until expiration.
    """
    
    result = await conn.execute("""
        UPDATE licenses 
        SET is_active = false, updated_at = NOW()
        WHERE license_key = $1
    """, license_key)
    
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="License not found")
    
    # Log revocation
    await conn.execute("""
        INSERT INTO license_validation_failures 
        (license_key, reason, ip_address, user_agent)
        VALUES ($1, $2, $3, $4)
    """, license_key, f"License revoked: {reason or 'Admin action'}", "ADMIN", "REVOCATION")
    
    logger.warning(f"⚠️ License revoked: {license_key} - Reason: {reason}")
    
    return {
        "success": True,
        "license_key": license_key,
        "message": "License revoked successfully",
        "revoked_at": datetime.utcnow().isoformat()
    }

# ═══════════════════════════════════════════════════════════════════════════
# DOWNLOADS AND DOCUMENTATION ENDPOINTS (v2.5.0)
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/downloads/demo-ova")
async def download_demo_ova():
    """
    Download Rhinometric Demo OVA (4-hour evaluation)
    
    File served: rhinometric-demo-2.5.0.ova
    Expected size: ~2-4 GB
    Format: VirtualBox/VMware OVA
    License: demo_cloud (4 hours, up to 20 hosts)
    """
    
    if not DEMO_OVA_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Demo OVA file not found. Please contact support@rhinometric.com"
        )
    
    # Get file size for logging
    file_size_mb = DEMO_OVA_FILE.stat().st_size / (1024 * 1024)
    logger.info(f"📥 Serving Demo OVA download ({file_size_mb:.2f} MB)")
    
    # Stream large file to avoid memory issues
    def iterfile():
        with open(DEMO_OVA_FILE, mode="rb") as file_like:
            chunk_size = 8192 * 1024  # 8MB chunks
            while chunk := file_like.read(chunk_size):
                yield chunk
    
    headers = {
        "Content-Disposition": f'attachment; filename="rhinometric-demo-2.5.0.ova"',
        "Content-Type": "application/octet-stream",
        "X-Content-Type-Options": "nosniff"
    }
    
    return StreamingResponse(
        iterfile(),
        headers=headers,
        media_type="application/octet-stream"
    )

@app.get("/downloads/trial-installer")
async def download_trial_installer():
    """
    Download Rhinometric Trial Installer (14-day evaluation)
    
    File served: rhinometric-trial-2.5.0-install.sh
    Platform: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
    License: trial (14 days, up to 5 hosts)
    Requirements: Docker 24.0+, 8GB RAM, 20GB disk
    """
    
    if not TRIAL_INSTALLER_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Trial installer not found. Please contact support@rhinometric.com"
        )
    
    logger.info(f"📥 Serving Trial Installer download")
    
    return FileResponse(
        path=TRIAL_INSTALLER_FILE,
        filename="rhinometric-trial-2.5.0-install.sh",
        media_type="application/x-sh",
        headers={
            "Content-Disposition": 'attachment; filename="rhinometric-trial-2.5.0-install.sh"',
            "X-Content-Type-Options": "nosniff"
        }
    )

@app.get("/docs/installation-guide")
async def download_installation_guide(lang: str = "es"):
    """
    Download Installation Guide PDF
    
    Query parameters:
    - lang: 'es' (default) or 'en'
    
    Returns: PDF file with complete installation instructions
    """
    
    if lang.lower() == "en":
        pdf_file = INSTALL_GUIDE_EN
        filename = "rhinometric-installation-guide-en.pdf"
    else:
        pdf_file = INSTALL_GUIDE_ES
        filename = "rhinometric-installation-guide-es.pdf"
    
    if not pdf_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Installation guide ({lang}) not found. Please contact support@rhinometric.com"
        )
    
    logger.info(f"📚 Serving Installation Guide ({lang.upper()})")
    
    return FileResponse(
        path=pdf_file,
        filename=filename,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff"
        }
    )

@app.get("/docs/user-manual")
async def download_user_manual(lang: str = "es"):
    """
    Download User Manual PDF
    
    Query parameters:
    - lang: 'es' (default) or 'en'
    
    Returns: PDF file with complete user documentation
    """
    
    if lang.lower() == "en":
        pdf_file = USER_MANUAL_EN
        filename = "rhinometric-user-manual-en.pdf"
    else:
        pdf_file = USER_MANUAL_ES
        filename = "rhinometric-user-manual-es.pdf"
    
    if not pdf_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"User manual ({lang}) not found. Please contact support@rhinometric.com"
        )
    
    logger.info(f"📚 Serving User Manual ({lang.upper()})")
    
    return FileResponse(
        path=pdf_file,
        filename=filename,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff"
        }
    )

@app.get("/downloads/info")
async def downloads_info():
    """
    Get information about available downloads
    
    Returns file availability, sizes, and metadata
    """
    
    def get_file_info(file_path: Path, file_type: str, description: str):
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            return {
                "available": True,
                "type": file_type,
                "description": description,
                "size_mb": round(size_mb, 2),
                "path": str(file_path.name)
            }
        else:
            return {
                "available": False,
                "type": file_type,
                "description": description,
                "message": "File not yet deployed - contact support"
            }
    
    return {
        "downloads": {
            "demo_ova": get_file_info(
                DEMO_OVA_FILE,
                "Virtual Machine (OVA)",
                "4-hour demo for VirtualBox/VMware - ready to import and test"
            ),
            "trial_installer": get_file_info(
                TRIAL_INSTALLER_FILE,
                "Shell Script (.sh)",
                "14-day trial installer for Linux servers (Ubuntu/Debian/CentOS)"
            )
        },
        "documentation": {
            "installation_guide_es": get_file_info(
                INSTALL_GUIDE_ES,
                "PDF Document",
                "Guía completa de instalación en español"
            ),
            "installation_guide_en": get_file_info(
                INSTALL_GUIDE_EN,
                "PDF Document",
                "Complete installation guide in English"
            ),
            "user_manual_es": get_file_info(
                USER_MANUAL_ES,
                "PDF Document",
                "Manual de usuario de Rhinometric Console en español"
            ),
            "user_manual_en": get_file_info(
                USER_MANUAL_EN,
                "PDF Document",
                "Rhinometric Console user manual in English"
            )
        },
        "server_info": {
            "version": "2.5.0",
            "base_url": "http://[SERVER]:5000",
            "endpoints": {
                "demo_ova": "/downloads/demo-ova",
                "trial_installer": "/downloads/trial-installer",
                "installation_guide": "/docs/installation-guide?lang=es|en",
                "user_manual": "/docs/user-manual?lang=es|en"
            }
        }
    }

# ═══════════════════════════════════════════════════════════════════════════
# ROOT
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "service": "Rhinometric License Server",
        "version": "2.1.0",
        "docs": "/api/docs",
        "health": "/api/health",
        "admin": "/admin"
    }

# Serve Admin UI
@app.get("/admin")
async def admin_ui():
    """Serve the admin UI HTML page"""
    static_dir = Path(__file__).parent / "static"
    admin_file = static_dir / "index.html"
    if admin_file.exists():
        return FileResponse(admin_file)
    raise HTTPException(status_code=404, detail="Admin UI not found")
