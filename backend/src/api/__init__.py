"""API router configuration."""

from fastapi import APIRouter

from src.api import (
    health,
    auth,
    stocks,
    recommendations,
    backtest,
    settings,
    simulation,
    contrarian,
    prices,
    watchlist,
)

api_router = APIRouter(prefix="/api")

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router)
api_router.include_router(stocks.router)
api_router.include_router(recommendations.router)
api_router.include_router(backtest.router)
api_router.include_router(settings.router)
api_router.include_router(simulation.router)
api_router.include_router(contrarian.router)
api_router.include_router(prices.router)
api_router.include_router(watchlist.router)
