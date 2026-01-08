"""Trade API endpoints."""

from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.auth.middleware import get_current_user
from src.models.user import User
from src.models.trade import Trade, TradeAction
from src.services.trade_service import TradeService
from src.services.portfolio_service import PortfolioService
from src.core.exceptions import ValidationError, NotFoundError
from src.core.logging import logger

router = APIRouter(prefix="/trades", tags=["Trades"])


# Request/Response models
class TradeCreateRequest(BaseModel):
    """Request to create a new trade."""

    trade_date: date = Field(..., description="Trade date (YYYY-MM-DD)")
    stock_code: str = Field(..., min_length=6, max_length=6, pattern=r"^[0-9]{6}$")
    action: str = Field(..., pattern=r"^(BUY|SELL)$", description="BUY or SELL")
    quantity: int = Field(..., gt=0, description="Number of shares")
    price: float = Field(..., gt=0, description="Price per share (KRW)")
    reason: Optional[str] = Field(None, max_length=100, description="Trade reason/notes")
    entry_reason: Optional[str] = Field(None, max_length=50, description="Entry reason for position (BUY only)")
    confidence_score: Optional[int] = Field(None, ge=0, le=100, description="Confidence score (0-100)")


class TradeResponse(BaseModel):
    """Trade response model."""

    id: str
    portfolio_id: str
    trade_date: str
    stock_code: str
    stock_name: str
    action: str
    quantity: int
    price: float
    total_amount: float
    realized_pnl: Optional[float] = None
    reason: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class TradeListResponse(BaseModel):
    """Response for trade list with pagination."""

    trades: list[TradeResponse]
    total: int
    page: int
    page_size: int


@router.post("", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def create_trade(
    request: TradeCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new trade.

    Creates a BUY or SELL trade and updates the portfolio accordingly.
    - BUY: Deducts cash, creates/updates position
    - SELL: Increases cash, reduces/removes position, calculates realized P&L
    """
    try:
        portfolio_service = PortfolioService(db)
        portfolio = portfolio_service.get_portfolio(current_user.id)

        trade_service = TradeService(db)
        trade = trade_service.create_trade(
            portfolio_id=portfolio.id,
            trade_date=request.trade_date,
            stock_code=request.stock_code,
            action=request.action,
            quantity=request.quantity,
            price=Decimal(str(request.price)),
            reason=request.reason,
            entry_reason=request.entry_reason,
            confidence_score=request.confidence_score,
        )

        return TradeResponse(
            id=trade.id,
            portfolio_id=trade.portfolio_id,
            trade_date=trade.trade_date.isoformat(),
            stock_code=trade.stock_code,
            stock_name=trade.stock_name,
            action=trade.action.value,
            quantity=trade.quantity,
            price=float(trade.price),
            total_amount=float(trade.total_amount),
            realized_pnl=float(trade.realized_pnl) if trade.realized_pnl else None,
            reason=trade.reason,
            created_at=trade.created_at.isoformat(),
        )

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.message))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))


@router.get("", response_model=TradeListResponse)
async def list_trades(
    stock_code: Optional[str] = Query(None, description="Filter by stock code"),
    action: Optional[str] = Query(None, pattern=r"^(BUY|SELL)$", description="Filter by action"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List trades with optional filters and pagination."""
    try:
        portfolio_service = PortfolioService(db)
        portfolio = portfolio_service.get_portfolio(current_user.id)

        # Build query
        query = db.query(Trade).filter(Trade.portfolio_id == portfolio.id)

        if stock_code:
            query = query.filter(Trade.stock_code == stock_code)
        if action:
            query = query.filter(Trade.action == TradeAction(action))
        if start_date:
            query = query.filter(Trade.trade_date >= start_date)
        if end_date:
            query = query.filter(Trade.trade_date <= end_date)

        # Get total count
        total = query.count()

        # Apply pagination
        trades = (
            query.order_by(Trade.trade_date.desc(), Trade.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return TradeListResponse(
            trades=[
                TradeResponse(
                    id=t.id,
                    portfolio_id=t.portfolio_id,
                    trade_date=t.trade_date.isoformat(),
                    stock_code=t.stock_code,
                    stock_name=t.stock_name,
                    action=t.action.value,
                    quantity=t.quantity,
                    price=float(t.price),
                    total_amount=float(t.total_amount),
                    realized_pnl=float(t.realized_pnl) if t.realized_pnl else None,
                    reason=t.reason,
                    created_at=t.created_at.isoformat(),
                )
                for t in trades
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trade(
    trade_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a trade and rollback its effects.

    This reverses the trade:
    - BUY: Restores cash, removes/reduces position
    - SELL: Deducts cash, restores position
    """
    try:
        portfolio_service = PortfolioService(db)
        portfolio = portfolio_service.get_portfolio(current_user.id)

        trade_service = TradeService(db)
        trade_service.delete_trade(trade_id, portfolio.id)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.message))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))


@router.get("/export", response_class=StreamingResponse)
async def export_trades_csv(
    stock_code: Optional[str] = Query(None, description="Filter by stock code"),
    action: Optional[str] = Query(None, pattern=r"^(BUY|SELL)$", description="Filter by action"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export trades to CSV file.

    Returns a CSV file containing all trades matching the filter criteria.
    """
    try:
        portfolio_service = PortfolioService(db)
        portfolio = portfolio_service.get_portfolio(current_user.id)

        # Build query
        query = db.query(Trade).filter(Trade.portfolio_id == portfolio.id)

        if stock_code:
            query = query.filter(Trade.stock_code == stock_code)
        if action:
            query = query.filter(Trade.action == TradeAction(action))
        if start_date:
            query = query.filter(Trade.trade_date >= start_date)
        if end_date:
            query = query.filter(Trade.trade_date <= end_date)

        trades = query.order_by(Trade.trade_date.desc(), Trade.created_at.desc()).all()

        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([
            "거래일",
            "종목코드",
            "종목명",
            "거래유형",
            "수량",
            "단가",
            "거래금액",
            "실현손익",
            "거래사유",
            "입력일시",
        ])

        # Data rows
        for trade in trades:
            writer.writerow([
                trade.trade_date.isoformat(),
                trade.stock_code,
                trade.stock_name,
                trade.action.value,
                trade.quantity,
                float(trade.price),
                float(trade.total_amount),
                float(trade.realized_pnl) if trade.realized_pnl else "",
                trade.reason or "",
                trade.created_at.isoformat(),
            ])

        output.seek(0)

        # Generate filename with date range
        filename_parts = ["trades"]
        if start_date:
            filename_parts.append(f"from_{start_date.isoformat()}")
        if end_date:
            filename_parts.append(f"to_{end_date.isoformat()}")
        filename = "_".join(filename_parts) + ".csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8",
            },
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))
