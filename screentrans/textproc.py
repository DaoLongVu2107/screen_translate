"""Xu ly chu truoc khi dich: lam sach loi OCR, noi dong, tach ten nguoi noi."""
import re

# Chu Trung/Nhat (khong dung dau cach giua cac tu) va chu Han Quoc (co dau cach)
NOSPACE = r"\u3000-\u303f\u3040-\u30ff\u3400-\u9fff\uff00-\uffef"
CJK = NOSPACE + r"\uac00-\ud7af"
_CJK_RE = re.compile(f"[{CJK}]")
_NOSPACE_RE = re.compile(f"[{NOSPACE}]")

# Ky hieu trang tri hay gap trong khung thoai game (mui ten "bam de tiep", khung, gach...)
_DECOR = "▼▽▾▿▶▷►▸◀◁◄◂▲△◆◇■□▪▫●○◎◉★☆♦♢♪♫※†‡¶§→←↓↑⇒⇨➤➜➔❖✦✧〓|¦‖"
_QUOTES = str.maketrans({"“": '"', "”": '"', "„": '"', "«": '"', "»": '"', "″": '"',
                         "‘": "'", "’": "'", "‚": "'", "`": "'", "´": "'", "′": "'"})
_LATIN_LANGS = {"en", "fr", "de", "es", "pt", "it", "vi"}


def _fix_cjk_spaces(line: str) -> str:
    """Windows OCR chen dau cach giua tung chu Han/Kana -> bo di."""
    return re.sub(f"(?<=[{NOSPACE}]) +(?=[{NOSPACE}])", "", line)


def clean_line(line: str, lang: str = "en") -> str:
    s = _fix_cjk_spaces(line).translate(_QUOTES)
    s = s.strip().strip(_DECOR + " _~=*#^<>")      # bo ky hieu trang tri o hai dau
    s = re.sub(f"\\s+[{re.escape(_DECOR)}]+\\s*$", "", s)
    s = re.sub(r"\s+", " ", s)
    if lang in _LATIN_LANGS:
        # Chu so bi doc nham trong mot tu: D0ctor -> Doctor, wi1l -> will
        s = re.sub(r"(?<=[A-Za-z])0(?=[A-Za-z])", lambda m: "o", s)
        s = re.sub(r"\b0(?=[a-z]{2,})", "o", s)
        s = re.sub(r"(?<=[a-z])1(?=[a-z])", "l", s)
        s = re.sub(r"(?<=[a-z])5(?=[a-z])", "s", s)
        if lang == "en":
            s = re.sub(r"(?<![\w'])[l|](?=\s|'m|'ll|'ve|'d\b)", "I", s)   # "l am" -> "I am"
        # Dau cach truoc dau cau, thieu dau cach sau dau cau
        s = re.sub(r"\s+([,.!?;:%)\]])", r"\1", s)
        s = re.sub(r"([(\[])\s+", r"\1", s)
        s = re.sub(r"([,!?;])(?=[A-Za-z])", r"\1 ", s)
        s = re.sub(r"\.{4,}", "...", s)
        s = re.sub(r"([!?])\1{2,}", r"\1\1", s)
    return s.strip()


def join_lines(lines: list[str]) -> str:
    lines = [ln.strip() for ln in lines if ln.strip()]
    if not lines:
        return ""
    text = lines[0]
    for ln in lines[1:]:
        if re.search(r"[A-Za-z]-$", text) and ln[:1].islower():
            text = text[:-1] + ln          # noi tu bi ngat dong: "trans-" + "lation"
        elif _NOSPACE_RE.search(text[-1:]) or _NOSPACE_RE.search(ln[:1]):
            text += ln                     # tieng Trung/Nhat khong dung dau cach
        else:
            text += " " + ln
    return text


_NAME_COLON = re.compile(
    r"^\s*([^\s:：\"'「『(\[][^:：\n\"「『]{0,24}?)\s*[:：]\s*(?=\S)(.+)$", re.S)
_SENTENCE_END = re.compile(r"[.!?…。！？,，、~\-—\"'」』)]$")


def _looks_like_name(s: str) -> bool:
    s = s.strip()
    if not s or len(s) > 24 or _SENTENCE_END.search(s):
        return False
    if _CJK_RE.search(s):
        return len(s) <= 10
    words = s.split()
    if len(words) > 3 or not any(c.isalpha() for c in s):
        return False
    # Ten rieng: moi tu viet hoa chu dau (Amiya, Kal'tsit, Doctor), hoac viet hoa toan bo
    return all(w[:1].isupper() or w.isupper() or not w[:1].isalpha() for w in words)


def split_speaker(lines: list[str]):
    """Tach ten nguoi noi -> (ten, cac dong loi thoai). Ten = '' neu khong co."""
    if not lines:
        return "", lines
    first = lines[0]
    m = _NAME_COLON.match(first)
    if m and _looks_like_name(m.group(1)):
        return m.group(1).strip(), [m.group(2).strip()] + lines[1:]
    # Ten nam rieng mot dong ngan phia tren loi thoai
    if len(lines) >= 2 and _looks_like_name(first):
        nxt = lines[1]
        if nxt[:1] in "\"「『(" or len(nxt) > len(first) or _CJK_RE.search(first):
            return first.strip(), lines[1:]
    return "", lines


def prepare(raw: str, lang: str, clean: bool = True, speaker: bool = True):
    """Chu OCR tho (moi dong cach nhau boi \\n) -> (ten nguoi noi, loi thoai da noi dong)."""
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if clean:
        lines = [c for c in (clean_line(ln, lang) for ln in lines) if c]
    name = ""
    if speaker:
        name, lines = split_speaker(lines)
    body = join_lines(lines)
    if clean and lang in _LATIN_LANGS:
        body = re.sub(r"\s+([,.!?;:])", r"\1", body)
    return name, body
