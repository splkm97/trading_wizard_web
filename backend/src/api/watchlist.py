"""Watchlist API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.auth.middleware import get_current_user
from src.db.database import get_db
from src.models.user import User
from src.models.watchlist import Watchlist
from src.services.watchlist_service import WatchlistService

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


@router.get("", response_model=List[WatchlistItem])
async def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's watchlist with insights."""
    service = WatchlistService(db)
    watchlists = service.get_user_watchlist(current_user.id)

    return [
        WatchlistItem(
            stock_code=w.stock_code,
            stock_name=w.stock_name,
            current_price=eval(w.current_price) if w.current_price else None,
            indicators=eval(w.indicators) if w.indicators else None,
            recommendation_score=w.recommendation_score,
            recommendation_reason=w.recommendation_reason,
            added_at=w.added_at.isoformat(),
        )
        for w in watchlists
    ]


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
