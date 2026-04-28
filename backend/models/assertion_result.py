"""
SQLAlchemy model for Assertion Results (failures only).

Only FAILED assertion evaluations are persisted here.
Passed assertions are counted in the summary columns on
external_service_checks but do NOT generate rows in this table.

This keeps the table small during normal operation and rich
during incidents when diagnostic detail matters.
"""

import uuid
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base


class AssertionResult(Base):
    """
    One row per FAILED assertion evaluation.

    Fields like assertion_type and assertion_name are snapshotted
    at write time so the row remains meaningful even if the
    assertion definition is later edited or deleted.
    """
    __tablename__ = "assertion_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    check_id = Column(
        Integer,
        ForeignKey("external_service_checks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assertion_id = Column(
        UUID(as_uuid=True),
        ForeignKey("service_assertions.id", ondelete="CASCADE"),
        nullable=False,
    )
    service_id = Column(Integer, nullable=False)  # denormalized for fast queries

    # -- Snapshot of what failed --
    assertion_type = Column(String(30), nullable=False)
    assertion_name = Column(String(255), nullable=True)
    expected_value = Column(Text, nullable=False)
    actual_value = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    evaluated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_assertion_results_svc_time", "service_id", "evaluated_at"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "check_id": self.check_id,
            "assertion_id": str(self.assertion_id),
            "service_id": self.service_id,
            "assertion_type": self.assertion_type,
            "assertion_name": self.assertion_name,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "error_message": self.error_message,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
        }

    def __repr__(self):
        return (
            f"<AssertionResult(id={self.id}, check_id={self.check_id}, "
            f"type={self.assertion_type}, passed=False)>"
        )
