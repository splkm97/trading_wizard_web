"""Simulation game API endpoints."""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.auth.middleware import get_current_user
from src.models.user import User
from src.models.game_session import GameStatus
from src.services.simulation_service import (
    SimulationService,
    InsufficientFundsError,
    DuplicateBuyError,
    InvalidDateRangeError,
    GameNotFoundError,
)

router = APIRouter(prefix="/simulation", tags=["Simulation"])


class CreateSessionRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    start_date: date
    end_date: date
    initial_capital: float = Field(100_000_000, gt=0)


class GameSessionResponse(BaseModel):
    id: str
    name: Optional[str]
    start_date: str
    end_date: str
    current_date: str
    initial_capital: float
    cash_balance: float
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PositionResponse(BaseModel):
    id: str
    stock_code: str
    stock_name: str
    quantity: int
    avg_entry_price: float
    entry_date: str
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None


class GameSessionWithSummaryResponse(GameSessionResponse):
    positions: list[PositionResponse] = []
    total_positions_value: float = 0
    total_value: float = 0
    total_return: float = 0
    total_return_pct: float = 0
    unrealized_pnl: float = 0
    is_game_over: bool = False


class ExecuteTradeRequest(BaseModel):
    stock_code: str
    action: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: Optional[int] = Field(None, gt=0)
    amount: Optional[float] = Field(None, gt=0)


class ExecuteTradeResponse(BaseModel):
    trade: SimulatedTradeResponse
    session: GameSessionWithSummaryResponse


class SimulatedTradeResponse(BaseModel):
    id: str
    trade_date: str
    stock_code: str
    stock_name: str
    action: str
    quantity: int
    price: float
    total_amount: float
    realized_pnl: Optional[float]
    realized_pnl_pct: Optional[float]
    confidence_score: Optional[float]
    created_at: str

    class Config:
        from_attributes = True


def _session_to_response(session) -> GameSessionResponse:
    return GameSessionResponse(
        id=session.id,
        name=session.name,
        start_date=session.start_date.isoformat(),
        end_date=session.end_date.isoformat(),
        current_date=session.current_date.isoformat(),
        initial_capital=float(session.initial_capital),
        cash_balance=float(session.cash_balance),
        status=session.status.value,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )


def _trade_to_response(trade) -> SimulatedTradeResponse:
    return SimulatedTradeResponse(
        id=trade.id,
        trade_date=trade.trade_date.isoformat(),
        stock_code=trade.stock_code,
        stock_name=trade.stock_name,
        action=trade.action.value,
        quantity=trade.quantity,
        price=float(trade.price),
        total_amount=float(trade.total_amount),
        realized_pnl=float(trade.realized_pnl) if trade.realized_pnl else None,
        realized_pnl_pct=float(trade.realized_pnl_pct) if trade.realized_pnl_pct else None,
        confidence_score=float(trade.confidence_score) if trade.confidence_score else None,
        created_at=trade.created_at.isoformat(),
    )


