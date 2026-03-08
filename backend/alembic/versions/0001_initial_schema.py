"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100)),
        sa.Column("city", sa.String(100)),
        sa.Column("country_code", sa.String(2)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "clothing_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_key", sa.String(512), nullable=False),
        sa.Column("category", sa.String(50), server_default="unknown"),
        sa.Column("subcategory", sa.String(100)),
        sa.Column("primary_color", sa.String(50)),
        sa.Column("secondary_colors", postgresql.JSONB),
        sa.Column("style_tags", postgresql.JSONB),
        sa.Column("season_tags", postgresql.JSONB),
        sa.Column("warmth_level", sa.Integer),
        sa.Column("brand", sa.String(100)),
        sa.Column("notes", sa.Text),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("classification_raw", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_clothing_user_id", "clothing_items", ["user_id"])
    op.create_index("ix_clothing_user_category", "clothing_items", ["user_id", "category"])

    op.create_table(
        "outfit_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("suggested_date", sa.Date, nullable=False),
        sa.Column("weather_snapshot", postgresql.JSONB),
        sa.Column("items", postgresql.JSONB),
        sa.Column("reasoning", sa.Text),
        sa.Column("occasion_tag", sa.String(50)),
        sa.Column("user_rating", sa.SmallInteger),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_outfit_user_date", "outfit_suggestions", ["user_id", "suggested_date"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("outfit_suggestions")
    op.drop_table("clothing_items")
    op.drop_table("users")
