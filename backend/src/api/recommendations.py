"""Recommendations API endpoints."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.auth.middleware import get_current_user
from src.db.database import get_db
from src.models.user import User
from src.models.portfolio import Portfolio
from src.models.user_settings import UserSettings
from src.wizard.signal_scanner import SignalScanner, load_kospi_top100, StockSignal
from src.wizard.recommendation import (
    RecommendationEngine,
    BuyRecommendation,
    format_buy_reason_detail,
)
from src.wizard.data_cache import refresh_cache, get_cache_info, is_cache_valid

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
    indicators: dict
    affordable: bool


class RecommendationsResponse(BaseModel):
    buy_recommendations: List[BuyRecommendationResponse]
    sell_recommendations: List[SellRecommendationResponse]
    all_buy_signals: List[BuySignalResponse]  # All signals regardless of cash
    scanned_count: int
    signal_count: int


@router.get("", response_model=RecommendationsResponse)
async def get_recommendations(
    max_results: int = Query(default=5, ge=1, le=20),
    confidence_threshold: int = Query(default=60, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get buy recommendations based on KOSPI Top 100 scan.

    This endpoint scans the KOSPI Top 100 stocks and returns
    buy recommendations based on the Bollinger Band Squeeze strategy.
    """
    # Get user's portfolio to check existing positions
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()

    existing_positions = []
    available_cash = 1_000_000  # Default
    initial_capital = 1_000_000  # Default
    position_count = 0

    if portfolio:
        existing_positions = [p.stock_code for p in portfolio.positions]
        available_cash = portfolio.cash_balance
        initial_capital = portfolio.initial_capital
        position_count = len(portfolio.positions)

    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    stop_loss_pct = float(settings.stop_loss_pct) if settings else 4.5
    take_profit_pct = float(settings.take_profit_pct) if settings else 12.0
    take_profit_ratio = float(settings.take_profit_ratio) if settings else 1.0
    sell_on_middle_band = settings.sell_on_middle_band if settings else False

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

    scanner = SignalScanner(
        confidence_threshold=confidence_threshold,
        stop_loss_percent=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        take_profit_ratio=take_profit_ratio,
        sell_on_middle_band=sell_on_middle_band,
    )
    signals = scanner.scan_for_buy_signals(
        stock_codes=stock_codes,
        existing_positions=existing_positions,
        max_results=max_results * 2,  # Get more signals for filtering
    )

    # Generate recommendations with position sizing
    engine = RecommendationEngine(
        max_positions=15,
        max_position_percent=10.0,
        confidence_threshold=confidence_threshold,
    )

    recommendations = engine.generate_buy_recommendations(
        signals=signals,
        available_cash=float(available_cash),
        current_position_count=position_count,
        initial_capital=float(initial_capital),
    )

    # Scan for SELL signals on existing positions
    sell_recs = []
    if portfolio and portfolio.positions:
        import yfinance as yf

        positions_data = []
        for p in portfolio.positions:
            current_price = None
            try:
                ticker = yf.Ticker(f"{p.stock_code}.KS")
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = float(hist["Close"].iloc[-1])
            except Exception:
                pass
            positions_data.append(
                {
                    "stock_code": p.stock_code,
                    "stock_name": p.stock_name,
                    "avg_entry_price": float(p.avg_entry_price),
                    "quantity": p.quantity,
                    "current_price": current_price,
                    "partial_take_profit_executed": getattr(
                        p, "partial_take_profit_executed", False
                    ),
                }
            )
        sell_signals = scanner.scan_for_sell_signals(positions_data)

        for sig in sell_signals:
            pos = next((p for p in portfolio.positions if p.stock_code == sig.stock_code), None)
            if pos:
                sell_recs.append(
                    SellRecommendationResponse(
                        stock_code=sig.stock_code,
                        stock_name=sig.stock_name,
                        current_price=sig.current_price,
                        quantity=pos.quantity,
                        sell_quantity=sig.indicators.get("sell_quantity", pos.quantity),
                        sell_ratio=sig.indicators.get("sell_ratio", 1.0),
                        entry_price=float(pos.avg_entry_price),
                        pnl_pct=sig.indicators.get("pnl_pct", 0),
                        reason=sig.reason,
                        indicators=sig.indicators,
                    )
                )

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
        all_buy_signals.append(
            BuySignalResponse(
                stock_code=sig.stock_code,
                stock_name=sig.stock_name,
                current_price=sig.current_price,
                confidence_score=sig.confidence_score,
                reason=sig.reason,
                indicators=sig.indicators,
                affordable=is_affordable,
            )
        )

    return RecommendationsResponse(
        buy_recommendations=buy_recs,
        sell_recommendations=sell_recs,
        all_buy_signals=all_buy_signals,
        scanned_count=len(stock_codes),
        signal_count=len(signals) + len(sell_recs),
    )


@router.get("/signal/{stock_code}", response_model=SignalResponse)
async def get_stock_signal(
    stock_code: str,
    current_user: User = Depends(get_current_user),
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


class CacheStatusResponse(BaseModel):
    cached: bool
    valid: bool
    timestamp: Optional[str] = None
    stock_count: Optional[int] = None


class CacheRefreshResponse(BaseModel):
    status: str
    message: str


@router.get("/cache/status", response_model=CacheStatusResponse)
async def get_cache_status(
    current_user: User = Depends(get_current_user),
):
    """Get current cache status."""
    info = get_cache_info()

    if info:
        return CacheStatusResponse(
            cached=True,
            valid=is_cache_valid(max_age_hours=24),
            timestamp=info.get("timestamp"),
            stock_count=info.get("stock_count"),
        )

    return CacheStatusResponse(cached=False, valid=False)


@router.post("/cache/refresh", response_model=CacheRefreshResponse)
async def refresh_stock_cache(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Refresh stock data cache in background.

    Downloads KOSPI Top 100 stock data and caches locally.
    Takes about 10-20 seconds.
    """
    background_tasks.add_task(refresh_cache)

    return CacheRefreshResponse(
        status="started",
        message="Cache refresh started in background. Check /cache/status for progress.",
    )
