#!/usr/bin/env python3
"""
Test script for RSS collector.

Creates a test data source and runs the RSS collector to verify functionality.
"""

import asyncio
import sys
from uuid import uuid4

from app.database import SessionLocal
from app.models import DataSource, Signal
from app.collectors.rss_collector import RSSCollector
from app.services import create_signal_from_dict


async def test_rss_collector():
    """Test the RSS collector with a real feed."""
    db = SessionLocal()

    try:
        # Create a test data source (Nature News RSS feed)
        print("Creating test data source...")
        test_source = DataSource(
            id=uuid4(),
            name="Nature News (Test)",
            source_type="rss",
            url="https://www.nature.com/nature.rss",  # Nature's RSS feed
            enabled=True,
            default_confidence="High",
            default_impact_areas=["Tech", "Ops"],
        )

        db.add(test_source)
        db.commit()
        db.refresh(test_source)

        print(f"✓ Created data source: {test_source.name}")
        print(f"  URL: {test_source.url}")
        print()

        # Initialize the collector
        print("Initializing RSS collector...")
        collector = RSSCollector(test_source, db)

        # Collect signals
        print("Collecting signals from RSS feed...")
        signals = await collector.collect()

        print(f"\n✓ Collected {len(signals)} signals\n")

        # Display the first few signals
        for i, signal in enumerate(signals[:5]):
            print(f"Signal {i + 1}:")
            print(f"  Entity: {signal['entity']}")
            print(f"  Topic: {signal['topic']}")
            print(f"  Event Type: {signal['event_type']}")
            print(f"  Confidence: {signal['confidence']}")
            print(f"  Status: {signal['status']}")
            print(f"  Impact Areas: {', '.join(signal['impact_areas'])}")
            print(f"  Evidence: {signal['evidence_snippet'][:100]}...")
            print(f"  URL: {signal['source_url']}")
            print()

        # Save signals to database
        if signals:
            print(f"Saving {len(signals)} signals to database...")
            saved_count = 0
            for signal_data in signals:
                try:
                    signal = create_signal_from_dict(db, signal_data)
                    saved_count += 1
                except Exception as e:
                    print(f"  ✗ Error saving signal: {e}")

            print(f"✓ Saved {saved_count}/{len(signals)} signals to database\n")

        # Clean up test data (delete signals first, then source)
        print("Cleaning up test data...")
        if signals:
            # Delete signals created from this source
            db.query(Signal).filter(Signal.data_source_id == test_source.id).delete()
            db.commit()
            print(f"✓ Deleted {len(signals)} test signals")

        db.delete(test_source)
        db.commit()
        print("✓ Deleted test data source")
        print("\n✓ Test complete")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("RSS Collector Test")
    print("=" * 60)
    print()

    asyncio.run(test_rss_collector())
