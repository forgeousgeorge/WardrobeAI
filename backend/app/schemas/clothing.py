from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class ClothingItemResponse(BaseModel):
    id: UUID
    user_id: UUID
    image_url: str | None = None
    category: str
    subcategory: str | None
    primary_color: str | None
    secondary_colors: list[str] | None
    style_tags: list[str] | None
    season_tags: list[str] | None
    warmth_level: int | None
    brand: str | None
    notes: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ClothingItemUpdate(BaseModel):
    brand: str | None = None
    notes: str | None = None
    style_tags: list[str] | None = None
    season_tags: list[str] | None = None
    category: str | None = None
    subcategory: str | None = None
