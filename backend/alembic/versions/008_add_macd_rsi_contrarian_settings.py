"""Add MACD/RSI contrarian strategy settings columns

Revision ID: 008
Revises: 007
Create Date: 2026-01-10

Adds new columns for MACD/RSI contrarian signal detection strategy:
- RSI settings (period, threshold)
- MACD settings (fast, slow, signal periods)
- Confidence threshold for contrarian signals
"""

import sqlalchemy as sa

from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade():
    # RSI Settings
    op.add_column(
        "user_settings",
        sa.Column("macd_rsi_rsi_period", sa.Integer(), nullable=False, server_default="14"),
    )
    op.add_column(
        "user_settings",
        sa.Column("macd_rsi_rsi_threshold", sa.Numeric(4, 1), nullable=False, server_default="30.0"),
    )

    # MACD Settings
    op.add_column(
        "user_settings",
        sa.Column("macd_rsi_macd_fast_period", sa.Integer(), nullable=False, server_default="12"),
    )
    op.add_column(
        "user_settings",
        sa.Column("macd_rsi_macd_slow_period", sa.Integer(), nullable=False, server_default="26"),
    )
    op.add_column(
        "user_settings",
        sa.Column("macd_rsi_macd_signal_period", sa.Integer(), nullable=False, server_default="9"),
    )

    # Confidence Threshold
    op.add_column(
        "user_settings",
        sa.Column("macd_rsi_confidence_threshold", sa.Numeric(5, 1), nullable=False, server_default="40.0"),
    )


def downgrade():
    op.drop_column("user_settings", "macd_rsi_confidence_threshold")
    op.drop_column("user_settings", "macd_rsi_macd_signal_period")
    op.drop_column("user_settings", "macd_rsi_macd_slow_period")
    op.drop_column("user_settings", "macd_rsi_macd_fast_period")
    op.drop_column("user_settings", "macd_rsi_rsi_threshold")
    op.drop_column("user_settings", "macd_rsi_rsi_period")
