"""
SQLAlchemy model for External Services (HTTP/HTTPS API + PostgreSQL connectors)
MVP: Allows users to connect and monitor their own external services.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float,
    ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from database import Base
import enum


class ServiceType(str, enum.Enum):
    HTTP = "http"
    POSTGRESQL = "postgresql"


class ServiceStatus(str, enum.Enum):
    UNKNOWN = "unknown"
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    ERROR = "error"


class MonitoringMode(str, enum.Enum):
    SYNTHETIC_ONLY = "synthetic_only"
    TELEMETRY_ENABLED = "telemetry_enabled"


class TelemetryStatus(str, enum.Enum):
    NOT_CONFIGURED = "not_configured"
    CONFIGURED = "configured"
    CONNECTED = "connected"
    RECEIVING_DATA = "receiving_data"
    ERROR = "error"


class ExternalService(Base):
    """
    External Service connector - represents a user-managed service
    that Rhinometric monitors (HTTP endpoint or PostgreSQL database).
    """
    __tablename__ = "external_services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    service_type = Column(
        SAEnum(ServiceType, name="service_type_enum", create_type=False),
        nullable=False,
        index=True,
    )
    environment = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    # ── Classification metadata (for Service Catalog) ──
    catalog_type = Column(String(50), nullable=True, index=True)   # REST_API, WEB_APP, DATABASE, etc.
    category = Column(String(100), nullable=True, index=True)      # payments, authentication, etc.
    tags = Column(JSONB, nullable=True)                            # ["critical", "external", "payments"]
    enabled = Column(Boolean, default=True, nullable=False, index=True)

    # Connection configuration (JSON)
    # HTTP:  { url, health_path, method, headers, auth_type, auth_value }
    # PG:    { host, port, database_name, username, password, ssl_mode }
    config = Column(JSONB, nullable=False, default=dict)

    # Check settings
    timeout_seconds = Column(Integer, default=10, nullable=False)
    check_interval_seconds = Column(Integer, default=60, nullable=False)

    # ── Monitoring-mode & telemetry flags ──
    monitoring_mode = Column(
        SAEnum(MonitoringMode, name="monitoring_mode_enum", create_type=False),
        default=MonitoringMode.SYNTHETIC_ONLY,
        nullable=False,
        index=True,
    )
    synthetic_enabled = Column(Boolean, default=True, nullable=False)
    metrics_enabled = Column(Boolean, default=False, nullable=False)
    logs_enabled = Column(Boolean, default=False, nullable=False)
    traces_enabled = Column(Boolean, default=False, nullable=False)
    telemetry_attached = Column(Boolean, default=False, nullable=False)
    telemetry_source_type = Column(String(50), nullable=True)   # "collector" | None
    telemetry_service_key = Column(String(255), nullable=True)  # key linking to collector
    telemetry_token = Column(String(128), nullable=True, unique=True, index=True)  # secure ingestion token
    telemetry_status = Column(
        SAEnum(TelemetryStatus, name="telemetry_status_enum", create_type=False),
        default=TelemetryStatus.NOT_CONFIGURED,
        nullable=False,
    )
    last_telemetry_at = Column(DateTime(timezone=True), nullable=True)  # last ingestion timestamp

    # Status (updated on each check / test)
    status = Column(
        SAEnum(ServiceStatus, name="service_status_enum", create_type=False),
        default=ServiceStatus.UNKNOWN,
        nullable=False,
    )
    status_message = Column(Text, nullable=True)
    last_check_at = Column(DateTime(timezone=True), nullable=True)
    last_response_time_ms = Column(Float, nullable=True)
    last_status_code = Column(Integer, nullable=True)

    # Audit
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<ExternalService(id={self.id}, name={self.name!r}, type={self.service_type})>"

    def to_dict(self):
        """Convert to dict (masks sensitive config fields)."""
        cfg = dict(self.config) if self.config else {}
        if self.service_type == ServiceType.POSTGRESQL and "password" in cfg:
            cfg["password"] = "********"
        if self.service_type == ServiceType.HTTP and "auth_value" in cfg:
            cfg["auth_value"] = "********"

        return {
            "id": self.id,
            "name": self.name,
            "service_type": self.service_type.value if self.service_type else None,
            "environment": self.environment,
            "description": self.description,
            "catalog_type": self.catalog_type,
            "category": self.category,
            "tags": self.tags or [],
            "enabled": self.enabled,
            "config": cfg,
            "timeout_seconds": self.timeout_seconds,
            "check_interval_seconds": self.check_interval_seconds,
            "monitoring_mode": self.monitoring_mode.value if self.monitoring_mode else "synthetic_only",
            "synthetic_enabled": self.synthetic_enabled if self.synthetic_enabled is not None else True,
            "metrics_enabled": self.metrics_enabled or False,
            "logs_enabled": self.logs_enabled or False,
            "traces_enabled": self.traces_enabled or False,
            "telemetry_attached": self.telemetry_attached or False,
            "telemetry_source_type": self.telemetry_source_type,
            "telemetry_service_key": self.telemetry_service_key,
            "telemetry_token": self.telemetry_token,
            "telemetry_status": self.telemetry_status.value if self.telemetry_status else "not_configured",
            "last_telemetry_at": self.last_telemetry_at.isoformat() if self.last_telemetry_at else None,
            "status": self.status.value if self.status else "unknown",
            "status_message": self.status_message,
            "last_check_at": self.last_check_at.isoformat() if self.last_check_at else None,
            "last_response_time_ms": self.last_response_time_ms,
            "last_status_code": self.last_status_code,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }