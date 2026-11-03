"""Luong nen: chup vung -> so sanh thay doi -> OCR -> dich -> gui ket qua."""
import logging
import threading
import time

import mss
from PIL import Image, ImageChops

from . import ocr as ocr_mod
from .textproc import prepare
from .translator import Translator

log = logging.getLogger(__name__)


SIG_W = 320             # anh thu nho de so sanh thay doi
PIXEL_DELTA = 28        # diem anh doi sang hon / toi hon muc nay moi tinh la "doi"
UNSTABLE_MAX = 5        # doc 5 lan lien tiep van khac nhau -> dich luon ban moi nhat


def _signature(img: Image.Image) -> Image.Image:
    h = max(8, SIG_W * img.height // max(1, img.width))
    return img.convert("L").resize((SIG_W, h), Image.BILINEAR)


def _diff(a: Image.Image, b: Image.Image) -> float:
    """Ty le diem anh thay doi ro rang (0..1). Khong lay trung binh ca vung: cau thoai
    chi chiem mot phan nho cua vung nen trung binh rat nho du da doi sang cau khac."""
    if a.size != b.size:
        return 1.0
    hist = ImageChops.difference(a, b).histogram()
    changed = sum(hist[PIXEL_DELTA:])
    return changed / max(1, a.width * a.height)


MIN_GAP = 1.0          # mac dinh: toi thieu 1 giay giua hai lan goi may dich


def _is_rate_limit(e: Exception) -> bool:
    name = type(e).__name__.lower()
    return ("toomanyrequests" in name or "ratelimit" in name or "resourceexhausted" in name
            or getattr(e, "status_code", None) == 429 or getattr(e, "code", None) == 429)


def _same(a, b) -> bool:
    """Giong het nhau (chi bo qua khac biet ve dau cach / xuong dong)."""
    return bool(a and b) and " ".join(a.split()) == " ".join(b.split())


def _key(raw: str, lang: str) -> str:
    """Chu dung de so sanh hai lan doc: da bo ky hieu trang tri (mui ten ▼ nhap nhay...),
    ky tu rac va khac biet dau cach. Khong so gan dung: khac mot chu van la khac."""
    if not raw:
        return ""
    return prepare(raw, lang, clean=True, speaker=False)[1]


class TranslateWorker(threading.Thread):
    def __init__(self, cfg: dict, on_result, on_error, on_status=None, gate=None):
        super().__init__(daemon=True)
        self.cfg = cfg
        self.on_result = on_result     # on_result(original, translated)
        self.on_error = on_error       # on_error(message)
        self.on_status = on_status or (lambda msg: None)
        self.gate = gate or (lambda: True)   # tra ve False -> khong chup / khong dich luc nay
        self._candidate = None         # chu OCR vua doc, cho lan doc sau xac nhan
        self._unstable = 0             # so lan doc lien tiep ra chu khac nhau
        self._idle_logged = False
        self._last_call = 0.0
        self._cooldown_until = 0.0
        self._backoff = 0.0
        self.region = None             # (left, top, width, height) toa do man hinh
        self.auto = False
        self._once = False
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._last_sig = None
        self._last_text = None

    # --- dieu khien tu luong giao dien ---
    def set_region(self, region):
        self.region = region
        self._last_sig = self._last_text = self._candidate = None
        self.auto = True
        self._wake.set()

    def move_region(self, region):
        """Cua so game bi keo di: doi vi tri vung nhung giu nguyen trang thai dich."""
        self.region = region
        self._last_sig = None

    def drop_pending(self):
        """Bo chu dang cho xac nhan (vd. vua chuyen sang cua so khac)."""
        self._candidate = None
        self._last_sig = None

    def set_auto(self, value: bool):
        self.auto = value
        self._wake.set()

    def translate_once(self):
        self._once = True
        self._last_sig = self._last_text = None
        self._wake.set()

    def stop(self):
        self._stop.set()
        self._wake.set()

    # --- vong lap ---
    def _dbg(self, msg, *args):
        if self.cfg.get("debug_log"):
            log.info("[chi tiet] " + msg, *args)

    def run(self):
        try:
            self._run()
        except Exception as e:           # khong de luong dich chet im lang
            log.exception("Luong dich bi loi va da dung")
            self.on_error(f"Luong dich bi loi: {e}")

    def _run(self):
        try:
            engine = ocr_mod.create(self.cfg)
            translator = Translator(self.cfg)
        except Exception as e:
            log.exception("Khoi tao OCR/dich that bai")
            self.on_error(f"Khong khoi tao duoc OCR/may dich:\n{e}")
            return
        interval = max(0.1, self.cfg["interval_ms"] / 1000)
        log.info("Bat dau dich: OCR=%s, may dich=%s, chu ky=%sms",
                 self.cfg["ocr_engine"], self.cfg["translator"], self.cfg["interval_ms"])
        with mss.mss() as sct:
            while not self._stop.is_set():
                self._wake.wait(interval if self.auto else None)
                self._wake.clear()
                if self._stop.is_set():
                    break
                if not self.region or not (self.auto or self._once):
                    continue
                forced, self._once = self._once, False
                if time.monotonic() < self._cooldown_until and not forced:
                    continue
                try:
                    self._tick(sct, engine, translator, forced)
                    self._backoff = 0.0
                except Exception as e:
                    if _is_rate_limit(e):
                        # bi chan vi goi qua nhieu: nghi 30s, 60s, 120s... (toi da 5 phut)
                        self._backoff = min(300.0, self._backoff * 2 or 30.0)
                        self._cooldown_until = time.monotonic() + self._backoff
                        self._last_text = self._last_sig = None
                        log.warning("May dich bao goi qua nhieu, nghi %ss", self._backoff)
                        self.on_status(f"⏳ máy dịch tạm chặn, thử lại sau {int(self._backoff)}s")
                    else:
                        log.exception("Loi khi dich")
                        self.on_error(str(e))

    def _tick(self, sct, engine, translator, forced: bool):
        if not self.gate():
            if self._candidate is not None:
                self._dbg("tam khong chup (app khong o phia truoc / dang chon vung)")
            self._candidate = None
            return
        left, top, w, h = self.region
        shot = sct.grab({"left": left, "top": top, "width": w, "height": h})
        img = Image.frombytes("RGB", shot.size, shot.rgb)

        # Anh khong doi thi bo qua, tru khi dang cho xac nhan chu moi
        sig = _signature(img)
        change = 1.0 if self._last_sig is None else _diff(sig, self._last_sig)
        self._last_sig = sig
        threshold = float(self.cfg.get("change_pixels", 0.0001))
        if change < threshold and not forced and self._candidate is None:
            if not self._idle_logged:
                self._dbg("anh khong doi (%.3f%% < %.3f%%), bo qua", change * 100, threshold * 100)
                self._idle_logged = True
            return
        self._idle_logged = False

        scale = float(self.cfg.get("upscale", 1.0))
        if scale > 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        t0 = time.monotonic()
        text = engine.recognize(img).strip()
        took = time.monotonic() - t0
        if took > 1.5:
            log.warning("OCR cham: %.1fs (vung %dx%d, phong to %.1f). Thu chon vung nho hon "
                        "hoac giam phong to.", took, w, h, scale)
        lang = self.cfg["source_lang"]
        key = _key(text, lang)
        self._dbg("doc duoc (anh doi %.2f%%, OCR %.2fs): %r", change * 100, took, key[:80])

        if not forced:
            # Chu giong het cau vua dich (man hinh dung yen) -> khong gui lai
            if not key or key == _key(self._last_text, lang):
                self._candidate = None
                self._unstable = 0
                return
            # Chi dich khi hai lan doc lien tiep ra cung mot chu: tranh dich tung chu khi
            # game hien chu kieu danh may. Neu chu cu doi mai thi sau vai lan van dich.
            if key != _key(self._candidate, lang):
                self._candidate = text
                self._unstable += 1
                if self._unstable < UNSTABLE_MAX:
                    return
                log.info("Chu doi lien tuc %d lan, dich luon ban moi nhat", self._unstable)
        if not key:
            return
        if not self.gate():          # trong luc OCR nguoi dung da chuyen cua so
            self._candidate = None
            return
        gap = float(self.cfg.get("min_send_gap", MIN_GAP))
        wait = gap - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._candidate = None
        self._unstable = 0
        self._last_text = text
        self._last_call = time.monotonic()
        t0 = time.monotonic()
        original, translated = translator.translate_dialogue(text)
        took = time.monotonic() - t0
        if took > 3:
            log.warning("May dich tra loi cham: %.1fs", took)
        self._dbg("da dich (%.2fs): %r", took, translated[:80])
        if translated:
            self.on_result(original, translated)
