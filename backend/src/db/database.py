"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.LOG_LEVEL == "DEBUG",
    pool_pre_ping=True,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    # Import all models to register them with Base

    Base.metadata.create_all(bind=engine)
