"""Ung dung chinh: phim tat toan cuc + khay he thong + dieu phoi cac thanh phan."""
import logging
import os
import queue
import sys
import tkinter as tk
from tkinter import messagebox

from . import config
from .overlay import Overlay
from .selector import RegionSelector
from .winutil import enable_dpi_awareness
from .worker import TranslateWorker

log = logging.getLogger("screentrans")


class App:
    def __init__(self):
        self.cfg = config.load()
        self.q: "queue.Queue[tuple]" = queue.Queue()

        enable_dpi_awareness()
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("Screen Translator")

        self.overlay = Overlay(self.root, self.cfg, on_menu=self.post)
        self.selecting = False
        self.region = None

        self.worker = TranslateWorker(
            self.cfg,
            on_result=lambda src, dst: self.post("result", src, dst),
            on_error=lambda msg: self.post("error", msg),
        )
        self.worker.start()

        self._register_hotkeys()
        self._start_tray()
        self.root.after(50, self._pump)

    # Moi luong khac (phim tat, khay, worker) chi day lenh vao queue;
    # tkinter chi duoc dung tu luong chinh.
    def post(self, cmd, *args):
        self.q.put((cmd, *args))

    def _pump(self):
        try:
            while True:
                cmd, *args = self.q.get_nowait()
                getattr(self, f"cmd_{cmd}")(*args)
        except queue.Empty:
            pass
        self.root.after(50, self._pump)

    # --- lenh ---
    def cmd_select_region(self):
        if self.selecting:
            return
        self.selecting = True
        self.overlay.hide()
        RegionSelector(self.root, self._on_region)

    def _on_region(self, region):
        self.selecting = False
        if region is None:
            if self.region:
                self.overlay.show()
            return
        self.region = region
        self.overlay.place_for_region(region)
        self.overlay.show_text("", "…")
        self.overlay.set_status("● đang dịch  (Alt+W tạm dừng)")
        self.worker.set_region(region)

    def cmd_toggle_auto(self):
        if not self.region:
            return self.cmd_select_region()
        on = not self.worker.auto
        self.worker.set_auto(on)
        self.overlay.set_status("● đang dịch" if on else "❚❚ tạm dừng")
        self.overlay.show()

    def cmd_translate_once(self):
        if not self.region:
            return self.cmd_select_region()
        self.overlay.set_status("↻ đang dịch lại…")
        self.worker.translate_once()

    def cmd_toggle_overlay(self):
        self.overlay.toggle()

    def cmd_result(self, original, translated):
        self.overlay.show_text(original, translated)
        if self.worker.auto:
            self.overlay.set_status("● đang dịch")

    def cmd_error(self, msg):
        log.error(msg)
        self.overlay.set_status("⚠ lỗi – xem app.log")
        if "khoi tao" in msg.lower():
            messagebox.showerror("Screen Translator", msg)

    def cmd_open_config(self):
        if sys.platform == "win32":
            os.startfile(config.CONFIG_PATH)

    def cmd_quit(self):
        self.worker.stop()
        try:
            import keyboard
            keyboard.unhook_all()
        except Exception:
            pass
        if getattr(self, "tray", None):
            self.tray.stop()
        self.root.quit()

    # --- phim tat & khay ---
    def _register_hotkeys(self):
        try:
            import keyboard
        except ImportError:
            log.warning("Chua cai thu vien keyboard -> khong co phim tat")
            return
        for name, combo in self.cfg["hotkeys"].items():
            if not combo:
                continue
            try:
                keyboard.add_hotkey(combo, self.post, args=(name,))
                log.info("Phim tat %s = %s", combo, name)
            except Exception:
                log.exception("Khong dang ky duoc phim tat %s", combo)

    def _start_tray(self):
        self.tray = None
        try:
            import pystray
            from PIL import Image, ImageDraw
        except ImportError:
            return
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((4, 4, 60, 60), 12, fill=(0, 150, 200, 255))
        try:
            from PIL import ImageFont
            font = ImageFont.load_default(size=40)
        except Exception:
            font = None
        d.text((32, 32), "T", fill="white", font=font, anchor="mm")
        hk = self.cfg["hotkeys"]
        item = pystray.MenuItem
        menu = pystray.Menu(
            item(f"Chọn vùng ({hk['select_region']})", lambda: self.post("select_region"), default=True),
            item(f"Tạm dừng / tiếp tục ({hk['toggle_auto']})", lambda: self.post("toggle_auto")),
            item(f"Dịch lại ({hk['translate_once']})", lambda: self.post("translate_once")),
            item(f"Ẩn / hiện khung ({hk['toggle_overlay']})", lambda: self.post("toggle_overlay")),
            pystray.Menu.SEPARATOR,
            item("Mở config.json", lambda: self.post("open_config")),
            item("Thoát", lambda: self.post("quit")),
        )
        self.tray = pystray.Icon("screentrans", img, "Screen Translator", menu)
        self.tray.run_detached()

    def run(self):
        self.root.mainloop()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(os.path.join(config.app_dir(), "app.log"), encoding="utf-8")]
        + ([logging.StreamHandler()] if sys.stderr else []),
    )
    App().run()
