"""
Standalone test for the clothing classification model.
Run from the backend/ directory:
    python test_classification.py <image_path_or_url>

If no argument is given, fetches a sample white t-shirt image from the web.
"""

import asyncio
import sys
import json
import os
import urllib.request
from pathlib import Path

# Ensure app package is importable from backend/
sys.path.insert(0, str(Path(__file__).parent))

# pydantic-settings looks for .env relative to cwd; the .env lives at project root
_project_root = Path(__file__).parent.parent
if (_project_root / ".env").exists():
    os.chdir(_project_root)

from app.services.claude_service import classify_image

SAMPLE_IMAGE_URL = "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600"

FIELDS_OF_INTEREST = [
    "category",
    "subcategory",
    "primary_color",
    "secondary_colors",
    "pattern",
    "silhouette",
    "style_tags",
    "occasion_tags",
    "season_tags",
    "temp_range_c",
    "warmth_level",
    "confidence",
]


def load_image(source: str) -> tuple[bytes, str]:
    if source.startswith("http://") or source.startswith("https://"):
        print(f"Fetching image from URL: {source}")
        req = urllib.request.Request(source, headers={"User-Agent": "WardrobeAI/1.0"})
        with urllib.request.urlopen(req) as resp:
            return resp.read(), "image/jpeg"
    else:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {source}")
        suffix = path.suffix.lower()
        media_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
        media_type = media_types.get(suffix, "image/jpeg")
        return path.read_bytes(), media_type


async def main():
    source = sys.argv[1] if len(sys.argv) > 1 else SAMPLE_IMAGE_URL
    image_bytes, media_type = load_image(source)
    print(f"Image loaded: {len(image_bytes):,} bytes  ({media_type})\n")

    print("Calling Claude Vision classification...")
    result = await classify_image(image_bytes, media_type)

    if "error" in result:
        print(f"\nERROR: {result['error']}")
        sys.exit(1)

    print("\n=== Classification Result ===\n")
    for field in FIELDS_OF_INTEREST:
        value = result.get(field, "<not returned>")
        print(f"  {field:<20} {json.dumps(value)}")

    extra_keys = set(result) - set(FIELDS_OF_INTEREST)
    if extra_keys:
        print(f"\n  (extra keys returned: {', '.join(sorted(extra_keys))})")

    print("\n=== Raw JSON ===\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
