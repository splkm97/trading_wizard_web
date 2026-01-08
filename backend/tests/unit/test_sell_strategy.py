import math
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.wizard.signal_scanner import SignalScanner


@pytest.fixture
def mock_stock_data():
    return pd.DataFrame(
        {
            "Close": [100.0],
            "BB_Upper": [105.0],
            "BB_Middle": [100.0],
            "BB_Lower": [95.0],
            "RSI": [50.0],
            "MACD_Histogram": [0.5],
            "Volume_Ratio": [1.5],
            "BB_Width": [10.0],
        }
    )


@pytest.fixture
def scanner():
    return SignalScanner(
        confidence_threshold=60,
        stop_loss_percent=5.0,
        take_profit_pct=10.0,
        take_profit_ratio=0.5,
    )


class TestStopLoss:
    def test_stop_loss_triggers_at_exactly_minus_5_percent(self, scanner, mock_stock_data):
        mock_stock_data["Close"] = [9500.0]
        mock_stock_data["BB_Middle"] = [10000.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 1
                assert signals[0].reason == "stop_loss_hit"
                assert signals[0].indicators["sell_quantity"] == 100
                assert signals[0].indicators["sell_ratio"] == 1.0

    def test_stop_loss_does_not_trigger_at_minus_4_percent(self, scanner, mock_stock_data):
        mock_stock_data["Close"] = [9600.0]
        mock_stock_data["BB_Middle"] = [9500.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 0

    def test_stop_loss_triggers_at_minus_10_percent(self, scanner, mock_stock_data):
        mock_stock_data["Close"] = [9000.0]
        mock_stock_data["BB_Middle"] = [10000.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 1
                assert signals[0].reason == "stop_loss_hit"


class TestTakeProfit:
    def test_take_profit_triggers_at_plus_10_percent_with_50_percent_sell(
        self, scanner, mock_stock_data
    ):
        mock_stock_data["Close"] = [11000.0]
        mock_stock_data["BB_Middle"] = [10500.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 1
                assert signals[0].reason == "take_profit_target_hit"
                assert signals[0].indicators["sell_quantity"] == 50
                assert signals[0].indicators["sell_ratio"] == 0.5

    def test_take_profit_does_not_trigger_at_plus_9_percent(self, scanner, mock_stock_data):
        mock_stock_data["Close"] = [10900.0]
        mock_stock_data["BB_Middle"] = [10800.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 0

    def test_take_profit_does_not_re_trigger_when_executed(self, scanner, mock_stock_data):
        mock_stock_data["Close"] = [11000.0]
        mock_stock_data["BB_Middle"] = [10500.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "avg_entry_price": 10000.0,
                        "quantity": 50,
                        "partial_take_profit_executed": True,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 0

    def test_minimum_1_share_sold_on_partial_take_profit(self, scanner, mock_stock_data):
        mock_stock_data["Close"] = [11000.0]
        mock_stock_data["BB_Middle"] = [10500.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "avg_entry_price": 10000.0,
                        "quantity": 1,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 1
                assert signals[0].indicators["sell_quantity"] == 1


class TestTrendBreakdown:
    def test_trend_breakdown_triggers_when_close_below_middle_band(self, scanner, mock_stock_data):
        mock_stock_data["Close"] = [9800.0]
        mock_stock_data["BB_Middle"] = [10000.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 1
                assert signals[0].reason == "trend_broken_middle_band"
                assert signals[0].indicators["sell_quantity"] == 100
                assert signals[0].indicators["sell_ratio"] == 1.0

    def test_trend_breakdown_does_not_trigger_when_close_equals_middle_band(
        self, scanner, mock_stock_data
    ):
        mock_stock_data["Close"] = [10000.0]
        mock_stock_data["BB_Middle"] = [10000.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 0

    def test_stop_loss_takes_priority_over_trend_breakdown(self, scanner, mock_stock_data):
        mock_stock_data["Close"] = [9400.0]
        mock_stock_data["BB_Middle"] = [10000.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 1
                assert signals[0].reason == "stop_loss_hit"

    def test_take_profit_and_trend_breakdown_can_coexist(self, scanner, mock_stock_data):
        mock_stock_data["Close"] = [11000.0]
        mock_stock_data["BB_Middle"] = [11500.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 2
                reasons = [s.reason for s in signals]
                assert "take_profit_target_hit" in reasons
                assert "trend_broken_middle_band" in reasons

                take_profit_signal = next(
                    s for s in signals if s.reason == "take_profit_target_hit"
                )
                trend_signal = next(s for s in signals if s.reason == "trend_broken_middle_band")

                assert take_profit_signal.indicators["sell_quantity"] == 50
                assert trend_signal.indicators["sell_quantity"] == 50


class TestConfigurableParameters:
    def test_custom_stop_loss_pct_triggers_at_custom_threshold(self, mock_stock_data):
        scanner = SignalScanner(
            stop_loss_percent=3.0,
            take_profit_pct=10.0,
            take_profit_ratio=0.5,
        )
        mock_stock_data["Close"] = [9700.0]
        mock_stock_data["BB_Middle"] = [10000.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 1
                assert signals[0].reason == "stop_loss_hit"

    def test_custom_take_profit_pct_does_not_trigger_at_default(self, mock_stock_data):
        scanner = SignalScanner(
            stop_loss_percent=5.0,
            take_profit_pct=15.0,
            take_profit_ratio=0.5,
        )
        mock_stock_data["Close"] = [11000.0]
        mock_stock_data["BB_Middle"] = [10500.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 0

    def test_custom_take_profit_ratio_sells_70_percent(self, mock_stock_data):
        scanner = SignalScanner(
            stop_loss_percent=5.0,
            take_profit_pct=10.0,
            take_profit_ratio=0.7,
        )
        mock_stock_data["Close"] = [11000.0]
        mock_stock_data["BB_Middle"] = [10500.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 1
                assert signals[0].indicators["sell_quantity"] == 70
                assert signals[0].indicators["sell_ratio"] == 0.7


class TestParameterValidation:
    def test_stop_loss_percent_below_range_raises_error(self):
        with pytest.raises(ValueError, match="stop_loss_percent must be between 1.0 and 20.0"):
            SignalScanner(stop_loss_percent=0.5)

    def test_stop_loss_percent_above_range_raises_error(self):
        with pytest.raises(ValueError, match="stop_loss_percent must be between 1.0 and 20.0"):
            SignalScanner(stop_loss_percent=25.0)

    def test_take_profit_pct_below_range_raises_error(self):
        with pytest.raises(ValueError, match="take_profit_pct must be between 5.0 and 50.0"):
            SignalScanner(take_profit_pct=3.0)

    def test_take_profit_pct_above_range_raises_error(self):
        with pytest.raises(ValueError, match="take_profit_pct must be between 5.0 and 50.0"):
            SignalScanner(take_profit_pct=60.0)

    def test_take_profit_ratio_below_range_raises_error(self):
        with pytest.raises(ValueError, match="take_profit_ratio must be between 0.1 and 1.0"):
            SignalScanner(take_profit_ratio=0.05)

    def test_take_profit_ratio_above_range_raises_error(self):
        with pytest.raises(ValueError, match="take_profit_ratio must be between 0.1 and 1.0"):
            SignalScanner(take_profit_ratio=1.5)
