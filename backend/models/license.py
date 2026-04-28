from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from models.user import Base

class LicenseLimit(Base):
    __tablename__ = "license_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    feature = Column(String(100), nullable=False, unique=True)
    max_value = Column(Integer, nullable=False, default=-1)
    current_value = Column(Integer, nullable=False, default=0)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<LicenseLimit {self.feature}: {self.current_value}/{self.max_value}>"

    def to_dict(self):
        return {
            "id": self.id,
            "feature": self.feature,
            "max_value": self.max_value,
            "current_value": self.current_value,
            "description": self.description,
            "is_active": self.is_active
        }
