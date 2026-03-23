import logging
import time
from datetime import date, datetime, timezone

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Simple in-memory TTL cache: key → (data, expiry_epoch)
_cache: dict[str, tuple[dict, float]] = {}
_TTL_SECONDS = 3600


def _cache_key(city: str, country: str, for_date: date) -> str:
    return f"{city.lower()}:{country.lower()}:{for_date.isoformat()}"


def _get_cached(key: str) -> dict | None:
    if key in _cache:
        data, expiry = _cache[key]
        if time.monotonic() < expiry:
            return data
        del _cache[key]
    return None


def _set_cached(key: str, data: dict) -> None:
    _cache[key] = (data, time.monotonic() + _TTL_SECONDS)


async def get_weather_for_date(city: str | None, country: str | None, for_date: date) -> dict:
    city = city or settings.openweather_default_city
    country = country or settings.openweather_default_country
    key = _cache_key(city, country, for_date)

    cached = _get_cached(key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{settings.openweather_base_url}/forecast",
                params={
                    "q": f"{city},{country}",
                    "appid": settings.openweather_api_key,
                    "units": "metric",
                    "cnt": 40,
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "OpenWeatherMap API error %s for %s,%s: %s",
            exc.response.status_code, city, country, exc.response.text,
        )
        raise
    except Exception as exc:
        logger.error("OpenWeatherMap request failed for %s,%s: %s", city, country, exc)
        raise

    # Find forecast entry closest to 08:00 on the requested date
    target_dt = datetime(for_date.year, for_date.month, for_date.day, 8, 0, tzinfo=timezone.utc)
    best = None
    best_delta = None

    for entry in data.get("list", []):
        entry_dt = datetime.fromtimestamp(entry["dt"], tz=timezone.utc)
        if entry_dt.date() != for_date:
            continue
        delta = abs((entry_dt - target_dt).total_seconds())
        if best_delta is None or delta < best_delta:
            best = entry
            best_delta = delta

    if not best and data.get("list"):
        best = data["list"][0]

    if not best:
        return {
            "temp_c": 20.0,
            "feels_like_c": 20.0,
            "temp_f": 68.0,
            "feels_like_f": 68.0,
            "description": "unknown",
            "icon_code": "01d",
            "humidity": 50,
            "wind_kph": 0.0,
            "wind_mph": 0.0,
        }

    temp_c = round(best["main"]["temp"], 1)
    feels_like_c = round(best["main"]["feels_like"], 1)
    wind_kph = round(best["wind"]["speed"] * 3.6, 1)

    snapshot = {
        "temp_c": temp_c,
        "feels_like_c": feels_like_c,
        "temp_f": round(temp_c * 9 / 5 + 32, 1),
        "feels_like_f": round(feels_like_c * 9 / 5 + 32, 1),
        "description": best["weather"][0]["description"],
        "icon_code": best["weather"][0]["icon"],
        "humidity": best["main"]["humidity"],
        "wind_kph": wind_kph,
        "wind_mph": round(wind_kph / 1.609, 1),
    }

    _set_cached(key, snapshot)
    return snapshot
