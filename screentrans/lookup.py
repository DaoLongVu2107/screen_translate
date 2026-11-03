"""Tra tung tu bang tu dien cua Google Dich mien phi (nghia chinh + nghia theo loai tu)."""
from collections import OrderedDict

from .i18n import t

URL = "https://translate.googleapis.com/translate_a/single"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
}


def parse(data):
    """Phan hoi cua Google -> (nghia chinh, [(loai tu, [nghia...]), ...])."""
    main, senses = "", []
    try:
        main = "".join(seg[0] for seg in (data[0] or []) if isinstance(seg, list) and seg
                       and isinstance(seg[0], str)).strip()
    except (TypeError, IndexError):
        pass
    try:
        for entry in data[1] or []:
            pos, terms = entry[0], entry[1]
            if isinstance(pos, str) and isinstance(terms, list):
                senses.append((pos, [t for t in terms if isinstance(t, str)][:6]))
    except (TypeError, IndexError):
        pass
    return main, senses


class WordLookup:
    def __init__(self, source: str, target: str):
        import requests
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        self.source, self.target = source, target
        self._cache: OrderedDict = OrderedDict()

    def lookup(self, word: str):
        key = word.lower()
        if key in self._cache:
            return self._cache[key]
        params = [("client", "gtx"), ("sl", self.source), ("tl", self.target),
                  ("hl", self.target), ("dt", "t"), ("dt", "bd"), ("ie", "UTF-8"),
                  ("oe", "UTF-8"), ("q", word)]
        r = self._session.get(URL, params=params, timeout=5, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError(t("Google không trả lời (HTTP {code})").format(code=r.status_code))
        result = parse(r.json())
        self._cache[key] = result
        if len(self._cache) > 1000:
            self._cache.popitem(last=False)
        return result
