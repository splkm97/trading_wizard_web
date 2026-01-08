"""User settings service."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from src.models.user_settings import UserSettings
from src.core.exceptions import NotFoundError
from src.core.logging import logger


class SettingsService:
    """Service for managing user settings."""

    def __init__(self, db: Session):
        self.db = db

    def get_settings(self, user_id: str) -> UserSettings:
        """
        Get user settings. Creates default settings if not exists.

        Args:
            user_id: User ID

        Returns:
            UserSettings model
        """
        settings = self.db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

        if not settings:
            # Create default settings
            settings = UserSettings(
                user_id=user_id,
                max_positions=15,
                max_position_pct=Decimal("10.00"),
                stop_loss_pct=Decimal("4.50"),
                confidence_threshold=50,
                take_profit_enabled=True,
                take_profit_pct=Decimal("9.00"),
                take_profit_ratio=Decimal("1.00"),
                bollinger_period=12,
                bollinger_std_dev=Decimal("1.3"),
                squeeze_threshold_pct=55,
                squeeze_lookback_days=10,
                expansion_threshold_pct=Decimal("20.00"),
                band_touch_tolerance=Decimal("0.0010"),
                trading_days_per_year=252,
                days_per_year=365,
            )
            self.db.add(settings)
            self.db.commit()
            logger.info(f"Created default settings for user {user_id}")

        return settings

    def update_settings(
        self,
        user_id: str,
        # Risk Management
        max_positions: Optional[int] = None,
        max_position_pct: Optional[float] = None,
        stop_loss_pct: Optional[float] = None,
        confidence_threshold: Optional[int] = None,
        # Take Profit Settings
        take_profit_enabled: Optional[bool] = None,
        take_profit_pct: Optional[float] = None,
        take_profit_ratio: Optional[float] = None,
        # Bollinger Band Parameters
        bollinger_period: Optional[int] = None,
        bollinger_std_dev: Optional[float] = None,
        # Squeeze Detection
        squeeze_threshold_pct: Optional[int] = None,
        squeeze_lookback_days: Optional[int] = None,
        # Advanced Squeeze Settings
        expansion_threshold_pct: Optional[float] = None,
        band_touch_tolerance: Optional[float] = None,
        # Metrics Configuration
        trading_days_per_year: Optional[int] = None,
        days_per_year: Optional[int] = None,
    ) -> tuple[UserSettings, list[dict]]:
        """
        Update user settings.

        Args:
            user_id: User ID
            max_positions: Max number of positions (1-50)
            max_position_pct: Max position percentage (1-100)
            stop_loss_pct: Stop loss percentage (1-50)
            confidence_threshold: Confidence threshold (0-100)
            take_profit_enabled: Enable/disable take profit
            take_profit_pct: Take profit target percentage (5-50)
            take_profit_ratio: Partial sell ratio (0.1-1.0)
            bollinger_period: Bollinger period (5-200)
            bollinger_std_dev: Standard deviation multiplier (0-5)
            squeeze_threshold_pct: Squeeze threshold percentage (5-100)
            squeeze_lookback_days: Lookback days (2-30)
            expansion_threshold_pct: Expansion threshold percentage (5-100)
            band_touch_tolerance: Band touch tolerance (0-0.01)
            trading_days_per_year: Trading days per year (200-365)
            days_per_year: Calendar days per year (360-366)

        Returns:
            Tuple of (updated settings, constitution warnings)
        """
        settings = self.get_settings(user_id)

        # Risk Management
        if max_positions is not None:
            if max_positions < 1 or max_positions > 50:
                raise ValueError("max_positions must be between 1 and 50")
            settings.max_positions = max_positions

        if max_position_pct is not None:
            if max_position_pct < 1 or max_position_pct > 100:
                raise ValueError("max_position_pct must be between 1 and 100")
            settings.max_position_pct = Decimal(str(max_position_pct))

        if stop_loss_pct is not None:
            if stop_loss_pct < 1 or stop_loss_pct > 50:
                raise ValueError("stop_loss_pct must be between 1 and 50")
            settings.stop_loss_pct = Decimal(str(stop_loss_pct))

        if confidence_threshold is not None:
            if confidence_threshold < 0 or confidence_threshold > 100:
                raise ValueError("confidence_threshold must be between 0 and 100")
            settings.confidence_threshold = confidence_threshold

        # Take Profit Settings
        if take_profit_enabled is not None:
            settings.take_profit_enabled = take_profit_enabled

        if take_profit_pct is not None:
            if take_profit_pct < 5 or take_profit_pct > 50:
                raise ValueError("take_profit_pct must be between 5 and 50")
            settings.take_profit_pct = Decimal(str(take_profit_pct))

        if take_profit_ratio is not None:
            if take_profit_ratio < 0.1 or take_profit_ratio > 1.0:
                raise ValueError("take_profit_ratio must be between 0.1 and 1.0")
            settings.take_profit_ratio = Decimal(str(take_profit_ratio))

        # Bollinger Band Parameters
        if bollinger_period is not None:
            if bollinger_period < 5 or bollinger_period > 200:
                raise ValueError("bollinger_period must be between 5 and 200")
            settings.bollinger_period = bollinger_period

        if bollinger_std_dev is not None:
            if bollinger_std_dev <= 0 or bollinger_std_dev > 5:
                raise ValueError("bollinger_std_dev must be between 0 and 5")
            settings.bollinger_std_dev = Decimal(str(bollinger_std_dev))

        # Squeeze Detection
        if squeeze_threshold_pct is not None:
            if squeeze_threshold_pct < 5 or squeeze_threshold_pct > 100:
                raise ValueError("squeeze_threshold_pct must be between 5 and 100")
            settings.squeeze_threshold_pct = squeeze_threshold_pct

        if squeeze_lookback_days is not None:
            if squeeze_lookback_days < 2 or squeeze_lookback_days > 30:
                raise ValueError("squeeze_lookback_days must be between 2 and 30")
            settings.squeeze_lookback_days = squeeze_lookback_days

        # Advanced Squeeze Settings
        if expansion_threshold_pct is not None:
            if expansion_threshold_pct < 5 or expansion_threshold_pct > 100:
                raise ValueError("expansion_threshold_pct must be between 5 and 100")
            settings.expansion_threshold_pct = Decimal(str(expansion_threshold_pct))

        if band_touch_tolerance is not None:
            if band_touch_tolerance < 0 or band_touch_tolerance > 0.01:
                raise ValueError("band_touch_tolerance must be between 0 and 0.01")
            settings.band_touch_tolerance = Decimal(str(band_touch_tolerance))

        # Metrics Configuration
        if trading_days_per_year is not None:
            if trading_days_per_year < 200 or trading_days_per_year > 365:
                raise ValueError("trading_days_per_year must be between 200 and 365")
            settings.trading_days_per_year = trading_days_per_year

        if days_per_year is not None:
            if days_per_year < 360 or days_per_year > 366:
                raise ValueError("days_per_year must be between 360 and 366")
            settings.days_per_year = days_per_year

        self.db.commit()

        # Check Constitution III compliance
        warnings = settings.check_constitution_compliance()
        if warnings:
            logger.warning(f"Constitution III warnings for user {user_id}: {warnings}")

        return settings, warnings
