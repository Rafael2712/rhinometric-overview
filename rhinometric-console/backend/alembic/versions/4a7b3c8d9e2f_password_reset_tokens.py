"""password_reset_tokens

Revision ID: 4a7b3c8d9e2f
Revises: 36a49ee275ae
Create Date: 2026-02-09 14:45:00.000000

Adds password reset functionality:
- password_reset_tokens table for self-service password recovery
- email_verified field in users table for security
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '4a7b3c8d9e2f'
down_revision: Union[str, None] = '36a49ee275ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create password_reset_tokens table and add email_verified field.
    Idempotent: Only creates/adds if they don't exist.
    """
    # Create password_reset_tokens table
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token VARCHAR(255) NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """))
    
    # Create indexes
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token 
        ON password_reset_tokens(token);
    """))
    
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires_at 
        ON password_reset_tokens(expires_at);
    """))
    
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_used 
        ON password_reset_tokens(used);
    """))
    
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id 
        ON password_reset_tokens(user_id);
    """))
    
    # Add email_verified column to users
    op.execute(text("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='users' AND column_name='email_verified'
            ) THEN
                ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
            END IF;
        END $$;
    """))
    
    # Create index on email_verified
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_users_email_verified 
        ON users(email_verified);
    """))
    
    # Set email_verified to TRUE for existing users with local auth
    op.execute(text("""
        UPDATE users 
        SET email_verified = TRUE 
        WHERE email_verified IS NULL AND sso_provider = 'local';
    """))
    
    print("✅ password_reset_tokens table and email_verified field added")


def downgrade() -> None:
    """
    Remove password_reset_tokens table and email_verified field.
    """
    # Drop indexes
    op.execute(text("DROP INDEX IF EXISTS idx_password_reset_tokens_token;"))
    op.execute(text("DROP INDEX IF EXISTS idx_password_reset_tokens_expires_at;"))
    op.execute(text("DROP INDEX IF EXISTS idx_password_reset_tokens_used;"))
    op.execute(text("DROP INDEX IF EXISTS idx_password_reset_tokens_user_id;"))
    op.execute(text("DROP INDEX IF EXISTS idx_users_email_verified;"))
    
    # Drop table
    op.execute(text("DROP TABLE IF EXISTS password_reset_tokens CASCADE;"))
    
    # Drop column
    op.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS email_verified;"))
    
    print("✅ password_reset_tokens table and email_verified field removed")
