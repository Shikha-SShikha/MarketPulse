"""Pytest fixtures for testing."""

import os

# Set DATABASE_URL for the app before importing it
# When running inside Docker (exec), use postgres hostname
# When running outside (local), use localhost
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/intelligence_db"
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


# Use the same PostgreSQL instance as docker-compose
TEST_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Return authorization headers for curator endpoints."""
    return {"Authorization": "Bearer dev-token-change-in-production"}


@pytest.fixture
def sample_signal():
    """Return sample signal data for testing."""
    return {
        "entity": "Test Publisher",
        "event_type": "announcement",
        "topic": "Test Topic",
        "source_url": "https://example.com/test",
        "evidence_snippet": "This is a test evidence snippet that is long enough to pass validation requirements.",
        "confidence": "High",
        "impact_areas": ["Ops", "Tech"],
    }
