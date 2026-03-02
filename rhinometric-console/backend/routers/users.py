"""
User Management API - CRUD operations for users with RBAC enforcement
Requires OWNER or ADMIN role for most operations
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

router = APIRouter()

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class UserCreate(BaseModel):
    """Schema for creating new user"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role_names: List[str] = ["VIEWER"]  # Default role
    phone: Optional[str] = None
    timezone: Optional[str] = "UTC"
    language: Optional[str] = "en"
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscore and dash')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r"[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r"[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r"[0-9]", v):
            raise ValueError('Password must contain at least one number')
        return v

class UserUpdate(BaseModel):
    """Schema for updating user (all fields optional)"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None

class AdminResetPasswordRequest(BaseModel):
    """Schema for admin-initiated password reset"""
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r"[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r"[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r"[0-9]", v):
            raise ValueError('Password must contain at least one number')
        return v

class UserRoleAssignment(BaseModel):
    """Schema for assigning/removing roles"""
    role_name: str

class UserResponse(BaseModel):
    """Schema for user response"""
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
    """Extended response for user creation - includes email delivery info."""
    welcome_email_sent: bool = False
    delivery_mode: str = "manual"  # "email" or "manual"
    temporary_password: Optional[str] = None  # Only returned when must_change_password=True AND email failed

class UserListResponse(BaseModel):
    """Schema for paginated user list"""
    total: int
    page: int
    page_size: int
    users: List[UserResponse]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def check_role_assignment_allowed(
    assigner: UserModel,
    target_role: RoleModel,
    db: Session
) -> None:
    """
    Validate if assigner can assign/remove target role.
    
    Rules:
    - OWNER can assign any role
    - ADMIN cannot assign/remove OWNER role
    - OPERATOR and VIEWER cannot assign roles
    """
    assigner_roles = assigner.get_roles()
    
    # Only OWNER and ADMIN can manage roles
    if "OWNER" not in assigner_roles and "ADMIN" not in assigner_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER and ADMIN can manage user roles"
        )
    
    # ADMIN cannot assign OWNER role
    if "OWNER" not in assigner_roles and target_role.name == "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER can assign OWNER role"
        )

# ============================================================================
# USER CRUD ENDPOINTS
# ============================================================================

@router.post("/", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Create new user (OWNER/ADMIN only).
    
    - OWNER can create users with any role
    - ADMIN cannot create users with OWNER role
    - Default password must be changed on first login
    """
    # Check if username already exists
    existing = db.query(UserModel).filter(UserModel.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    existing = db.query(UserModel).filter(UserModel.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Validate roles exist
    roles = db.query(RoleModel).filter(RoleModel.name.in_(user_data.role_names)).all()
    if len(roles) != len(user_data.role_names):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more roles do not exist"
        )
    
    # Check if assigner can assign these roles
    for role in roles:
        check_role_assignment_allowed(current_user, role, db)
    
    # ⚡ TAREA B: Validate license limits for roles
    from services.license_validator import validate_user_roles, LicenseLimitError
    try:
        validate_user_roles(db, user_data.role_names)
    except LicenseLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    
    # Create user
    new_user = UserModel(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        timezone=user_data.timezone,
        language=user_data.language,
        must_change_password=True,  # Force password change on first login
        updated_at=datetime.utcnow()
    )
    new_user.set_password(user_data.password)
    
    db.add(new_user)
    db.flush()  # Get user ID
    
    # Assign roles using UserRole association table
    for role in roles:
        user_role = UserRoleModel(user_id=new_user.id, role_id=role.id)
        db.add(user_role)
    
    db.commit()
    db.refresh(new_user)
    
    # Ensure updated_at is set (fallback for database default not working)
    if new_user.updated_at is None:
        new_user.updated_at = new_user.created_at or datetime.utcnow()
        db.commit()
        db.refresh(new_user)
    
    # ⚡ TAREA C: Audit log - user created
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
        message=f"User {new_user.username} created with roles: {', '.join(user_data.role_names)}",
        metadata={"roles": user_data.role_names, "email": new_user.email}
    )
    
    # ── Welcome email (graceful degradation) ──────────────────────
    welcome_email_sent = False
    delivery_mode = "manual"
    try:
        from services.email_service import send_welcome_email
        login_url = str(request.base_url).rstrip("/") if request else None
        welcome_email_sent = await send_welcome_email(
            email=new_user.email,
            username=new_user.username,
            password=user_data.password,
            full_name=new_user.full_name,
            roles=user_data.role_names,
            login_url=login_url,
        )
        if welcome_email_sent:
            delivery_mode = "email"
    except Exception as exc:
        welcome_email_sent = False

    # ── Observability: structured warning on SMTP failure ──────
    import logging
    _log = logging.getLogger("rhinometric.users")
    if welcome_email_sent:
        _log.info("WELCOME_EMAIL_OK: sent to %s for user %s", new_user.email, new_user.username)
    else:
        import json as _json
        try:
            _ch_path = "/app/data/notification_channels.json"
            with open(_ch_path) as _f:
                _ch = _json.load(_f).get("email", {})
            smtp_host = _ch.get("smtp_host", "N/A")
            smtp_port = _ch.get("smtp_port", "N/A")
        except Exception:
            smtp_host, smtp_port = "N/A", "N/A"
        _log.warning(
            "WELCOME_EMAIL_FAILED: smtp timeout — host=%s port=%s target=%s user=%s",
            smtp_host, smtp_port, new_user.email, new_user.username,
        )

    # ── Audit: record delivery mode ───────────────────────────
    from services.audit_logger import log_audit_event, AuditEvent
    await log_audit_event(
        category=AuditEvent.USER_MANAGEMENT,
        action="welcome_email_delivery",
        user_id=current_user.id,
        username=current_user.username,
        target_user_id=new_user.id,
        target_username=new_user.username,
        ip_address=request.client.host if request and request.client else None,
        status="success" if welcome_email_sent else "failed",
        message=f"welcome_email_delivery_mode={delivery_mode} target={new_user.email}",
        metadata={"delivery_mode": delivery_mode, "target_email": new_user.email},
    )

    # ── Build response (include temp password ONLY if email failed + must_change) ──
    temp_password = None
    if not welcome_email_sent and new_user.must_change_password:
        temp_password = user_data.password  # plain text; never stored, shown once

    return UserCreateResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        must_change_password=new_user.must_change_password,
        last_login=new_user.last_login,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
        roles=new_user.get_roles(),
        phone=new_user.phone,
        timezone=new_user.timezone,
        language=new_user.language,
        welcome_email_sent=welcome_email_sent,
        delivery_mode=delivery_mode,
        temporary_password=temp_password,
    )

