"""Luong nen: chup vung -> so sanh thay doi -> OCR -> dich -> gui ket qua."""
import logging
import threading

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


class TranslateWorker(threading.Thread):
    def __init__(self, cfg: dict, on_result, on_error):
        super().__init__(daemon=True)
        self.cfg = cfg
        self.on_result = on_result     # on_result(original, translated)
        self.on_error = on_error       # on_error(message)
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
        self._last_sig = self._last_text = None
        self.auto = True
        self._wake.set()

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
                try:
                    self._tick(sct, engine, translator, forced)
                except Exception as e:
                    log.exception("Loi khi dich")
                    self.on_error(str(e))

    def _tick(self, sct, engine, translator, forced: bool):
        left, top, w, h = self.region
        shot = sct.grab({"left": left, "top": top, "width": w, "height": h})
        img = Image.frombytes("RGB", shot.size, shot.rgb)

        sig = _signature(img)
        if not forced and self._last_sig is not None \
                and _diff(sig, self._last_sig) < self.cfg["change_threshold"]:
            return
        self._last_sig = sig

        scale = float(self.cfg.get("upscale", 1.0))
        if scale > 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        text = engine.recognize(img).strip()
        if not text or (text == self._last_text and not forced):
            return
        self._last_text = text
        self.on_result(text, translator.translate(text))
