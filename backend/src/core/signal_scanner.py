"""
Stock universe scanner for trading signals.
Fetches data from yfinance and calculates technical indicators.
Adapted from trading_wizard_bundle for web application use.
"""

import warnings
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

from src.core.indicators import calculate_all_indicators, calculate_confidence_score

warnings.filterwarnings("ignore")


@dataclass
class StockSignal:
    """Signal information for a stock."""

    stock_code: str
    stock_name: str
    signal_type: str
    confidence_score: float
    current_price: float
    reason: str
    indicators: dict[str, float]


@dataclass
class PositionInfo:
    """Position information for sell signal scanning."""

    stock_code: str
    stock_name: str
    quantity: int
    entry_price: float


def fetch_stock_data(stock_code: str, days: int = 60) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data from Yahoo Finance.

    Args:
        stock_code: 6-digit Korean stock code
        days: Number of days of history to fetch

    Returns:
        DataFrame with OHLCV data or None if fetch failed
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days + 30)  # Extra days for indicator warmup

    ticker = f"{stock_code}.KS"
    try:
        df = yf.download(
            ticker,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            progress=False,
            auto_adjust=False,
        )

        if df.empty:
            # Try KOSDAQ
            ticker = f"{stock_code}.KQ"
            df = yf.download(
                ticker,
                start=start_date.isoformat(),
                end=end_date.isoformat(),
                progress=False,
                auto_adjust=False,
            )

        if df.empty or len(df) < 30:
            return None

        # Handle MultiIndex columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df[["Open", "High", "Low", "Close", "Volume"]].dropna()

    except Exception:
        return None


