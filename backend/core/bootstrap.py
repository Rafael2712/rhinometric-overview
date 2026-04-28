"""
Bootstrap module - Ensures critical data exists on startup.
This script runs on every backend startup to guarantee:
1. Default roles exist (OWNER, ADMIN, OPERATOR, VIEWER)
2. Admin user exists with OWNER role
"""
import os
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import SessionLocal
from models.user import User
from models.role import Role, UserRole

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def seed_default_roles():
    """
    Ensure the 4 default roles exist.
    Idempotent - safe to call on every startup.
    """
    default_roles = [
        {"id": 1, "name": "OWNER",    "level": 1, "description": "Full platform access"},
        {"id": 2, "name": "ADMIN",    "level": 2, "description": "Administrative access"},
        {"id": 3, "name": "OPERATOR", "level": 3, "description": "Operational access"},
        {"id": 4, "name": "VIEWER",   "level": 4, "description": "Read-only access"},
    ]

    db: Session = SessionLocal()
    try:
        for role_data in default_roles:
            existing = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not existing:
                role = Role(**role_data)
                db.add(role)
                logger.info(f"[BOOTSTRAP] Created role: {role_data['name']}")
        db.commit()
        logger.info("[BOOTSTRAP] Default roles verified")
    except Exception as e:
        logger.error(f"[BOOTSTRAP] Failed to seed roles: {str(e)}")
        db.rollback()
    finally:
        db.close()


def ensure_admin_user():
    """
    Ensures admin user exists with credentials from environment variables.
    - If user doesn't exist: creates it with RHINO_ADMIN_USER/PASSWORD
    - If user exists: does NOT modify password (respects manual changes)
    - If database connection fails: logs error but doesn't crash

    This makes the admin user "immortal" - it will always exist after startup.
    """
    # Get admin credentials from environment (with secure defaults)
    admin_username = os.getenv("RHINO_ADMIN_USER", "admin")
    admin_password = os.getenv("RHINO_ADMIN_PASSWORD", "admin123")
    admin_email = os.getenv("RHINO_ADMIN_EMAIL", "admin@rhinometric.local")

    db: Session = SessionLocal()
    try:
        # Check if admin user exists
        user = db.query(User).filter(User.username == admin_username).first()

        if user:
            logger.info(f"[BOOTSTRAP] Admin user \'{admin_username}\' already exists - no changes made")
            return

        # Admin doesn't exist - create it
        logger.warning(f"[BOOTSTRAP] Admin user \'{admin_username}\' NOT FOUND - creating now...")

        new_admin = User(
            username=admin_username,
            email=admin_email,
            password_hash=get_password_hash(admin_password),
            full_name="System Administrator",
            is_active=True,
            must_change_password=True  # Force password change on first login
        )

        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

        # Assign OWNER role to admin
        owner_role = db.query(Role).filter(Role.name == "OWNER").first()
        if owner_role:
            user_role = UserRole(user_id=new_admin.id, role_id=owner_role.id)
            db.add(user_role)
            db.commit()

        logger.info(f"[BOOTSTRAP] Admin user \'{admin_username}\' created successfully with OWNER role")
        logger.info(f"[BOOTSTRAP] Default password: {admin_password} (change immediately!)")

    except Exception as e:
        logger.error(f"[BOOTSTRAP] Failed to ensure admin user exists: {str(e)}")
        db.rollback()

    finally:
        db.close()
