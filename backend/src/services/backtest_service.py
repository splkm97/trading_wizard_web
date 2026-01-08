"""Backtest execution service.

Runs backtests using the Bollinger Band Squeeze strategy,
reading parameters from UserSettings.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from src.core.indicators import calculate_all_indicators, calculate_confidence_score
from src.models.backtest import BacktestResult
from src.models.user_settings import UserSettings
from src.services.stock_service import stock_service
from src.core.logging import logger


@dataclass
class Position:
    """Backtest position."""

    stock_code: str
    stock_name: str
    quantity: int
    entry_price: float
    entry_date: str
    partial_take_profit_executed: bool = False


@dataclass
class Trade:
    """Backtest trade record."""

    date: str
    stock_code: str
    stock_name: str
    action: str
    price: float
    quantity: int
    reason: str
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None


@dataclass
class BacktestState:
    """Backtest simulation state."""

    initial_capital: float
    cash: float
    positions: dict[str, Position] = field(default_factory=dict)
    trades: list[Trade] = field(default_factory=list)
    daily_values: list[tuple[str, float]] = field(default_factory=list)


class BacktestService:
    """Service for running backtests."""

    def __init__(
        self,
        db: Session,
        max_positions: int = 15,
        max_position_pct: float = 10.0,
        stop_loss_pct: float = 4.5,
        confidence_threshold: int = 55,
        take_profit_enabled: bool = True,
        take_profit_pct: float = 12.0,
        take_profit_ratio: float = 1.0,
        sell_on_middle_band: bool = False,
        bollinger_period: int = 15,
        bollinger_std_dev: float = 1.5,
        squeeze_threshold_pct: int = 60,
        squeeze_lookback_days: int = 10,
        expansion_threshold_pct: float = 20.0,
        band_touch_tolerance: float = 0.001,
        trading_days_per_year: int = 252,
        days_per_year: int = 365,
    ):
        """Initialize backtest service with strategy parameters."""
        self.db = db
        # Risk Management
        self.max_positions = max_positions
        self.max_position_pct = max_position_pct
        self.stop_loss_pct = stop_loss_pct
        self.confidence_threshold = confidence_threshold
        # Take Profit Settings
        self.take_profit_enabled = take_profit_enabled
        self.take_profit_pct = take_profit_pct
        self.take_profit_ratio = take_profit_ratio
        self.sell_on_middle_band = sell_on_middle_band
        self.bollinger_period = bollinger_period
        self.bollinger_std_dev = bollinger_std_dev
        # Squeeze Detection
        self.squeeze_threshold_pct = squeeze_threshold_pct
        self.squeeze_lookback_days = squeeze_lookback_days
        # Advanced Squeeze Settings
        self.expansion_threshold_pct = expansion_threshold_pct
        self.band_touch_tolerance = band_touch_tolerance
        # Metrics Configuration
        self.trading_days_per_year = trading_days_per_year
        self.days_per_year = days_per_year

    @classmethod
    def from_user_settings(cls, db: Session, user_id: str) -> BacktestService:
        """Create service with user's settings."""
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if settings:
            return cls(
                db=db,
                # Risk Management
                max_positions=settings.max_positions,
                max_position_pct=float(settings.max_position_pct),
                stop_loss_pct=float(settings.stop_loss_pct),
                confidence_threshold=settings.confidence_threshold,
                # Take Profit Settings
                take_profit_enabled=settings.take_profit_enabled,
                take_profit_pct=float(settings.take_profit_pct),
                take_profit_ratio=float(settings.take_profit_ratio),
                sell_on_middle_band=settings.sell_on_middle_band,
                bollinger_period=settings.bollinger_period,
                bollinger_std_dev=float(settings.bollinger_std_dev),
                # Squeeze Detection
                squeeze_threshold_pct=settings.squeeze_threshold_pct,
                squeeze_lookback_days=settings.squeeze_lookback_days,
                # Advanced Squeeze Settings
                expansion_threshold_pct=float(settings.expansion_threshold_pct),
                band_touch_tolerance=float(settings.band_touch_tolerance),
                # Metrics Configuration
                trading_days_per_year=settings.trading_days_per_year,
                days_per_year=settings.days_per_year,
            )
        return cls(db=db)

    def run_backtest(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        stock_list_name: str,
        initial_capital: float = 1_000_000,
        name: Optional[str] = None,
        progress_callback=None,
    ) -> BacktestResult:
        """
        Run a backtest simulation.

        Args:
            user_id: User ID to save result for
            start_date: Backtest start date
            end_date: Backtest end date
            stock_list_name: Stock list filename (e.g., kospi_top100_2025jan)
            initial_capital: Starting capital in KRW
            name: Optional name for this backtest
            progress_callback: Optional callback(step, total_steps, message)

        Returns:
            BacktestResult model
        """
        logger.info(f"Starting backtest: {start_date} to {end_date}")

        # Load stock list
        stock_codes = self._load_stock_list(stock_list_name, user_id)
        stock_names = stock_service.get_all_stock_names()

        # Fetch data
        if progress_callback:
            progress_callback(1, 5, "데이터 수집 중...")

        all_data = self._fetch_all_data(stock_codes, start_date, end_date)

        if progress_callback:
            progress_callback(2, 5, "지표 계산 중...")

        # Calculate indicators
        for code in all_data:
            all_data[code] = calculate_all_indicators(all_data[code])

        if progress_callback:
            progress_callback(3, 5, "시뮬레이션 실행 중...")

        # Run simulation
        state = self._run_simulation(
            all_data=all_data,
            stock_names=stock_names,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
        )

        if progress_callback:
            progress_callback(4, 5, "결과 분석 중...")

        # Analyze results
        metrics = self._analyze_performance(state)

        # Create result
        result = BacktestResult(
            user_id=user_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            stock_list_name=stock_list_name,
            initial_capital=Decimal(str(initial_capital)),
            final_value=Decimal(str(metrics["final_value"])),
            total_return_pct=Decimal(str(metrics["total_return_pct"])),
            max_drawdown_pct=Decimal(str(metrics["max_drawdown"])),
            total_trades=metrics["total_trades"],
            winning_trades=metrics["winning_trades"],
            win_rate_pct=Decimal(str(metrics["win_rate"])),
            result_json=json.dumps(self._build_result_json(state, metrics), ensure_ascii=False),
        )

        self.db.add(result)
        self.db.commit()

        if progress_callback:
            progress_callback(5, 5, "완료!")

        logger.info(f"Backtest completed: {metrics['total_return_pct']:.2f}% return")
        return result

    def _load_stock_list(self, stock_list_name: str, user_id: str) -> list[str]:
        """Load stock list from database or file.

        First checks if stock_list_name is a custom list ID or name,
        then falls back to file-based lists.
        """
        from src.models.stock_list import StockList

        # Try to load from database first (by ID or name)
        from sqlalchemy import or_

        stock_list = (
            self.db.query(StockList)
            .filter(
                or_(StockList.user_id == user_id, StockList.is_default == True),  # noqa: E712
                or_(StockList.id == stock_list_name, StockList.name == stock_list_name),
            )
            .first()
        )

        if stock_list:
            return stock_list.get_stock_codes_list()[:100]

        # Fall back to file-based stock lists
        filename = f"{stock_list_name}.txt"
        possible_paths = [
            Path(f"data/{filename}"),
            Path(f"../data/{filename}"),
            Path(filename),
        ]

        for path in possible_paths:
            if path.exists():
                with open(path, "r") as f:
                    stocks = [
                        line.strip() for line in f if line.strip() and not line.startswith("#")
                    ]
                return stocks[:100]

        raise FileNotFoundError(f"Stock list not found: {stock_list_name}")

    def _fetch_all_data(
        self,
        stock_codes: list[str],
        start_date: date,
        end_date: date,
    ) -> dict[str, pd.DataFrame]:
        """Fetch all stock data upfront."""
        # Add buffer for indicator calculation
        start_with_buffer = start_date - timedelta(days=60)

        all_data = {}

        for code in stock_codes:
            ticker = f"{code}.KS"
            try:
                df = yf.download(
                    ticker,
                    start=start_with_buffer.isoformat(),
                    end=(end_date + timedelta(days=1)).isoformat(),
                    progress=False,
                    auto_adjust=False,
                )

                if df.empty:
                    ticker = f"{code}.KQ"
                    df = yf.download(
                        ticker,
                        start=start_with_buffer.isoformat(),
                        end=(end_date + timedelta(days=1)).isoformat(),
                        progress=False,
                        auto_adjust=False,
                    )

                if not df.empty and len(df) >= 30:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    all_data[code] = df[["Open", "High", "Low", "Close", "Volume"]].dropna()

            except Exception as e:
                logger.warning(f"Failed to fetch data for {code}: {e}")

        return all_data

    def _run_simulation(
        self,
        all_data: dict[str, pd.DataFrame],
        stock_names: dict[str, str],
        start_date: date,
        end_date: date,
        initial_capital: float,
    ) -> BacktestState:
        """Run the backtest simulation."""
        state = BacktestState(initial_capital=initial_capital, cash=initial_capital)

        # Get trading days
        if not all_data:
            return state

        sample_df = list(all_data.values())[0]
        trading_days = sample_df.loc[str(start_date) : str(end_date)].index.tolist()

        for trading_date in trading_days:
            date_str = trading_date.strftime("%Y-%m-%d")

            # 1. Check SELL signals
            positions_to_sell = []
            for code, pos in state.positions.items():
                if code not in all_data:
                    continue

                sell_signal = self._check_sell_signal(
                    all_data[code], date_str, pos.entry_price, pos.partial_take_profit_executed
                )
                if sell_signal:
                    positions_to_sell.append((code, sell_signal))

            # Execute sells
            for code, signal in positions_to_sell:
                pos = state.positions[code]

                # Determine sell quantity
                sell_ratio = signal.get("sell_ratio", 1.0)
                sell_quantity = int(pos.quantity * sell_ratio)
                if sell_quantity < 1:
                    sell_quantity = pos.quantity  # Force sell at least 1 or all if tiny

                proceeds = signal["price"] * sell_quantity
                pnl = (signal["price"] - pos.entry_price) * sell_quantity
                pnl_pct = signal["pnl_pct"]

                state.cash += proceeds
                state.trades.append(
                    Trade(
                        date=date_str,
                        stock_code=code,
                        stock_name=pos.stock_name,
                        action="SELL",
                        price=signal["price"],
                        quantity=sell_quantity,
                        reason=signal["reason"],
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                    )
                )

                # Update position state
                if sell_ratio >= 1.0 or sell_quantity >= pos.quantity:
                    # Full exit
                    del state.positions[code]
                else:
                    # Partial exit
                    pos.quantity -= sell_quantity
                    if signal["reason"] == "take_profit_target_hit":
                        pos.partial_take_profit_executed = True

            # 2. Check BUY signals
            if len(state.positions) < self.max_positions:
                buy_candidates = []

                for code, df in all_data.items():
                    if code in state.positions:
                        continue

                    buy_signal = self._check_buy_signal(df, date_str)
                    if buy_signal:
                        buy_candidates.append((code, buy_signal))

                # Sort by confidence
                buy_candidates.sort(key=lambda x: x[1]["confidence"], reverse=True)

                # Execute buys
                for code, signal in buy_candidates:
                    if len(state.positions) >= self.max_positions:
                        break

                    quantity = self._calculate_position_size(
                        signal["price"], state.cash, initial_capital
                    )
                    if quantity < 1:
                        continue

                    cost = signal["price"] * quantity
                    if cost > state.cash:
                        continue

                    state.cash -= cost
                    state.positions[code] = Position(
                        stock_code=code,
                        stock_name=stock_names.get(code, code),
                        quantity=quantity,
                        entry_price=signal["price"],
                        entry_date=date_str,
                    )
                    state.trades.append(
                        Trade(
                            date=date_str,
                            stock_code=code,
                            stock_name=stock_names.get(code, code),
                            action="BUY",
                            price=signal["price"],
                            quantity=quantity,
                            reason=f"squeeze_breakout (conf:{signal['confidence']})",
                        )
                    )

            # 3. Calculate daily value
            positions_value = 0
            for code, pos in state.positions.items():
                if code in all_data:
                    try:
                        idx = all_data[code].index.get_loc(trading_date)
                        current_price = float(all_data[code].iloc[idx]["Close"])
                        positions_value += current_price * pos.quantity
                    except (KeyError, IndexError):
                        positions_value += pos.entry_price * pos.quantity

            total_value = state.cash + positions_value
            state.daily_values.append((date_str, total_value))

        return state

    def _check_buy_signal(self, df: pd.DataFrame, date_str: str) -> Optional[dict]:
        """Check for buy signal on given date."""
        try:
            idx = df.index.get_loc(pd.Timestamp(date_str))
            if idx < 30:
                return None

            row = df.iloc[idx]
            prev_rows = df.iloc[idx - 5 : idx]

            if pd.isna(row["BB_Upper"]) or pd.isna(row["RSI"]):
                return None

            price_breakout = row["Close"] > row["BB_Upper"]
            was_in_squeeze = prev_rows["In_Squeeze"].any()
            bandwidth_expanding = row["BB_Width"] > df.iloc[idx - 1]["BB_Width"]

            if price_breakout and (was_in_squeeze or bandwidth_expanding):
                # Calculate continuous confidence score
                confidence = calculate_confidence_score(
                    volume_ratio=float(row["Volume_Ratio"]),
                    rsi=float(row["RSI"]),
                    macd_histogram=float(row["MACD_Histogram"]),
                    macd_signal=float(row["MACD_Signal"]),
                )

                if confidence >= self.confidence_threshold:
                    return {
                        "price": float(row["Close"]),
                        "confidence": confidence,
                    }
        except (KeyError, IndexError):
            pass
        return None

    def _check_sell_signal(
        self,
        df: pd.DataFrame,
        date_str: str,
        entry_price: float,
        partial_take_profit_executed: bool = False,
    ) -> Optional[dict]:
        """Check for sell signal with priority: Stop Loss > Take Profit > Trend Breakdown."""
        try:
            idx = df.index.get_loc(pd.Timestamp(date_str))
            row = df.iloc[idx]

            current_price = float(row["Close"])
            pnl_pct = ((current_price - entry_price) / entry_price) * 100

            # 1. Stop Loss (Priority 1)
            if pnl_pct <= -self.stop_loss_pct:
                return {
                    "price": current_price,
                    "reason": f"stop_loss ({pnl_pct:.1f}%)",
                    "pnl_pct": pnl_pct,
                    "sell_ratio": 1.0,
                }

            # 2. Daily Take Profit Check (Priority 2)
            # Only trigger once per position, and only if enabled
            if (
                self.take_profit_enabled
                and pnl_pct >= self.take_profit_pct
                and not partial_take_profit_executed
            ):
                return {
                    "price": current_price,
                    "reason": "take_profit_target_hit",
                    "pnl_pct": pnl_pct,
                    "sell_ratio": self.take_profit_ratio,
                }

            if self.sell_on_middle_band:
                bb_middle = row["BB_Middle"]
                if not pd.isna(bb_middle) and current_price < bb_middle:
                    return {
                        "price": current_price,
                        "reason": "trend_broken_middle_band",
                        "pnl_pct": pnl_pct,
                        "sell_ratio": 1.0,
                    }

        except (KeyError, IndexError):
            pass
        return None

    def _calculate_position_size(self, price: float, cash: float, initial_capital: float) -> int:
        """Calculate position size."""
        max_allocation = initial_capital * (self.max_position_pct / 100)
        max_shares = int(max_allocation / price)
        affordable_shares = int(cash / price)
        return min(max_shares, affordable_shares)

    def _analyze_performance(self, state: BacktestState) -> dict:
        """Analyze backtest performance."""
        final_value = state.daily_values[-1][1] if state.daily_values else state.initial_capital
        total_return = ((final_value - state.initial_capital) / state.initial_capital) * 100

        sell_trades = [t for t in state.trades if t.action == "SELL"]
        winning_trades = [t for t in sell_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in sell_trades if t.pnl and t.pnl <= 0]

        win_rate = (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0

        total_pnl = sum(t.pnl for t in sell_trades if t.pnl)
        avg_win = float(np.mean([t.pnl for t in winning_trades])) if winning_trades else 0
        avg_loss = float(np.mean([t.pnl for t in losing_trades])) if losing_trades else 0

        # Max drawdown
        values = [v[1] for v in state.daily_values]
        max_drawdown = 0
        if values:
            peak = values[0]
            for v in values:
                if v > peak:
                    peak = v
                drawdown = (peak - v) / peak * 100
                max_drawdown = max(max_drawdown, drawdown)

        return {
            "final_value": final_value,
            "total_return_pct": total_return,
            "total_trades": len(state.trades),
            "buy_trades": len([t for t in state.trades if t.action == "BUY"]),
            "sell_trades": len(sell_trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "max_drawdown": max_drawdown,
        }

    def _build_result_json(self, state: BacktestState, metrics: dict) -> dict:
        """Build detailed result JSON."""
        return {
            "backtest_metrics": metrics,
            "positions": [
                {
                    "stock_code": p.stock_code,
                    "stock_name": p.stock_name,
                    "quantity": p.quantity,
                    "entry_price": p.entry_price,
                    "entry_date": p.entry_date,
                }
                for p in state.positions.values()
            ],
            "trade_history": [
                {
                    "date": t.date,
                    "stock_code": t.stock_code,
                    "stock_name": t.stock_name,
                    "action": t.action,
                    "price": t.price,
                    "quantity": t.quantity,
                    "reason": t.reason,
                    "pnl": t.pnl,
                    "pnl_pct": t.pnl_pct,
                }
                for t in state.trades
            ],
            "daily_values": [{"date": d, "value": v} for d, v in state.daily_values],
        }

    def get_results(self, user_id: str, limit: int = 20) -> list[BacktestResult]:
        """Get backtest results for a user."""
        return (
            self.db.query(BacktestResult)
            .filter(BacktestResult.user_id == user_id)
            .order_by(BacktestResult.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_result(self, result_id: str, user_id: str) -> Optional[BacktestResult]:
        """Get a specific backtest result."""
        return (
            self.db.query(BacktestResult)
            .filter(BacktestResult.id == result_id, BacktestResult.user_id == user_id)
            .first()
        )
