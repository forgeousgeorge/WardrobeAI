import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ClothingItem(Base):
    __tablename__ = "clothing_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    image_key: Mapped[str] = mapped_column(String(512), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50), default="unknown")
    subcategory: Mapped[str | None] = mapped_column(String(100))
    primary_color: Mapped[str | None] = mapped_column(String(50))
    secondary_colors: Mapped[list | None] = mapped_column(JSONB)
    style_tags: Mapped[list | None] = mapped_column(JSONB)
    occasion_tags: Mapped[list | None] = mapped_column(JSONB)
    season_tags: Mapped[list | None] = mapped_column(JSONB)
    pattern: Mapped[str | None] = mapped_column(String(50))
    silhouette: Mapped[str | None] = mapped_column(String(100))
    warmth_level: Mapped[int | None] = mapped_column(Integer)
    temp_range_min: Mapped[int | None] = mapped_column(Integer)
    temp_range_max: Mapped[int | None] = mapped_column(Integer)
    brand: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    classification_raw: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="clothing_items")
