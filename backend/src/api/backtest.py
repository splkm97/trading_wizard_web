"""Backtest API endpoints."""

from __future__ import annotations

import json
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.auth.middleware import get_current_user
from src.models.user import User
from src.models.backtest import BacktestResult
from src.services.backtest_service import BacktestService
from src.core.exceptions import NotFoundError
from src.core.logging import logger

router = APIRouter(prefix="/backtest", tags=["Backtest"])


# Request/Response models
class StrategyOverrides(BaseModel):
    """Optional strategy parameter overrides for a single backtest run."""

    # Risk Management
    max_positions: Optional[int] = Field(None, ge=1, le=50)
    max_position_pct: Optional[float] = Field(None, ge=1, le=100)
    stop_loss_pct: Optional[float] = Field(None, ge=1, le=50)
    confidence_threshold: Optional[int] = Field(None, ge=0, le=100)

    # Take Profit Settings
    take_profit_enabled: Optional[bool] = None
    take_profit_pct: Optional[float] = Field(None, ge=5, le=50)
    take_profit_ratio: Optional[float] = Field(None, ge=0.1, le=1.0)

    # Bollinger Band Parameters
    bollinger_period: Optional[int] = Field(None, ge=5, le=200)
    bollinger_std_dev: Optional[float] = Field(None, gt=0, le=5)

    # Squeeze Detection
    squeeze_threshold_pct: Optional[int] = Field(None, ge=5, le=100)
    squeeze_lookback_days: Optional[int] = Field(None, ge=2, le=30)

    # Advanced Squeeze Settings
    expansion_threshold_pct: Optional[float] = Field(None, ge=5, le=100)
    band_touch_tolerance: Optional[float] = Field(None, ge=0, le=0.01)

    # Metrics Configuration
    trading_days_per_year: Optional[int] = Field(None, ge=200, le=365)
    days_per_year: Optional[int] = Field(None, ge=360, le=366)


class BacktestRunRequest(BaseModel):
    """Request to run a backtest."""

    start_date: date = Field(..., description="Backtest start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="Backtest end date (YYYY-MM-DD)")
    stock_list: str = Field(
        ...,
        description="Stock list name (e.g., kospi_top100_2025jan) or custom list ID/name",
    )
    initial_capital: float = Field(1_000_000, gt=0, description="Initial capital (KRW)")
    name: Optional[str] = Field(None, max_length=100, description="Backtest name")
    strategy_overrides: Optional[StrategyOverrides] = Field(
        None, description="Optional strategy parameter overrides for this backtest"
    )


class BacktestResultResponse(BaseModel):
    """Backtest result summary."""

    id: str
    name: Optional[str]
    start_date: str
    end_date: str
    stock_list_name: str
    initial_capital: float
    final_value: float
    total_return_pct: float
    max_drawdown_pct: float
    total_trades: int
    winning_trades: int
    win_rate_pct: float
    created_at: str

    class Config:
        from_attributes = True


class BacktestResultDetailResponse(BacktestResultResponse):
    """Detailed backtest result with trade history."""

    result_json: dict


class BacktestResultsListResponse(BaseModel):
    """List of backtest results."""

    results: list[BacktestResultResponse]
    total: int


@router.post("/run", response_model=BacktestResultResponse, status_code=status.HTTP_201_CREATED)
async def run_backtest(
    request: BacktestRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run a backtest simulation.

    Executes the Bollinger Band Squeeze strategy backtest using the user's settings.
    This is a synchronous operation that may take up to 3 minutes.
    """
    # Validate dates
    if request.start_date >= request.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date",
        )

    try:
        # Create backtest service with user settings
        backtest_service = BacktestService.from_user_settings(db, current_user.id)

        # Apply strategy overrides if provided
        if request.strategy_overrides:
            overrides = request.strategy_overrides.model_dump(exclude_none=True)
            for key, value in overrides.items():
                if hasattr(backtest_service, key):
                    setattr(backtest_service, key, value)
            logger.info(f"Applied strategy overrides: {list(overrides.keys())}")

        result = backtest_service.run_backtest(
            user_id=current_user.id,
            start_date=request.start_date,
            end_date=request.end_date,
            stock_list_name=request.stock_list,
            initial_capital=request.initial_capital,
            name=request.name,
        )

        return BacktestResultResponse(
            id=result.id,
            name=result.name,
            start_date=result.start_date.isoformat(),
            end_date=result.end_date.isoformat(),
            stock_list_name=result.stock_list_name,
            initial_capital=float(result.initial_capital),
            final_value=float(result.final_value),
            total_return_pct=float(result.total_return_pct),
            max_drawdown_pct=float(result.max_drawdown_pct),
            total_trades=result.total_trades,
            winning_trades=result.winning_trades,
            win_rate_pct=float(result.win_rate_pct),
            created_at=result.created_at.isoformat(),
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtest execution failed: {str(e)}",
        )


@router.get("/results", response_model=BacktestResultsListResponse)
async def list_backtest_results(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get list of user's backtest results."""
    backtest_service = BacktestService(db)
    results = backtest_service.get_results(current_user.id, limit=limit)

    return BacktestResultsListResponse(
        results=[
            BacktestResultResponse(
                id=r.id,
                name=r.name,
                start_date=r.start_date.isoformat(),
                end_date=r.end_date.isoformat(),
                stock_list_name=r.stock_list_name,
                initial_capital=float(r.initial_capital),
                final_value=float(r.final_value),
                total_return_pct=float(r.total_return_pct),
                max_drawdown_pct=float(r.max_drawdown_pct),
                total_trades=r.total_trades,
                winning_trades=r.winning_trades,
                win_rate_pct=float(r.win_rate_pct),
                created_at=r.created_at.isoformat(),
            )
            for r in results
        ],
        total=len(results),
    )


@router.get("/{result_id}", response_model=BacktestResultDetailResponse)
async def get_backtest_result(
    result_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed backtest result including trade history."""
    backtest_service = BacktestService(db)
    result = backtest_service.get_result(result_id, current_user.id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest result not found",
        )

    # Parse result_json
    result_json = result.result_json
    if isinstance(result_json, str):
        result_json = json.loads(result_json)

    return BacktestResultDetailResponse(
        id=result.id,
        name=result.name,
        start_date=result.start_date.isoformat(),
        end_date=result.end_date.isoformat(),
        stock_list_name=result.stock_list_name,
        initial_capital=float(result.initial_capital),
        final_value=float(result.final_value),
        total_return_pct=float(result.total_return_pct),
        max_drawdown_pct=float(result.max_drawdown_pct),
        total_trades=result.total_trades,
        winning_trades=result.winning_trades,
        win_rate_pct=float(result.win_rate_pct),
        created_at=result.created_at.isoformat(),
        result_json=result_json,
    )
