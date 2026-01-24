"""
Async price fetching service using concurrent execution.

This module provides parallel stock data fetching using ThreadPoolExecutor
to overcome yfinance's synchronous API limitations while respecting rate limits.
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_MAX_WORKERS = 10
DEFAULT_CHUNK_SIZE = 10
DEFAULT_RETRY_ATTEMPTS = 2


class AsyncPriceService:
    """
    Async wrapper for yfinance with parallel execution support.

    This service uses a ThreadPoolExecutor to fetch stock data in parallel,
    significantly reducing total fetch time for batch operations.
    """

    def __init__(
        self,
        max_workers: int = DEFAULT_MAX_WORKERS,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ):
        """
        Initialize the async price service.

        Args:
            max_workers: Maximum concurrent fetch threads
            chunk_size: Number of stocks per batch (to avoid rate limiting)
        """
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def _convert_to_yahoo_ticker(self, stock_code: str) -> str:
        """Convert Korean stock code to Yahoo Finance ticker format."""
        return f"{stock_code}.KS"

    def _fetch_single_price(self, stock_code: str) -> tuple[str, Decimal | None]:
        """
        Fetch current price for a single stock.

        Args:
            stock_code: 6-digit Korean stock code

        Returns:
            Tuple of (stock_code, price or None)
        """
        ticker_str = self._convert_to_yahoo_ticker(stock_code)

        try:
            ticker = yf.Ticker(ticker_str)
            info = ticker.info

            price = info.get("regularMarketPrice")
            if price is None:
                price = info.get("previousClose")

            if price is not None:
                return stock_code, Decimal(str(price))

            # Try KOSDAQ suffix as fallback
            ticker_str = f"{stock_code}.KQ"
            ticker = yf.Ticker(ticker_str)
            info = ticker.info

            price = info.get("regularMarketPrice") or info.get("previousClose")
            if price is not None:
                return stock_code, Decimal(str(price))

        except Exception as e:
            logger.debug(f"Failed to fetch price for {stock_code}: {e}")

        return stock_code, None

    def _fetch_historical_single(
        self, stock_code: str, days: int = 60
    ) -> tuple[str, pd.DataFrame | None]:
        """
        Fetch historical OHLCV data for a single stock.

        Args:
            stock_code: 6-digit Korean stock code
            days: Number of days of history

        Returns:
            Tuple of (stock_code, DataFrame or None)
        """
        end_date = date.today() + timedelta(days=1)
        start_date = end_date - timedelta(days=days + 30)

        ticker_str = self._convert_to_yahoo_ticker(stock_code)

        try:
            df = yf.download(
                ticker_str,
                start=start_date.isoformat(),
                end=end_date.isoformat(),
                progress=False,
                auto_adjust=False,
            )

            # Try KOSDAQ suffix if empty
            if df.empty:
                ticker_str = f"{stock_code}.KQ"
                df = yf.download(
                    ticker_str,
                    start=start_date.isoformat(),
                    end=end_date.isoformat(),
                    progress=False,
                    auto_adjust=False,
                )

            if df.empty or len(df) < 30:
                return stock_code, None

            # Handle MultiIndex columns from yfinance
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            return stock_code, df[["Open", "High", "Low", "Close", "Volume"]].dropna()

        except Exception as e:
            logger.debug(f"Failed to fetch historical data for {stock_code}: {e}")
            return stock_code, None

    async def get_prices_batch_async(
        self, stock_codes: list[str]
    ) -> dict[str, Decimal | None]:
        """
        Fetch current prices for multiple stocks in parallel.

        Args:
            stock_codes: List of 6-digit Korean stock codes

        Returns:
            Dictionary mapping stock codes to prices (or None if failed)
        """
        if not stock_codes:
            return {}

        loop = asyncio.get_event_loop()
        results = {}

        # Process in chunks to avoid rate limiting
        for i in range(0, len(stock_codes), self.chunk_size):
            chunk = stock_codes[i : i + self.chunk_size]

            # Submit all tasks in the chunk
            futures = [
                loop.run_in_executor(self._executor, self._fetch_single_price, code)
                for code in chunk
            ]

            # Wait for all tasks to complete
            chunk_results = await asyncio.gather(*futures)

            for code, price in chunk_results:
                results[code] = price

            # Small delay between chunks to be respectful of rate limits
            if i + self.chunk_size < len(stock_codes):
                await asyncio.sleep(0.5)

        return results

    async def get_historical_batch_async(
        self, stock_codes: list[str], days: int = 60
    ) -> dict[str, pd.DataFrame | None]:
        """
        Fetch historical data for multiple stocks in parallel.

        Args:
            stock_codes: List of 6-digit Korean stock codes
            days: Number of days of history

        Returns:
            Dictionary mapping stock codes to DataFrames (or None if failed)
        """
        if not stock_codes:
            return {}

        loop = asyncio.get_event_loop()
        results = {}

        # Process in chunks to avoid rate limiting
        for i in range(0, len(stock_codes), self.chunk_size):
            chunk = stock_codes[i : i + self.chunk_size]

            # Submit all tasks in the chunk
            futures = [
                loop.run_in_executor(
                    self._executor, self._fetch_historical_single, code, days
                )
                for code in chunk
            ]

            # Wait for all tasks to complete
            chunk_results = await asyncio.gather(*futures)

            for code, df in chunk_results:
                results[code] = df

            # Small delay between chunks
            if i + self.chunk_size < len(stock_codes):
                await asyncio.sleep(0.5)

        return results

    def get_prices_batch_sync(
        self, stock_codes: list[str]
    ) -> dict[str, Decimal | None]:
        """
        Synchronous version of batch price fetching using ThreadPoolExecutor.

        This method is useful when called from non-async context.

        Args:
            stock_codes: List of 6-digit Korean stock codes

        Returns:
            Dictionary mapping stock codes to prices (or None if failed)
        """
        if not stock_codes:
            return {}

        results = {}

        # Process in chunks
        for i in range(0, len(stock_codes), self.chunk_size):
            chunk = stock_codes[i : i + self.chunk_size]

            # Submit all tasks in the chunk
            future_to_code = {
                self._executor.submit(self._fetch_single_price, code): code
                for code in chunk
            }

            # Collect results
            for future in as_completed(future_to_code):
                try:
                    code, price = future.result()
                    results[code] = price
                except Exception as e:
                    code = future_to_code[future]
                    logger.error(f"Error fetching price for {code}: {e}")
                    results[code] = None

        return results

    def get_historical_batch_sync(
        self, stock_codes: list[str], days: int = 60
    ) -> dict[str, pd.DataFrame | None]:
        """
        Synchronous version of batch historical data fetching.

        Args:
            stock_codes: List of 6-digit Korean stock codes
            days: Number of days of history

        Returns:
            Dictionary mapping stock codes to DataFrames (or None if failed)
        """
        if not stock_codes:
            return {}

        results = {}

        # Process in chunks
        for i in range(0, len(stock_codes), self.chunk_size):
            chunk = stock_codes[i : i + self.chunk_size]

            # Submit all tasks in the chunk
            future_to_code = {
                self._executor.submit(self._fetch_historical_single, code, days): code
                for code in chunk
            }

            # Collect results
            for future in as_completed(future_to_code):
                try:
                    code, df = future.result()
                    results[code] = df
                except Exception as e:
                    code = future_to_code[future]
                    logger.error(f"Error fetching historical data for {code}: {e}")
                    results[code] = None

        return results

    def shutdown(self):
        """Shutdown the executor gracefully."""
        self._executor.shutdown(wait=True)


# Module-level singleton
_async_price_service: AsyncPriceService | None = None


def get_async_price_service() -> AsyncPriceService:
    """Get or create the async price service singleton."""
    global _async_price_service
    if _async_price_service is None:
        _async_price_service = AsyncPriceService()
    return _async_price_service


# Convenience alias
async_price_service = get_async_price_service
