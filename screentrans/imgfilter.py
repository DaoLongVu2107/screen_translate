"""Loc anh truoc khi OCR: giu chu theo mau, tang tuong phan, dao mau, lam net, den trang."""
from PIL import Image, ImageChops, ImageFilter, ImageOps

DEFAULT = {
    "text_color_on": False,     # chi giu nhung diem anh gan mau chu
    "text_color": "#FFFFFF",
    "color_tolerance": 25,      # do lech mau cho phep, tinh theo %
    "autocontrast": False,
    "invert": False,
    "sharpen": False,
    "threshold": 0,             # 0 = tat; 1..100 = chuyen den trang theo nguong %
}


def is_active(f: dict) -> bool:
    f = {**DEFAULT, **(f or {})}
    return bool(f["text_color_on"] or f["autocontrast"] or f["invert"] or f["sharpen"]
                or f["threshold"])


def _hex(c: str):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def apply(img: Image.Image, f: dict) -> Image.Image:
    f = {**DEFAULT, **(f or {})}
    if not is_active(f):
        return img
    out = img.convert("RGB")
    if f["text_color_on"]:
        # Khoang cach mau = lech lon nhat trong 3 kenh R, G, B so voi mau chu
        solid = Image.new("RGB", out.size, _hex(f["text_color"]))
        r, g, b = ImageChops.difference(out, solid).split()
        dist = ImageChops.lighter(ImageChops.lighter(r, g), b)
        tol = round(float(f["color_tolerance"]) * 255 / 100)
        out = dist.point(lambda v: 0 if v <= tol else 255)      # chu den tren nen trang
    else:
        out = out.convert("L")
    if f["invert"]:
        out = ImageOps.invert(out)
    if f["autocontrast"]:
        out = ImageOps.autocontrast(out, cutoff=1)
    if f["sharpen"]:
        out = out.filter(ImageFilter.SHARPEN)
    if f["threshold"]:
        t = round(float(f["threshold"]) * 255 / 100)
        out = out.point(lambda v: 255 if v > t else 0)
    return out
