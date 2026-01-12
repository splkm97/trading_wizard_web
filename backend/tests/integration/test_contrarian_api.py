"""Integration tests for the Contrarian Strategy API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.contrarian import router as contrarian_router
from src.auth.middleware import get_current_user
from src.db.database import get_db
from src.models.user import User
from src.models.user_settings import UserSettings
from src.wizard.signal_scanner import StockSignal


# Create a test app without database dependencies
def create_test_app():
    """Create a FastAPI app for testing without database initialization."""
    test_app = FastAPI()
    test_app.include_router(contrarian_router)
    return test_app


@pytest.fixture
def mock_user():
    """Create a mock user for authentication."""
    user = MagicMock(spec=User)
    user.id = "test-user-id-12345678"
    user.fingerprint = "a" * 64
    user.nickname = "TestUser"
    return user


@pytest.fixture
def mock_user_settings(mock_user):
    """Create mock user settings with MACD/RSI contrarian settings."""
    settings = MagicMock(spec=UserSettings)
    settings.user_id = mock_user.id

    # Bollinger settings
    settings.bollinger_period = 15
    settings.bollinger_std_dev = 1.5
    settings.squeeze_threshold_pct = 60
    settings.squeeze_lookback_days = 10

    # MACD/RSI contrarian settings
    settings.macd_rsi_rsi_period = 14
    settings.macd_rsi_rsi_threshold = 30.0
    settings.macd_rsi_macd_fast_period = 12
    settings.macd_rsi_macd_slow_period = 26
    settings.macd_rsi_macd_signal_period = 9
    settings.macd_rsi_confidence_threshold = 40.0

    return settings


@pytest.fixture
def mock_db_session(mock_user_settings):
    """Create a mock database session."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_user_settings
    return db


@pytest.fixture
def test_app():
    """Create test FastAPI app."""
    return create_test_app()


@pytest.fixture
def client(test_app, mock_user, mock_db_session):
    """Create a test client with mocked dependencies."""

    def override_get_current_user():
        return mock_user

    def override_get_db():
        yield mock_db_session

    test_app.dependency_overrides[get_current_user] = override_get_current_user
    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as test_client:
        yield test_client

    # Clean up overrides
    test_app.dependency_overrides.clear()


@pytest.fixture
def mock_contrarian_signals():
    """Create mock contrarian signals for testing."""
    return [
        StockSignal(
            stock_code="005930",
            stock_name="Samsung Electronics",
            signal_type="BUY",
            confidence_score=75.5,
            current_price=65000.0,
            reason="macd_rsi_contrarian",
            indicators={
                "rsi": 25.5,
                "macd": 0.5,
                "macd_signal": 0.3,
                "macd_histogram": 0.2,
            },
        ),
        StockSignal(
            stock_code="000660",
            stock_name="SK Hynix",
            signal_type="BUY",
            confidence_score=68.2,
            current_price=125000.0,
            reason="macd_rsi_contrarian",
            indicators={
                "rsi": 28.0,
                "macd": 0.8,
                "macd_signal": 0.5,
                "macd_histogram": 0.3,
            },
        ),
    ]


