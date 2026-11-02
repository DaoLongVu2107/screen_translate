"""Nhan dang chu (OCR): Windows OCR co san trong Win10/11, hoac Tesseract."""
import asyncio

from PIL import Image

from .textproc import _fix_cjk_spaces, join_lines as _join_lines  # noqa: F401


def _lines(lines) -> str:
    """Tra ve cac dong tho, moi dong cach nhau boi \\n (lam sach / noi dong o textproc)."""
    return "\n".join(_fix_cjk_spaces(ln).strip() for ln in lines if ln and ln.strip())


class WindowsOcr:
    def __init__(self, lang: str):
        import winocr  # noqa: F401  (bao loi som neu chua cai)
        self.lang = lang

    def recognize(self, img: Image.Image) -> str:
        import winocr
        result = asyncio.run(winocr.recognize_pil(img.convert("RGBA"), self.lang))
        return _lines(line.text for line in result.lines)


class TesseractOcr:
    def __init__(self, cmd: str, lang: str):
        import pytesseract
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
        self.lang = lang

    def recognize(self, img: Image.Image) -> str:
        import pytesseract
        raw = pytesseract.image_to_string(img.convert("L"), lang=self.lang)
        return _lines(raw.splitlines())


def create(cfg: dict):
    from .config import lang_info
    _, win_lang, tess_lang, _ = lang_info(cfg["source_lang"])
    if cfg["ocr_engine"] == "tesseract":
        return TesseractOcr(cfg["tesseract_cmd"], tess_lang)
    return WindowsOcr(win_lang)
