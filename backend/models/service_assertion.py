"""
SQLAlchemy model for Service Assertions.

Defines expected-behavior rules that are evaluated against each
synthetic check result. Each assertion belongs to one ExternalService
and specifies a condition (e.g. status_code equals 200).

v1 assertion types (fixed scope):
  - status_code      : HTTP status must equal expected value
  - response_time    : latency must be less than threshold (ms)
  - text_contains    : response body must contain a substring
  - json_path_equals : value at a JSON dot-path must equal expected
"""

import uuid
import enum
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey,
    Index, CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base


class AssertionType(str, enum.Enum):
    STATUS_CODE = "status_code"
    RESPONSE_TIME = "response_time"
    TEXT_CONTAINS = "text_contains"
    JSON_PATH_EQUALS = "json_path_equals"


class ServiceAssertion(Base):
    """
    One assertion rule attached to an external service.

    Evaluation happens inside health_checker._check_one() after
    the connector returns a response.  Multiple assertions per
    service are supported and evaluated in `order`.
    """
    __tablename__ = "service_assertions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(
        Integer,
        ForeignKey("external_services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # -- Assertion definition --
    assertion_type = Column(String(30), nullable=False)
    operator = Column(String(20), nullable=False)
    expected_value = Column(Text, nullable=False)
    json_path = Column(String(500), nullable=True)

    # -- Metadata --
    name = Column(String(255), nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    severity = Column(String(20), default="warning", nullable=False)
    order = Column(Integer, default=0, nullable=False)

    # -- Audit --
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_svc_assertions_enabled", "service_id", "enabled"),
        CheckConstraint(
            "assertion_type IN ('status_code', 'response_time', 'text_contains', 'json_path_equals')",
            name="chk_assertion_type",
        ),
        CheckConstraint(
            "severity IN ('info', 'warning', 'critical')",
            name="chk_assertion_severity",
        ),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "service_id": self.service_id,
            "assertion_type": self.assertion_type,
            "operator": self.operator,
            "expected_value": self.expected_value,
            "json_path": self.json_path,
            "name": self.name,
            "enabled": self.enabled,
            "severity": self.severity,
            "order": self.order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return (
            f"<ServiceAssertion(id={self.id}, service_id={self.service_id}, "
            f"type={self.assertion_type}, expected={self.expected_value!r})>"
        )
