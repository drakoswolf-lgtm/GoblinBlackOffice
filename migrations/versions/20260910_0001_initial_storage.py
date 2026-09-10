"""Create initial durable Black Office storage.

Revision ID: 20260910_0001
Revises:
Create Date: 2026-09-10
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260910_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "office_records",
        sa.Column("record_type", sa.String(length=32), nullable=False),
        sa.Column("record_id", sa.String(length=128), nullable=False),
        sa.Column("business_id", sa.String(length=128), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("record_type", "record_id"),
    )
    op.create_index(
        "ix_office_records_business_id",
        "office_records",
        ["business_id"],
        unique=False,
    )

    op.create_table(
        "ledgergut_receipts",
        sa.Column("record_id", sa.String(length=64), nullable=False),
        sa.Column("business_id", sa.String(length=128), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("record_id"),
    )
    op.create_index(
        "ix_ledgergut_receipts_business_id",
        "ledgergut_receipts",
        ["business_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ledgergut_receipts_business_id", table_name="ledgergut_receipts")
    op.drop_table("ledgergut_receipts")
    op.drop_index("ix_office_records_business_id", table_name="office_records")
    op.drop_table("office_records")
