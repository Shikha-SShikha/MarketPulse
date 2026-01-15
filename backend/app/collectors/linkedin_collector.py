"""LinkedIn collector for automated signal ingestion from influencer posts.

WARNING: LinkedIn scraping violates their Terms of Service.
- Use at your own risk
- Use dedicated account (not personal)
- Expect potential account suspension
- Implement conservative rate limiting
- Only scrape public profiles/posts

This collector is designed with caution:
- Long delays between requests (10-15 seconds)
- Limited posts per run (20-30 max)
- Human-like behavior patterns
- Daily collection only (not hourly)
"""

import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from sqlalchemy.orm import Session

from app.collectors.base import BaseCollector
from app.collectors.classification import classify_text, extract_entities
from app.models import DataSource

logger = logging.getLogger(__name__)


class LinkedInCollector(BaseCollector):
    """
    LinkedIn scraper for monitoring influencer posts.

    Configuration required in data_source.config:
    {
        "target_type": "profile" | "hashtag",
        "target_value": "username" or "#hashtag",
        "max_posts": 20,  # Limit per collection
        "min_delay_seconds": 10,  # Minimum delay between actions
        "max_delay_seconds": 15   # Maximum delay between actions
    }

    Credentials required in environment:
    LINKEDIN_EMAIL=your-email@example.com
    LINKEDIN_PASSWORD=your-password
    """

    def __init__(self, data_source: DataSource, db: Session, email: str = None, password: str = None):
        """
        Initialize LinkedIn collector.

        Args:
            data_source: DataSource model instance with LinkedIn config
            db: Database session
            email: LinkedIn email (or from config.py)
            password: LinkedIn password (or from config.py)
        """
        super().__init__(data_source, db)

        self.config = data_source.config or {}
        self.target_type = self.config.get('target_type', 'profile')
        self.target_value = self.config.get('target_value')
        self.max_posts = self.config.get('max_posts', 20)
        self.min_delay = self.config.get('min_delay_seconds', 10)
        self.max_delay = self.config.get('max_delay_seconds', 15)

        # Credentials
        self.email = email
        self.password = password

        if not self.target_value:
            raise ValueError(f"DataSource {data_source.name} missing 'target_value' in config")

        if not self.email or not self.password:
            raise ValueError("LinkedIn credentials not provided (email and password required)")

    async def collect(self) -> List[Dict]:
        """
        Scrape LinkedIn posts from configured profile or hashtag.

        Returns:
            List of signal dictionaries ready for create_signal()
        """
        signals = []

        try:
            logger.info(f"Starting LinkedIn collection: {self.target_type}={self.target_value}")
            logger.warning("LinkedIn scraping violates ToS - use dedicated account only!")

            async with async_playwright() as p:
                # Launch browser with stealth settings
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                    ]
                )

                # Create context with realistic settings
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US',
                )

                page = await context.new_page()

                try:
                    # Login
                    await self._login(page)

                    # Navigate to target
                    if self.target_type == 'profile':
                        await self._scrape_profile(page, signals)
                    elif self.target_type == 'hashtag':
                        await self._scrape_hashtag(page, signals)
                    else:
                        raise ValueError(f"Unknown target_type: {self.target_type}")

                    logger.info(f"Extracted {len(signals)} signals from LinkedIn")
                    self.update_source_metadata(success=True)

                except Exception as e:
                    logger.error(f"Error during LinkedIn scraping: {e}", exc_info=True)
                    self.update_source_metadata(success=False, error=str(e))
                    raise

                finally:
                    await browser.close()

        except Exception as e:
            error_msg = f"LinkedIn collection failed: {str(e)}"
            logger.error(error_msg)
            self.update_source_metadata(success=False, error=str(e))
            raise

        return signals

    async def _login(self, page):
        """Login to LinkedIn with provided credentials."""
        logger.info("Logging in to LinkedIn...")

        try:
            await page.goto('https://www.linkedin.com/login', timeout=30000)
            await self._human_delay()

            # Fill login form
            await page.fill('input[name="session_key"]', self.email)
            await self._human_delay(2, 4)

            await page.fill('input[name="session_password"]', self.password)
            await self._human_delay(2, 4)

            # Submit
            await page.click('button[type="submit"]')
            await self._human_delay(5, 8)

            # Wait for navigation to complete
            await page.wait_for_url('https://www.linkedin.com/feed/', timeout=30000)

            logger.info("LinkedIn login successful")

        except PlaywrightTimeout:
            logger.error("LinkedIn login timeout - check credentials or CAPTCHA required")
            raise ValueError("LinkedIn login failed - possible CAPTCHA or invalid credentials")
        except Exception as e:
            logger.error(f"LinkedIn login error: {e}")
            raise

    async def _scrape_profile(self, page, signals: List[Dict]):
        """Scrape posts from a LinkedIn profile."""
        logger.info(f"Scraping profile: {self.target_value}")

        # Navigate to profile
        profile_url = f"https://www.linkedin.com/in/{self.target_value}/recent-activity/all/"
        await page.goto(profile_url, timeout=30000)
        await self._human_delay()

        # Scroll to load posts
        await self._scroll_to_load_posts(page, self.max_posts)

        # Extract posts
        posts = await page.query_selector_all('div.feed-shared-update-v2')
        logger.info(f"Found {len(posts)} posts on profile")

        for i, post in enumerate(posts[:self.max_posts]):
            await self._human_delay()
            signal = await self._process_post(post)
            if signal:
                signals.append(signal)

            if (i + 1) % 5 == 0:
                logger.info(f"Processed {i + 1}/{min(len(posts), self.max_posts)} posts")

    async def _scrape_hashtag(self, page, signals: List[Dict]):
        """Scrape posts from a LinkedIn hashtag."""
        logger.info(f"Scraping hashtag: {self.target_value}")

        # Navigate to hashtag feed
        hashtag = self.target_value.replace('#', '')
        hashtag_url = f"https://www.linkedin.com/feed/hashtag/{hashtag}/"
        await page.goto(hashtag_url, timeout=30000)
        await self._human_delay()

        # Scroll to load posts
        await self._scroll_to_load_posts(page, self.max_posts)

        # Extract posts
        posts = await page.query_selector_all('div.feed-shared-update-v2')
        logger.info(f"Found {len(posts)} posts for hashtag")

        for i, post in enumerate(posts[:self.max_posts]):
            await self._human_delay()
            signal = await self._process_post(post)
            if signal:
                signals.append(signal)

            if (i + 1) % 5 == 0:
                logger.info(f"Processed {i + 1}/{min(len(posts), self.max_posts)} posts")

    async def _process_post(self, post) -> Optional[Dict]:
        """Process a single LinkedIn post into a signal."""
        try:
            # Extract text content
            text_elem = await post.query_selector('.feed-shared-update-v2__description, .feed-shared-text')
            if not text_elem:
                return None

            text = await text_elem.inner_text()
            text = text.strip()

            # Skip short posts
            if len(text) < 100:
                return None

            # Extract author
            author_elem = await post.query_selector('.feed-shared-actor__name, .feed-shared-actor__title')
            author = "LinkedIn User"
            if author_elem:
                author = await author_elem.inner_text()
                author = author.strip()

            # Extract link to post (for source_url)
            link_elem = await post.query_selector('a.feed-shared-control-menu__trigger, a[href*="/feed/update/"]')
            post_url = "https://www.linkedin.com"
            if link_elem:
                href = await link_elem.get_attribute('href')
                if href and href.startswith('http'):
                    post_url = href

            # Classify the post
            classification = classify_text(text)
            if not classification:
                logger.debug(f"Could not classify post from {author}")
                return None

            # Extract entities
            entities = extract_entities(text)

            # Use author as entity if no entities found
            entity = entities[0] if entities else author

            # Create evidence snippet (first 200 chars)
            evidence_snippet = text[:200] if len(text) > 200 else text

            # Use data source's default confidence
            confidence = self.data_source.default_confidence

            # Determine status (auto-approve high confidence)
            status = 'approved' if confidence == 'High' else 'pending_review'

            # Build signal dictionary
            signal = {
                'entity': entity,
                'event_type': classification['event_type'],
                'topic': classification['topic'],
                'source_url': post_url,
                'evidence_snippet': evidence_snippet,
                'confidence': confidence,
                'impact_areas': classification['impact_areas'],
                'entity_tags': entities if len(entities) > 1 else [author],
                'curator_name': None,  # Automated signal
                'status': status,
                'data_source_id': self.data_source.id,
                'notes': f"LinkedIn post by {author} - Auto-collected on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
            }

            logger.debug(f"Processed LinkedIn post: {entity} - {classification['topic']}")
            return signal

        except Exception as e:
            logger.error(f"Error processing LinkedIn post: {e}")
            return None

    async def _scroll_to_load_posts(self, page, target_count: int):
        """Scroll page to load more posts (LinkedIn infinite scroll)."""
        logger.info("Scrolling to load posts...")

        for _ in range(min(3, (target_count // 10) + 1)):  # Max 3 scrolls
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await self._human_delay(3, 5)

        logger.info("Scroll complete")

    async def _human_delay(self, min_sec: float = None, max_sec: float = None):
        """Add random delay to simulate human behavior."""
        min_delay = min_sec if min_sec is not None else self.min_delay
        max_delay = max_sec if max_sec is not None else self.max_delay

        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
