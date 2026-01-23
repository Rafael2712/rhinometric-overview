"""
Authentication router with DATABASE-backed users and bcrypt password hashing
RBAC implementation - replaces in-memory user_store
"""

from datetime import datetime, timedelta
from typing import Optional, List
import re
import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session
from config import settings
from database import get_db
from models.user import User as UserModel
from models.role import Role as RoleModel

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login", auto_error=False)

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
    print(f"🔑 LOGIN ATTEMPT - Username: {form_data.username}, Password length: {len(form_data.password)}")
    
    # Find user by username
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    
    if not user:
        print(f"❌ User not found: {form_data.username}")
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
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "must_change_password": user.must_change_password,
        "roles": roles
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserModel = Depends(get_current_user)):
    """
    Get current authenticated user information.
    Returns user details including roles.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        roles=current_user.get_roles(),
        must_change_password=current_user.must_change_password,
        last_login=current_user.last_login
    )

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
