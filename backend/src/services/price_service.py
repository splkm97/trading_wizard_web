"""Price fetching service using yfinance."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
import yfinance as yf

from src.core.logging import logger


class PriceService:
    """Service for fetching stock prices from Yahoo Finance."""

    # Korean stock suffix for Yahoo Finance
    KRX_SUFFIX = ".KS"

    @staticmethod
    def get_ticker_symbol(stock_code: str) -> str:
        """Convert Korean stock code to Yahoo Finance ticker.

        Args:
            stock_code: 6-digit Korean stock code

        Returns:
            Yahoo Finance ticker symbol (e.g., '005930.KS')
        """
        return f"{stock_code}{PriceService.KRX_SUFFIX}"

    def get_current_price(self, stock_code: str) -> Optional[Decimal]:
        """Get current price for a stock.

        Args:
            stock_code: 6-digit Korean stock code

        Returns:
            Current price or None if not available
        """
        try:
            ticker = yf.Ticker(self.get_ticker_symbol(stock_code))
            info = ticker.info

            # Try different price fields
            price = info.get("regularMarketPrice") or info.get("previousClose")

            if price:
                return Decimal(str(price))

            logger.warning(f"No price found for {stock_code}")
            return None

        except Exception as e:
            logger.error(f"Failed to fetch price for {stock_code}: {e}")
            return None

    def get_prices_batch(self, stock_codes: list[str]) -> dict[str, Optional[Decimal]]:
        """Get current prices for multiple stocks.

        Args:
            stock_codes: List of 6-digit Korean stock codes

        Returns:
            Dict mapping stock code to price (None if not available)
        """
        if not stock_codes:
            return {}

        results = {}

        try:
            # Create ticker symbols
            tickers = " ".join(self.get_ticker_symbol(code) for code in stock_codes)
            data = yf.Tickers(tickers)

            for code in stock_codes:
                symbol = self.get_ticker_symbol(code)
                try:
                    ticker = data.tickers.get(symbol)
                    if ticker:
                        info = ticker.info
                        price = info.get("regularMarketPrice") or info.get("previousClose")
                        results[code] = Decimal(str(price)) if price else None
                    else:
                        results[code] = None
                except Exception as e:
                    logger.warning(f"Failed to get price for {code}: {e}")
                    results[code] = None

        except Exception as e:
            logger.error(f"Batch price fetch failed: {e}")
            # Return None for all codes
            for code in stock_codes:
                results[code] = None

        return results

    def get_historical_prices(
        self,
        stock_code: str,
        period: str = "1y",
    ) -> list[dict]:
        """Get historical prices for a stock.

        Args:
            stock_code: 6-digit Korean stock code
            period: Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)

        Returns:
            List of {date, open, high, low, close, volume} dicts
        """
        try:
            ticker = yf.Ticker(self.get_ticker_symbol(stock_code))
            hist = ticker.history(period=period)

            if hist.empty:
                return []

            return [
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                }
                for date, row in hist.iterrows()
            ]

        except Exception as e:
            logger.error(f"Failed to fetch historical prices for {stock_code}: {e}")
            return []


# Singleton instance
price_service = PriceService()
