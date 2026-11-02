"""Doc / ghi cau hinh tu config.json (tao file mac dinh neu chua co)."""
import copy
import json
import logging
import os
import sys

log = logging.getLogger(__name__)

DEFAULTS = {
    "hotkeys": {
        "select_region": "alt+q",    # chon vung + bat dich lien tuc
        "toggle_auto": "alt+w",      # tam dung / tiep tuc dich lien tuc
        "translate_once": "alt+e",   # dich lai vung hien tai 1 lan
        "toggle_overlay": "alt+h",   # an / hien khung dich
        "quit": "ctrl+alt+x",
    },
    # Ngon ngu cho OCR cua Windows: en-US, ja, ko, zh-Hans-CN, zh-Hant-TW, ...
    "ocr_engine": "windows",          # "windows" hoac "tesseract"
    "ocr_lang": "en-US",
    "tesseract_cmd": "C:/Program Files/Tesseract-OCR/tesseract.exe",
    "tesseract_lang": "eng",          # eng, jpn, chi_sim, kor, ...
    # Ngon ngu cho may dich (ma Google): auto, en, ja, ko, zh-CN, vi, ...
    "translator": "google",           # "google" hoac "deepl"
    "deepl_api_key": "",
    "source_lang": "auto",
    "target_lang": "vi",
    "interval_ms": 600,               # chu ky chup man hinh khi dich lien tuc
    "change_threshold": 0.02,         # muc thay doi anh toi thieu de OCR lai (0..1)
    "upscale": 2.0,                   # phong to anh truoc OCR, giup doc chu nho
    "overlay": {
        "position": "below",          # below | above | over (de len vung chon)
        "font_family": "Segoe UI",
        "font_size": 15,
        "fg": "#FFFFFF",
        "bg": "#101010",
        "opacity": 0.85,
        "min_width": 320,
        "show_original": False,
    },
}


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
