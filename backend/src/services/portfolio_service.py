"""Portfolio service for summary and management."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from src.models.portfolio import Portfolio
from src.models.position import Position
from src.services.price_service import price_service
from src.core.exceptions import NotFoundError
from src.core.logging import logger


class PortfolioService:
    """Service for portfolio operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_portfolio(self, user_id: str) -> Portfolio:
        """Get portfolio by user ID.

        Args:
            user_id: User ID

        Returns:
            Portfolio object

        Raises:
            NotFoundError: If portfolio not found
        """
        portfolio = self.db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        if not portfolio:
            raise NotFoundError("Portfolio not found")
        return portfolio

    def get_portfolio_summary(self, user_id: str, include_prices: bool = False) -> dict:
        """Get portfolio summary with positions.

        Args:
            user_id: User ID
            include_prices: Whether to fetch current prices from Yahoo Finance

        Returns:
            Portfolio summary dict
        """
        portfolio = self.get_portfolio(user_id)
        positions = (
            self.db.query(Position)
            .filter(Position.portfolio_id == portfolio.id)
            .all()
        )

        # Calculate totals
        total_invested = sum(p.total_cost for p in positions)
        cash_balance = Decimal(str(portfolio.cash_balance))
        initial_capital = Decimal(str(portfolio.initial_capital))

        # Get current prices if requested
        current_prices = {}
        if include_prices and positions:
            stock_codes = [p.stock_code for p in positions]
            current_prices = price_service.get_prices_batch(stock_codes)

        # Build position list with optional current values
        position_list = []
        total_current_value = Decimal("0")
        total_unrealized_pnl = Decimal("0")

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
                    current_value = current_price * p.quantity
                    unrealized_pnl = current_value - p.total_cost
                    pnl_pct = (unrealized_pnl / p.total_cost * 100) if p.total_cost else Decimal("0")

                    pos_data["current_price"] = float(current_price)
                    pos_data["current_value"] = float(current_value)
                    pos_data["unrealized_pnl"] = float(unrealized_pnl)
                    pos_data["unrealized_pnl_pct"] = float(pnl_pct)

                    total_current_value += current_value
                    total_unrealized_pnl += unrealized_pnl
                else:
                    pos_data["current_price"] = None
                    pos_data["current_value"] = None
                    pos_data["unrealized_pnl"] = None
                    pos_data["unrealized_pnl_pct"] = None

            position_list.append(pos_data)

        # Total value calculation
        if include_prices and positions:
            total_value = cash_balance + total_current_value
        else:
            total_value = cash_balance + total_invested

        # Return percentage
        return_pct = ((total_value - initial_capital) / initial_capital * 100) if initial_capital else Decimal("0")

        result = {
            "portfolio_id": portfolio.id,
            "initial_capital": float(initial_capital),
            "cash_balance": float(cash_balance),
            "total_invested": float(total_invested),
            "total_value": float(total_value),
            "return_pct": float(return_pct),
            "position_count": len(positions),
            "positions": position_list,
        }

        if include_prices:
            result["total_unrealized_pnl"] = float(total_unrealized_pnl)

        return result

    def update_initial_capital(self, user_id: str, amount: Decimal) -> Portfolio:
        """Update initial capital and reset cash balance.

        Args:
            user_id: User ID
            amount: New initial capital amount

        Returns:
            Updated portfolio

        Raises:
            NotFoundError: If portfolio not found
        """
        portfolio = self.get_portfolio(user_id)

        # Check if there are any positions
        position_count = (
            self.db.query(Position)
            .filter(Position.portfolio_id == portfolio.id)
            .count()
        )

        if position_count > 0:
            logger.warning(f"Updating initial capital with {position_count} existing positions")

        portfolio.initial_capital = amount
        portfolio.cash_balance = amount
        self.db.commit()

        logger.info(f"Initial capital updated to {amount:,.0f} for user {user_id}")
        return portfolio

    def get_positions(self, portfolio_id: str) -> list[Position]:
        """Get all positions for a portfolio.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            List of Position objects
        """
        return (
            self.db.query(Position)
            .filter(Position.portfolio_id == portfolio_id)
            .order_by(Position.stock_code)
            .all()
        )

    def get_position(self, portfolio_id: str, stock_code: str) -> Optional[Position]:
        """Get a specific position.

        Args:
            portfolio_id: Portfolio ID
            stock_code: Stock code

        Returns:
            Position or None
        """
        return (
            self.db.query(Position)
            .filter(
                Position.portfolio_id == portfolio_id,
                Position.stock_code == stock_code,
            )
            .first()
        )
