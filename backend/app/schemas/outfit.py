from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel

from app.schemas.clothing import ClothingItemResponse


class WeatherSnapshot(BaseModel):
    temp_c: float
    feels_like_c: float
    description: str
    icon_code: str
    humidity: int
    wind_kph: float


class OutfitSuggestionResponse(BaseModel):
    id: UUID
    user_id: UUID
    suggested_date: date
    weather_snapshot: dict | None
    items: list[UUID]
    reasoning: str | None
    occasion_tag: str | None
    user_rating: int | None
    created_at: datetime
    clothing_details: list[ClothingItemResponse] | None = None

    model_config = {"from_attributes": True}


class RateOutfitRequest(BaseModel):
    rating: int
