"""Watchlist API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.auth.middleware import get_current_user
from src.db.database import get_db
from src.models.user import User
from src.services.watchlist_service import WatchlistService
from src.wizard.signal_scanner import SignalScanner, fetch_stock_data

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/watchlists", tags=["watchlists"])


class WatchlistItem(BaseModel):
    stock_code: str
    stock_name: str
    current_price: dict | None
    indicators: dict | None
    recommendation_score: int | None
    recommendation_reason: str | None
    added_at: str


class AddToWatchlistRequest(BaseModel):
    stock_code: str
    stock_name: str


@router.get("", response_model=list[WatchlistItem])
async def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's watchlist with real-time insights."""
    service = WatchlistService(db)
    watchlists = service.get_user_watchlist(current_user.id)

    # Create scanner to analyze stocks
    scanner = SignalScanner()
    result = []

    for w in watchlists:
        try:
            # Fetch real-time data
            df = fetch_stock_data(w.stock_code)

            if df is not None and len(df) >= 20:
                latest = df.iloc[-1]

                # Get current price info
                current_price = {
                    "close": float(latest["Close"]),
                    "open": float(latest["Open"]),
                    "high": float(latest["High"]),
                    "low": float(latest["Low"]),
                }

                # Calculate indicators
                indicators = None
                if "RSI" in df.columns and "MACD" in df.columns:
                    indicators = {
                        "rsi": float(latest["RSI"]) if not df["RSI"].isna().iloc[-1] else None,
                        "macd": float(latest["MACD"]) if not df["MACD"].isna().iloc[-1] else None,
                        "macd_signal": float(latest["MACD_Signal"]) if "MACD_Signal" in df.columns and not df["MACD_Signal"].isna().iloc[-1] else None,
                    }

                # Get recommendation score and reason
                score = None
                reason = None
                signal = scanner.analyze_stock(w.stock_code, w.stock_name)
                if signal:
                    score = signal.get("score", signal.get("confidence"))
                    reasons = signal.get("reasons", [])
                    reason = "\n".join(reasons) if reasons else None

                result.append(WatchlistItem(
                    stock_code=w.stock_code,
                    stock_name=w.stock_name,
                    current_price=current_price,
                    indicators=indicators,
                    recommendation_score=score,
                    recommendation_reason=reason,
                    added_at=w.added_at.isoformat(),
                ))
            else:
                # No data available
                result.append(WatchlistItem(
                    stock_code=w.stock_code,
                    stock_name=w.stock_name,
                    current_price=None,
                    indicators=None,
                    recommendation_score=None,
                    recommendation_reason=None,
                    added_at=w.added_at.isoformat(),
                ))
        except Exception as e:
            logger.error(f"Error fetching data for {w.stock_code}: {e}")
            result.append(WatchlistItem(
                stock_code=w.stock_code,
                stock_name=w.stock_name,
                current_price=None,
                indicators=None,
                recommendation_score=None,
                recommendation_reason=None,
                added_at=w.added_at.isoformat(),
            ))

    return result


@router.post("")
async def add_to_watchlist(
    request: AddToWatchlistRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add stock to watchlist."""
    service = WatchlistService(db)
    watchlist = service.add_to_watchlist(current_user.id, request.stock_code, request.stock_name)
    return {"status": "added", "watchlist_id": watchlist.id}


@router.delete("/{stock_code}")
async def remove_from_watchlist(
    stock_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove stock from watchlist."""
    service = WatchlistService(db)
    success = service.remove_from_watchlist(current_user.id, stock_code)

    if not success:
        raise HTTPException(status_code=404, detail="Stock not in watchlist")

    return {"status": "removed"}
