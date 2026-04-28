"""
Password Reset Token model for self-service password recovery
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime, timedelta


class PasswordResetToken(Base):
    """
    Password reset tokens for self-service password recovery.
    
    - Tokens expire after 1 hour
    - Single-use only (marked as 'used' after redemption)
    - Linked to user for validation
    """
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        status = "used" if self.used else ("expired" if self.is_expired() else "valid")
        return f"<PasswordResetToken(user_id={self.user_id}, status={status})>"
    
    def is_expired(self) -> bool:
        """Check if token has expired"""
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)
    
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)"""
        return not self.used and not self.is_expired()
    
    @staticmethod
    def generate_expiration(hours: int = 1) -> datetime:
        """Generate expiration datetime (default 1 hour from now)"""
        return datetime.utcnow() + timedelta(hours=hours)
