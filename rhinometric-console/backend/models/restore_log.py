"""
SQLAlchemy model for Restore audit log.
Phase 3: Tracks who restored what and when.
"""

import uuid as _uuid
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base


class RestoreLog(Base):
    """Tracks each restore operation for audit purposes."""
    __tablename__ = "restore_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)
    backup_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    backup_filename = Column(String(500), nullable=False)
    restored_by = Column(String(255), nullable=False)
    services_restored = Column(Integer, nullable=False, default=0)
    dependencies_restored = Column(Integer, nullable=False, default=0)
    restored_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "backup_id": str(self.backup_id),
            "backup_filename": self.backup_filename,
            "restored_by": self.restored_by,
            "services_restored": self.services_restored,
            "dependencies_restored": self.dependencies_restored,
            "restored_at": self.restored_at.isoformat() if self.restored_at else None,
        }
