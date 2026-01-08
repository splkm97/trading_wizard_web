"""
Technical indicator calculations for trading strategies.
Extracted from trading_wizard_bundle for reuse in web application.
"""

import pandas as pd


def calculate_bollinger_bands(
    close: pd.Series, window: int = 12, num_std: float = 1.3
) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.

    Args:
        close: Close price series
        window: Moving average window (default 20)
        num_std: Number of standard deviations (default 2)

    Returns:
        Tuple of (upper, middle, lower, width, width_ma)
    """
    sma = close.rolling(window=window).mean()
    std = close.rolling(window=window).std()

    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    width = (upper - lower) / sma * 100
    width_ma = width.rolling(window=10).mean()

    return upper, sma, lower, width, width_ma


def calculate_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculate RSI (Relative Strength Index).

    Args:
        close: Close price series
        window: RSI window (default 14)

    Returns:
        RSI series (0-100)
    """
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_macd(
    close: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Args:
        close: Close price series
        fast_period: Fast EMA period (default 12)
        slow_period: Slow EMA period (default 26)
        signal_period: Signal line period (default 9)

    Returns:
        Tuple of (macd, signal, histogram)
    """
    ema_fast = close.ewm(span=fast_period).mean()
    ema_slow = close.ewm(span=slow_period).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=signal_period).mean()
    histogram = macd - signal

    return macd, signal, histogram


def calculate_volume_ratio(volume: pd.Series, window: int = 20) -> pd.Series:
    """
    Calculate volume ratio to moving average.

    Args:
        volume: Volume series
        window: Moving average window (default 20)

    Returns:
        Volume ratio series
    """
    volume_ma = volume.rolling(window=window).mean()
    return volume / volume_ma


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all technical indicators needed for signal generation.

    Args:
        df: DataFrame with OHLCV data (columns: Open, High, Low, Close, Volume)

    Returns:
        DataFrame with added indicator columns
    """
    df = df.copy()
    close = df["Close"]
    volume = df["Volume"]

    # Bollinger Bands
    bb_upper, bb_middle, bb_lower, bb_width, bb_width_ma = calculate_bollinger_bands(close)
    df["BB_Upper"] = bb_upper
    df["BB_Middle"] = bb_middle
    df["BB_Lower"] = bb_lower
    df["BB_Width"] = bb_width
    df["BB_Width_MA"] = bb_width_ma

    # RSI
    df["RSI"] = calculate_rsi(close)

    # MACD
    macd, macd_signal, macd_histogram = calculate_macd(close)
    df["MACD"] = macd
    df["MACD_Signal"] = macd_signal
    df["MACD_Histogram"] = macd_histogram

    # Volume
    df["Volume_MA"] = volume.rolling(window=20).mean()
    df["Volume_Ratio"] = calculate_volume_ratio(volume)

    df["In_Squeeze"] = df["BB_Width"] < (df["BB_Width_MA"] * 0.55)

    df["MA_200"] = close.rolling(window=200).mean()

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

    Args:
        volume_ratio: Volume / 20-day average volume
        rsi: RSI value (0-100)
        macd_histogram: MACD histogram value
        macd_signal: MACD signal line value

    Returns:
        Confidence score (0-100)
    """
    score = 25.0  # Base score for Bollinger breakout

    # Volume Score (0-25점)
    # 1.0x -> 0점, 1.5x -> 12.5점, 2.0x -> 25점 (cap)
    if volume_ratio > 1.0:
        vol_score = min(25.0, (volume_ratio - 1.0) * 25.0)
        score += vol_score

    # RSI Score (0-20점)
    # 50이 최적(20점), 30/70에서 0점, 범위 밖은 0점
    if 30 <= rsi <= 70:
        distance = abs(rsi - 50)
        rsi_score = 20.0 * (1 - distance / 20.0)
        score += rsi_score

    # MACD Score (0-30점)
    # Histogram이 양수일 때, Signal 대비 비율로 점수 계산
    if macd_histogram > 0:
        macd_signal_abs = abs(macd_signal) if macd_signal != 0 else 0.001
        macd_ratio = min(macd_histogram / macd_signal_abs, 1.0)
        macd_score = 30.0 * macd_ratio
        score += macd_score

    return score
