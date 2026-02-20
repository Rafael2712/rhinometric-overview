"""
═══════════════════════════════════════════════════════════════════════════
 RHINOMETRIC LICENSE SERVER v2.5.0 - TIER SUPPORT ADDITIONS
═══════════════════════════════════════════════════════════════════════════

This file contains the NEW/UPDATED models and endpoints to support:
- demo_cloud (4 hours)
- trial (14 days, 5 hosts)
- annual_standard (1 year, 20 hosts)

INTEGRATION INSTRUCTIONS:
1. Run the migration: migrations/001_add_tier_support.sql
2. Add/replace the models and endpoints from this file into main.py
3. Update the LicenseCreateRequest and LicenseValidateResponse models
4. Add the new /api/license/status endpoint for Rhinometric Console

═══════════════════════════════════════════════════════════════════════════
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════════════════════════════════
# ENUMS FOR LICENSE TIERS
# ═══════════════════════════════════════════════════════════════════════════

class LicenseTier(str, Enum):
    """License tier types with their characteristics"""
    DEMO_CLOUD = "demo_cloud"      # 4 hours, 20 hosts, cloud-hosted demo
    TRIAL = "trial"                 # 14 days, 5 hosts, on-prem trial
    ANNUAL_STANDARD = "annual_standard"  # 1 year, 20 hosts, commercial
    ENTERPRISE = "enterprise"       # Custom (future)

class LicenseStatus(str, Enum):
    """License status"""
    NOT_ACTIVATED = "not_activated"  # Never used
    ACTIVE = "active"                # Currently valid
    EXPIRED = "expired"              # Past expiration date
    REVOKED = "revoked"              # Manually disabled
    OVER_LIMIT = "over_limit"        # Exceeds max_hosts

class DeploymentMode(str, Enum):
    """
    Deployment mode for the Rhinometric installation.
    Controls runtime behavior but does NOT affect SKU/pricing.
    """
    ON_PREMISE = "ON_PREMISE"                    # Self-hosted customer installation
    SAAS_SINGLE_TENANT = "SAAS_SINGLE_TENANT"    # Cloud-hosted single-tenant deployment

# ═══════════════════════════════════════════════════════════════════════════
# UPDATED PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════

class LicenseCreateRequestV2(BaseModel):
    """Model for creating licenses with tier support"""
    customer_name: str = Field(..., min_length=1, max_length=255)
    client_email: str
    client_company: Optional[str] = ""
    tier: LicenseTier = Field(default=LicenseTier.TRIAL)
    
    # Deployment mode (does not affect SKU or pricing)
    deployment_mode: DeploymentMode = Field(default=DeploymentMode.ON_PREMISE)

    # Optional metadata
    client_phone: Optional[str] = None
    client_country: Optional[str] = None
    notes: Optional[str] = None

class LicenseFullResponse(BaseModel):
    """Complete license information with tier data"""
    id: int
    customer_name: str
    license_key: str
    tier: str
    max_hosts: int
    deployment_mode: str = "ON_PREMISE"  # ON_PREMISE or SAAS_SINGLE_TENANT
    
    # Dates
    issued_at: datetime  # When license was created
    activated_at: Optional[datetime]  # First validation
    expires_at: Optional[datetime]  # Expiration date
    
    # Status
    status: str  # not_activated, active, expired, revoked, over_limit
    days_remaining: Optional[int]
    
    # Organization
    organization: Optional[str]
    organization_email: Optional[str]
    
    # Metadata
    is_active: bool
    activation_count: int = 0

class LicenseStatusResponse(BaseModel):
    """
    Response for /api/license/status endpoint
    Used by Rhinometric Console to display license information
    """
    # License identification
    license_key: str
    tier: str  # demo_cloud, trial, annual_standard
    
    # Limits
    max_hosts: int
    hosts_used: int  # Calculated from Prometheus
    hosts_available: int  # max_hosts - hosts_used

    # Deployment
    deployment_mode: str = "ON_PREMISE"  # ON_PREMISE or SAAS_SINGLE_TENANT
    
    # Dates
    issued_at: datetime
    activated_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    # Status
    status: str  # not_activated, active, expired, revoked, over_limit
    is_valid: bool  # Quick check: active and not expired
    days_remaining: Optional[int]
    hours_remaining: Optional[int]  # For demo_cloud (4 hours)
    
    # Organization
    organization: Optional[str]
    organization_email: Optional[str]
    
    # Messages for UI
    message: str  # Human-readable status message
    warning: Optional[str]  # Warning if approaching limit/expiration

class LicenseValidateRequestV2(BaseModel):
    """Request model for license validation with tier support"""
    license_key: str = Field(..., min_length=10)
    
    # Optional client identification
    hardware_id: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class LicenseValidateResponseV2(BaseModel):
    """Response model for license validation with tier data"""
    valid: bool
    
    # License details
    license_id: Optional[int] = None
    customer_name: Optional[str] = None
    tier: Optional[str] = None
    max_hosts: Optional[int] = None
    deployment_mode: str = "ON_PREMISE"  # ON_PREMISE or SAAS_SINGLE_TENANT
    
    # Timing
    issued_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    days_remaining: Optional[int] = None
    hours_remaining: Optional[int] = None  # For demo_cloud
    
    # Status
    status: Optional[str] = None
    message: str
    
    # Activation info
    activation_id: Optional[int] = None
    first_activation: bool = False  # True if this is the first time

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def generate_license_key_v2(tier: LicenseTier) -> str:
    """Generate license key based on tier"""
    import secrets
    import string
    from datetime import datetime
    
    prefix_map = {
        LicenseTier.DEMO_CLOUD: "DEMO-CLOUD",
        LicenseTier.TRIAL: "TRIAL",
        LicenseTier.ANNUAL_STANDARD: "ANNUAL",
        LicenseTier.ENTERPRISE: "ENTERPRISE"
    }
    
    prefix = prefix_map.get(tier, "TRIAL")
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
    
    return f"RHINO-{prefix}-{datetime.now().year}-{random_part}"

def get_tier_defaults(tier: LicenseTier) -> dict:
    """Get default settings for each tier"""
    defaults = {
        LicenseTier.DEMO_CLOUD: {
            "max_hosts": 20,
            "duration_hours": 4,
            "description": "Cloud-hosted demo (4 hours)"
        },
        LicenseTier.TRIAL: {
            "max_hosts": 5,
            "duration_days": 14,
            "description": "On-premise trial (14 days, 5 hosts)"
        },
        LicenseTier.ANNUAL_STANDARD: {
            "max_hosts": 20,
            "duration_days": 365,
            "description": "Annual commercial license (1 year, 20 hosts)"
        },
        LicenseTier.ENTERPRISE: {
            "max_hosts": 100,
            "duration_days": 365,
            "description": "Enterprise (custom)"
        }
    }
    
    return defaults.get(tier, defaults[LicenseTier.TRIAL])

def calculate_expiration(tier: LicenseTier, from_date: datetime = None) -> datetime:
    """Calculate expiration date based on tier"""
    if from_date is None:
        from_date = datetime.utcnow()
    
    defaults = get_tier_defaults(tier)
    
    if "duration_hours" in defaults:
        return from_date + timedelta(hours=defaults["duration_hours"])
    elif "duration_days" in defaults:
        return from_date + timedelta(days=defaults["duration_days"])
    else:
        # Default to 14 days
        return from_date + timedelta(days=14)

def compute_license_status(
    is_active: bool,
    activated_at: Optional[datetime],
    expires_at: Optional[datetime],
    hosts_used: int,
    max_hosts: int
) -> str:
    """
    Compute license status based on current state
    
    Priority order:
    1. revoked (is_active = false)
    2. not_activated (activated_at is null)
    3. expired (expires_at < now)
    4. over_limit (hosts_used > max_hosts)
    5. active (all good)
    """
    now = datetime.utcnow()
    
    if not is_active:
        return LicenseStatus.REVOKED.value
    
    if activated_at is None:
        return LicenseStatus.NOT_ACTIVATED.value
    
    if expires_at and expires_at < now:
        return LicenseStatus.EXPIRED.value
    
    if hosts_used > max_hosts:
        return LicenseStatus.OVER_LIMIT.value
    
    return LicenseStatus.ACTIVE.value

# ═══════════════════════════════════════════════════════════════════════════
# NEW ENDPOINTS TO ADD TO main.py
# ═══════════════════════════════════════════════════════════════════════════

"""
# ADD THIS ENDPOINT TO main.py

