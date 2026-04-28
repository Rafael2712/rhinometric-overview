"""
SQLAlchemy model for Alert Acknowledgements
Tracks which alerts have been acknowledged by users
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SAEnum
from sqlalchemy.sql import func
from database import Base
import enum


class AckStatus(str, enum.Enum):
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class AlertAcknowledgement(Base):
    """
    Tracks alert acknowledgements from the Rhinometric Console.
    Allows users to mark alerts as 'someone is looking into this'.
    """
    __tablename__ = "alert_acknowledgements"

    id = Column(Integer, primary_key=True, index=True)
    fingerprint = Column(String(64), nullable=False, index=True)
    alertname = Column(String(255), nullable=False, index=True)
    status = Column(String(20), nullable=False, default=AckStatus.ACKNOWLEDGED.value)
    ack_by = Column(String(100), nullable=False)
    ack_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    note = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