@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role_filter: Optional[str] = None,
    active_only: bool = True,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN", "OPERATOR"])),
    db: Session = Depends(get_db)
):
    """
    List all users with pagination (OWNER/ADMIN/OPERATOR).
    
    - Search by username, email, or full name
    - Filter by role
    - Filter by active status
    """
    query = db.query(UserModel)
    
    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (UserModel.username.ilike(search_pattern)) |
            (UserModel.email.ilike(search_pattern)) |
            (UserModel.full_name.ilike(search_pattern))
        )
    
    # Apply role filter
    if role_filter:
        query = query.join(UserModel.roles).filter(RoleModel.name == role_filter)
    
    # Exclude soft-deleted users
    if hasattr(UserModel, 'is_deleted'):
        query = query.filter(
            (UserModel.is_deleted == False) | (UserModel.is_deleted == None)
        )

    # Exclude soft-deleted users
    if hasattr(UserModel, 'is_deleted'):
        query = query.filter(
            (UserModel.is_deleted == False) | (UserModel.is_deleted == None)
        )

    # Apply active filter
    if active_only:
        query = query.filter(UserModel.is_active == True)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    users = query.order_by(UserModel.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Convert to response format
    user_responses = [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            must_change_password=user.must_change_password,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at or user.created_at or datetime.utcnow(),  # Fallback if NULL
            roles=user.get_roles(),
            phone=user.phone,
            timezone=user.timezone,
            language=user.language
        )
        for user in users
    ]
    
    return UserListResponse(
        total=total,
        page=page,
        page_size=page_size,
        users=user_responses
    )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN", "OPERATOR"])),
    db: Session = Depends(get_db)
):
    """
    Get user details by ID (OWNER/ADMIN/OPERATOR).
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=user.get_roles(),
        phone=user.phone,
        timezone=user.timezone,
        language=user.language
    )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Update user details (OWNER/ADMIN only).
    
    - Cannot modify OWNER unless you are OWNER
    - Cannot deactivate yourself
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if target user is OWNER
    if user.is_owner() and not current_user.is_owner():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER can modify OWNER account"
        )
    
    # Cannot deactivate yourself
    if user.id == current_user.id and user_data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Update fields
    if user_data.email is not None:
        # Check email uniqueness
        existing = db.query(UserModel).filter(
            UserModel.email == user_data.email,
            UserModel.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
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
    
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=user.get_roles(),
        phone=user.phone,
        timezone=user.timezone,
        language=user.language
    )

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Soft-delete user (OWNER/ADMIN).

    Safety rules:
    - Cannot delete yourself
    - Cannot delete the last OWNER
    - Cannot delete an already-deleted user
    - ADMIN cannot delete OWNER users
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Already deleted?
    if getattr(user, 'is_deleted', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already deleted"
        )

    # Cannot delete yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    # ADMIN cannot delete OWNER
    if user.is_owner() and not current_user.is_owner():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER can delete another OWNER account"
        )

    # Cannot delete the LAST owner
    if user.is_owner():
        from models.role import Role as RoleModel
        owner_role = db.query(RoleModel).filter(RoleModel.name == "OWNER").first()
        if owner_role:
            from models.role import UserRole as UserRoleModel
            owner_count = db.query(UserRoleModel).filter(
                UserRoleModel.role_id == owner_role.id
            ).join(UserModel, UserModel.id == UserRoleModel.user_id).filter(
                UserModel.is_active == True,
                (UserModel.is_deleted == False) | (UserModel.is_deleted == None)
            ).count()
            if owner_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the last OWNER. Transfer ownership first."
                )

    # Soft-delete
    user.is_active = False
    if hasattr(user, 'is_deleted'):
        user.is_deleted = True
    if hasattr(user, 'deleted_at'):
        user.deleted_at = datetime.utcnow()
    if hasattr(user, 'deleted_by'):
        user.deleted_by = current_user.id
    user.updated_at = datetime.utcnow()

    db.commit()

    # Audit log
    try:
        from services.audit_logger import log_audit_event, AuditEvent
        await log_audit_event(
            category=AuditEvent.USER_MANAGEMENT,
            action="user_deleted",
            user_id=current_user.id,
            username=current_user.username,
            target_user_id=user.id,
            target_username=user.username,
            ip_address=request.client.host if request and request.client else None,
            status="success",
            message=f"User {user.username} ({user.email}) soft-deleted by {current_user.username}",
        )
    except Exception:
        pass

    import logging
    logging.getLogger("rhinometric.users").info(
        "[USER] DELETED user_id=%d username=%s deleted_by=%s",
        user.id, user.username, current_user.username,
    )

    return {"message": f"User {user.username} has been deleted", "user_id": user.id}


    # ADMIN cannot delete OWNER
    if user.is_owner() and not current_user.is_owner():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER can delete another OWNER account"
        )

    # Cannot delete the LAST owner
    if user.is_owner():
        from models.role import Role as RoleModel
        owner_role = db.query(RoleModel).filter(RoleModel.name == "OWNER").first()
        if owner_role:
            from models.role import UserRole as UserRoleModel
            owner_count = db.query(UserRoleModel).filter(
                UserRoleModel.role_id == owner_role.id
            ).join(UserModel, UserModel.id == UserRoleModel.user_id).filter(
                UserModel.is_active == True,
                (UserModel.is_deleted == False) | (UserModel.is_deleted == None)
            ).count()
            if owner_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the last OWNER. Transfer ownership first."
                )

    # Soft-delete
    user.is_active = False
    if hasattr(user, 'is_deleted'):
        user.is_deleted = True
    if hasattr(user, 'deleted_at'):
        user.deleted_at = datetime.utcnow()
    if hasattr(user, 'deleted_by'):
        user.deleted_by = current_user.id
    user.updated_at = datetime.utcnow()

    db.commit()

    # Audit log
    try:
        from services.audit_logger import log_audit_event, AuditEvent
        await log_audit_event(
            category=AuditEvent.USER_MANAGEMENT,
            action="user_deleted",
            user_id=current_user.id,
            username=current_user.username,
            target_user_id=user.id,
            target_username=user.username,
            ip_address=request.client.host if request and request.client else None,
            status="success",
            message=f"User {user.username} ({user.email}) soft-deleted by {current_user.username}",
        )
    except Exception:
        pass

    import logging
    logging.getLogger("rhinometric.users").info(
        "[USER] DELETED user_id=%d username=%s deleted_by=%s",
        user.id, user.username, current_user.username,
    )

    return {"message": f"User {user.username} has been deleted", "user_id": user.id}



# ============================================================================
# ROLE MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/{user_id}/roles", response_model=UserResponse)
async def assign_role(
    user_id: int,
    role_data: UserRoleAssignment,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Assign role to user (OWNER/ADMIN).
    
    - OWNER can assign any role
    - ADMIN cannot assign OWNER role
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    role = db.query(RoleModel).filter(RoleModel.name == role_data.role_name).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if assigner can assign this role
    check_role_assignment_allowed(current_user, role, db)
    
    # Check if user already has this role
    existing_assignment = db.query(UserRoleModel).filter(
        UserRoleModel.user_id == user_id,
        UserRoleModel.role_id == role.id
    ).first()
    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has this role"
        )
    
    # ⚡ TAREA B: Validate license limit for this role
    from services.license_validator import can_add_user_with_role
    can_add, error_msg = can_add_user_with_role(db, role_data.role_name)
    if not can_add:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_msg
        )
    
    # Assign role using UserRole table
    user_role = UserRoleModel(user_id=user_id, role_id=role.id, assigned_by=current_user.id)
    db.add(user_role)
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    # ⚡ TAREA C: Audit log - role assigned
    from services.audit_logger import log_audit_event, AuditEvent
    await log_audit_event(
        category=AuditEvent.ROLE_MANAGEMENT,
        action=AuditEvent.ROLE_ASSIGNED,
        user_id=current_user.id,
        username=current_user.username,
        target_user_id=user.id,
        target_username=user.username,
        role=role_data.role_name,
        ip_address=request.client.host if request and request.client else None,
        status="success",
        message=f"Role {role_data.role_name} assigned to user {user.username}",
        metadata={"all_roles": user.get_roles()}
    )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=user.get_roles(),
        phone=user.phone,
        timezone=user.timezone,
        language=user.language
    )

@router.delete("/{user_id}/roles/{role_name}", response_model=UserResponse)
async def remove_role(
    user_id: int,
    role_name: str,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Remove role from user (OWNER/ADMIN).
    
    - OWNER can remove any role
    - ADMIN cannot remove OWNER role
    - Cannot remove user's last role
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    role = db.query(RoleModel).filter(RoleModel.name == role_name).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if assigner can remove this role
    check_role_assignment_allowed(current_user, role, db)
    
    # Check if user has this role
    user_role = db.query(UserRoleModel).filter(
        UserRoleModel.user_id == user_id,
        UserRoleModel.role_id == role.id
    ).first()
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have this role"
        )
    
    # Cannot remove user's last role
    roles_count = db.query(UserRoleModel).filter(UserRoleModel.user_id == user_id).count()
    if roles_count == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove user's last role. Assign another role first."
        )
    
    # Remove role from UserRole table
    db.delete(user_role)
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=user.get_roles(),
        phone=user.phone,
        timezone=user.timezone,
        language=user.language
    )

@router.get("/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN", "OPERATOR"])),
    db: Session = Depends(get_db)
):
    """
    Get all permissions for user (via their roles).
    Returns: { "permissions": [{"resource": "dashboards", "action": "create"}, ...] }
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    permissions = user.get_all_permissions(db)
    
    return {
        "user_id": user.id,
        "username": user.username,
        "roles": user.get_roles(),
        "permissions": [
            {"resource": p.resource, "action": p.action, "description": p.description}
            for p in permissions
        ],
        "total_permissions": len(permissions)
    }

