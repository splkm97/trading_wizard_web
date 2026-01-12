"""Contrarian Strategy API endpoints for MACD/RSI signals."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.auth.middleware import get_current_user
from src.db.database import get_db
from src.models.user import User
from src.models.user_settings import UserSettings
from src.wizard.signal_scanner import SignalScanner, load_kospi_top100

router = APIRouter(prefix="/contrarian", tags=["contrarian"])


# Pydantic Schemas

class ContrarianIndicators(BaseModel):
    """Technical indicators for contrarian signals."""
    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float


class ContrarianSignal(BaseModel):
    """Individual contrarian signal response."""
    stock_code: str
    stock_name: str
    signal_type: str  # Always "BUY" for contrarian signals
    confidence_score: float
    current_price: float
    reason: str
    indicators: ContrarianIndicators


class AppliedContrarianSettings(BaseModel):
    """Settings that were applied for the contrarian scan."""
    rsi_period: int
    rsi_threshold: float
    macd_fast_period: int
    macd_slow_period: int
    macd_signal_period: int
    confidence_threshold: float


class ContrarianSignalsResponse(BaseModel):
    """Response for contrarian signals endpoint."""
    signals: List[ContrarianSignal]
    scanned_count: int
    signal_count: int
    applied_settings: AppliedContrarianSettings
    scan_date: str  # Date for which signals were scanned (YYYY-MM-DD)


class SingleContrarianSignalResponse(BaseModel):
    """Response for single stock contrarian signal."""
    signal: Optional[ContrarianSignal]
    applied_settings: AppliedContrarianSettings


# Endpoints

@router.get("/signals", response_model=ContrarianSignalsResponse)
async def get_contrarian_signals(
    max_results: int = Query(default=10, ge=1, le=50),
    scan_date: Optional[str] = Query(default=None, description="Date to scan for signals (YYYY-MM-DD). Defaults to today."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get MACD/RSI contrarian buy signals.

    Scans KOSPI Top 100 for stocks with:
    - RSI <= threshold (oversold)
    - MACD golden cross (momentum reversal)
    - Confidence score >= threshold

    Args:
        max_results: Maximum number of results to return
        scan_date: Date to scan for signals (YYYY-MM-DD). Defaults to today.
    """
    # Parse scan_date or use today
    if scan_date:
        try:
            target_date = datetime.strptime(scan_date, "%Y-%m-%d").date()
        except ValueError:
            target_date = date.today()
    else:
        target_date = date.today()
    # Load user settings
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()

    # Get contrarian strategy settings
    rsi_period = settings.macd_rsi_rsi_period if settings else 14
    rsi_threshold = float(settings.macd_rsi_rsi_threshold) if settings else 30.0
    macd_fast_period = settings.macd_rsi_macd_fast_period if settings else 12
    macd_slow_period = settings.macd_rsi_macd_slow_period if settings else 26
    macd_signal_period = settings.macd_rsi_macd_signal_period if settings else 9
    confidence_threshold = float(settings.macd_rsi_confidence_threshold) if settings else 40.0

    # Load stock codes
    try:
        stock_codes = load_kospi_top100()
    except FileNotFoundError:
        stock_codes = ["005930", "000660", "035420", "051910", "006400"]

    # Initialize scanner with user's Bollinger settings (for indicator calculation)
    bollinger_period = settings.bollinger_period if settings else 15
    bollinger_std_dev = float(settings.bollinger_std_dev) if settings else 1.5
    squeeze_threshold_pct = settings.squeeze_threshold_pct if settings else 60
    squeeze_lookback_days = settings.squeeze_lookback_days if settings else 10

    scanner = SignalScanner(
        bollinger_period=bollinger_period,
        bollinger_std_dev=bollinger_std_dev,
        squeeze_threshold_pct=squeeze_threshold_pct,
        squeeze_lookback_days=squeeze_lookback_days,
    )

    # Scan for contrarian signals
    signals = scanner.scan_for_contrarian_signals(
        stock_codes=stock_codes,
        rsi_threshold=rsi_threshold,
        confidence_threshold=confidence_threshold,
        max_results=max_results,
        target_date=target_date,
    )

    # Convert to response format
    response_signals = []
    for sig in signals:
        response_signals.append(
            ContrarianSignal(
                stock_code=sig.stock_code,
                stock_name=sig.stock_name,
                signal_type=sig.signal_type,
                confidence_score=sig.confidence_score,
                current_price=sig.current_price,
                reason=sig.reason,
                indicators=ContrarianIndicators(
                    rsi=sig.indicators["rsi"],
                    macd=sig.indicators["macd"],
                    macd_signal=sig.indicators["macd_signal"],
                    macd_histogram=sig.indicators["macd_histogram"],
                ),
            )
        )

    # Build applied settings
    applied_settings = AppliedContrarianSettings(
        rsi_period=rsi_period,
        rsi_threshold=rsi_threshold,
        macd_fast_period=macd_fast_period,
        macd_slow_period=macd_slow_period,
        macd_signal_period=macd_signal_period,
        confidence_threshold=confidence_threshold,
    )

    return ContrarianSignalsResponse(
        signals=response_signals,
        scanned_count=len(stock_codes),
        signal_count=len(response_signals),
        applied_settings=applied_settings,
        scan_date=target_date.strftime("%Y-%m-%d"),
    )
