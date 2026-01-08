"""Trade processing service."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from src.models.portfolio import Portfolio
from src.models.position import Position
from src.models.trade import Trade, TradeAction
from src.services.stock_service import stock_service
from src.core.exceptions import ValidationError, NotFoundError
from src.core.logging import logger


class TradeService:
    """Service for processing trades and updating positions."""

    def __init__(self, db: Session):
        self.db = db

    def create_trade(
        self,
        portfolio_id: str,
        trade_date: date,
        stock_code: str,
        action: str,
        quantity: int,
        price: Decimal,
        reason: Optional[str] = None,
        entry_reason: Optional[str] = None,
        confidence_score: Optional[int] = None,
    ) -> Trade:
        """Create and process a new trade.

        Args:
            portfolio_id: Portfolio ID
            trade_date: Date of trade
            stock_code: 6-digit stock code
            action: 'BUY' or 'SELL'
            quantity: Number of shares
            price: Price per share
            reason: Trade reason/notes
            entry_reason: Entry reason for position (BUY only)
            confidence_score: Confidence score for position (BUY only)

        Returns:
            Created Trade object

        Raises:
            ValidationError: If trade validation fails
            NotFoundError: If portfolio or stock not found
        """
        # Validate stock code
        if not stock_service.validate_stock_code(stock_code):
            raise ValidationError(f"Invalid stock code format: {stock_code}")

        # Get stock name
        stock_name = stock_service.get_stock_name(stock_code)
        if not stock_name:
            raise ValidationError(f"Unknown stock code: {stock_code}")

        # Validate action
        try:
            trade_action = TradeAction(action.upper())
        except ValueError:
            raise ValidationError(f"Invalid trade action: {action}")

        # Get portfolio
        portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise NotFoundError("Portfolio not found")

        # Validate quantity and price
        if quantity <= 0:
            raise ValidationError("Quantity must be positive")
        if price <= 0:
            raise ValidationError("Price must be positive")

        price = Decimal(str(price))
        total_amount = price * quantity

        if trade_action == TradeAction.BUY:
            trade = self._process_buy(
                portfolio=portfolio,
                trade_date=trade_date,
                stock_code=stock_code,
                stock_name=stock_name,
                quantity=quantity,
                price=price,
                reason=reason,
                entry_reason=entry_reason,
                confidence_score=confidence_score,
            )
        else:
            trade = self._process_sell(
                portfolio=portfolio,
                trade_date=trade_date,
                stock_code=stock_code,
                stock_name=stock_name,
                quantity=quantity,
                price=price,
                reason=reason,
            )

        self.db.commit()
        logger.info(f"Trade created: {trade}")
        return trade

    def _process_buy(
        self,
        portfolio: Portfolio,
        trade_date: date,
        stock_code: str,
        stock_name: str,
        quantity: int,
        price: Decimal,
        reason: Optional[str] = None,
        entry_reason: Optional[str] = None,
        confidence_score: Optional[int] = None,
    ) -> Trade:
        """Process a BUY trade."""
        total_amount = price * quantity

        # Check cash balance
        cash_balance = Decimal(str(portfolio.cash_balance))
        if cash_balance < total_amount:
            raise ValidationError(
                f"Insufficient balance: {cash_balance:,.0f} KRW < {total_amount:,.0f} KRW"
            )

        # Update cash balance
        portfolio.cash_balance = cash_balance - total_amount

        # Get or create position
        position = (
            self.db.query(Position)
            .filter(Position.portfolio_id == portfolio.id, Position.stock_code == stock_code)
            .first()
        )

        if position:
            # Update existing position
            position.update_on_buy(quantity, price, trade_date, entry_reason, confidence_score)
        else:
            # Create new position
            position = Position(
                portfolio_id=portfolio.id,
                stock_code=stock_code,
                stock_name=stock_name,
                quantity=quantity,
                avg_entry_price=price,
                first_entry_date=trade_date,
                entry_reason=entry_reason,
                confidence_score=confidence_score,
            )
            self.db.add(position)

        # Create trade record
        trade = Trade.create_buy(
            portfolio_id=portfolio.id,
            trade_date=trade_date,
            stock_code=stock_code,
            stock_name=stock_name,
            quantity=quantity,
            price=price,
            reason=reason,
        )
        self.db.add(trade)

        return trade

    def _process_sell(
        self,
        portfolio: Portfolio,
        trade_date: date,
        stock_code: str,
        stock_name: str,
        quantity: int,
        price: Decimal,
        reason: Optional[str] = None,
    ) -> Trade:
        """Process a SELL trade."""
        # Get position
        position = (
            self.db.query(Position)
            .filter(Position.portfolio_id == portfolio.id, Position.stock_code == stock_code)
            .first()
        )

        if not position:
            raise ValidationError(f"No position found for {stock_code}")

        if position.quantity < quantity:
            raise ValidationError(
                f"Insufficient quantity: own {position.quantity} shares, trying to sell {quantity}"
            )

        # Calculate realized P&L
        avg_entry_price = position.update_on_sell(quantity)
        realized_pnl = (price - avg_entry_price) * quantity

        # Update cash balance
        total_amount = price * quantity
        portfolio.cash_balance = Decimal(str(portfolio.cash_balance)) + total_amount

        # Delete position if fully sold
        if position.quantity == 0:
            self.db.delete(position)

        # Create trade record
        trade = Trade.create_sell(
            portfolio_id=portfolio.id,
            trade_date=trade_date,
            stock_code=stock_code,
            stock_name=stock_name,
            quantity=quantity,
            price=price,
            realized_pnl=realized_pnl,
            reason=reason,
        )
        self.db.add(trade)

        return trade

    def delete_trade(self, trade_id: str, portfolio_id: str) -> bool:
        """Delete a trade and rollback its effects.

        Args:
            trade_id: Trade ID to delete
            portfolio_id: Portfolio ID (for authorization)

        Returns:
            True if deleted successfully

        Raises:
            NotFoundError: If trade not found
            ValidationError: If rollback not possible
        """
        trade = (
            self.db.query(Trade)
            .filter(Trade.id == trade_id, Trade.portfolio_id == portfolio_id)
            .first()
        )

        if not trade:
            raise NotFoundError("Trade not found")

        portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

        if trade.is_buy:
            self._rollback_buy(trade, portfolio)
        else:
            self._rollback_sell(trade, portfolio)

        self.db.delete(trade)
        self.db.commit()

        logger.info(f"Trade deleted and rolled back: {trade_id}")
        return True

    def _rollback_buy(self, trade: Trade, portfolio: Portfolio) -> None:
        """Rollback a BUY trade."""
        # Restore cash
        portfolio.cash_balance = Decimal(str(portfolio.cash_balance)) + Decimal(str(trade.total_amount))

        # Update or delete position
        position = (
            self.db.query(Position)
            .filter(Position.portfolio_id == portfolio.id, Position.stock_code == trade.stock_code)
            .first()
        )

        if position:
            if position.quantity <= trade.quantity:
                self.db.delete(position)
            else:
                # Recalculate average price (approximate - exact reversal is complex)
                position.quantity -= trade.quantity

    def _rollback_sell(self, trade: Trade, portfolio: Portfolio) -> None:
        """Rollback a SELL trade."""
        # Deduct cash
        portfolio.cash_balance = Decimal(str(portfolio.cash_balance)) - Decimal(str(trade.total_amount))

        # Restore position
        position = (
            self.db.query(Position)
            .filter(Position.portfolio_id == portfolio.id, Position.stock_code == trade.stock_code)
            .first()
        )

        if position:
            position.quantity += trade.quantity
        else:
            # Recreate position
            position = Position(
                portfolio_id=portfolio.id,
                stock_code=trade.stock_code,
                stock_name=trade.stock_name,
                quantity=trade.quantity,
                avg_entry_price=trade.price,  # Use sell price as approximation
                first_entry_date=trade.trade_date,
            )
            self.db.add(position)
