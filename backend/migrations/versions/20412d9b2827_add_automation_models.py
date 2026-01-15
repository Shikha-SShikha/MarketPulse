"""add_automation_models

Revision ID: 20412d9b2827
Revises: 0f94eafc8765
Create Date: 2025-12-19 00:16:10.374004

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20412d9b2827'
down_revision: Union[str, None] = '0f94eafc8765'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create data_sources table
    op.create_table(
        'data_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_fetched_at', sa.DateTime(), nullable=True),
        sa.Column('last_success_at', sa.DateTime(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('default_confidence', sa.String(10), nullable=False, server_default='Medium'),
        sa.Column('default_impact_areas', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_data_sources_enabled', 'data_sources', ['enabled'])

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('link', sa.Text(), nullable=True),
        sa.Column('read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('dismissed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('ix_notifications_unread', 'notifications', ['read', 'dismissed', 'created_at'])

    # Add automation fields to signals table
    op.add_column('signals', sa.Column('status', sa.String(20), nullable=False, server_default='approved'))
    op.add_column('signals', sa.Column('data_source_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('signals', sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    op.add_column('signals', sa.Column('reviewed_by', sa.String(255), nullable=True))

    # Create indexes for new signal fields
    op.create_index('ix_signals_status', 'signals', ['status', 'deleted_at'])

    # Create foreign key constraint
    op.create_foreign_key(
        'fk_signals_data_source_id',
        'signals', 'data_sources',
        ['data_source_id'], ['id']
    )


def downgrade() -> None:
    # Drop foreign key and indexes
    op.drop_constraint('fk_signals_data_source_id', 'signals', type_='foreignkey')
    op.drop_index('ix_signals_status', 'signals')

    # Remove automation fields from signals
    op.drop_column('signals', 'reviewed_by')
    op.drop_column('signals', 'reviewed_at')
    op.drop_column('signals', 'data_source_id')
    op.drop_column('signals', 'status')

    # Drop notifications table
    op.drop_index('ix_notifications_unread', 'notifications')
    op.drop_index('ix_notifications_created_at', 'notifications')
    op.drop_table('notifications')

    # Drop data_sources table
    op.drop_index('ix_data_sources_enabled', 'data_sources')
    op.drop_table('data_sources')
