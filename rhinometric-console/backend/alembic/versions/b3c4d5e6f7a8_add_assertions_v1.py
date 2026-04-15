"""add assertions v1 tables and summary columns

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-04-15 20:00:00.000000

Creates:
  - service_assertions: assertion definitions per external service
  - assertion_results: failed assertion evaluation detail (failures only)
  - 5 summary columns on external_service_checks
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'b3c4d5e6f7a8'
down_revision = ('a1b2c3d4e5f6', '4a7b3c8d9e2f')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. service_assertions table ──────────────────────────────
    op.create_table(
        'service_assertions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('service_id', sa.Integer(),
                  sa.ForeignKey('external_services.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('assertion_type', sa.String(30), nullable=False),
        sa.Column('operator', sa.String(20), nullable=False),
        sa.Column('expected_value', sa.Text(), nullable=False),
        sa.Column('json_path', sa.String(500), nullable=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('severity', sa.String(20), nullable=False, server_default=sa.text("'warning'")),
        sa.Column('order', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.CheckConstraint(
            "assertion_type IN ('status_code', 'response_time', 'text_contains', 'json_path_equals')",
            name='chk_assertion_type',
        ),
        sa.CheckConstraint(
            "severity IN ('info', 'warning', 'critical')",
            name='chk_assertion_severity',
        ),
    )
    op.create_index('ix_svc_assertions_service', 'service_assertions', ['service_id'])
    op.create_index('ix_svc_assertions_enabled', 'service_assertions', ['service_id', 'enabled'])

    # ── 2. assertion_results table (failures only) ───────────────
    op.create_table(
        'assertion_results',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('check_id', sa.Integer(),
                  sa.ForeignKey('external_service_checks.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('assertion_id', UUID(as_uuid=True),
                  sa.ForeignKey('service_assertions.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('assertion_type', sa.String(30), nullable=False),
        sa.Column('assertion_name', sa.String(255), nullable=True),
        sa.Column('expected_value', sa.Text(), nullable=False),
        sa.Column('actual_value', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_assertion_results_check', 'assertion_results', ['check_id'])
    op.create_index('ix_assertion_results_svc_time', 'assertion_results', ['service_id', 'evaluated_at'])

    # ── 3. Summary columns on external_service_checks ────────────
    op.add_column('external_service_checks',
                  sa.Column('assertions_total', sa.Integer(), server_default=sa.text('0'), nullable=False))
    op.add_column('external_service_checks',
                  sa.Column('assertions_passed', sa.Integer(), server_default=sa.text('0'), nullable=False))
    op.add_column('external_service_checks',
                  sa.Column('assertions_failed', sa.Integer(), server_default=sa.text('0'), nullable=False))
    op.add_column('external_service_checks',
                  sa.Column('first_failed_assertion', sa.String(255), nullable=True))
    op.add_column('external_service_checks',
                  sa.Column('first_failed_message', sa.Text(), nullable=True))


def downgrade() -> None:
    # Drop summary columns from external_service_checks
    op.drop_column('external_service_checks', 'first_failed_message')
    op.drop_column('external_service_checks', 'first_failed_assertion')
    op.drop_column('external_service_checks', 'assertions_failed')
    op.drop_column('external_service_checks', 'assertions_passed')
    op.drop_column('external_service_checks', 'assertions_total')

    # Drop assertion_results table
    op.drop_index('ix_assertion_results_svc_time', table_name='assertion_results')
    op.drop_index('ix_assertion_results_check', table_name='assertion_results')
    op.drop_table('assertion_results')

    # Drop service_assertions table
    op.drop_index('ix_svc_assertions_enabled', table_name='service_assertions')
    op.drop_index('ix_svc_assertions_service', table_name='service_assertions')
    op.drop_table('service_assertions')
