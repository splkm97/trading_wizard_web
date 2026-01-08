"""Initial tables for User, UserSettings, Portfolio, Position, Trade, BacktestResult

Revision ID: 001
Revises:
Create Date: 2026-01-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('public_key', sa.Text(), nullable=False, unique=True),
        sa.Column('fingerprint', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('nickname', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
    )

    # User settings table
    op.create_table(
        'user_settings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), unique=True, nullable=False),
        sa.Column('max_positions', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('max_position_pct', sa.Numeric(5, 2), nullable=False, server_default='10.00'),
        sa.Column('stop_loss_pct', sa.Numeric(5, 2), nullable=False, server_default='5.00'),
        sa.Column('confidence_threshold', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), unique=True, nullable=False),
        sa.Column('initial_capital', sa.Numeric(15, 2), nullable=False, server_default='1000000'),
        sa.Column('cash_balance', sa.Numeric(15, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Positions table
    op.create_table(
        'positions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('portfolio_id', sa.String(36), sa.ForeignKey('portfolios.id'), nullable=False),
        sa.Column('stock_code', sa.String(6), nullable=False),
        sa.Column('stock_name', sa.String(100), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('avg_entry_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('first_entry_date', sa.Date(), nullable=False),
        sa.Column('entry_reason', sa.String(50), nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('portfolio_id', 'stock_code', name='uq_position_portfolio_stock'),
    )
    op.create_index('idx_position_portfolio', 'positions', ['portfolio_id'])

    # Trades table
    op.create_table(
        'trades',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('portfolio_id', sa.String(36), sa.ForeignKey('portfolios.id'), nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('stock_code', sa.String(6), nullable=False),
        sa.Column('stock_name', sa.String(100), nullable=False),
        sa.Column('action', sa.String(4), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(12, 2), nullable=False),
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('realized_pnl', sa.Numeric(15, 2), nullable=True),
        sa.Column('reason', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_trade_portfolio_date', 'trades', ['portfolio_id', 'trade_date'])
    op.create_index('idx_trade_stock', 'trades', ['stock_code'])

    # Backtest results table
    op.create_table(
        'backtest_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('stock_list_name', sa.String(50), nullable=False),
        sa.Column('initial_capital', sa.Numeric(15, 2), nullable=False),
        sa.Column('final_value', sa.Numeric(15, 2), nullable=False),
        sa.Column('total_return_pct', sa.Numeric(8, 4), nullable=False),
        sa.Column('max_drawdown_pct', sa.Numeric(8, 4), nullable=False),
        sa.Column('total_trades', sa.Integer(), nullable=False),
        sa.Column('winning_trades', sa.Integer(), nullable=False),
        sa.Column('win_rate_pct', sa.Numeric(6, 2), nullable=False),
        sa.Column('result_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_backtest_user_created', 'backtest_results', ['user_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_backtest_user_created', 'backtest_results')
    op.drop_table('backtest_results')
    op.drop_index('idx_trade_stock', 'trades')
    op.drop_index('idx_trade_portfolio_date', 'trades')
    op.drop_table('trades')
    op.drop_index('idx_position_portfolio', 'positions')
    op.drop_table('positions')
    op.drop_table('portfolios')
    op.drop_table('user_settings')
    op.drop_table('users')
