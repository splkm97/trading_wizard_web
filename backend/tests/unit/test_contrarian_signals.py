"""Unit tests for MACD/RSI contrarian signal detection."""

from unittest.mock import patch

import pandas as pd
import pytest

from src.wizard.signal_scanner import (
    SignalScanner,
    calculate_contrarian_confidence,
    detect_macd_golden_cross,
    format_contrarian_reason_detail,
)


class TestCalculateContrarianConfidence:
    """Tests for calculate_contrarian_confidence() function - T010."""

    def test_deeply_oversold_rsi_20_or_below(self):
        """RSI <= 20 should give base score of 80."""
        # RSI = 20, no MACD bonus
        score = calculate_contrarian_confidence(rsi=20.0, macd_histogram=0, macd_signal=1.0)
        assert score == 80.0

        # RSI = 15, no MACD bonus
        score = calculate_contrarian_confidence(rsi=15.0, macd_histogram=0, macd_signal=1.0)
        assert score == 80.0

        # RSI = 20 (boundary)
        score = calculate_contrarian_confidence(rsi=20.0, macd_histogram=0, macd_signal=1.0)
        assert score == 80.0

    def test_oversold_rsi_20_to_25(self):
        """RSI 20-25 should give base score of 60."""
        # RSI = 22
        score = calculate_contrarian_confidence(rsi=22.0, macd_histogram=0, macd_signal=1.0)
        assert score == 60.0

        # RSI = 25 (boundary)
        score = calculate_contrarian_confidence(rsi=25.0, macd_histogram=0, macd_signal=1.0)
        assert score == 60.0

    def test_mildly_oversold_rsi_25_to_30(self):
        """RSI 25-30 should give base score of 40."""
        # RSI = 27
        score = calculate_contrarian_confidence(rsi=27.0, macd_histogram=0, macd_signal=1.0)
        assert score == 40.0

        # RSI = 30
        score = calculate_contrarian_confidence(rsi=30.0, macd_histogram=0, macd_signal=1.0)
        assert score == 40.0

    def test_macd_histogram_bonus_full(self):
        """Full MACD bonus (+20) when histogram equals signal strength."""
        # RSI = 20 (base 80) + MACD bonus (histogram = signal, ratio = 1.0, bonus = 20)
        score = calculate_contrarian_confidence(rsi=20.0, macd_histogram=100.0, macd_signal=100.0)
        assert score == 100.0  # 80 + 20 = 100 (capped)

    def test_macd_histogram_bonus_partial(self):
        """Partial MACD bonus when histogram < signal."""
        # RSI = 25 (base 60) + MACD bonus (histogram = 50% of signal, bonus = 10)
        score = calculate_contrarian_confidence(rsi=25.0, macd_histogram=50.0, macd_signal=100.0)
        assert score == 70.0  # 60 + 10 = 70

    def test_macd_histogram_bonus_capped(self):
        """MACD bonus should be capped even with large histogram."""
        # RSI = 20 (base 80) + MACD bonus (histogram > signal, ratio capped at 1.0)
        score = calculate_contrarian_confidence(rsi=20.0, macd_histogram=200.0, macd_signal=100.0)
        assert score == 100.0  # 80 + 20 = 100

    def test_no_macd_bonus_negative_histogram(self):
        """No MACD bonus when histogram is negative."""
        score = calculate_contrarian_confidence(rsi=20.0, macd_histogram=-50.0, macd_signal=100.0)
        assert score == 80.0  # Just base score

    def test_no_macd_bonus_zero_signal(self):
        """No MACD bonus when signal is zero (avoid division by zero)."""
        score = calculate_contrarian_confidence(rsi=20.0, macd_histogram=50.0, macd_signal=0.0)
        assert score == 80.0  # Just base score

    def test_total_score_capped_at_100(self):
        """Total score should never exceed 100."""
        score = calculate_contrarian_confidence(rsi=15.0, macd_histogram=500.0, macd_signal=100.0)
        assert score == 100.0


