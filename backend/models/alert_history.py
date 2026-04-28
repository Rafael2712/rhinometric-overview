"""
SQLAlchemy model for Alert History.
Stores all alert notifications received from Grafana webhook.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON
from sqlalchemy.sql import func
from database import Base


class AlertHistory(Base):
    """Stores alert notifications received from Grafana webhook contact point."""
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    fingerprint = Column(String(64), nullable=False, index=True)
    alertname = Column(String(255), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # firing, resolved
    severity = Column(String(20), nullable=True, index=True)
    category = Column(String(50), nullable=True, index=True)  # external-services, system, etc.
    service_name = Column(String(255), nullable=True, index=True)
    summary = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    labels = Column(JSON, nullable=True)
    annotations = Column(JSON, nullable=True)
    value = Column(Float, nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    generator_url = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())