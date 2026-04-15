"""
SQLAlchemy model for External Service Check History.
Stores every health-check result for uptime/latency graphs.
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.sql import func
from database import Base


class ExternalServiceCheck(Base):
    """One row per health-check execution."""
    __tablename__ = "external_service_checks"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(
        Integer,
        ForeignKey("external_services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(20), nullable=False)          # up, down, degraded, error
    response_time_ms = Column(Float, nullable=True)
    status_code = Column(Integer, nullable=True)         # HTTP status code (null for PG)
    message = Column(Text, nullable=True)
    checked_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # -- Assertion summary (v1) --
    assertions_total = Column(Integer, nullable=False, server_default="0")
    assertions_passed = Column(Integer, nullable=False, server_default="0")
    assertions_failed = Column(Integer, nullable=False, server_default="0")
    first_failed_assertion = Column(String(255), nullable=True)
    first_failed_message = Column(Text, nullable=True)

    # Composite index for time-range queries per service
    __table_args__ = (
        Index("ix_ext_checks_svc_time", "service_id", "checked_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "service_id": self.service_id,
            "status": self.status,
            "response_time_ms": self.response_time_ms,
            "status_code": self.status_code,
            "message": self.message,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
            "assertions_total": self.assertions_total or 0,
            "assertions_passed": self.assertions_passed or 0,
            "assertions_failed": self.assertions_failed or 0,
            "first_failed_assertion": self.first_failed_assertion,
            "first_failed_message": self.first_failed_message,
        }