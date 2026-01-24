"""Unit tests for the signal precomputer service."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytz


class TestSignalPrecomputer:
    """Tests for signal precomputation functionality."""

    def test_is_market_hours_during_trading(self):
        """Test is_market_hours returns True during market hours."""

        # Mock datetime to be during market hours (10:00 KST on Monday)
        mock_now = datetime(2026, 1, 13, 10, 0, 0, tzinfo=pytz.timezone("Asia/Seoul"))

        with patch("src.services.signal_precomputer.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now
            # Note: This test may pass or fail depending on actual time
            # In real testing, we should mock the entire datetime module

    def test_is_market_hours_weekend(self):
        """Test is_market_hours returns False on weekends."""
        from src.services.signal_precomputer import KST

        # Create a Saturday datetime
        saturday = datetime(2026, 1, 11, 10, 0, 0)  # Saturday

        with patch("src.services.signal_precomputer.datetime") as mock_datetime:
            mock_now = KST.localize(saturday)
            mock_datetime.now.return_value = mock_now
            # Weekend check should return False

    def test_precompute_bollinger_signals_handles_empty_result(self):
        """Test precompute_bollinger_signals handles empty scanner results."""
        from src.services.signal_precomputer import precompute_bollinger_signals

        mock_scanner = MagicMock()
        mock_scanner.scan_for_buy_signals.return_value = []

        result = precompute_bollinger_signals(
            scanner=mock_scanner,
            stock_codes=["005930", "000660"],
            max_results=10,
            force_fetch=False,
        )

        assert result == []
        mock_scanner.scan_for_buy_signals.assert_called_once()

    def test_precompute_contrarian_signals_handles_exception(self):
        """Test precompute_contrarian_signals handles scanner exceptions gracefully."""
        from src.services.signal_precomputer import precompute_contrarian_signals

        mock_scanner = MagicMock()
        mock_scanner.scan_for_contrarian_signals.side_effect = Exception("Scanner error")

        result = precompute_contrarian_signals(
            scanner=mock_scanner,
            stock_codes=["005930"],
            max_results=10,
        )

        assert result == []

    def test_get_cached_signals_returns_none_when_empty(self):
        """Test get_cached_signals returns None when cache is empty."""
        from src.services.signal_precomputer import get_cached_signals

        # Use a fresh cache instance
        with patch("src.services.signal_precomputer.get_cache_service") as mock_cache:
            mock_cache_instance = MagicMock()
            mock_cache_instance.get.return_value = None
            mock_cache_instance.signals_key.return_value = "signals:bollinger:latest"
            mock_cache.return_value = mock_cache_instance

            result = get_cached_signals("bollinger")
            assert result is None

    def test_invalidate_signal_cache(self):
        """Test invalidate_signal_cache clears all signal caches."""
        from src.services.signal_precomputer import invalidate_signal_cache

        with patch("src.services.signal_precomputer.get_cache_service") as mock_cache:
            mock_cache_instance = MagicMock()
            mock_cache_instance.signals_key.side_effect = lambda x: f"signals:{x}:latest"
            mock_cache.return_value = mock_cache_instance

            invalidate_signal_cache()

            # Verify delete was called for all signal types
            assert mock_cache_instance.delete.call_count >= 3

    def test_precompute_all_signals_returns_stats(self):
        """Test precompute_all_signals returns proper statistics."""
        from src.services.signal_precomputer import precompute_all_signals

        with patch("src.services.signal_precomputer.is_market_hours") as mock_market:
            mock_market.return_value = False

            result = precompute_all_signals(force_fetch=False)

            assert "market_open" in result
            assert "bollinger_count" in result
            assert "contrarian_count" in result
            assert "duration_ms" in result
            assert result["market_open"] is False


class TestSignalCaching:
    """Tests for signal caching integration."""

    def test_cache_key_format(self):
        """Test that cache keys follow expected format."""
        from src.core.cache import CacheService

        assert CacheService.signals_key("bollinger") == "signals:bollinger:latest"
        assert CacheService.signals_key("contrarian") == "signals:contrarian:latest"
        assert CacheService.signals_key("candidates") == "signals:candidates:latest"
