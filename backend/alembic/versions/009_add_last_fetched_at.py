"""Add last_fetched_at column to historical_prices

Revision ID: 009
Revises: 008
Create Date: 2026-01-12

Adds last_fetched_at column to track when yfinance data was last fetched.
Used for rate limiting yfinance API calls (30-minute interval).
"""

import sqlalchemy as sa

from alembic import op

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "historical_prices",
        sa.Column("last_fetched_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("historical_prices", "last_fetched_at")
