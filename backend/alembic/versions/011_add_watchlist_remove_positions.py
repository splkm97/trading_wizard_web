"""Add watchlists table and remove positions/trades tables.

Revision ID: 011
Revises: 010
Create Date: 2026-01-14 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "011"
down_revision = "010"
branch_labels = None
depends_on = "010"


def upgrade():
    # Create watchlists table
    op.create_table(
        "watchlists",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("stock_code", sa.String(6), nullable=False),
        sa.Column("stock_name", sa.String(100), nullable=False),
        sa.Column("current_price", sa.String(50), nullable=True),
        sa.Column("indicators", sa.Text(), nullable=True),
        sa.Column("recommendation_score", sa.Integer(), nullable=True),
        sa.Column("recommendation_reason", sa.String(500), nullable=True),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.Column("last_updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id", "stock_code", name="uq_watchlist_user_stock"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index
    op.create_index(
        "idx_watchlist_user_stock", "watchlists", ["user_id", "stock_code"], unique=True
    )

    # Drop old tables
    op.drop_table("trades")
    op.drop_table("positions")
    op.drop_table("portfolios")


def downgrade():
    # Recreate old tables (for rollback)
    op.create_table(
        "portfolios",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("initial_capital", sa.Numeric(15, 2), nullable=False),
        sa.Column("cash_balance", sa.Numeric(15, 2), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], unique=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Drop watchlists table
    op.drop_index("idx_watchlist_user_stock", table_name="watchlists")
    op.drop_table("watchlists")
