"""May dich, co cache de khong goi lai cung 1 cau."""
import logging
import re
from collections import OrderedDict, deque

from .ai_translator import PROVIDERS as AI_PROVIDERS, AiTranslator

log = logging.getLogger(__name__)

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
        r = self._session.post(self.URL, params={"key": self.key}, json=body, timeout=10)
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
                                   timeout=5, allow_redirects=False)
        except self._requests.RequestException as e:
            return None, f"không kết nối được: {type(e).__name__}"
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
            if not any(e.startswith("HTTP") for e in errors):
                break                    # mat mang: thu lai cung vo ich, bao loi ngay
            self._new_session()          # bi chan: xoa cookie roi thu lai mot lan
            if attempt == 0:
                time.sleep(0.7)
        detail = ", ".join(dict.fromkeys(errors))
        if any(e.startswith("HTTP") for e in errors):
            raise ApiError(429, f"Google tạm chặn ({detail})")
        raise ApiError(0, f"Không kết nối được tới Google Dịch ({detail}). Kiểm tra mạng.")


ENGINE_NAMES = {"google": "Google Dịch", "google_cloud": "Google Cloud", "deepl": "DeepL",
                **{k: v[0] for k, v in AI_PROVIDERS.items()}}


def is_rate_limit(e: Exception) -> bool:
    name = type(e).__name__.lower()
    return ("toomanyrequests" in name or "ratelimit" in name or "resourceexhausted" in name
            or getattr(e, "status_code", None) == 429 or getattr(e, "code", None) == 429)


def make_engine(engine: str, cfg: dict):
    """Tao may dich theo ten. Thieu API key... thi bao loi ngay."""
    from .config import lang_info
    src, dst = lang_info(cfg["source_lang"])[3], lang_info(cfg["target_lang"])[3]
    if engine in AI_PROVIDERS:
        ai = cfg["ai"][engine]
        return AiTranslator(engine, ai["api_key"], ai["model"],
                            _english_name(cfg["source_lang"]), _english_name(cfg["target_lang"]),
                            notes=cfg.get("ai_notes", ""),
                            context_lines=int(cfg.get("ai_context_lines", 3)))
    if engine == "google_cloud":
        return GoogleCloudTranslator(cfg.get("google_cloud_api_key", ""), src, dst)
    if engine == "deepl":
        if not cfg.get("deepl_api_key"):
            raise ValueError("Chưa nhập DeepL API key.")
        from deep_translator import DeeplTranslator
        return DeeplTranslator(api_key=cfg["deepl_api_key"], source=src.split("-")[0],
                               target=dst.split("-")[0], use_free_api=True)
    return GoogleFreeTranslator(src, dst)


def engine_chain(cfg: dict) -> list:
    chain = [e for e in (cfg.get("translator_chain") or []) if e in ENGINE_NAMES]
    return list(dict.fromkeys(chain or [cfg.get("translator", "google")]))


class Translator:
    """Dich qua chuoi may dich theo thu tu: may dau loi (bi chan, mat mang, sai key...)
    thi tu dung may tiep theo; may vua bi chan duoc tam bo qua mot luc."""

    def __init__(self, cfg: dict):
        import time
        self._time = time
        self._lang = cfg["source_lang"]
        self._clean = cfg.get("clean_ocr", True)
        self._speaker = cfg.get("split_speaker", True)
        self._subs = cfg.get("ocr_substitutions") or []
        n = max(0, min(5, int(cfg.get("google_context_lines", 0))))
        self._history: deque[str] = deque(maxlen=n or 1)
        self._context_n = n
        self._pause = max(5.0, float(cfg.get("block_pause", 30)))
        self._chain, skipped = [], []
        for eng in engine_chain(cfg):
            try:
                self._chain.append({"id": eng, "impl": make_engine(eng, cfg), "until": 0.0})
            except Exception as e:
                log.warning("Bo qua may dich %s: %s", eng, e)
                skipped.append(f"{ENGINE_NAMES.get(eng, eng)}: {e}")
        if not self._chain:
            raise ValueError("Không có máy dịch nào dùng được. " + "; ".join(skipped))
        self._impl = self._chain[0]["impl"]
        self.last_engine = None
        self.fallback_note = ""
        self._cache: OrderedDict[str, str] = OrderedDict()

    def translate_dialogue(self, raw: str):
        """Chu OCR tho -> (chu goc de hien thi, ban dich). Lam sach, tach ten nguoi noi,
        chi dich loi thoai va giu nguyen ten."""
        from .textproc import prepare
        name, body = prepare(raw, self._lang, clean=self._clean, speaker=self._speaker,
                             subs=self._subs)
        if not body:
            return raw, ""
        tr = self.translate(body)
        if name:
            return f"{name}: {body}", f"{name}: {tr}"
        return body, tr

    def translate(self, text: str) -> str:
        self.fallback_note = ""
        if text in self._cache:
            self._cache.move_to_end(text)
            self._history.append(text)
            return self._cache[text]
        now = self._time.monotonic()
        ready = [e for e in self._chain if e["until"] <= now]
        errors = []
        result = None
        for i, entry in enumerate(ready or self._chain):
            self._impl = entry["impl"]
            try:
                if self._context_n and self._history and isinstance(self._impl, GoogleFreeTranslator):
                    result = self._translate_with_context(text)
                else:
                    result = self._impl.translate(text[:4900]) or ""
                self.last_engine = entry["id"]
                if entry is not self._chain[0]:
                    failed = ", ".join(ENGINE_NAMES.get(e, e) for e, _ in errors) or \
                        ENGINE_NAMES.get(self._chain[0]["id"], "")
                    self.fallback_note = f"dịch bằng {ENGINE_NAMES.get(entry['id'])} ({failed} đang lỗi)"
                break
            except Exception as e:
                errors.append((entry["id"], e))
                entry["until"] = now + self._pause       # tam bo qua may nay mot luc
                if len(self._chain) > 1:
                    log.warning("May dich %s loi (%s), thu may tiep theo", entry["id"], e)
        if result is None:
            if errors and all(is_rate_limit(e) for _, e in errors):
                raise ApiError(429, "; ".join(f"{ENGINE_NAMES.get(n, n)}: {e}" for n, e in errors))
            if len(errors) == 1:
                raise errors[0][1]
            raise RuntimeError("Mọi máy dịch đều lỗi: " +
                               "; ".join(f"{ENGINE_NAMES.get(n, n)}: {e}" for n, e in errors))
        self._history.append(text)
        self._cache[text] = result
        if len(self._cache) > 500:
            self._cache.popitem(last=False)
        return result

    def _translate_with_context(self, text: str) -> str:
        """Gui N cau truoc + cau hien tai trong mot lan (moi cau mot dong) de Google hieu
        mach hoi thoai, roi chi lay dong cuoi. Khong tach dung so dong -> dich rieng."""
        prev = []
        for p in list(self._history)[-self._context_n:]:
            p = " ".join(p.split())[-400:]
            if not re.search(r"[.!?…。！？」』\"']$", p):
                p += "。" if re.search(r"[\u3040-\u30ff\u3400-\u9fff]$", p) else "."
            prev.append(p)
        body = " ".join(text.split())[:4000]
        out = self._impl.translate("\n".join(prev + [body])) or ""
        parts = [x.strip() for x in out.split("\n") if x.strip()]
        if len(parts) == len(prev) + 1:
            return parts[-1]
        return self._impl.translate(text[:4900]) or ""
