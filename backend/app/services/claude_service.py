import asyncio
import base64
import json
import re

import httpx

from app.config import settings

_client = None  # anthropic.Anthropic, lazily imported

CLASSIFICATION_PROMPT = """You are a fashion classification assistant.
Analyze the clothing item in this photo and respond with ONLY a JSON object.
No markdown, no explanation, no code fences.

Return a JSON object with these exact keys:
- "category": one of: top, bottom, outerwear, shoes, accessory, full_outfit, unknown
- "subcategory": descriptive string such as "dress shirt", "jeans", "sneakers", or null
- "primary_color": dominant color as a simple color name, or null
- "secondary_colors": array of additional color names, or empty array []
- "pattern": one of: solid, striped, plaid, floral, graphic, abstract, animal_print, none
- "silhouette": fit descriptor such as "slim-fit", "relaxed", "oversized", "cropped", "A-line", "fitted", "boxy", or null
- "style_tags": array chosen from: casual, formal, sporty, business, outdoor, evening, beach, loungewear, streetwear
- "occasion_tags": array chosen from: everyday, office, gym, date, party, beach, hiking, formal_event, travel
- "season_tags": array chosen from: spring, summer, fall, winter
- "temp_range_c": object with "min" and "max" integer fields representing the comfortable wearing temperature range in Celsius — reason from the fabric weight, coverage, and material visible in the image
- "warmth_level": integer 1–5 where 1=very light (best above 28°C), 2=light (22–28°C), 3=medium (15–22°C), 4=warm (5–15°C), 5=very warm (below 5°C)
- "confidence": float 0.0–1.0 representing your confidence in the overall classification"""

LOCAL_CLASSIFICATION_PROMPT = """Output ONLY valid JSON. Start with { as the very first character. No text before or after. No markdown. No code fences.

You are a fashion classification assistant. Analyze the clothing item in this photo.

Return a JSON object with these exact keys:
- "category": one of: top, bottom, outerwear, shoes, accessory, full_outfit, unknown
- "subcategory": descriptive string such as "dress shirt", "jeans", "sneakers", or null
- "primary_color": dominant color as a simple color name, or null
- "secondary_colors": array of additional color names, or empty array []
- "pattern": one of: solid, striped, plaid, floral, graphic, abstract, animal_print, none
- "silhouette": fit descriptor such as "slim-fit", "relaxed", "oversized", "cropped", "A-line", "fitted", "boxy", or null
- "style_tags": array chosen from: casual, formal, sporty, business, outdoor, evening, beach, loungewear, streetwear
- "occasion_tags": array chosen from: everyday, office, gym, date, party, beach, hiking, formal_event, travel
- "season_tags": array chosen from: spring, summer, fall, winter
- "temp_range_c": object with "min" and "max" integer fields — reason from the fabric weight, coverage, and material visible in the image to estimate comfortable wearing temperature in Celsius
- "warmth_level": integer 1–5 where 1=very light (best above 28°C), 2=light (22–28°C), 3=medium (15–22°C), 4=warm (5–15°C), 5=very warm (below 5°C)
- "confidence": float 0.0–1.0 representing your confidence in the overall classification"""

_CLASSIFICATION_DEFAULTS: dict = {
    "category": "unknown",
    "subcategory": None,
    "primary_color": None,
    "secondary_colors": [],
    "pattern": "none",
    "silhouette": None,
    "style_tags": [],
    "occasion_tags": [],
    "season_tags": [],
    "temp_range_c": {"min": 10, "max": 25},
    "warmth_level": 3,
    "confidence": 0.5,
}

_VALID_CATEGORIES = {"top", "bottom", "outerwear", "shoes", "accessory", "full_outfit", "unknown"}
_VALID_PATTERNS = {"solid", "striped", "plaid", "floral", "graphic", "abstract", "animal_print", "none"}
_VALID_STYLE_TAGS = {"casual", "formal", "sporty", "business", "outdoor", "evening", "beach", "loungewear", "streetwear"}
_VALID_OCCASION_TAGS = {"everyday", "office", "gym", "date", "party", "beach", "hiking", "formal_event", "travel"}
_VALID_SEASON_TAGS = {"spring", "summer", "fall", "winter"}


def _filter_tags(tags: object, valid_set: set) -> list[str]:
    """Normalize tag lists, splitting pipe-joined values and filtering to known entries."""
    if not isinstance(tags, list):
        return []
    result = []
    for tag in tags:
        for part in str(tag).split("|"):
            part = part.strip().lower()
            if part in valid_set and part not in result:
                result.append(part)
    return result


def _sanitize_classification(data: dict) -> dict:
    """Validate and truncate classification fields to fit DB column constraints."""
    cat = str(data.get("category", "unknown")).lower().strip()
    data["category"] = cat if cat in _VALID_CATEGORIES else "unknown"

    if data.get("subcategory"):
        data["subcategory"] = str(data["subcategory"])[:100]

    if data.get("primary_color"):
        data["primary_color"] = str(data["primary_color"])[:50]

    sc = data.get("secondary_colors", [])
    data["secondary_colors"] = [str(c)[:50] for c in sc] if isinstance(sc, list) else []

    pat = str(data.get("pattern", "none")).lower().strip()
    data["pattern"] = pat if pat in _VALID_PATTERNS else "none"

    data["style_tags"] = _filter_tags(data.get("style_tags", []), _VALID_STYLE_TAGS)
    data["occasion_tags"] = _filter_tags(data.get("occasion_tags", []), _VALID_OCCASION_TAGS)
    data["season_tags"] = _filter_tags(data.get("season_tags", []), _VALID_SEASON_TAGS)

    try:
        data["warmth_level"] = max(1, min(5, int(data.get("warmth_level", 3))))
    except (TypeError, ValueError):
        data["warmth_level"] = _CLASSIFICATION_DEFAULTS["warmth_level"]

    tr = data.get("temp_range_c", {})
    if isinstance(tr, dict):
        try:
            data["temp_range_c"] = {
                "min": int(tr.get("min", _CLASSIFICATION_DEFAULTS["temp_range_c"]["min"])),
                "max": int(tr.get("max", _CLASSIFICATION_DEFAULTS["temp_range_c"]["max"])),
            }
        except (TypeError, ValueError):
            data["temp_range_c"] = dict(_CLASSIFICATION_DEFAULTS["temp_range_c"])
    else:
        data["temp_range_c"] = dict(_CLASSIFICATION_DEFAULTS["temp_range_c"])

    return data

