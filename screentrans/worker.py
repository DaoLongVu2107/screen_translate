"""Luong nen: chup vung -> so sanh thay doi -> OCR -> dich -> gui ket qua."""
import logging
import threading
import time

import mss
from PIL import Image, ImageChops, ImageStat

from . import ocr as ocr_mod
from .translator import Translator

log = logging.getLogger(__name__)


def _signature(img: Image.Image) -> Image.Image:
    return img.convert("L").resize((64, max(8, 64 * img.height // max(1, img.width))))


def _diff(a: Image.Image, b: Image.Image) -> float:
    if a.size != b.size:
        return 1.0
    return ImageStat.Stat(ImageChops.difference(a, b)).mean[0] / 255.0


MIN_GAP = 1.0          # toi thieu 1 giay giua hai lan goi may dich


def _is_rate_limit(e: Exception) -> bool:
    name = type(e).__name__.lower()
    return ("toomanyrequests" in name or "ratelimit" in name or "resourceexhausted" in name
            or getattr(e, "status_code", None) == 429 or getattr(e, "code", None) == 429)


def _same(a, b) -> bool:
    """Giong het nhau (chi bo qua khac biet ve dau cach / xuong dong)."""
    return bool(a and b) and " ".join(a.split()) == " ".join(b.split())


class TranslateWorker(threading.Thread):
    def __init__(self, cfg: dict, on_result, on_error, on_status=None, gate=None):
        super().__init__(daemon=True)
        self.cfg = cfg
        self.on_result = on_result     # on_result(original, translated)
        self.on_error = on_error       # on_error(message)
        self.on_status = on_status or (lambda msg: None)
        self.gate = gate or (lambda: True)   # tra ve False -> khong chup / khong dich luc nay
        self._candidate = None         # chu OCR vua doc, cho lan doc sau xac nhan
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
    def run(self):
        try:
            engine = ocr_mod.create(self.cfg)
            translator = Translator(self.cfg)
        except Exception as e:
            log.exception("Khoi tao OCR/dich that bai")
            self.on_error(f"Khong khoi tao duoc OCR/may dich:\n{e}")
            return
        interval = max(0.1, self.cfg["interval_ms"] / 1000)
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
            self._candidate = None
            return
        left, top, w, h = self.region
        shot = sct.grab({"left": left, "top": top, "width": w, "height": h})
        img = Image.frombytes("RGB", shot.size, shot.rgb)

        # Anh khong doi thi bo qua, tru khi dang cho xac nhan chu moi
        sig = _signature(img)
        unchanged = self._last_sig is not None \
            and _diff(sig, self._last_sig) < self.cfg["change_threshold"]
        self._last_sig = sig
        if unchanged and not forced and self._candidate is None:
            return

        scale = float(self.cfg.get("upscale", 1.0))
        if scale > 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        text = engine.recognize(img).strip()

        if not forced:
            # Chu giong het cau vua dich (man hinh dung yen) -> khong gui lai
            if not text or _same(text, self._last_text):
                self._candidate = None
                return
            # Chi dich khi hai lan doc lien tiep ra cung mot chu: tranh dich tung chu
            # khi game hien chu kieu danh may
            if not _same(text, self._candidate):
                self._candidate = text
                return
        if not text:
            return
        if not self.gate():          # trong luc OCR nguoi dung da chuyen cua so
            self._candidate = None
            return
        wait = MIN_GAP - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._candidate = None
        self._last_text = text
        self._last_call = time.monotonic()
        original, translated = translator.translate_dialogue(text)
        if translated:
            self.on_result(original, translated)
