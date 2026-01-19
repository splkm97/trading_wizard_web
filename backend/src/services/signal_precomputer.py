"""
Background worker to pre-compute trading signals.

This module runs as an APScheduler job to pre-compute signals every 30 seconds
during Korean market hours (9:00-15:30 KST). Results are cached in Redis for
sub-100ms API response times.
"""

from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd
import pytz

from src.core.cache import get_cache_service
from src.core.config import settings
from src.core.indicators import calculate_all_indicators
from src.wizard.signal_scanner import (
    SignalScanner,
    fetch_stock_data,
    load_kospi_top100,
)

logger = logging.getLogger(__name__)

# Korean timezone
KST = pytz.timezone("Asia/Seoul")


def is_market_hours() -> bool:
    """
    Check if Korean stock market is currently open.

    Market hours: 9:00 - 15:30 KST, weekdays only.
    """
    now = datetime.now(KST)

    # Skip weekends (0=Monday, 6=Sunday)
    if now.weekday() >= 5:
        return False

    # Market hours: 9:00 - 15:30
    market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

    return market_open <= now <= market_close


def precompute_bollinger_signals(
    scanner: SignalScanner,
    stock_codes: list[str],
    max_results: int = 50,
    force_fetch: bool = False,
) -> list[dict]:
    """
    Pre-compute Bollinger Band squeeze breakout signals.

    Args:
        scanner: SignalScanner instance
        stock_codes: List of stock codes to scan
        max_results: Maximum number of signals to return
        force_fetch: If True, always fetch fresh data from yfinance

    Returns:
        List of signal dictionaries
    """
    try:
        signals = scanner.scan_for_buy_signals(
            stock_codes=stock_codes,
            existing_positions=[],
            max_results=max_results,
            force_fetch=force_fetch,
        )
        return [s.to_dict() for s in signals]
    except Exception as e:
        logger.error(f"Failed to compute Bollinger signals: {e}")
        return []


def precompute_contrarian_signals(
    scanner: SignalScanner,
    stock_codes: list[str],
    max_results: int = 50,
) -> list[dict]:
    """
    Pre-compute MACD/RSI contrarian signals.

    Args:
        scanner: SignalScanner instance
        stock_codes: List of stock codes to scan
        max_results: Maximum number of signals to return

    Returns:
        List of signal dictionaries
    """
    try:
        signals = scanner.scan_for_contrarian_signals(
            stock_codes=stock_codes,
            max_results=max_results,
        )
        return [s.to_dict() for s in signals]
    except Exception as e:
        logger.error(f"Failed to compute contrarian signals: {e}")
        return []


def precompute_contrarian_candidates(
    scanner: SignalScanner,
    stock_codes: list[str],
    max_results: int = 30,
) -> list[dict]:
    """
    Pre-compute contrarian pre-signal candidates.

    Args:
        scanner: SignalScanner instance
        stock_codes: List of stock codes to scan
        max_results: Maximum number of candidates to return

    Returns:
        List of candidate dictionaries
    """
    try:
        candidates = scanner.scan_for_contrarian_candidates(
            stock_codes=stock_codes,
            max_results=max_results,
        )
        return [c.to_dict() for c in candidates]
    except Exception as e:
        logger.error(f"Failed to compute contrarian candidates: {e}")
        return []


def update_watchlist_insights(db, watchlist_service):
    """Update price and indicator data for all watchlist entries.

    This function is called periodically to refresh watchlist data.

    Args:
        db: Database session
        watchlist_service: WatchlistService instance
    """
    from src.models.watchlist import Watchlist

    try:
        watchlists = db.query(Watchlist).all()

        if not watchlists:
            logger.debug("No watchlist entries found")
            return

        scanner = SignalScanner()
        updated_count = 0

        for watchlist_item in watchlists:
            try:
                df = fetch_stock_data(watchlist_item.stock_code, days=60)

                if df is None or len(df) == 0:
                    logger.debug(f"No data found for {watchlist_item.stock_code}")
                    continue

                df_with_indicators = calculate_all_indicators(df)
                latest = df_with_indicators.iloc[-1]

                price_data = {"close": float(latest["Close"]), "volume": int(latest["Volume"])}

                indicators_data = {
                    "rsi": float(latest["RSI"]) if not pd.isna(latest["RSI"]) else None,
                    "macd": float(latest["MACD"]) if not pd.isna(latest["MACD"]) else None,
                    "macd_histogram": float(latest["MACD_Histogram"])
                    if not pd.isna(latest["MACD_Histogram"])
                    else None,
                    "bb_upper": float(latest["BB_Upper"])
                    if not pd.isna(latest["BB_Upper"])
                    else None,
                    "bb_middle": float(latest["BB_Middle"])
                    if not pd.isna(latest["BB_Middle"])
                    else None,
                    "bb_lower": float(latest["BB_Lower"])
                    if not pd.isna(latest["BB_Lower"])
                    else None,
                }

                signal = scanner.scan_single_stock(watchlist_item.stock_code)

                score = signal.confidence_score if signal and signal.signal_type == "BUY" else None
                reason = signal.reason if signal and signal.signal_type == "BUY" else None

                watchlist_service.update_insights(
                    watchlist_item.id, price_data, indicators_data, score, reason
                )

                updated_count += 1

            except Exception as e:
                logger.warning(f"Failed to update insights for {watchlist_item.stock_code}: {e}")
                continue

        logger.info(f"Updated insights for {updated_count}/{len(watchlists)} watchlist entries")

    except Exception as e:
        logger.error(f"Watchlist insights update failed: {e}")


