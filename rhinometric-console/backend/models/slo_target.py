"""
SQLAlchemy model for SLO Targets — configurable per-service objectives.

Each service can have up to 3 SLO targets:
  - availability  (percentage, e.g. 99.0)
  - latency       (p95 ms, e.g. 1000)
  - health_score  (0-100, e.g. 70)

If no target row exists for a service, platform defaults apply.
"""

from sqlalchemy import (
    Column, Integer, Float, String, DateTime, ForeignKey,
    UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class SLOTarget(Base):
    __tablename__ = "slo_targets"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(
        Integer,
        ForeignKey("external_services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slo_type = Column(
        String(30),
        nullable=False,
        index=True,
    )  # 'availability' | 'latency' | 'health_score'

    target_value = Column(Float, nullable=False)
    # availability → 99.0 (percentage)
    # latency     → 1000  (ms, upper bound)
    # health_score → 70   (0-100, lower bound)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    service = relationship("ExternalService", backref="slo_targets")

    __table_args__ = (
        UniqueConstraint("service_id", "slo_type", name="uq_slo_target_service_type"),
        CheckConstraint("slo_type IN ('availability', 'latency', 'health_score')", name="ck_slo_type"),
    )

    def __repr__(self):
        return f"<SLOTarget(service_id={self.service_id}, type={self.slo_type}, target={self.target_value})>"
