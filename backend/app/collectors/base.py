"""Base collector class for all data sources."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import DataSource


class BaseCollector(ABC):
    """
    Abstract base class for all data collectors.

    Provides common interface and utility methods for RSS feeds,
    web scrapers, LinkedIn, and email ingestion.
    """

    def __init__(self, data_source: DataSource, db: Session):
        """
        Initialize collector with data source configuration.

        Args:
            data_source: DataSource model instance with configuration
            db: Database session for updating collection metadata
        """
        self.data_source = data_source
        self.db = db

    @abstractmethod
    async def collect(self) -> List[Dict]:
        """
        Collect signals from the source.

        Returns:
            List of signal dictionaries ready for create_signal()
            Each dict should contain: entity, event_type, topic, source_url,
            evidence_snippet, confidence, impact_areas, entity_tags, status
        """
        pass

    def update_source_metadata(self, success: bool, error: str = None):
        """
        Update DataSource collection metadata after collection attempt.

        Args:
            success: Whether collection succeeded
            error: Error message if collection failed
        """
        self.data_source.last_fetched_at = datetime.utcnow()

        if success:
            self.data_source.last_success_at = datetime.utcnow()
            self.data_source.error_count = 0
            self.data_source.last_error = None
        else:
            self.data_source.error_count += 1
            self.data_source.last_error = error

        self.db.commit()
        self.db.refresh(self.data_source)

    def extract_entities(self, text: str) -> List[str]:
        """
        Extract entity names from text.

        Simple implementation using common patterns.
        Can be enhanced with NER in Phase 3.

        Args:
            text: Text to extract entities from

        Returns:
            List of entity names found
        """
        entities = []

        # Common STM publishing entities
        known_entities = [
            "Springer", "Springer Nature", "Elsevier", "Wiley",
            "Taylor & Francis", "SAGE", "Oxford University Press",
            "Cambridge University Press", "IEEE", "Nature",
            "Science", "PLOS", "COPE", "ICMJE", "NIH", "Wellcome",
            "Plan S", "cOAlition S"
        ]

        text_lower = text.lower()

        for entity in known_entities:
            if entity.lower() in text_lower:
                entities.append(entity)

        return entities if entities else ["Unknown"]
