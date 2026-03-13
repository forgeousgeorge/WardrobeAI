"""Add occasion_tags, pattern, silhouette, temp_range columns

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-12 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clothing_items", sa.Column("occasion_tags", JSONB, nullable=True))
    op.add_column("clothing_items", sa.Column("pattern", sa.String(50), nullable=True))
    op.add_column("clothing_items", sa.Column("silhouette", sa.String(100), nullable=True))
    op.add_column("clothing_items", sa.Column("temp_range_min", sa.Integer, nullable=True))
    op.add_column("clothing_items", sa.Column("temp_range_max", sa.Integer, nullable=True))


def downgrade() -> None:
    op.drop_column("clothing_items", "occasion_tags")
    op.drop_column("clothing_items", "pattern")
    op.drop_column("clothing_items", "silhouette")
    op.drop_column("clothing_items", "temp_range_min")
    op.drop_column("clothing_items", "temp_range_max")