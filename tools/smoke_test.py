"""Kiem tra nhanh tren Windows: import duoc moi module va Windows OCR doc duoc chu."""
import sys

sys.path.insert(0, ".")
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import screentrans.app  # noqa: E402,F401
from screentrans import config, ocr  # noqa: E402

img = Image.new("RGB", (900, 120), "white")
ImageDraw.Draw(img).text((20, 30), "Hello screen translator", fill="black",
                         font=ImageFont.load_default(size=48))
text = ocr.create(config.DEFAULTS).recognize(img)
print("OCR:", repr(text))
sys.exit(0 if "translator" in text.lower() else 1)
