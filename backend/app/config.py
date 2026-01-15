"""Application configuration from environment variables."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Database
    database_url: str = "postgresql://postgres:postgres@postgres:5432/intelligence_db"

    # Authentication
    curator_token: str = "dev-token-change-in-production"

    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    # Logging
    log_level: str = "INFO"

    # Collector configuration
    enable_automated_collection: bool = True
    collection_schedule_hour: int = 9  # 9 AM UTC

    # LinkedIn scraping (optional - use with caution)
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None

    # Email ingestion
    email_ingestion_enabled: bool = False
    email_imap_server: Optional[str] = None
    email_username: Optional[str] = None
    email_password: Optional[str] = None

    # OpenAI configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"  # Cost-effective model for brief generation
    openai_temperature: float = 0.5  # Balanced temperature for precise but flexible outputs

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
