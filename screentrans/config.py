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
    "quick_translate": "Dịch nhanh một lần",
    "edit_region": "Chỉnh vùng dịch",
    "toggle_subtitle": "Chế độ phụ đề",
    "toggle_click_through": "Chuột xuyên qua khung",
    "open_settings": "Mở cài đặt",
    "quit": "Thoát",
}

DEFAULTS = {
    "hotkeys": {
        "select_region": "alt+q",
        "toggle_auto": "alt+w",
        "translate_once": "alt+e",
        "toggle_overlay": "alt+h",
        "quick_translate": "alt+d",
        "edit_region": "alt+r",
        "toggle_subtitle": "alt+v",
        "toggle_click_through": "alt+c",
        "open_settings": "alt+s",
        "quit": "ctrl+alt+x",
    },
    "source_lang": "en",
    "target_lang": "vi",
    "ocr_engine": "windows",          # "windows" hoac "tesseract"
    "tesseract_cmd": "C:/Program Files/Tesseract-OCR/tesseract.exe",
    "translator": "google",           # google | google_cloud | deepl | claude | openai | gemini | grok
    "translator_chain": ["google"],   # thu tu may dich: may dau loi thi dung may sau
    "ocr_substitutions": [],          # bang thay the loi OCR: [{"from", "to", "word"}]
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
    "google_context_lines": 0,        # so cau truoc gui kem cho Google Dich mien phi (0 = tat)
    "min_send_gap": 1.0,              # toi thieu bao nhieu giay giua hai lan gui dich
    "ai_notes": "",                   # bang ten rieng / van phong cho AI
    "ai_context_lines": 3,            # so cau truoc gui kem de AI hieu ngu canh
    "interval_ms": 600,               # chu ky chup man hinh khi dich lien tuc
    "change_pixels": 0.0001,          # ty le diem anh phai doi moi doc lai chu (0.01%)
    "debug_log": False,               # ghi log chi tiet tung lan doc / dich de tim loi
    "pixel_delta_pct": 11,            # diem anh sang/toi hon bao nhieu % moi tinh la doi
    "confirm_reads": 2,               # doc bao nhieu lan giong nhau moi dich (1 = dich ngay)
    "unstable_max": 5,                # doc bao nhieu lan khac nhau lien tiep thi dich luon (0 = tat)
    "block_pause": 30,                # bi may dich chan thi nghi bao nhieu giay (gap doi moi lan)
    "history_max": 200,               # so cau giu trong lich su khung dich
    "word_lookup": True,              # re chuot vao chu goc de tra tung tu
    "auto_hide_empty": True,          # vung het chu thi tu an khung dich
    "hide_after_empty": 2,            # doc bao nhieu lan khong thay chu thi an
    "ocr_filter": {                   # loc anh truoc khi OCR (xem imgfilter.py)
        "text_color_on": False, "text_color": "#FFFFFF", "color_tolerance": 25,
        "autocontrast": False, "invert": False, "sharpen": False, "threshold": 0,
    },
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
        "click_through": False,       # chuot bam xuyen qua khung dich
        "mode": "history",            # history: lich su cac cau | subtitle: phu de cau moi nhat
        "subtitle_font_size": 24,
        "subtitle_geom": None,        # vi tri khung phu de nguoi dung da keo (toa do man hinh)
    },
    "ui_theme": "light",              # giao dien cua so cai dat: light | dark
    "proxy": "",                      # vd. http://127.0.0.1:8080, de trong = khong dung
    "check_updates": True,            # tu kiem tra ban moi khi mo app (toi da 1 lan/ngay)
    "last_update_check": "",
    "remember_games": True,           # nho vung dich theo tung game (theo ten file exe)
    "auto_start_games": True,         # mo game da luu vung -> tu bat dich
    "pause_when_unfocused": True,     # chi dich khi game dang o phia truoc
    "scale_with_window": True,        # doi kich thuoc cua so -> vung dich co gian theo
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
            user = json.load(f)
        cfg = _merge(DEFAULTS, user)
        if "translator_chain" not in user:          # cau hinh ban cu: giu may dich dang dung
            cfg["translator_chain"] = [cfg.get("translator", "google")]
        return cfg
    except Exception:
        log.exception("config.json loi, dung cau hinh mac dinh")
        return copy.deepcopy(DEFAULTS)


def save(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
