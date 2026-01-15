"""
Sync data sources and entities based on user's comprehensive list.

Strategy:
1. Add missing industry news sources (RSS feeds where available)
2. Add all competitors as entities (news about them will appear in industry sources)
3. Add tools/platforms as entities (industry segment)
4. Add personas as influencer entities
"""

from app.database import SessionLocal
from app.models import DataSource, Entity
import uuid
from datetime import datetime
from sqlalchemy import func

db = SessionLocal()

# ==============================================================================
# INDUSTRY NEWS DATA SOURCES (RSS feeds and websites)
# ==============================================================================

INDUSTRY_NEWS_SOURCES = [
    {
        "name": "Research Information",
        "source_type": "rss",
        "url": "https://www.researchinformation.info/feed",
        "enabled": True,
        "default_confidence": "High",
        "description": "News and analysis for the research information industry"
    },
    {
        "name": "Society for Scholarly Publishing (SSP)",
        "source_type": "rss",
        "url": "https://scholarlypublishing.org/feed/",
        "enabled": True,
        "default_confidence": "High",
        "description": "SSP news and resources for scholarly publishing professionals"
    },
    {
        "name": "Digital Science News",
        "source_type": "rss",
        "url": "https://www.digital-science.com/feed/",
        "enabled": True,
        "default_confidence": "High",
        "description": "Digital Science company news and insights"
    },
    {
        "name": "Publishing Perspectives",
        "source_type": "rss",
        "url": "https://publishingperspectives.com/feed/",
        "enabled": True,
        "default_confidence": "Medium",
        "description": "International publishing news and trends"
    },
    {
        "name": "InPublishing",
        "source_type": "rss",
        "url": "https://www.inpublishing.co.uk/feed/",
        "enabled": True,
        "default_confidence": "Medium",
        "description": "UK publishing industry news and insights"
    },
    # Note: Journalology, Knowledge Speak, LSEP, IOS Press - will need manual URL verification
]

# ==============================================================================
# COMPETITOR ENTITIES (tracked but not scraped directly)
# ==============================================================================

COMPETITOR_ENTITIES = [
    # Major competitors
    {"name": "Straive", "aliases": ["Straive", "SPi Global"]},
    {"name": "MPS Limited", "aliases": ["MPS", "MPS Limited"]},
    {"name": "Amnet", "aliases": ["Amnet", "Amnet Systems"]},
    {"name": "Integra Software Services", "aliases": ["Integra", "Integra Software"]},
    {"name": "KnowledgeWorks Global", "aliases": ["KGL", "KnowledgeWorks Global", "KnowledgeWorks"]},
    {"name": "Nova Techset", "aliases": ["Nova Techset", "Nova Tech"]},
    {"name": "Transforma", "aliases": ["Transforma"]},
    {"name": "X Publisher", "aliases": ["X Publisher", "XPublisher"]},
    {"name": "Enago", "aliases": ["Enago", "Crimson Interactive"]},
    {"name": "Aptara", "aliases": ["Aptara", "iEnergizer Aptara"]},
    {"name": "Lumina Datamatics", "aliases": ["Lumina", "Lumina Datamatics"]},
    {"name": "Inera", "aliases": ["Inera"]},
    {"name": "SciSpace", "aliases": ["SciSpace", "Typeset"]},
]

# ==============================================================================
# TOOLS & PLATFORMS (industry segment)
# ==============================================================================

TOOLS_PLATFORMS = [
    # Editorial management systems
    {"name": "Aries Systems", "aliases": ["Aries", "Aries Systems", "Editorial Manager"]},
    {"name": "eJournalPress", "aliases": ["eJournalPress"]},
    {"name": "ScholarOne", "aliases": ["ScholarOne", "Clarivate ScholarOne"]},
    {"name": "Manuscript Manager", "aliases": ["Manuscript Manager"]},

    # Research infrastructure
    {"name": "PubMed", "aliases": ["PubMed", "NCBI PubMed"]},
    {"name": "PubMed Central", "aliases": ["PMC", "PubMed Central"]},
    {"name": "DOAJ", "aliases": ["DOAJ", "Directory of Open Access Journals"]},
    {"name": "CCDC", "aliases": ["CCDC", "Cambridge Crystallographic Data Centre"]},

    # Content tools
    {"name": "Trinka", "aliases": ["Trinka", "Trinka.ai"]},
    {"name": "Edifix", "aliases": ["Edifix"]},
    {"name": "iThenticate", "aliases": ["iThenticate", "Turnitin iThenticate"]},
    {"name": "ImageTwin", "aliases": ["ImageTwin", "ImageTwin.ai"]},

    # Publishing platforms
    {"name": "Brightcove", "aliases": ["Brightcove"]},
    {"name": "ReadCube", "aliases": ["ReadCube", "Digital Science ReadCube"]},
    {"name": "Continual Engine", "aliases": ["Continual Engine"]},
    {"name": "HighWire Press", "aliases": ["HighWire", "HighWire Press"]},
    {"name": "Atypon", "aliases": ["Atypon", "Wiley Atypon"]},
    {"name": "PubFactory", "aliases": ["PubFactory"]},
    {"name": "Glencore Software", "aliases": ["Glencore Software"]},
    {"name": "Ingenta", "aliases": ["Ingenta"]},
]

