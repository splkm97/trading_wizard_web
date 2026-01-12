"""
Stock universe scanner for daily trading signals.
Fetches data from yfinance and calculates technical indicators.

Optimized for PostgreSQL-first data access strategy:
1. Memory cache (5min TTL)
2. PostgreSQL DB (permanent storage)
3. yfinance API (fallback)
"""

from __future__ import annotations

import json
import logging
import math
import warnings
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, text

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


@dataclass
class StockSignal:
    """Signal information for a stock."""

    stock_code: str
    stock_name: str
    signal_type: str  # "BUY", "SELL", "HOLD"
    confidence_score: float  # Changed from int to float for precision (3 decimal places)
    current_price: float
    reason: str
    indicators: Dict[str, float]

    def to_dict(self) -> dict:
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "signal_type": self.signal_type,
            "confidence_score": self.confidence_score,
            "current_price": self.current_price,
            "reason": self.reason,
            "indicators": self.indicators,
        }


def get_stock_name(stock_code: str) -> str:
    """Get Korean stock name from local mapping file."""
    possible_paths = [
        Path("data/stock_names_kr.json"),
        Path(__file__).parent.parent.parent.parent.parent / "data" / "stock_names_kr.json",
        Path(__file__).parent.parent.parent.parent.parent.parent / "data" / "stock_names_kr.json",
    ]

    for path in possible_paths:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    names = json.load(f)
                if stock_code in names:
                    return names[stock_code]
            except Exception:
                pass

    # Fallback to yfinance
    try:
        ticker = yf.Ticker(f"{stock_code}.KS")
        info = ticker.info
        name = info.get("shortName") or info.get("longName")
        if name:
            return name
    except Exception:
        pass
    return stock_code


def load_kospi_top100(filepath: str = "kospi_top100.txt") -> List[str]:
    """Load KOSPI Top 100 stock codes from file."""
    # In Docker container: /app/src/wizard/signal_scanner.py -> /app/data/
    # Parent chain: wizard -> src -> app (3 levels up)
    app_root = Path(__file__).parent.parent.parent  # /app in container

    possible_paths = [
        app_root / "data" / filepath,  # /app/data/kospi_top100.txt (Docker)
        Path("data") / filepath,  # Relative to cwd
        Path(filepath),  # Current directory
        Path(__file__).parent.parent.parent.parent.parent / filepath,  # Legacy
        Path(__file__).parent.parent.parent.parent.parent / "data" / filepath,
    ]

    for path in possible_paths:
        if path.exists():
            with open(path, "r") as f:
                stocks = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            return [s for s in stocks if s][:100]

    raise FileNotFoundError(
        f"Could not find {filepath} in any expected location. Tried: {[str(p) for p in possible_paths]}"
    )


