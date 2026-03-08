"""Run this script once to generate placeholder PWA icons."""
from PIL import Image, ImageDraw, ImageFont
import os

for size in [192, 512]:
    img = Image.new("RGB", (size, size), color=(99, 102, 241))
    draw = ImageDraw.Draw(img)
    text = "W"
    font_size = size // 2
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - bbox[1]), text, fill="white", font=font)
    out_path = os.path.join(os.path.dirname(__file__), f"icon-{size}.png")
    img.save(out_path)
    print(f"Saved {out_path}")
