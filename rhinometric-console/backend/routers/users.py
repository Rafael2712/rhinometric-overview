"""
User Management API - CRUD operations with Keycloak as source of truth.
Requires OWNER or ADMIN role for most operations.

Architecture:
- Keycloak is the ONLY source of truth for user identity/auth
- Local DB stores: user_id (KC ref), role, metadata
- All create/update/delete operations sync to Keycloak FIRST
- NO soft delete - users are permanently removed
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

# ======================================================================
# PYDANTIC SCHEMAS
# ======================================================================

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
    role_name: Optional[str] = None


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

    class Config:
        from_attributes = True


class UserCreateResponse(UserResponse):
    welcome_email_sent: bool = False
    delivery_mode: str = "manual"


class UserListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    users: List[UserResponse]


# ======================================================================
# HELPERS
# ======================================================================

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
    )


def _check_role_allowed(assigner: UserModel, target_role_name: str, db: Session):
    assigner_roles = assigner.get_roles()
    if "OWNER" not in assigner_roles and "ADMIN" not in assigner_roles:
        raise HTTPException(403, "Only OWNER and ADMIN can manage user roles")
    if "OWNER" not in assigner_roles and target_role_name == "OWNER":
        raise HTTPException(403, "Only OWNER can assign OWNER role")


# ======================================================================
# CREATE USER - Keycloak FIRST, then DB
# ======================================================================

@router.post("/", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
    request: Request = None,
):
    # Check for existing users in DB (including any orphan records)
    existing_username = db.query(UserModel).filter(UserModel.username == user_data.username).first()
    if existing_username:
        # Check if this is an orphan record (deleted from KC but still in DB)
        if existing_username.sso_external_id:
            try:
                from services.keycloak_admin import find_kc_user
                kc_user = find_kc_user(username=user_data.username)
                if kc_user is None:
                    # Orphan record - KC user gone, purge DB record
                    logger.info("[USER] Purging orphan DB record for username=%s", user_data.username)
                    db.query(UserRoleModel).filter(UserRoleModel.user_id == existing_username.id).delete()
                    db.delete(existing_username)
                    db.flush()
                else:
                    raise HTTPException(400, "Username already exists")
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(400, "Username already exists")
        else:
            raise HTTPException(400, "Username already exists")

    existing_email = db.query(UserModel).filter(UserModel.email == user_data.email).first()
    if existing_email:
        if existing_email.sso_external_id:
            try:
                from services.keycloak_admin import find_kc_user
                kc_user = find_kc_user(email=user_data.email)
                if kc_user is None:
                    logger.info("[USER] Purging orphan DB record for email=%s", user_data.email)
                    db.query(UserRoleModel).filter(UserRoleModel.user_id == existing_email.id).delete()
                    db.delete(existing_email)
                    db.flush()
                else:
                    raise HTTPException(400, "Email already exists")
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(400, "Email already exists")
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
                .filter(UserModel.is_active == True)
                .count()
            )
            if existing_owners >= 1:
                raise HTTPException(409, "Only one OWNER is allowed. Transfer ownership first.")

    # License validation
    try:
        from services.license_validator import validate_user_roles, LicenseLimitError
        validate_user_roles(db, user_data.role_names)
    except ImportError:
        pass
    except Exception as e:
        raise HTTPException(403, str(e))

    # === STEP 1: Create in Keycloak FIRST (source of truth) ===
    primary_role = user_data.role_names[0]
    kc_id = None
    try:
        from services.keycloak_admin import create_kc_user
        parts = (user_data.full_name or "").split(" ", 1)
        first = parts[0] if parts else ""
        last = parts[1] if len(parts) > 1 else ""
        kc_id = create_kc_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            first_name=first,
            last_name=last,
            role_name=primary_role,
        )
    except Exception as exc:
        logger.error("[USER] Keycloak user creation failed for %s: %s", user_data.username, exc)
        raise HTTPException(502, f"Failed to create user in Keycloak: {exc}")

    # === STEP 2: Create DB record with KC reference ===
    try:
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
            sso_external_id=kc_id,
            sso_provider="keycloak",
            updated_at=datetime.utcnow(),
        )
        new_user.set_password(user_data.password)
        db.add(new_user)
        db.flush()

        for role in roles:
            db.add(UserRoleModel(user_id=new_user.id, role_id=role.id))
        db.flush()
        db.commit()
        db.refresh(new_user)
    except Exception as exc:
        db.rollback()
        # Rollback: delete from KC if DB failed
        if kc_id:
            try:
                from services.keycloak_admin import delete_kc_user
                delete_kc_user(kc_id)
                logger.info("[USER] Rolled back KC user %s after DB failure", kc_id)
            except Exception:
                logger.error("[USER] CRITICAL: KC user %s created but DB rollback failed. Manual cleanup needed.", kc_id)
        raise HTTPException(500, f"Failed to create user in database: {exc}")

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
            message=f"User {new_user.username} created with roles: {','.join(user_data.role_names)} (KC synced)",
            metadata={"roles": user_data.role_names, "email": new_user.email, "kc_id": kc_id},
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

    return UserCreateResponse(
        **_user_response(new_user).dict(),
        welcome_email_sent=welcome_email_sent,
        delivery_mode="email" if welcome_email_sent else "manual",
    )


# ======================================================================
# LIST USERS
# ======================================================================

@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    role_filter: Optional[str] = None,
    active_only: bool = False,
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
    if active_only:
        query = query.filter(UserModel.is_active == True)
    total = query.count()
    offset = (page - 1) * page_size
    users = query.order_by(UserModel.created_at.desc()).offset(offset).limit(page_size).all()
    return UserListResponse(total=total, page=page, page_size=page_size, users=[_user_response(u) for u in users])


# ======================================================================
# GET USER
# ======================================================================

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


# ======================================================================
# UPDATE USER  (profile fields + optional role change + KC sync)
# ======================================================================

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
    request: Request = None,
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.is_owner() and not current_user.is_owner():
        raise HTTPException(403, "Only OWNER can modify OWNER account")
    if user.id == current_user.id and user_data.is_active is False:
        raise HTTPException(400, "Cannot deactivate your own account")

    # Track what needs to sync to Keycloak
    kc_update = {}

    # Profile fields
    if user_data.email is not None:
        dup = db.query(UserModel).filter(UserModel.email == user_data.email, UserModel.id != user_id).first()
        if dup:
            raise HTTPException(400, "Email already exists")
        user.email = user_data.email
        kc_update["email"] = user_data.email

    if user_data.full_name is not None:
        user.full_name = user_data.full_name
        parts = (user_data.full_name or "").split(" ", 1)
        kc_update["firstName"] = parts[0] if parts else ""
        kc_update["lastName"] = parts[1] if len(parts) > 1 else ""

    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.timezone is not None:
        user.timezone = user_data.timezone
    if user_data.language is not None:
        user.language = user_data.language

    if user_data.is_active is not None:
        user.is_active = user_data.is_active
        kc_update["enabled"] = user_data.is_active

    # === Sync profile changes to Keycloak FIRST ===
    if kc_update and user.sso_external_id:
        try:
            from services.keycloak_admin import update_kc_user
            update_kc_user(user.sso_external_id, **kc_update)
        except Exception as exc:
            logger.error("[KC SYNC] update failed for %s: %s", user.username, exc)
            raise HTTPException(502, f"Failed to sync changes to Keycloak: {exc}")

    # Role change (single-role model)
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
                    .filter(UserModel.is_active == True)
                    .count()
                )
                if existing_owners >= 1:
                    raise HTTPException(409, "Only one OWNER allowed. Transfer ownership first.")

        # Cannot demote yourself if you are the last OWNER
        if user.is_owner() and new_role_name != "OWNER":
            if user.id == current_user.id:
                raise HTTPException(400, "Cannot remove your own OWNER role")

        # Sync role to KC FIRST
        if user.sso_external_id:
            try:
                from services.keycloak_admin import set_kc_user_role
                set_kc_user_role(user.sso_external_id, new_role_name)
            except Exception as exc:
                logger.error("[KC SYNC] role change failed for %s: %s", user.username, exc)
                raise HTTPException(502, f"Failed to sync role to Keycloak: {exc}")

        # Replace all roles in DB
        db.query(UserRoleModel).filter(UserRoleModel.user_id == user.id).delete()
        db.add(UserRoleModel(user_id=user.id, role_id=new_role.id, assigned_by=current_user.id))
        db.flush()

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    logger.info("[USER] UPDATED id=%d username=%s by=%s fields=%s",
                user.id, user.username, current_user.username,
                list(kc_update.keys()) + (["role"] if user_data.role_name else []))

    return _user_response(user)


# ======================================================================
# DELETE USER - Hard delete from Keycloak AND DB (NO soft delete)
# ======================================================================

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
                .filter(UserModel.is_active == True)
                .count()
            )
            if cnt <= 1:
                raise HTTPException(409, "Cannot delete the last OWNER. Transfer ownership first.")

    username = user.username
    uid = user.id
    kc_id = user.sso_external_id

    # === STEP 1: Delete from Keycloak FIRST ===
    if kc_id:
        try:
            from services.keycloak_admin import delete_kc_user
            delete_kc_user(kc_id)
            logger.info("[USER] Deleted from Keycloak: kc_id=%s username=%s", kc_id, username)
        except Exception as exc:
            logger.error("[KC SYNC] delete failed for %s: %s", username, exc)
            raise HTTPException(502, f"Failed to delete user from Keycloak: {exc}")

    # === STEP 2: Hard delete from DB ===
    db.query(UserRoleModel).filter(UserRoleModel.user_id == user.id).delete()
    db.delete(user)
    db.commit()

    # Audit (best-effort)
    try:
        from services.audit_logger import log_audit_event, AuditEvent
        await log_audit_event(
            category=AuditEvent.USER_MANAGEMENT, action="user_deleted",
            user_id=current_user.id, username=current_user.username,
            target_user_id=uid, target_username=username,
            ip_address=request.client.host if request and request.client else None,
            status="success", message=f"User {username} permanently deleted from DB and Keycloak",
        )
    except Exception:
        pass

    logger.info("[USER] HARD-DELETED id=%d username=%s by=%s", uid, username, current_user.username)
    return {"ok": True, "user_id": uid, "message": f"User {username} permanently deleted"}


# ======================================================================
# ROLE MANAGEMENT
# ======================================================================

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
            .filter(UserModel.is_active == True)
            .filter(UserModel.id != user_id)
            .count()
        )
        if existing_owners > 0:
            raise HTTPException(409, "Only one OWNER is allowed. Transfer ownership first.")
    current_roles = user.get_roles()
    if current_roles == [new_role.name]:
        return _user_response(user)

    # Sync to KC FIRST
    if user.sso_external_id:
        try:
            from services.keycloak_admin import set_kc_user_role
            set_kc_user_role(user.sso_external_id, new_role.name)
        except Exception as e:
            logger.error("[Users] KC role sync failed for %s: %s", user.username, e)
            raise HTTPException(502, f"Failed to sync role to Keycloak: {e}")

    db.query(UserRoleModel).filter(UserRoleModel.user_id == user_id).delete()
    db.add(UserRoleModel(user_id=user_id, role_id=new_role.id, assigned_by=current_user.id))
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

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

# ======================================================================
# PERMISSIONS
# ======================================================================

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


# ======================================================================
# RESET PASSWORD - Via Keycloak ONLY
# ======================================================================

@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    request_data: AdminResetPasswordRequest,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """Admin sets a temporary password for a user via Keycloak Admin API.
    The user must change it on next login."""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.is_owner() and not current_user.is_owner():
        raise HTTPException(403, "Only OWNER can reset OWNER password")
    if not user.sso_external_id:
        raise HTTPException(400, "User has no Keycloak account. Cannot reset password.")

    # Set temporary password in Keycloak (source of truth)
    try:
        from services.keycloak_admin import set_kc_user_password
        set_kc_user_password(user.sso_external_id, request_data.new_password, temporary=True)
    except Exception as exc:
        logger.error("[KC] Password reset failed for %s: %s", user.username, exc)
        raise HTTPException(502, f"Failed to reset password in Keycloak: {exc}")

    # Update local DB to reflect must_change_password
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
            status="success", message=f"Password reset via Keycloak for {user.username}",
        )
    except Exception:
        pass

    return {"message": f"Password reset for {user.username} (via Keycloak)", "user_id": user.id, "must_change_password": True}


@router.post("/{user_id}/send-reset-email")
async def send_reset_email(
    user_id: int,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Send password reset email to user.
    Generates a temporary password, sets it in Keycloak, and emails it
    via the backend's Zoho API (SMTP ports are blocked on this server).
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if not user.sso_external_id:
        raise HTTPException(400, "User has no Keycloak account.")

    # Generate a secure random temporary password
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    while True:
        temp_password = ''.join(secrets.choice(alphabet) for _ in range(14))
        # Ensure it meets validation rules: upper + lower + digit
        if (any(c.isupper() for c in temp_password)
                and any(c.islower() for c in temp_password)
                and any(c.isdigit() for c in temp_password)):
            break

    # Step 1: Set temporary password in Keycloak (must change on next login)
    try:
        from services.keycloak_admin import set_kc_user_password
        set_kc_user_password(user.sso_external_id, temp_password, temporary=True)
    except Exception as exc:
        logger.error("[KC] Password set failed for %s: %s", user.username, exc)
        raise HTTPException(502, f"Failed to set password in Keycloak: {exc}")

    # Step 2: Send email with temp password via backend email service (Zoho API)
    email_sent = False
    try:
        from services.email_service import _load_zoho_api_config, _send_via_zoho_api, _get_public_base_url
        zoho_cfg = _load_zoho_api_config()
        if zoho_cfg:
            from_email = zoho_cfg.get("from_email", "noreply@rhinometric.com")
            login_url = _get_public_base_url()
            subject = "Password Reset - Rhinometric Platform"
            html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:40px 20px">
<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,0.06)">
<tr><td style="padding:32px 40px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:12px 12px 0 0">
<h1 style="color:#fff;font-size:22px;margin:0">Rhinometric Platform</h1></td></tr>
<tr><td style="padding:40px">
<h2 style="color:#1f2937;font-size:24px">Password Reset</h2>
<p style="color:#4b5563">Hello <strong>{user.full_name or user.username}</strong>,</p>
<p style="color:#4b5563">Your password has been reset by an administrator. Use the temporary password below to log in:</p>
<div style="padding:20px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;margin:20px 0">
<table style="width:100%">
<tr><td style="padding:6px 0;color:#6b7280;width:100px">Username:</td><td style="font-weight:600;color:#1f2937">{user.username}</td></tr>
<tr><td style="padding:6px 0;color:#6b7280">Password:</td><td style="font-weight:600;color:#1f2937;font-family:monospace">{temp_password}</td></tr>
</table></div>
<p style="text-align:center;margin:32px 0"><a href="{login_url}" style="display:inline-block;padding:16px 32px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;text-decoration:none;border-radius:6px;font-weight:600">Login to Rhinometric</a></p>
<div style="margin-top:24px;padding:12px;background:#fef3c7;border-radius:4px;border-left:4px solid #f59e0b">
<p style="margin:0;color:#92400e;font-size:14px"><strong>Security:</strong> You must change this password on first login. Do not share credentials.</p></div>
</td></tr>
<tr><td style="padding:20px 40px;background:#f9fafb;border-radius:0 0 12px 12px;text-align:center">
<p style="color:#9ca3af;font-size:12px;margin:0">&copy; {__import__("datetime").datetime.utcnow().year} Rhinometric</p>
</td></tr></table></td></tr></table></body></html>"""
            await _send_via_zoho_api(user.email, subject, html, from_email, zoho_cfg)
            email_sent = True
            logger.info("[USER] Reset email sent to %s via Zoho API", user.email)
        else:
            logger.warning("[USER] Zoho API not configured, cannot send reset email")
    except Exception as exc:
        logger.error("[USER] Failed to send reset email to %s: %s", user.email, exc)

    # Step 3: Update local DB
    user.must_change_password = True
    user.updated_at = datetime.utcnow()
    db.commit()

    # Audit (best-effort)
    try:
        from services.audit_logger import log_audit_event, AuditEvent
        await log_audit_event(
            category=AuditEvent.USER_MANAGEMENT, action="password_reset_email_sent",
            user_id=current_user.id, username=current_user.username,
            target_user_id=user.id, target_username=user.username,
            ip_address=request.client.host if request and request.client else None,
            status="success", message=f"Password reset email sent to {user.email} (email_sent={email_sent})",
        )
    except Exception:
        pass

    if email_sent:
        return {"message": f"Password reset email sent to {user.email}", "user_id": user.id}
    else:
        # Password was still set in KC, just email delivery failed
        return {"message": f"Temporary password set in Keycloak for {user.username}, but email delivery failed. Share the new password manually.", "user_id": user.id}


# ======================================================================
# ROLES LIST (for frontend dropdowns)
# ======================================================================

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
