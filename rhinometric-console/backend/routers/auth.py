"""
Authentication router with DATABASE-backed users and bcrypt password hashing
RBAC implementation - replaces in-memory user_store
"""

from datetime import datetime, timedelta
from typing import Optional, List
import re
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from config import settings
from database import get_db
from models.user import User as UserModel
from models.role import Role as RoleModel
from models.password_reset import PasswordResetToken
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login", auto_error=False)

# Rate limiter for forgot password (3 requests per hour per IP)
limiter = Limiter(key_func=get_remote_address)
RATE_LIMIT_FORGOT = "3/hour"

# ============================================================================
# PYDANTIC MODELS (API Schemas)
# ============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str
    must_change_password: bool = False
    roles: List[str] = []

class TokenData(BaseModel):
    username: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    roles: List[str]
    must_change_password: bool = False
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# ============================================================================
# JWT TOKEN UTILITIES
# ============================================================================

def create_access_token(data: dict) -> str:
    """Generate JWT token with user data"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# ============================================================================
# DEPENDENCIES
# ============================================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserModel:
    """
    Verify JWT token and return current user from database.
    Validates token, checks user exists and is active.
    """
    
    # OPTIONAL: Skip authentication if DISABLE_AUTH=true (development only)
    if os.getenv("DISABLE_AUTH", "false").lower() == "true":
        # Return first OWNER user for dev mode
        dev_user = db.query(UserModel).join(UserModel.roles).filter(
            RoleModel.name == "OWNER"
        ).first()
        if dev_user:
            return dev_user
        # Fallback to any user
        dev_user = db.query(UserModel).first()
        if dev_user:
            return dev_user
        raise HTTPException(status_code=500, detail="No users in database")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Fetch user from database
    user = db.query(UserModel).filter(UserModel.username == username).first()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user

def require_role(allowed_roles: List[str]):
    """
    Dependency factory for role-based access control.
    Usage: Depends(require_role(["OWNER", "ADMIN"]))
    """
    async def role_checker(current_user: UserModel = Depends(get_current_user)):
        user_roles = current_user.get_roles()
        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user with username/password and return JWT token.
    
    Default credentials (MUST be changed on first login):
    - Username: admin
    - Password: admin
    
    Password is verified using bcrypt hashing.
    """
    from services.audit_logger import log_audit_event, AuditEvent
    
    print(f"🔑 LOGIN ATTEMPT - Identifier: {form_data.username}, Password length: {len(form_data.password)}")
    
    # ⚡ TAREA B: Dual-mode login - Find user by EMAIL or USERNAME (backward compatible)
    identifier = form_data.username.strip()
    user = db.query(UserModel).filter(
        (UserModel.email == identifier) | (UserModel.username == identifier)
    ).first()
    
    if not user:
        print(f"❌ User not found: {identifier}")
        
        # ⚡ TAREA C: Audit log - login failed (user not found)
        await log_audit_event(
            category=AuditEvent.AUTH,
            action=AuditEvent.LOGIN_FAILED,
            username=identifier,
            ip_address=request.client.host if request and request.client else None,
            status="failure",
            message=f"User not found (tried email/username): {identifier}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"✅ User found: {user.username}, Hash: {user.password_hash[:30]}...")
    
    # Verify password with bcrypt
    password_valid = user.verify_password(form_data.password)
    print(f"🔐 Password verification result: {password_valid}")
    
    if not password_valid:
        print(f"❌ Password invalid for user: {form_data.username}")
        
        # ⚡ TAREA C: Audit log - login failed (wrong password)
        await log_audit_event(
            category=AuditEvent.AUTH,
            action=AuditEvent.LOGIN_FAILED,
            user_id=user.id,
            username=user.username,
            ip_address=request.client.host if request and request.client else None,
            status="failure",
            message="Invalid password"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Get user roles
    roles = user.get_roles()
    
    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "roles": roles,
            "must_change_password": user.must_change_password
        }
    )
    
    # ⚡ TAREA C: Audit log - successful login
    await log_audit_event(
        category=AuditEvent.AUTH,
        action=AuditEvent.LOGIN,
        user_id=user.id,
        username=user.username,
        ip_address=request.client.host if request and request.client else None,
        role=roles[0] if roles else None,
        status="success",
        message="User logged in successfully",
        metadata={"roles": roles}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "must_change_password": user.must_change_password,
        "roles": roles
    }

