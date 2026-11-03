"""Nhan dang chu (OCR): Windows OCR co san trong Win10/11, hoac Tesseract."""
import asyncio

from PIL import Image

from .textproc import _fix_cjk_spaces, join_lines as _join_lines  # noqa: F401


def _lines(lines) -> str:
    """Tra ve cac dong tho, moi dong cach nhau boi \\n (lam sach / noi dong o textproc)."""
    return "\n".join(_fix_cjk_spaces(ln).strip() for ln in lines if ln and ln.strip())


# Ten goi OCR cua Windows (Features on Demand) theo ngon ngu
OCR_CAPABILITY = {"en": "en-US", "ja": "ja-JP", "zh-hans": "zh-CN", "zh-hant": "zh-TW", "zh": "zh-CN",
                  "ko": "ko-KR", "ru": "ru-RU", "fr": "fr-FR", "de": "de-DE", "es": "es-ES",
                  "pt": "pt-BR", "it": "it-IT"}


def capability_name(tag: str):
    """'ja' -> 'Language.OCR~~~ja-JP~0.0.1.0'; None neu Windows khong co OCR cho ngon ngu nay."""
    t = tag.lower()
    key = "zh-hans" if t.startswith("zh-hans") else "zh-hant" if t.startswith("zh-hant") else t.split("-")[0]
    region = OCR_CAPABILITY.get(key)
    return f"Language.OCR~~~{region}~0.0.1.0" if region else None


def resolve_windows_lang(tag: str):
    """Ngon ngu Windows OCR dung duoc cho tag: dung tag neu da cai, khong thi mot goi cung
    ngon ngu khac vung (vd. can en-US ma may co en-GB). None neu chua cai goi nao."""
    from winrt.windows.globalization import Language
    from winrt.windows.media.ocr import OcrEngine
    if OcrEngine.is_language_supported(Language(tag)):
        return tag
    base = tag.lower().split("-")[0]
    script = "hant" if "hant" in tag.lower() else "hans" if "hans" in tag.lower() else ""
    for lang in OcrEngine.available_recognizer_languages:
        t = lang.language_tag.lower()
        if t.split("-")[0] == base and (not script or script in t or base != "zh"):
            return lang.language_tag
    return None


class OcrLanguageMissing(Exception):
    """Windows chua cai goi nhan dang chu cho ngon ngu nay."""

    def __init__(self, tag: str):
        super().__init__(f"Windows OCR language pack missing: {tag}")
        self.tag = tag
        self.capability = capability_name(tag)


async def _await(op):
    return await op


class WindowsOcr:
    """Goi thang Windows.Media.Ocr (thu vien winocr bao loi sai ngon ngu va lap lai moi lan doc)."""

    def __init__(self, lang: str):
        from winrt.windows.globalization import Language
        from winrt.windows.media.ocr import OcrEngine
        tag = resolve_windows_lang(lang)
        if not tag:
            raise OcrLanguageMissing(lang)
        self.lang = tag
        self.engine = OcrEngine.try_create_from_language(Language(tag))
        if self.engine is None:
            raise OcrLanguageMissing(lang)

    def recognize(self, img: Image.Image) -> str:
        from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
        from winrt.windows.storage.streams import DataWriter
        img = img.convert("RGBA")
        writer = DataWriter()
        writer.write_bytes(img.tobytes())
        bitmap = SoftwareBitmap.create_copy_from_buffer(writer.detach_buffer(), BitmapPixelFormat.RGBA8,
                                                        img.width, img.height)
        result = asyncio.run(_await(self.engine.recognize_async(bitmap)))
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
