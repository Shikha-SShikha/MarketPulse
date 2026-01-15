"""Quick test of entity management API endpoints."""

import sys
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services import get_entities, get_segment_statistics

def test_entities():
    """Test entity listing."""
    db: Session = SessionLocal()

    try:
        # Test get_entities
        print("=" * 60)
        print("Testing get_entities()...")
        print("=" * 60)

        entities, total = get_entities(db, limit=5)
        print(f"✓ Total entities: {total}")
        print(f"✓ Returned: {len(entities)} entities")

        for entity in entities[:3]:
            print(f"  - {entity.name} ({entity.segment})")

        # Test get_entities with segment filter
        print("\n" + "=" * 60)
        print("Testing get_entities(segment='competitor')...")
        print("=" * 60)

        competitors, comp_total = get_entities(db, segment="competitor")
        print(f"✓ Total competitors: {comp_total}")
        print(f"✓ Returned: {len(competitors)} entities")

        for entity in competitors[:3]:
            print(f"  - {entity.name}")

        # Test segment statistics
        print("\n" + "=" * 60)
        print("Testing get_segment_statistics()...")
        print("=" * 60)

        stats = get_segment_statistics(db, days=7)

        for segment, data in stats.items():
            print(f"  {segment}:")
            print(f"    - Entities: {data['entity_count']}")
            print(f"    - Total signals: {data['signal_count']}")
            print(f"    - Recent signals (7d): {data['recent_signals']}")

        print("\n✓ All entity API tests passed!")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    test_entities()
