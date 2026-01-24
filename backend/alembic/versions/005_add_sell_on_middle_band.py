"""Add sell_on_middle_band column

Revision ID: 005
Revises: 004
Create Date: 2025-01-08
"""

import sqlalchemy as sa

from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user_settings",
        sa.Column("sell_on_middle_band", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column("user_settings", "sell_on_middle_band")
