"""recommendation_items.label: метка скоринга, посчитанная matcher'ом

Revision ID: 0007_rec_item_label
Revises: 0006_missing_scenarios
Create Date: 2026-11-21 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007_rec_item_label"
down_revision = "0006_missing_scenarios"
branch_labels = None
depends_on = None

SCHEMA = "core"


def upgrade() -> None:
    op.add_column(
        "recommendation_items",
        sa.Column("label", sa.String(16), nullable=True),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_column("recommendation_items", "label", schema=SCHEMA)