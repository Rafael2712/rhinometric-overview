"""
SQLAlchemy model for user-defined alert rules (Phase 2.6).
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey
)
from sqlalchemy.sql import func
from database import Base
import uuid as _uuid
from sqlalchemy.dialects.postgresql import UUID


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("external_services.id", ondelete="CASCADE"), nullable=False, index=True)
    metric = Column(String(50), nullable=False)          # latency_ms | error_rate | availability_pct | response_time_p95
    operator = Column(String(5), nullable=False)          # > < >= <=
    threshold = Column(Float, nullable=False)
    window_minutes = Column(Integer, nullable=False, default=5)
    severity = Column(String(20), nullable=False, default="warning")  # info | warning | critical
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<AlertRule {self.name} ({self.metric} {self.operator} {self.threshold})>"
