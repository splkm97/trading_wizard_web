"""Stock lookup API endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from src.auth.middleware import get_current_user
from src.models.user import User
from src.services.stock_service import stock_service

router = APIRouter(prefix="/stocks", tags=["Stocks"])


class StockInfo(BaseModel):
    """Stock information response."""

    code: str
    name: str


class StockSearchResponse(BaseModel):
    """Stock search response."""

    results: list[StockInfo]
    total: int


@router.get("/search", response_model=StockSearchResponse)
async def search_stocks(
    q: str = Query(..., min_length=1, description="Search query (code prefix or name)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    current_user: User = Depends(get_current_user),
):
    """Search stocks by code or name.

    - Code prefix search: "0059" matches "005930" (삼성전자)
    - Name search: "삼성" matches stocks with "삼성" in name
    """
    results = stock_service.search_stocks(q, limit=limit)

    return StockSearchResponse(
        results=[StockInfo(code=r["code"], name=r["name"]) for r in results],
        total=len(results),
    )


@router.get("/{stock_code}", response_model=StockInfo)
async def get_stock(
    stock_code: str,
    current_user: User = Depends(get_current_user),
):
    """Get stock information by code.

    Args:
        stock_code: 6-digit stock code
    """
    if not stock_service.validate_stock_code(stock_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid stock code format. Must be 6 digits.",
        )

    name = stock_service.get_stock_name(stock_code)
    if not name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock not found: {stock_code}",
        )

    return StockInfo(code=stock_code, name=name)