class TestContrarianSignalsEndpoint:
    """Tests for GET /contrarian/signals endpoint."""

    def test_get_contrarian_signals_success(self, client, mock_contrarian_signals):
        """Test successful retrieval of contrarian signals."""
        with (
            patch(
                "src.api.contrarian.load_kospi_top100",
                return_value=["005930", "000660", "035420"],
            ),
            patch(
                "src.api.contrarian.SignalScanner.scan_for_contrarian_signals",
                return_value=mock_contrarian_signals,
            ),
        ):
            response = client.get("/contrarian/signals")

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "signals" in data
            assert "scanned_count" in data
            assert "signal_count" in data
            assert "applied_settings" in data

            # Verify signals data
            assert len(data["signals"]) == 2
            assert data["signal_count"] == 2
            assert data["scanned_count"] == 3

            # Verify first signal structure
            first_signal = data["signals"][0]
            assert first_signal["stock_code"] == "005930"
            assert first_signal["stock_name"] == "Samsung Electronics"
            assert first_signal["signal_type"] == "BUY"
            assert first_signal["confidence_score"] == 75.5
            assert first_signal["current_price"] == 65000.0
            assert first_signal["reason"] == "macd_rsi_contrarian"

            # Verify indicators structure
            assert "indicators" in first_signal
            assert first_signal["indicators"]["rsi"] == 25.5
            assert first_signal["indicators"]["macd"] == 0.5
            assert first_signal["indicators"]["macd_signal"] == 0.3
            assert first_signal["indicators"]["macd_histogram"] == 0.2

    def test_applied_settings_in_response(self, client, mock_contrarian_signals):
        """Test that applied_settings is present and correct in response."""
        with (
            patch(
                "src.api.contrarian.load_kospi_top100",
                return_value=["005930"],
            ),
            patch(
                "src.api.contrarian.SignalScanner.scan_for_contrarian_signals",
                return_value=mock_contrarian_signals[:1],
            ),
        ):
            response = client.get("/contrarian/signals")

            assert response.status_code == 200
            data = response.json()

            # Verify applied_settings exists
            assert "applied_settings" in data

            # Verify applied_settings structure
            applied_settings = data["applied_settings"]
            assert "rsi_period" in applied_settings
            assert "rsi_threshold" in applied_settings
            assert "macd_fast_period" in applied_settings
            assert "macd_slow_period" in applied_settings
            assert "macd_signal_period" in applied_settings
            assert "confidence_threshold" in applied_settings

            # Verify applied_settings values match mock user settings
            assert applied_settings["rsi_period"] == 14
            assert applied_settings["rsi_threshold"] == 30.0
            assert applied_settings["macd_fast_period"] == 12
            assert applied_settings["macd_slow_period"] == 26
            assert applied_settings["macd_signal_period"] == 9
            assert applied_settings["confidence_threshold"] == 40.0

    def test_empty_signals_response_when_no_matches(self, client):
        """Test response when no contrarian signals match criteria."""
        with (
            patch(
                "src.api.contrarian.load_kospi_top100",
                return_value=["005930", "000660", "035420", "051910", "006400"],
            ),
            patch(
                "src.api.contrarian.SignalScanner.scan_for_contrarian_signals",
                return_value=[],
            ),
        ):
            response = client.get("/contrarian/signals")

            assert response.status_code == 200
            data = response.json()

            # Verify empty signals
            assert data["signals"] == []
            assert data["signal_count"] == 0
            assert data["scanned_count"] == 5

            # applied_settings should still be present
            assert "applied_settings" in data
            assert data["applied_settings"]["rsi_period"] == 14

    def test_max_results_query_parameter(self, client, mock_contrarian_signals):
        """Test max_results query parameter limits returned signals."""
        with (
            patch(
                "src.api.contrarian.load_kospi_top100",
                return_value=["005930", "000660"],
            ),
            patch(
                "src.api.contrarian.SignalScanner.scan_for_contrarian_signals",
                return_value=mock_contrarian_signals[:1],
            ) as mock_scan,
        ):
            response = client.get("/contrarian/signals?max_results=5")

            assert response.status_code == 200

            # Verify max_results was passed to scanner
            mock_scan.assert_called_once()
            call_kwargs = mock_scan.call_args[1]
            assert call_kwargs["max_results"] == 5

    def test_max_results_validation_min(self, client):
        """Test max_results validation rejects values below minimum."""
        response = client.get("/contrarian/signals?max_results=0")
        assert response.status_code == 422  # Validation error

    def test_max_results_validation_max(self, client):
        """Test max_results validation rejects values above maximum."""
        response = client.get("/contrarian/signals?max_results=51")
        assert response.status_code == 422  # Validation error

    def test_fallback_stock_codes_when_file_not_found(self, client):
        """Test fallback to default stock codes when kospi_top100.txt not found."""
        with (
            patch(
                "src.api.contrarian.load_kospi_top100",
                side_effect=FileNotFoundError("File not found"),
            ),
            patch(
                "src.api.contrarian.SignalScanner.scan_for_contrarian_signals",
                return_value=[],
            ),
        ):
            response = client.get("/contrarian/signals")

            assert response.status_code == 200
            data = response.json()

            # Should use fallback stock codes (5 stocks)
            assert data["scanned_count"] == 5


