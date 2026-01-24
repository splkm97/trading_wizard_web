"""Add partial_take_profit_executed column to positions table

Revision ID: 002
Revises: 001
Create Date: 2026-01-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add partial_take_profit_executed boolean column to positions table.

    This field tracks whether a position has already executed a partial
    take-profit sell, preventing re-triggering on subsequent scans.
    Default is False for existing positions.
    """
    op.add_column(
        "positions",
        sa.Column(
            "partial_take_profit_executed", sa.Boolean(), nullable=False, server_default="false"
        ),
    )


def downgrade() -> None:
    """Remove partial_take_profit_executed column from positions table."""
    op.drop_column("positions", "partial_take_profit_executed")