class TestDetectMacdGoldenCross:
    """Tests for detect_macd_golden_cross() function - T011."""

    def test_golden_cross_detected(self):
        """Detect golden cross when MACD crosses above signal."""
        df = pd.DataFrame({
            "MACD": [-10.0, 5.0],
            "MACD_Signal": [0.0, 0.0],
        })
        assert detect_macd_golden_cross(df) is True

    def test_golden_cross_exact_crossing(self):
        """Detect when MACD equals signal (crossing point)."""
        df = pd.DataFrame({
            "MACD": [-5.0, 0.0],
            "MACD_Signal": [0.0, 0.0],
        })
        assert detect_macd_golden_cross(df) is True

    def test_no_cross_macd_stays_below(self):
        """No cross when MACD stays below signal."""
        df = pd.DataFrame({
            "MACD": [-10.0, -5.0],
            "MACD_Signal": [0.0, 0.0],
        })
        assert detect_macd_golden_cross(df) is False

    def test_no_cross_macd_already_above(self):
        """No cross when MACD was already above signal."""
        df = pd.DataFrame({
            "MACD": [5.0, 10.0],
            "MACD_Signal": [0.0, 0.0],
        })
        assert detect_macd_golden_cross(df) is False

    def test_death_cross_not_detected(self):
        """Death cross (MACD falling below signal) should return False."""
        df = pd.DataFrame({
            "MACD": [10.0, -5.0],
            "MACD_Signal": [0.0, 0.0],
        })
        assert detect_macd_golden_cross(df) is False

    def test_insufficient_data(self):
        """Return False when insufficient data."""
        df = pd.DataFrame({
            "MACD": [5.0],
            "MACD_Signal": [0.0],
        })
        assert detect_macd_golden_cross(df) is False

    def test_empty_dataframe(self):
        """Return False for empty dataframe."""
        df = pd.DataFrame({"MACD": [], "MACD_Signal": []})
        assert detect_macd_golden_cross(df) is False

    def test_nan_values_current(self):
        """Return False when current values are NaN."""
        df = pd.DataFrame({
            "MACD": [-5.0, float('nan')],
            "MACD_Signal": [0.0, 0.0],
        })
        assert detect_macd_golden_cross(df) is False

    def test_nan_values_previous(self):
        """Return False when previous values are NaN."""
        df = pd.DataFrame({
            "MACD": [float('nan'), 5.0],
            "MACD_Signal": [0.0, 0.0],
        })
        assert detect_macd_golden_cross(df) is False