@router.get("/me")
async def get_me(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information with roles and permissions.
    
    This endpoint is used by the frontend to:
    - Display user profile
    - Configure dynamic UI menu based on permissions
    - Show role badges
    - Determine feature access
    
    Returns:
        {
            "id": 1,
            "username": "admin",
            "email": "admin@rhinometric.com",
            "full_name": "System Administrator",
            "roles": ["OWNER"],
            "permissions": [
                {"resource": "users", "actions": ["create", "read", "update", "delete"]},
                {"resource": "dashboards", "actions": ["read", "update"]}
            ],
            "highest_role": "OWNER",
            "must_change_password": false,
            "last_login": "2026-02-09T12:30:00Z",
            "sso_provider": "local",
            "avatar_url": null,
            "timezone": "UTC",
            "language": "en"
        }
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "roles": current_user.get_roles(),
        "permissions": current_user.get_all_permissions(db),
        "highest_role": current_user.get_highest_role(),
        "must_change_password": current_user.must_change_password,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "sso_provider": current_user.sso_provider or "local",
        "avatar_url": current_user.avatar_url,
        "phone": current_user.phone,
        "timezone": current_user.timezone,
        "language": current_user.language
    }

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password.
    
    Password requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    
    Old password must be provided for verification.
    """
    # Verify old password
    if not current_user.verify_password(request.old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password complexity
    password = request.new_password
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter"
        )
    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter"
        )
    if not re.search(r"[0-9]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one number"
        )
    
    # Cannot reuse old password
    if current_user.verify_password(password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as old password"
        )
    
    # Update password (automatically hashes with bcrypt)
    current_user.set_password(password)
    current_user.must_change_password = False
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Password changed successfully",
        "must_change_password": False
    }

@router.get("/check-permissions/{resource}/{action}")
async def check_permission(
    resource: str,
    action: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if current user has specific permission.
    Returns: { "has_permission": true/false }
    """
    has_perm = current_user.has_permission(resource, action, db)
    return {
        "resource": resource,
        "action": action,
        "has_permission": has_perm,
        "user_roles": current_user.get_roles()
    }

# ============================================================================
# PASSWORD RESET ENDPOINTS (SELF-SERVICE)
# ============================================================================

@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    forgot_request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Initiate password reset process.
    
    - Rate limited to 3 requests per hour per IP
    - Sends reset email with token link
    - Token expires in 1 hour
    - Always returns success (security: don't reveal if email exists)
    
    Request body:
        {
            "email": "user@example.com"
        }
    """
    from services.audit_logger import log_audit_event, AuditEvent
    from services.email_service import send_password_reset_email
    
    email = forgot_request.email.lower().strip()
    
    # Find user by email
    user = db.query(UserModel).filter(UserModel.email == email).first()
    
    if user:
        # Generate unique reset token (UUID)
        reset_token = str(uuid.uuid4())
        
        # Create password reset token in database
        token_record = PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            expires_at=PasswordResetToken.generate_expiration(hours=1),
            used=False
        )
        db.add(token_record)
        db.commit()
        
        # Send password reset email
        email_sent = await send_password_reset_email(
            email=user.email,
            username=user.username,
            reset_token=reset_token
        )
        
        # Audit log
        await log_audit_event(
            category=AuditEvent.AUTH,
            action="password_reset_requested",
            user_id=user.id,
            username=user.username,
            ip_address=request.client.host if request.client else None,
            status="success" if email_sent else "email_failed",
            message=f"Password reset requested for {email}",
            metadata={"email_sent": email_sent}
        )
        
        print(f"✅ Password reset token generated for {email}")
    else:
        # User not found - still return success (security: don't reveal if email exists)
        await log_audit_event(
            category=AuditEvent.AUTH,
            action="password_reset_requested",
            username=email,
            ip_address=request.client.host if request.client else None,
            status="user_not_found",
            message=f"Password reset requested for non-existent email: {email}"
        )
        
        print(f"⚠️  Password reset requested for non-existent email: {email}")
    
    # Always return success (don't reveal if email exists)
    return {
        "message": "If your email is registered, you will receive a password reset link shortly.",
        "email": email
    }


@router.post("/reset-password")
async def reset_password(
    request: Request,
    reset_request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using token from email.
    
    - Validates token (exists, not used, not expired)
    - Updates user password
    - Marks token as used (single-use)
    - Invalidates all other tokens for this user
    
    Request body:
        {
            "token": "uuid-token-from-email",
            "new_password": "NewSecurePass123!"
        }
    """
    from services.audit_logger import log_audit_event, AuditEvent
    
    token = reset_request.token.strip()
    new_password = reset_request.new_password
    
    # Find token in database
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token
    ).first()
    
    if not token_record:
        await log_audit_event(
            category=AuditEvent.AUTH,
            action="password_reset_failed",
            ip_address=request.client.host if request.client else None,
            status="invalid_token",
            message="Password reset attempted with invalid token"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check if token is valid (not used, not expired)
    if not token_record.is_valid():
        reason = "already used" if token_record.used else "expired"
        await log_audit_event(
            category=AuditEvent.AUTH,
            action="password_reset_failed",
            user_id=token_record.user_id,
            ip_address=request.client.host if request.client else None,
            status=f"token_{reason.replace(' ', '_')}",
            message=f"Password reset attempted with {reason} token"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Reset token is {reason}"
        )
    
    # Get user
    user = db.query(UserModel).filter(UserModel.id == token_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate new password strength
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Update user password
    user.set_password(new_password)
    user.must_change_password = False
    
    # Mark this token as used
    token_record.used = True
    
    # Invalidate all other reset tokens for this user (security)
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.id != token_record.id,
        PasswordResetToken.used == False
    ).update({"used": True})
    
    db.commit()
    
    # Audit log
    await log_audit_event(
        category=AuditEvent.AUTH,
        action=AuditEvent.PASSWORD_CHANGED,
        user_id=user.id,
        username=user.username,
        ip_address=request.client.host if request.client else None,
        status="success",
        message=f"Password reset successfully for {user.username}"
    )
    
    print(f"✅ Password reset successfully for user: {user.username}")
    
    return {
        "message": "Password reset successfully. You can now login with your new password.",
        "username": user.username
    }
