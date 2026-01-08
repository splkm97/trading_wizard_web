"""API router configuration."""

from fastapi import APIRouter

from src.api import (
    health,
    auth,
    trades,
    stocks,
    portfolio,
    positions,
    recommendations,
    backtest,
    settings,
    stock_lists,
    simulation,
)

api_router = APIRouter(prefix="/api")

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router)
api_router.include_router(trades.router)
api_router.include_router(stocks.router)
api_router.include_router(portfolio.router)
api_router.include_router(positions.router)
api_router.include_router(recommendations.router)
api_router.include_router(backtest.router)
api_router.include_router(settings.router)
api_router.include_router(stock_lists.router)
api_router.include_router(simulation.router)
