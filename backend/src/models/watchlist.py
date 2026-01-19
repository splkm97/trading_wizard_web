"""Watchlist model for user's stock watchlists with insights."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from src.models.base import BaseModel, TimestampMixin


class Watchlist(BaseModel, TimestampMixin):
    """User's watchlist entry with stock insights."""

    __tablename__ = "watchlists"

    # Foreign key to User
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Stock information
    stock_code = Column(String(6), nullable=False)
    stock_name = Column(String(100), nullable=False)

    # Current price and indicators (updated periodically)
    current_price = Column(String(50), nullable=True)
    indicators = Column(Text, nullable=True)
    recommendation_score = Column(Integer, nullable=True)
    recommendation_reason = Column(String(500), nullable=True)

    # Timestamps
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="watchlists")

    __table_args__ = (Index("idx_watchlist_user_stock", "user_id", "stock_code", unique=True),)

    def __repr__(self):
        return f"<Watchlist(user_id={self.user_id}, stock_code={self.stock_code})>"
