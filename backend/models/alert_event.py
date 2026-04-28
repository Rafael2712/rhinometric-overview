"""
SQLAlchemy model for Alert Events.

Canonical Alert Model (v2) with full lifecycle support.

  ONE active alert per (entity_name + alert_type fingerprint).
  Severity is UPDATED in-place; no duplicate rows for the same problem.

Status lifecycle:
  firing -> acknowledged -> resolved
  firing -> resolved  (auto or manual)
  firing -> dismissed  (false positive / irrelevant)
  firing -> silenced   (temporarily muted)
  acknowledged -> resolved
  silenced -> firing   (when silence expires, reverts conceptually)
"""

import uuid
from sqlalchemy import Column, String, DateTime, Text, Float, JSON, Index, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from database import Base


class AlertEvent(Base):
    """Persistent alert lifecycle events.

    Each row represents a canonical alert for a unique problem.
    The fingerprint = sha256(alert_name|entity_name|rule_type)[:16]
    guarantees ONE ACTIVE ROW per (service + alert_type).

    Statuses: firing | acknowledged | resolved | dismissed | silenced
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
    ai_decision = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    source = Column(String(100), nullable=True, default="alertmanager")
    generator_url = Column(String(500), nullable=True)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # -- v2 dedup lifecycle fields --
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    escalation_count = Column(Integer, nullable=False, default=0,
        doc="Number of times severity was escalated while alert remained active")
    last_evaluated_at = Column(DateTime(timezone=True), nullable=True,
        doc="Timestamp of last rule-evaluation pass that touched this alert")

    # -- v3 user-action lifecycle fields --
    acknowledged_by = Column(String(150), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(150), nullable=True,
        doc="Username who manually resolved; NULL = auto-resolved")
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    dismissed_by = Column(String(150), nullable=True)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)
    silenced_until = Column(DateTime(timezone=True), nullable=True,
        doc='Alert is silenced (hidden from notifications) until this timestamp')

    # -- v4 notification tracking fields --
    notification_sent_at = Column(DateTime(timezone=True), nullable=True,
        doc="Timestamp when firing email notification was sent")
    recovery_notification_sent_at = Column(DateTime(timezone=True), nullable=True,
        doc="Timestamp when recovery email notification was sent")

    # -- Phase 5.2: AI Decision Engine --
    ai_decision = Column(JSONB, nullable=True,
        doc="Structured AI triage decision (ignore/monitor/notify/escalate)")

    # Composite index for efficient history queries
    __table_args__ = (
        Index("ix_alert_events_fp_status", "fingerprint", "status"),
        Index("ix_alert_events_entity", "entity_type", "entity_name"),
        Index("ix_alert_events_started", "started_at"),
    )