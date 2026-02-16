"""
RHINOMETRIC v2.4.0 - Dashboard Builder Database Models
======================================================

SQLAlchemy ORM models para persistencia PostgreSQL.
"""

from sqlalchemy import Column, String, Integer, JSON, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class Dashboard(Base):
    """Dashboard storage table."""
    __tablename__ = "dashboards"
    
    id = Column(String(100), primary_key=True, index=True)
    title = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)  # Array de strings
    template = Column(String(50), nullable=True)
    
    # Dashboard configuration (panels, time_range, variables, etc.)
    config = Column(JSON, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    
    def __repr__(self):
        return f"<Dashboard(id='{self.id}', title='{self.title}', version={self.version})>"


# Database connection - Build from env vars (compatible with docker-compose)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "rhinometric")
POSTGRES_USER = os.getenv("POSTGRES_USER", "rhinometric")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "rhinometric")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency para obtener sesión de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Inicializar base de datos (crear tablas)."""
    Base.metadata.create_all(bind=engine)
