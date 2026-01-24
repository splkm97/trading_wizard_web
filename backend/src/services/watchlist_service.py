"""Watchlist service for managing stock watchlists with insights."""

import json

from sqlalchemy.orm import Session

from src.models.watchlist import Watchlist


class WatchlistService:
    """Service for watchlist CRUD operations and insights."""

    def __init__(self, db: Session):
        self.db = db

    def add_to_watchlist(self, user_id: str, stock_code: str, stock_name: str) -> Watchlist:
        """Add stock to user's watchlist."""
        existing = (
            self.db.query(Watchlist)
            .filter(Watchlist.user_id == user_id, Watchlist.stock_code == stock_code)
            .first()
        )

        if existing:
            return existing

        watchlist = Watchlist(user_id=user_id, stock_code=stock_code, stock_name=stock_name)
        self.db.add(watchlist)
        self.db.commit()
        self.db.refresh(watchlist)
        return watchlist

    def remove_from_watchlist(self, user_id: str, stock_code: str) -> bool:
        """Remove stock from user's watchlist."""
        watchlist = (
            self.db.query(Watchlist)
            .filter(Watchlist.user_id == user_id, Watchlist.stock_code == stock_code)
            .first()
        )

        if not watchlist:
            return False

        self.db.delete(watchlist)
        self.db.commit()
        return True

    def get_user_watchlist(self, user_id: str) -> list[Watchlist]:
        """Get all watchlist entries for user."""
        return (
            self.db.query(Watchlist)
            .filter(Watchlist.user_id == user_id)
            .order_by(Watchlist.added_at.desc())
            .all()
        )

    def update_insights(
        self,
        watchlist_id: str,
        price_data: dict,
        indicators: dict,
        score: int | None = None,
        reason: str | None = None,
    ):
        """Update price and insights for watchlist entry."""
        watchlist = self.db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()

        if not watchlist:
            return

        watchlist.current_price = json.dumps(price_data) if price_data else None
        watchlist.indicators = json.dumps(indicators) if indicators else None
        watchlist.recommendation_score = score
        watchlist.recommendation_reason = reason
        self.db.commit()
