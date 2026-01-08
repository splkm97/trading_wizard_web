"""Portfolio model for user's investment portfolio."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Numeric, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class Portfolio(BaseModel):
    """User's investment portfolio with 1:1 relationship to User."""

    __tablename__ = "portfolios"

    # Foreign key to User (1:1 relationship)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)

    # Capital and balance
    initial_capital = Column(Numeric(15, 2), nullable=False, default=1000000)
    cash_balance = Column(Numeric(15, 2), nullable=False, default=1000000)

    # Timestamps
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="portfolio")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="portfolio", cascade="all, delete-orphan")

    def set_initial_capital(self, amount: Decimal):
        """Set initial capital and reset cash balance."""
        self.initial_capital = amount
        self.cash_balance = amount

    def __repr__(self):
        return f"<Portfolio(initial_capital={self.initial_capital}, cash_balance={self.cash_balance})>"
