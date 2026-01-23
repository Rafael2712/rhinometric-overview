#!/usr/bin/env python3
"""
Trial Bundle Extension for License Server v2.5.0
Adds endpoint to create demo_cloud + trial bundle with enterprise email.

Usage: Import this in main.py after app creation:
    from extensions.trial_bundle import add_trial_bundle_endpoint
    add_trial_bundle_endpoint(app, get_db, logger)
"""

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import logging

from utils.email_enterprise import send_trial_bundle_email
from utils.email_sender import generate_license_key

class TrialBundleRequest(BaseModel):
    """Request para crear trial bundle (demo + trial)"""
    customer_name: str = Field(..., min_length=2, max_length=255)
    client_email: EmailStr
    client_company: Optional[str] = None
    locale: str = Field(default="es", pattern="^(es|en)$")

class TrialBundleResponse(BaseModel):
    """Response con ambas licencias creadas"""
    demo_license: dict
    trial_license: dict
    email_sent: bool
    message: str

def add_trial_bundle_endpoint(app: FastAPI, get_db, logger_instance, smtp_config: dict):
    """
    Agrega el endpoint de trial bundle al app FastAPI.
    
    Args:
        app: FastAPI app instance
        get_db: Database dependency function
        logger_instance: Logger instance
        smtp_config: Dict con config SMTP (host, port, user, password, from_addr)
    """
    
    @app.post("/api/admin/trial-bundle", response_model=TrialBundleResponse, status_code=201)
    async def create_trial_bundle(request: TrialBundleRequest, conn = Depends(get_db)):
        """
        Crea bundle de evaluación: 1 demo_cloud (4h, 20 hosts) + 1 trial (14d, 5 hosts).
        Envía un solo email profesional con ambas licencias.
        
        Esto es lo que se usa en producción cuando un lead solicita evaluar Rhinometric.
        
        Request body:
        {
            "customer_name": "Juan Pérez",
            "client_email": "juan.perez@empresa.com",
            "client_company": "Empresa SA",
            "locale": "es"
        }
        """
        
        try:
            # 1. Generar licencia DEMO_CLOUD (4 horas, 20 hosts)
            demo_key = generate_license_key("demo")
            demo_expires_at = datetime.utcnow() + timedelta(hours=4)
            
            demo_row = await conn.fetchrow("""
                INSERT INTO licenses (
                    customer_name, license_key, tier, max_hosts, 
                    expires_at, is_active, client_email, client_company
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id, customer_name, license_key, tier, max_hosts, 
                          created_at, expires_at, is_active
            """, 
                request.customer_name, 
                demo_key, 
                "demo_cloud",
                20,  # max_hosts para demo
                demo_expires_at, 
                True,
                request.client_email,
                request.client_company or ""
            )
            
            # 2. Generar licencia TRIAL (14 días, 5 hosts)
            trial_key = generate_license_key("trial")
            trial_expires_at = datetime.utcnow() + timedelta(days=14)
            
            trial_row = await conn.fetchrow("""
                INSERT INTO licenses (
                    customer_name, license_key, tier, max_hosts,
                    expires_at, is_active, client_email, client_company
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id, customer_name, license_key, tier, max_hosts,
                          created_at, expires_at, is_active
            """,
                request.customer_name,
                trial_key,
                "trial",
                5,  # max_hosts para trial
                trial_expires_at,
                True,
                request.client_email,
                request.client_company or ""
            )
            
            # 3. Enviar email bundle profesional
            email_sent = await send_trial_bundle_email(
                customer_email=request.client_email,
                customer_name=request.customer_name,
                demo_license_key=demo_key,
                trial_license_key=trial_key,
                smtp_config=smtp_config,
                locale=request.locale
            )
            
            logger_instance.info(f"✅ Trial bundle created for {request.customer_name} ({request.client_email})")
            logger_instance.info(f"   Demo: {demo_key} (expires in 4h)")
            logger_instance.info(f"   Trial: {trial_key} (expires in 14d)")
            logger_instance.info(f"   Email sent: {email_sent}")
            
            return TrialBundleResponse(
                demo_license={
                    "id": demo_row['id'],
                    "license_key": demo_key,
                    "tier": "demo_cloud",
                    "max_hosts": 20,
                    "expires_at": demo_expires_at.isoformat(),
                    "hours_remaining": 4
                },
                trial_license={
                    "id": trial_row['id'],
                    "license_key": trial_key,
                    "tier": "trial",
                    "max_hosts": 5,
                    "expires_at": trial_expires_at.isoformat(),
                    "days_remaining": 14
                },
                email_sent=email_sent,
                message=f"Trial bundle created successfully. Email {'sent' if email_sent else 'NOT sent (check SMTP config)'} to {request.client_email}"
            )
            
        except Exception as e:
            logger_instance.error(f"❌ Error creating trial bundle: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error creating trial bundle: {str(e)}"
            )
    
    logger_instance.info("✅ Trial bundle endpoint registered at POST /api/admin/trial-bundle")