class TestContrarianEndpointAuthentication:
    """Tests for authentication on contrarian endpoints."""

    def test_unauthenticated_request_returns_401(self):
        """Test that unauthenticated requests return 401 Unauthorized."""
        test_app = create_test_app()
        with TestClient(test_app) as unauthenticated_client:
            response = unauthenticated_client.get("/contrarian/signals")
            # Endpoint requires authentication - returns 401 or 403 depending on auth scheme
            assert response.status_code in [401, 403]


class TestContrarianEndpointWithDefaultSettings:
    """Tests for contrarian endpoint when user has no custom settings."""

    def test_default_settings_when_no_user_settings(self, mock_user):
        """Test that default settings are used when user has no settings."""
        test_app = create_test_app()

        mock_db = MagicMock()
        # Return None for user settings query
        mock_db.query.return_value.filter.return_value.first.return_value = None

        def override_get_current_user():
            return mock_user

        def override_get_db():
            yield mock_db

        test_app.dependency_overrides[get_current_user] = override_get_current_user
        test_app.dependency_overrides[get_db] = override_get_db

        try:
            with (
                TestClient(test_app) as test_client,
                patch(
                    "src.api.contrarian.load_kospi_top100",
                    return_value=["005930"],
                ),
                patch(
                    "src.api.contrarian.SignalScanner.scan_for_contrarian_signals",
                    return_value=[],
                ),
            ):
                response = test_client.get("/contrarian/signals")

                assert response.status_code == 200
                data = response.json()

                # Verify default settings are used
                applied_settings = data["applied_settings"]
                assert applied_settings["rsi_period"] == 14
                assert applied_settings["rsi_threshold"] == 30.0
                assert applied_settings["macd_fast_period"] == 12
                assert applied_settings["macd_slow_period"] == 26
                assert applied_settings["macd_signal_period"] == 9
                assert applied_settings["confidence_threshold"] == 40.0
        finally:
            test_app.dependency_overrides.clear()