def precompute_all_signals(force_fetch: bool = False, db=None) -> dict:
    """
    Pre-compute all trading signals and cache results.

    This function:
    1. Checks if market is open (skips during off-hours to save resources)
    2. Loads KOSPI Top 100 stocks
    3. Computes Bollinger and Contrarian signals
    4. Updates watchlist insights with price and indicator data
    5. Caches results in Redis with configured TTL

    Args:
        force_fetch: If True, always fetch fresh data from yfinance
        db: Database session for watchlist insights update

    Returns:
        Dictionary with computation statistics
    """
    start_time = datetime.now()
    stats = {
        "market_open": False,
        "bollinger_count": 0,
        "contrarian_count": 0,
        "candidates_count": 0,
        "watchlist_updated": False,
        "duration_ms": 0,
        "cached": False,
    }

    # Check market hours (allow force computation outside market hours)
    if not force_fetch and not is_market_hours():
        logger.debug("Market is closed, skipping signal pre-computation")
        return stats

    stats["market_open"] = True

    try:
        # Load stock universe
        stock_codes = load_kospi_top100()
        logger.info(f"Pre-computing signals for {len(stock_codes)} stocks")

        # Create scanner with default settings
        scanner = SignalScanner()

        # Compute all signal types
        bollinger_signals = precompute_bollinger_signals(
            scanner, stock_codes, force_fetch=force_fetch
        )
        contrarian_signals = precompute_contrarian_signals(scanner, stock_codes)
        contrarian_candidates = precompute_contrarian_candidates(scanner, stock_codes)

        stats["bollinger_count"] = len(bollinger_signals)
        stats["contrarian_count"] = len(contrarian_signals)
        stats["candidates_count"] = len(contrarian_candidates)

        # Cache results
        cache = get_cache_service()
        cache_ttl = settings.SIGNAL_CACHE_TTL_SECONDS

        # Store signals with metadata
        cache_data = {
            "bollinger": {
                "signals": bollinger_signals,
                "computed_at": datetime.now().isoformat(),
                "count": len(bollinger_signals),
            },
            "contrarian": {
                "signals": contrarian_signals,
                "computed_at": datetime.now().isoformat(),
                "count": len(contrarian_signals),
            },
            "candidates": {
                "signals": contrarian_candidates,
                "computed_at": datetime.now().isoformat(),
                "count": len(contrarian_candidates),
            },
        }

        # Cache each signal type separately for flexible retrieval
        cache.set(cache.signals_key("bollinger"), cache_data["bollinger"], cache_ttl)
        cache.set(cache.signals_key("contrarian"), cache_data["contrarian"], cache_ttl)
        cache.set(cache.signals_key("candidates"), cache_data["candidates"], cache_ttl)

        # Also cache a combined version for quick overview
        cache.set("signals:all:latest", cache_data, cache_ttl)

        stats["cached"] = True

        if db:
            from src.services.watchlist_service import WatchlistService

            watchlist_service = WatchlistService(db)
            update_watchlist_insights(db, watchlist_service)
            stats["watchlist_updated"] = True

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        stats["duration_ms"] = round(duration_ms, 2)

        logger.info(
            f"Signal pre-computation complete: "
            f"Bollinger={stats['bollinger_count']}, "
            f"Contrarian={stats['contrarian_count']}, "
            f"Candidates={stats['candidates_count']}, "
            f"WatchlistUpdated={stats['watchlist_updated']}, "
            f"Duration={stats['duration_ms']}ms"
        )

    except Exception as e:
        logger.error(f"Signal pre-computation failed: {e}")
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        stats["duration_ms"] = round(duration_ms, 2)

    return stats


def get_cached_signals(strategy: str = "bollinger") -> dict | None:
    """
    Retrieve cached signals for a strategy.

    Args:
        strategy: Signal strategy ("bollinger", "contrarian", "candidates")

    Returns:
        Cached signal data or None if not available
    """
    cache = get_cache_service()
    return cache.get(cache.signals_key(strategy))


def is_cache_stale(cached_data: dict | None) -> bool:
    """
    Check if cached data is stale based on computed_at timestamp.

    Uses SIGNAL_STALE_THRESHOLD_SECONDS from settings (default: 60 seconds).
    Cache is still valid but considered "stale" and should trigger background refresh.

    Args:
        cached_data: Cached signal data with computed_at field

    Returns:
        True if cache is stale, False if fresh
    """
    if not cached_data or "computed_at" not in cached_data:
        return True

    try:
        computed_at = datetime.fromisoformat(cached_data["computed_at"])
        age_seconds = (datetime.now() - computed_at).total_seconds()
        return age_seconds > settings.SIGNAL_STALE_THRESHOLD_SECONDS
    except (ValueError, TypeError):
        return True


def get_cached_signals_with_staleness(strategy: str = "bollinger") -> tuple[dict | None, bool]:
    """
    Retrieve cached signals with staleness indicator.

    Implements stale-while-revalidate pattern:
    - Returns cached data even if stale (for fast response)
    - Returns staleness flag so caller can trigger background refresh

    Args:
        strategy: Signal strategy ("bollinger", "contrarian", "candidates")

    Returns:
        Tuple of (cached_data, is_stale)
    """
    cached_data = get_cached_signals(strategy)
    is_stale = is_cache_stale(cached_data)
    return cached_data, is_stale


def get_all_cached_signals() -> dict | None:
    """
    Retrieve all cached signals.

    Returns:
        Combined cached signal data or None if not available
    """
    cache = get_cache_service()
    return cache.get("signals:all:latest")


def invalidate_signal_cache() -> None:
    """Clear all cached signals."""
    cache = get_cache_service()
    cache.delete(cache.signals_key("bollinger"))
    cache.delete(cache.signals_key("contrarian"))
    cache.delete(cache.signals_key("candidates"))
    cache.delete("signals:all:latest")
    logger.info("Signal cache invalidated")
