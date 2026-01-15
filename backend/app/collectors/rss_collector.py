"""RSS feed collector for automated signal ingestion."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import feedparser
from dateutil import parser as date_parser
from sqlalchemy.orm import Session

from app.collectors.base import BaseCollector
from app.collectors.classification import classify_text, extract_entities_from_db, assign_confidence
from app.models import DataSource

logger = logging.getLogger(__name__)


class RSSCollector(BaseCollector):
    """
    Collector for RSS and Atom feeds.

    Parses feeds from publisher blogs, news sites, and industry sources,
    extracting signals with automatic classification.
    """

    def __init__(self, data_source: DataSource, db: Session):
        """
        Initialize RSS collector.

        Args:
            data_source: DataSource model instance with RSS feed URL
            db: Database session
        """
        super().__init__(data_source, db)
        self.feed_url = data_source.url

        if not self.feed_url:
            raise ValueError(f"DataSource {data_source.name} has no URL configured")

    async def collect(self) -> List[Dict]:
        """
        Parse RSS feed and extract signals.

        Returns:
            List of signal dictionaries ready for create_signal()
        """
        signals = []

        try:
            logger.info(f"Fetching RSS feed: {self.feed_url}")

            # Parse the feed
            feed = feedparser.parse(self.feed_url)

            # Check for errors
            if feed.bozo:
                error_msg = f"Feed parsing error: {feed.bozo_exception}"
                logger.warning(error_msg)
                # Continue anyway - some feeds work despite bozo flag

            if not feed.entries:
                logger.warning(f"No entries found in feed: {self.feed_url}")
                self.update_source_metadata(success=True)
                return signals

            logger.info(f"Found {len(feed.entries)} entries in feed")

            # Process each entry
            for entry in feed.entries:
                signal = self._process_entry(entry)
                if signal:
                    signals.append(signal)

            logger.info(f"Extracted {len(signals)} signals from {len(feed.entries)} entries")

            # Update source metadata
            self.update_source_metadata(success=True)

        except Exception as e:
            error_msg = f"Error collecting from RSS feed {self.feed_url}: {str(e)}"
            logger.error(error_msg)
            self.update_source_metadata(success=False, error=str(e))
            raise

        return signals

    def _process_entry(self, entry) -> Optional[Dict]:
        """
        Process a single feed entry into a signal.

        Args:
            entry: feedparser entry object

        Returns:
            Signal dictionary or None if entry should be skipped
        """
        try:
            # Extract basic data
            title = entry.get('title', '').strip()
            description = entry.get('summary', entry.get('description', '')).strip()
            link = entry.get('link', '')

            # Skip if no title or link
            if not title or not link:
                logger.debug(f"Skipping entry with no title or link")
                return None

            # Parse publication date
            published = self._parse_date(entry)

            # Skip old entries (only last 7 days)
            if published:
                # Make both datetimes timezone-aware for comparison
                now_utc = datetime.now(timezone.utc)
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
                days_old = (now_utc - published).days
                if days_old > 7:
                    logger.debug(f"Skipping old entry: {title} ({days_old} days old)")
                    return None

            # Combine title and description for classification
            text = f"{title} {description}"

            # Classify the signal
            classification = classify_text(text)

            if not classification:
                logger.debug(f"Could not classify entry: {title}")
                return None

            # Extract entities from database
            entity_matches = extract_entities_from_db(self.db, text)

            # Use first entity or source name as entity (legacy field)
            entity = entity_matches[0][0] if entity_matches else self.data_source.name

            # Extract entity IDs for signal_entities relationship
            entity_ids = [entity_id for _, entity_id in entity_matches] if entity_matches else []

            # Create evidence snippet (first 200 chars of description)
            evidence_snippet = description[:200] if len(description) > 200 else description

            # If description is too short, use title
            if len(evidence_snippet) < 50 and title:
                evidence_snippet = f"{title}. {description}"[:200]

            # Skip if evidence is still too short
            if len(evidence_snippet) < 50:
                logger.debug(f"Skipping entry with insufficient evidence: {title}")
                return None

            # Use data source's default confidence
            confidence = self.data_source.default_confidence

            # Determine status (auto-approve high confidence)
            status = 'approved' if confidence == 'High' else 'pending_review'

            # Build signal dictionary
            signal = {
                'entity': entity,
                'event_type': classification['event_type'],
                'topic': classification['topic'],
                'source_url': link,
                'evidence_snippet': evidence_snippet,
                'confidence': confidence,
                'impact_areas': classification['impact_areas'],
                'entity_tags': [name for name, _ in entity_matches[1:]] if len(entity_matches) > 1 else [],
                'curator_name': None,  # Automated signal
                'status': status,
                'data_source_id': self.data_source.id,
                'notes': f"Auto-collected from RSS feed on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                'entity_ids': entity_ids,  # For signal_entities relationship
            }

            logger.debug(f"Processed signal: {entity} - {classification['topic']}")

            return signal

        except Exception as e:
            logger.error(f"Error processing feed entry: {str(e)}")
            return None

    def _parse_date(self, entry) -> Optional[datetime]:
        """
        Parse publication date from feed entry.

        Tries multiple date fields and formats.

        Args:
            entry: feedparser entry object

        Returns:
            datetime object or None if date cannot be parsed
        """
        # Try different date fields
        date_fields = ['published', 'updated', 'created']

        for field in date_fields:
            date_str = entry.get(field)
            if date_str:
                try:
                    # Try parsing with dateutil (handles most formats)
                    return date_parser.parse(date_str)
                except Exception:
                    pass

                # Try feedparser's parsed dates
                try:
                    parsed_field = f"{field}_parsed"
                    if hasattr(entry, parsed_field):
                        time_struct = getattr(entry, parsed_field)
                        if time_struct:
                            return datetime(*time_struct[:6])
                except Exception:
                    pass

        # If no date found, return None (will be included anyway)
        return None
