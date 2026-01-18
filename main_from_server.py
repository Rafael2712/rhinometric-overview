from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import os
import secrets

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://license_admin:RhinoLic2025Secure!@postgres:5432/licenses")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class License(Base):
    __tablename__ = "licenses"
    
    license_key = Column(String, primary_key=True, index=True)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    activations = Column(Integer, default=0)
    max_activations = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    last_activation_at = Column(DateTime, nullable=True)
    machine_id = Column(String, nullable=True)

class Telemetry(Base):
    __tablename__ = "telemetry"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    license_key = Column(String, index=True)
    event_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    machine_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    event_metadata = Column(Text, nullable=True)  # RENAMED from metadata

Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="Rhinometric License Server", version="2.5.0")

# CORS
origins = os.getenv("CORS_ORIGINS", "https://rhinometric.com").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class LicenseRequest(BaseModel):
    email: str = None
    trial_days: int = 14

class ActivationRequest(BaseModel):
    license_key: str
    machine_id: str

class TelemetryEvent(BaseModel):
    license_key: str
    event_type: str
    machine_id: str = None
    event_metadata: str = None  # RENAMED

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "rhinometric-license-server", "version": "2.5.0"}

@app.post("/api/v1/trial/generate")
def generate_trial_license(request: LicenseRequest, db: Session = Depends(get_db)):
    """Generate a new trial license"""
    trial_days = int(os.getenv("OVA_TRIAL_DAYS", request.trial_days))
    license_key = f"RHINO-TRIAL-{secrets.token_hex(8).upper()}"
    
    expires_at = datetime.utcnow() + timedelta(days=trial_days)
    
    license_obj = License(
        license_key=license_key,
        email=request.email,
        expires_at=expires_at,
        max_activations=int(os.getenv("MAX_ACTIVATIONS_PER_LICENSE", 1))
    )
    
    db.add(license_obj)
    db.commit()
    db.refresh(license_obj)
    
    return {
        "license_key": license_key,
        "expires_at": expires_at.isoformat(),
        "trial_days": trial_days,
        "max_activations": license_obj.max_activations
    }

@app.post("/api/v1/license/activate")
def activate_license(request: ActivationRequest, db: Session = Depends(get_db)):
    """Activate a license for a specific machine"""
    license_obj = db.query(License).filter(License.license_key == request.license_key).first()
    
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    
    if not license_obj.is_active:
        raise HTTPException(status_code=403, detail="License is inactive")
    
    if datetime.utcnow() > license_obj.expires_at:
        raise HTTPException(status_code=403, detail="License has expired")
    
    if license_obj.machine_id and license_obj.machine_id != request.machine_id:
        if license_obj.activations >= license_obj.max_activations:
            raise HTTPException(status_code=403, detail="Maximum activations reached")
    
    license_obj.activations += 1
    license_obj.last_activation_at = datetime.utcnow()
    license_obj.machine_id = request.machine_id
    db.commit()
    
    telemetry = Telemetry(
        license_key=request.license_key,
        event_type="activation",
        machine_id=request.machine_id
    )
    db.add(telemetry)
    db.commit()
    
    days_remaining = (license_obj.expires_at - datetime.utcnow()).days
    
    return {
        "status": "activated",
        "expires_at": license_obj.expires_at.isoformat(),
        "days_remaining": days_remaining,
        "activations": license_obj.activations,
        "max_activations": license_obj.max_activations
    }

@app.get("/api/v1/license/{license_key}/status")
def check_license_status(license_key: str, db: Session = Depends(get_db)):
    """Check license status"""
    license_obj = db.query(License).filter(License.license_key == license_key).first()
    
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    
    days_remaining = max(0, (license_obj.expires_at - datetime.utcnow()).days)
    is_expired = datetime.utcnow() > license_obj.expires_at
    
    return {
        "license_key": license_key,
        "is_active": license_obj.is_active and not is_expired,
        "expires_at": license_obj.expires_at.isoformat(),
        "days_remaining": days_remaining,
        "activations": license_obj.activations,
        "max_activations": license_obj.max_activations
    }

@app.post("/api/v1/telemetry")
def log_telemetry(event: TelemetryEvent, db: Session = Depends(get_db)):
    """Log telemetry event"""
    telemetry = Telemetry(
        license_key=event.license_key,
        event_type=event.event_type,
        machine_id=event.machine_id,
        event_metadata=event.event_metadata
    )
    db.add(telemetry)
    db.commit()
    
    return {"status": "logged"}

@app.get("/api/v1/admin/licenses")
def list_licenses(db: Session = Depends(get_db)):
    """Admin: List all licenses"""
    licenses = db.query(License).all()
    return [
        {
            "license_key": lic.license_key,
            "email": lic.email,
            "created_at": lic.created_at.isoformat(),
            "expires_at": lic.expires_at.isoformat(),
            "activations": lic.activations,
            "is_active": lic.is_active
        }
        for lic in licenses
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
