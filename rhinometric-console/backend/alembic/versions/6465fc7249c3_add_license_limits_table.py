"""add_license_limits_table

Revision ID: 6465fc7249c3
Revises: fc2e72b0a860
Create Date: 2026-02-09 12:22:23.054225

Adds license_limits table for role-based tier control.
Integrates with License Server v2 to enforce max users per role.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '6465fc7249c3'
down_revision: Union[str, None] = 'fc2e72b0a860'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create license_limits table for role tiering.
    Idempotent: Only creates if not exists.
    """
    # Create license_limits table
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS license_limits (
            id SERIAL PRIMARY KEY,
            role_name VARCHAR(50) NOT NULL UNIQUE,
            max_users INTEGER,
            tier_required VARCHAR(50) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """))
    
    # Create index on role_name for fast lookups
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_license_limits_role 
        ON license_limits(role_name);
    """))
    
    # Insert default limits (idempotent with ON CONFLICT)
    op.execute(text("""
        INSERT INTO license_limits (role_name, max_users, tier_required, description) 
        VALUES
            ('OWNER', 1, 'trial', 'Maximum 1 owner per instance'),
            ('ADMIN', 2, 'trial', 'Maximum 2 admins on trial/annual tier'),
            ('OPERATOR', NULL, 'trial', 'Unlimited operators'),
            ('VIEWER', NULL, 'trial', 'Unlimited viewers')
        ON CONFLICT (role_name) DO NOTHING;
    """))
    
    # Add trigger for updated_at
    op.execute(text("""
        CREATE OR REPLACE FUNCTION update_license_limits_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))
    
    op.execute(text("""
        DROP TRIGGER IF EXISTS trigger_license_limits_updated_at ON license_limits;
        CREATE TRIGGER trigger_license_limits_updated_at
            BEFORE UPDATE ON license_limits
            FOR EACH ROW
            EXECUTE FUNCTION update_license_limits_updated_at();
    """))
    
    print("✅ license_limits table created successfully")


def downgrade() -> None:
    """
    Remove license_limits table and related objects.
    """
    # Drop trigger first
    op.execute(text("DROP TRIGGER IF EXISTS trigger_license_limits_updated_at ON license_limits;"))
    
    # Drop function
    op.execute(text("DROP FUNCTION IF EXISTS update_license_limits_updated_at();"))
    
    # Drop table
    op.execute(text("DROP TABLE IF EXISTS license_limits CASCADE;"))
    
    print("✅ license_limits table removed successfully")
