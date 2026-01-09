"""Add recommendation cache columns and historical prices table

Revision ID: 007
Revises: 006
Create Date: 2026-01-09

Adds:
- cached_recommendations and cached_recommendations_date columns to game_sessions
- recommendation_cache table for pre-computed recommendations
- historical_prices table for local stock price data (performance optimization)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # Add recommendation cache columns to game_sessions (if not exist)
    if not column_exists("game_sessions", "cached_recommendations"):
        op.add_column(
            "game_sessions",
            sa.Column("cached_recommendations", sa.Text(), nullable=True),
        )
    if not column_exists("game_sessions", "cached_recommendations_date"):
        op.add_column(
            "game_sessions",
            sa.Column("cached_recommendations_date", sa.Date(), nullable=True),
        )

    # Create recommendation_cache table (if not exists)
    if not table_exists("recommendation_cache"):
        op.create_table(
            "recommendation_cache",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "session_id",
                sa.String(36),
                sa.ForeignKey("game_sessions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("target_date", sa.Date(), nullable=False),
            sa.Column("recommendations_json", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("session_id", "target_date", name="uq_cache_session_date"),
        )
        op.create_index(
            "idx_cache_session_date", "recommendation_cache", ["session_id", "target_date"]
        )

    # Create historical_prices table for local stock data cache (if not exists)
    if not table_exists("historical_prices"):
        op.create_table(
            "historical_prices",
            sa.Column("stock_code", sa.String(10), nullable=False),
            sa.Column("date", sa.String(10), nullable=False),  # ISO format YYYY-MM-DD
            sa.Column("open", sa.Float(), nullable=False),
            sa.Column("high", sa.Float(), nullable=False),
            sa.Column("low", sa.Float(), nullable=False),
            sa.Column("close", sa.Float(), nullable=False),
            sa.Column("volume", sa.BigInteger(), nullable=False),
            sa.PrimaryKeyConstraint("stock_code", "date"),
        )
        op.create_index("ix_historical_prices_date", "historical_prices", ["date"])
        op.create_index(
            "ix_historical_prices_stock_date", "historical_prices", ["stock_code", "date"]
        )


def downgrade() -> None:
    # Drop historical_prices table
    if table_exists("historical_prices"):
        op.drop_index("ix_historical_prices_stock_date", "historical_prices")
        op.drop_index("ix_historical_prices_date", "historical_prices")
        op.drop_table("historical_prices")

    # Drop recommendation_cache table
    if table_exists("recommendation_cache"):
        op.drop_index("idx_cache_session_date", "recommendation_cache")
        op.drop_table("recommendation_cache")

    # Drop game_sessions columns
    if column_exists("game_sessions", "cached_recommendations_date"):
        op.drop_column("game_sessions", "cached_recommendations_date")
    if column_exists("game_sessions", "cached_recommendations"):
        op.drop_column("game_sessions", "cached_recommendations")
