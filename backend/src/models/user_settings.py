"""UserSettings model for strategy parameters."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class UserSettings(BaseModel):
    """User strategy settings."""

    __tablename__ = "user_settings"

    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)

    max_positions = Column(Integer, nullable=False, default=15)
    max_position_pct = Column(Numeric(5, 2), nullable=False, default=10.00)
    stop_loss_pct = Column(Numeric(5, 2), nullable=False, default=4.50)
    confidence_threshold = Column(Integer, nullable=False, default=55)

    take_profit_enabled = Column(Boolean, nullable=False, default=True)
    take_profit_pct = Column(Numeric(5, 2), nullable=False, default=12.00)
    take_profit_ratio = Column(Numeric(3, 2), nullable=False, default=1.00)

    sell_on_middle_band = Column(Boolean, nullable=False, default=False)

    bollinger_period = Column(Integer, nullable=False, default=15)
    bollinger_std_dev = Column(Numeric(3, 1), nullable=False, default=1.5)

    squeeze_threshold_pct = Column(Integer, nullable=False, default=60)
    squeeze_lookback_days = Column(Integer, nullable=False, default=10)

    expansion_threshold_pct = Column(Numeric(5, 2), nullable=False, default=20.00)
    band_touch_tolerance = Column(Numeric(5, 4), nullable=False, default=0.0010)

    trading_days_per_year = Column(Integer, nullable=False, default=252)
    days_per_year = Column(Integer, nullable=False, default=365)

    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="settings")

    def check_constitution_compliance(self) -> list[dict]:
        warnings = []

        if float(self.stop_loss_pct) < 5.0:
            warnings.append(
                {
                    "field": "stop_loss_pct",
                    "message": "Constitution III recommends stop_loss_pct >= 5%",
                    "recommended_value": 5.0,
                }
            )

        if float(self.max_position_pct) > 10.0:
            warnings.append(
                {
                    "field": "max_position_pct",
                    "message": "Constitution III recommends max_position_pct <= 10%",
                    "recommended_value": 10.0,
                }
            )

        if self.max_positions > 15:
            warnings.append(
                {
                    "field": "max_positions",
                    "message": "Constitution III recommends max_positions <= 15",
                    "recommended_value": 15,
                }
            )

        return warnings

    def __repr__(self):
        return f"<UserSettings(max_positions={self.max_positions}, stop_loss_pct={self.stop_loss_pct})>"

    def to_backtest_config_dict(self) -> dict:
        return {
            "max_positions": self.max_positions,
            "max_position_percent": float(self.max_position_pct),
            "stop_loss_percent": float(self.stop_loss_pct),
            "bollinger_period": self.bollinger_period,
            "bollinger_std_dev": float(self.bollinger_std_dev),
            "squeeze_threshold_percent": self.squeeze_threshold_pct,
            "squeeze_lookback_days": self.squeeze_lookback_days,
            "take_profit": {
                "enabled": self.take_profit_enabled,
                "target_pct": float(self.take_profit_pct),
                "ratio": float(self.take_profit_ratio),
            },
            "squeeze_advanced": {
                "expansion_threshold_percent": float(self.expansion_threshold_pct),
                "band_touch_tolerance": float(self.band_touch_tolerance),
            },
            "metrics": {
                "trading_days_per_year": self.trading_days_per_year,
                "days_per_year": self.days_per_year,
            },
        }
