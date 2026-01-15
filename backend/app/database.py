"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import get_settings

settings = get_settings()

# Create engine with connection pooling
# pool_size: Number of connections to keep open (min connections)
# max_overflow: Additional connections allowed beyond pool_size (max = pool_size + max_overflow)
# pool_pre_ping: Verify connections are alive before using
engine = create_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=15,  # Total max: 5 + 15 = 20 connections
    pool_pre_ping=True,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