def fetch_stock_data_from_db(
    stock_code: str, days: int = 60, engine=None
) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data from PostgreSQL database (fast).

    Args:
        stock_code: 6-digit stock code
        days: Number of days of history
        engine: SQLAlchemy engine (creates one if not provided)

    Returns:
        DataFrame with OHLCV data or None
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days + 30)

    query = text(
        """
        SELECT date, open, high, low, close, volume
        FROM historical_prices
        WHERE stock_code = :code
          AND date >= :start_date
          AND date <= :end_date
        ORDER BY date ASC
    """
    )

    try:
        # Create engine if not provided
        if engine is None:
            try:
                from src.core.config import settings

                engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
            except Exception:
                return None

        with engine.connect() as conn:
            df = pd.read_sql_query(
                query,
                conn,
                params={
                    "code": stock_code,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                index_col="date",
            )

        if df.empty or len(df) < 30:
            return None

        # Rename columns to match expected format
        df.columns = ["Open", "High", "Low", "Close", "Volume"]
        return df

    except Exception as e:
        logger.debug(f"DB fetch failed for {stock_code}: {e}")
        return None


def fetch_stock_data(stock_code: str, days: int = 60) -> Optional[pd.DataFrame]:
    """Fetch OHLCV data from Yahoo Finance (fallback)."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days + 30)

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

        return df[["Open", "High", "Low", "Close", "Volume"]].dropna()

    except Exception:
        return None


def calculate_indicators(
    df: pd.DataFrame,
    bollinger_period: int = 20,
    bollinger_std_dev: float = 2.0,
    squeeze_threshold_pct: int = 70,
    squeeze_lookback_days: int = 10,
) -> pd.DataFrame:
    """Calculate all technical indicators needed for signal generation.

    Args:
        df: DataFrame with OHLCV data
        bollinger_period: Bollinger Bands moving average window
        bollinger_std_dev: Number of standard deviations
        squeeze_threshold_pct: Squeeze threshold as % of MA
        squeeze_lookback_days: Days to look back for squeeze MA
    """
    close = df["Close"].copy()
    volume = df["Volume"].copy()

    # Bollinger Bands with configurable parameters
    sma = close.rolling(window=bollinger_period).mean()
    std = close.rolling(window=bollinger_period).std()
    df["BB_Upper"] = sma + (std * bollinger_std_dev)
    df["BB_Middle"] = sma
    df["BB_Lower"] = sma - (std * bollinger_std_dev)
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / sma * 100
    df["BB_Width_MA"] = df["BB_Width"].rolling(window=squeeze_lookback_days).mean()

    # RSI (14-day)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD (12, 26, 9)
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9).mean()
    df["MACD_Histogram"] = df["MACD"] - df["MACD_Signal"]

    # Volume (20-day average)
    df["Volume_MA"] = volume.rolling(window=20).mean()
    df["Volume_Ratio"] = volume / df["Volume_MA"]

    # Squeeze detection with configurable threshold
    squeeze_ratio = squeeze_threshold_pct / 100.0
    df["In_Squeeze"] = df["BB_Width"] < (df["BB_Width_MA"] * squeeze_ratio)

    return df


def calculate_confidence_score(
    volume_ratio: float, rsi: float, macd_histogram: float, macd_signal: float
) -> float:
    """
    Calculate signal confidence score (0-100 points) with continuous scoring.

    Scoring:
        - Base (Bollinger breakout): 25 points
        - Volume (0-25): Linear scale from 1.0x to 2.0x
        - RSI (0-20): Peak at 50, decreases toward 30/70
        - MACD (0-30): Based on histogram strength relative to signal
    """
    score = 25.0  # Base score for Bollinger breakout

    # Volume Score (0-25점)
    if volume_ratio > 1.0:
        vol_score = min(25.0, (volume_ratio - 1.0) * 25.0)
        score += vol_score

    # RSI Score (0-20점)
    if 30 <= rsi <= 70:
        distance = abs(rsi - 50)
        rsi_score = 20.0 * (1 - distance / 20.0)
        score += rsi_score

    # MACD Score (0-30점)
    if macd_histogram > 0:
        macd_signal_abs = abs(macd_signal) if macd_signal != 0 else 0.001
        macd_ratio = min(macd_histogram / macd_signal_abs, 1.0)
        macd_score = 30.0 * macd_ratio
        score += macd_score

    return score


def calculate_contrarian_confidence(rsi: float, macd_histogram: float, macd_signal: float) -> float:
    """
    Calculate contrarian signal confidence score (0-100 points).

    Scoring (per research.md):
        - RSI ≤ 20: Base 80 points (deeply oversold)
        - RSI 20-25: Base 60 points (oversold)
        - RSI 25-30: Base 40 points (mildly oversold)
        - MACD histogram bonus: 0-20 points based on histogram strength relative to signal
    """
    # Base score from RSI tier
    if rsi <= 20:
        base = 80.0
    elif rsi <= 25:
        base = 60.0
    else:  # 25 < rsi <= 30
        base = 40.0

    # MACD histogram bonus (0-20 points)
    if macd_histogram > 0 and macd_signal != 0:
        # Normalize histogram relative to signal strength
        ratio = min(abs(macd_histogram) / abs(macd_signal), 1.0)
        bonus = 20.0 * ratio
    else:
        bonus = 0.0

    return min(100.0, base + bonus)


def format_contrarian_reason_detail(
    rsi: float,
    macd: float,  # noqa: ARG001 - Reserved for future use
    macd_signal: float,
    macd_histogram: float,
) -> str:
    """
    Generate detailed Korean explanation of contrarian signal.

    Args:
        rsi: RSI value
        macd: MACD line value
        macd_signal: MACD signal line value
        macd_histogram: MACD histogram value

    Returns:
        Detailed reason text in Korean
    """
    # Determine RSI oversold level
    if rsi <= 20:
        rsi_desc = f"RSI {rsi:.1f}로 심각한 과매도 상태입니다"
    elif rsi <= 25:
        rsi_desc = f"RSI {rsi:.1f}로 강한 과매도 상태입니다"
    else:
        rsi_desc = f"RSI {rsi:.1f}로 과매도 상태입니다"

    # MACD description
    macd_strength = "강한" if macd_histogram > abs(macd_signal * 0.5) else ""
    macd_desc = f"MACD가 시그널선을 {macd_strength}상향 돌파했습니다"

    # Combine
    return f"{rsi_desc}. {macd_desc}. 기술적 반등 가능성이 높습니다."


def detect_macd_golden_cross(df: pd.DataFrame) -> bool:
    """
    Detect if MACD golden cross occurred on most recent trading day.

    Golden Cross Definition:
        - Previous day: MACD line < Signal line
        - Current day: MACD line >= Signal line

    Args:
        df: DataFrame with MACD and MACD_Signal columns

    Returns:
        True if golden cross occurred on most recent day
    """
    if len(df) < 2:
        return False

    current = df.iloc[-1]
    previous = df.iloc[-2]

    # Check for NaN values
    if pd.isna(current["MACD"]) or pd.isna(current["MACD_Signal"]):
        return False
    if pd.isna(previous["MACD"]) or pd.isna(previous["MACD_Signal"]):
        return False

    prev_macd = float(previous["MACD"])
    prev_signal = float(previous["MACD_Signal"])
    curr_macd = float(current["MACD"])
    curr_signal = float(current["MACD_Signal"])

    # Previous day: MACD below signal
    # Current day: MACD at or above signal
    return prev_macd < prev_signal and curr_macd >= curr_signal


class SignalScanner:
    """Scans stock universe for trading signals."""

    def __init__(
        self,
        confidence_threshold: int = 55,
        stop_loss_percent: float = 4.5,
        take_profit_pct: float = 12.0,
        take_profit_ratio: float = 1.0,
        sell_on_middle_band: bool = False,
        use_cache: bool = True,
        # Bollinger Band parameters
        bollinger_period: int = 20,
        bollinger_std_dev: float = 2.0,
        # Squeeze detection parameters
        squeeze_threshold_pct: int = 70,
        squeeze_lookback_days: int = 10,
        # Position sizing parameters
        max_positions: int = 15,
        max_position_pct: float = 10.0,
    ):
        if not 1.0 <= stop_loss_percent <= 20.0:
            raise ValueError("stop_loss_percent must be between 1.0 and 20.0")
        if not 5.0 <= take_profit_pct <= 50.0:
            raise ValueError("take_profit_pct must be between 5.0 and 50.0")
        if not 0.1 <= take_profit_ratio <= 1.0:
            raise ValueError("take_profit_ratio must be between 0.1 and 1.0")

        self.confidence_threshold = confidence_threshold
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_pct = take_profit_pct
        self.take_profit_ratio = take_profit_ratio
        self.sell_on_middle_band = sell_on_middle_band
        self.use_cache = use_cache

        # Bollinger Band parameters
        self.bollinger_period = bollinger_period
        self.bollinger_std_dev = bollinger_std_dev

        # Squeeze detection parameters
        self.squeeze_threshold_pct = squeeze_threshold_pct
        self.squeeze_lookback_days = squeeze_lookback_days

        # Position sizing parameters
        self.max_positions = max_positions
        self.max_position_pct = max_position_pct

        self._cache: Dict[str, pd.DataFrame] = {}

    def _load_cache(self) -> None:
        """Load cache from disk if available (30 min TTL)."""
        if not self._cache and self.use_cache:
            try:
                from src.wizard.data_cache import load_cache, is_cache_valid

                # Use cache if valid within 30 minutes
                if is_cache_valid(max_age_hours=0.5):
                    self._cache = load_cache(max_age_hours=0.5, auto_refresh=False)
                else:
                    # Cache expired - don't load stale data, rely on DB
                    logger.debug("Cache expired (>30min), using DB as primary source")
            except Exception:
                pass

    def _get_stock_data(self, stock_code: str) -> Optional[pd.DataFrame]:
        """
        Get stock data with PostgreSQL-first caching strategy.

        Priority:
        1. PostgreSQL DB (primary source, most up-to-date)
        2. Memory/disk cache (fallback if DB unavailable)
        3. yfinance API (last resort)

        Args:
            stock_code: 6-digit stock code

        Returns:
            DataFrame with indicators or None
        """
        # L1: PostgreSQL DB (primary source - always has latest data)
        df = fetch_stock_data_from_db(stock_code)
        if df is not None and len(df) >= 30:
            df = calculate_indicators(
                df,
                bollinger_period=self.bollinger_period,
                bollinger_std_dev=self.bollinger_std_dev,
                squeeze_threshold_pct=self.squeeze_threshold_pct,
                squeeze_lookback_days=self.squeeze_lookback_days,
            )
            # Update memory cache
            self._cache[stock_code] = df.copy()
            return df

        # L2: Memory/disk cache (fallback if DB fails)
        self._load_cache()
        if stock_code in self._cache:
            cached_df = self._cache[stock_code].copy()
            # Recalculate indicators with user settings
            cached_df = calculate_indicators(
                cached_df,
                bollinger_period=self.bollinger_period,
                bollinger_std_dev=self.bollinger_std_dev,
                squeeze_threshold_pct=self.squeeze_threshold_pct,
                squeeze_lookback_days=self.squeeze_lookback_days,
            )
            logger.debug(f"{stock_code}: Using cache (DB unavailable)")
            return cached_df

        # L3: yfinance API (slow, 1-5s, last resort)
        df = fetch_stock_data(stock_code)
        if df is not None and len(df) >= 30:
            df = calculate_indicators(
                df,
                bollinger_period=self.bollinger_period,
                bollinger_std_dev=self.bollinger_std_dev,
                squeeze_threshold_pct=self.squeeze_threshold_pct,
                squeeze_lookback_days=self.squeeze_lookback_days,
            )
            # Update memory cache
            self._cache[stock_code] = df.copy()
            return df

        return None

    def scan_for_buy_signals(
        self,
        stock_codes: List[str],
        existing_positions: Optional[List[str]] = None,
        max_results: int = 10,
    ) -> List[StockSignal]:
        """Scan for BUY signals on stocks without positions."""
        signals = []
        existing = existing_positions or []
        candidates = [s for s in stock_codes if s not in existing]

        for stock_code in candidates:
            df = self._get_stock_data(stock_code)
            if df is None or len(df) < 35:
                continue
            latest = df.iloc[-1]

            if pd.isna(latest["BB_Upper"]) or pd.isna(latest["RSI"]):
                continue

            # Check BUY conditions
            price_breakout = latest["Close"] > latest["BB_Upper"]
            was_in_squeeze = df["In_Squeeze"].iloc[-5:-1].any()
            bandwidth_expanding = latest["BB_Width"] > df["BB_Width"].iloc[-2]

            if price_breakout and (was_in_squeeze or bandwidth_expanding):
                confidence = calculate_confidence_score(
                    volume_ratio=float(latest["Volume_Ratio"]),
                    rsi=float(latest["RSI"]),
                    macd_histogram=float(latest["MACD_Histogram"]),
                    macd_signal=float(latest["MACD_Signal"]),
                )

                if confidence >= self.confidence_threshold:
                    stock_name = get_stock_name(stock_code)
                    signals.append(
                        StockSignal(
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
                    )

        # Sort by confidence and return top results
        signals.sort(key=lambda x: x.confidence_score, reverse=True)
        return signals[:max_results]

    def scan_single_stock(self, stock_code: str) -> Optional[StockSignal]:
        """Scan a single stock for signals."""
        df = self._get_stock_data(stock_code)
        if df is None or len(df) < 35:
            return None

        latest = df.iloc[-1]

        if pd.isna(latest["BB_Upper"]) or pd.isna(latest["RSI"]):
            return None

        price_breakout = latest["Close"] > latest["BB_Upper"]
        was_in_squeeze = df["In_Squeeze"].iloc[-5:-1].any()
        bandwidth_expanding = latest["BB_Width"] > df["BB_Width"].iloc[-2]

        signal_type = "HOLD"
        reason = "no_signal"
        confidence = 0

        if price_breakout and (was_in_squeeze or bandwidth_expanding):
            signal_type = "BUY"
            reason = "squeeze_breakout_buy"
            confidence = calculate_confidence_score(
                volume_ratio=float(latest["Volume_Ratio"]),
                rsi=float(latest["RSI"]),
                macd_histogram=float(latest["MACD_Histogram"]),
                macd_signal=float(latest["MACD_Signal"]),
            )
        elif latest["Close"] < latest["BB_Lower"]:
            signal_type = "SELL"
            reason = "lower_band_touch"
            confidence = 100

        stock_name = get_stock_name(stock_code)
        return StockSignal(
            stock_code=stock_code,
            stock_name=stock_name,
            signal_type=signal_type,
            confidence_score=confidence,
            current_price=float(latest["Close"]),
            reason=reason,
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

    def scan_for_sell_signals(
        self,
        positions: List[dict],
    ) -> List[StockSignal]:
        signals = []

        for pos in positions:
            stock_code = pos.get("stock_code")
            stock_name = pos.get("stock_name") or get_stock_name(stock_code)
            entry_price = pos.get("avg_entry_price", 0)
            quantity = pos.get("quantity", 0)
            passed_current_price = pos.get("current_price")
            partial_take_profit_executed = pos.get("partial_take_profit_executed", False)

            if not stock_code or quantity <= 0:
                continue

            df = self._get_stock_data(stock_code)

            if df is not None:
                latest = df.iloc[-1]
                current_price = float(latest["Close"])
                bb_middle = float(latest["BB_Middle"]) if not pd.isna(latest["BB_Middle"]) else None
                base_indicators = {
                    "entry_price": entry_price,
                    "rsi": float(latest["RSI"]) if not pd.isna(latest["RSI"]) else 0,
                    "bb_lower": float(latest["BB_Lower"]) if not pd.isna(latest["BB_Lower"]) else 0,
                    "bb_middle": bb_middle if bb_middle is not None else 0,
                    "bb_upper": float(latest["BB_Upper"]) if not pd.isna(latest["BB_Upper"]) else 0,
                }
            elif passed_current_price:
                current_price = passed_current_price
                bb_middle = None
                base_indicators = {"entry_price": entry_price}
            else:
                continue

            pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
            base_indicators["pnl_pct"] = pnl_pct

            if pnl_pct <= -self.stop_loss_percent:
                signals.append(
                    StockSignal(
                        stock_code=stock_code,
                        stock_name=stock_name,
                        signal_type="SELL",
                        confidence_score=100,
                        current_price=current_price,
                        reason="stop_loss_hit",
                        indicators={
                            **base_indicators,
                            "sell_quantity": quantity,
                            "sell_ratio": 1.0,
                        },
                    )
                )
                continue

            if pnl_pct >= self.take_profit_pct and not partial_take_profit_executed:
                sell_quantity = max(1, math.ceil(quantity * self.take_profit_ratio))
                signals.append(
                    StockSignal(
                        stock_code=stock_code,
                        stock_name=stock_name,
                        signal_type="SELL",
                        confidence_score=100,
                        current_price=current_price,
                        reason="take_profit_target_hit",
                        indicators={
                            **base_indicators,
                            "sell_quantity": sell_quantity,
                            "sell_ratio": self.take_profit_ratio,
                        },
                    )
                )
                remaining_quantity = quantity - sell_quantity
                if (
                    self.sell_on_middle_band
                    and remaining_quantity > 0
                    and bb_middle is not None
                    and current_price < bb_middle
                ):
                    signals.append(
                        StockSignal(
                            stock_code=stock_code,
                            stock_name=stock_name,
                            signal_type="SELL",
                            confidence_score=100,
                            current_price=current_price,
                            reason="trend_broken_middle_band",
                            indicators={
                                **base_indicators,
                                "sell_quantity": remaining_quantity,
                                "sell_ratio": 1.0,
                            },
                        )
                    )
                continue

            if self.sell_on_middle_band and bb_middle is not None and current_price < bb_middle:
                signals.append(
                    StockSignal(
                        stock_code=stock_code,
                        stock_name=stock_name,
                        signal_type="SELL",
                        confidence_score=100,
                        current_price=current_price,
                        reason="trend_broken_middle_band",
                        indicators={
                            **base_indicators,
                            "sell_quantity": quantity,
                            "sell_ratio": 1.0,
                        },
                    )
                )

        return signals

    def scan_for_contrarian_signals(
        self,
        stock_codes: List[str],
        rsi_threshold: float = 30.0,
        confidence_threshold: float = 40.0,
        max_results: int = 10,
        target_date: Optional[date] = None,
    ) -> List[StockSignal]:
        """
        Scan for MACD/RSI contrarian BUY signals.

        Signal Criteria:
            1. RSI(14) <= rsi_threshold (oversold condition)
            2. MACD golden cross on most recent day
            3. Confidence score >= confidence_threshold

        Args:
            stock_codes: List of stock codes to scan
            rsi_threshold: Maximum RSI to consider (default 30)
            confidence_threshold: Minimum confidence score (default 40)
            max_results: Maximum number of signals to return
            target_date: Date to scan for signals (defaults to latest available)

        Returns:
            List of StockSignal with contrarian BUY signals
        """
        signals = []

        for stock_code in stock_codes:
            df = self._get_stock_data(stock_code)
            if df is None or len(df) < 35:
                continue

            # If target_date is specified, find the row for that date
            if target_date is not None:
                # Filter to data up to and including target_date
                df_filtered = df[df.index.date <= target_date]
                if len(df_filtered) < 35:
                    continue
                latest = df_filtered.iloc[-1]
                # Use filtered dataframe for golden cross detection
                df_for_cross = df_filtered
            else:
                latest = df.iloc[-1]
                df_for_cross = df

            # Check for NaN in required indicators
            if pd.isna(latest["RSI"]) or pd.isna(latest["MACD"]) or pd.isna(latest["MACD_Signal"]):
                continue

            rsi = float(latest["RSI"])
            macd = float(latest["MACD"])
            macd_signal = float(latest["MACD_Signal"])
            macd_histogram = float(latest["MACD_Histogram"])

            # Condition 1: RSI <= threshold (oversold)
            if rsi > rsi_threshold:
                continue

            # Condition 2: MACD golden cross on most recent day
            if not detect_macd_golden_cross(df_for_cross):
                continue

            # Calculate confidence score
            confidence = calculate_contrarian_confidence(rsi, macd_histogram, macd_signal)

            # Condition 3: Confidence >= threshold
            if confidence < confidence_threshold:
                continue

            # Generate signal with detailed reason
            stock_name = get_stock_name(stock_code)
            reason_detail = format_contrarian_reason_detail(
                rsi=rsi,
                macd=macd,
                macd_signal=macd_signal,
                macd_histogram=macd_histogram,
            )
            signals.append(
                StockSignal(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    signal_type="BUY",
                    confidence_score=confidence,
                    current_price=float(latest["Close"]),
                    reason="contrarian_oversold_reversal",
                    indicators={
                        "rsi": rsi,
                        "macd": macd,
                        "macd_signal": macd_signal,
                        "macd_histogram": macd_histogram,
                        "reason_detail": reason_detail,
                    },
                )
            )

        # Sort by confidence and return top results
        signals.sort(key=lambda x: x.confidence_score, reverse=True)
        return signals[:max_results]

    def get_current_prices(self, stock_codes: List[str]) -> Dict[str, float]:
        """Get current prices for a list of stocks."""
        prices = {}
        for stock_code in stock_codes:
            df = fetch_stock_data(stock_code, days=5)
            if df is not None and len(df) > 0:
                prices[stock_code] = float(df.iloc[-1]["Close"])
        return prices
