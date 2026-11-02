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
from .settings import SettingsWindow
from .winutil import enable_dpi_awareness
from .worker import TranslateWorker

log = logging.getLogger("screentrans")


class App:
    def __init__(self):
        self.first_run = not os.path.exists(config.CONFIG_PATH)
        self.cfg = config.load()
        self.q: "queue.Queue[tuple]" = queue.Queue()

        enable_dpi_awareness()
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("Screen Translator")

        self.selecting = False
        self.region = None
        self.settings = None
        self.overlay = Overlay(self.root, self.cfg, on_menu=self.post)
        self.worker = self._new_worker()

        self.register_hotkeys()
        self.tray = None
        self._start_tray()
        self.root.after(50, self._pump)
        if self.first_run:
            self.root.after(300, self._welcome)

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
        except Exception:
            log.exception("Loi xu ly lenh")
        self.root.after(50, self._pump)

    def _new_worker(self):
        w = TranslateWorker(
            self.cfg,
            on_result=lambda src, dst: self.post("result", src, dst),
            on_error=lambda msg: self.post("error", msg),
            on_status=lambda msg: self.post("status", msg),
        )
        w.start()
        return w

    def _welcome(self):
        hk = self.cfg["hotkeys"]
        messagebox.showinfo(
            "Screen Translator",
            f"App đang chạy ở khay hệ thống (góc phải thanh taskbar).\n\n"
            f"{hk['select_region']}: chọn vùng cần dịch\n"
            f"{hk['toggle_auto']}: tạm dừng / tiếp tục\n"
            f"{hk['open_settings']}: mở cài đặt (ngôn ngữ, phím tắt, giao diện)")

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
        self.overlay.set_status("● đang dịch")
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

    def cmd_status(self, msg):
        self.overlay.set_status(msg)

    def cmd_error(self, msg):
        log.error(msg)
        self.overlay.set_status("⚠ " + msg.splitlines()[0][:80])
        if "khoi tao" in msg.lower() or "khởi tạo" in msg.lower():
            messagebox.showerror("Screen Translator", msg)

    def cmd_open_settings(self):
        if self.settings and self.settings.win.winfo_exists():
            self.settings.win.lift()
            self.settings.win.focus_force()
            return
        self.settings = SettingsWindow(self.root, self.cfg, on_save=self.apply_config,
                                       pause_hotkeys=self.unregister_hotkeys,
                                       resume_hotkeys=self.register_hotkeys)

    def apply_config(self, cfg):
        """Luu cai dat va ap dung ngay, khong can khoi dong lai."""
        self.cfg = cfg
        config.save(cfg)
        auto = self.worker.auto
        self.worker.stop()
        self.worker = self._new_worker()

        was_visible = self.overlay.visible
        old = self.overlay
        self.overlay = Overlay(self.root, cfg, on_menu=self.post)
        old.win.destroy()
        if self.region:
            self.overlay.place_for_region(self.region)
            self.worker.region = self.region
            self.worker.set_auto(auto)
            self.overlay.show_text(old.original, old.translated)
            self.overlay.set_status("● đang dịch" if auto else "❚❚ tạm dừng")
            if not was_visible:
                self.overlay.hide()
            self.worker.translate_once()

        self.unregister_hotkeys()
        self.register_hotkeys()
        if self.tray:
            self.tray.menu = self._tray_menu()
            self.tray.update_menu()

    def cmd_quit(self):
        self.worker.stop()
        self.unregister_hotkeys()
        if self.tray:
            self.tray.stop()
        self.root.quit()

    # --- phim tat & khay ---
    def register_hotkeys(self):
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
            except Exception:
                log.exception("Khong dang ky duoc phim tat %s", combo)

    def unregister_hotkeys(self):
        try:
            import keyboard
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass

    def _tray_menu(self):
        import pystray
        hk = self.cfg["hotkeys"]
        names = config.HOTKEY_NAMES

        def item(cmd, default=False):
            label = names[cmd] + (f"   ({hk[cmd]})" if hk.get(cmd) else "")
            return pystray.MenuItem(label, lambda: self.post(cmd), default=default)
        return pystray.Menu(
            item("select_region", default=True),
            item("toggle_auto"),
            item("translate_once"),
            item("toggle_overlay"),
            pystray.Menu.SEPARATOR,
            item("open_settings"),
            item("quit"),
        )

    def _start_tray(self):
        try:
            import pystray
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            return
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((4, 4, 60, 60), 12, fill=(0, 150, 200, 255))
        try:
            font = ImageFont.load_default(size=40)
        except Exception:
            font = None
        d.text((32, 32), "T", fill="white", font=font, anchor="mm")
        self.tray = pystray.Icon("screentrans", img, "Screen Translator", self._tray_menu())
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
