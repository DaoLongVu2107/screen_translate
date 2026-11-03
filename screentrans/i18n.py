"""Ngon ngu giao dien: chuoi tieng Viet trong code la khoa, bang EN la ban tieng Anh.
t("...") tra ve tieng Anh khi giao dien dang la tieng Anh, khong co ban dich thi giu nguyen."""
import ctypes
import locale
import sys

from .i18n_en import EN

_lang = "vi"


def system_lang() -> str:
    """'vi' neu Windows / he thong dang dung tieng Viet, nguoc lai 'en'."""
    try:
        if sys.platform == "win32":
            return "vi" if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF == 0x2A else "en"
        loc = (locale.getlocale()[0] or "")
        return "vi" if loc.lower().startswith("vi") else "en"
    except Exception:
        return "en"


def set_lang(lang: str):
    global _lang
    _lang = system_lang() if lang in (None, "", "auto") else ("en" if lang == "en" else "vi")


def lang() -> str:
    return _lang


def t(text: str) -> str:
    if _lang == "en":
        return EN.get(text, text)
    return text
