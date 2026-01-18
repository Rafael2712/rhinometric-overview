"""
═══════════════════════════════════════════════════════════════════════════
 INTEGRATION GUIDE: Trial Self-Service Module
═══════════════════════════════════════════════════════════════════════════
 
 Add this code to license-server-v2-main.py to enable trial self-service
 
═══════════════════════════════════════════════════════════════════════════
"""

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: Add imports (after existing imports in main.py)
# ═══════════════════════════════════════════════════════════════════════════

from fastapi.staticfiles import StaticFiles
from license_server_trial_selfservice import router as trial_router
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: Add config variables (after SMTP config section)
# ═══════════════════════════════════════════════════════════════════════════

# Trial Self-Service Configuration
OVA_DOWNLOAD_URL = os.getenv(
    "OVA_DOWNLOAD_URL",
    "https://rhinometric.com/downloads/rhinometric-v2.5.0.ova"
)
MANUAL_INSTALL_URL = os.getenv(
    "MANUAL_INSTALL_URL",
    "https://docs.rhinometric.com/installation"
)
MANUAL_USER_URL = os.getenv(
    "MANUAL_USER_URL",
    "https://docs.rhinometric.com/user-guide"
)

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: Store config in app state (in startup event or after app creation)
# ═══════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_extended():
    """Extended startup to include trial self-service config"""
    # ... existing startup code ...
    
    # Store SMTP config in app state for trial module
    app.state.smtp_host = SMTP_HOST
    app.state.smtp_port = SMTP_PORT
    app.state.smtp_user = SMTP_USER
    app.state.smtp_password = SMTP_PASSWORD
    app.state.smtp_from = SMTP_FROM
    
    # Store download URLs
    app.state.ova_download_url = OVA_DOWNLOAD_URL
    app.state.manual_install_url = MANUAL_INSTALL_URL
    app.state.manual_user_url = MANUAL_USER_URL
    
    logger.info(f"✅ Trial self-service configured with OVA URL: {OVA_DOWNLOAD_URL}")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: Include trial router (after other routers)
# ═══════════════════════════════════════════════════════════════════════════

# Include trial self-service router (no authentication required)
app.include_router(trial_router)
logger.info("✅ Trial self-service endpoints registered")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 5: Serve static files and add /trial redirect
# ═══════════════════════════════════════════════════════════════════════════

# Mount static files directory for trial signup form
STATIC_DIR = Path("/app/static")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    logger.info(f"✅ Static files served from {STATIC_DIR}")
else:
    logger.warning(f"⚠️  Static directory not found: {STATIC_DIR}")

# Convenience redirect: /trial → /static/trial-signup.html
@app.get("/trial", response_class=HTMLResponse)
async def trial_page_redirect():
    """Redirect to trial signup page"""
    try:
        with open(STATIC_DIR / "trial-signup.html") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Trial signup page not found. Please contact support."
        )

# ═══════════════════════════════════════════════════════════════════════════
# STEP 6: Add admin endpoint to view trial signups (optional)
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/admin/trial-signups", dependencies=[Depends(verify_admin_token)])
async def list_trial_signups(
    days: int = 7,
    tier: Optional[str] = None,
    conn = Depends(get_db)
):
    """
    List recent trial signups (last N days)
    Admin only
    """
    where_clause = "WHERE issued_at >= NOW() - INTERVAL '%s days'" % days
    params = []
    
    if tier in ['demo_cloud', 'trial']:
        where_clause += " AND tier = $1"
        params.append(tier)
    
    query = f"""
        SELECT 
            id,
            customer_name,
            organization,
            organization_email,
            client_country,
            tier,
            license_key,
            status,
            issued_at,
            activated_at,
            expires_at
        FROM licenses
        {where_clause}
        ORDER BY issued_at DESC
        LIMIT 100
    """
    
    rows = await conn.fetch(query, *params)
    
    signups = []
    for row in rows:
        signups.append({
            "id": row['id'],
            "customer_name": row['customer_name'],
            "organization": row['organization'],
            "email": row['organization_email'],
            "country": row['client_country'],
            "tier": row['tier'],
            "license_key": row['license_key'],
            "status": row['status'],
            "issued_at": row['issued_at'].isoformat(),
            "activated_at": row['activated_at'].isoformat() if row['activated_at'] else None,
            "expires_at": row['expires_at'].isoformat() if row['expires_at'] else None
        })
    
    return {
        "total": len(signups),
        "days_filter": days,
        "tier_filter": tier,
        "signups": signups
    }

# ═══════════════════════════════════════════════════════════════════════════
# STEP 7: Add metrics for trial signups (optional, if using Prometheus)
# ═══════════════════════════════════════════════════════════════════════════

from prometheus_client import Counter, Gauge

# Metrics
trial_signups_counter = Counter(
    'rhinometric_trial_signups_total',
    'Total trial signups',
    ['tier']
)

trial_activations_counter = Counter(
    'rhinometric_trial_activations_total',
    'Total trial activations',
    ['tier']
)

# Update counter when creating licenses (in trial_selfservice.py):
# trial_signups_counter.labels(tier='demo_cloud').inc()
# trial_signups_counter.labels(tier='trial').inc()

logger.info("✅ Trial metrics configured")

# ═══════════════════════════════════════════════════════════════════════════
# COMPLETE! Trial self-service is now integrated.
# ═══════════════════════════════════════════════════════════════════════════
