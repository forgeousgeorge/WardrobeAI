import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, SmallInteger, Text, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OutfitSuggestion(Base):
    __tablename__ = "outfit_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    suggested_date: Mapped[date] = mapped_column(Date, nullable=False)
    weather_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    items: Mapped[list] = mapped_column(JSONB, default=list)
    reasoning: Mapped[str | None] = mapped_column(Text)
    occasion_tag: Mapped[str | None] = mapped_column(String(50))
    user_rating: Mapped[int | None] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="outfit_suggestions")