@app.post("/api/licenses/v2", response_model=LicenseFullResponse, status_code=201)
async def create_license_v2(request: LicenseCreateRequestV2, conn = Depends(get_db)):
    '''
    Create a new license with tier support (v2)
    
    Tiers:
    - demo_cloud: 4 hours, 20 hosts, cloud demo
    - trial: 14 days, 5 hosts, on-premise
    - annual_standard: 1 year, 20 hosts, commercial
    '''
    
    try:
        # Generate license key
        license_key = generate_license_key_v2(request.tier)
        
        # Get tier defaults
        defaults = get_tier_defaults(request.tier)
        max_hosts = defaults["max_hosts"]
        
        # Calculate expiration (NOT activated yet, so from created_at)
        created_at = datetime.utcnow()
        expires_at = calculate_expiration(request.tier, created_at)
        
        # Insert into database
        row = await conn.fetchrow('''
            INSERT INTO licenses (
                customer_name, license_key, tier, max_hosts,
                created_at, expires_at, license_status,
                client_email, client_company, client_phone, client_country, notes,
                is_active
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
            ) RETURNING id
        ''', 
            request.customer_name, license_key, request.tier.value, max_hosts,
            created_at, expires_at, LicenseStatus.NOT_ACTIVATED.value,
            request.client_email, request.client_company, request.client_phone, 
            request.client_country, request.notes,
            True
        )
        
        license_id = row['id']
        days_remaining = (expires_at - created_at).days
        
        logger.info(f"✅ License created: {license_key} ({request.tier.value}) for {request.customer_name}")
        
        return LicenseFullResponse(
            id=license_id,
            customer_name=request.customer_name,
            license_key=license_key,
            tier=request.tier.value,
            max_hosts=max_hosts,
            issued_at=created_at,
            activated_at=None,
            expires_at=expires_at,
            status=LicenseStatus.NOT_ACTIVATED.value,
            days_remaining=days_remaining,
            organization=request.client_company,
            organization_email=request.client_email,
            is_active=True,
            activation_count=0
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating license: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating license: {str(e)}")


@app.post("/api/licenses/validate/v2", response_model=LicenseValidateResponseV2)
async def validate_license_v2(request: LicenseValidateRequestV2, conn = Depends(get_db)):
    '''
    Validate a license key and update activation status (v2)
    
    On FIRST validation:
    - Sets activated_at to NOW
    - Recalculates expires_at based on tier (demo_cloud: +4h from activation)
    
    Returns tier, max_hosts, status, and expiration info
    '''
    
    try:
        # Fetch license
        license_row = await conn.fetchrow('''
            SELECT id, customer_name, license_key, tier, max_hosts,
                   created_at, activated_at, expires_at, license_status, is_active,
                   client_email, client_company
            FROM licenses
            WHERE license_key = $1
        ''', request.license_key)
        
        if not license_row:
            # Log failed attempt
            await conn.execute('''
                INSERT INTO license_validation_failures 
                (license_key, reason, ip_address, user_agent)
                VALUES ($1, $2, $3, $4)
            ''', request.license_key, 'License not found', request.ip_address, request.user_agent)
            
            return LicenseValidateResponseV2(
                valid=False,
                message="License key not found"
            )
        
        # Check if revoked
        if not license_row['is_active']:
            return LicenseValidateResponseV2(
                valid=False,
                tier=license_row['tier'],
                message="License has been revoked"
            )
        
        now = datetime.utcnow()
        activated_at = license_row['activated_at']
        expires_at = license_row['expires_at']
        tier = license_row['tier']
        first_activation = False
        
        # FIRST ACTIVATION: Set activated_at and recalculate expires_at for demo_cloud
        if activated_at is None:
            activated_at = now
            first_activation = True
            
            # For demo_cloud, recalculate expiration from activation time
            if tier == LicenseTier.DEMO_CLOUD.value:
                expires_at = now + timedelta(hours=4)
            
            # Update database
            await conn.execute('''
                UPDATE licenses 
                SET activated_at = $1, expires_at = $2, license_status = $3, updated_at = NOW()
                WHERE id = $4
            ''', activated_at, expires_at, LicenseStatus.ACTIVE.value, license_row['id'])
            
            logger.info(f"🎉 FIRST ACTIVATION: {request.license_key} ({tier})")
        
        # Check if expired
        if expires_at < now:
            await conn.execute('''
                UPDATE licenses 
                SET license_status = $1, updated_at = NOW()
                WHERE id = $2
            ''', LicenseStatus.EXPIRED.value, license_row['id'])
            
            return LicenseValidateResponseV2(
                valid=False,
                tier=tier,
                expires_at=expires_at,
                message=f"License expired on {expires_at.strftime('%Y-%m-%d %H:%M UTC')}"
            )
        
        # Calculate remaining time
        time_remaining = expires_at - now
        days_remaining = time_remaining.days
        hours_remaining = int(time_remaining.total_seconds() / 3600)
        
        # Register activation
        import json as json_module
        activation_row = await conn.fetchrow('''
            INSERT INTO license_activations 
            (license_id, license_key, ip_address, user_agent, hardware_id, hostname,
             validation_status)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        ''', license_row['id'], request.license_key, request.ip_address,
            request.user_agent, request.hardware_id, request.hostname, 'success')
        
        # Update last_check
        await conn.execute('''
            UPDATE licenses SET last_check = NOW() WHERE id = $1
        ''', license_row['id'])
        
        logger.info(f"✅ License validated: {request.license_key} ({tier}) - {days_remaining}d remaining")
        
        return LicenseValidateResponseV2(
            valid=True,
            license_id=license_row['id'],
            customer_name=license_row['customer_name'],
            tier=tier,
            max_hosts=license_row['max_hosts'],
            issued_at=license_row['created_at'],
            activated_at=activated_at,
            expires_at=expires_at,
            days_remaining=days_remaining,
            hours_remaining=hours_remaining if tier == 'demo_cloud' else None,
            status=LicenseStatus.ACTIVE.value,
            message=f"License valid - {hours_remaining}h remaining" if tier == 'demo_cloud' else f"License valid - {days_remaining} days remaining",
            activation_id=activation_row['id'],
            first_activation=first_activation
        )
        
    except Exception as e:
        logger.error(f"❌ Error validating license: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")
"""

# ═══════════════════════════════════════════════════════════════════════════
# END OF FILE
# ═══════════════════════════════════════════════════════════════════════════
