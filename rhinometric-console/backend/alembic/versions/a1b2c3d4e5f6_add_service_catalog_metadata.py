"""add service catalog classification metadata

Revision ID: a1b2c3d4e5f6
Revises: 8b5d4e2f1a3c
Create Date: 2026-03-16 16:30:00.000000

Adds optional classification fields to external_services:
  - catalog_type (VARCHAR 50)  — REST_API, WEB_APP, DATABASE, etc.
  - category     (VARCHAR 100) — payments, authentication, etc.
  - tags         (JSONB)       — ["critical", "external"]

All fields are nullable — existing services are unaffected.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'a1b2c3d4e5f6'
down_revision = '8b5d4e2f1a3c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('external_services', sa.Column('catalog_type', sa.String(50), nullable=True))
    op.add_column('external_services', sa.Column('category', sa.String(100), nullable=True))
    op.add_column('external_services', sa.Column('tags', JSONB, nullable=True))
    op.create_index('ix_external_services_catalog_type', 'external_services', ['catalog_type'])
    op.create_index('ix_external_services_category', 'external_services', ['category'])


def downgrade() -> None:
    op.drop_index('ix_external_services_category', table_name='external_services')
    op.drop_index('ix_external_services_catalog_type', table_name='external_services')
    op.drop_column('external_services', 'tags')
    op.drop_column('external_services', 'category')
    op.drop_column('external_services', 'catalog_type')
