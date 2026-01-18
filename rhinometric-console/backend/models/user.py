"""
SQLAlchemy User model with bcrypt password hashing
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from passlib.context import CryptContext
from typing import List, Optional

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """
    User model with bcrypt password hashing
    """
    __tablename__ = "users"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    
    # Status fields
    is_active = Column(Boolean, default=True, index=True)
    must_change_password = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    
    # Additional fields
    avatar_url = Column(Text)
    phone = Column(String(50))
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    
    # Relationships
    roles = relationship("UserRole", foreign_keys="[UserRole.user_id]", back_populates="user", cascade="all, delete-orphan")
    creator = relationship("User", remote_side=[id], foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
    
    def to_dict(self, include_roles: bool = False):
        """
        Convert user to dictionary (excludes password_hash)
        """
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "must_change_password": self.must_change_password,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "avatar_url": self.avatar_url,
            "phone": self.phone,
            "timezone": self.timezone,
            "language": self.language
        }
        
        if include_roles:
            data["roles"] = [
                {
                    "id": ur.role.id,
                    "name": ur.role.name,
                    "level": ur.role.level,
                    "assigned_at": ur.assigned_at.isoformat() if ur.assigned_at else None
                }
                for ur in self.roles
            ]
        
        return data
    
    # ========================================================================
    # PASSWORD METHODS
    # ========================================================================
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt
        """
        return pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash
        """
        return pwd_context.verify(password, self.password_hash)
    
    def set_password(self, password: str):
        """
        Set user password (hashes automatically)
        """
        self.password_hash = self.hash_password(password)
    
    # ========================================================================
    # ROLE METHODS
    # ========================================================================
    
    def get_roles(self) -> List[str]:
        """
        Get list of role names for this user
        Returns: ['OWNER', 'ADMIN'] etc.
        """
        return [ur.role.name for ur in self.roles if ur.role]
    
    def get_highest_role(self) -> Optional[str]:
        """
        Get highest role (lowest level number)
        Returns: 'OWNER' if user has multiple roles
        """
        if not self.roles:
            return None
        return min(self.roles, key=lambda ur: ur.role.level).role.name
    
    def has_role(self, role_name: str) -> bool:
        """
        Check if user has a specific role
        """
        return role_name in self.get_roles()
    
    def is_owner(self) -> bool:
        """Check if user has OWNER role"""
        return self.has_role("OWNER")
    
    def is_admin(self) -> bool:
        """Check if user has ADMIN role"""
        return self.has_role("ADMIN")
    
    def is_operator(self) -> bool:
        """Check if user has OPERATOR role"""
        return self.has_role("OPERATOR")
    
    def is_viewer(self) -> bool:
        """Check if user has VIEWER role"""
        return self.has_role("VIEWER")
    
    # ========================================================================
    # PERMISSION METHODS (will be implemented with permission checking)
    # ========================================================================
    
    def has_permission(self, resource: str, action: str, db_session) -> bool:
        """
        Check if user has a specific permission
        Uses database function user_has_permission()
        """
        from sqlalchemy import text
        result = db_session.execute(
            text("SELECT user_has_permission(:user_id, :resource, :action)"),
            {"user_id": self.id, "resource": resource, "action": action}
        )
        return result.scalar()
    
    def can_create(self, resource: str, db_session) -> bool:
        """Check if user can create resource"""
        return self.has_permission(resource, "create", db_session)
    
    def can_read(self, resource: str, db_session) -> bool:
        """Check if user can read resource"""
        return self.has_permission(resource, "read", db_session)
    
    def can_update(self, resource: str, db_session) -> bool:
        """Check if user can update resource"""
        return self.has_permission(resource, "update", db_session)
    
    def can_delete(self, resource: str, db_session) -> bool:
        """Check if user can delete resource"""
        return self.has_permission(resource, "delete", db_session)
