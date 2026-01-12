"""Price update API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/prices", tags=["Prices"])


class PriceUpdateRequest(BaseModel):
    """Request body for price update."""
    stock_codes: Optional[List[str]] = None


class PriceUpdateResponse(BaseModel):
    """Response for price update."""
    success: int
    failed: int
    total: int
    message: str


class SinglePriceResponse(BaseModel):
    """Response for single stock price."""
    stock_code: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


@router.post("/update", response_model=PriceUpdateResponse)
async def update_prices(request: PriceUpdateRequest = None):
    """
    Update closing prices for stocks.

    If stock_codes is not provided, updates all stocks that are
    missing today's price data.
    """
    from src.services.price_updater import update_all_closing_prices

    stock_codes = request.stock_codes if request else None
    result = update_all_closing_prices(stock_codes)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return PriceUpdateResponse(
        success=result.get("success", 0),
        failed=result.get("failed", 0),
        total=result.get("total", 0),
        message=f"Updated {result.get('success', 0)} stocks successfully"
    )


@router.post("/update/{stock_code}", response_model=SinglePriceResponse)
async def update_single_price(stock_code: str):
    """
    Update closing price for a single stock.

    Returns the updated price data.
    """
    from src.services.price_updater import fetch_closing_price, save_closing_price

    # Fetch price
    price_data = fetch_closing_price(stock_code)
    if not price_data:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch price for {stock_code}"
        )

    # Save to DB
    if not save_closing_price(stock_code, price_data):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save price for {stock_code}"
        )

    return SinglePriceResponse(
        stock_code=stock_code,
        date=price_data["date"].isoformat(),
        open=price_data["open"],
        high=price_data["high"],
        low=price_data["low"],
        close=price_data["close"],
        volume=price_data["volume"]
    )


@router.get("/realtime/{stock_code}", response_model=SinglePriceResponse)
async def get_realtime_price(stock_code: str):
    """
    Get real-time price for a stock (does not save to DB).
    """
    from src.services.price_updater import fetch_closing_price

    price_data = fetch_closing_price(stock_code)
    if not price_data:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch realtime price for {stock_code}"
        )

    return SinglePriceResponse(
        stock_code=stock_code,
        date=price_data["date"].isoformat(),
        open=price_data["open"],
        high=price_data["high"],
        low=price_data["low"],
        close=price_data["close"],
        volume=price_data["volume"]
    )


@router.get("/status")
async def get_price_status():
    """
    Get price update status - how many stocks need updates.
    """
    from src.services.price_updater import get_stocks_needing_update
    from datetime import date

    stocks_needing_update = get_stocks_needing_update()

    return {
        "date": date.today().isoformat(),
        "stocks_needing_update": len(stocks_needing_update),
        "sample_stocks": stocks_needing_update[:10] if stocks_needing_update else []
    }
