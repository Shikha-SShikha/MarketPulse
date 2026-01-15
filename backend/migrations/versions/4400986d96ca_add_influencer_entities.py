"""add_influencer_entities

Revision ID: 4400986d96ca
Revises: 94e9eb8d3a28
Create Date: 2025-12-24 03:24:38.034736

"""
from typing import Sequence, Union
from datetime import datetime
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4400986d96ca'
down_revision: Union[str, None] = '94e9eb8d3a28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Influencer entities (newsletters, blogs, thought leaders)
INFLUENCER_ENTITIES = [
    # Blogs & Publications
    {"name": "The Scholarly Kitchen", "segment": "influencer", "aliases": ["Scholarly Kitchen", "The Scholarly Kitchen", "SSP Scholarly Kitchen"]},
    {"name": "The Geyser", "segment": "influencer", "aliases": ["The Geyser", "Geyser"]},
    {"name": "Learned Publishing", "segment": "influencer", "aliases": ["Learned Publishing"]},
    {"name": "Against the Grain", "segment": "influencer", "aliases": ["Against the Grain", "ATG"]},

    # Thought Leaders
    {"name": "Rick Anderson", "segment": "influencer", "aliases": ["Rick Anderson"]},
    {"name": "Ann Michael", "segment": "influencer", "aliases": ["Ann Michael"]},
    {"name": "Angela Cochran", "segment": "influencer", "aliases": ["Angela Cochran"]},
    {"name": "Phil Davis", "segment": "influencer", "aliases": ["Phil Davis"]},
    {"name": "Lisa Hinchliffe", "segment": "influencer", "aliases": ["Lisa Hinchliffe"]},
]


def upgrade() -> None:
    # 1. Update TNQ Technologies aliases (TNQ Books -> TNQ Tech)
    op.execute("""
        UPDATE entities
        SET aliases = ARRAY['TNQ', 'TNQ Tech', 'TNQ Technologies']
        WHERE name = 'TNQ Technologies'
    """)

    # 2. Add influencer entities
    entities_data = []
    now = datetime.utcnow()

    for entity in INFLUENCER_ENTITIES:
        entities_data.append({
            'id': str(uuid.uuid4()),
            'name': entity['name'],
            'segment': entity['segment'],
            'aliases': entity['aliases'],
            'entity_metadata': None,
            'notes': None,
            'created_at': now,
            'updated_at': now,
        })

    # Bulk insert influencer entities
    op.bulk_insert(
        sa.table('entities',
            sa.column('id', sa.String),
            sa.column('name', sa.String),
            sa.column('segment', sa.String),
            sa.column('aliases', sa.ARRAY(sa.String)),
            sa.column('entity_metadata', sa.JSON),
            sa.column('notes', sa.Text),
            sa.column('created_at', sa.DateTime),
            sa.column('updated_at', sa.DateTime),
        ),
        entities_data
    )


def downgrade() -> None:
    # Revert TNQ Technologies aliases
    op.execute("""
        UPDATE entities
        SET aliases = ARRAY['TNQ', 'TNQ Books', 'TNQ Technologies']
        WHERE name = 'TNQ Technologies'
    """)

    # Delete influencer entities
    op.execute("DELETE FROM entities WHERE segment = 'influencer'")
