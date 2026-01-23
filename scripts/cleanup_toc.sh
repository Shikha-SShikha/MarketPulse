#!/bin/bash
# Quick cleanup script for TOC signals

echo "🧹 TOC Signal Cleanup"
echo ""
echo "This will delete 199 TOC signals (Science journal Volume/Issue notices)"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

docker-compose exec -T backend python3 << 'EOF'
import re
from datetime import datetime
from app.database import get_db
from app.models import Signal

def is_toc_signal(signal):
    """Check if signal is a TOC notice."""
    text = f"{signal.entity} {signal.evidence_snippet}".lower()

    # Pattern 1: Volume/Issue citations
    if re.search(r'volume \d+,?\s*issue \d+', text):
        return True

    # Pattern 2: TOC alerts
    if any(kw in text for kw in ['toc alert', 'table of contents', 'latest articles from']):
        return True

    # Pattern 3: Very short evidence with mostly metadata
    if len(signal.evidence_snippet) < 100:
        metadata_keywords = ['volume', 'issue', 'page', 'january', 'february', 'march',
                            'april', 'may', 'june', 'july', 'august', 'september',
                            'october', 'november', 'december']
        word_count = len(signal.evidence_snippet.split())
        metadata_words = sum(1 for kw in metadata_keywords if kw in text)

        if word_count > 0 and (metadata_words / word_count) > 0.4:
            return True

    return False

db = next(get_db())

print("🔍 Finding TOC signals...")
signals = db.query(Signal).filter(Signal.deleted_at.is_(None)).all()

toc_signals = []
for signal in signals:
    if is_toc_signal(signal):
        toc_signals.append(signal)

print(f"Found {len(toc_signals)} TOC signals")
print("🗑️  Deleting...")

now = datetime.utcnow()
deleted_count = 0

for signal in toc_signals:
    signal.deleted_at = now
    signal.notes = (signal.notes or '') + f"\n[Auto-deleted {now.strftime('%Y-%m-%d')}: TOC cleanup]"
    deleted_count += 1

db.commit()

print(f"✅ Deleted {deleted_count} TOC signals")
print(f"   Remaining signals: {len(signals) - deleted_count}")

db.close()
EOF

echo ""
echo "✅ Cleanup complete!"
