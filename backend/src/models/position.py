"""Position model for held stock positions."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class Position(BaseModel):
    """Stock position in a portfolio."""

    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "stock_code", name="uq_position_portfolio_stock"),
        Index("idx_position_portfolio", "portfolio_id"),
    )

    # Foreign key to Portfolio
    portfolio_id = Column(String(36), ForeignKey("portfolios.id"), nullable=False)

    # Stock information
    stock_code = Column(String(6), nullable=False)
    stock_name = Column(String(100), nullable=False)

    # Position details
    quantity = Column(Integer, nullable=False)
    avg_entry_price = Column(Numeric(12, 2), nullable=False)
    first_entry_date = Column(Date, nullable=False)

    # From trading_wizard_bundle - entry reason and confidence
    entry_reason = Column(String(50), nullable=True)
    confidence_score = Column(Integer, nullable=True)  # 0-100

    partial_take_profit_executed = Column(Boolean, nullable=False, default=False)

    # Timestamps
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")

    def update_on_buy(
        self,
        quantity: int,
        price: Decimal,
        entry_date: date,
        reason: str = None,
        confidence: int = None,
    ):
        """Update position on a buy trade.

        Recalculates average entry price when adding to existing position.
        """
        if self.quantity == 0:
            # New position
            self.quantity = quantity
            self.avg_entry_price = price
            self.first_entry_date = entry_date
            self.entry_reason = reason
            self.confidence_score = confidence
        else:
            # Add to existing position - recalculate average price
            total_cost = (Decimal(str(self.avg_entry_price)) * self.quantity) + (price * quantity)
            self.quantity += quantity
            self.avg_entry_price = total_cost / self.quantity

    def update_on_sell(self, quantity: int) -> Decimal:
        """Update position on a sell trade.

        Returns the average entry price for P&L calculation.
        Raises ValueError if trying to sell more than owned.
        """
        if quantity > self.quantity:
            raise ValueError(f"Cannot sell {quantity} shares, only {self.quantity} owned")

        avg_price = Decimal(str(self.avg_entry_price))
        self.quantity -= quantity
        return avg_price

    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost of position."""
        return Decimal(str(self.avg_entry_price)) * self.quantity

    def mark_take_profit_executed(self) -> None:
        self.partial_take_profit_executed = True

    def __repr__(self):
        return f"<Position(stock_code={self.stock_code}, quantity={self.quantity})>"