class TestContrarianSettingsUpdate:
    """Tests to verify settings persist and apply to scans."""

    def test_updated_settings_persist_and_apply_to_scan(self, mock_user):
        """Test that updated contrarian settings persist and apply to subsequent scans."""
        test_app = create_test_app()

        # Create mock settings with custom values
        custom_settings = MagicMock(spec=UserSettings)
        custom_settings.user_id = mock_user.id

        # Custom MACD/RSI contrarian settings (different from defaults)
        custom_settings.macd_rsi_rsi_period = 10
        custom_settings.macd_rsi_rsi_threshold = 25.0
        custom_settings.macd_rsi_macd_fast_period = 8
        custom_settings.macd_rsi_macd_slow_period = 21
        custom_settings.macd_rsi_macd_signal_period = 7
        custom_settings.macd_rsi_confidence_threshold = 50.0

        # Bollinger settings (required for SignalScanner)
        custom_settings.bollinger_period = 15
        custom_settings.bollinger_std_dev = 1.5
        custom_settings.squeeze_threshold_pct = 60
        custom_settings.squeeze_lookback_days = 10

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = custom_settings

        def override_get_current_user():
            return mock_user

        def override_get_db():
            yield mock_db

        test_app.dependency_overrides[get_current_user] = override_get_current_user
        test_app.dependency_overrides[get_db] = override_get_db

        try:
            with (
                TestClient(test_app) as test_client,
                patch(
                    "src.api.contrarian.load_kospi_top100",
                    return_value=["005930"],
                ),
                patch(
                    "src.api.contrarian.SignalScanner.scan_for_contrarian_signals",
                    return_value=[],
                ) as mock_scan,
            ):
                response = test_client.get("/contrarian/signals")

                assert response.status_code == 200
                data = response.json()

                # Verify custom settings are applied
                applied_settings = data["applied_settings"]
                assert applied_settings["rsi_period"] == 10
                assert applied_settings["rsi_threshold"] == 25.0
                assert applied_settings["macd_fast_period"] == 8
                assert applied_settings["macd_slow_period"] == 21
                assert applied_settings["macd_signal_period"] == 7
                assert applied_settings["confidence_threshold"] == 50.0

                # Verify the scanner was called with custom threshold settings
                mock_scan.assert_called_once()
                call_kwargs = mock_scan.call_args[1]
                assert call_kwargs["rsi_threshold"] == 25.0
                assert call_kwargs["confidence_threshold"] == 50.0
        finally:
            test_app.dependency_overrides.clear()

    def test_settings_changes_affect_signal_filtering(self, mock_user, mock_contrarian_signals):
        """Test that changing confidence_threshold affects which signals are returned."""
        test_app = create_test_app()

        # Low threshold settings - should include more signals
        low_threshold_settings = MagicMock(spec=UserSettings)
        low_threshold_settings.user_id = mock_user.id
        low_threshold_settings.macd_rsi_rsi_period = 14
        low_threshold_settings.macd_rsi_rsi_threshold = 30.0
        low_threshold_settings.macd_rsi_macd_fast_period = 12
        low_threshold_settings.macd_rsi_macd_slow_period = 26
        low_threshold_settings.macd_rsi_macd_signal_period = 9
        low_threshold_settings.macd_rsi_confidence_threshold = 30.0  # Low threshold
        low_threshold_settings.bollinger_period = 15
        low_threshold_settings.bollinger_std_dev = 1.5
        low_threshold_settings.squeeze_threshold_pct = 60
        low_threshold_settings.squeeze_lookback_days = 10

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = low_threshold_settings

        def override_get_current_user():
            return mock_user

        def override_get_db():
            yield mock_db

        test_app.dependency_overrides[get_current_user] = override_get_current_user
        test_app.dependency_overrides[get_db] = override_get_db

        try:
            with (
                TestClient(test_app) as test_client,
                patch(
                    "src.api.contrarian.load_kospi_top100",
                    return_value=["005930", "000660"],
                ),
                patch(
                    "src.api.contrarian.SignalScanner.scan_for_contrarian_signals",
                    return_value=mock_contrarian_signals,  # Return both signals
                ) as mock_scan,
            ):
                response = test_client.get("/contrarian/signals")

                assert response.status_code == 200
                data = response.json()

                # Verify the low threshold was passed to scanner
                mock_scan.assert_called_once()
                call_kwargs = mock_scan.call_args[1]
                assert call_kwargs["confidence_threshold"] == 30.0

                # Both signals should be returned with low threshold
                assert data["signal_count"] == 2
                assert data["applied_settings"]["confidence_threshold"] == 30.0
        finally:
            test_app.dependency_overrides.clear()

    def test_rsi_threshold_affects_scan_parameters(self, mock_user):
        """Test that RSI threshold setting is correctly passed to the scanner."""
        test_app = create_test_app()

        # Custom RSI settings
        custom_settings = MagicMock(spec=UserSettings)
        custom_settings.user_id = mock_user.id
        custom_settings.macd_rsi_rsi_period = 20
        custom_settings.macd_rsi_rsi_threshold = 20.0  # Very strict RSI threshold
        custom_settings.macd_rsi_macd_fast_period = 12
        custom_settings.macd_rsi_macd_slow_period = 26
        custom_settings.macd_rsi_macd_signal_period = 9
        custom_settings.macd_rsi_confidence_threshold = 40.0
        custom_settings.bollinger_period = 15
        custom_settings.bollinger_std_dev = 1.5
        custom_settings.squeeze_threshold_pct = 60
        custom_settings.squeeze_lookback_days = 10

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = custom_settings

        def override_get_current_user():
            return mock_user

        def override_get_db():
            yield mock_db

        test_app.dependency_overrides[get_current_user] = override_get_current_user
        test_app.dependency_overrides[get_db] = override_get_db

        try:
            with (
                TestClient(test_app) as test_client,
                patch(
                    "src.api.contrarian.load_kospi_top100",
                    return_value=["005930"],
                ),
                patch(
                    "src.api.contrarian.SignalScanner.scan_for_contrarian_signals",
                    return_value=[],
                ) as mock_scan,
            ):
                response = test_client.get("/contrarian/signals")

                assert response.status_code == 200
                data = response.json()

                # Verify custom RSI threshold was applied
                assert data["applied_settings"]["rsi_period"] == 20
                assert data["applied_settings"]["rsi_threshold"] == 20.0

                # Verify scanner received custom RSI threshold
                mock_scan.assert_called_once()
                call_kwargs = mock_scan.call_args[1]
                assert call_kwargs["rsi_threshold"] == 20.0
        finally:
            test_app.dependency_overrides.clear()

    def test_settings_isolation_between_users(self, mock_user):
        """Test that different users can have different contrarian settings."""
        test_app = create_test_app()

        # User 1 settings
        user1_settings = MagicMock(spec=UserSettings)
        user1_settings.user_id = mock_user.id
        user1_settings.macd_rsi_rsi_period = 14
        user1_settings.macd_rsi_rsi_threshold = 30.0
        user1_settings.macd_rsi_macd_fast_period = 12
        user1_settings.macd_rsi_macd_slow_period = 26
        user1_settings.macd_rsi_macd_signal_period = 9
        user1_settings.macd_rsi_confidence_threshold = 40.0
        user1_settings.bollinger_period = 15
        user1_settings.bollinger_std_dev = 1.5
        user1_settings.squeeze_threshold_pct = 60
        user1_settings.squeeze_lookback_days = 10

        # User 2 with different settings
        user2 = MagicMock(spec=User)
        user2.id = "user-2-different-id"
        user2.fingerprint = "b" * 64
        user2.nickname = "User2"

        user2_settings = MagicMock(spec=UserSettings)
        user2_settings.user_id = user2.id
        user2_settings.macd_rsi_rsi_period = 7
        user2_settings.macd_rsi_rsi_threshold = 40.0  # Different from user1
        user2_settings.macd_rsi_macd_fast_period = 6
        user2_settings.macd_rsi_macd_slow_period = 13
        user2_settings.macd_rsi_macd_signal_period = 5
        user2_settings.macd_rsi_confidence_threshold = 60.0  # Different from user1
        user2_settings.bollinger_period = 20
        user2_settings.bollinger_std_dev = 2.0
        user2_settings.squeeze_threshold_pct = 50
        user2_settings.squeeze_lookback_days = 15

        # Test with user1
        mock_db1 = MagicMock()
        mock_db1.query.return_value.filter.return_value.first.return_value = user1_settings

        def override_get_user1():
            return mock_user

        def override_get_db1():
            yield mock_db1

        test_app.dependency_overrides[get_current_user] = override_get_user1
        test_app.dependency_overrides[get_db] = override_get_db1

        try:
            with (
                TestClient(test_app) as test_client,
                patch(
                    "src.api.contrarian.load_kospi_top100",
                    return_value=["005930"],
                ),
                patch(
                    "src.api.contrarian.SignalScanner.scan_for_contrarian_signals",
                    return_value=[],
                ),
            ):
                response1 = test_client.get("/contrarian/signals")
                assert response1.status_code == 200
                data1 = response1.json()

                # Verify user1 settings
                assert data1["applied_settings"]["rsi_threshold"] == 30.0
                assert data1["applied_settings"]["confidence_threshold"] == 40.0
        finally:
            test_app.dependency_overrides.clear()

        # Now test with user2
        mock_db2 = MagicMock()
        mock_db2.query.return_value.filter.return_value.first.return_value = user2_settings

        def override_get_user2():
            return user2

        def override_get_db2():
            yield mock_db2

        test_app.dependency_overrides[get_current_user] = override_get_user2
        test_app.dependency_overrides[get_db] = override_get_db2

        try:
            with (
                TestClient(test_app) as test_client,
                patch(
                    "src.api.contrarian.load_kospi_top100",
                    return_value=["005930"],
                ),
                patch(
                    "src.api.contrarian.SignalScanner.scan_for_contrarian_signals",
                    return_value=[],
                ),
            ):
                response2 = test_client.get("/contrarian/signals")
                assert response2.status_code == 200
                data2 = response2.json()

                # Verify user2 has different settings
                assert data2["applied_settings"]["rsi_threshold"] == 40.0
                assert data2["applied_settings"]["confidence_threshold"] == 60.0
                assert data2["applied_settings"]["macd_fast_period"] == 6
                assert data2["applied_settings"]["macd_slow_period"] == 13
        finally:
            test_app.dependency_overrides.clear()