class TestScanForContrarianSignals:
    """Tests for scan_for_contrarian_signals() method - T012."""

    @pytest.fixture
    def mock_stock_data(self):
        """Create mock stock data with RSI and MACD indicators."""
        # Create data that would generate indicators after calculation
        df = pd.DataFrame({
            "Open": [100.0] * 40,
            "High": [105.0] * 40,
            "Low": [95.0] * 40,
            "Close": [100.0] * 40,
            "Volume": [1000000] * 40,
            "RSI": [50.0] * 38 + [25.0, 25.0],  # RSI oversold on last 2 days
            "MACD": [0.0] * 38 + [-5.0, 5.0],  # Golden cross on last day
            "MACD_Signal": [0.0] * 40,
            "MACD_Histogram": [0.0] * 38 + [-5.0, 5.0],
            "BB_Upper": [110.0] * 40,
            "BB_Middle": [100.0] * 40,
            "BB_Lower": [90.0] * 40,
            "BB_Width": [20.0] * 40,
            "BB_Width_MA": [20.0] * 40,
            "Volume_MA": [1000000] * 40,
            "Volume_Ratio": [1.0] * 40,
            "In_Squeeze": [False] * 40,
        })
        return df

    @patch.object(SignalScanner, '_get_stock_data')
    @patch('src.wizard.signal_scanner.get_stock_name')
    def test_signal_detected_with_valid_conditions(self, mock_get_name, mock_get_data, mock_stock_data):
        """Signal detected when RSI oversold AND MACD golden cross."""
        mock_get_data.return_value = mock_stock_data
        mock_get_name.return_value = "Test Stock"

        scanner = SignalScanner()
        signals = scanner.scan_for_contrarian_signals(
            stock_codes=["005930"],
            rsi_threshold=30.0,
            confidence_threshold=40.0,
        )

        assert len(signals) == 1
        assert signals[0].stock_code == "005930"
        assert signals[0].signal_type == "BUY"
        assert signals[0].reason == "contrarian_oversold_reversal"

    @patch.object(SignalScanner, '_get_stock_data')
    def test_no_signal_rsi_above_threshold(self, mock_get_data, mock_stock_data):
        """No signal when RSI is above threshold."""
        # Modify RSI to be above threshold
        mock_stock_data["RSI"] = [50.0] * 40
        mock_get_data.return_value = mock_stock_data

        scanner = SignalScanner()
        signals = scanner.scan_for_contrarian_signals(
            stock_codes=["005930"],
            rsi_threshold=30.0,
        )

        assert len(signals) == 0

    @patch.object(SignalScanner, '_get_stock_data')
    def test_no_signal_no_golden_cross(self, mock_get_data, mock_stock_data):
        """No signal when no MACD golden cross."""
        # Modify MACD to stay below signal
        mock_stock_data["MACD"] = [-5.0] * 40
        mock_get_data.return_value = mock_stock_data

        scanner = SignalScanner()
        signals = scanner.scan_for_contrarian_signals(
            stock_codes=["005930"],
            rsi_threshold=30.0,
        )

        assert len(signals) == 0

    @patch.object(SignalScanner, '_get_stock_data')
    def test_no_signal_below_confidence_threshold(self, mock_get_data, mock_stock_data):
        """No signal when confidence below threshold."""
        # RSI at 30 gives base 40, with small histogram gives < 50 confidence
        mock_stock_data["RSI"] = [50.0] * 38 + [30.0, 30.0]
        mock_stock_data["MACD_Histogram"] = [0.0] * 38 + [-0.1, 0.1]  # Tiny histogram
        mock_get_data.return_value = mock_stock_data

        scanner = SignalScanner()
        signals = scanner.scan_for_contrarian_signals(
            stock_codes=["005930"],
            rsi_threshold=30.0,
            confidence_threshold=50.0,  # High threshold
        )

        assert len(signals) == 0

    @patch.object(SignalScanner, '_get_stock_data')
    def test_insufficient_data_excluded(self, mock_get_data):
        """Stocks with insufficient data are excluded."""
        # Return short dataframe
        short_df = pd.DataFrame({
            "Close": [100.0] * 20,
            "RSI": [25.0] * 20,
            "MACD": [5.0] * 20,
            "MACD_Signal": [0.0] * 20,
        })
        mock_get_data.return_value = short_df

        scanner = SignalScanner()
        signals = scanner.scan_for_contrarian_signals(stock_codes=["005930"])

        assert len(signals) == 0

    @patch.object(SignalScanner, '_get_stock_data')
    def test_none_data_excluded(self, mock_get_data):
        """Stocks with None data are excluded."""
        mock_get_data.return_value = None

        scanner = SignalScanner()
        signals = scanner.scan_for_contrarian_signals(stock_codes=["005930"])

        assert len(signals) == 0

    @patch.object(SignalScanner, '_get_stock_data')
    @patch('src.wizard.signal_scanner.get_stock_name')
    def test_signals_sorted_by_confidence(self, mock_get_name, mock_get_data, mock_stock_data):
        """Signals should be sorted by confidence descending."""
        def side_effect(stock_code):
            df = mock_stock_data.copy()
            if stock_code == "005930":
                df["RSI"] = [50.0] * 38 + [15.0, 15.0]  # Very oversold -> high confidence
            else:
                df["RSI"] = [50.0] * 38 + [28.0, 28.0]  # Mildly oversold -> lower confidence
            return df

        mock_get_data.side_effect = side_effect
        mock_get_name.return_value = "Test Stock"

        scanner = SignalScanner()
        signals = scanner.scan_for_contrarian_signals(
            stock_codes=["000660", "005930"],  # 000660 listed first
            rsi_threshold=30.0,
            confidence_threshold=40.0,
        )

        assert len(signals) == 2
        # Higher confidence (005930 with RSI 15) should be first
        assert signals[0].stock_code == "005930"
        assert signals[0].confidence_score > signals[1].confidence_score

    @patch.object(SignalScanner, '_get_stock_data')
    @patch('src.wizard.signal_scanner.get_stock_name')
    def test_max_results_respected(self, mock_get_name, mock_get_data, mock_stock_data):
        """max_results parameter should limit output."""
        mock_get_data.return_value = mock_stock_data
        mock_get_name.return_value = "Test Stock"

        scanner = SignalScanner()
        signals = scanner.scan_for_contrarian_signals(
            stock_codes=["005930", "000660", "035420"],
            rsi_threshold=30.0,
            confidence_threshold=40.0,
            max_results=1,
        )

        assert len(signals) <= 1

    @patch.object(SignalScanner, '_get_stock_data')
    @patch('src.wizard.signal_scanner.get_stock_name')
    def test_indicators_in_signal(self, mock_get_name, mock_get_data, mock_stock_data):
        """Signal should contain correct indicators."""
        mock_get_data.return_value = mock_stock_data
        mock_get_name.return_value = "Test Stock"

        scanner = SignalScanner()
        signals = scanner.scan_for_contrarian_signals(
            stock_codes=["005930"],
            rsi_threshold=30.0,
        )

        assert len(signals) == 1
        indicators = signals[0].indicators
        assert "rsi" in indicators
        assert "macd" in indicators
        assert "macd_signal" in indicators
        assert "macd_histogram" in indicators
        assert "reason_detail" in indicators
        # reason_detail should be a Korean explanation
        assert isinstance(indicators["reason_detail"], str)
        assert len(indicators["reason_detail"]) > 0


