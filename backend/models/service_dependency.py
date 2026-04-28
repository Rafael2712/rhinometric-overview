"""
SQLAlchemy model for Service Dependencies (Phase 2.8 — Service Map).

Represents directional dependencies between monitored services.
Example: API → PostgreSQL (source=API, target=PostgreSQL)
"""

import uuid as _uuid
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class ServiceDependency(Base):
    """
    Directional dependency between two external services.
    source_service  ──depends-on──▶  target_service
    """
    __tablename__ = "service_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)
    source_service_id = Column(
        Integer,
        ForeignKey("external_services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_service_id = Column(
        Integer,
        ForeignKey("external_services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dependency_type = Column(
        String(50),
        nullable=False,
        default="http",
    )
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    source_service = relationship(
        "ExternalService",
        foreign_keys=[source_service_id],
        lazy="joined",
    )
    target_service = relationship(
        "ExternalService",
        foreign_keys=[target_service_id],
        lazy="joined",
    )

    # Prevent duplicate edges
    __table_args__ = (
        UniqueConstraint(
            "source_service_id", "target_service_id",
            name="uq_service_dep_src_tgt",
        ),
    )

    def __repr__(self):
        return (
            f"<ServiceDependency(id={self.id}, "
            f"src={self.source_service_id}, tgt={self.target_service_id}, "
            f"type={self.dependency_type!r})>"
        )
