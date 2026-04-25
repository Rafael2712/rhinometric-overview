"""
SQLAlchemy model for Incidents.
Phase 2.3 ? Incident Management Engine.
Phase 3   ? AI-Powered Incident Management (title, summary, hints, postmortem, linking).

Groups multiple related alert events into a single operational incident.
An incident is created when alert events fire for the same entity/scope,
and resolved when all linked alert events are resolved.
"""

import uuid
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from database import Base


class Incident(Base):
    """Operational incident grouping related alert events."""
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_key = Column(String(255), nullable=False, index=True)  # partial unique via ix_incidents_incident_key_active
    entity_name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, default="service")
    severity = Column(String(20), nullable=False, default="warning")
    status = Column(String(20), nullable=False, default="open", index=True)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    tags = Column(JSONB, nullable=True, default=list)

    # ── Phase 3: AI-powered fields ──────────────────────────────
    title = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    investigation_hints = Column(JSONB, nullable=True, default=list)
    postmortem = Column(Text, nullable=True)
    anomaly_id = Column(Text, nullable=True)
    alert_fingerprint = Column(Text, nullable=True)

    # ── Phase 5.1: AI Incident Briefing ──────────────────────────
    ai_briefing = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_incidents_entity", "entity_type", "entity_name"),
        Index("ix_incidents_status_started", "status", "started_at"),
    )
