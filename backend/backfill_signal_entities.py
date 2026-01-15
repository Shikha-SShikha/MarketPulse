"""
Backfill script to create signal_entities relationships for existing signals.

This script:
1. Loads all signals from the database
2. For each signal, uses the legacy 'entity' field to find matching entities
3. Creates signal_entities records linking signals to entities
4. Marks the first entity as primary
"""

from app.database import SessionLocal
from app.models import Signal, Entity, SignalEntity
from app.collectors.classification import extract_entities_from_db
from sqlalchemy import text


def backfill_signal_entities():
    """Backfill signal_entities relationships for existing signals."""
    db = SessionLocal()

    try:
        # Get all signals that don't have entity relationships yet
        signals_without_entities = db.query(Signal).filter(
            ~Signal.id.in_(
                db.query(SignalEntity.signal_id).distinct()
            )
        ).all()

        print(f"Found {len(signals_without_entities)} signals without entity relationships")

        created_count = 0
        skipped_count = 0

        for signal in signals_without_entities:
            # Use the legacy entity field to find matching entities
            # First try exact match by name
            entity = db.query(Entity).filter(Entity.name == signal.entity).first()

            if not entity:
                # Try fuzzy match using the entity extraction logic
                # This searches both names and aliases
                entity_matches = extract_entities_from_db(
                    db,
                    f"{signal.entity} {signal.topic} {signal.evidence_snippet}",
                    use_cache=False
                )

                if entity_matches:
                    # Use the first match (highest confidence)
                    entity_name, entity_id = entity_matches[0]
                    entity = db.query(Entity).filter(Entity.id == entity_id).first()

            if entity:
                # Create signal_entity relationship
                signal_entity = SignalEntity(
                    signal_id=signal.id,
                    entity_id=entity.id,
                    is_primary=True  # Mark as primary since it's the only entity
                )
                db.add(signal_entity)
                created_count += 1

                if created_count % 50 == 0:
                    print(f"  Processed {created_count} signals...")
                    db.commit()
            else:
                print(f"  WARNING: Could not find entity for signal {signal.id} (entity: {signal.entity})")
                skipped_count += 1

        # Final commit
        db.commit()

        print(f"\nBackfill complete:")
        print(f"  Created: {created_count} signal-entity relationships")
        print(f"  Skipped: {skipped_count} signals (no matching entity found)")

        # Verify results
        total_relationships = db.query(SignalEntity).count()
        print(f"  Total signal_entities in database: {total_relationships}")

    except Exception as e:
        print(f"ERROR during backfill: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Starting signal_entities backfill...")
    print("=" * 60)
    backfill_signal_entities()
    print("=" * 60)
    print("Backfill complete!")
