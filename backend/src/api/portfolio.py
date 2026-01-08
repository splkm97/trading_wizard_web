"""Portfolio API endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.auth.middleware import get_current_user
from src.models.user import User
from src.services.portfolio_service import PortfolioService
from src.core.exceptions import NotFoundError

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


class PositionResponse(BaseModel):
    """Position in portfolio."""

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


class PortfolioSummaryResponse(BaseModel):
    """Portfolio summary response."""

    portfolio_id: str
    initial_capital: float
    cash_balance: float
    total_invested: float
    total_value: float
    return_pct: float
    position_count: int
    positions: list[PositionResponse]
    total_unrealized_pnl: Optional[float] = None


class UpdateCapitalRequest(BaseModel):
    """Request to update initial capital."""

    initial_capital: float = Field(..., gt=0, description="New initial capital (KRW)")


@router.get("", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    include_prices: bool = Query(False, description="Include current prices from Yahoo Finance"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get portfolio summary with positions.

    Set include_prices=true to fetch current stock prices (may take longer).
    """
    try:
        service = PortfolioService(db)
        summary = service.get_portfolio_summary(current_user.id, include_prices=include_prices)
        return PortfolioSummaryResponse(**summary)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))


@router.put("/capital", response_model=PortfolioSummaryResponse)
async def update_initial_capital(
    request: UpdateCapitalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update initial capital.

    Warning: This resets the cash balance to the new initial capital.
    Existing positions will not be affected.
    """
    try:
        from decimal import Decimal

        service = PortfolioService(db)
        service.update_initial_capital(current_user.id, Decimal(str(request.initial_capital)))

        # Return updated summary
        summary = service.get_portfolio_summary(current_user.id)
        return PortfolioSummaryResponse(**summary)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))
