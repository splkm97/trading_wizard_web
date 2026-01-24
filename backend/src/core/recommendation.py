"""
Recommendation generation for daily trading wizard.
Adapted from trading_wizard_bundle for web application use.
"""

from dataclasses import dataclass

from src.core.signal_scanner import PositionInfo, StockSignal


@dataclass
class BuyRecommendation:
    """BUY recommendation with position sizing."""

    stock_code: str
    stock_name: str
    recommended_price: float
    quantity: int
    total_cost: float
    confidence_score: float
    reason: str
    indicators: dict[str, float]


@dataclass
class SellRecommendation:
    """SELL recommendation."""

    stock_code: str
    stock_name: str
    current_price: float
    quantity: int
    entry_price: float
    expected_pnl: float
    pnl_pct: float
    reason: str
    indicators: dict[str, float]


class RecommendationEngine:
    """Generates buy/sell recommendations with position sizing and risk management."""

    def __init__(
        self,
        max_positions: int = 15,
        max_position_percent: float = 10.0,
        confidence_threshold: int = 60,
    ):
        """
        Initialize recommendation engine.

        Args:
            max_positions: Maximum number of positions allowed
            max_position_percent: Maximum percentage of capital per position
            confidence_threshold: Minimum confidence score for recommendations
        """
        self.max_positions = max_positions
        self.max_position_percent = max_position_percent
        self.confidence_threshold = confidence_threshold

    def generate_buy_recommendations(
        self,
        signals: list[StockSignal],
        cash_balance: float,
        current_position_count: int,
    ) -> list[BuyRecommendation]:
        """
        Generate BUY recommendations with position sizing.

        Args:
            signals: List of BUY signals from scanner
            cash_balance: Available cash
            current_position_count: Number of existing positions

        Returns:
            List of BuyRecommendation objects
        """
        recommendations = []
        available_slots = self.max_positions - current_position_count

        if available_slots <= 0:
            return []

        remaining_cash = cash_balance

        for signal in signals[:available_slots]:
            if signal.confidence_score < self.confidence_threshold:
                continue

            # Position sizing: max X% of total capital per position
            max_allocation = cash_balance * (self.max_position_percent / 100)

            # Calculate max shares we can buy
            max_shares = int(max_allocation / signal.current_price)
            if max_shares < 1:
                continue

            total_cost = signal.current_price * max_shares

            # Check if we have enough cash
            if total_cost > remaining_cash:
                max_shares = int(remaining_cash / signal.current_price)
                total_cost = signal.current_price * max_shares

            if max_shares < 1:
                continue

            recommendations.append(
                BuyRecommendation(
                    stock_code=signal.stock_code,
                    stock_name=signal.stock_name,
                    recommended_price=signal.current_price,
                    quantity=max_shares,
                    total_cost=total_cost,
                    confidence_score=signal.confidence_score,
                    reason=signal.reason,
                    indicators=signal.indicators,
                )
            )

            # Update remaining cash for next recommendation
            remaining_cash -= total_cost

        return recommendations

    def generate_sell_recommendations(
        self,
        signals: list[StockSignal],
        positions: list[PositionInfo],
    ) -> list[SellRecommendation]:
        """
        Generate SELL recommendations.

        Args:
            signals: List of SELL signals from scanner
            positions: Current positions

        Returns:
            List of SellRecommendation objects
        """
        recommendations = []
        position_map = {p.stock_code: p for p in positions}

        for signal in signals:
            pos = position_map.get(signal.stock_code)
            if pos is None:
                continue

            pnl = (signal.current_price - pos.entry_price) * pos.quantity
            pnl_pct = ((signal.current_price - pos.entry_price) / pos.entry_price) * 100

            recommendations.append(
                SellRecommendation(
                    stock_code=signal.stock_code,
                    stock_name=signal.stock_name,
                    current_price=signal.current_price,
                    quantity=pos.quantity,
                    entry_price=pos.entry_price,
                    expected_pnl=pnl,
                    pnl_pct=pnl_pct,
                    reason=signal.reason,
                    indicators=signal.indicators,
                )
            )

        return recommendations
