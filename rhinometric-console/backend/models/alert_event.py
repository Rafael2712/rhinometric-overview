"""
SQLAlchemy model for Alert Events.
Phase 2.2 — Alert Event Store (Alert History Foundation).

Stores every alert lifecycle transition so that the platform maintains
a complete history of alert activity even after Alertmanager resolves them.
"""

import uuid
from sqlalchemy import Column, String, DateTime, Text, Float, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base


class AlertEvent(Base):
    """Persistent alert lifecycle events.

    Each row represents a single alert lifecycle transition (firing → resolved).
    The fingerprint links back to the anomaly group that originated the alert.
    """
    __tablename__ = "alert_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_name = Column(String(255), nullable=False, index=True)
    metric_name = Column(String(255), nullable=True)
    severity = Column(String(20), nullable=False, default="warning", index=True)
    status = Column(String(20), nullable=False, default="firing", index=True)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    fingerprint = Column(String(64), nullable=False, index=True)
    labels = Column(JSON, nullable=True)
    annotations = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    source = Column(String(100), nullable=True, default="alertmanager")
    generator_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Composite index for efficient history queries
    __table_args__ = (
        Index("ix_alert_events_fp_status", "fingerprint", "status"),
        Index("ix_alert_events_entity", "entity_type", "entity_name"),
        Index("ix_alert_events_started", "started_at"),
    )
