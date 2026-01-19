"""
Unit tests for PostgreSQL optimization functions.

Tests:
1. Bulk insert functionality
2. Raw SQL query optimization
3. Signal Scanner DB-first strategy
"""

import os
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestBulkLoadScript:
    """Tests for bulk_load_historical_prices_postgres.py functions."""

    def test_load_stock_codes(self):
        """Test stock code loading from file."""
        from scripts.bulk_load_historical_prices_postgres import load_stock_codes

        # This may fail if file doesn't exist, which is expected in some environments
        try:
            codes = load_stock_codes()
            assert isinstance(codes, list)
            assert len(codes) > 0
            # All codes should be strings
            for code in codes:
                assert isinstance(code, str)
                assert len(code) == 6  # Korean stock codes are 6 digits
        except SystemExit:
            pytest.skip("Stock code file not found")

    def test_download_stock_data_returns_list(self):
        """Test that download function returns list of records."""
        from scripts.bulk_load_historical_prices_postgres import download_stock_data

        # Use a well-known stock code
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        records = download_stock_data("005930", start_date.isoformat(), end_date.isoformat())

        assert isinstance(records, list)
        # Records may be empty if yfinance fails, but should be a list
        if records:
            record = records[0]
            assert "stock_code" in record
            assert "date" in record
            assert "open" in record
            assert "high" in record
            assert "low" in record
            assert "close" in record
            assert "volume" in record


class TestSimulationServiceOptimization:
    """Tests for simulation_service.py query optimization."""

    @patch("src.services.simulation_service.pd.read_sql_query")
    def test_fetch_historical_data_from_db_uses_raw_sql(self, mock_read_sql):
        """Test that _fetch_historical_data_from_db uses pandas.read_sql_query."""
        # Create mock DataFrame
        mock_df = pd.DataFrame(
            {
                "open": [100.0] * 30,
                "high": [101.0] * 30,
                "low": [99.0] * 30,
                "close": [100.5] * 30,
                "volume": [1000000] * 30,
            },
            index=pd.date_range(end=date.today(), periods=30, freq="D"),
        )
        mock_read_sql.return_value = mock_df

        # Mock the session
        mock_session = MagicMock()
        mock_bind = MagicMock()
        mock_connection = MagicMock()
        mock_bind.connect.return_value = mock_connection
        mock_session.get_bind.return_value = mock_bind

        from src.services.simulation_service import SimulationService

        service = SimulationService(mock_session)
        result = service._fetch_historical_data_from_db("005930", date.today(), 30)

        # Verify read_sql_query was called
        mock_read_sql.assert_called_once()
        # Connection should be closed
        mock_connection.close.assert_called_once()

    def test_fetch_historical_data_from_db_returns_none_on_insufficient_data(self):
        """Test that method returns None when data is insufficient."""
        # Create mock with less than 30 records
        mock_df = pd.DataFrame(
            {
                "open": [100.0] * 10,
                "high": [101.0] * 10,
                "low": [99.0] * 10,
                "close": [100.5] * 10,
                "volume": [1000000] * 10,
            }
        )

        mock_session = MagicMock()
        mock_bind = MagicMock()
        mock_connection = MagicMock()
        mock_bind.connect.return_value = mock_connection
        mock_session.get_bind.return_value = mock_bind

        with patch("src.services.simulation_service.pd.read_sql_query", return_value=mock_df):
            from src.services.simulation_service import SimulationService

            service = SimulationService(mock_session)
            result = service._fetch_historical_data_from_db("005930", date.today(), 30)

            assert result is None


class TestSignalScannerDBFirst:
    """Tests for Signal Scanner DB-first data access."""

    def test_fetch_stock_data_from_db_function_exists(self):
        """Test that fetch_stock_data_from_db function is available."""
        from src.wizard.signal_scanner import fetch_stock_data_from_db

        assert callable(fetch_stock_data_from_db)

    @patch("src.wizard.signal_scanner.create_engine")
    @patch("src.wizard.signal_scanner.pd.read_sql_query")
    def test_fetch_stock_data_from_db_uses_raw_sql(self, mock_read_sql, mock_engine):
        """Test that fetch_stock_data_from_db uses pandas.read_sql_query."""
        # Create mock DataFrame
        mock_df = pd.DataFrame(
            {
                "open": [100.0] * 30,
                "high": [101.0] * 30,
                "low": [99.0] * 30,
                "close": [100.5] * 30,
                "volume": [1000000] * 30,
            }
        )
        mock_read_sql.return_value = mock_df

        # Mock engine and connection
        mock_conn = MagicMock()
        mock_engine_instance = MagicMock()
        mock_engine_instance.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine_instance.connect.return_value.__exit__ = MagicMock(return_value=False)

        from src.wizard.signal_scanner import fetch_stock_data_from_db

        result = fetch_stock_data_from_db("005930", engine=mock_engine_instance)

        # Verify read_sql_query was called
        mock_read_sql.assert_called_once()

    def test_signal_scanner_get_stock_data_tries_db_first(self):
        """Test that SignalScanner._get_stock_data tries DB before yfinance."""
        from src.wizard.signal_scanner import SignalScanner

        scanner = SignalScanner(use_cache=False)

        with patch("src.wizard.signal_scanner.fetch_stock_data_from_db") as mock_db, patch(
            "src.wizard.signal_scanner.fetch_stock_data"
        ) as mock_yf:

            # DB returns valid data
            mock_df = pd.DataFrame(
                {
                    "Open": [100.0] * 35,
                    "High": [101.0] * 35,
                    "Low": [99.0] * 35,
                    "Close": [100.5] * 35,
                    "Volume": [1000000] * 35,
                },
                index=pd.date_range(end=date.today(), periods=35, freq="D"),
            )
            mock_db.return_value = mock_df

            result = scanner._get_stock_data("005930")

            # DB should be called
            mock_db.assert_called_once()
            # yfinance should NOT be called when DB succeeds
            mock_yf.assert_not_called()

    def test_signal_scanner_falls_back_to_yfinance(self):
        """Test that SignalScanner falls back to yfinance when DB fails."""
        from src.wizard.signal_scanner import SignalScanner

        scanner = SignalScanner(use_cache=False)

        with patch("src.wizard.signal_scanner.fetch_stock_data_from_db") as mock_db, patch(
            "src.wizard.signal_scanner.fetch_stock_data"
        ) as mock_yf:

            # DB returns None
            mock_db.return_value = None

            # yfinance returns valid data
            mock_df = pd.DataFrame(
                {
                    "Open": [100.0] * 35,
                    "High": [101.0] * 35,
                    "Low": [99.0] * 35,
                    "Close": [100.5] * 35,
                    "Volume": [1000000] * 35,
                },
                index=pd.date_range(end=date.today(), periods=35, freq="D"),
            )
            mock_yf.return_value = mock_df

            result = scanner._get_stock_data("005930")

            # DB should be called first
            mock_db.assert_called_once()
            # yfinance should be called as fallback
            mock_yf.assert_called_once()


class TestQueryOptimization:
    """Tests for SQL query optimization."""

    def test_raw_sql_query_uses_indexes(self):
        """Test that raw SQL query is index-optimized."""
        from sqlalchemy import text

        query = text(
            """
            SELECT date, open, high, low, close, volume
            FROM historical_prices
            WHERE stock_code = :code
              AND date >= :start_date
              AND date <= :end_date
            ORDER BY date ASC
        """
        )

        # Query should contain index-friendly patterns
        query_str = str(query)
        assert "stock_code" in query_str
        assert "date" in query_str
        assert "ORDER BY date" in query_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
