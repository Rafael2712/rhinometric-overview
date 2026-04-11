"""
SQLAlchemy model for Synthetic Monitoring Alert Policies.

Replaces the generic metric/operator/threshold model with
product-oriented rule types: SERVICE_DOWN, HIGH_LATENCY, DEGRADED_HEALTH.

The DB table is migrated in-place from the old alert_rules schema
via an Alembic migration (see migrations/).
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
)
from sqlalchemy.sql import func
from database import Base
import uuid as _uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)

    # ── Identity ────────────────────────────────────────────────
    name = Column(String(255), nullable=False, index=True)
    rule_type = Column(
        String(30), nullable=False, default="SERVICE_DOWN",
        doc="SERVICE_DOWN | HIGH_LATENCY | DEGRADED_HEALTH",
    )

    # ── Scope ───────────────────────────────────────────────────
    # NULL service_id  =  applies to ALL services (global policy)
    service_id = Column(Integer, nullable=True, index=True)

    # ── Thresholds ──────────────────────────────────────────────
    # SERVICE_DOWN
    consecutive_failures = Column(Integer, nullable=False, default=3,
        doc="Failures before first alert")
    critical_escalation_failures = Column(Integer, nullable=False, default=6,
        doc="Failures before escalating to critical")
    incident_after_seconds = Column(Integer, nullable=False, default=120,
        doc="Seconds of sustained downtime before creating incident")

    # HIGH_LATENCY
    latency_threshold_ms = Column(Float, nullable=True, default=1000.0,
        doc="Absolute latency threshold in ms")
    latency_deviation_pct = Column(Float, nullable=True,
        doc="% deviation over baseline (alternative to absolute)")

    # DEGRADED_HEALTH
    anomaly_score_threshold = Column(Float, nullable=True, default=70.0,
        doc="Anomaly score threshold (0-100)")

    # ── Common ──────────────────────────────────────────────────
    sustained_checks = Column(Integer, nullable=False, default=3,
        doc="Consecutive checks exceeding threshold before alerting")
    severity = Column(String(20), nullable=False, default="warning",
        doc="info | warning | critical")
    cooldown_seconds = Column(Integer, nullable=False, default=120,
        doc="Seconds between repeated alerts for same condition")
    enabled = Column(Boolean, nullable=False, default=True)

    # ── Metadata ────────────────────────────────────────────────
    is_default = Column(Boolean, nullable=False, default=False,
        doc="True for system-generated default rules")
    description = Column(Text, nullable=True)
    config = Column(JSONB, nullable=True,
        doc="Extra config for future extensibility")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now())

    # ── Legacy columns (kept for backward compat, hidden from UI)
    metric = Column(String(50), nullable=True)
    operator = Column(String(5), nullable=True)
    threshold = Column(Float, nullable=True)
    window_minutes = Column(Integer, nullable=True)

    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<AlertRule {self.name} type={self.rule_type} svc={self.service_id}>"
