"""
Grafana Proxy with Role-Based Access Control
Routes requests to Grafana while enforcing Rhinometric's RBAC
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import httpx
from config import settings
from models.user import User as UserModel

router = APIRouter()

# URLs prohibidas para VIEWER y OPERATOR
ADMIN_ONLY_PATHS = [
    "/admin",
    "/datasources",
    "/org/",
    "/api/admin",
    "/api/datasources",
    "/api/org",
    "/api/user/",
    "/api/users",
    "/plugins",
    "/api/plugins",
]

VIEWER_BLOCKED_PATHS = ADMIN_ONLY_PATHS + [
    "/api/dashboards/db",  # Create/edit dashboards
    "/api/folders",  # Create/edit folders
    "/api/annotations",  # Create annotations
    "/api/alerts",  # Edit alerts
]

def is_path_allowed(path: str, user: UserModel) -> bool:
    """Check if user has permission to access Grafana path"""
    
    # OWNER and ADMIN have full access
    if user.is_owner() or user.is_admin():
        return True
    
    # OPERATOR can't access admin paths
    if user.has_role("OPERATOR"):
        for blocked in ADMIN_ONLY_PATHS:
            if blocked in path:
                return False
        return True
    
    # VIEWER has most restrictions
    if user.has_role("VIEWER"):
        for blocked in VIEWER_BLOCKED_PATHS:
            if blocked in path:
                return False
        return True
    
    return False

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def grafana_proxy(
    path: str,
    request: Request,
    response: Response,
    token: Optional[str] = Query(None, description="JWT token as query parameter for browser navigation")
):
    """
    Proxy all requests to Grafana with RBAC enforcement
    
    Access levels:
    - OWNER/ADMIN: Full access to all Grafana features
    - OPERATOR: Can view and edit dashboards, no admin access
    - VIEWER: Read-only access to dashboards, no editing
    
    Token can be provided via:
    - Authorization header (preferred for API calls)
    - Query parameter ?token=... (for browser navigation via window.open)
    - Cookie: grafana_token (set automatically after first auth)
    """
    
    # Get user from Authorization header, query parameter, or cookie
    from jose import jwt, JWTError
    from database import SessionLocal
    
    current_user = None
    
    # Try to get token from multiple sources
    auth_header = request.headers.get("authorization")
    jwt_token = None
    
    if auth_header and auth_header.startswith("Bearer "):
        jwt_token = auth_header.split(" ")[1]
    elif token:
        jwt_token = token
    elif request.cookies.get("grafana_token"):
        jwt_token = request.cookies.get("grafana_token")
    
    if not jwt_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Token required via Authorization header, ?token= parameter, or cookie"
        )
    
    # Decode token and get user
    try:
        payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        db = SessionLocal()
        try:
            current_user = db.query(UserModel).filter(UserModel.username == username).first()
            if not current_user:
                raise HTTPException(status_code=401, detail="User not found")
            if not current_user.is_active:
                raise HTTPException(status_code=403, detail="User account is disabled")
            
            # Load roles before closing session to avoid DetachedInstanceError
            _ = current_user.get_roles()
        finally:
            db.close()
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    # Check if user has permission for this path
    if not is_path_allowed(f"/{path}", current_user):
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. Your role ({', '.join(current_user.get_roles())}) does not have permission to access this Grafana resource."
        )
    
    # Build Grafana URL - WITH /api/grafana prefix when SERVE_FROM_SUB_PATH=true
    # Frontend calls /api/grafana/d/... → Backend keeps /api/grafana → Grafana receives /api/grafana/d/...
    grafana_url = f"http://rhinometric-grafana:3000/api/grafana/{path}"
    
    # Add kiosk mode for VIEWER and OPERATOR (hide Grafana UI chrome)
    if current_user.has_role("VIEWER") or current_user.has_role("OPERATOR"):
        # Add kiosk parameter to hide Grafana menu
        if "?" in grafana_url:
            grafana_url += "&kiosk=tv"
        else:
            grafana_url += "?kiosk=tv"
    
    # Get request body if exists
    body = await request.body()
    
    # Forward request to Grafana
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Prepare headers with X-Forwarded-* for proper proxy handling
            proxy_headers = {
                key: value for key, value in request.headers.items()
                if key.lower() not in ["host", "authorization", "content-length"]
            }
            # Add forwarding headers
            proxy_headers["X-Forwarded-For"] = request.client.host if request.client else "unknown"
            proxy_headers["X-Forwarded-Proto"] = "http"
            proxy_headers["X-Forwarded-Host"] = "89.167.15.73:3002"
            
            response = await client.request(
                method=request.method,
                url=grafana_url,
                headers=proxy_headers,
                content=body if body else None,
                params=request.query_params,
            )
            
            # Build response headers without problematic ones
            response_headers = {
                key: value for key, value in response.headers.items()
                if key.lower() not in ["content-length", "transfer-encoding", "location", "content-security-policy", "x-frame-options"]
            }
            
            # Rewrite HTML content to fix resource paths
            content = response.content
            content_type = response.headers.get("content-type", "")
            
            if "text/html" in content_type:
                # Decode HTML and rewrite URLs to go through proxy
                html_content = content.decode('utf-8', errors='ignore')
                
                # Replace absolute paths with proxied paths
                html_content = html_content.replace('href="/public/', 'href="/api/grafana/public/')
                html_content = html_content.replace('src="/public/', 'src="/api/grafana/public/')
                html_content = html_content.replace('href="/api/', 'href="/api/grafana/api/')
                html_content = html_content.replace('src="/api/', 'src="/api/grafana/api/')
                html_content = html_content.replace('url(/public/', 'url(/api/grafana/public/')
                html_content = html_content.replace('"baseUrl":""', '"baseUrl":"/api/grafana"')
                html_content = html_content.replace("'baseUrl':''", "'baseUrl':'/api/grafana'")
                
                content = html_content.encode('utf-8')
            
            # Create response
            grafana_response = Response(
                content=content,
                status_code=response.status_code,
                headers=response_headers,
                media_type=response.headers.get("content-type")
            )
            
            # Set cookie with token if it was provided via query parameter (first time)
            if token and jwt_token:
                grafana_response.set_cookie(
                    key="grafana_token",
                    value=jwt_token,
                    httponly=True,
                    samesite="lax",
                    path="/api/grafana",
                    max_age=3600  # 1 hour
                )
            
            return grafana_response
            
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Grafana service unavailable: {str(e)}"
            )