@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    request_data: AdminResetPasswordRequest,
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Reset a user's password (OWNER/ADMIN only).
    Forces user to change password on next login.
    
    Password requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    """
    # Get target user
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # OWNER protection: Only another OWNER can reset an OWNER's password
    if user.is_owner() and not current_user.is_owner():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER can reset another OWNER's password"
        )
    
    # Validate new password complexity
    new_password = request_data.new_password

    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    if not re.search(r"[A-Z]", new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter"
        )
    if not re.search(r"[a-z]", new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter"
        )
    if not re.search(r"[0-9]", new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one number"
        )
    
    # Set new password and force change on next login
    user.set_password(new_password)
    user.must_change_password = True
    user.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Audit log
    from services.audit_logger import log_audit_event, AuditEvent
    try:
        await log_audit_event(
            category=AuditEvent.USER_MANAGEMENT,
            action="admin_password_reset",
            user_id=current_user.id,
            username=current_user.username,
            target_user_id=user.id,
            target_username=user.username,
            ip_address=request.client.host if request and request.client else None,
            status="success",
            message=f"Admin {current_user.username} reset password for {user.username}",
        )
    except Exception:
        pass

    return {
        "message": f"Password reset successfully for user {user.username}",
        "user_id": user.id,
        "username": user.username,
        "must_change_password": True
    }
