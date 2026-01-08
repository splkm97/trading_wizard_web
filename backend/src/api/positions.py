"""Positions API endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.auth.middleware import get_current_user
from src.models.user import User
from src.services.portfolio_service import PortfolioService
from src.services.price_service import price_service
from src.core.exceptions import NotFoundError

router = APIRouter(prefix="/positions", tags=["Positions"])


class PositionResponse(BaseModel):
    """Position response."""

    id: str
    stock_code: str
    stock_name: str
    quantity: int
    avg_entry_price: float
    total_cost: float
    first_entry_date: str
    entry_reason: Optional[str] = None
    confidence_score: Optional[int] = None
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None


class PositionListResponse(BaseModel):
    """List of positions."""

    positions: list[PositionResponse]
    total: int


@router.get("", response_model=PositionListResponse)
async def list_positions(
    include_prices: bool = Query(False, description="Include current prices"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all positions in portfolio.

    Set include_prices=true to fetch current stock prices.
    """
    try:
        service = PortfolioService(db)
        portfolio = service.get_portfolio(current_user.id)
        positions = service.get_positions(portfolio.id)

        # Get current prices if requested
        current_prices = {}
        if include_prices and positions:
            stock_codes = [p.stock_code for p in positions]
            current_prices = price_service.get_prices_batch(stock_codes)

        position_list = []
        for p in positions:
            pos_data = {
                "id": p.id,
                "stock_code": p.stock_code,
                "stock_name": p.stock_name,
                "quantity": p.quantity,
                "avg_entry_price": float(p.avg_entry_price),
                "total_cost": float(p.total_cost),
                "first_entry_date": p.first_entry_date.isoformat(),
                "entry_reason": p.entry_reason,
                "confidence_score": p.confidence_score,
            }

            if include_prices:
                current_price = current_prices.get(p.stock_code)
                if current_price:
                    from decimal import Decimal

                    current_value = current_price * p.quantity
                    unrealized_pnl = current_value - p.total_cost
                    pnl_pct = (unrealized_pnl / p.total_cost * 100) if p.total_cost else Decimal("0")

                    pos_data["current_price"] = float(current_price)
                    pos_data["current_value"] = float(current_value)
                    pos_data["unrealized_pnl"] = float(unrealized_pnl)
                    pos_data["unrealized_pnl_pct"] = float(pnl_pct)
                else:
                    pos_data["current_price"] = None
                    pos_data["current_value"] = None
                    pos_data["unrealized_pnl"] = None
                    pos_data["unrealized_pnl_pct"] = None

            position_list.append(PositionResponse(**pos_data))

        return PositionListResponse(positions=position_list, total=len(position_list))

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))


@router.get("/{stock_code}", response_model=PositionResponse)
async def get_position(
    stock_code: str,
    include_price: bool = Query(False, description="Include current price"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific position by stock code."""
    try:
        service = PortfolioService(db)
        portfolio = service.get_portfolio(current_user.id)
        position = service.get_position(portfolio.id, stock_code)

        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No position found for {stock_code}",
            )

        pos_data = {
            "id": position.id,
            "stock_code": position.stock_code,
            "stock_name": position.stock_name,
            "quantity": position.quantity,
            "avg_entry_price": float(position.avg_entry_price),
            "total_cost": float(position.total_cost),
            "first_entry_date": position.first_entry_date.isoformat(),
            "entry_reason": position.entry_reason,
            "confidence_score": position.confidence_score,
        }

        if include_price:
            current_price = price_service.get_current_price(stock_code)
            if current_price:
                from decimal import Decimal

                current_value = current_price * position.quantity
                unrealized_pnl = current_value - position.total_cost
                pnl_pct = (unrealized_pnl / position.total_cost * 100) if position.total_cost else Decimal("0")

                pos_data["current_price"] = float(current_price)
                pos_data["current_value"] = float(current_value)
                pos_data["unrealized_pnl"] = float(unrealized_pnl)
                pos_data["unrealized_pnl_pct"] = float(pnl_pct)
            else:
                pos_data["current_price"] = None
                pos_data["current_value"] = None
                pos_data["unrealized_pnl"] = None
                pos_data["unrealized_pnl_pct"] = None

        return PositionResponse(**pos_data)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))
