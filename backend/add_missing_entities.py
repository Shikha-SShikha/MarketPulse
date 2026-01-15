"""Add entities for the new data sources we just added."""

from app.database import SessionLocal
from app.models import Entity
import uuid
from datetime import datetime

db = SessionLocal()

# Entities to add for new data sources
NEW_ENTITIES = [
    # Industry Organizations (sources we added)
    {"name": "Retraction Watch", "segment": "industry", "aliases": ["Retraction Watch"]},
    {"name": "ACRLog", "segment": "influencer", "aliases": ["ACRLog", "ACRL Insider"]},
    {"name": "STM Association", "segment": "industry", "aliases": ["STM Association", "STM-Assoc", "International STM Publishers Association"]},
    {"name": "SPARC", "segment": "industry", "aliases": ["SPARC", "Scholarly Publishing and Academic Resources Coalition"]},
    {"name": "In the Library with the Lead Pipe", "segment": "influencer", "aliases": ["Lead Pipe", "In the Library with the Lead Pipe"]},

    # Additional influencers we should track
    {"name": "Delta Think", "segment": "influencer", "aliases": ["Delta Think"]},
    {"name": "Roger Schonfeld", "segment": "influencer", "aliases": ["Roger Schonfeld"]},
    {"name": "Kent Anderson", "segment": "influencer", "aliases": ["Kent Anderson"]},
]


def add_entities():
    """Add missing entities to the database."""

    print("=" * 70)
    print("ADDING MISSING ENTITIES")
    print("=" * 70)

    added = 0
    skipped = 0

    for entity_data in NEW_ENTITIES:
        # Check if entity already exists
        existing = db.query(Entity).filter(
            Entity.name == entity_data['name']
        ).first()

        if existing:
            print(f"⊘ Skipped: {entity_data['name']} (already exists)")
            skipped += 1
            continue

        # Create new entity
        entity = Entity(
            id=uuid.uuid4(),
            name=entity_data['name'],
            segment=entity_data['segment'],
            aliases=entity_data['aliases'],
            entity_metadata=None,
            notes=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(entity)
        print(f"✓ Added: {entity_data['name']} ({entity_data['segment']})")
        added += 1

    db.commit()

    print("\n" + "=" * 70)
    print(f"✅ Complete! Added {added} new entities, skipped {skipped}")
    print("=" * 70)

    # Show totals
    from sqlalchemy import func
    counts = db.query(Entity.segment, func.count(Entity.id)).group_by(Entity.segment).all()
    print("\nEntity Totals by Segment:")
    for segment, count in counts:
        print(f"  {segment.capitalize()}: {count} entities")

    total = db.query(Entity).count()
    print(f"\nTotal entities: {total}")

    db.close()


if __name__ == "__main__":
    add_entities()
