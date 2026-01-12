"""
Price updater service for fetching and saving closing prices.

Runs after market close (15:30 KST) to update historical_prices table.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import List, Optional

import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def get_db_engine() -> Optional[Engine]:
    """Get SQLAlchemy engine from settings."""
    try:
        from src.core.config import settings
        return create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    except Exception as e:
        logger.error(f"Failed to create DB engine: {e}")
        return None


def fetch_closing_price(stock_code: str) -> Optional[dict]:
    """
    Fetch today's closing price from yfinance.

    Args:
        stock_code: 6-digit Korean stock code

    Returns:
        Dict with OHLCV data or None
    """
    ticker = f"{stock_code}.KS"
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")

        if hist.empty:
            # Try KOSDAQ
            ticker = f"{stock_code}.KQ"
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")

        if hist.empty:
            return None

        latest = hist.iloc[-1]
        return {
            "date": hist.index[-1].date(),
            "open": float(latest["Open"]),
            "high": float(latest["High"]),
            "low": float(latest["Low"]),
            "close": float(latest["Close"]),
            "volume": int(latest["Volume"]),
        }
    except Exception as e:
        logger.debug(f"Failed to fetch price for {stock_code}: {e}")
        return None


def save_closing_price(
    stock_code: str,
    price_data: dict,
    engine: Optional[Engine] = None
) -> bool:
    """
    Save closing price to historical_prices table.

    Uses UPSERT (INSERT ... ON CONFLICT DO UPDATE) for idempotency.

    Args:
        stock_code: 6-digit stock code
        price_data: Dict with date, open, high, low, close, volume
        engine: SQLAlchemy engine (creates one if not provided)

    Returns:
        True if saved successfully
    """
    if engine is None:
        engine = get_db_engine()
        if engine is None:
            return False

    # Check if using PostgreSQL or SQLite
    is_postgres = "postgresql" in str(engine.url)

    if is_postgres:
        query = text("""
            INSERT INTO historical_prices (stock_code, date, open, high, low, close, volume)
            VALUES (:stock_code, :date, :open, :high, :low, :close, :volume)
            ON CONFLICT (stock_code, date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume
        """)
    else:
        # SQLite uses INSERT OR REPLACE
        query = text("""
            INSERT OR REPLACE INTO historical_prices (stock_code, date, open, high, low, close, volume)
            VALUES (:stock_code, :date, :open, :high, :low, :close, :volume)
        """)

    try:
        with engine.begin() as conn:
            conn.execute(query, {
                "stock_code": stock_code,
                "date": price_data["date"].isoformat() if isinstance(price_data["date"], date) else price_data["date"],
                "open": price_data["open"],
                "high": price_data["high"],
                "low": price_data["low"],
                "close": price_data["close"],
                "volume": price_data["volume"],
            })
        return True
    except Exception as e:
        logger.error(f"Failed to save price for {stock_code}: {e}")
        return False


def get_stocks_needing_update(engine: Optional[Engine] = None) -> List[str]:
    """
    Get list of stock codes that need price updates for today.

    Returns stocks from historical_prices that don't have today's data.
    """
    if engine is None:
        engine = get_db_engine()
        if engine is None:
            return []

    today = date.today()

    query = text("""
        SELECT DISTINCT stock_code
        FROM historical_prices
        WHERE stock_code NOT IN (
            SELECT stock_code
            FROM historical_prices
            WHERE date = :today
        )
    """)

    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"today": today.isoformat()})
            return [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Failed to get stocks needing update: {e}")
        return []


def update_all_closing_prices(stock_codes: Optional[List[str]] = None) -> dict:
    """
    Update closing prices for all stocks or specified list.

    Args:
        stock_codes: Optional list of stock codes. If None, updates stocks
                     that are in DB but missing today's data.

    Returns:
        Dict with update statistics
    """
    engine = get_db_engine()
    if engine is None:
        return {"success": 0, "failed": 0, "error": "Database unavailable"}

    if stock_codes is None:
        stock_codes = get_stocks_needing_update(engine)

    if not stock_codes:
        logger.info("No stocks need price updates")
        return {"success": 0, "failed": 0, "skipped": "No stocks need updates"}

    logger.info(f"Updating closing prices for {len(stock_codes)} stocks...")

    import time

    success = 0
    failed = 0
    batch_size = 10  # Process in batches
    delay_between_batches = 2.0  # 2 seconds between batches (rate limiting)

    for i, stock_code in enumerate(stock_codes):
        price_data = fetch_closing_price(stock_code)
        if price_data:
            if save_closing_price(stock_code, price_data, engine):
                success += 1
                logger.debug(f"{stock_code}: Saved {price_data['close']:,.0f} ({price_data['date']})")
            else:
                failed += 1
        else:
            failed += 1
            logger.debug(f"{stock_code}: Failed to fetch price")

        # Rate limiting: pause after every batch
        if (i + 1) % batch_size == 0 and i + 1 < len(stock_codes):
            logger.debug(f"Processed {i + 1}/{len(stock_codes)}, pausing {delay_between_batches}s...")
            time.sleep(delay_between_batches)

    logger.info(f"Price update complete: {success} success, {failed} failed")
    return {"success": success, "failed": failed, "total": len(stock_codes)}


def update_single_stock_price(stock_code: str) -> bool:
    """
    Update closing price for a single stock.

    Args:
        stock_code: 6-digit stock code

    Returns:
        True if updated successfully
    """
    price_data = fetch_closing_price(stock_code)
    if not price_data:
        return False

    return save_closing_price(stock_code, price_data)


# Scheduler job function
def scheduled_price_update():
    """
    Scheduled job to run after market close.
    Updates all stocks in the database with today's closing prices.
    """
    import pytz
    from datetime import datetime

    kst = pytz.timezone("Asia/Seoul")
    now = datetime.now(kst)

    # Skip weekends
    if now.weekday() >= 5:
        logger.info("Weekend - skipping price update")
        return

    logger.info(f"Running scheduled price update at {now.strftime('%Y-%m-%d %H:%M:%S')} KST")
    result = update_all_closing_prices()
    logger.info(f"Scheduled update result: {result}")


if __name__ == "__main__":
    # CLI for manual updates
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        # Update specific stock
        stock_code = sys.argv[1]
        print(f"Updating {stock_code}...")
        if update_single_stock_price(stock_code):
            print("Success!")
        else:
            print("Failed!")
    else:
        # Update all stocks
        print("Updating all stocks...")
        result = update_all_closing_prices()
        print(f"Result: {result}")
