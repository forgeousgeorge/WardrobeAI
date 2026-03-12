import base64
import json
import re
import time

import httpx

from app.config import settings

_client = None  # anthropic.Anthropic, lazily imported

CLASSIFICATION_PROMPT = """You are a fashion classification assistant.
Analyze the clothing item in this photo and respond with ONLY a JSON object.
No markdown, no explanation, no code fences. JSON keys required:
{
  "category": "top|bottom|outerwear|shoes|accessory|full_outfit|unknown",
  "subcategory": "string (e.g. dress shirt, jeans, sneakers)",
  "primary_color": "string",
  "secondary_colors": ["string"],
  "pattern": "solid|striped|plaid|floral|graphic|abstract|animal_print|none",
  "silhouette": "string (e.g. slim-fit, relaxed, oversized, cropped, A-line, fitted, boxy)",
  "style_tags": ["casual|formal|sporty|business|outdoor|evening|beach|loungewear|streetwear"],
  "occasion_tags": ["everyday|office|gym|date|party|beach|hiking|formal_event|travel"],
  "season_tags": ["spring|summer|fall|winter"],
  "temp_range_c": {"min": 10, "max": 25},
  "warmth_level": 1,
  "confidence": 0.95
}
warmth_level: 1=very light (>28°C), 2=light (22-28°C), 3=medium (15-22°C), 4=warm (5-15°C), 5=very warm (<5°C).
temp_range_c: estimated comfortable temperature range in Celsius for wearing this item."""

LOCAL_CLASSIFICATION_PROMPT = """Output ONLY valid JSON starting with { as the very first character. No text before or after. No markdown. No code fences.

You are a fashion classification assistant. Analyze the clothing item in this photo and return a JSON object with these exact keys:
{
  "category": "top|bottom|outerwear|shoes|accessory|full_outfit|unknown",
  "subcategory": "string (e.g. dress shirt, jeans, sneakers)",
  "primary_color": "string",
  "secondary_colors": ["string"],
  "pattern": "solid|striped|plaid|floral|graphic|abstract|animal_print|none",
  "silhouette": "string (e.g. slim-fit, relaxed, oversized, cropped, A-line, fitted, boxy)",
  "style_tags": ["casual|formal|sporty|business|outdoor|evening|beach|loungewear|streetwear"],
  "occasion_tags": ["everyday|office|gym|date|party|beach|hiking|formal_event|travel"],
  "season_tags": ["spring|summer|fall|winter"],
  "temp_range_c": {"min": 10, "max": 25},
  "warmth_level": 1,
  "confidence": 0.95
}
warmth_level: 1=very light (>28°C), 2=light (22-28°C), 3=medium (15-22°C), 4=warm (5-15°C), 5=very warm (<5°C).
temp_range_c: estimated comfortable temperature range in Celsius for wearing this item."""

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
        _client = anthropic.Anthropic(api_key=settings.claude_api_key)
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


def _classify_local(image_bytes: bytes, media_type: str) -> dict:
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    payload = {
        "model": settings.vision_model,
        "prompt": LOCAL_CLASSIFICATION_PROMPT,
        "images": [b64],
        "stream": False,
        "options": {"temperature": 0.1},
    }
    for attempt in range(3):
        try:
            resp = httpx.post(
                f"{settings.ollama_host}/api/generate",
                json=payload,
                timeout=300.0,
            )
            resp.raise_for_status()
            data = _repair_json(resp.json()["response"])
            for key, default in _CLASSIFICATION_DEFAULTS.items():
                data.setdefault(key, default)
            return data
        except (json.JSONDecodeError, KeyError, ValueError):
            if attempt == 2:
                raise
            time.sleep(1)


def _suggest_local(weather: dict, items: list[dict], occasion: str) -> dict:
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
        "model": settings.vision_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.4},
    }
    for attempt in range(3):
        try:
            resp = httpx.post(
                f"{settings.ollama_host}/api/generate",
                json=payload,
                timeout=120.0,
            )
            resp.raise_for_status()
            return _repair_json(resp.json()["response"])
        except (json.JSONDecodeError, KeyError, ValueError):
            if attempt == 2:
                raise
            time.sleep(1)


def classify_image(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    """Classify a clothing item image. Routes to local Ollama or Claude based on vision_backend setting."""
    if settings.vision_backend == "local":
        try:
            return _classify_local(image_bytes, media_type)
        except Exception as exc:
            return {"error": str(exc), "category": "unknown", "confidence": 0.0}

    client = _get_client()
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    try:
        message = client.messages.create(
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
        return _extract_json(raw_text)
    except Exception as exc:
        return {"error": str(exc), "category": "unknown", "confidence": 0.0}


def suggest_outfit(weather: dict, items: list[dict], occasion: str = "casual") -> dict:
    """Suggest an outfit given weather and wardrobe. Routes to local Ollama or Claude based on vision_backend setting."""
    if settings.vision_backend == "local":
        try:
            return _suggest_local(weather, items, occasion)
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
        message = client.messages.create(
            model=settings.claude_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = message.content[0].text
        return _extract_json(raw_text)
    except Exception as exc:
        return {"error": str(exc), "items": [], "reasoning": "Could not generate suggestion."}
