"""Data collection modules for automated signal ingestion."""

from app.collectors.base import BaseCollector
from app.collectors.rss_collector import RSSCollector

__all__ = ["BaseCollector", "RSSCollector"]
