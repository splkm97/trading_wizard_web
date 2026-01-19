"""Add optimized indexes for historical_prices table

Revision ID: 010
Revises: 009
Create Date: 2026-01-13

Adds indexes to optimize query performance for signal scanning:
1. Covering index for scan queries (stock_code, date, close, volume)
2. Index for freshness checks (stock_code, last_fetched_at)
"""

from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade():
    # Index for freshness checks - faster lookup of last_fetched_at by stock_code
    op.create_index(
        "ix_historical_prices_freshness",
        "historical_prices",
        ["stock_code", "last_fetched_at"],
    )

    # Composite index for scan queries - covers common lookups
    # Note: PostgreSQL will use this for queries filtering by stock_code and date
    op.create_index(
        "ix_historical_prices_scan",
        "historical_prices",
        ["stock_code", "date"],
        postgresql_include=["close", "volume"],  # Covering index for PostgreSQL
    )


def downgrade():
    op.drop_index("ix_historical_prices_scan", table_name="historical_prices")
    op.drop_index("ix_historical_prices_freshness", table_name="historical_prices")