class TestFormatContrarianReasonDetail:
    """Tests for format_contrarian_reason_detail() function - T020."""

    def test_deeply_oversold_rsi_below_20(self):
        """RSI <= 20 should describe as 'severely oversold'."""
        result = format_contrarian_reason_detail(
            rsi=18.5,
            macd=0.5,
            macd_signal=0.3,
            macd_histogram=0.2,
        )
        assert "RSI 18.5" in result
        assert "심각한 과매도" in result
        assert "MACD" in result
        assert "상향 돌파" in result

    def test_oversold_rsi_between_20_and_25(self):
        """RSI 20-25 should describe as 'strongly oversold'."""
        result = format_contrarian_reason_detail(
            rsi=22.0,
            macd=0.5,
            macd_signal=0.3,
            macd_histogram=0.2,
        )
        assert "RSI 22.0" in result
        assert "강한 과매도" in result

    def test_mildly_oversold_rsi_between_25_and_30(self):
        """RSI 25-30 should describe as 'oversold'."""
        result = format_contrarian_reason_detail(
            rsi=28.0,
            macd=0.5,
            macd_signal=0.3,
            macd_histogram=0.2,
        )
        assert "RSI 28.0" in result
        assert "과매도 상태" in result
        # Should NOT contain 'severely' or 'strongly'
        assert "심각한" not in result
        assert "강한 과매도" not in result

    def test_strong_macd_histogram(self):
        """Strong MACD histogram should indicate 'strong' breakout."""
        # macd_histogram > abs(macd_signal * 0.5) = strong
        result = format_contrarian_reason_detail(
            rsi=25.0,
            macd=1.0,
            macd_signal=0.5,
            macd_histogram=0.5,  # > 0.25 (0.5 * 0.5)
        )
        assert "강한" in result or "강한상향" in result

    def test_weak_macd_histogram(self):
        """Weak MACD histogram should not indicate 'strong' breakout."""
        # macd_histogram <= abs(macd_signal * 0.5) = not strong
        result = format_contrarian_reason_detail(
            rsi=25.0,
            macd=0.5,
            macd_signal=1.0,
            macd_histogram=0.1,  # < 0.5 (1.0 * 0.5)
        )
        # Should contain '상향 돌파' but not with '강한' prefix
        assert "상향 돌파" in result

    def test_result_contains_rebound_message(self):
        """Result should contain technical rebound possibility message."""
        result = format_contrarian_reason_detail(
            rsi=20.0,
            macd=0.5,
            macd_signal=0.3,
            macd_histogram=0.2,
        )
        assert "기술적 반등 가능성" in result

    def test_rsi_boundary_20(self):
        """RSI exactly at 20 should be 'severely oversold'."""
        result = format_contrarian_reason_detail(
            rsi=20.0,
            macd=0.5,
            macd_signal=0.3,
            macd_histogram=0.2,
        )
        assert "심각한 과매도" in result

    def test_rsi_boundary_25(self):
        """RSI exactly at 25 should be 'strongly oversold'."""
        result = format_contrarian_reason_detail(
            rsi=25.0,
            macd=0.5,
            macd_signal=0.3,
            macd_histogram=0.2,
        )
        assert "강한 과매도" in result

    def test_result_format_structure(self):
        """Result should be a properly formatted Korean sentence."""
        result = format_contrarian_reason_detail(
            rsi=22.0,
            macd=0.5,
            macd_signal=0.3,
            macd_histogram=0.2,
        )
        # Should contain proper sentence structure with periods
        assert result.endswith(".")
        # Should have two main parts connected by period
        parts = result.split(".")
        assert len(parts) >= 3  # At least RSI desc, MACD desc, rebound message


