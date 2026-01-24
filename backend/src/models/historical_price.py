"""Historical stock price data model."""

from sqlalchemy import BigInteger, Column, DateTime, Float, Index, String

from src.db.database import Base


class HistoricalPrice(Base):
    """Historical OHLCV data for stocks."""

    __tablename__ = "historical_prices"

    stock_code = Column(String(10), primary_key=True)
    date = Column(String(10), primary_key=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    last_fetched_at = Column(DateTime, nullable=True)  # yfinance fetch timestamp

    __table_args__ = (
        Index("ix_historical_prices_date", "date"),
        Index("ix_historical_prices_stock_date", "stock_code", "date"),
    )
