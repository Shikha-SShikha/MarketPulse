"""
Add additional data sources for comprehensive STM intelligence coverage.

Categories:
- Influencer blogs and newsletters
- Publisher blogs (customer sources)
- Industry organizations
- Research integrity sources
- Competitor news
"""

from app.database import SessionLocal
from app.models import DataSource
from sqlalchemy import func
import uuid
from datetime import datetime

db = SessionLocal()

# Data sources to add
NEW_SOURCES = [
    # INFLUENCER SOURCES
    {
        "name": "The Geyser (Lisa Hinchliffe)",
        "source_type": "rss",
        "url": "https://lisahinchliffe.com/feed/",
        "enabled": True,
        "default_confidence": "High",
        "config": None,
        "description": "Lisa Hinchliffe's blog on scholarly communication and libraries"
    },
    {
        "name": "Learned Publishing Journal",
        "source_type": "rss",
        "url": "https://onlinelibrary.wiley.com/feed/17414857/most-recent",
        "enabled": True,
        "default_confidence": "High",
        "config": None,
        "description": "Official journal of the Association of Learned and Professional Society Publishers"
    },
    {
        "name": "Against the Grain",
        "source_type": "web",
        "url": "https://www.charleston-hub.com/media/against-the-grain/",
        "enabled": True,
        "default_confidence": "Medium",
        "config": {
            "selectors": {
                "item": "article, .post",
                "title": "h2 a, h3 a, .entry-title a",
                "link": "h2 a, h3 a, .entry-title a",
                "description": ".entry-content, .entry-summary, p"
            },
            "base_url": "https://www.charleston-hub.com"
        },
        "description": "Library and publishing industry news"
    },

    # PUBLISHER BLOGS (Customer Sources)
    {
        "name": "Wiley Exchange Blog",
        "source_type": "rss",
        "url": "https://www.wiley.com/network/feed",
        "enabled": True,
        "default_confidence": "High",
        "config": None,
        "description": "Wiley's insights on research, publishing, and education"
    },
    {
        "name": "Springer Nature Blog",
        "source_type": "rss",
        "url": "https://www.springernature.com/gp/blog/feed",
        "enabled": True,
        "default_confidence": "High",
        "config": None,
        "description": "Springer Nature company news and insights"
    },
    {
        "name": "Elsevier Connect",
        "source_type": "rss",
        "url": "https://www.elsevier.com/connect/feed",
        "enabled": True,
        "default_confidence": "High",
        "config": None,
        "description": "Elsevier's blog on research and publishing trends"
    },
    {
        "name": "Taylor & Francis Newsroom",
        "source_type": "rss",
        "url": "https://newsroom.taylorandfrancisgroup.com/feed/",
        "enabled": True,
        "default_confidence": "High",
        "config": None,
        "description": "Taylor & Francis news and announcements"
    },
    {
        "name": "SAGE Ocean Blog",
        "source_type": "rss",
        "url": "https://ocean.sagepub.com/blog/feed",
        "enabled": True,
        "default_confidence": "Medium",
        "config": None,
        "description": "SAGE's blog on data science and social science research"
    },

    # INDUSTRY ORGANIZATIONS
    {
        "name": "COPE (Committee on Publication Ethics)",
        "source_type": "rss",
        "url": "https://publicationethics.org/feed",
        "enabled": True,
        "default_confidence": "High",
        "config": None,
        "description": "Publication ethics guidelines and news"
    },
    {
        "name": "Crossref Blog",
        "source_type": "rss",
        "url": "https://www.crossref.org/feed/",
        "enabled": True,
        "default_confidence": "High",
        "config": None,
        "description": "Crossref infrastructure updates and insights"
    },
    {
        "name": "ORCID Blog",
        "source_type": "rss",
        "url": "https://info.orcid.org/feed/",
        "enabled": True,
        "default_confidence": "High",
        "config": None,
        "description": "ORCID news and updates on researcher identifiers"
    },
    {
        "name": "STM Association News",
        "source_type": "rss",
        "url": "https://www.stm-assoc.org/feed/",
        "enabled": True,
        "default_confidence": "High",
        "config": None,
        "description": "International STM Publishers Association news"
    },

    # RESEARCH INTEGRITY & OPEN ACCESS
    {
        "name": "Retraction Watch",
        "source_type": "rss",
        "url": "https://retractionwatch.com/feed/",
        "enabled": True,
        "default_confidence": "High",
        "config": None,
        "description": "Tracking retractions and research integrity issues"
    },
    {
        "name": "SPARC (Open Access News)",
        "source_type": "rss",
        "url": "https://sparcopen.org/feed/",
        "enabled": True,
        "default_confidence": "Medium",
        "config": None,
        "description": "Scholarly Publishing and Academic Resources Coalition"
    },
    {
        "name": "PLOS Speaking of Medicine",
        "source_type": "rss",
        "url": "https://speakingofmedicine.plos.org/feed/",
        "enabled": True,
        "default_confidence": "Medium",
        "config": None,
        "description": "PLOS blog on open access and medical research"
    },

    # LIBRARY & INFORMATION SCIENCE
    {
        "name": "In the Library with the Lead Pipe",
        "source_type": "rss",
        "url": "https://www.inthelibrarywiththeleadpipe.org/feed/",
        "enabled": True,
        "default_confidence": "Medium",
        "config": None,
        "description": "Open access, peer-reviewed journal by and for library workers"
    },
    {
        "name": "ACRLog (ACRL Insider)",
        "source_type": "rss",
        "url": "https://acrlog.org/feed/",
        "enabled": True,
        "default_confidence": "Medium",
        "config": None,
        "description": "Association of College & Research Libraries blog"
    },
]


def add_data_sources():
    """Add new data sources to the database."""

    print("=" * 70)
    print("ADDING NEW DATA SOURCES")
    print("=" * 70)

    added = 0
    skipped = 0

    for source_data in NEW_SOURCES:
        # Check if source already exists
        existing = db.query(DataSource).filter(
            DataSource.name == source_data['name']
        ).first()

        if existing:
            print(f"⊘ Skipped: {source_data['name']} (already exists)")
            skipped += 1
            continue

        # Create new data source
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
        print(f"✓ Added: {source_data['name']} ({source_data['source_type']})")
        added += 1

    db.commit()

    print("\n" + "=" * 70)
    print(f"✅ Complete! Added {added} new sources, skipped {skipped}")
    print("=" * 70)

    # Show summary by category
    print("\nData Sources by Type:")
    type_counts = db.query(DataSource.source_type, func.count(DataSource.id)).group_by(DataSource.source_type).all()
    for source_type, count in type_counts:
        print(f"  {source_type}: {count} sources")

    print(f"\nTotal enabled sources: {db.query(DataSource).filter(DataSource.enabled == True).count()}")

    db.close()


if __name__ == "__main__":
    add_data_sources()
