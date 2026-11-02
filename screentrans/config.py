"""Doc / ghi cau hinh tu config.json (tao file mac dinh neu chua co)."""
import copy
import json
import logging
import os
import sys

log = logging.getLogger(__name__)

# ma -> (ten hien thi, ngon ngu Windows OCR, ngon ngu Tesseract, ma Google)
LANGUAGES = {
    "en": ("Tiếng Anh", "en-US", "eng", "en"),
    "ja": ("Tiếng Nhật", "ja", "jpn", "ja"),
    "zh-CN": ("Tiếng Trung giản thể", "zh-Hans-CN", "chi_sim", "zh-CN"),
    "zh-TW": ("Tiếng Trung phồn thể", "zh-Hant-TW", "chi_tra", "zh-TW"),
    "ko": ("Tiếng Hàn", "ko", "kor", "ko"),
    "ru": ("Tiếng Nga", "ru", "rus", "ru"),
    "fr": ("Tiếng Pháp", "fr-FR", "fra", "fr"),
    "de": ("Tiếng Đức", "de-DE", "deu", "de"),
    "es": ("Tiếng Tây Ban Nha", "es-ES", "spa", "es"),
    "pt": ("Tiếng Bồ Đào Nha", "pt-BR", "por", "pt"),
    "it": ("Tiếng Ý", "it-IT", "ita", "it"),
    "th": ("Tiếng Thái", "th", "tha", "th"),
    "vi": ("Tiếng Việt", "vi", "vie", "vi"),
}

HOTKEY_NAMES = {
    "select_region": "Chọn vùng dịch",
    "toggle_auto": "Tạm dừng / tiếp tục",
    "translate_once": "Dịch lại ngay",
    "toggle_overlay": "Ẩn / hiện khung dịch",
    "open_settings": "Mở cài đặt",
    "quit": "Thoát",
}

DEFAULTS = {
    "hotkeys": {
        "select_region": "alt+q",
        "toggle_auto": "alt+w",
        "translate_once": "alt+e",
        "toggle_overlay": "alt+h",
        "open_settings": "alt+s",
        "quit": "ctrl+alt+x",
    },
    "source_lang": "en",
    "target_lang": "vi",
    "ocr_engine": "windows",          # "windows" hoac "tesseract"
    "tesseract_cmd": "C:/Program Files/Tesseract-OCR/tesseract.exe",
    "translator": "google",           # google | google_cloud | deepl | claude | openai | gemini | grok
    "deepl_api_key": "",
    "google_cloud_api_key": "",
    "ai": {
        "claude": {"api_key": "", "model": "claude-opus-5-5"},
        "openai": {"api_key": "", "model": "gpt-5.4-mini"},
        "gemini": {"api_key": "", "model": "gemini-flash-latest"},
        "grok": {"api_key": "", "model": "grok-4.3"},
    },
    "clean_ocr": True,                # lam sach loi OCR truoc khi dich
    "split_speaker": True,            # tach ten nguoi noi, giu nguyen ten
    "google_context": True,           # gui kem cau truoc cho Google Dich mien phi
    "ai_notes": "",                   # bang ten rieng / van phong cho AI
    "ai_context_lines": 3,            # so cau truoc gui kem de AI hieu ngu canh
    "interval_ms": 600,               # chu ky chup man hinh khi dich lien tuc
    "change_threshold": 0.02,         # muc thay doi anh toi thieu de OCR lai (0..1)
    "upscale": 2.0,                   # phong to anh truoc OCR, giup doc chu nho
    "overlay": {
        "position": "below",          # below | above | over
        "font_family": "Segoe UI",
        "font_size": 15,
        "fg": "#FFFFFF",
        "bg": "#101010",
        "opacity": 0.85,
        "min_width": 320,
        "height": 160,
        "show_original": False,
    },
    "remember_games": True,           # nho vung dich theo tung game (theo ten file exe)
    "auto_start_games": True,         # mo game da luu vung -> tu bat dich
    "pause_when_unfocused": True,     # chi dich khi game dang o phia truoc
    # "Game.exe": {"title": ..., "region": [dx, dy, w, h], "overlay": [dx, dy, w, h]}
    # (toa do tinh tu goc tren-trai vung noi dung cua cua so game)
    "profiles": {},
}


def lang_info(code: str):
    return LANGUAGES.get(code, LANGUAGES["en"])


def app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


CONFIG_PATH = os.path.join(app_dir(), "config.json")


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load() -> dict:
    if not os.path.exists(CONFIG_PATH):
        save(DEFAULTS)
        return copy.deepcopy(DEFAULTS)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return _merge(DEFAULTS, json.load(f))
    except Exception:
        log.exception("config.json loi, dung cau hinh mac dinh")
        return copy.deepcopy(DEFAULTS)


def save(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
