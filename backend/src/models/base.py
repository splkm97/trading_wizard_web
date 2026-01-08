"""Base model with common fields and mixins."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String

from src.db.database import Base


def generate_uuid() -> str:
    """Generate UUID as string for SQLite compatibility."""
    return str(uuid.uuid4())


class BaseModel(Base):
    """Abstract base model with UUID and timestamps."""

    __abstract__ = True

    id = Column(String(36), primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class TimestampMixin:
    """Mixin for models that need updated_at timestamp."""

    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