@router.post("/sessions", response_model=GameSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new simulation game session."""
    service = SimulationService(db)

    try:
        from decimal import Decimal

        session = service.create_session(
            user_id=current_user.id,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=Decimal(str(request.initial_capital)),
            name=request.name,
        )
        return _session_to_response(session)
    except InvalidDateRangeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/sessions", response_model=list[GameSessionResponse])
async def list_sessions(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List user's game sessions."""
    service = SimulationService(db)

    game_status = None
    if status_filter:
        try:
            game_status = GameStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}. Must be one of: IN_PROGRESS, COMPLETED, ABANDONED",
            )

    sessions = service.list_sessions(current_user.id, status=game_status)
    return [_session_to_response(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=GameSessionWithSummaryResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific game session with portfolio summary."""
    service = SimulationService(db)

    try:
        service.get_session(session_id, current_user.id)
        summary = service.calculate_portfolio_summary(
            service.get_session(session_id, current_user.id)
        )
        return GameSessionWithSummaryResponse(
            id=summary["id"],
            name=summary["name"],
            start_date=summary["start_date"],
            end_date=summary["end_date"],
            current_date=summary["current_date"],
            initial_capital=summary["initial_capital"],
            cash_balance=summary["cash_balance"],
            status=summary["status"],
            created_at=summary["created_at"],
            updated_at=summary["updated_at"],
            positions=[PositionResponse(**p) for p in summary["positions"]],
            total_positions_value=summary["total_positions_value"],
            total_value=summary["total_value"],
            total_return=summary["total_return"],
            total_return_pct=summary["total_return_pct"],
            unrealized_pnl=summary["unrealized_pnl"],
            is_game_over=summary["is_game_over"],
        )
    except GameNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a game session."""
    service = SimulationService(db)

    try:
        service.delete_session(session_id, current_user.id)
    except GameNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")


@router.get("/sessions/{session_id}/recommendations")
async def get_recommendations(
    session_id: str,
    min_score: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get stock recommendations for current turn."""
    service = SimulationService(db)

    try:
        session = service.get_session(session_id, current_user.id)
        return service.get_recommendations(session, min_score=min_score)
    except GameNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/sessions/{session_id}/stocks/{stock_code}")
async def get_stock_detail(
    session_id: str,
    stock_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get stock detail with chart and indicators."""
    service = SimulationService(db)

    try:
        session = service.get_session(session_id, current_user.id)
        return service.get_stock_detail(session, stock_code)
    except GameNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/sessions/{session_id}/trade", response_model=ExecuteTradeResponse)
async def execute_trade(
    session_id: str,
    request: ExecuteTradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute a trade (buy or sell)."""
    from decimal import Decimal
    from src.services.stock_service import stock_service

    service = SimulationService(db)

    try:
        session = service.get_session(session_id, current_user.id)

        if session.status != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in progress",
            )

        current_price = service.get_price_at_date(request.stock_code, session.current_date)
        if current_price is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to fetch price for {request.stock_code}",
            )

        price = Decimal(str(current_price))

        if request.action == "BUY":
            if not request.quantity and not request.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either quantity or amount is required for BUY",
                )

            quantity = int(request.amount / current_price) if request.amount else request.quantity
            if not quantity or quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity must be greater than 0",
                )

            stock_name = stock_service.get_stock_name_or_default(
                request.stock_code, request.stock_code
            )

            try:
                detail = service.get_stock_detail(session, request.stock_code)
                confidence_score = Decimal(str(detail.get("confidence_score", 0)))
            except Exception:
                confidence_score = None

            trade = service.execute_buy(
                session=session,
                stock_code=request.stock_code,
                stock_name=stock_name,
                quantity=quantity,
                price=price,
                confidence_score=confidence_score,
            )
        else:
            trade = service.execute_sell(
                session=session,
                stock_code=request.stock_code,
                price=price,
            )

        summary = service.calculate_portfolio_summary(session)
        session_response = GameSessionWithSummaryResponse(
            id=summary["id"],
            name=summary["name"],
            start_date=summary["start_date"],
            end_date=summary["end_date"],
            current_date=summary["current_date"],
            initial_capital=summary["initial_capital"],
            cash_balance=summary["cash_balance"],
            status=summary["status"],
            created_at=summary["created_at"],
            updated_at=summary["updated_at"],
            positions=[PositionResponse(**p) for p in summary["positions"]],
            total_positions_value=summary["total_positions_value"],
            total_value=summary["total_value"],
            total_return=summary["total_return"],
            total_return_pct=summary["total_return_pct"],
            unrealized_pnl=summary["unrealized_pnl"],
            is_game_over=summary["is_game_over"],
        )

        return ExecuteTradeResponse(
            trade=_trade_to_response(trade),
            session=session_response,
        )

    except GameNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    except InsufficientFundsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"현금이 부족합니다. 필요: {e.required:,.0f}원, 보유: {e.available:,.0f}원",
        )
    except DuplicateBuyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"이미 {e.stock_code} 종목을 보유 중입니다. 매도/홀딩만 가능합니다.",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


class AdvanceTurnResponse(BaseModel):
    session: GameSessionWithSummaryResponse
    recommendations: list[dict] = []
    is_game_over: bool = False


@router.post("/sessions/{session_id}/turn", response_model=AdvanceTurnResponse)
async def advance_turn(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Advance to next trading day."""
    service = SimulationService(db)

    try:
        session = service.get_session(session_id, current_user.id)

        if session.status != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in progress",
            )

        session = service.advance_turn(session)
        summary = service.calculate_portfolio_summary(session)

        recommendations = []
        if not session.is_game_over:
            recommendations = service.get_recommendations(session)

        session_response = GameSessionWithSummaryResponse(
            id=summary["id"],
            name=summary["name"],
            start_date=summary["start_date"],
            end_date=summary["end_date"],
            current_date=summary["current_date"],
            initial_capital=summary["initial_capital"],
            cash_balance=summary["cash_balance"],
            status=summary["status"],
            created_at=summary["created_at"],
            updated_at=summary["updated_at"],
            positions=[PositionResponse(**p) for p in summary["positions"]],
            total_positions_value=summary["total_positions_value"],
            total_value=summary["total_value"],
            total_return=summary["total_return"],
            total_return_pct=summary["total_return_pct"],
            unrealized_pnl=summary["unrealized_pnl"],
            is_game_over=summary["is_game_over"],
        )

        return AdvanceTurnResponse(
            session=session_response,
            recommendations=recommendations,
            is_game_over=session.is_game_over,
        )
    except GameNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")


@router.get("/sessions/{session_id}/report")
async def get_report(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get backtest-style report."""
    service = SimulationService(db)

    try:
        session = service.get_session(session_id, current_user.id)
        return service.generate_report(session)
    except GameNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/sessions/{session_id}/export")
async def export_trades(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export trades as JSON."""
    service = SimulationService(db)

    try:
        session = service.get_session(session_id, current_user.id)
        return service.export_trades(session)
    except GameNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


class PrecomputeResponse(BaseModel):
    days_computed: int
    message: str


@router.post("/sessions/{session_id}/precompute", response_model=PrecomputeResponse)
async def precompute_recommendations(
    session_id: str,
    days_ahead: int = 3,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pre-compute recommendations for next N trading days."""
    service = SimulationService(db)

    try:
        session = service.get_session(session_id, current_user.id)

        if session.status != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in progress",
            )

        days_computed = service.precompute_recommendations(session, days_ahead=days_ahead)

        return PrecomputeResponse(
            days_computed=days_computed,
            message=f"Pre-computed {days_computed} days of recommendations",
        )
    except GameNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
