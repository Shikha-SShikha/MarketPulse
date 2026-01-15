"""add_entity_segmentation

Revision ID: 51d2993fed9e
Revises: 20412d9b2827
Create Date: 2025-12-23 20:53:02.624318

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '51d2993fed9e'
down_revision: Union[str, None] = '20412d9b2827'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create entities table
    op.create_table(
        'entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('segment', sa.String(50), nullable=False),
        sa.Column('aliases', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('entity_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Create indexes for entities table
    op.create_index('ix_entities_segment', 'entities', ['segment'])
    op.create_index('ix_entities_name', 'entities', ['name'])

    # Create signal_entities junction table
    op.create_table(
        'signal_entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('signal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # Create indexes for signal_entities table
    op.create_index('ix_signal_entities_signal', 'signal_entities', ['signal_id'])
    op.create_index('ix_signal_entities_entity', 'signal_entities', ['entity_id'])

    # Create unique constraint on (signal_id, entity_id)
    op.create_unique_constraint('uq_signal_entity', 'signal_entities', ['signal_id', 'entity_id'])

    # Create foreign key constraints with CASCADE delete
    op.create_foreign_key(
        'fk_signal_entities_signal',
        'signal_entities', 'signals',
        ['signal_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_signal_entities_entity',
        'signal_entities', 'entities',
        ['entity_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop foreign key constraints
    op.drop_constraint('fk_signal_entities_entity', 'signal_entities', type_='foreignkey')
    op.drop_constraint('fk_signal_entities_signal', 'signal_entities', type_='foreignkey')

    # Drop unique constraint
    op.drop_constraint('uq_signal_entity', 'signal_entities', type_='unique')

    # Drop indexes for signal_entities
    op.drop_index('ix_signal_entities_entity', 'signal_entities')
    op.drop_index('ix_signal_entities_signal', 'signal_entities')

    # Drop signal_entities table
    op.drop_table('signal_entities')

    # Drop indexes for entities
    op.drop_index('ix_entities_name', 'entities')
    op.drop_index('ix_entities_segment', 'entities')

    # Drop entities table
    op.drop_table('entities')
