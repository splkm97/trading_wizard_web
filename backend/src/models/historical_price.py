"""Historical stock price data model."""

from sqlalchemy import Column, String, Float, BigInteger, Index

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

    __table_args__ = (
        Index("ix_historical_prices_date", "date"),
        Index("ix_historical_prices_stock_date", "stock_code", "date"),
    )
