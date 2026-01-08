"""
Recommendation generation for daily wizard.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from src.wizard.signal_scanner import StockSignal


@dataclass
class BuyRecommendation:
    """BUY recommendation with position sizing."""

    stock_code: str
    stock_name: str
    recommended_price: float
    quantity: int
    total_cost: float
    confidence_score: int
    reason: str
    indicators: Dict[str, float]

    def to_dict(self) -> dict:
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "recommended_price": self.recommended_price,
            "quantity": self.quantity,
            "total_cost": self.total_cost,
            "confidence_score": self.confidence_score,
            "reason": self.reason,
            "indicators": self.indicators,
        }


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
    indicators: Dict[str, float]

    def to_dict(self) -> dict:
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "current_price": self.current_price,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "expected_pnl": self.expected_pnl,
            "pnl_pct": self.pnl_pct,
            "reason": self.reason,
            "indicators": self.indicators,
        }


class RecommendationEngine:
    """Generates buy/sell recommendations with position sizing."""

    def __init__(
        self,
        max_positions: int = 15,
        max_position_percent: float = 10.0,
        confidence_threshold: int = 60,
    ):
        self.max_positions = max_positions
        self.max_position_percent = max_position_percent
        self.confidence_threshold = confidence_threshold

    def generate_buy_recommendations(
        self,
        signals: List[StockSignal],
        available_cash: float,
        current_position_count: int = 0,
        initial_capital: float = 1_000_000,
    ) -> List[BuyRecommendation]:
        """Generate BUY recommendations with position sizing."""
        recommendations = []
        available_slots = self.max_positions - current_position_count

        if available_slots <= 0:
            return []

        remaining_cash = available_cash

        for signal in signals[:available_slots]:
            if signal.confidence_score < self.confidence_threshold:
                continue

            # Position sizing: max 10% of INITIAL capital per position (consistent sizing)
            max_allocation = initial_capital * (self.max_position_percent / 100)
            max_shares = int(max_allocation / signal.current_price)

            # Allow at least 1 share if affordable and within 15% of capital
            if max_shares < 1:
                if signal.current_price <= initial_capital * 0.15:
                    max_shares = 1
                else:
                    continue

            total_cost = signal.current_price * max_shares

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

            remaining_cash -= total_cost

        return recommendations


def format_buy_reason_detail(rec: BuyRecommendation) -> str:
    """Generate detailed explanation for BUY recommendation."""
    ind = rec.indicators

    volume_pass = ind.get("volume_ratio", 0) >= 1.5
    rsi_pass = 30 <= ind.get("rsi", 50) <= 70
    macd_pass = ind.get("macd_histogram", 0) > 0

    lines = []
    lines.append(f"[매수 추천] {rec.stock_code} ({rec.stock_name})")
    lines.append("")
    lines.append("1. 볼린저 밴드 상단 돌파 (Squeeze Breakout)")
    lines.append(f"   - 현재가 {rec.recommended_price:,.0f}원이 상단밴드 {ind.get('bb_upper', 0):,.0f}원을 돌파")
    lines.append(f"   - 밴드폭: {ind.get('bb_width', 0):.2f}% (변동성 확대 중)")
    lines.append("")
    lines.append("2. 보조지표 분석")
    lines.append(f"   - RSI({ind.get('rsi', 0):.1f}): {'중립구간' if rsi_pass else '과매수/과매도 구간'}")
    lines.append(f"   - MACD({ind.get('macd_histogram', 0):.2f}): {'상승추세' if macd_pass else '하락추세'}")
    lines.append(f"   - 거래량({ind.get('volume_ratio', 0):.1f}x): {'평균 대비 급증' if volume_pass else '평균 수준'}")
    lines.append("")
    lines.append(f"3. 신뢰도 점수: {rec.confidence_score}/100")

    return "\n".join(lines)
