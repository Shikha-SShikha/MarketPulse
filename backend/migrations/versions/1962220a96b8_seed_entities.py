"""seed_entities

Revision ID: 1962220a96b8
Revises: 51d2993fed9e
Create Date: 2025-12-23 20:56:01.912101

"""
from typing import Sequence, Union
from datetime import datetime
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1962220a96b8'
down_revision: Union[str, None] = '51d2993fed9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Entity classification with segments and aliases
ENTITIES = [
    # ==================== CUSTOMERS ====================
    # Major Commercial Publishers
    {"name": "Springer Nature", "segment": "customer", "aliases": ["Springer", "Springer Nature"]},
    {"name": "Elsevier", "segment": "customer", "aliases": ["Elsevier"]},
    {"name": "Wiley", "segment": "customer", "aliases": ["Wiley", "Wiley-Blackwell"]},
    {"name": "Taylor & Francis", "segment": "customer", "aliases": ["Taylor & Francis", "Taylor and Francis"]},
    {"name": "SAGE Publishing", "segment": "customer", "aliases": ["SAGE", "SAGE Publishing"]},
    {"name": "Oxford University Press", "segment": "customer", "aliases": ["Oxford University Press", "OUP"]},
    {"name": "Cambridge University Press", "segment": "customer", "aliases": ["Cambridge University Press", "CUP"]},

    # Journals (owned by publishers - potential customers)
    {"name": "Nature", "segment": "customer", "aliases": ["Nature"]},
    {"name": "Science", "segment": "customer", "aliases": ["Science"]},
    {"name": "Cell", "segment": "customer", "aliases": ["Cell"]},
    {"name": "The Lancet", "segment": "customer", "aliases": ["Lancet", "The Lancet"]},
    {"name": "BMJ", "segment": "customer", "aliases": ["BMJ"]},

    # Professional Societies (potential customers)
    {"name": "IEEE", "segment": "customer", "aliases": ["IEEE"]},
    {"name": "ACM", "segment": "customer", "aliases": ["ACM"]},
    {"name": "American Chemical Society", "segment": "customer", "aliases": ["ACS", "American Chemical Society"]},
    {"name": "American Physical Society", "segment": "customer", "aliases": ["APS", "American Physical Society"]},
    {"name": "American Institute of Physics", "segment": "customer", "aliases": ["AIP", "American Institute of Physics"]},
    {"name": "Royal Society of Chemistry", "segment": "customer", "aliases": ["RSC", "Royal Society of Chemistry"]},
    {"name": "American Mathematical Society", "segment": "customer", "aliases": ["AMS", "American Mathematical Society"]},

    # Open Access Publishers (potential customers)
    {"name": "PLOS", "segment": "customer", "aliases": ["PLOS", "Public Library of Science"]},
    {"name": "BioMed Central", "segment": "customer", "aliases": ["BioMed Central", "BMC"]},
    {"name": "Frontiers", "segment": "customer", "aliases": ["Frontiers"]},
    {"name": "MDPI", "segment": "customer", "aliases": ["MDPI"]},
    {"name": "PeerJ", "segment": "customer", "aliases": ["PeerJ"]},
    {"name": "eLife", "segment": "customer", "aliases": ["eLife"]},

    # ==================== COMPETITORS ====================
    # Production & Editorial Service Providers
    {"name": "Kriyadocs", "segment": "competitor", "aliases": ["Kriyadocs"]},
    {"name": "KnowledgeWorks Global", "segment": "competitor", "aliases": ["KnowledgeWorks", "KnowledgeWorks Global"]},
    {"name": "Cactus Communications", "segment": "competitor", "aliases": ["Cactus", "Cactus Communications"]},
    {"name": "Editage", "segment": "competitor", "aliases": ["Editage"]},
    {"name": "SPi Global", "segment": "competitor", "aliases": ["SPi Global", "SPi"]},
    {"name": "Straive", "segment": "competitor", "aliases": ["Straive"]},
    {"name": "Integra Software Services", "segment": "competitor", "aliases": ["Integra", "Integra Software Services"]},
    {"name": "TNQ Technologies", "segment": "competitor", "aliases": ["TNQ", "TNQ Books", "TNQ Technologies"]},
    {"name": "Exeter Premedia Services", "segment": "competitor", "aliases": ["Exeter Premedia", "Exeter Premedia Services"]},
    {"name": "Aptara", "segment": "competitor", "aliases": ["Aptara"]},
    {"name": "MPS Limited", "segment": "competitor", "aliases": ["MPS", "MPS Limited"]},
    {"name": "Newgen KnowledgeWorks", "segment": "competitor", "aliases": ["Newgen", "Newgen KnowledgeWorks"]},
    {"name": "Publishing Technology", "segment": "competitor", "aliases": ["Publishing Technology", "PubTech"]},

    # Editorial Management Systems (platform competitors)
    {"name": "Aries Systems", "segment": "competitor", "aliases": ["Aries Systems", "Editorial Manager"]},
    {"name": "ScholarOne", "segment": "competitor", "aliases": ["ScholarOne"]},
    {"name": "eJournal Press", "segment": "competitor", "aliases": ["eJournal Press"]},

    # ==================== INDUSTRY ====================
    # Infrastructure & Standards Organizations
    {"name": "Crossref", "segment": "industry", "aliases": ["Crossref"]},
    {"name": "ORCID", "segment": "industry", "aliases": ["ORCID"]},
    {"name": "DOI Foundation", "segment": "industry", "aliases": ["DOI", "DOI Foundation"]},
    {"name": "DOAJ", "segment": "industry", "aliases": ["DOAJ"]},
    {"name": "PubMed", "segment": "industry", "aliases": ["PubMed"]},
    {"name": "arXiv", "segment": "industry", "aliases": ["arXiv"]},

    # Integrity & Ethics Organizations
    {"name": "COPE", "segment": "industry", "aliases": ["COPE", "Committee on Publication Ethics"]},
    {"name": "ICMJE", "segment": "industry", "aliases": ["ICMJE", "International Committee of Medical Journal Editors"]},
    {"name": "Retraction Watch", "segment": "industry", "aliases": ["Retraction Watch"]},

    # Funders & Policy Organizations
    {"name": "National Institutes of Health", "segment": "industry", "aliases": ["NIH", "National Institutes of Health"]},
    {"name": "Wellcome Trust", "segment": "industry", "aliases": ["Wellcome", "Wellcome Trust"]},
    {"name": "Bill & Melinda Gates Foundation", "segment": "industry", "aliases": ["Gates Foundation", "Bill & Melinda Gates Foundation"]},
    {"name": "National Science Foundation", "segment": "industry", "aliases": ["NSF", "National Science Foundation"]},
    {"name": "cOAlition S", "segment": "industry", "aliases": ["Plan S", "cOAlition S"]},
    {"name": "European Commission", "segment": "industry", "aliases": ["European Commission", "EU"]},
]


def upgrade() -> None:
    """Seed the entities table with classified STM entities."""
    # Prepare bulk insert data
    entities_data = []
    now = datetime.utcnow()

    for entity in ENTITIES:
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

    # Bulk insert entities
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
    """Remove seeded entities."""
    # Delete all seeded entities
    op.execute("DELETE FROM entities")
