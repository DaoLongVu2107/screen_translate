"""May dich, co cache de khong goi lai cung 1 cau."""
from collections import OrderedDict

from .ai_translator import PROVIDERS as AI_PROVIDERS, AiTranslator

_EN_NAMES = {"en": "English", "ja": "Japanese", "zh-CN": "Simplified Chinese",
             "zh-TW": "Traditional Chinese", "ko": "Korean", "ru": "Russian", "fr": "French",
             "de": "German", "es": "Spanish", "pt": "Portuguese", "it": "Italian", "th": "Thai",
             "vi": "Vietnamese"}


def _english_name(code: str) -> str:
    return _EN_NAMES.get(code, code)


class Translator:
    def __init__(self, cfg: dict):
        from .config import lang_info
        src, dst = lang_info(cfg["source_lang"])[3], lang_info(cfg["target_lang"])[3]
        engine = cfg["translator"]
        if engine in AI_PROVIDERS:
            ai = cfg["ai"][engine]
            self._impl = AiTranslator(engine, ai["api_key"], ai["model"],
                                      _english_name(cfg["source_lang"]),
                                      _english_name(cfg["target_lang"]),
                                      notes=cfg.get("ai_notes", ""),
                                      context_lines=int(cfg.get("ai_context_lines", 3)))
        elif engine == "deepl":
            src, dst = src.split("-")[0], dst.split("-")[0]
            from deep_translator import DeeplTranslator
            self._impl = DeeplTranslator(api_key=cfg["deepl_api_key"], source=src,
                                         target=dst, use_free_api=True)
        else:
            from deep_translator import GoogleTranslator
            self._impl = GoogleTranslator(source=src, target=dst)
        self._cache: OrderedDict[str, str] = OrderedDict()

    def translate(self, text: str) -> str:
        if text in self._cache:
            self._cache.move_to_end(text)
            return self._cache[text]
        result = self._impl.translate(text[:4900]) or ""
        self._cache[text] = result
        if len(self._cache) > 500:
            self._cache.popitem(last=False)
        return result
