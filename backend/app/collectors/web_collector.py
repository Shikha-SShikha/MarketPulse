"""Web scraper collector for automated signal ingestion."""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.collectors.base import BaseCollector
from app.collectors.classification import classify_text, extract_entities_from_db
from app.models import DataSource

logger = logging.getLogger(__name__)


class WebCollector(BaseCollector):
    """
    Generic web scraper collector.

    Scrapes web pages using CSS selectors configured in data source config.
    Supports blog posts, news pages, and other content-rich pages.
    """

    def __init__(self, data_source: DataSource, db: Session):
        """
        Initialize web collector.

        Args:
            data_source: DataSource model instance with URL and CSS selectors
            db: Database session
        """
        super().__init__(data_source, db)
        self.url = data_source.url

        if not self.url:
            raise ValueError(f"DataSource {data_source.name} has no URL configured")

        # Get selectors from config
        self.config = data_source.config or {}
        self.selectors = self.config.get('selectors', {})

        if not self.selectors:
            raise ValueError(f"DataSource {data_source.name} has no selectors configured in config")

        # Base URL for resolving relative links
        self.base_url = self.config.get('base_url', self.url)

    async def collect(self) -> List[Dict]:
        """
        Scrape web page and extract signals.

        Returns:
            List of signal dictionaries ready for create_signal()
        """
        signals = []

        try:
            logger.info(f"Scraping web page: {self.url}")

            # Fetch the page
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.url,
                    headers={'User-Agent': 'Mozilla/5.0 (STM Intelligence Bot)'},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_msg = f"HTTP {response.status} fetching {self.url}"
                        logger.error(error_msg)
                        self.update_source_metadata(success=False, error=error_msg)
                        return signals

                    html = await response.text()

            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')

            # Extract items using configured selector
            item_selector = self.selectors.get('item')
            if not item_selector:
                raise ValueError("No 'item' selector configured")

            items = soup.select(item_selector)

            if not items:
                logger.warning(f"No items found using selector '{item_selector}' on {self.url}")
                self.update_source_metadata(success=True)
                return signals

            logger.info(f"Found {len(items)} items on page")

            # Process each item
            for item in items:
                signal = self._process_item(item)
                if signal:
                    signals.append(signal)

            logger.info(f"Extracted {len(signals)} signals from {len(items)} items")

            # Update source metadata
            self.update_source_metadata(success=True)

        except aiohttp.ClientError as e:
            error_msg = f"Network error scraping {self.url}: {str(e)}"
            logger.error(error_msg)
            self.update_source_metadata(success=False, error=str(e))
            raise

        except Exception as e:
            error_msg = f"Error scraping {self.url}: {str(e)}"
            logger.error(error_msg)
            self.update_source_metadata(success=False, error=str(e))
            raise

        return signals

    def _process_item(self, item) -> Optional[Dict]:
        """
        Process a single scraped item into a signal.

        Args:
            item: BeautifulSoup element representing one item

        Returns:
            Signal dictionary or None if item should be skipped
        """
        try:
            # Extract title
            title_selector = self.selectors.get('title')
            if not title_selector:
                logger.debug("No title selector configured, skipping item")
                return None

            title_elem = item.select_one(title_selector)
            if not title_elem:
                logger.debug(f"No title found using selector '{title_selector}'")
                return None

            title = title_elem.get_text(strip=True)

            # Extract link
            link_selector = self.selectors.get('link', 'a')  # default to 'a' tag
            link_elem = item.select_one(link_selector)
            if not link_elem:
                logger.debug(f"No link found using selector '{link_selector}'")
                return None

            link = link_elem.get('href', '')

            # Resolve relative URLs
            if link and not link.startswith(('http://', 'https://')):
                link = urljoin(self.base_url, link)

            # Extract description/snippet
            description_selector = self.selectors.get('description')
            description = ""
            if description_selector:
                desc_elem = item.select_one(description_selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)

            # Skip if no title or link
            if not title or not link:
                logger.debug("Skipping item with no title or link")
                return None

            # Combine title and description for classification
            text = f"{title} {description}"

            # Classify the signal
            classification = classify_text(text)

            if not classification:
                logger.debug(f"Could not classify item: {title}")
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
                logger.debug(f"Skipping item with insufficient evidence: {title}")
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
                'notes': f"Auto-collected from web scraping on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                'entity_ids': entity_ids,  # For signal_entities relationship
            }

            logger.debug(f"Processed signal: {entity} - {classification['topic']}")

            return signal

        except Exception as e:
            logger.error(f"Error processing scraped item: {str(e)}")
            return None
