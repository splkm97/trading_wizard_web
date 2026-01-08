"""
Stock data caching for faster recommendations.
Pre-downloads KOSPI Top 100 data and caches locally.
"""

from __future__ import annotations

import json
import pickle
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading

import pandas as pd
import yfinance as yf

from src.wizard.signal_scanner import load_kospi_top100, calculate_indicators

# Cache directory
# In Docker: /app/cache (separate from /app/data for PVC isolation)
# Parent chain: wizard -> src -> app (3 levels up)
APP_ROOT = Path(__file__).parent.parent.parent  # /app in container
CACHE_DIR = APP_ROOT / "cache"
CACHE_FILE = CACHE_DIR / "stock_data_cache.pkl"
CACHE_META_FILE = CACHE_DIR / "cache_meta.json"

# Cache lock for thread safety
_cache_lock = threading.Lock()
_memory_cache: Dict[str, pd.DataFrame] = {}
_cache_timestamp: Optional[datetime] = None


def get_cache_dir() -> Path:
    """Ensure cache directory exists and return path."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def fetch_stock_data_batch(stock_codes: List[str], days: int = 60) -> Dict[str, pd.DataFrame]:
    """
    Fetch OHLCV data for multiple stocks in batch.

    Args:
        stock_codes: List of 6-digit Korean stock codes
        days: Number of days of history

    Returns:
        Dict of stock_code -> DataFrame
    """
    results = {}
    end_date = date.today()
    start_date = end_date - timedelta(days=days + 30)

    # Build ticker list (try KS first)
    tickers = [f"{code}.KS" for code in stock_codes]

    try:
        # Download all at once
        data = yf.download(
            tickers,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            progress=True,
            auto_adjust=False,
            group_by='ticker',
            threads=True,
        )

        for code in stock_codes:
            ticker = f"{code}.KS"
            try:
                if isinstance(data.columns, pd.MultiIndex):
                    if ticker in data.columns.get_level_values(0):
                        df = data[ticker].copy()
                    else:
                        continue
                else:
                    df = data.copy()

                if df.empty or len(df) < 30:
                    continue

                # Select only needed columns
                df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()

                if len(df) >= 30:
                    # Calculate indicators
                    df = calculate_indicators(df)
                    results[code] = df

            except Exception as e:
                print(f"  Warning: Failed to process {code}: {e}")
                continue

    except Exception as e:
        print(f"Batch download failed: {e}")
        # Fallback to individual downloads
        for code in stock_codes:
            try:
                ticker = f"{code}.KS"
                df = yf.download(
                    ticker,
                    start=start_date.isoformat(),
                    end=end_date.isoformat(),
                    progress=False,
                    auto_adjust=False,
                )

                if df.empty:
                    ticker = f"{code}.KQ"
                    df = yf.download(
                        ticker,
                        start=start_date.isoformat(),
                        end=end_date.isoformat(),
                        progress=False,
                        auto_adjust=False,
                    )

                if not df.empty and len(df) >= 30:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
                    df = calculate_indicators(df)
                    results[code] = df

            except Exception:
                continue

    return results


def refresh_cache(stock_codes: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
    """
    Refresh the stock data cache.

    Args:
        stock_codes: List of stock codes to cache. If None, uses KOSPI Top 100.

    Returns:
        Dict of cached data
    """
    global _memory_cache, _cache_timestamp

    if stock_codes is None:
        try:
            stock_codes = load_kospi_top100()
        except FileNotFoundError:
            stock_codes = ["005930", "000660", "035420"]  # Fallback

    print(f"Refreshing cache for {len(stock_codes)} stocks...")
    start_time = datetime.now()

    # Fetch all data
    data = fetch_stock_data_batch(stock_codes)

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"Downloaded {len(data)} stocks in {elapsed:.1f}s")

    # Save to disk
    with _cache_lock:
        get_cache_dir()

        # Save pickle
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(data, f)

        # Save metadata
        meta = {
            "timestamp": datetime.now().isoformat(),
            "stock_count": len(data),
            "stocks": list(data.keys()),
        }
        with open(CACHE_META_FILE, 'w') as f:
            json.dump(meta, f, indent=2)

        # Update memory cache
        _memory_cache = data
        _cache_timestamp = datetime.now()

    print(f"Cache saved: {len(data)} stocks")
    return data


def load_cache() -> Dict[str, pd.DataFrame]:
    """
    Load cached data from disk or memory.

    Returns:
        Dict of stock_code -> DataFrame with indicators
    """
    global _memory_cache, _cache_timestamp

    with _cache_lock:
        # Return memory cache if recent (within 5 minutes)
        if _memory_cache and _cache_timestamp:
            age = (datetime.now() - _cache_timestamp).total_seconds()
            if age < 300:  # 5 minutes
                return _memory_cache

        # Try loading from disk
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, 'rb') as f:
                    data = pickle.load(f)
                _memory_cache = data
                _cache_timestamp = datetime.now()
                return data
            except Exception as e:
                print(f"Failed to load cache: {e}")

    return {}


def get_cache_info() -> Optional[dict]:
    """Get cache metadata."""
    if CACHE_META_FILE.exists():
        try:
            with open(CACHE_META_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return None


def is_cache_valid(max_age_hours: int = 24) -> bool:
    """
    Check if cache is valid (exists and not too old).

    Args:
        max_age_hours: Maximum age in hours

    Returns:
        True if cache is valid
    """
    info = get_cache_info()
    if not info:
        return False

    try:
        timestamp = datetime.fromisoformat(info["timestamp"])
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        return age_hours < max_age_hours
    except Exception:
        return False


def get_cached_data(stock_code: str) -> Optional[pd.DataFrame]:
    """
    Get cached data for a single stock.

    Args:
        stock_code: 6-digit stock code

    Returns:
        DataFrame with indicators or None
    """
    cache = load_cache()
    return cache.get(stock_code)


# CLI for manual cache refresh
if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Stock Data Cache Manager")
    print("=" * 60)

    # Check current cache status
    info = get_cache_info()
    if info:
        print(f"\nCurrent cache:")
        print(f"  Timestamp: {info['timestamp']}")
        print(f"  Stocks: {info['stock_count']}")
        print(f"  Valid: {is_cache_valid()}")
    else:
        print("\nNo cache found.")

    if len(sys.argv) > 1 and sys.argv[1] == "--refresh":
        print("\nRefreshing cache...")
        refresh_cache()
        print("\nDone!")
    else:
        print("\nRun with --refresh to update cache")
