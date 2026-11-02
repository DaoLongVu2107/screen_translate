"""May dich, co cache de khong goi lai cung 1 cau."""
from collections import OrderedDict

from .ai_translator import PROVIDERS as AI_PROVIDERS, AiTranslator

_EN_NAMES = {"en": "English", "ja": "Japanese", "zh-CN": "Simplified Chinese",
             "zh-TW": "Traditional Chinese", "ko": "Korean", "ru": "Russian", "fr": "French",
             "de": "German", "es": "Spanish", "pt": "Portuguese", "it": "Italian", "th": "Thai",
             "vi": "Vietnamese"}


def _english_name(code: str) -> str:
    return _EN_NAMES.get(code, code)


class ApiError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code


class GoogleCloudTranslator:
    """Google Cloud Translation API (ban chinh thuc, can API key, khong bi gioi han 5 lan/giay)."""
    URL = "https://translation.googleapis.com/language/translate/v2"

    def __init__(self, api_key: str, source: str, target: str):
        if not api_key:
            raise ValueError("Chưa nhập API key cho Google Cloud (Cài đặt → Dịch).")
        import requests
        self._session = requests.Session()
        self.key, self.source, self.target = api_key, source, target

    def translate(self, text: str) -> str:
        import html
        body = {"q": text, "target": self.target, "format": "text"}
        if self.source != "auto":
            body["source"] = self.source
        r = self._session.post(self.URL, params={"key": self.key}, json=body, timeout=20)
        if r.status_code != 200:
            try:
                msg = r.json()["error"]["message"]
            except Exception:
                msg = r.text[:200]
            raise ApiError(r.status_code, msg)
        return html.unescape(r.json()["data"]["translations"][0]["translatedText"])


class GoogleFreeTranslator:
    """Google Dich mien phi, cach lam giong Translumo: goi cong cua tien ich Chrome
    (translate.googleapis.com, client=gtx), loi thi chuyen sang cong du phong (clients5),
    gui kem thong tin giong trinh duyet; bi chan thi xoa cookie va thu lai."""
    URLS = [
        "https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&ie=UTF-8&oe=UTF-8",
        "https://clients5.google.com/translate_a/t?client=dict-chrome-ex&ie=UTF-8&oe=UTF-8",
    ]
    HEADERS = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "DNT": "1",
    }

    def __init__(self, source: str, target: str):
        import requests
        self._requests = requests
        self.source, self.target = source, target
        self._new_session()

    def _new_session(self):
        self._session = self._requests.Session()
        self._session.headers.update(self.HEADERS)

    @staticmethod
    def _parse(body):
        if not isinstance(body, list) or not body:
            return ""
        payload = body[0]
        if isinstance(payload, str):
            return payload
        if not isinstance(payload, list):
            return ""
        # dict-chrome-ex voi sl=auto tra ve ["ban dich", "ma ngon ngu"]
        if len(payload) == 2 and all(isinstance(x, str) for x in payload) and len(payload[1]) <= 6:
            return payload[0]
        out = []
        for part in payload:
            if isinstance(part, str):
                out.append(part)
            elif isinstance(part, list) and part and isinstance(part[0], str):
                out.append(part[0])
        return "".join(out)

    def _try(self, url: str, text: str):
        try:
            r = self._session.post(f"{url}&sl={self.source}&tl={self.target}", data={"q": text},
                                   timeout=10, allow_redirects=False)
        except self._requests.RequestException as e:
            return None, str(e)
        if r.status_code != 200:     # 429, hoac 302 sang trang xac minh "sorry"
            return None, f"HTTP {r.status_code}"
        try:
            result = self._parse(r.json())
        except ValueError:
            return None, "phản hồi không hợp lệ"
        return (result, None) if result else (None, "phản hồi rỗng")

    def translate(self, text: str) -> str:
        import time
        errors = []
        for attempt in range(2):
            for url in self.URLS:
                result, err = self._try(url, text)
                if result:
                    return result
                errors.append(err)
            self._new_session()          # xoa cookie roi thu lai mot lan
            if attempt == 0:
                time.sleep(0.7)
        raise ApiError(429, "Google tạm chặn (" + ", ".join(dict.fromkeys(errors)) + ")")


class Translator:
    def __init__(self, cfg: dict):
        from .config import lang_info
        src, dst = lang_info(cfg["source_lang"])[3], lang_info(cfg["target_lang"])[3]
        self._lang = cfg["source_lang"]
        self._clean = cfg.get("clean_ocr", True)
        self._speaker = cfg.get("split_speaker", True)
        engine = cfg["translator"]
        if engine in AI_PROVIDERS:
            ai = cfg["ai"][engine]
            self._impl = AiTranslator(engine, ai["api_key"], ai["model"],
                                      _english_name(cfg["source_lang"]),
                                      _english_name(cfg["target_lang"]),
                                      notes=cfg.get("ai_notes", ""),
                                      context_lines=int(cfg.get("ai_context_lines", 3)))
        elif engine == "google_cloud":
            self._impl = GoogleCloudTranslator(cfg.get("google_cloud_api_key", ""), src, dst)
        elif engine == "deepl":
            src, dst = src.split("-")[0], dst.split("-")[0]
            from deep_translator import DeeplTranslator
            self._impl = DeeplTranslator(api_key=cfg["deepl_api_key"], source=src,
                                         target=dst, use_free_api=True)
        else:
            self._impl = GoogleFreeTranslator(src, dst)
        self._cache: OrderedDict[str, str] = OrderedDict()

    def translate_dialogue(self, raw: str):
        """Chu OCR tho -> (chu goc de hien thi, ban dich). Lam sach, tach ten nguoi noi,
        chi dich loi thoai va giu nguyen ten."""
        from .textproc import prepare
        name, body = prepare(raw, self._lang, clean=self._clean, speaker=self._speaker)
        if not body:
            return raw, ""
        tr = self.translate(body)
        if name:
            return f"{name}: {body}", f"{name}: {tr}"
        return body, tr

    def translate(self, text: str) -> str:
        if text in self._cache:
            self._cache.move_to_end(text)
            return self._cache[text]
        result = self._impl.translate(text[:4900]) or ""
        self._cache[text] = result
        if len(self._cache) > 500:
            self._cache.popitem(last=False)
        return result
