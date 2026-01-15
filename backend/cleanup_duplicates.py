"""Script to clean up duplicate signals in the database."""

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.models import Signal
from app.config import get_settings

def cleanup_duplicate_signals():
    """Remove duplicate signals, keeping the oldest one for each URL."""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Find all URLs that have duplicates
        duplicates = (
            db.query(Signal.source_url)
            .filter(Signal.deleted_at.is_(None))
            .group_by(Signal.source_url)
            .having(func.count(Signal.id) > 1)
            .all()
        )

        total_deleted = 0

        for (url,) in duplicates:
            # Get all signals for this URL, ordered by creation date
            signals = (
                db.query(Signal)
                .filter(Signal.source_url == url, Signal.deleted_at.is_(None))
                .order_by(Signal.created_at)
                .all()
            )

            # Keep the first one, delete the rest
            keep = signals[0]
            delete = signals[1:]

            print(f"\nURL: {url[:80]}...")
            print(f"  Keeping: {keep.id} (created {keep.created_at})")
            print(f"  Deleting: {len(delete)} duplicates")

            for signal in delete:
                db.delete(signal)
                total_deleted += 1

        db.commit()
        print(f"\n✅ Cleanup complete! Deleted {total_deleted} duplicate signals.")
        print(f"   Found duplicates for {len(duplicates)} URLs.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during cleanup: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_duplicate_signals()
