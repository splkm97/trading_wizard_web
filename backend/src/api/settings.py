"""Settings API endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.auth.middleware import get_current_user
from src.models.user import User
from src.services.settings_service import SettingsService
from src.core.logging import logger

router = APIRouter(prefix="/settings", tags=["Settings"])


class SettingsResponse(BaseModel):
    """User settings response."""

    # Risk Management
    max_positions: int
    max_position_pct: float
    stop_loss_pct: float
    confidence_threshold: int

    # Take Profit Settings
    take_profit_enabled: bool
    take_profit_pct: float
    take_profit_ratio: float

    # Bollinger Band Parameters
    bollinger_period: int
    bollinger_std_dev: float

    # Squeeze Detection
    squeeze_threshold_pct: int
    squeeze_lookback_days: int

    # Advanced Squeeze Settings
    expansion_threshold_pct: float
    band_touch_tolerance: float

    # Metrics Configuration
    trading_days_per_year: int
    days_per_year: int

    class Config:
        from_attributes = True


class SettingsUpdateRequest(BaseModel):
    """Request to update settings."""

    # Risk Management
    max_positions: Optional[int] = Field(None, ge=1, le=50, description="Max positions (1-50)")
    max_position_pct: Optional[float] = Field(None, ge=1, le=100, description="Max position % (1-100)")
    stop_loss_pct: Optional[float] = Field(None, ge=1, le=50, description="Stop loss % (1-50)")
    confidence_threshold: Optional[int] = Field(None, ge=0, le=100, description="Confidence threshold (0-100)")

    # Take Profit Settings
    take_profit_enabled: Optional[bool] = Field(None, description="Enable take profit")
    take_profit_pct: Optional[float] = Field(None, ge=5, le=50, description="Take profit target % (5-50)")
    take_profit_ratio: Optional[float] = Field(None, ge=0.1, le=1.0, description="Partial sell ratio (0.1-1.0)")

    # Bollinger Band Parameters
    bollinger_period: Optional[int] = Field(None, ge=5, le=200, description="Bollinger period (5-200)")
    bollinger_std_dev: Optional[float] = Field(None, gt=0, le=5, description="Std dev multiplier (0-5)")

    # Squeeze Detection
    squeeze_threshold_pct: Optional[int] = Field(None, ge=5, le=100, description="Squeeze threshold % (5-100)")
    squeeze_lookback_days: Optional[int] = Field(None, ge=2, le=30, description="Lookback days (2-30)")

    # Advanced Squeeze Settings
    expansion_threshold_pct: Optional[float] = Field(None, ge=5, le=100, description="Expansion threshold % (5-100)")
    band_touch_tolerance: Optional[float] = Field(None, ge=0, le=0.01, description="Band touch tolerance (0-0.01)")

    # Metrics Configuration
    trading_days_per_year: Optional[int] = Field(None, ge=200, le=365, description="Trading days per year (200-365)")
    days_per_year: Optional[int] = Field(None, ge=360, le=366, description="Calendar days per year (360-366)")


class ConstitutionWarning(BaseModel):
    """Constitution III warning."""

    field: str
    message: str
    recommended_value: float


class SettingsUpdateResponse(BaseModel):
    """Response for settings update with warnings."""

    settings: SettingsResponse
    warnings: list[ConstitutionWarning]


@router.get("", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user settings."""
    settings_service = SettingsService(db)
    settings = settings_service.get_settings(current_user.id)

    return SettingsResponse(
        # Risk Management
        max_positions=settings.max_positions,
        max_position_pct=float(settings.max_position_pct),
        stop_loss_pct=float(settings.stop_loss_pct),
        confidence_threshold=settings.confidence_threshold,
        # Take Profit Settings
        take_profit_enabled=settings.take_profit_enabled,
        take_profit_pct=float(settings.take_profit_pct),
        take_profit_ratio=float(settings.take_profit_ratio),
        # Bollinger Band Parameters
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


@router.put("", response_model=SettingsUpdateResponse)
async def update_settings(
    request: SettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update user settings.

    Returns updated settings along with any Constitution III warnings.
    """
    try:
        settings_service = SettingsService(db)
        settings, warnings = settings_service.update_settings(
            user_id=current_user.id,
            # Risk Management
            max_positions=request.max_positions,
            max_position_pct=request.max_position_pct,
            stop_loss_pct=request.stop_loss_pct,
            confidence_threshold=request.confidence_threshold,
            # Take Profit Settings
            take_profit_enabled=request.take_profit_enabled,
            take_profit_pct=request.take_profit_pct,
            take_profit_ratio=request.take_profit_ratio,
            # Bollinger Band Parameters
            bollinger_period=request.bollinger_period,
            bollinger_std_dev=request.bollinger_std_dev,
            # Squeeze Detection
            squeeze_threshold_pct=request.squeeze_threshold_pct,
            squeeze_lookback_days=request.squeeze_lookback_days,
            # Advanced Squeeze Settings
            expansion_threshold_pct=request.expansion_threshold_pct,
            band_touch_tolerance=request.band_touch_tolerance,
            # Metrics Configuration
            trading_days_per_year=request.trading_days_per_year,
            days_per_year=request.days_per_year,
        )

        return SettingsUpdateResponse(
            settings=SettingsResponse(
                # Risk Management
                max_positions=settings.max_positions,
                max_position_pct=float(settings.max_position_pct),
                stop_loss_pct=float(settings.stop_loss_pct),
                confidence_threshold=settings.confidence_threshold,
                # Take Profit Settings
                take_profit_enabled=settings.take_profit_enabled,
                take_profit_pct=float(settings.take_profit_pct),
                take_profit_ratio=float(settings.take_profit_ratio),
                # Bollinger Band Parameters
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
            ),
            warnings=[
                ConstitutionWarning(
                    field=w["field"],
                    message=w["message"],
                    recommended_value=w["recommended_value"],
                )
                for w in warnings
            ],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
