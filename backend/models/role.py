"""
SQLAlchemy models for RBAC - Roles and Permissions
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Role(Base):
    """
    Role model - OWNER, ADMIN, OPERATOR, VIEWER
    """
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    level = Column(Integer, nullable=False, index=True)  # 1=OWNER, 2=ADMIN, 3=OPERATOR, 4=VIEWER
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Role(name='{self.name}', level={self.level})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "level": self.level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Permission(Base):
    """
    Permission model - Granular permissions on resources
    """
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    resource = Column(String(100), nullable=False, index=True)  # dashboards, alerts, users, etc.
    action = Column(String(50), nullable=False, index=True)     # create, read, update, delete
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Unique constraint on resource + action
    __table_args__ = (
        UniqueConstraint('resource', 'action', name='uix_resource_action'),
    )
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Permission(resource='{self.resource}', action='{self.action}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "resource": self.resource,
            "action": self.action,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class UserRole(Base):
    """
    User-Role association (Many-to-Many)
    """
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    
    # Unique constraint: one user can't have the same role twice
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', name='uix_user_role'),
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="roles")
    role = relationship("Role", back_populates="user_roles")
    assigner = relationship("User", foreign_keys=[assigned_by])
    
    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role_id": self.role_id,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "assigned_by": self.assigned_by
        }


class RolePermission(Base):
    """
    Role-Permission association (Many-to-Many)
    """
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Unique constraint: one role can't have the same permission twice
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uix_role_permission'),
    )
    
    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    
    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "role_id": self.role_id,
            "permission_id": self.permission_id,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None
        }
