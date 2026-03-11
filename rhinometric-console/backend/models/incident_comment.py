"""
SQLAlchemy model for Incident Comments.
Phase 2.5 — Incident Timeline & Collaboration Layer.
"""

import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base


class IncidentComment(Base):
    """User comment on an incident."""
    __tablename__ = "incident_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author = Column(String(100), nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_incident_comments_inc_time", "incident_id", "created_at"),
    )
