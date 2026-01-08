"""Models for Turn-Based Trading Simulation Game.

Includes GameSession, SimulatedPosition, and SimulatedTrade.
"""

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
    Index,
    Text,
)
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class GameStatus(str, enum.Enum):
    """Game session status."""

    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class SimulatedTradeAction(str, enum.Enum):
    """Trade action type for simulation."""

    BUY = "BUY"
    SELL = "SELL"


class GameSession(BaseModel):
    """Simulation game session."""

    __tablename__ = "game_sessions"
    __table_args__ = (
        Index("idx_game_session_user", "user_id"),
        Index("idx_game_session_user_status", "user_id", "status"),
    )

    # Foreign key to User
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Game settings
    name = Column(String(100), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    current_date = Column(Date, nullable=False)

    # Portfolio state (embedded, not separate table)
    initial_capital = Column(Numeric(15, 2), nullable=False, default=Decimal("100000000"))
    cash_balance = Column(Numeric(15, 2), nullable=False)

    # Game status
    status = Column(
        Enum(GameStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=GameStatus.IN_PROGRESS,
    )

    # Recommendations cache (JSON string, regenerated only on turn advance)
    cached_recommendations = Column(Text, nullable=True)
    cached_recommendations_date = Column(Date, nullable=True)

    # Timestamps
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="game_sessions")
    positions = relationship(
        "SimulatedPosition",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    trades = relationship(
        "SimulatedTrade",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def is_game_over(self) -> bool:
        """Check if game has ended."""
        return self.status == GameStatus.COMPLETED or self.current_date >= self.end_date

    @property
    def turn_number(self) -> int:
        """Calculate current turn number (1-based)."""
        # This is a simplified calculation - actual implementation should count trading days
        if self.current_date <= self.start_date:
            return 1
        return (self.current_date - self.start_date).days + 1

    def __repr__(self):
        return f"<GameSession(id={self.id}, user_id={self.user_id}, status={self.status.value})>"


class SimulatedPosition(BaseModel):
    """Simulated stock position in a game session."""

    __tablename__ = "simulated_positions"
    __table_args__ = (
        UniqueConstraint("session_id", "stock_code", name="uq_simulated_position_session_stock"),
        Index("idx_simulated_position_session", "session_id"),
    )

    # Foreign key to GameSession
    session_id = Column(
        String(36), ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
    )

    # Stock information
    stock_code = Column(String(20), nullable=False)
    stock_name = Column(String(100), nullable=False)

    # Position details
    quantity = Column(Integer, nullable=False)
    avg_entry_price = Column(Numeric(15, 2), nullable=False)
    entry_date = Column(Date, nullable=False)

    # Timestamps
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session = relationship("GameSession", back_populates="positions")

    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost of position."""
        return Decimal(str(self.avg_entry_price)) * self.quantity

    def update_on_buy(self, quantity: int, price: Decimal, entry_date: date) -> None:
        """Update position on additional buy.

        Recalculates average entry price when adding to existing position.
        """
        total_cost = (Decimal(str(self.avg_entry_price)) * self.quantity) + (price * quantity)
        self.quantity += quantity
        self.avg_entry_price = total_cost / self.quantity
        # Don't update entry_date - keep original first entry date

    def __repr__(self):
        return f"<SimulatedPosition(stock_code={self.stock_code}, quantity={self.quantity})>"


class SimulatedTrade(BaseModel):
    """Simulated trade record in a game session."""

    __tablename__ = "simulated_trades"
    __table_args__ = (
        Index("idx_simulated_trade_session", "session_id"),
        Index("idx_simulated_trade_session_date", "session_id", "trade_date"),
    )

    # Foreign key to GameSession
    session_id = Column(
        String(36), ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
    )

    # Trade details
    trade_date = Column(Date, nullable=False)
    stock_code = Column(String(20), nullable=False)
    stock_name = Column(String(100), nullable=False)
    action = Column(
        Enum(SimulatedTradeAction, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(15, 2), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)

    # Realized P&L (only for SELL trades)
    realized_pnl = Column(Numeric(15, 2), nullable=True)
    realized_pnl_pct = Column(Numeric(8, 4), nullable=True)

    # Confidence score at time of trade (for BUY trades)
    confidence_score = Column(Numeric(5, 2), nullable=True)

    # Relationships
    session = relationship("GameSession", back_populates="trades")

    @classmethod
    def create_buy(
        cls,
        session_id: str,
        trade_date: date,
        stock_code: str,
        stock_name: str,
        quantity: int,
        price: Decimal,
        confidence_score: Optional[Decimal] = None,
    ) -> "SimulatedTrade":
        """Factory method to create a BUY trade."""
        return cls(
            session_id=session_id,
            trade_date=trade_date,
            stock_code=stock_code,
            stock_name=stock_name,
            action=SimulatedTradeAction.BUY,
            quantity=quantity,
            price=price,
            total_amount=price * quantity,
            confidence_score=confidence_score,
        )

    @classmethod
    def create_sell(
        cls,
        session_id: str,
        trade_date: date,
        stock_code: str,
        stock_name: str,
        quantity: int,
        price: Decimal,
        avg_entry_price: Decimal,
    ) -> "SimulatedTrade":
        """Factory method to create a SELL trade with realized P&L calculation."""
        total_amount = price * quantity
        cost_basis = avg_entry_price * quantity
        realized_pnl = total_amount - cost_basis
        realized_pnl_pct = (realized_pnl / cost_basis) * 100 if cost_basis > 0 else Decimal("0")

        return cls(
            session_id=session_id,
            trade_date=trade_date,
            stock_code=stock_code,
            stock_name=stock_name,
            action=SimulatedTradeAction.SELL,
            quantity=quantity,
            price=price,
            total_amount=total_amount,
            realized_pnl=realized_pnl,
            realized_pnl_pct=realized_pnl_pct,
        )

    def __repr__(self):
        return f"<SimulatedTrade({self.action.value} {self.stock_code} x{self.quantity} @ {self.price})>"


class RecommendationCache(BaseModel):
    """Cache for pre-computed recommendations by date."""

    __tablename__ = "recommendation_cache"
    __table_args__ = (
        UniqueConstraint("session_id", "target_date", name="uq_cache_session_date"),
        Index("idx_cache_session_date", "session_id", "target_date"),
    )

    session_id = Column(
        String(36), ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
    )
    target_date = Column(Date, nullable=False)
    recommendations_json = Column(Text, nullable=False)

    session = relationship("GameSession", backref="recommendation_caches")
