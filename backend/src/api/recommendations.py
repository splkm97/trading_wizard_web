"""Recommendations API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.auth.middleware import get_current_user
from src.db.database import get_db
from src.models.user import User
from src.models.user_settings import UserSettings
from src.services.signal_precomputer import (
    get_cached_signals_with_staleness,
    precompute_all_signals,
)
from src.wizard.recommendation import (
    RecommendationEngine,
    format_buy_reason_detail,
    format_signal_reason_detail,
)
from src.wizard.signal_scanner import SignalScanner, StockSignal, load_kospi_top100

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class IndicatorsResponse(BaseModel):
    rsi: float
    macd_histogram: float
    volume_ratio: float
    bb_width: float
    bb_upper: float
    bb_middle: float
    bb_lower: float


class SignalResponse(BaseModel):
    stock_code: str
    stock_name: str
    signal_type: str
    confidence_score: float
    current_price: float
    reason: str
    indicators: dict


class BuyRecommendationResponse(BaseModel):
    stock_code: str
    stock_name: str
    recommended_price: float
    quantity: int
    total_cost: float
    confidence_score: float
    reason: str
    reason_detail: str
    indicators: dict


class SellRecommendationResponse(BaseModel):
    stock_code: str
    stock_name: str
    current_price: float
    quantity: int
    sell_quantity: int
    sell_ratio: float
    entry_price: float
    pnl_pct: float
    reason: str
    indicators: dict


class BuySignalResponse(BaseModel):
    stock_code: str
    stock_name: str
    current_price: float
    confidence_score: float
    reason: str
    reason_detail: str
    indicators: dict
    affordable: bool


class AppliedSettingsResponse(BaseModel):
    """Settings that were applied to generate recommendations."""

    # Risk Management
    stop_loss_pct: float
    max_positions: int
    max_position_pct: float
    confidence_threshold: int

    # Take Profit
    take_profit_pct: float
    take_profit_ratio: float

    # Sell Conditions
    sell_on_middle_band: bool

    # Bollinger Band
    bollinger_period: int
    bollinger_std_dev: float

    # Squeeze Detection
    squeeze_threshold_pct: int
    squeeze_lookback_days: int


class RecommendationsResponse(BaseModel):
    buy_recommendations: list[BuyRecommendationResponse]
    sell_recommendations: list[SellRecommendationResponse]
    all_buy_signals: list[BuySignalResponse]  # All signals regardless of cash
    scanned_count: int
    signal_count: int
    applied_settings: AppliedSettingsResponse  # Settings used for this scan


def _trigger_background_refresh():
    """Trigger background signal refresh (non-blocking)."""
    try:
        precompute_all_signals(force_fetch=False)
        logger.debug("Background signal refresh completed")
    except Exception as e:
        logger.warning(f"Background signal refresh failed: {e}")


@router.get("", response_model=RecommendationsResponse)
async def get_recommendations(
    background_tasks: BackgroundTasks,
    max_results: int = Query(default=5, ge=1, le=20),
    confidence_threshold: int = Query(default=60, ge=0, le=100),
    force_fetch: bool = Query(
        default=False, description="Force fetch from yfinance and save to DB"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get buy recommendations based on KOSPI Top 100 scan.

    This endpoint scans the KOSPI Top 100 stocks and returns
    buy recommendations based on the Bollinger Band Squeeze strategy.

    Data source:
    - Default: Uses pre-computed cached signals with stale-while-revalidate
      - If cache is fresh (< 1 min): Return immediately
      - If cache is stale (1-5 min): Return stale data + trigger background refresh
      - If cache is expired (> 5 min): Compute fresh (slower)
    - force_fetch=true: Force fresh computation from yfinance
    """
    # Stale-while-revalidate uses the signal_precomputer functions directly
    existing_positions = []
    available_cash = 1_000_000
    initial_capital = 1_000_000
    position_count = 0

    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()

    # Read all settings from UserSettings or use defaults
    stop_loss_pct = float(settings.stop_loss_pct) if settings else 4.5
    take_profit_pct = float(settings.take_profit_pct) if settings else 12.0
    take_profit_ratio = float(settings.take_profit_ratio) if settings else 1.0
    sell_on_middle_band = settings.sell_on_middle_band if settings else False

    # Bollinger Band parameters
    bollinger_period = settings.bollinger_period if settings else 15
    bollinger_std_dev = float(settings.bollinger_std_dev) if settings else 1.5

    # Squeeze detection parameters
    squeeze_threshold_pct = settings.squeeze_threshold_pct if settings else 60
    squeeze_lookback_days = settings.squeeze_lookback_days if settings else 10

    # Position sizing parameters
    max_positions = settings.max_positions if settings else 15
    max_position_pct = float(settings.max_position_pct) if settings else 10.0

    # Use confidence_threshold from settings if not overridden by query param
    if confidence_threshold == 60:  # default value
        confidence_threshold = settings.confidence_threshold if settings else 55

    # Load KOSPI Top 100
    try:
        stock_codes = load_kospi_top100()
    except FileNotFoundError:
        # Fallback to a few major stocks if file not found
        stock_codes = [
            "005930",  # Samsung Electronics
            "000660",  # SK Hynix
            "035420",  # NAVER
            "051910",  # LG Chem
            "006400",  # Samsung SDI
        ]

    # Stale-While-Revalidate: Try to use cached signals if not force_fetch
    signals = []
    use_cache = not force_fetch

    if use_cache:
        # Use stale-while-revalidate pattern
        cached_data, is_stale = get_cached_signals_with_staleness("bollinger")

        if cached_data and "signals" in cached_data:
            cache_age = cached_data.get("computed_at", "unknown")
            if is_stale:
                logger.info(
                    f"Using STALE cached signals (computed at {cache_age}), "
                    "triggering background refresh"
                )
                # Schedule background refresh (non-blocking)
                background_tasks.add_task(_trigger_background_refresh)
            else:
                logger.debug(f"Using FRESH cached signals (computed at {cache_age})")

            # Convert cached dicts back to StockSignal objects
            for sig_dict in cached_data["signals"]:
                # Filter out existing positions
                if sig_dict["stock_code"] not in existing_positions:
                    signals.append(
                        StockSignal(
                            stock_code=sig_dict["stock_code"],
                            stock_name=sig_dict["stock_name"],
                            signal_type=sig_dict["signal_type"],
                            confidence_score=sig_dict["confidence_score"],
                            current_price=sig_dict["current_price"],
                            reason=sig_dict["reason"],
                            indicators=sig_dict["indicators"],
                        )
                    )
            # Filter by confidence threshold
            signals = [s for s in signals if s.confidence_score >= confidence_threshold]

    # If no cached signals (even stale) or force_fetch, compute fresh
    if not signals or force_fetch:
        scanner = SignalScanner(
            confidence_threshold=confidence_threshold,
            stop_loss_percent=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            take_profit_ratio=take_profit_ratio,
            sell_on_middle_band=sell_on_middle_band,
            bollinger_period=bollinger_period,
            bollinger_std_dev=bollinger_std_dev,
            squeeze_threshold_pct=squeeze_threshold_pct,
            squeeze_lookback_days=squeeze_lookback_days,
            max_positions=max_positions,
            max_position_pct=max_position_pct,
        )
        signals = scanner.scan_for_buy_signals(
            stock_codes=stock_codes,
            existing_positions=existing_positions,
            max_results=max_results * 2,
            force_fetch=force_fetch,
        )
        logger.debug(f"Computed fresh signals: {len(signals)} found")

    # Create scanner instance for sell signals (reuse cached signals for buy)
    scanner = SignalScanner(
        confidence_threshold=confidence_threshold,
        stop_loss_percent=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        take_profit_ratio=take_profit_ratio,
        sell_on_middle_band=sell_on_middle_band,
        bollinger_period=bollinger_period,
        bollinger_std_dev=bollinger_std_dev,
        squeeze_threshold_pct=squeeze_threshold_pct,
        squeeze_lookback_days=squeeze_lookback_days,
        max_positions=max_positions,
        max_position_pct=max_position_pct,
    )

    # Generate recommendations with position sizing from user settings
    engine = RecommendationEngine(
        max_positions=max_positions,
        max_position_percent=max_position_pct,
        confidence_threshold=confidence_threshold,
    )

    recommendations = engine.generate_buy_recommendations(
        signals=signals,
        available_cash=float(available_cash),
        current_position_count=position_count,
        initial_capital=float(initial_capital),
    )

    # Portfolio, position, and trade functionality removed - no sell recommendations
    sell_recs = []

    # Convert BUY recommendations to response format
    buy_recs = []
    for rec in recommendations[:max_results]:
        reason_detail = format_buy_reason_detail(rec)
        buy_recs.append(
            BuyRecommendationResponse(
                stock_code=rec.stock_code,
                stock_name=rec.stock_name,
                recommended_price=rec.recommended_price,
                quantity=rec.quantity,
                total_cost=rec.total_cost,
                confidence_score=rec.confidence_score,
                reason=rec.reason,
                reason_detail=reason_detail,
                indicators=rec.indicators,
            )
        )

    # All buy signals (regardless of affordability)
    recommended_codes = {rec.stock_code for rec in recommendations}
    all_buy_signals = []
    for sig in signals:
        # Check if this stock is in the affordable recommendations
        is_affordable = sig.stock_code in recommended_codes
        reason_detail = format_signal_reason_detail(sig)
        all_buy_signals.append(
            BuySignalResponse(
                stock_code=sig.stock_code,
                stock_name=sig.stock_name,
                current_price=sig.current_price,
                confidence_score=sig.confidence_score,
                reason=sig.reason,
                reason_detail=reason_detail,
                indicators=sig.indicators,
                affordable=is_affordable,
            )
        )

    # Build applied settings response
    applied_settings = AppliedSettingsResponse(
        stop_loss_pct=stop_loss_pct,
        max_positions=max_positions,
        max_position_pct=max_position_pct,
        confidence_threshold=confidence_threshold,
        take_profit_pct=take_profit_pct,
        take_profit_ratio=take_profit_ratio,
        sell_on_middle_band=sell_on_middle_band,
        bollinger_period=bollinger_period,
        bollinger_std_dev=bollinger_std_dev,
        squeeze_threshold_pct=squeeze_threshold_pct,
        squeeze_lookback_days=squeeze_lookback_days,
    )

    return RecommendationsResponse(
        buy_recommendations=buy_recs,
        sell_recommendations=sell_recs,
        all_buy_signals=all_buy_signals,
        scanned_count=len(stock_codes),
        signal_count=len(signals) + len(sell_recs),
        applied_settings=applied_settings,
    )


@router.get("/signal/{stock_code}", response_model=SignalResponse)
async def get_stock_signal(
    stock_code: str,
    _current_user: User = Depends(get_current_user),
):
    """Get signal analysis for a specific stock."""
    scanner = SignalScanner()
    signal = scanner.scan_single_stock(stock_code)

    if signal is None:
        return SignalResponse(
            stock_code=stock_code,
            stock_name=stock_code,
            signal_type="UNKNOWN",
            confidence_score=0,
            current_price=0,
            reason="insufficient_data",
            indicators={},
        )

    return SignalResponse(
        stock_code=signal.stock_code,
        stock_name=signal.stock_name,
        signal_type=signal.signal_type,
        confidence_score=signal.confidence_score,
        current_price=signal.current_price,
        reason=signal.reason,
        indicators=signal.indicators,
    )
