"""
User Management API - CRUD operations with Keycloak sync and RBAC.
Requires OWNER or ADMIN role for most operations.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.user import User as UserModel
from models.role import Role as RoleModel, UserRole as UserRoleModel
from routers.auth import get_current_user, require_role
import re
import logging

logger = logging.getLogger("rhinometric.users")

router = APIRouter()

# ====================================================================
# PYDANTIC SCHEMAS
# ====================================================================

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role_names: List[str] = ["VIEWER"]
    phone: Optional[str] = None
    timezone: Optional[str] = "UTC"
    language: Optional[str] = "en"

    @validator("username")
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscore, dash, and dot")
        return v

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Must contain lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Must contain a number")
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None
    role_name: Optional[str] = None          # NEW: change role in one call


class AdminResetPasswordRequest(BaseModel):
    new_password: str

    @validator("new_password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Must contain lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Must contain a number")
        return v


class UserRoleAssignment(BaseModel):
    role_name: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    must_change_password: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    roles: List[str]
    phone: Optional[str]
    timezone: Optional[str]
    language: Optional[str]
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None

    class Config:
        from_attributes = True


class UserCreateResponse(UserResponse):
    welcome_email_sent: bool = False
    delivery_mode: str = "manual"
    temporary_password: Optional[str] = None


class UserListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    users: List[UserResponse]


# ====================================================================
# HELPERS
# ====================================================================

def _user_response(user: UserModel) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at or user.created_at or datetime.utcnow(),
        roles=user.get_roles(),
        phone=user.phone,
        timezone=user.timezone,
        language=user.language,
        is_deleted=getattr(user, "is_deleted", False) or False,
        deleted_at=getattr(user, "deleted_at", None),
        deleted_by=getattr(user, "deleted_by", None),
    )


def _check_role_allowed(assigner: UserModel, target_role_name: str, db: Session):
    assigner_roles = assigner.get_roles()
    if "OWNER" not in assigner_roles and "ADMIN" not in assigner_roles:
        raise HTTPException(403, "Only OWNER and ADMIN can manage user roles")
    if "OWNER" not in assigner_roles and target_role_name == "OWNER":
        raise HTTPException(403, "Only OWNER can assign OWNER role")


def _kc_sync_create(user: UserModel, password: str, role_name: str) -> Optional[str]:
    """Create user in Keycloak (best-effort)."""
    try:
        from services.keycloak_admin import create_kc_user
        parts = (user.full_name or "").split(" ", 1)
        first = parts[0] if parts else ""
        last = parts[1] if len(parts) > 1 else ""
        kc_id = create_kc_user(
            username=user.username,
            email=user.email,
            password=password,
            first_name=first,
            last_name=last,
            role_name=role_name,
        )
        return kc_id
    except Exception as exc:
        logger.error("[KC SYNC] create failed for %s: %s", user.username, exc)
        return None


def _kc_sync_disable(user: UserModel):
    """Disable user in Keycloak (best-effort)."""
    kc_id = user.sso_external_id
    if not kc_id:
        return
    try:
        from services.keycloak_admin import disable_kc_user
        disable_kc_user(kc_id)
    except Exception as exc:
        logger.error("[KC SYNC] disable failed for %s: %s", user.username, exc)


def _kc_sync_enable(user: UserModel):
    """Enable user in Keycloak (best-effort)."""
    kc_id = user.sso_external_id
    if not kc_id:
        return
    try:
        from services.keycloak_admin import enable_kc_user
        enable_kc_user(kc_id)
    except Exception as exc:
        logger.error("[KC SYNC] enable failed for %s: %s", user.username, exc)


def _kc_sync_role(user: UserModel, role_name: str):
    """Sync role change to Keycloak (best-effort)."""
    kc_id = user.sso_external_id
    if not kc_id:
        return
    try:
        from services.keycloak_admin import set_kc_user_role
        set_kc_user_role(kc_id, role_name)
    except Exception as exc:
        logger.error("[KC SYNC] role change failed for %s: %s", user.username, exc)


# ====================================================================
# CREATE USER
# ====================================================================

@router.post("/", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
    request: Request = None,
):
    # --- handle soft-deleted conflicts ---
    existing_username = db.query(UserModel).filter(UserModel.username == user_data.username).first()
    if existing_username:
        if getattr(existing_username, "is_deleted", False):
            # Hard-delete the stale record so username can be reused
            db.query(UserRoleModel).filter(UserRoleModel.user_id == existing_username.id).delete()
            db.delete(existing_username)
            db.flush()
            logger.info("[USER] Purged soft-deleted user %s to allow re-creation", user_data.username)
        else:
            raise HTTPException(400, "Username already exists")

    existing_email = db.query(UserModel).filter(UserModel.email == user_data.email).first()
    if existing_email:
        if getattr(existing_email, "is_deleted", False):
            db.query(UserRoleModel).filter(UserRoleModel.user_id == existing_email.id).delete()
            db.delete(existing_email)
            db.flush()
            logger.info("[USER] Purged soft-deleted user with email %s to allow re-creation", user_data.email)
        else:
            raise HTTPException(400, "Email already exists")

    # Validate roles
    roles = db.query(RoleModel).filter(RoleModel.name.in_(user_data.role_names)).all()
    if len(roles) != len(user_data.role_names):
        raise HTTPException(400, "One or more roles do not exist")
    for role in roles:
        _check_role_allowed(current_user, role.name, db)

    # OWNER uniqueness
    if "OWNER" in user_data.role_names:
        owner_role = db.query(RoleModel).filter(RoleModel.name == "OWNER").first()
        if owner_role:
            existing_owners = (
                db.query(UserRoleModel)
                .filter(UserRoleModel.role_id == owner_role.id)
                .join(UserModel, UserModel.id == UserRoleModel.user_id)
                .filter(UserModel.is_active == True, (UserModel.is_deleted == False) | (UserModel.is_deleted == None))
                .count()
            )
            if existing_owners >= 1:
                raise HTTPException(409, "Only one OWNER is allowed. Transfer ownership first.")

    # License validation
    try:
        from services.license_validator import validate_user_roles, LicenseLimitError
        validate_user_roles(db, user_data.role_names)
    except Exception:
        pass

    # Create DB user
    new_user = UserModel(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        timezone=user_data.timezone,
        language=user_data.language,
        must_change_password=True,
        is_active=True,
        is_deleted=False,
        updated_at=datetime.utcnow(),
    )
    new_user.set_password(user_data.password)
    db.add(new_user)
    db.flush()

    primary_role = user_data.role_names[0]
    for role in roles:
        db.add(UserRoleModel(user_id=new_user.id, role_id=role.id))
    db.flush()

    # Sync to Keycloak
    kc_id = _kc_sync_create(new_user, user_data.password, primary_role)
    if kc_id:
        new_user.sso_external_id = kc_id
        new_user.sso_provider = "keycloak"

    db.commit()
    db.refresh(new_user)

    # Audit log (best-effort)
    try:
        from services.audit_logger import log_audit_event, AuditEvent
        await log_audit_event(
            category=AuditEvent.USER_MANAGEMENT,
            action=AuditEvent.USER_CREATED,
            user_id=current_user.id,
            username=current_user.username,
            target_user_id=new_user.id,
            target_username=new_user.username,
            ip_address=request.client.host if request and request.client else None,
            status="success",
            message=f"User {new_user.username} created with roles: {','.join(user_data.role_names)}",
            metadata={"roles": user_data.role_names, "email": new_user.email, "kc_synced": kc_id is not None},
        )
    except Exception:
        pass

    # Welcome email (best-effort)
    welcome_email_sent = False
    try:
        from services.email_service import send_welcome_email
        login_url = str(request.base_url).rstrip("/") if request else None
        welcome_email_sent = await send_welcome_email(
            email=new_user.email, username=new_user.username,
            password=user_data.password, full_name=new_user.full_name,
            roles=user_data.role_names, login_url=login_url,
        )
    except Exception:
        pass

    temp_password = user_data.password if (not welcome_email_sent and new_user.must_change_password) else None

    return UserCreateResponse(
        **_user_response(new_user).dict(),
        welcome_email_sent=welcome_email_sent,
        delivery_mode="email" if welcome_email_sent else "manual",
        temporary_password=temp_password,
    )


# ====================================================================
# LIST USERS
# ====================================================================

@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    role_filter: Optional[str] = None,
    active_only: bool = True,
    include_deleted: bool = Query(False),
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
):
    query = db.query(UserModel)
    if search:
        pat = f"%{search}%"
        query = query.filter(
            (UserModel.username.ilike(pat)) | (UserModel.email.ilike(pat)) | (UserModel.full_name.ilike(pat))
        )
    if role_filter:
        query = query.join(UserModel.roles).join(RoleModel).filter(RoleModel.name == role_filter)
    if not include_deleted:
        query = query.filter((UserModel.is_deleted == False) | (UserModel.is_deleted == None))
    if active_only and not include_deleted:
        query = query.filter(UserModel.is_active == True)
    total = query.count()
    offset = (page - 1) * page_size
    users = query.order_by(UserModel.created_at.desc()).offset(offset).limit(page_size).all()
    return UserListResponse(total=total, page=page, page_size=page_size, users=[_user_response(u) for u in users])


# ====================================================================
# GET USER
# ====================================================================

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return _user_response(user)


# ====================================================================
# UPDATE USER  (profile fields + optional role change)
# ====================================================================

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.is_owner() and not current_user.is_owner():
        raise HTTPException(403, "Only OWNER can modify OWNER account")
    if user.id == current_user.id and user_data.is_active is False:
        raise HTTPException(400, "Cannot deactivate your own account")

    # Profile fields
    if user_data.email is not None:
        dup = db.query(UserModel).filter(UserModel.email == user_data.email, UserModel.id != user_id).first()
        if dup:
            raise HTTPException(400, "Email already exists")
        user.email = user_data.email
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.timezone is not None:
        user.timezone = user_data.timezone
    if user_data.language is not None:
        user.language = user_data.language
    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    # Role change (single-role model for simplicity)
    if user_data.role_name is not None:
        new_role_name = user_data.role_name.upper()
        _check_role_allowed(current_user, new_role_name, db)
        new_role = db.query(RoleModel).filter(RoleModel.name == new_role_name).first()
        if not new_role:
            raise HTTPException(400, f"Role {new_role_name} does not exist")

        # OWNER uniqueness
        if new_role_name == "OWNER" and not user.is_owner():
            owner_role = db.query(RoleModel).filter(RoleModel.name == "OWNER").first()
            if owner_role:
                existing_owners = (
                    db.query(UserRoleModel)
                    .filter(UserRoleModel.role_id == owner_role.id)
                    .join(UserModel, UserModel.id == UserRoleModel.user_id)
                    .filter(UserModel.is_active == True, (UserModel.is_deleted == False) | (UserModel.is_deleted == None))
                    .count()
                )
                if existing_owners >= 1:
                    raise HTTPException(409, "Only one OWNER allowed. Transfer ownership first.")

        # Cannot demote yourself if you are the last OWNER
        if user.is_owner() and new_role_name != "OWNER":
            if user.id == current_user.id:
                raise HTTPException(400, "Cannot remove your own OWNER role")

        # Replace all roles with the new one
        db.query(UserRoleModel).filter(UserRoleModel.user_id == user.id).delete()
        db.add(UserRoleModel(user_id=user.id, role_id=new_role.id, assigned_by=current_user.id))
        db.flush()

        # Sync to KC
        _kc_sync_role(user, new_role_name)

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return _user_response(user)


# ====================================================================
# DELETE USER (soft-delete + KC disable)
# ====================================================================

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
    request: Request = None,
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if getattr(user, "is_deleted", False):
        raise HTTPException(400, "User is already deleted")
    if user.id == current_user.id:
        raise HTTPException(403, "Cannot delete your own account")
    if user.is_owner() and not current_user.is_owner():
        raise HTTPException(403, "Only OWNER can delete another OWNER")

    if user.is_owner():
        owner_role = db.query(RoleModel).filter(RoleModel.name == "OWNER").first()
        if owner_role:
            cnt = (
                db.query(UserRoleModel).filter(UserRoleModel.role_id == owner_role.id)
                .join(UserModel, UserModel.id == UserRoleModel.user_id)
                .filter(UserModel.is_active == True, (UserModel.is_deleted == False) | (UserModel.is_deleted == None))
                .count()
            )
            if cnt <= 1:
                raise HTTPException(409, "Cannot delete the last OWNER. Transfer ownership first.")

    user.is_active = False
    user.is_deleted = True
    user.deleted_at = datetime.utcnow()
    user.deleted_by = current_user.id
    user.updated_at = datetime.utcnow()
    db.commit()

    # Disable in KC
    _kc_sync_disable(user)

    # Audit
    try:
        from services.audit_logger import log_audit_event, AuditEvent
        await log_audit_event(
            category=AuditEvent.USER_MANAGEMENT, action="user_deleted",
            user_id=current_user.id, username=current_user.username,
            target_user_id=user.id, target_username=user.username,
            ip_address=request.client.host if request and request.client else None,
            status="success", message=f"User {user.username} soft-deleted",
        )
    except Exception:
        pass

    logger.info("[USER] DELETED id=%d username=%s by=%s", user.id, user.username, current_user.username)
    return {"ok": True, "user_id": user.id, "deleted_at": str(user.deleted_at)}


# ====================================================================
# RESTORE USER
# ====================================================================

@router.post("/{user_id}/restore")
async def restore_user(
    user_id: int,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
    request: Request = None,
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if not getattr(user, "is_deleted", False):
        raise HTTPException(400, "User is not deleted")

    user.is_deleted = False
    user.is_active = True
    user.deleted_at = None
    user.deleted_by = None
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    # Re-enable in KC
    _kc_sync_enable(user)

    logger.info("[USER] RESTORED id=%d username=%s by=%s", user.id, user.username, current_user.username)
    return {"ok": True, "user_id": user.id, "message": f"User {user.username} restored"}


# ====================================================================
# ROLE MANAGEMENT
# ====================================================================

@router.post("/{user_id}/roles", response_model=UserResponse)
async def assign_role(
    user_id: int,
    role_data: UserRoleAssignment,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
    request: Request = None,
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    role = db.query(RoleModel).filter(RoleModel.name == role_data.role_name).first()
    if not role:
        raise HTTPException(404, "Role not found")
    _check_role_allowed(current_user, role.name, db)

    existing = db.query(UserRoleModel).filter(UserRoleModel.user_id == user_id, UserRoleModel.role_id == role.id).first()
    if existing:
        raise HTTPException(400, "User already has this role")

    try:
        from services.license_validator import can_add_user_with_role
        can_add, err = can_add_user_with_role(db, role_data.role_name)
        if not can_add:
            raise HTTPException(403, err)
    except ImportError:
        pass

    db.add(UserRoleModel(user_id=user_id, role_id=role.id, assigned_by=current_user.id))
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return _user_response(user)


@router.delete("/{user_id}/roles/{role_name}", response_model=UserResponse)
async def remove_role(
    user_id: int,
    role_name: str,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    role = db.query(RoleModel).filter(RoleModel.name == role_name).first()
    if not role:
        raise HTTPException(404, "Role not found")
    _check_role_allowed(current_user, role.name, db)

    ur = db.query(UserRoleModel).filter(UserRoleModel.user_id == user_id, UserRoleModel.role_id == role.id).first()
    if not ur:
        raise HTTPException(400, "User does not have this role")
    cnt = db.query(UserRoleModel).filter(UserRoleModel.user_id == user_id).count()
    if cnt == 1:
        raise HTTPException(400, "Cannot remove last role. Assign another first.")

    db.delete(ur)
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return _user_response(user)



# ================================================================
# CHANGE ROLE (single-role replacement)
# ================================================================

@router.put("/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: int,
    role_data: UserRoleAssignment,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
    request: Request = None,
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == current_user.id:
        raise HTTPException(400, "Cannot change your own role")
    new_role = db.query(RoleModel).filter(RoleModel.name == role_data.role_name).first()
    if not new_role:
        raise HTTPException(404, f"Role {role_data.role_name} not found")
    _check_role_allowed(current_user, role_data.role_name, db)
    if new_role.name == "OWNER":
        owner_role = db.query(RoleModel).filter(RoleModel.name == "OWNER").first()
        existing_owners = (
            db.query(UserRoleModel)
            .filter(UserRoleModel.role_id == owner_role.id)
            .join(UserModel, UserModel.id == UserRoleModel.user_id)
            .filter(UserModel.is_active == True, (UserModel.is_deleted == False) | (UserModel.is_deleted == None))
            .filter(UserModel.id != user_id)
            .count()
        )
        if existing_owners > 0:
            raise HTTPException(409, "Only one OWNER is allowed. Transfer ownership first.")
    current_roles = user.get_roles()
    if current_roles == [new_role.name]:
        return _user_response(user)
    db.query(UserRoleModel).filter(UserRoleModel.user_id == user_id).delete()
    db.add(UserRoleModel(user_id=user_id, role_id=new_role.id, assigned_by=current_user.id))
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    if user.sso_external_id:
        try:
            from services.keycloak_admin import set_kc_user_role
            set_kc_user_role(user.sso_external_id, new_role.name)
        except Exception as e:
            logger.warning("[Users] KC role sync failed for %s: %s", user.username, e)
    try:
        from services.audit_logger import log_audit_event, AuditEvent
        await log_audit_event(
            category=AuditEvent.ROLE_MANAGEMENT, action=AuditEvent.ROLE_ASSIGNED,
            user_id=current_user.id, username=current_user.username,
            target_user_id=user.id, target_username=user.username,
            role=new_role.name, status="success",
            ip_address=request.client.host if request and request.client else None,
            message=f"Role changed from {current_roles} to [{new_role.name}]",
        )
    except Exception:
        pass
    logger.info("[Users] Role changed: user=%s from=%s to=%s by=%s", user.username, current_roles, new_role.name, current_user.username)
    return _user_response(user)

# ====================================================================
# PERMISSIONS
# ====================================================================

@router.get("/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    perms = user.get_all_permissions(db)
    return {"user_id": user.id, "username": user.username, "roles": user.get_roles(), "permissions": perms, "total_permissions": len(perms)}


# ====================================================================
# RESET PASSWORD
# ====================================================================

@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    request_data: AdminResetPasswordRequest,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
    request: Request = None,
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.is_owner() and not current_user.is_owner():
        raise HTTPException(403, "Only OWNER can reset OWNER password")

    user.set_password(request_data.new_password)
    user.must_change_password = True
    user.updated_at = datetime.utcnow()
    db.commit()

    # Audit
    try:
        from services.audit_logger import log_audit_event, AuditEvent
        await log_audit_event(
            category=AuditEvent.USER_MANAGEMENT, action="admin_password_reset",
            user_id=current_user.id, username=current_user.username,
            target_user_id=user.id, target_username=user.username,
            ip_address=request.client.host if request and request.client else None,
            status="success", message=f"Password reset for {user.username}",
        )
    except Exception:
        pass

    return {"message": f"Password reset for {user.username}", "user_id": user.id, "must_change_password": True}


# ====================================================================
# ROLES LIST (for frontend dropdowns)
# ====================================================================

@router.get("/meta/roles")
async def list_roles(
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
):
    """Return available roles with metadata. Used by frontend for create/edit forms."""
    roles = db.query(RoleModel).order_by(RoleModel.level).all()
    caller_is_owner = current_user.is_owner()
    return {
        "roles": [
            {
                "name": r.name,
                "description": r.description,
                "level": r.level,
                "assignable": True if caller_is_owner else r.name != "OWNER",
            }
            for r in roles
        ]
    }
