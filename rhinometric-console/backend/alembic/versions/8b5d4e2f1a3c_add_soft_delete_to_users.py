"""add soft-delete columns to users

Revision ID: 8b5d4e2f1a3c
Revises: 36a49ee275ae
Create Date: 2026-03-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '8b5d4e2f1a3c'
down_revision = '36a49ee275ae'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('deleted_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.create_index('ix_users_is_deleted', 'users', ['is_deleted'])


def downgrade() -> None:
    op.drop_index('ix_users_is_deleted', table_name='users')
    op.drop_column('users', 'deleted_by')
    op.drop_column('users', 'deleted_at')
    op.drop_column('users', 'is_deleted')
