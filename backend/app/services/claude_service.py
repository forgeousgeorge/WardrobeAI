import base64
import json
import re

import anthropic

from app.config import settings

_client: anthropic.Anthropic | None = None

CLASSIFICATION_PROMPT = """You are a fashion classification assistant.
Analyze the clothing item in this photo and respond with ONLY a JSON object.
No markdown, no explanation, no code fences. JSON keys required:
{
  "category": "top|bottom|outerwear|shoes|accessory|full_outfit|unknown",
  "subcategory": "string (e.g. dress shirt, jeans, sneakers)",
  "primary_color": "string",
  "secondary_colors": ["string"],
  "style_tags": ["casual|formal|sporty|business|outdoor|evening"],
  "season_tags": ["spring|summer|fall|winter"],
  "warmth_level": 1,
  "confidence": 0.95
}
warmth_level: 1=very light, 2=light, 3=medium, 4=warm, 5=very warm."""

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


def _get_client() -> anthropic.Anthropic:
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


def classify_image(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    """Call Claude Vision to classify a clothing item. Returns classification dict."""
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
    """Ask Claude to pick items for an outfit given weather and wardrobe."""
    client = _get_client()
    items_json = json.dumps(items, indent=2)

    prompt = OUTFIT_PROMPT_TEMPLATE.format(
        temp_c=weather.get("temp_c", "?"),
        feels_like_c=weather.get("feels_like_c", "?"),
        description=weather.get("description", "unknown"),
        humidity=weather.get("humidity", "?"),
        wind_kph=weather.get("wind_kph", "?"),
        occasion=occasion,
        items_json=items_json,
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