def fetch_stock_data_for_date(
    stock_code: str,
    target_date: date,
    days: int = 60,
) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data up to a specific date (for backtesting).

    Args:
        stock_code: 6-digit Korean stock code
        target_date: Target date to fetch data up to
        days: Number of days of history to fetch

    Returns:
        DataFrame with OHLCV data or None if fetch failed
    """
    end_date = target_date + timedelta(days=1)
    start_date = target_date - timedelta(days=days + 30)

    ticker = f"{stock_code}.KS"
    try:
        df = yf.download(
            ticker,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            progress=False,
            auto_adjust=False,
        )

        if df.empty:
            ticker = f"{stock_code}.KQ"
            df = yf.download(
                ticker,
                start=start_date.isoformat(),
                end=end_date.isoformat(),
                progress=False,
                auto_adjust=False,
            )

        if df.empty or len(df) < 30:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Filter to only include data up to target date
        df = df[df.index.date <= target_date]

        return df[["Open", "High", "Low", "Close", "Volume"]].dropna()

    except Exception:
        return None


class SignalScanner:
    """Scans stock universe for trading signals."""

    def __init__(
        self,
        confidence_threshold: int = 55,
        stop_loss_percent: float = 4.5,
        sell_on_middle_band: bool = False,
        take_profit_pct: float = 12.0,
    ):
        self.confidence_threshold = confidence_threshold
        self.stop_loss_percent = stop_loss_percent
        self.sell_on_middle_band = sell_on_middle_band
        self.take_profit_pct = take_profit_pct

    def scan_for_buy_signals(
        self,
        stock_codes: list[str],
        existing_positions: list[str],
        stock_names: dict[str, str],
        progress_callback=None,
    ) -> list[StockSignal]:
        """
        Scan for BUY signals on stocks without positions.

        Args:
            stock_codes: List of stock codes to scan
            existing_positions: List of stock codes already in portfolio
            stock_names: Dict mapping stock_code -> stock_name
            progress_callback: Optional callback(current, total, stock_code)

        Returns:
            List of StockSignal objects for BUY recommendations
        """
        signals = []

        # Filter out stocks we already own
        candidates = [s for s in stock_codes if s not in existing_positions]
        total = len(candidates)

        for i, stock_code in enumerate(candidates):
            if progress_callback:
                progress_callback(i + 1, total, stock_code)

            df = fetch_stock_data(stock_code)
            if df is None or len(df) < 35:
                continue

            signal = self._check_buy_signal(df, stock_code, stock_names.get(stock_code, stock_code))
            if signal:
                signals.append(signal)

        # Sort by confidence score descending
        signals.sort(key=lambda x: x.confidence_score, reverse=True)
        return signals

    def _check_buy_signal(
        self,
        df: pd.DataFrame,
        stock_code: str,
        stock_name: str,
    ) -> Optional[StockSignal]:
        """Check if a stock has a buy signal."""
        df = calculate_all_indicators(df)
        latest = df.iloc[-1]

        # Skip if indicators are NaN
        if pd.isna(latest["BB_Upper"]) or pd.isna(latest["RSI"]):
            return None

        # Check BUY conditions
        price_breakout = latest["Close"] > latest["BB_Upper"]
        was_in_squeeze = df["In_Squeeze"].iloc[-5:-1].any()
        bandwidth_expanding = latest["BB_Width"] > df["BB_Width"].iloc[-2]

        if price_breakout and (was_in_squeeze or bandwidth_expanding):
            # Calculate continuous confidence score
            confidence = calculate_confidence_score(
                volume_ratio=float(latest["Volume_Ratio"]),
                rsi=float(latest["RSI"]),
                macd_histogram=float(latest["MACD_Histogram"]),
                macd_signal=float(latest["MACD_Signal"]),
            )

            if confidence >= self.confidence_threshold:
                return StockSignal(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    signal_type="BUY",
                    confidence_score=confidence,
                    current_price=float(latest["Close"]),
                    reason="squeeze_breakout_buy",
                    indicators={
                        "rsi": float(latest["RSI"]),
                        "macd_histogram": float(latest["MACD_Histogram"]),
                        "volume_ratio": float(latest["Volume_Ratio"]),
                        "bb_width": float(latest["BB_Width"]),
                        "bb_upper": float(latest["BB_Upper"]),
                        "bb_middle": float(latest["BB_Middle"]),
                        "bb_lower": float(latest["BB_Lower"]),
                    },
                )
        return None

    def scan_for_sell_signals(
        self, positions: list[PositionInfo], progress_callback=None
    ) -> list[StockSignal]:
        """
        Scan for SELL signals on existing positions.

        Args:
            positions: List of position info
            progress_callback: Optional callback(current, total, stock_code)

        Returns:
            List of StockSignal objects for SELL recommendations
        """
        signals = []
        total = len(positions)

        for i, pos in enumerate(positions):
            if progress_callback:
                progress_callback(i + 1, total, pos.stock_code)

            df = fetch_stock_data(pos.stock_code)
            if df is None:
                continue

            signal = self._check_sell_signal(df, pos)
            if signal:
                signals.append(signal)

        return signals

    def _check_sell_signal(
        self,
        df: pd.DataFrame,
        pos: PositionInfo,
    ) -> Optional[StockSignal]:
        df = calculate_all_indicators(df)
        latest = df.iloc[-1]
        current_price = float(latest["Close"])
        pnl_pct = ((current_price - pos.entry_price) / pos.entry_price) * 100

        sell_reason = None
        sell_quantity = pos.quantity
        sell_ratio = 1.0

        if pnl_pct <= -self.stop_loss_percent:
            sell_reason = f"stop_loss ({pnl_pct:.1f}%)"

        elif pnl_pct >= self.take_profit_pct:
            sell_reason = f"take_profit ({pnl_pct:+.1f}%)"

        elif self.sell_on_middle_band and current_price < latest["BB_Middle"]:
            sell_reason = f"middle_band_cross ({pnl_pct:+.1f}%)"

        if sell_reason:
            return StockSignal(
                stock_code=pos.stock_code,
                stock_name=pos.stock_name,
                signal_type="SELL",
                confidence_score=100,
                current_price=current_price,
                reason=sell_reason,
                indicators={
                    "entry_price": pos.entry_price,
                    "pnl_pct": pnl_pct,
                    "sell_quantity": sell_quantity,
                    "sell_ratio": sell_ratio,
                    "rsi": float(latest["RSI"]),
                    "bb_lower": float(latest["BB_Lower"]),
                    "bb_middle": float(latest["BB_Middle"]),
                },
            )
        return None

    def get_current_prices(self, stock_codes: list[str]) -> dict[str, float]:
        """
        Get current prices for a list of stocks.

        Args:
            stock_codes: List of stock codes

        Returns:
            Dict of stock_code -> current_price
        """
        prices = {}
        for stock_code in stock_codes:
            df = fetch_stock_data(stock_code, days=5)
            if df is not None and len(df) > 0:
                prices[stock_code] = float(df.iloc[-1]["Close"])
        return prices
