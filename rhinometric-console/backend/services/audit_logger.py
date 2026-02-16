"""
Audit Logging Service for Rhinometric Console
Sends structured audit events to Loki for compliance and security tracking
"""

import logging
import httpx
import json
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
from fastapi import Request
import os

logger = logging.getLogger("rhinometric.audit")

# Loki endpoint (internal service)
LOKI_URL = os.getenv("LOKI_URL", "http://loki:3100")


class AuditEvent:
    """Structured audit event"""
    
    # Event categories
    AUTH = "auth"
    USER_MANAGEMENT = "user_management"
    ROLE_MANAGEMENT = "role_management"
    LICENSE = "license"
    CONFIG = "config"
    ACCESS = "access"
    
    # Event actions
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    PASSWORD_CHANGED = "password_changed"
    LICENSE_VALIDATED = "license_validated"
    LICENSE_ACTIVATED = "license_activated"
    LICENSE_LIMIT_EXCEEDED = "license_limit_exceeded"
    CONFIG_CHANGED = "config_changed"
    RESOURCE_ACCESSED = "resource_accessed"
    PERMISSION_DENIED = "permission_denied"
    
    def __init__(
        self,
        category: str,
        action: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        target_user_id: Optional[int] = None,
        target_username: Optional[str] = None,
        role: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.category = category
        self.action = action
        self.user_id = user_id
        self.username = username
        self.target_user_id = target_user_id
        self.target_username = target_username
        self.role = role
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.status = status
        self.message = message
        self.metadata = metadata or {}
        
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp,
            "category": self.category,
            "action": self.action,
            "user_id": self.user_id,
            "username": self.username,
            "target_user_id": self.target_user_id,
            "target_username": self.target_username,
            "role": self.role,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "message": self.message,
            "metadata": self.metadata
        }
    
    def to_log_line(self) -> str:
        """Convert to single-line JSON for Loki"""
        return json.dumps(self.to_dict(), separators=(',', ':'))


async def send_to_loki(event: AuditEvent) -> bool:
    """
    Send audit event to Loki.
    
    Args:
        event: AuditEvent to send
        
    Returns:
        True if successful, False otherwise (non-blocking)
    """
    try:
        # Loki push API format
        payload = {
            "streams": [
                {
                    "stream": {
                        "job": "rhinometric-audit",
                        "category": event.category,
                        "action": event.action,
                        "status": event.status
                    },
                    "values": [
                        [
                            str(int(datetime.utcnow().timestamp() * 1_000_000_000)),  # Nanosecond timestamp
                            event.to_log_line()
                        ]
                    ]
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{LOKI_URL}/loki/api/v1/push",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code not in [200, 204]:
                logger.warning(f"Loki push failed: {response.status_code} - {response.text}")
                return False
            
            logger.debug(f"✅ Audit event sent to Loki: {event.action}")
            return True
            
    except Exception as e:
        # Non-blocking: log error but don't fail the request
        logger.error(f"❌ Failed to send audit event to Loki: {str(e)}")
        return False


def audit_log(category: str, action: str, message: Optional[str] = None):
    """
    Decorator for automatic audit logging of FastAPI endpoints.
    
    Usage:
        @router.post("/users")
        @audit_log(AuditEvent.USER_MANAGEMENT, AuditEvent.USER_CREATED, "User created")
        async def create_user(...):
            ...
    
    Args:
        category: Event category (e.g., AuditEvent.AUTH)
        action: Event action (e.g., AuditEvent.LOGIN)
        message: Optional message template
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and current_user from kwargs (if available)
            request: Optional[Request] = kwargs.get('request')
            current_user = kwargs.get('current_user')
            
            # Extract IP and User-Agent from request
            ip_address = None
            user_agent = None
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
            
            # Execute the function
            try:
                result = await func(*args, **kwargs)
                
                # Create audit event (success)
                event = AuditEvent(
                    category=category,
                    action=action,
                    user_id=current_user.id if current_user else None,
                    username=current_user.username if current_user else None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status="success",
                    message=message
                )
                
                # Send to Loki (non-blocking)
                await send_to_loki(event)
                
                return result
                
            except Exception as e:
                # Create audit event (failure)
                event = AuditEvent(
                    category=category,
                    action=action,
                    user_id=current_user.id if current_user else None,
                    username=current_user.username if current_user else None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status="failure",
                    message=f"{message or ''} - Error: {str(e)}"
                )
                
                # Send to Loki (non-blocking)
                await send_to_loki(event)
                
                # Re-raise the exception
                raise
        
        return wrapper
    return decorator


async def log_audit_event(
    category: str,
    action: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    target_user_id: Optional[int] = None,
    target_username: Optional[str] = None,
    role: Optional[str] = None,
    ip_address: Optional[str] = None,
    status: str = "success",
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Manual audit logging function (for use outside decorators).
    
    Example:
        await log_audit_event(
            category=AuditEvent.AUTH,
            action=AuditEvent.LOGIN,
            username="admin",
            ip_address="192.168.1.100",
            status="success",
            message="User logged in successfully"
        )
    """
    event = AuditEvent(
        category=category,
        action=action,
        user_id=user_id,
        username=username,
        target_user_id=target_user_id,
        target_username=target_username,
        role=role,
        ip_address=ip_address,
        status=status,
        message=message,
        metadata=metadata
    )
    
    await send_to_loki(event)
