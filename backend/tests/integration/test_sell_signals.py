from unittest.mock import patch

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


class TestSellSignalIntegration:
    def test_full_sell_signal_flow_stop_loss(self, mock_stock_data):
        scanner = SignalScanner(
            stop_loss_percent=5.0,
            take_profit_pct=10.0,
            take_profit_ratio=0.5,
        )
        mock_stock_data["Close"] = [9400.0]
        mock_stock_data["BB_Middle"] = [10000.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "stock_name": "Test Stock",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 1
                signal = signals[0]
                assert signal.signal_type == "SELL"
                assert signal.reason == "stop_loss_hit"
                assert signal.indicators["sell_quantity"] == 100
                assert signal.indicators["sell_ratio"] == 1.0
                assert "entry_price" in signal.indicators
                assert "pnl_pct" in signal.indicators
                assert "bb_middle" in signal.indicators

    def test_full_sell_signal_flow_take_profit(self, mock_stock_data):
        scanner = SignalScanner(
            stop_loss_percent=5.0,
            take_profit_pct=10.0,
            take_profit_ratio=0.5,
        )
        mock_stock_data["Close"] = [11000.0]
        mock_stock_data["BB_Middle"] = [10500.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "stock_name": "Test Stock",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 1
                signal = signals[0]
                assert signal.signal_type == "SELL"
                assert signal.reason == "take_profit_target_hit"
                assert signal.indicators["sell_quantity"] == 50

    def test_full_sell_signal_flow_trend_breakdown(self, mock_stock_data):
        scanner = SignalScanner(
            stop_loss_percent=5.0,
            take_profit_pct=10.0,
            take_profit_ratio=0.5,
        )
        mock_stock_data["Close"] = [9800.0]
        mock_stock_data["BB_Middle"] = [10000.0]

        with patch.object(scanner, "_get_stock_data", return_value=mock_stock_data):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "stock_name": "Test Stock",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    }
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 1
                signal = signals[0]
                assert signal.signal_type == "SELL"
                assert signal.reason == "trend_broken_middle_band"
                assert signal.indicators["sell_quantity"] == 100

    def test_priority_order_stop_loss_over_trend_breakdown(self, mock_stock_data):
        scanner = SignalScanner(
            stop_loss_percent=5.0,
            take_profit_pct=10.0,
            take_profit_ratio=0.5,
        )
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

    def test_priority_order_take_profit_over_trend_breakdown(self, mock_stock_data):
        scanner = SignalScanner(
            stop_loss_percent=5.0,
            take_profit_pct=10.0,
            take_profit_ratio=0.5,
        )
        mock_stock_data["Close"] = [11000.0]
        mock_stock_data["BB_Middle"] = [12000.0]

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
                assert reasons[0] == "take_profit_target_hit"
                assert reasons[1] == "trend_broken_middle_band"

    def test_multiple_positions_independent_signals(self, mock_stock_data):
        scanner = SignalScanner(
            stop_loss_percent=5.0,
            take_profit_pct=10.0,
            take_profit_ratio=0.5,
        )

        def get_stock_data_side_effect(stock_code):
            data = pd.DataFrame(
                {
                    "Close": [0.0],
                    "BB_Upper": [105.0],
                    "BB_Middle": [100.0],
                    "BB_Lower": [95.0],
                    "RSI": [50.0],
                    "MACD_Histogram": [0.5],
                    "Volume_Ratio": [1.5],
                    "BB_Width": [10.0],
                }
            )
            if stock_code == "005930":
                data["Close"] = [9400.0]
                data["BB_Middle"] = [10000.0]
            elif stock_code == "000660":
                data["Close"] = [11000.0]
                data["BB_Middle"] = [10500.0]
            return data

        with patch.object(scanner, "_get_stock_data", side_effect=get_stock_data_side_effect):
            with patch("src.wizard.signal_scanner.get_stock_name", return_value="Test Stock"):
                positions = [
                    {
                        "stock_code": "005930",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    },
                    {
                        "stock_code": "000660",
                        "avg_entry_price": 10000.0,
                        "quantity": 100,
                        "partial_take_profit_executed": False,
                    },
                ]

                signals = scanner.scan_for_sell_signals(positions)

                assert len(signals) == 2
                reasons = {s.stock_code: s.reason for s in signals}
                assert reasons["005930"] == "stop_loss_hit"
                assert reasons["000660"] == "take_profit_target_hit"
