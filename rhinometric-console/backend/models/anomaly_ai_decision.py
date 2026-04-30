"""
SQLAlchemy model for persisting AI triage decisions for anomaly groups.
Keyed by the Go anomaly engine fingerprint (stable 32-char hex identifier).
Added in Phase 5: Anomaly AI Triage persistence.
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


class AnomalyAiDecision(Base):
    """Persisted AI triage decision for an anomaly group."""
    __tablename__ = "anomaly_ai_decisions"

    # Go engine fingerprint — stable 32-char hex identifying an anomaly group
    fingerprint = Column(String(64), primary_key=True, index=True)
    ai_decision = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
