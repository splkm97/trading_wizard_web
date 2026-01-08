"""Add simulation game tables (GameSession, SimulatedPosition, SimulatedTrade)

Revision ID: 006
Revises: 005
Create Date: 2026-01-08

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # GameSessions table
    op.create_table(
        "game_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("current_date", sa.Date(), nullable=False),
        sa.Column("initial_capital", sa.Numeric(15, 2), nullable=False, server_default="100000000"),
        sa.Column("cash_balance", sa.Numeric(15, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="IN_PROGRESS"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_game_session_user", "game_sessions", ["user_id"])
    op.create_index("idx_game_session_user_status", "game_sessions", ["user_id", "status"])

    # SimulatedPositions table
    op.create_table(
        "simulated_positions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("game_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stock_code", sa.String(20), nullable=False),
        sa.Column("stock_name", sa.String(100), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("avg_entry_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("session_id", "stock_code", name="uq_simulated_position_session_stock"),
    )
    op.create_index("idx_simulated_position_session", "simulated_positions", ["session_id"])

    # SimulatedTrades table
    op.create_table(
        "simulated_trades",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("game_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("stock_code", sa.String(20), nullable=False),
        sa.Column("stock_name", sa.String(100), nullable=False),
        sa.Column("action", sa.String(4), nullable=False),  # BUY or SELL
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(15, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("realized_pnl", sa.Numeric(15, 2), nullable=True),
        sa.Column("realized_pnl_pct", sa.Numeric(8, 4), nullable=True),
        sa.Column("confidence_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_simulated_trade_session", "simulated_trades", ["session_id"])
    op.create_index(
        "idx_simulated_trade_session_date", "simulated_trades", ["session_id", "trade_date"]
    )


def downgrade() -> None:
    op.drop_index("idx_simulated_trade_session_date", "simulated_trades")
    op.drop_index("idx_simulated_trade_session", "simulated_trades")
    op.drop_table("simulated_trades")
    op.drop_index("idx_simulated_position_session", "simulated_positions")
    op.drop_table("simulated_positions")
    op.drop_index("idx_game_session_user_status", "game_sessions")
    op.drop_index("idx_game_session_user", "game_sessions")
    op.drop_table("game_sessions")
