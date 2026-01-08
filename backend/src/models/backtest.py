"""BacktestResult model for storing backtest results."""

from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class BacktestResult(BaseModel):
    """Backtest execution result."""

    __tablename__ = "backtest_results"
    __table_args__ = (Index("idx_backtest_user_created", "user_id", "created_at"),)

    # Foreign key to User
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Backtest parameters
    name = Column(String(100), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    stock_list_name = Column(String(50), nullable=False)
    initial_capital = Column(Numeric(15, 2), nullable=False)

    # Results
    final_value = Column(Numeric(15, 2), nullable=False)
    total_return_pct = Column(Numeric(8, 4), nullable=False)
    max_drawdown_pct = Column(Numeric(8, 4), nullable=False)
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    win_rate_pct = Column(Numeric(6, 2), nullable=False)

    # Detailed results as JSON (trades, daily_values, etc.)
    result_json = Column(JSON, nullable=False)

    # Execution timestamp (stored in created_at)

    # Relationships
    user = relationship("User", back_populates="backtest_results")

    def __repr__(self):
        return f"<BacktestResult(name={self.name}, return={self.total_return_pct}%)>"
