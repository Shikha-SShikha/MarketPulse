#!/usr/bin/env python3
"""
Clean up irrelevant TOC (Table of Contents) signals from database.

This script identifies and removes signals that are just journal TOC notices
without actual content (e.g., "Science, Volume 391, Issue 6783...").

Safety features:
- Shows preview of what will be deleted
- Requires confirmation before deletion
- Uses soft-delete (sets deleted_at timestamp)
- Creates audit log
"""

import sys
import re
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from app.database import get_db
from app.models import Signal
from sqlalchemy import func


def is_toc_signal(signal: Signal) -> bool:
    """
    Check if signal is a TOC notice.

    Patterns that indicate TOC notices:
    - "Volume \d+, Issue \d+"
    - "Table of Contents"
    - Very short evidence with just citation
    - No meaningful content
    """
    text = f"{signal.entity} {signal.evidence_snippet}".lower()

    # Pattern 1: Volume/Issue citations
    if re.search(r'volume \d+,?\s*issue \d+', text):
        return True

    # Pattern 2: TOC alerts
    if any(kw in text for kw in ['toc alert', 'table of contents', 'latest articles from']):
        return True

    # Pattern 3: Very short evidence with just journal name
    if len(signal.evidence_snippet) < 100:
        # Check if it's mostly just journal metadata
        metadata_keywords = ['volume', 'issue', 'page', 'january', 'february', 'march',
                            'april', 'may', 'june', 'july', 'august', 'september',
                            'october', 'november', 'december']
        word_count = len(signal.evidence_snippet.split())
        metadata_words = sum(1 for kw in metadata_keywords if kw in text)

        # If more than 40% of words are metadata, it's likely a TOC
        if word_count > 0 and (metadata_words / word_count) > 0.4:
            return True

    return False


def find_toc_signals(db):
    """Find all TOC signals in database."""
    signals = db.query(Signal).filter(Signal.deleted_at.is_(None)).all()

    toc_signals = []
    for signal in signals:
        if is_toc_signal(signal):
            toc_signals.append(signal)

    return toc_signals


def preview_deletions(toc_signals, limit=10):
    """Show preview of what will be deleted."""
    print(f"\n{'='*80}")
    print(f"Found {len(toc_signals)} TOC signals to clean up")
    print(f"{'='*80}\n")

    if not toc_signals:
        print("✨ No TOC signals found. Database is clean!")
        return

    # Group by topic to show distribution
    topics = {}
    for sig in toc_signals:
        topics[sig.topic] = topics.get(sig.topic, 0) + 1

    print("Distribution by topic:")
    for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True):
        print(f"  {topic}: {count} signals")

    print(f"\nPreview (first {min(limit, len(toc_signals))} signals):")
    print("-" * 80)

    for i, sig in enumerate(toc_signals[:limit], 1):
        print(f"\n{i}. ID: {sig.id}")
        print(f"   Entity: {sig.entity}")
        print(f"   Topic: {sig.topic}")
        print(f"   Evidence: {sig.evidence_snippet[:100]}...")
        print(f"   Created: {sig.created_at}")


def soft_delete_signals(db, toc_signals):
    """Soft-delete signals by setting deleted_at timestamp."""
    now = datetime.utcnow()
    deleted_count = 0

    for signal in toc_signals:
        signal.deleted_at = now
        signal.notes = (signal.notes or '') + f"\n[Auto-deleted {now.strftime('%Y-%m-%d')}: TOC signal cleanup]"
        deleted_count += 1

    db.commit()
    return deleted_count


def create_audit_log(toc_signals, deleted_count):
    """Create audit log file."""
    log_file = Path(__file__).parent.parent / 'logs' / f'toc_cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    log_file.parent.mkdir(exist_ok=True)

    with open(log_file, 'w') as f:
        f.write(f"TOC Signal Cleanup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*80}\n\n")
        f.write(f"Total signals deleted: {deleted_count}\n\n")

        f.write("Deleted signals:\n")
        f.write("-" * 80 + "\n")

        for sig in toc_signals:
            f.write(f"\nID: {sig.id}\n")
            f.write(f"Entity: {sig.entity}\n")
            f.write(f"Topic: {sig.topic}\n")
            f.write(f"Event Type: {sig.event_type}\n")
            f.write(f"Created: {sig.created_at}\n")
            f.write(f"Evidence: {sig.evidence_snippet}\n")
            f.write(f"Source: {sig.source_url}\n")
            f.write("-" * 80 + "\n")

    return log_file


def main():
    """Main cleanup workflow."""
    print("\n🧹 TOC Signal Cleanup Script")
    print("This script will remove irrelevant journal TOC notices from the database.\n")

    # Connect to database
    db = next(get_db())

    try:
        # Find TOC signals
        print("🔍 Scanning database for TOC signals...")
        toc_signals = find_toc_signals(db)

        # Show preview
        preview_deletions(toc_signals, limit=10)

        if not toc_signals:
            return

        # Confirm deletion
        print(f"\n{'='*80}")
        print(f"⚠️  WARNING: This will soft-delete {len(toc_signals)} signals")
        print(f"{'='*80}")
        print("\nDeleted signals will:")
        print("  - Have deleted_at timestamp set")
        print("  - No longer appear in API queries")
        print("  - Be excluded from future briefs")
        print("  - Still exist in database (soft-delete, not hard-delete)")

        response = input(f"\nProceed with deletion? (yes/no): ").strip().lower()

        if response != 'yes':
            print("\n❌ Cleanup cancelled. No signals were deleted.")
            return

        # Perform deletion
        print("\n🗑️  Deleting TOC signals...")
        deleted_count = soft_delete_signals(db, toc_signals)

        # Create audit log
        print("📝 Creating audit log...")
        log_file = create_audit_log(toc_signals, deleted_count)

        print(f"\n✅ Cleanup complete!")
        print(f"   Deleted: {deleted_count} signals")
        print(f"   Audit log: {log_file}")

        # Show final stats
        total_signals = db.query(func.count(Signal.id)).filter(Signal.deleted_at.is_(None)).scalar()
        print(f"   Remaining active signals: {total_signals}")

    finally:
        db.close()


if __name__ == '__main__':
    main()
