"""Trade model for individual trade records."""

from __future__ import annotations

import enum
from datetime import date
from decimal import Decimal

from sqlalchemy import Column, String, Integer, Numeric, Date, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class TradeAction(enum.Enum):
    """Trade action type."""

    BUY = "BUY"
    SELL = "SELL"


class Trade(BaseModel):
    """Individual trade record."""

    __tablename__ = "trades"
    __table_args__ = (
        Index("idx_trade_portfolio_date", "portfolio_id", "trade_date"),
        Index("idx_trade_stock", "stock_code"),
    )

    # Foreign key to Portfolio
    portfolio_id = Column(String(36), ForeignKey("portfolios.id"), nullable=False)

    # Trade details
    trade_date = Column(Date, nullable=False)
    stock_code = Column(String(6), nullable=False)
    stock_name = Column(String(100), nullable=False)
    action = Column(Enum(TradeAction), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)

    # Realized PnL (only for SELL trades)
    realized_pnl = Column(Numeric(15, 2), nullable=True)

    # Trade reason
    reason = Column(String(100), nullable=True)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="trades")

    @classmethod
    def create_buy(
        cls,
        portfolio_id: str,
        trade_date: date,
        stock_code: str,
        stock_name: str,
        quantity: int,
        price: Decimal,
        reason: str | None = None,
    ) -> Trade:
        """Factory method to create a BUY trade."""
        total_amount = Decimal(quantity) * price
        return cls(
            portfolio_id=portfolio_id,
            trade_date=trade_date,
            stock_code=stock_code,
            stock_name=stock_name,
            action=TradeAction.BUY,
            quantity=quantity,
            price=price,
            total_amount=total_amount,
            reason=reason,
        )

    @classmethod
    def create_sell(
        cls,
        portfolio_id: str,
        trade_date: date,
        stock_code: str,
        stock_name: str,
        quantity: int,
        price: Decimal,
        realized_pnl: Decimal,
        reason: str | None = None,
    ) -> Trade:
        """Factory method to create a SELL trade."""
        total_amount = Decimal(quantity) * price
        return cls(
            portfolio_id=portfolio_id,
            trade_date=trade_date,
            stock_code=stock_code,
            stock_name=stock_name,
            action=TradeAction.SELL,
            quantity=quantity,
            price=price,
            total_amount=total_amount,
            realized_pnl=realized_pnl,
            reason=reason,
        )

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy trade."""
        return self.action == TradeAction.BUY

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell trade."""
        return self.action == TradeAction.SELL

    def __repr__(self):
        return f"<Trade({self.action.value} {self.stock_code} x{self.quantity} @ {self.price})>"
