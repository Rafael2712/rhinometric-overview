"""add_sso_fields_to_users

Revision ID: 36a49ee275ae
Revises: 6465fc7249c3
Create Date: 2026-02-09 12:37:00.000000

Adds SSO fields to users table for future SAML/LDAP/OAuth2 integration
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '36a49ee275ae'
down_revision: Union[str, None] = '6465fc7249c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add SSO fields to users table.
    Idempotent: Only adds columns if they don't exist.
    """
    # Add sso_provider column
    op.execute(text("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='users' AND column_name='sso_provider'
            ) THEN
                ALTER TABLE users ADD COLUMN sso_provider VARCHAR(50);
            END IF;
        END $$;
    """))
    
    # Add sso_external_id column
    op.execute(text("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='users' AND column_name='sso_external_id'
            ) THEN
                ALTER TABLE users ADD COLUMN sso_external_id VARCHAR(255);
            END IF;
        END $$;
    """))
    
    # Create index on sso_external_id
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_users_sso_external_id 
        ON users(sso_external_id);
    """))
    
    # Set default 'local' for existing users
    op.execute(text("""
        UPDATE users 
        SET sso_provider = 'local' 
        WHERE sso_provider IS NULL;
    """))
    
    print("✅ SSO fields added to users table")


def downgrade() -> None:
    """
    Remove SSO fields from users table.
    """
    # Drop index
    op.execute(text("DROP INDEX IF EXISTS idx_users_sso_external_id;"))
    
    # Drop columns
    op.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS sso_external_id;"))
    op.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS sso_provider;"))
    
    print("✅ SSO fields removed from users table")
