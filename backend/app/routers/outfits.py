import logging
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.clothing_item import ClothingItem
from app.models.outfit_suggestion import OutfitSuggestion
from app.models.user import User
from app.schemas.clothing import ClothingItemResponse
from app.schemas.outfit import OutfitSuggestionResponse, RateOutfitRequest
from app.services import claude_service, minio_service, weather_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/outfits", tags=["outfits"])


def _item_response(item: ClothingItem) -> ClothingItemResponse:
    image_url = None
    if item.image_key:
        try:
            image_url = minio_service.get_presigned_url(item.image_key)
        except Exception:
            pass
    data = ClothingItemResponse.model_validate(item)
    data.image_url = image_url
    return data


def _suggestion_response(suggestion: OutfitSuggestion, details: list[ClothingItemResponse] | None = None) -> OutfitSuggestionResponse:
    data = OutfitSuggestionResponse.model_validate(suggestion)
    data.clothing_details = details
    return data


@router.get("/suggest", response_model=OutfitSuggestionResponse)
async def suggest_outfit(
    for_date: date = Query(default_factory=date.today),
    occasion: str = Query("casual"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check cache
    cached = await db.execute(
        select(OutfitSuggestion).where(
            OutfitSuggestion.user_id == current_user.id,
            OutfitSuggestion.suggested_date == for_date,
            OutfitSuggestion.occasion_tag == occasion,
        )
    )
    existing = cached.scalar_one_or_none()
    if existing:
        # Auto-evict cached failures (empty items) so the AI is retried
        if not existing.items:
            await db.delete(existing)
            await db.commit()
        else:
            item_ids = [uuid.UUID(i) if isinstance(i, str) else i for i in existing.items]
            details = await _fetch_item_details(item_ids, current_user.id, db)
            return _suggestion_response(existing, details)

    # Fetch weather
    try:
        weather = await weather_service.get_weather_for_date(current_user.city, current_user.country_code, for_date)
    except Exception:
        logger.warning("Weather fetch failed, using defaults", exc_info=True)
        weather = {
            "temp_c": 20.0, "feels_like_c": 20.0, "description": "unknown",
            "icon_code": "01d", "humidity": 50, "wind_kph": 0.0,
            "temp_f": 68.0, "feels_like_f": 68.0, "wind_mph": 0.0,
        }

    # Fetch active wardrobe
    items_result = await db.execute(
        select(ClothingItem).where(
            ClothingItem.user_id == current_user.id,
            ClothingItem.is_active == True,
        )
    )
    wardrobe = items_result.scalars().all()

    if not wardrobe:
        raise HTTPException(status_code=400, detail="No clothing items in wardrobe. Upload some items first.")

    wardrobe_payload = [
        {
            "id": str(item.id),
            "category": item.category,
            "subcategory": item.subcategory,
            "primary_color": item.primary_color,
            "style_tags": item.style_tags or [],
            "season_tags": item.season_tags or [],
            "warmth_level": item.warmth_level or 3,
        }
        for item in wardrobe
    ]

    suggestion_data = await claude_service.suggest_outfit(weather, wardrobe_payload, occasion)

    # Don't cache failed suggestions — return an error so the frontend shows a retry button
    if "error" in suggestion_data or not suggestion_data.get("items"):
        logger.warning(
            "Outfit suggestion failed for user=%s, occasion=%s: %s",
            current_user.id, occasion, suggestion_data.get("error", "empty items"),
        )
        raise HTTPException(
            status_code=502,
            detail=suggestion_data.get("reasoning", "Could not generate outfit suggestion. Please try again."),
        )

    # Validate returned UUIDs against actual wardrobe
    wardrobe_ids = {str(item.id) for item in wardrobe}
    selected_ids = [i for i in suggestion_data.get("items", []) if i in wardrobe_ids]

    suggestion = OutfitSuggestion(
        user_id=current_user.id,
        suggested_date=for_date,
        weather_snapshot=weather,
        items=selected_ids,
        reasoning=suggestion_data.get("reasoning"),
        occasion_tag=occasion,
    )
    db.add(suggestion)
    await db.commit()
    await db.refresh(suggestion)

    item_ids = [uuid.UUID(i) for i in selected_ids]
    details = await _fetch_item_details(item_ids, current_user.id, db)
    return _suggestion_response(suggestion, details)


async def _fetch_item_details(
    item_ids: list[uuid.UUID], user_id: uuid.UUID, db: AsyncSession
) -> list[ClothingItemResponse]:
    if not item_ids:
        return []
    result = await db.execute(
        select(ClothingItem).where(
            ClothingItem.id.in_(item_ids),
            ClothingItem.user_id == user_id,
        )
    )
    items = result.scalars().all()
    return [_item_response(i) for i in items]


@router.get("/", response_model=list[OutfitSuggestionResponse])
async def list_suggestions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OutfitSuggestion)
        .where(OutfitSuggestion.user_id == current_user.id)
        .order_by(OutfitSuggestion.suggested_date.desc())
        .offset(offset)
        .limit(limit)
    )
    suggestions = result.scalars().all()
    return [_suggestion_response(s) for s in suggestions]


@router.get("/{suggestion_id}", response_model=OutfitSuggestionResponse)
async def get_suggestion(
    suggestion_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OutfitSuggestion).where(
            OutfitSuggestion.id == suggestion_id,
            OutfitSuggestion.user_id == current_user.id,
        )
    )
    suggestion = result.scalar_one_or_none()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    item_ids = [uuid.UUID(i) if isinstance(i, str) else i for i in (suggestion.items or [])]
    details = await _fetch_item_details(item_ids, current_user.id, db)
    return _suggestion_response(suggestion, details)


@router.post("/{suggestion_id}/rate", response_model=OutfitSuggestionResponse)
async def rate_suggestion(
    suggestion_id: uuid.UUID,
    body: RateOutfitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not 1 <= body.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    result = await db.execute(
        select(OutfitSuggestion).where(
            OutfitSuggestion.id == suggestion_id,
            OutfitSuggestion.user_id == current_user.id,
        )
    )
    suggestion = result.scalar_one_or_none()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    suggestion.user_rating = body.rating
    await db.commit()
    await db.refresh(suggestion)
    return _suggestion_response(suggestion)
