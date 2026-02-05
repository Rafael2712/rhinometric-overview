"""
Bootstrap module - Ensures critical data exists on startup.
This script runs on every backend startup to guarantee admin user exists.
"""
import os
import logging
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import SessionLocal
from models.user import User

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

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
    admin_password = os.getenv("RHINO_ADMIN_PASSWORD", "271211Rc")
    admin_email = os.getenv("RHINO_ADMIN_EMAIL", "admin@rhinometric.local")
    
    db: Session = SessionLocal()
    try:
        # Check if admin user exists
        user = db.query(User).filter(User.username == admin_username).first()
        
        if user:
            logger.info(f"[BOOTSTRAP] Admin user '{admin_username}' already exists - no changes made")
            return
        
        # Admin doesn't exist - create it
        logger.warning(f"[BOOTSTRAP] Admin user '{admin_username}' NOT FOUND - creating now...")
        
        new_admin = User(
            username=admin_username,
            email=admin_email,
            password_hash=get_password_hash(admin_password),
            full_name="System Administrator",
            is_active=True,
            must_change_password=False
        )
        
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        
        # Create owner role for admin
        from models.user_role import UserRole
        admin_role = UserRole(
            user_id=new_admin.id,
            role="owner"
        )
        db.add(admin_role)
        db.commit()
        
        logger.info(f"[BOOTSTRAP] ✅ Admin user '{admin_username}' created successfully with 'owner' role")
        
    except Exception as e:
        logger.error(f"[BOOTSTRAP] ❌ Failed to ensure admin user exists: {str(e)}")
        db.rollback()
        # Don't crash the app - just log the error
        
    finally:
        db.close()