class TestScanForContrarianCandidates:
    """Tests for scan_for_contrarian_candidates() method."""

    @pytest.fixture
    def mock_candidate_stock_data(self):
        """Create mock stock data for candidate testing."""
        # Create 40 rows of data
        dates = pd.date_range(start='2024-01-01', periods=40, freq='D')
        data = {
            'Close': [50000.0] * 40,
            'MACD': [-0.5] * 38 + [-0.3, -0.2],  # MACD rising but still below signal
            'MACD_Signal': [0.0] * 40,  # MACD < Signal
            'MACD_Histogram': [-0.5] * 38 + [-0.3, -0.2],  # Rising but still negative
            'RSI': [50.0] * 38 + [28.0, 28.0],  # Oversold
            'BB_Width': [0.1] * 40,
        }
        return pd.DataFrame(data, index=dates)

    @patch.object(SignalScanner, '_get_stock_data')
    @patch('src.wizard.signal_scanner.get_stock_name')
    def test_rsi_oversold_waiting_detected(self, mock_get_name, mock_get_data, mock_candidate_stock_data):
        """RSI oversold with rising MACD histogram should be RSI_OVERSOLD_WAITING."""
        mock_get_data.return_value = mock_candidate_stock_data
        mock_get_name.return_value = "Test Stock"

        scanner = SignalScanner()
        candidates = scanner.scan_for_contrarian_candidates(
            stock_codes=["005930"],
            rsi_threshold_max=40.0,
            confidence_threshold=20.0,
        )

        assert len(candidates) == 1
        assert candidates[0].signal_type == "CANDIDATE"
        assert candidates[0].indicators["signal_stage"] == "RSI_OVERSOLD_WAITING"
        assert "RSI" in candidates[0].indicators["reason_detail"]
        assert "과매도" in candidates[0].indicators["reason_detail"]

    @patch.object(SignalScanner, '_get_stock_data')
    @patch('src.wizard.signal_scanner.get_stock_name')
    def test_macd_crossed_rsi_recovering_detected(self, mock_get_name, mock_get_data):
        """MACD golden cross with recovering RSI should be MACD_CROSSED_RSI_RECOVERING."""
        # Create data where MACD crosses but RSI > 30
        dates = pd.date_range(start='2024-01-01', periods=40, freq='D')
        data = {
            'Close': [50000.0] * 40,
            'MACD': [-0.3] * 38 + [-0.1, 0.1],  # Crosses from below to above
            'MACD_Signal': [0.0] * 40,  # Signal at 0
            'MACD_Histogram': [-0.3] * 38 + [-0.1, 0.1],  # Crosses to positive
            'RSI': [50.0] * 38 + [35.0, 35.0],  # Above 30 but below 40
            'BB_Width': [0.1] * 40,
        }
        df = pd.DataFrame(data, index=dates)
        mock_get_data.return_value = df
        mock_get_name.return_value = "Test Stock"

        scanner = SignalScanner()
        candidates = scanner.scan_for_contrarian_candidates(
            stock_codes=["005930"],
            rsi_threshold_max=40.0,
            confidence_threshold=20.0,
        )

        assert len(candidates) == 1
        assert candidates[0].indicators["signal_stage"] == "MACD_CROSSED_RSI_RECOVERING"
        assert "MACD" in candidates[0].indicators["reason_detail"]
        assert "골든크로스" in candidates[0].indicators["reason_detail"]

    @patch.object(SignalScanner, '_get_stock_data')
    @patch('src.wizard.signal_scanner.get_stock_name')
    def test_approaching_detected(self, mock_get_name, mock_get_data):
        """Both indicators approaching thresholds should be APPROACHING."""
        # Create data where both RSI and MACD are approaching
        dates = pd.date_range(start='2024-01-01', periods=40, freq='D')
        data = {
            'Close': [50000.0] * 40,
            'MACD': [-0.2] * 38 + [-0.15, -0.1],
            'MACD_Signal': [0.0] * 40,
            'MACD_Histogram': [-0.4] * 38 + [-0.3, -0.2],  # Rising but < 0 and >= -0.5
            'RSI': [50.0] * 38 + [35.0, 35.0],  # Between 30 and 40
            'BB_Width': [0.1] * 40,
        }
        df = pd.DataFrame(data, index=dates)
        mock_get_data.return_value = df
        mock_get_name.return_value = "Test Stock"

        scanner = SignalScanner()
        candidates = scanner.scan_for_contrarian_candidates(
            stock_codes=["005930"],
            rsi_threshold_max=40.0,
            confidence_threshold=20.0,
        )

        assert len(candidates) == 1
        assert candidates[0].indicators["signal_stage"] == "APPROACHING"
        assert "접근" in candidates[0].indicators["reason_detail"]

    @patch.object(SignalScanner, '_get_stock_data')
    @patch('src.wizard.signal_scanner.get_stock_name')
    @patch('src.wizard.signal_scanner.detect_macd_golden_cross')
    def test_full_signal_excluded_from_candidates(self, mock_cross, mock_get_name, mock_get_data, mock_candidate_stock_data):
        """Stocks with full signal conditions should not be candidates."""
        # Modify data to have RSI <= 30 and golden cross (full signal)
        df = mock_candidate_stock_data.copy()
        df["RSI"] = [50.0] * 38 + [25.0, 25.0]  # Oversold
        mock_get_data.return_value = df
        mock_get_name.return_value = "Test Stock"
        mock_cross.return_value = True  # Golden cross detected

        scanner = SignalScanner()
        candidates = scanner.scan_for_contrarian_candidates(
            stock_codes=["005930"],
            rsi_threshold_max=40.0,
            confidence_threshold=20.0,
        )

        # Full signal should be excluded from candidates
        assert len(candidates) == 0

    @patch.object(SignalScanner, '_get_stock_data')
    @patch('src.wizard.signal_scanner.get_stock_name')
    def test_rsi_above_max_threshold_excluded(self, mock_get_name, mock_get_data):
        """Stocks with RSI above max threshold should be excluded."""
        dates = pd.date_range(start='2024-01-01', periods=40, freq='D')
        data = {
            'Close': [50000.0] * 40,
            'MACD': [-0.5] * 40,
            'MACD_Signal': [0.0] * 40,
            'MACD_Histogram': [-0.5] * 38 + [-0.3, -0.2],
            'RSI': [50.0] * 38 + [45.0, 45.0],  # Above 40 threshold
            'BB_Width': [0.1] * 40,
        }
        df = pd.DataFrame(data, index=dates)
        mock_get_data.return_value = df
        mock_get_name.return_value = "Test Stock"

        scanner = SignalScanner()
        candidates = scanner.scan_for_contrarian_candidates(
            stock_codes=["005930"],
            rsi_threshold_max=40.0,
            confidence_threshold=20.0,
        )

        assert len(candidates) == 0

    @patch.object(SignalScanner, '_get_stock_data')
    @patch('src.wizard.signal_scanner.get_stock_name')
    def test_candidates_sorted_by_confidence(self, mock_get_name, mock_get_data, mock_candidate_stock_data):
        """Candidates should be sorted by confidence descending."""
        def side_effect(stock_code):
            df = mock_candidate_stock_data.copy()
            if stock_code == "005930":
                df["RSI"] = [50.0] * 38 + [25.0, 25.0]  # Very oversold -> higher confidence
            else:
                df["RSI"] = [50.0] * 38 + [29.0, 29.0]  # Mildly oversold -> lower confidence
            return df

        mock_get_data.side_effect = side_effect
        mock_get_name.return_value = "Test Stock"

        scanner = SignalScanner()
        candidates = scanner.scan_for_contrarian_candidates(
            stock_codes=["000660", "005930"],
            rsi_threshold_max=40.0,
            confidence_threshold=20.0,
        )

        assert len(candidates) == 2
        # Higher confidence (005930 with RSI 25) should be first
        assert candidates[0].stock_code == "005930"
        assert candidates[0].confidence_score > candidates[1].confidence_score

    @patch.object(SignalScanner, '_get_stock_data')
    @patch('src.wizard.signal_scanner.get_stock_name')
    def test_max_results_respected(self, mock_get_name, mock_get_data, mock_candidate_stock_data):
        """max_results should limit the number of candidates."""
        mock_get_data.return_value = mock_candidate_stock_data
        mock_get_name.return_value = "Test Stock"

        scanner = SignalScanner()
        candidates = scanner.scan_for_contrarian_candidates(
            stock_codes=["005930", "000660", "035420"],
            rsi_threshold_max=40.0,
            confidence_threshold=20.0,
            max_results=1,
        )

        assert len(candidates) <= 1
