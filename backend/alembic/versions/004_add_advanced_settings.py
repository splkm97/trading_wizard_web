"""Add advanced strategy settings columns

Revision ID: 004
Revises: 003
Create Date: 2025-01-07

Adds new columns for advanced backtest configuration:
- Take profit settings (target_pct, ratio)
- Bollinger Band parameters (period, std_dev)
- Squeeze detection (threshold_percent, lookback_days)
- Advanced squeeze settings (expansion_threshold_pct, band_touch_tolerance)
- Metrics configuration (trading_days_per_year, days_per_year)
"""

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    # Take Profit Settings
    op.add_column(
        "user_settings",
        sa.Column("take_profit_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "user_settings",
        sa.Column("take_profit_pct", sa.Numeric(5, 2), nullable=False, server_default="10.00"),
    )
    op.add_column(
        "user_settings",
        sa.Column("take_profit_ratio", sa.Numeric(3, 2), nullable=False, server_default="0.50"),
    )

    # Bollinger Band Parameters
    op.add_column(
        "user_settings",
        sa.Column("bollinger_period", sa.Integer(), nullable=False, server_default="20"),
    )
    op.add_column(
        "user_settings",
        sa.Column("bollinger_std_dev", sa.Numeric(3, 1), nullable=False, server_default="2.0"),
    )

    # Squeeze Detection
    op.add_column(
        "user_settings",
        sa.Column("squeeze_threshold_pct", sa.Integer(), nullable=False, server_default="30"),
    )
    op.add_column(
        "user_settings",
        sa.Column("squeeze_lookback_days", sa.Integer(), nullable=False, server_default="10"),
    )

    # Advanced Squeeze Settings
    op.add_column(
        "user_settings",
        sa.Column("expansion_threshold_pct", sa.Numeric(5, 2), nullable=False, server_default="20.00"),
    )
    op.add_column(
        "user_settings",
        sa.Column("band_touch_tolerance", sa.Numeric(5, 4), nullable=False, server_default="0.0010"),
    )

    # Metrics Configuration
    op.add_column(
        "user_settings",
        sa.Column("trading_days_per_year", sa.Integer(), nullable=False, server_default="252"),
    )
    op.add_column(
        "user_settings",
        sa.Column("days_per_year", sa.Integer(), nullable=False, server_default="365"),
    )


def downgrade():
    # Metrics Configuration
    op.drop_column("user_settings", "days_per_year")
    op.drop_column("user_settings", "trading_days_per_year")

    # Advanced Squeeze Settings
    op.drop_column("user_settings", "band_touch_tolerance")
    op.drop_column("user_settings", "expansion_threshold_pct")

    # Squeeze Detection
    op.drop_column("user_settings", "squeeze_lookback_days")
    op.drop_column("user_settings", "squeeze_threshold_pct")

    # Bollinger Band Parameters
    op.drop_column("user_settings", "bollinger_std_dev")
    op.drop_column("user_settings", "bollinger_period")

    # Take Profit Settings
    op.drop_column("user_settings", "take_profit_ratio")
    op.drop_column("user_settings", "take_profit_pct")
    op.drop_column("user_settings", "take_profit_enabled")
