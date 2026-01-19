"""rename_entity_metadata_column

Revision ID: 94e9eb8d3a28
Revises: 1962220a96b8
Create Date: 2025-12-23 21:01:59.415468

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94e9eb8d3a28'
down_revision: Union[str, None] = '1962220a96b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op: Column was already created as 'entity_metadata' in the initial migration
    # This migration is kept for version consistency but does nothing
    pass


def downgrade() -> None:
    # No-op: Nothing to undo
    pass
