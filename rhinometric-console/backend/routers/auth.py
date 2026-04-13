"""
Authentication router - Keycloak OIDC ONLY mode.
All legacy HS256 / local password auth has been removed.
Keycloak is the sole identity provider.
"""

from datetime import datetime
from typing import Optional, List
import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy.orm import Session
from config import settings
from database import get_db
from models.user import User as UserModel
from models.role import Role as RoleModel

import logging

logger = logging.getLogger('rhinometric.auth')

# Keycloak OIDC
from core.oidc import (
    is_keycloak_token, validate_keycloak_token,
    extract_user_info, map_keycloak_roles, OIDC_ENABLED
)

router = APIRouter()

# tokenUrl is kept for OpenAPI docs; login is handled by Keycloak
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="keycloak", auto_error=False)

# ==================================================================
# PYDANTIC MODELS
# ==================================================================

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

# ==================================================================
# DEPENDENCIES
# ==================================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserModel:
    """
    Verify Keycloak RS256 JWT token and return current user.
    This is Keycloak-only — no local HS256 fallback.
    """

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

    if not OIDC_ENABLED:
        logger.error("[Auth] OIDC is not enabled but Keycloak-only mode is active")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

    try:
        claims = validate_keycloak_token(token)
        user_info = extract_user_info(claims)
        username = user_info.get("username")
        logger.debug(f"[OIDC] Keycloak token validated for user: {username}")

        if not username:
            raise credentials_exception

        # JIT provision or fetch existing user (try sub, then username, then email)
        kc_sub = user_info.get("keycloak_sub")
        user = None
        if kc_sub:
            user = db.query(UserModel).filter(UserModel.sso_external_id == kc_sub).first()
        if user is None:
            user = db.query(UserModel).filter(UserModel.username == username).first()
        if user is None:
            email = user_info.get("email")
            if email:
                user = db.query(UserModel).filter(UserModel.email == email).first()

        if user is None:
            user = _jit_provision_user(db, user_info)
            logger.info(f"[OIDC] JIT provisioned user: {username}")
        else:
            # Bind KC sub if missing
            if kc_sub and not user.sso_external_id:
                user.sso_external_id = kc_sub
                user.sso_provider = "keycloak"
                db.commit()
            # Sync roles from Keycloak on each request
            if user.sso_provider == "keycloak":
                _sync_keycloak_roles(db, user, user_info.get("roles", []))

    except JWTError as e:
        logger.warning(f"[OIDC] Keycloak token validation failed: {str(e)}")
        raise credentials_exception

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    if getattr(user, 'is_deleted', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return user


def _jit_provision_user(db: Session, user_info: dict) -> UserModel:
    """
    Just-In-Time provision a user from Keycloak claims.
    Creates a local DB record for a Keycloak-authenticated user.
    """
    from models.role import UserRole

    kc_roles = user_info.get("roles", [])
    local_role_names = map_keycloak_roles(kc_roles)

    user = UserModel(
        username=user_info["username"],
        email=user_info.get("email") or f"{user_info['username']}@keycloak.local",
        full_name=user_info.get("full_name") or user_info["username"],
        password_hash="KEYCLOAK_SSO_USER",
        sso_provider="keycloak",
        sso_external_id=user_info.get("keycloak_sub"),
        is_active=True,
        must_change_password=False,
    )
    db.add(user)
    db.flush()  # Get user.id

    # Assign mapped roles
    for role_name in local_role_names:
        role = db.query(RoleModel).filter(RoleModel.name == role_name).first()
        if role:
            user_role = UserRole(user_id=user.id, role_id=role.id)
            db.add(user_role)

    db.commit()
    db.refresh(user)
    return user


def _sync_keycloak_roles(db: Session, user: UserModel, kc_roles: list):
    """
    Sync Keycloak realm roles to local user roles.
    Only modifies roles for users with sso_provider=keycloak.
    """
    from models.role import UserRole

    local_role_names = map_keycloak_roles(kc_roles)
    current_roles = set(user.get_roles())
    desired_roles = set(local_role_names)

    if current_roles == desired_roles:
        return  # No change needed

    # Remove existing roles
    db.query(UserRole).filter(UserRole.user_id == user.id).delete()

    # Add new roles
    for role_name in desired_roles:
        role = db.query(RoleModel).filter(RoleModel.name == role_name).first()
        if role:
            user_role = UserRole(user_id=user.id, role_id=role.id)
            db.add(user_role)

    db.commit()
    logger.info(f"[OIDC] Synced roles for {user.username}: {current_roles} -> {desired_roles}")


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


# Convenience shortcuts
require_owner = require_role(["OWNER"])
require_admin = require_role(["OWNER", "ADMIN"])
require_operator = require_role(["OWNER", "ADMIN", "OPERATOR"])
require_viewer = require_role(["OWNER", "ADMIN", "OPERATOR", "VIEWER"])


# ==================================================================
# AUTH ENDPOINTS
# ==================================================================

@router.get("/me")
async def get_me(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information with roles and permissions.
    """
    # Update last_login on profile fetch (closest to "login" in SSO flow)
    current_user.last_login = datetime.utcnow()
    db.commit()

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "roles": current_user.get_roles(),
        "permissions": current_user.get_all_permissions(db),
        "highest_role": current_user.get_highest_role(),
        "must_change_password": False,  # Always false in Keycloak-only mode
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "sso_provider": current_user.sso_provider or "keycloak",
        "avatar_url": current_user.avatar_url,
        "phone": current_user.phone,
        "timezone": current_user.timezone,
        "language": current_user.language
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

# ==================================================================
# OIDC Configuration Endpoint (Public)
# ==================================================================

@router.get("/oidc/config")
async def get_oidc_config():
    """
    Returns OIDC/Keycloak configuration for the frontend.
    This is a PUBLIC endpoint (no auth required).
    The frontend uses this to initialize keycloak-js.
    """
    from core.oidc import (
        KEYCLOAK_PUBLIC_URL, KEYCLOAK_REALM,
        KEYCLOAK_CLIENT_ID, OIDC_ENABLED
    )

    return {
        "enabled": OIDC_ENABLED,
        "keycloak_url": f"{KEYCLOAK_PUBLIC_URL}/auth",
        "realm": KEYCLOAK_REALM,
        "client_id": KEYCLOAK_CLIENT_ID,
    }