OUTFIT_PROMPT_TEMPLATE = """You are a personal stylist assistant.
Given the weather and available wardrobe items below, suggest a complete outfit for the occasion.
Respond with ONLY a JSON object — no markdown, no explanation.

Weather:
- Temperature: {temp_c}°C (feels like {feels_like_c}°C)
- Conditions: {description}
- Humidity: {humidity}%
- Wind: {wind_kph} km/h

Occasion: {occasion}

Available wardrobe items (JSON array):
{items_json}

Return JSON with these keys:
{{
  "items": ["uuid1", "uuid2", "uuid3"],
  "reasoning": "Brief explanation of choices",
  "occasion": "{occasion}"
}}
Select 2-5 items that form a cohesive outfit appropriate for the weather and occasion.
Only use UUIDs from the provided list."""


def _get_client():
    import anthropic  # lazy — only needed for cloud backend
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.claude_api_key)
    return _client


def _extract_json(text: str) -> dict:
    """Extract JSON from Claude response, stripping any markdown fences."""
    text = text.strip()
    # Remove markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _repair_json(text: str) -> dict:
    """Extract JSON from a local model response, tolerating extra text and fences."""
    text = text.strip()
    text = re.sub(r"```(?:json)?", "", text).strip()
    start = text.index("{")
    end = text.rindex("}") + 1
    return json.loads(text[start:end])


async def _classify_local(image_bytes: bytes, media_type: str) -> dict:
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    payload = {
        "model": settings.active_vision_model,
        "prompt": LOCAL_CLASSIFICATION_PROMPT,
        "images": [b64],
        "stream": False,
        "options": {"temperature": 0.1},
    }
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(
                    f"{settings.ollama_host}/api/generate",
                    json=payload,
                )
            resp.raise_for_status()
            data = _repair_json(resp.json()["response"])
            for key, default in _CLASSIFICATION_DEFAULTS.items():
                data.setdefault(key, default)
            return _sanitize_classification(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            if attempt == 2:
                raise
            await asyncio.sleep(1)


async def _suggest_local(weather: dict, items: list[dict], occasion: str) -> dict:
    prompt = OUTFIT_PROMPT_TEMPLATE.format(
        temp_c=weather.get("temp_c", "?"),
        feels_like_c=weather.get("feels_like_c", "?"),
        description=weather.get("description", "unknown"),
        humidity=weather.get("humidity", "?"),
        wind_kph=weather.get("wind_kph", "?"),
        occasion=occasion,
        items_json=json.dumps(items, indent=2),
    )
    payload = {
        "model": settings.active_text_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.4},
    }
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{settings.ollama_host}/api/generate",
                    json=payload,
                )
            resp.raise_for_status()
            return _repair_json(resp.json()["response"])
        except (json.JSONDecodeError, KeyError, ValueError):
            if attempt == 2:
                raise
            await asyncio.sleep(1)


async def classify_image(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    """Classify a clothing item image. Routes to local Ollama or Claude based on vision_backend setting."""
    if settings.vision_backend == "local":
        try:
            return await _classify_local(image_bytes, media_type)
        except Exception as exc:
            return {"error": str(exc), "category": "unknown", "confidence": 0.0}

    client = _get_client()
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    try:
        message = await client.messages.create(
            model=settings.claude_model,
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": CLASSIFICATION_PROMPT},
                    ],
                }
            ],
        )
        raw_text = message.content[0].text
        return _sanitize_classification(_extract_json(raw_text))
    except Exception as exc:
        return {"error": str(exc), "category": "unknown", "confidence": 0.0}


async def suggest_outfit(weather: dict, items: list[dict], occasion: str = "casual") -> dict:
    """Suggest an outfit given weather and wardrobe. Routes to local Ollama or Claude based on vision_backend setting."""
    if settings.vision_backend == "local":
        try:
            return await _suggest_local(weather, items, occasion)
        except Exception as exc:
            return {"error": str(exc), "items": [], "reasoning": "Could not generate suggestion."}

    client = _get_client()
    prompt = OUTFIT_PROMPT_TEMPLATE.format(
        temp_c=weather.get("temp_c", "?"),
        feels_like_c=weather.get("feels_like_c", "?"),
        description=weather.get("description", "unknown"),
        humidity=weather.get("humidity", "?"),
        wind_kph=weather.get("wind_kph", "?"),
        occasion=occasion,
        items_json=json.dumps(items, indent=2),
    )

    try:
        message = await client.messages.create(
            model=settings.claude_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = message.content[0].text
        return _extract_json(raw_text)
    except Exception as exc:
        return {"error": str(exc), "items": [], "reasoning": "Could not generate suggestion."}
