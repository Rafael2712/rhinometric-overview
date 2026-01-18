"""
Database connection and session management for Rhinometric Console
Supports PostgreSQL with SQLAlchemy ORM
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from contextlib import contextmanager

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rhinometric:rhinometric@postgres:5432/rhinometric"
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,        # Connection pool size
    max_overflow=20,     # Max connections beyond pool_size
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False           # Set to True for SQL query logging
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for ORM models
Base = declarative_base()

# ============================================================================
# DATABASE SESSION DEPENDENCY (FastAPI)
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    Automatically commits or rolls back on success/failure.
    
    Usage in FastAPI:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# ============================================================================
# CONTEXT MANAGER (for manual usage)
# ============================================================================

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for manual database session management.
    
    Usage:
        with get_db_session() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """
    Initialize database - create all tables.
    Should be called on application startup.
    """
    import rhinometric_console.backend.models.user  # noqa
    import rhinometric_console.backend.models.role  # noqa
    # Import all models here to ensure they're registered
    
    Base.metadata.create_all(bind=engine)

def check_db_connection() -> bool:
    """
    Check if database connection is working.
    Returns True if connection is successful, False otherwise.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

# ============================================================================
# HEALTH CHECK
# ============================================================================

def get_db_health() -> dict:
    """
    Get database health status.
    Returns dict with connection status and pool info.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
        
        pool = engine.pool
        
        return {
            "status": "healthy",
            "connected": True,
            "version": version,
            "pool_size": pool.size(),
            "pool_checked_out": pool.checkedout(),
            "pool_overflow": pool.overflow()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }
