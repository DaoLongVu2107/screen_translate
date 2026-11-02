"""Nhan dang chu (OCR): Windows OCR co san trong Win10/11, hoac Tesseract."""
import asyncio
import re

from PIL import Image

_CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af\uff00-\uffef]")


def _join_lines(lines: list[str]) -> str:
    lines = [ln.strip() for ln in lines if ln.strip()]
    if not lines:
        return ""
    text = lines[0]
    for ln in lines[1:]:
        if text.endswith("-") and not text.endswith("--"):
            text = text[:-1] + ln          # noi tu bi ngat dong: "trans-" + "late"
        elif _CJK.search(text[-1:]) or _CJK.search(ln[:1]):
            text += ln                     # tieng Trung/Nhat khong dung dau cach
        else:
            text += " " + ln
    return text


def _fix_cjk_spaces(line: str) -> str:
    # Windows OCR chen dau cach giua tung chu Han/Kana -> bo di
    return re.sub(r"(?<=[\u3040-\u30ff\u3400-\u9fff\uff00-\uffef]) (?=[\u3040-\u30ff\u3400-\u9fff\uff00-\uffef])", "", line)


class WindowsOcr:
    def __init__(self, lang: str):
        import winocr  # noqa: F401  (bao loi som neu chua cai)
        self.lang = lang

    def recognize(self, img: Image.Image) -> str:
        import winocr
        result = asyncio.run(winocr.recognize_pil(img.convert("RGBA"), self.lang))
        lines = [_fix_cjk_spaces(line.text) for line in result.lines]
        return _join_lines(lines)


class TesseractOcr:
    def __init__(self, cmd: str, lang: str):
        import pytesseract
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
        self.lang = lang

    def recognize(self, img: Image.Image) -> str:
        import pytesseract
        raw = pytesseract.image_to_string(img.convert("L"), lang=self.lang)
        return _join_lines(_fix_cjk_spaces(ln) for ln in raw.splitlines())


def create(cfg: dict):
    if cfg["ocr_engine"] == "tesseract":
        return TesseractOcr(cfg["tesseract_cmd"], cfg["tesseract_lang"])
    return WindowsOcr(cfg["ocr_lang"])
