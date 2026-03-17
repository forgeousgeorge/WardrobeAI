import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from PIL import Image, ImageOps
import io
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.clothing_item import ClothingItem
from app.models.user import User
from app.schemas.clothing import ClothingItemResponse, ClothingItemUpdate
from app.services import claude_service, minio_service

router = APIRouter(prefix="/clothing", tags=["clothing"])


def _generate_name(classification: dict) -> str:
    color = classification.get("primary_color") or ""
    label = classification.get("subcategory") or classification.get("category") or "item"
    parts = [p.title() for p in [color, label] if p]
    return " ".join(parts)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}


def _ext_from_content_type(ct: str) -> str:
    mapping = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/heic": "heic"}
    return mapping.get(ct, "jpg")


def _item_to_response(item: ClothingItem) -> ClothingItemResponse:
    image_url = None
    if item.image_key:
        try:
            image_url = minio_service.get_presigned_url(item.image_key)
        except Exception:
            pass
    data = ClothingItemResponse.model_validate(item)
    data.image_url = image_url
    return data


@router.post("/upload", response_model=ClothingItemResponse, status_code=status.HTTP_201_CREATED)
async def upload_clothing(
    file: Annotated[UploadFile, File()],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content_type = file.content_type or "image/jpeg"
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")

    image_bytes = await file.read()
    if len(image_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    # Validate it's actually an image and normalize to JPEG
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        img = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        image_bytes = buf.getvalue()
        content_type = "image/jpeg"
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    item_id = uuid.uuid4()
    ext = _ext_from_content_type(content_type)

    image_key = minio_service.upload_image(current_user.id, item_id, image_bytes, content_type, ext)
    classification = await claude_service.classify_image(image_bytes, content_type)

    if "error" in classification:
        try:
            minio_service.delete_object(image_key)
        except Exception:
            pass
        raise HTTPException(
            status_code=502,
            detail=f"Classification failed: {classification['error']}. Please try again or add the item manually.",
        )

    tr = classification.get("temp_range_c") or {}
    item = ClothingItem(
        id=item_id,
        user_id=current_user.id,
        image_key=image_key,
        name=_generate_name(classification),
        category=classification.get("category", "unknown"),
        subcategory=classification.get("subcategory"),
        primary_color=classification.get("primary_color"),
        secondary_colors=classification.get("secondary_colors"),
        style_tags=classification.get("style_tags"),
        occasion_tags=classification.get("occasion_tags"),
        season_tags=classification.get("season_tags"),
        pattern=classification.get("pattern"),
        silhouette=classification.get("silhouette"),
        warmth_level=classification.get("warmth_level"),
        temp_range_min=tr.get("min"),
        temp_range_max=tr.get("max"),
        classification_raw=classification,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return _item_to_response(item)


@router.get("/", response_model=list[ClothingItemResponse])
async def list_clothing(
    category: str | None = Query(None),
    season: str | None = Query(None),
    temp_c: float | None = Query(None, description="Filter items appropriate for this temperature in Celsius"),
    is_active: bool = Query(True),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(ClothingItem).where(
        ClothingItem.user_id == current_user.id,
        ClothingItem.is_active == is_active,
    )
    if category:
        q = q.where(ClothingItem.category == category)
    if season:
        q = q.where(ClothingItem.season_tags.contains([season]))
    if temp_c is not None:
        q = q.where(
            ClothingItem.temp_range_min <= temp_c,
            ClothingItem.temp_range_max >= temp_c,
        )

    q = q.order_by(ClothingItem.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(q)
    items = result.scalars().all()
    return [_item_to_response(i) for i in items]


@router.get("/{item_id}", response_model=ClothingItemResponse)
async def get_clothing_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClothingItem).where(ClothingItem.id == item_id, ClothingItem.user_id == current_user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return _item_to_response(item)


@router.patch("/{item_id}", response_model=ClothingItemResponse)
async def update_clothing_item(
    item_id: uuid.UUID,
    body: ClothingItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClothingItem).where(ClothingItem.id == item_id, ClothingItem.user_id == current_user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)
    return _item_to_response(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clothing_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClothingItem).where(ClothingItem.id == item_id, ClothingItem.user_id == current_user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.is_active = False
    await db.commit()


@router.post("/{item_id}/archive", response_model=ClothingItemResponse)
async def toggle_archive(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClothingItem).where(ClothingItem.id == item_id, ClothingItem.user_id == current_user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.is_active = not item.is_active
    await db.commit()
    await db.refresh(item)
    return _item_to_response(item)
