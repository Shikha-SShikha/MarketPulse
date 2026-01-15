"""add_embedding_vector_to_signals

Revision ID: a12962c79fff
Revises: a56385b6e2fb
Create Date: 2026-01-06 15:50:03.681700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'a12962c79fff'
down_revision: Union[str, None] = 'a56385b6e2fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add embedding column to signals table
    # Using 1536 dimensions for OpenAI's text-embedding-3-small model
    op.add_column('signals', sa.Column('embedding', Vector(1536), nullable=True))

    # Create an index for efficient similarity search using cosine distance
    # Using ivfflat index (good balance of speed and accuracy)
    # Lists parameter set to signals/1000 (will create ~70 clusters for 70K signals)
    op.execute('CREATE INDEX IF NOT EXISTS signals_embedding_idx ON signals USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')


def downgrade() -> None:
    # Drop the index first
    op.execute('DROP INDEX IF EXISTS signals_embedding_idx')

    # Drop the embedding column
    op.drop_column('signals', 'embedding')