# ==============================================================================
# PERSONAS (influencer segment)
# ==============================================================================

PERSONAS = [
    {"name": "Ankor Rai", "aliases": ["Ankor Rai"]},
    {"name": "Rahul Arora", "aliases": ["Rahul Arora"]},
    {"name": "Aashish Agarwal", "aliases": ["Aashish Agarwal"]},
    {"name": "Sriram Subramanya", "aliases": ["Sriram Subramanya"]},
    {"name": "Atul Goel", "aliases": ["Atul Goel"]},
    {"name": "Ravi Venkataramani", "aliases": ["Ravi Venkataramani"]},
    {"name": "Abhishek Goel", "aliases": ["Abhishek Goel"]},
]


def add_data_sources():
    """Add missing industry news data sources."""
    print("\n" + "=" * 70)
    print("ADDING INDUSTRY NEWS DATA SOURCES")
    print("=" * 70)

    added = 0
    skipped = 0

    for source_data in INDUSTRY_NEWS_SOURCES:
        existing = db.query(DataSource).filter(
            DataSource.name == source_data['name']
        ).first()

        if existing:
            print(f"⊘ Skipped: {source_data['name']} (already exists)")
            skipped += 1
            continue

        source = DataSource(
            id=uuid.uuid4(),
            name=source_data['name'],
            source_type=source_data['source_type'],
            url=source_data['url'],
            enabled=source_data['enabled'],
            default_confidence=source_data['default_confidence'],
            config=source_data.get('config'),
            last_fetched_at=None,
            last_success_at=None,
            error_count=0,
            last_error=None,
            default_impact_areas=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(source)
        print(f"✓ Added: {source_data['name']}")
        added += 1

    db.commit()
    print(f"\n→ Added {added} sources, skipped {skipped}")
    return added


def add_entities(entities_list, segment, category_name):
    """Add entities to database."""
    print(f"\n" + "=" * 70)
    print(f"ADDING {category_name.upper()}")
    print("=" * 70)

    added = 0
    skipped = 0

    for entity_data in entities_list:
        existing = db.query(Entity).filter(
            Entity.name == entity_data['name']
        ).first()

        if existing:
            print(f"⊘ Skipped: {entity_data['name']} (already exists)")
            skipped += 1
            continue

        entity = Entity(
            id=uuid.uuid4(),
            name=entity_data['name'],
            segment=segment,
            aliases=entity_data['aliases'],
            entity_metadata=None,
            notes=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(entity)
        print(f"✓ Added: {entity_data['name']} ({segment})")
        added += 1

    db.commit()
    print(f"\n→ Added {added} entities, skipped {skipped}")
    return added


def show_summary():
    """Show final summary of data sources and entities."""
    print("\n" + "=" * 70)
    print("FINAL SYSTEM STATUS")
    print("=" * 70)

    # Data sources
    print("\n📁 DATA SOURCES:")
    type_counts = db.query(DataSource.source_type, func.count(DataSource.id)).group_by(DataSource.source_type).all()
    for stype, count in type_counts:
        print(f"  {stype.upper()}: {count} sources")

    enabled = db.query(DataSource).filter(DataSource.enabled == True).count()
    total_sources = db.query(DataSource).count()
    print(f"  Enabled: {enabled}/{total_sources}")

    # Entities
    print("\n📇 ENTITIES:")
    segment_counts = db.query(Entity.segment, func.count(Entity.id)).group_by(Entity.segment).order_by(Entity.segment).all()
    for segment, count in segment_counts:
        print(f"  {segment.capitalize()}: {count} entities")

    total_entities = db.query(Entity).count()
    print(f"  Total: {total_entities} entities")


def main():
    """Sync all data sources and entities."""
    print("\n" + "=" * 70)
    print("SYNCING DATA SOURCES & ENTITIES FROM USER LIST")
    print("=" * 70)

    # Add data sources
    sources_added = add_data_sources()

    # Add entities
    competitors_added = add_entities(COMPETITOR_ENTITIES, "competitor", "Competitor Entities")
    tools_added = add_entities(TOOLS_PLATFORMS, "industry", "Tools & Platforms")
    personas_added = add_entities(PERSONAS, "influencer", "Personas")

    # Show summary
    show_summary()

    print("\n" + "=" * 70)
    print("✅ SYNC COMPLETE!")
    print("=" * 70)
    print(f"\nAdded:")
    print(f"  {sources_added} data sources")
    print(f"  {competitors_added} competitors")
    print(f"  {tools_added} tools/platforms")
    print(f"  {personas_added} personas")
    print(f"\nTotal new items: {sources_added + competitors_added + tools_added + personas_added}")

    db.close()


if __name__ == "__main__":
    main()
