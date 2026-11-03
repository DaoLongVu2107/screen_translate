"""Kiem tra cai dat sai: tra ve danh sach (ten tab, loi) de to do trong cua so cai dat."""
import logging
import os
import re
import sys
from .i18n import t

log = logging.getLogger(__name__)


def windows_ocr_languages():
    """Cac ngon ngu Windows OCR da cai tren may (vd. ['en-US', 'ja'])."""
    from winrt.windows.media.ocr import OcrEngine
    return [lang.language_tag for lang in OcrEngine.available_recognizer_languages]


def _has_lang(available, tag: str) -> bool:
    base = tag.split("-")[0].lower()
    return any(a.lower() == tag.lower() or a.lower().split("-")[0] == base for a in available)


def validate(cfg: dict, deep: bool = True, hotkey_errors=None):
    from .config import LANGUAGES, lang_info
    from .translator import ENGINE_NAMES, engine_chain
    problems = []

    def add(tab, msg):
        problems.append((tab, msg))

    # Ngon ngu
    if cfg.get("source_lang") == cfg.get("target_lang"):
        add(t("Ngôn ngữ"), t("Ngôn ngữ gốc trùng với ngôn ngữ dịch sang."))
    lang_name, win_lang, tess_lang, _ = lang_info(cfg.get("source_lang", "en"))

    # May dich
    chain = engine_chain(cfg)
    missing = []
    for eng in chain:
        if eng == "deepl" and not cfg.get("deepl_api_key"):
            missing.append(eng)
        elif eng == "google_cloud" and not cfg.get("google_cloud_api_key"):
            missing.append(eng)
        elif eng in cfg.get("ai", {}) and not cfg["ai"][eng].get("api_key"):
            missing.append(eng)
    for eng in missing:
        add(t("Dịch"), t("{engine} chưa có API key nên sẽ bị bỏ qua.").format(engine=t(ENGINE_NAMES.get(eng, eng))))
    if chain and len(missing) == len(chain):
        add(t("Dịch"), t("Không còn máy dịch nào dùng được. Nhập API key hoặc thêm Google Dịch vào thứ tự."))

    # Nhan dang chu
    if cfg.get("ocr_engine") == "tesseract":
        cmd = cfg.get("tesseract_cmd") or ""
        if cmd and not os.path.isfile(cmd):
            add(t("Nhận dạng"), t("Không tìm thấy tesseract.exe ở “{cmd}”.").format(cmd=cmd))
        elif deep:
            try:
                import pytesseract
                if cmd:
                    pytesseract.pytesseract.tesseract_cmd = cmd
                if tess_lang not in pytesseract.get_languages(config=""):
                    add(t("Nhận dạng"), t("Tesseract chưa có dữ liệu cho {lang} ({code}).").format(lang=t(lang_name), code=tess_lang))
            except Exception as e:
                add(t("Nhận dạng"), t("Không chạy được Tesseract: {e}").format(e=e))
    elif deep and sys.platform == "win32":
        try:
            from .ocr import resolve_windows_lang
            if not resolve_windows_lang(win_lang):
                add(t("Nhận dạng"), t("Windows chưa cài gói nhận dạng chữ cho {lang}. Vào Settings → Time & language → "
                                     "Language & region → Add a language để thêm.").format(lang=t(lang_name)))
        except Exception as e:
            log.info("Khong kiem tra duoc ngon ngu Windows OCR: %s", e)

    # Phim tat
    used = [h for h in cfg.get("hotkeys", {}).values() if h]
    dup = sorted({h for h in used if used.count(h) > 1})
    if dup:
        add(t("Phím tắt"), t("Phím tắt bị trùng: ") + ", ".join(dup) + ".")
    for combo in hotkey_errors or []:
        add(t("Phím tắt"), t("Không đăng ký được phím {combo}, có thể app khác đang dùng.").format(combo=combo))

    # Loc anh
    flt = cfg.get("ocr_filter") or {}
    if flt.get("text_color_on") and not re.fullmatch(r"#[0-9A-Fa-f]{6}", flt.get("text_color", "")):
        add(t("Lọc ảnh"), t("Màu chữ để lọc không hợp lệ."))

    # He thong
    proxy = (cfg.get("proxy") or "").strip()
    if proxy and not re.match(r"^(https?|socks5h?)://[^\s/:]+(:\d+)?/?$", proxy):
        add(t("Hệ thống"), t("Proxy phải có dạng http://máy:cổng, ví dụ http://127.0.0.1:8080."))
    return problems
