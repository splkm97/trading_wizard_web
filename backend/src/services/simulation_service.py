"""Simulation game service for Turn-Based Trading Simulation."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from src.models.game_session import (
    GameSession,
    GameStatus,
    SimulatedPosition,
    SimulatedTrade,
    RecommendationCache,
)
from src.core.indicators import calculate_all_indicators, calculate_confidence_score
from src.services.stock_service import stock_service
from src.wizard.signal_scanner import load_kospi_top100

if TYPE_CHECKING:
    from src.models.user import User


class InsufficientFundsError(Exception):
    def __init__(self, required: Decimal, available: Decimal):
        self.required = required
        self.available = available
        super().__init__(f"Insufficient funds: required {required}, available {available}")


class DuplicateBuyError(Exception):
    def __init__(self, stock_code: str):
        self.stock_code = stock_code
        super().__init__(f"Already own position in {stock_code}. Use Sell/Hold instead.")


class InvalidDateRangeError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class GameNotFoundError(Exception):
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Game session not found: {session_id}")


class SimulationService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        initial_capital: Decimal = Decimal("100000000"),
        name: Optional[str] = None,
    ) -> GameSession:
        today = date.today()

        if start_date >= end_date:
            raise InvalidDateRangeError("시작일은 종료일보다 이전이어야 합니다")

        if end_date > today:
            raise InvalidDateRangeError("종료일은 오늘 이전이어야 합니다")

        min_date = date(2015, 1, 1)
        if start_date < min_date:
            raise InvalidDateRangeError(f"시작일은 {min_date} 이후여야 합니다")

        min_duration = timedelta(days=7)
        if (end_date - start_date) < min_duration:
            raise InvalidDateRangeError("시뮬레이션 기간은 최소 7일 이상이어야 합니다")

        session = GameSession(
            user_id=user_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            current_date=start_date,
            initial_capital=initial_capital,
            cash_balance=initial_capital,
            status=GameStatus.IN_PROGRESS,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str, user_id: str) -> GameSession:
        session = (
            self.db.query(GameSession)
            .filter(GameSession.id == session_id, GameSession.user_id == user_id)
            .first()
        )
        if not session:
            raise GameNotFoundError(session_id)
        return session

    def list_sessions(
        self,
        user_id: str,
        status: Optional[GameStatus] = None,
    ) -> list[GameSession]:
        query = self.db.query(GameSession).filter(GameSession.user_id == user_id)
        if status:
            query = query.filter(GameSession.status == status)
        return query.order_by(GameSession.created_at.desc()).all()

    def delete_session(self, session_id: str, user_id: str) -> None:
        session = self.get_session(session_id, user_id)
        self.db.delete(session)
        self.db.commit()

    def _fetch_historical_data(
        self,
        stock_code: str,
        end_date: date,
        days: int = 90,
    ) -> Optional[pd.DataFrame]:
        """Fetch historical OHLCV data ending at specific date."""
        start_date = end_date - timedelta(days=days + 30)

        ticker = f"{stock_code}.KS"
        try:
            df = yf.download(
                ticker,
                start=start_date.isoformat(),
                end=(end_date + timedelta(days=1)).isoformat(),
                progress=False,
                auto_adjust=False,
            )

            if df.empty:
                ticker = f"{stock_code}.KQ"
                df = yf.download(
                    ticker,
                    start=start_date.isoformat(),
                    end=(end_date + timedelta(days=1)).isoformat(),
                    progress=False,
                    auto_adjust=False,
                )

            if df.empty or len(df) < 30:
                return None

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()

            df.index = pd.to_datetime(df.index).date
            df = df[df.index <= end_date]

            return df

        except Exception:
            return None

    def _get_owned_stock_codes(self, session: GameSession) -> set[str]:
        """Get set of stock codes currently owned in the session."""
        positions = (
            self.db.query(SimulatedPosition)
            .filter(SimulatedPosition.session_id == session.id)
            .all()
        )
        return {p.stock_code for p in positions}

    def get_recommendations(
        self,
        session: GameSession,
        min_score: int = 50,
        force_refresh: bool = False,
    ) -> list[dict]:
        """Get stock recommendations for current turn. Uses cache if available."""
        import json

        owned_codes = self._get_owned_stock_codes(session)

        if (
            not force_refresh
            and session.cached_recommendations
            and session.cached_recommendations_date == session.current_date
        ):
            cached = json.loads(session.cached_recommendations)
            for rec in cached:
                rec["is_owned"] = rec["stock_code"] in owned_codes
            return cached

        cache_entry = (
            self.db.query(RecommendationCache)
            .filter(
                RecommendationCache.session_id == session.id,
                RecommendationCache.target_date == session.current_date,
            )
            .first()
        )
        if cache_entry and not force_refresh:
            cached = json.loads(cache_entry.recommendations_json)
            session.cached_recommendations = cache_entry.recommendations_json
            session.cached_recommendations_date = session.current_date
            self.db.commit()
            for rec in cached:
                rec["is_owned"] = rec["stock_code"] in owned_codes
            return cached

        recommendations = self._compute_recommendations(session, min_score)

        session.cached_recommendations = json.dumps(recommendations)
        session.cached_recommendations_date = session.current_date
        self.db.commit()

        for rec in recommendations:
            rec["is_owned"] = rec["stock_code"] in owned_codes

        return recommendations

    def _compute_recommendations(
        self,
        session: GameSession,
        min_score: int = 50,
    ) -> list[dict]:
        """Compute fresh recommendations (expensive operation)."""
        recommendations = []

        try:
            stock_codes = load_kospi_top100()
        except FileNotFoundError:
            stock_codes = []

        for stock_code in stock_codes:
            df = self._fetch_historical_data(stock_code, session.current_date)
            if df is None or len(df) < 35:
                continue

            df = calculate_all_indicators(df)
            latest = df.iloc[-1]

            if pd.isna(latest["BB_Upper"]) or pd.isna(latest["RSI"]):
                continue

            price_breakout = latest["Close"] > latest["BB_Upper"]
            was_in_squeeze = df["In_Squeeze"].iloc[-5:-1].any()
            bandwidth_expanding = latest["BB_Width"] > df["BB_Width"].iloc[-2]

            if price_breakout and (was_in_squeeze or bandwidth_expanding):
                confidence = calculate_confidence_score(
                    volume_ratio=float(latest["Volume_Ratio"]),
                    rsi=float(latest["RSI"]),
                    macd_histogram=float(latest["MACD_Histogram"]),
                    macd_signal=float(latest["MACD_Signal"]),
                )

                if confidence >= min_score:
                    stock_name = stock_service.get_stock_name_or_default(stock_code, stock_code)

                    recommendations.append(
                        {
                            "stock_code": stock_code,
                            "stock_name": stock_name,
                            "confidence_score": round(confidence, 2),
                            "is_owned": False,
                            "current_price": float(latest["Close"]),
                            "bollinger_score": 25.0,
                            "rsi_score": self._calc_rsi_score(float(latest["RSI"])),
                            "macd_score": self._calc_macd_score(
                                float(latest["MACD_Histogram"]),
                                float(latest["MACD_Signal"]),
                            ),
                            "volume_score": self._calc_volume_score(float(latest["Volume_Ratio"])),
                        }
                    )

        recommendations.sort(key=lambda x: x["confidence_score"], reverse=True)
        return recommendations[:20]

    def _calc_rsi_score(self, rsi: float) -> float:
        if 30 <= rsi <= 70:
            distance = abs(rsi - 50)
            return round(20.0 * (1 - distance / 20.0), 2)
        return 0.0

    def _calc_macd_score(self, histogram: float, signal: float) -> float:
        if histogram > 0:
            signal_abs = abs(signal) if signal != 0 else 0.001
            ratio = min(histogram / signal_abs, 1.0)
            return round(30.0 * ratio, 2)
        return 0.0

    def _calc_volume_score(self, volume_ratio: float) -> float:
        if volume_ratio > 1.0:
            return round(min(25.0, (volume_ratio - 1.0) * 25.0), 2)
        return 0.0

    def get_stock_detail(
        self,
        session: GameSession,
        stock_code: str,
    ) -> dict:
        """Get detailed stock information for analysis. (T016)"""
        df = self._fetch_historical_data(stock_code, session.current_date, days=90)
        if df is None or len(df) < 35:
            raise ValueError(f"Insufficient data for {stock_code}")

        df = calculate_all_indicators(df)
        latest = df.iloc[-1]

        stock_name = stock_service.get_stock_name_or_default(stock_code, stock_code)

        position = (
            self.db.query(SimulatedPosition)
            .filter(
                SimulatedPosition.session_id == session.id,
                SimulatedPosition.stock_code == stock_code,
            )
            .first()
        )

        is_owned = position is not None
        owned_quantity = position.quantity if position else None
        avg_entry_price = float(position.avg_entry_price) if position else None

        current_price = float(latest["Close"])
        unrealized_pnl = None
        unrealized_pnl_pct = None

        if position:
            cost_basis = float(position.avg_entry_price) * position.quantity
            current_value = current_price * position.quantity
            unrealized_pnl = current_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0

        confidence = 0.0
        if latest["Close"] > latest["BB_Upper"]:
            confidence = calculate_confidence_score(
                volume_ratio=float(latest["Volume_Ratio"]),
                rsi=float(latest["RSI"]),
                macd_histogram=float(latest["MACD_Histogram"]),
                macd_signal=float(latest["MACD_Signal"]),
            )

        price_history = []
        for idx in df.tail(60).index:
            row = df.loc[idx]
            price_history.append(
                {
                    "date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                }
            )

        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "current_price": current_price,
            "confidence_score": round(confidence, 2),
            "is_owned": is_owned,
            "owned_quantity": owned_quantity,
            "avg_entry_price": avg_entry_price,
            "unrealized_pnl": round(unrealized_pnl, 2) if unrealized_pnl else None,
            "unrealized_pnl_pct": round(unrealized_pnl_pct, 2) if unrealized_pnl_pct else None,
            "indicators": {
                "bollinger": {
                    "upper": float(latest["BB_Upper"]),
                    "middle": float(latest["BB_Middle"]),
                    "lower": float(latest["BB_Lower"]),
                    "bandwidth": float(latest["BB_Width"]),
                    "score": 25.0 if latest["Close"] > latest["BB_Upper"] else 0.0,
                },
                "rsi": {
                    "value": float(latest["RSI"]),
                    "score": self._calc_rsi_score(float(latest["RSI"])),
                },
                "macd": {
                    "macd": float(latest["MACD"]),
                    "signal": float(latest["MACD_Signal"]),
                    "histogram": float(latest["MACD_Histogram"]),
                    "score": self._calc_macd_score(
                        float(latest["MACD_Histogram"]),
                        float(latest["MACD_Signal"]),
                    ),
                },
                "volume": {
                    "current": int(latest["Volume"]),
                    "average": int(latest["Volume_MA"]),
                    "ratio": float(latest["Volume_Ratio"]),
                    "score": self._calc_volume_score(float(latest["Volume_Ratio"])),
                },
            },
            "price_history": price_history,
        }

    def get_price_at_date(self, stock_code: str, target_date: date) -> Optional[float]:
        """Get closing price for a stock at a specific date."""
        df = self._fetch_historical_data(stock_code, target_date, days=10)
        if df is None or len(df) == 0:
            return None
        return float(df.iloc[-1]["Close"])

    def execute_buy(
        self,
        session: GameSession,
        stock_code: str,
        stock_name: str,
        quantity: int,
        price: Decimal,
        confidence_score: Optional[Decimal] = None,
    ) -> SimulatedTrade:
        existing_position = (
            self.db.query(SimulatedPosition)
            .filter(
                SimulatedPosition.session_id == session.id,
                SimulatedPosition.stock_code == stock_code,
            )
            .first()
        )
        if existing_position:
            raise DuplicateBuyError(stock_code)

        total_cost = price * quantity
        if total_cost > session.cash_balance:
            raise InsufficientFundsError(total_cost, Decimal(str(session.cash_balance)))

        trade = SimulatedTrade.create_buy(
            session_id=session.id,
            trade_date=session.current_date,
            stock_code=stock_code,
            stock_name=stock_name,
            quantity=quantity,
            price=price,
            confidence_score=confidence_score,
        )
        self.db.add(trade)

        position = SimulatedPosition(
            session_id=session.id,
            stock_code=stock_code,
            stock_name=stock_name,
            quantity=quantity,
            avg_entry_price=price,
            entry_date=session.current_date,
        )
        self.db.add(position)

        session.cash_balance = Decimal(str(session.cash_balance)) - total_cost
        self.db.commit()
        self.db.refresh(trade)
        return trade

    def execute_sell(
        self,
        session: GameSession,
        stock_code: str,
        price: Decimal,
    ) -> SimulatedTrade:
        position = (
            self.db.query(SimulatedPosition)
            .filter(
                SimulatedPosition.session_id == session.id,
                SimulatedPosition.stock_code == stock_code,
            )
            .first()
        )
        if not position:
            raise ValueError(f"No position found for {stock_code}")

        trade = SimulatedTrade.create_sell(
            session_id=session.id,
            trade_date=session.current_date,
            stock_code=stock_code,
            stock_name=position.stock_name,
            quantity=position.quantity,
            price=price,
            avg_entry_price=Decimal(str(position.avg_entry_price)),
        )
        self.db.add(trade)

        total_proceeds = price * position.quantity
        session.cash_balance = Decimal(str(session.cash_balance)) + total_proceeds

        self.db.delete(position)
        self.db.commit()
        self.db.refresh(trade)
        return trade

    def advance_turn(self, session: GameSession) -> GameSession:
        next_date = self._get_next_trading_day(session.current_date)

        if next_date >= session.end_date:
            session.current_date = session.end_date
            session.status = GameStatus.COMPLETED
        else:
            session.current_date = next_date

        session.cached_recommendations = None
        session.cached_recommendations_date = None

        self.db.commit()
        self.db.refresh(session)
        return session

    def _get_next_trading_day(self, current: date) -> date:
        next_day = current + timedelta(days=1)
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        return next_day

    def _get_next_n_trading_days(self, start: date, n: int) -> list[date]:
        """Get next N trading days after start date."""
        days = []
        current = start
        for _ in range(n):
            current = self._get_next_trading_day(current)
            days.append(current)
        return days

    def precompute_recommendations(
        self,
        session: GameSession,
        days_ahead: int = 3,
        min_score: int = 50,
    ) -> int:
        """Pre-compute recommendations for next N trading days. Returns count of days computed."""
        import json

        future_dates = self._get_next_n_trading_days(session.current_date, days_ahead)
        future_dates = [d for d in future_dates if d <= session.end_date]

        computed_count = 0
        for target_date in future_dates:
            existing = (
                self.db.query(RecommendationCache)
                .filter(
                    RecommendationCache.session_id == session.id,
                    RecommendationCache.target_date == target_date,
                )
                .first()
            )
            if existing:
                continue

            recommendations = self._compute_recommendations_for_date(
                session, target_date, min_score
            )

            cache_entry = RecommendationCache(
                session_id=session.id,
                target_date=target_date,
                recommendations_json=json.dumps(recommendations),
            )
            self.db.add(cache_entry)
            computed_count += 1

        if computed_count > 0:
            self.db.commit()

        return computed_count

    def _compute_recommendations_for_date(
        self,
        session: GameSession,
        target_date: date,
        min_score: int = 50,
    ) -> list[dict]:
        """Compute recommendations for a specific date (not current_date)."""
        recommendations = []

        try:
            stock_codes = load_kospi_top100()
        except FileNotFoundError:
            stock_codes = []

        for stock_code in stock_codes:
            df = self._fetch_historical_data(stock_code, target_date)
            if df is None or len(df) < 35:
                continue

            df = calculate_all_indicators(df)
            latest = df.iloc[-1]

            if pd.isna(latest["BB_Upper"]) or pd.isna(latest["RSI"]):
                continue

            price_breakout = latest["Close"] > latest["BB_Upper"]
            was_in_squeeze = df["In_Squeeze"].iloc[-5:-1].any()
            bandwidth_expanding = latest["BB_Width"] > df["BB_Width"].iloc[-2]

            if price_breakout and (was_in_squeeze or bandwidth_expanding):
                confidence = calculate_confidence_score(
                    volume_ratio=float(latest["Volume_Ratio"]),
                    rsi=float(latest["RSI"]),
                    macd_histogram=float(latest["MACD_Histogram"]),
                    macd_signal=float(latest["MACD_Signal"]),
                )

                if confidence >= min_score:
                    stock_name = stock_service.get_stock_name_or_default(stock_code, stock_code)

                    recommendations.append(
                        {
                            "stock_code": stock_code,
                            "stock_name": stock_name,
                            "confidence_score": round(confidence, 2),
                            "is_owned": False,
                            "current_price": float(latest["Close"]),
                            "bollinger_score": 25.0,
                            "rsi_score": self._calc_rsi_score(float(latest["RSI"])),
                            "macd_score": self._calc_macd_score(
                                float(latest["MACD_Histogram"]),
                                float(latest["MACD_Signal"]),
                            ),
                            "volume_score": self._calc_volume_score(float(latest["Volume_Ratio"])),
                        }
                    )

        recommendations.sort(key=lambda x: x["confidence_score"], reverse=True)
        return recommendations[:20]

    def calculate_portfolio_summary(self, session: GameSession) -> dict:
        """Calculate portfolio summary with current valuations."""
        positions = (
            self.db.query(SimulatedPosition)
            .filter(SimulatedPosition.session_id == session.id)
            .all()
        )

        total_positions_value = Decimal("0")
        unrealized_pnl = Decimal("0")
        position_details = []

        for pos in positions:
            current_price = self.get_price_at_date(pos.stock_code, session.current_date)
            if current_price is None:
                current_price = float(pos.avg_entry_price)

            current_value = Decimal(str(current_price)) * pos.quantity
            cost_basis = Decimal(str(pos.avg_entry_price)) * pos.quantity
            pos_pnl = current_value - cost_basis
            pos_pnl_pct = (pos_pnl / cost_basis * 100) if cost_basis > 0 else Decimal("0")

            total_positions_value += current_value
            unrealized_pnl += pos_pnl

            position_details.append(
                {
                    "id": pos.id,
                    "stock_code": pos.stock_code,
                    "stock_name": pos.stock_name,
                    "quantity": pos.quantity,
                    "avg_entry_price": float(pos.avg_entry_price),
                    "entry_date": pos.entry_date.isoformat(),
                    "current_price": current_price,
                    "current_value": float(current_value),
                    "unrealized_pnl": float(pos_pnl),
                    "unrealized_pnl_pct": float(pos_pnl_pct),
                }
            )

        total_value = Decimal(str(session.cash_balance)) + total_positions_value
        total_return = total_value - Decimal(str(session.initial_capital))
        total_return_pct = total_return / Decimal(str(session.initial_capital)) * 100

        return {
            "id": session.id,
            "name": session.name,
            "start_date": session.start_date.isoformat(),
            "end_date": session.end_date.isoformat(),
            "current_date": session.current_date.isoformat(),
            "initial_capital": float(session.initial_capital),
            "cash_balance": float(session.cash_balance),
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "positions": position_details,
            "total_positions_value": float(total_positions_value),
            "total_value": float(total_value),
            "total_return": float(total_return),
            "total_return_pct": float(total_return_pct),
            "unrealized_pnl": float(unrealized_pnl),
            "is_game_over": session.is_game_over,
        }

    def generate_report(self, session: GameSession) -> dict:
        trades = (
            self.db.query(SimulatedTrade)
            .filter(SimulatedTrade.session_id == session.id)
            .order_by(SimulatedTrade.trade_date)
            .all()
        )

        sell_trades = [t for t in trades if t.action.value == "SELL"]
        winning_trades = [t for t in sell_trades if t.realized_pnl and t.realized_pnl > 0]

        total_trades = len(sell_trades)
        winning_count = len(winning_trades)
        win_rate = (winning_count / total_trades * 100) if total_trades > 0 else 0

        total_profit = sum(
            float(t.realized_pnl) for t in sell_trades if t.realized_pnl and t.realized_pnl > 0
        )
        total_loss = abs(
            sum(float(t.realized_pnl) for t in sell_trades if t.realized_pnl and t.realized_pnl < 0)
        )
        profit_factor = (total_profit / total_loss) if total_loss > 0 else None

        equity_curve = self._calculate_equity_curve(session, trades)
        max_drawdown = self._calculate_mdd(equity_curve)

        stock_contributions = self._calculate_stock_contributions(sell_trades)

        summary = self.calculate_portfolio_summary(session)

        return {
            "session_id": session.id,
            "start_date": session.start_date.isoformat(),
            "end_date": session.end_date.isoformat(),
            "current_date": session.current_date.isoformat(),
            "initial_capital": float(session.initial_capital),
            "current_value": summary["total_value"],
            "total_return_pct": summary["total_return_pct"],
            "max_drawdown_pct": max_drawdown,
            "total_trades": total_trades,
            "winning_trades": winning_count,
            "win_rate_pct": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor else None,
            "equity_curve": equity_curve,
            "stock_contributions": stock_contributions,
        }

    def _calculate_equity_curve(
        self, session: GameSession, trades: list[SimulatedTrade]
    ) -> list[dict]:
        curve = [{"date": session.start_date.isoformat(), "value": float(session.initial_capital)}]

        current_cash = Decimal(str(session.initial_capital))
        positions: dict[str, dict] = {}
        current_date = session.start_date

        trade_by_date: dict[date, list[SimulatedTrade]] = {}
        for t in trades:
            if t.trade_date not in trade_by_date:
                trade_by_date[t.trade_date] = []
            trade_by_date[t.trade_date].append(t)

        while current_date <= session.current_date:
            if current_date in trade_by_date:
                for trade in trade_by_date[current_date]:
                    if trade.action.value == "BUY":
                        current_cash -= trade.total_amount
                        positions[trade.stock_code] = {
                            "quantity": trade.quantity,
                            "price": trade.price,
                        }
                    else:
                        current_cash += trade.total_amount
                        if trade.stock_code in positions:
                            del positions[trade.stock_code]

            positions_value = Decimal("0")
            for stock_code, pos in positions.items():
                price = self.get_price_at_date(stock_code, current_date)
                if price:
                    positions_value += Decimal(str(price)) * pos["quantity"]
                else:
                    positions_value += Decimal(str(pos["price"])) * pos["quantity"]

            total_value = current_cash + positions_value

            if current_date != session.start_date:
                curve.append({"date": current_date.isoformat(), "value": float(total_value)})

            current_date = self._get_next_trading_day(current_date)

        return curve

    def _calculate_mdd(self, equity_curve: list[dict]) -> float:
        if not equity_curve:
            return 0.0

        values = [p["value"] for p in equity_curve]
        peak = values[0]
        max_dd = 0.0

        for value in values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100 if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        return round(max_dd, 2)

    def _calculate_stock_contributions(self, sell_trades: list[SimulatedTrade]) -> list[dict]:
        stock_pnl: dict[str, dict] = {}

        for trade in sell_trades:
            code = trade.stock_code
            if code not in stock_pnl:
                stock_pnl[code] = {
                    "stock_code": code,
                    "stock_name": trade.stock_name,
                    "total_trades": 0,
                    "realized_pnl": 0.0,
                }
            stock_pnl[code]["total_trades"] += 1
            stock_pnl[code]["realized_pnl"] += (
                float(trade.realized_pnl) if trade.realized_pnl else 0
            )

        total_pnl = sum(abs(s["realized_pnl"]) for s in stock_pnl.values())

        contributions = []
        for data in stock_pnl.values():
            contribution_pct = (abs(data["realized_pnl"]) / total_pnl * 100) if total_pnl > 0 else 0
            contributions.append(
                {
                    "stock_code": data["stock_code"],
                    "stock_name": data["stock_name"],
                    "total_trades": data["total_trades"],
                    "realized_pnl": round(data["realized_pnl"], 2),
                    "contribution_pct": round(contribution_pct, 2),
                }
            )

        return sorted(contributions, key=lambda x: abs(x["realized_pnl"]), reverse=True)

    def export_trades(self, session: GameSession) -> dict:
        trades = (
            self.db.query(SimulatedTrade)
            .filter(SimulatedTrade.session_id == session.id)
            .order_by(SimulatedTrade.trade_date)
            .all()
        )

        report = self.generate_report(session)

        trade_list = []
        for trade in trades:
            trade_list.append(
                {
                    "date": trade.trade_date.isoformat(),
                    "stock_code": trade.stock_code,
                    "stock_name": trade.stock_name,
                    "action": trade.action.value,
                    "price": float(trade.price),
                    "quantity": trade.quantity,
                    "pnl": float(trade.realized_pnl) if trade.realized_pnl else None,
                    "pnl_pct": float(trade.realized_pnl_pct) if trade.realized_pnl_pct else None,
                }
            )

        daily_values = [[p["date"], p["value"]] for p in report["equity_curve"]]

        return {
            "start_date": session.start_date.isoformat(),
            "end_date": session.end_date.isoformat(),
            "initial_capital": float(session.initial_capital),
            "final_value": report["current_value"],
            "total_return_pct": report["total_return_pct"],
            "max_drawdown_pct": report["max_drawdown_pct"],
            "total_trades": report["total_trades"],
            "winning_trades": report["winning_trades"],
            "win_rate_pct": report["win_rate_pct"],
            "trades": trade_list,
            "daily_values": daily_values,
        }
