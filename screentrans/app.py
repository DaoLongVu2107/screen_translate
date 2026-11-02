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
from . import winutil
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
        try:                       # giao dien Fluent kieu Windows 11, che do toi
            import sv_ttk
            sv_ttk.set_theme("dark")
        except Exception:
            log.info("Khong co sv_ttk, dung giao dien mac dinh")

        self.selecting = False
        self.region = None
        self.settings = None
        # Game dang gan voi vung dich (de nho vung va bam theo cua so game)
        self.game_hwnd = self.game_exe = self.game_origin = None
        self.game_suspended = False
        self._was_auto = True
        self._dismissed: set = set()       # cua so nguoi dung da bao "quen"
        self._exe_cache: dict = {}
        self.overlay = self._new_overlay()
        self.worker = self._new_worker()
        self.root.after(1000, self._watch_games)

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

    def _new_overlay(self):
        return Overlay(self.root, self.cfg, on_menu=self.post, on_geometry=self._on_overlay_moved)

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
        self._remember_game(region)
        self.overlay.set_status(self._running_status())
        self.overlay.show()
        self.worker.set_region(region)

    def _running_status(self):
        return "● đang dịch" + (f" · {self.game_exe}" if self.game_exe else "")

    # --- nho vung theo tung game ---
    def _remember_game(self, region):
        """Tim cua so nam duoi vung vua chon; neu la game thi luu vung theo game do."""
        self._detach_game()
        if not self.cfg.get("remember_games", True):
            return
        left, top, w, h = region
        hwnd = winutil.window_at(left + w // 2, top + h // 2)
        if not hwnd or winutil.window_pid(hwnd) == os.getpid():
            return
        exe, origin = winutil.window_exe(hwnd), winutil.client_origin(hwnd)
        if not exe or not origin or exe.lower() in ("explorer.exe",):
            return
        self._attach_game(hwnd, exe, origin)
        ox, oy = origin
        ow = self.overlay.geometry()
        self.cfg["profiles"][exe] = {
            "title": winutil.window_title(hwnd),
            "region": [left - ox, top - oy, w, h],
            "overlay": [ow[0] - ox, ow[1] - oy, ow[2], ow[3]],
        }
        config.save(self.cfg)
        log.info("Da luu vung cho %s", exe)

    def _attach_game(self, hwnd, exe, origin):
        self.game_hwnd, self.game_exe, self.game_origin = hwnd, exe, origin
        self.game_suspended = False
        self._dismissed.discard(hwnd)

    def _detach_game(self):
        self.game_hwnd = self.game_exe = self.game_origin = None
        self.game_suspended = False

    def _load_profile(self, hwnd, exe):
        prof = self.cfg["profiles"].get(exe)
        origin = winutil.client_origin(hwnd)
        if not prof or not origin:
            return
        ox, oy = origin
        dx, dy, w, h = prof["region"]
        region = (ox + dx, oy + dy, w, h)
        self._attach_game(hwnd, exe, origin)
        self.region = region
        if prof.get("overlay"):
            x, y, ow, oh = prof["overlay"]
            self.overlay.set_geometry(ox + x, oy + y, ow, oh)
        else:
            self.overlay.place_for_region(region)
        self.overlay.set_status(self._running_status() + " (vùng đã lưu)")
        self.overlay.show()
        self.worker.set_region(region)
        log.info("Tu nap vung da luu cho %s", exe)

    def _on_overlay_moved(self, geom):
        """Nguoi dung keo / doi kich thuoc khung dich -> nho lai cho game hien tai."""
        x, y, w, h = geom
        self.cfg["overlay"]["height"] = h
        if self.game_exe and self.game_origin and self.game_exe in self.cfg["profiles"]:
            ox, oy = self.game_origin
            self.cfg["profiles"][self.game_exe]["overlay"] = [x - ox, y - oy, w, h]
        config.save(self.cfg)

    def _exe_of(self, hwnd):
        if hwnd not in self._exe_cache:
            if len(self._exe_cache) > 200:
                self._exe_cache.clear()
            self._exe_cache[hwnd] = winutil.window_exe(hwnd)
        return self._exe_cache[hwnd]

    def _watch_games(self):
        try:
            self._watch_games_once()
        except Exception:
            log.exception("Loi theo doi cua so game")
        self.root.after(500, self._watch_games)

    def _watch_games_once(self):
        if not winutil.IS_WIN or self.selecting:
            return
        hwnd = self.game_hwnd
        if hwnd:
            if not winutil.window_alive(hwnd):                 # game da tat
                log.info("%s da dong", self.game_exe)
                self.worker.set_auto(False)
                self.overlay.hide()
                self.overlay.set_status("game đã đóng")
                self.region = None
                self._detach_game()
            elif winutil.window_minimized(hwnd):               # game bi thu nho
                if not self.game_suspended:
                    self.game_suspended = True
                    self._was_auto = self.worker.auto
                    self.worker.set_auto(False)
                    self.overlay.hide()
            else:
                if self.game_suspended:                        # mo lai game
                    self.game_suspended = False
                    self.worker.set_auto(self._was_auto)
                    self.overlay.show()
                origin = winutil.client_origin(hwnd)
                if origin and self.region and origin != self.game_origin:   # cua so bi keo di
                    dx, dy = origin[0] - self.game_origin[0], origin[1] - self.game_origin[1]
                    left, top, w, h = self.region
                    self.region = (left + dx, top + dy, w, h)
                    self.game_origin = origin
                    self.worker.move_region(self.region)
                    self.overlay.move_by(dx, dy)

        if not (self.cfg.get("remember_games", True) and self.cfg.get("auto_start_games", True)):
            return
        fg = winutil.foreground_window()
        if not fg or fg == self.game_hwnd or fg in self._dismissed:
            return
        if winutil.window_pid(fg) == os.getpid():
            return
        exe = self._exe_of(fg)
        if exe and exe in self.cfg["profiles"] and not winutil.window_minimized(fg):
            self._load_profile(fg, exe)

    def cmd_forget_game(self):
        if not self.game_exe:
            self.overlay.set_status("vùng hiện tại không gắn với game nào")
            return
        exe = self.game_exe
        self.cfg["profiles"].pop(exe, None)
        config.save(self.cfg)
        self._dismissed.add(self.game_hwnd)
        self._detach_game()
        self.overlay.set_status(f"đã quên vùng của {exe}")

    def cmd_toggle_auto(self):
        if not self.region:
            return self.cmd_select_region()
        on = not self.worker.auto
        self.worker.set_auto(on)
        self.overlay.set_status(self._running_status() if on else "❚❚ tạm dừng")
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
            self.overlay.set_status(self._running_status())

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
        deleted = cfg.pop("_deleted_profiles", None)
        if deleted is not None:   # giu cac game vua luu trong luc cua so cai dat dang mo
            cfg["profiles"] = {k: v for k, v in self.cfg["profiles"].items() if k not in deleted}
        self.cfg = cfg
        config.save(cfg)
        auto = self.worker.auto
        self.worker.stop()
        self.worker = self._new_worker()

        was_visible = self.overlay.visible
        old = self.overlay
        geom = old.geometry()
        self.overlay = self._new_overlay()
        for o, t in old.entries[-50:]:          # giu lich su dich
            self.overlay.add_entry(o, t)
        old.win.destroy()
        if self.region:
            self.overlay.set_geometry(*geom)
            self.worker.region = self.region
            self.worker.set_auto(auto)
            self.overlay.set_status(self._running_status() if auto else "❚❚ tạm dừng")
            if was_visible:
                self.overlay.show()
            self.worker.translate_once()
        if not cfg.get("remember_games", True):
            self._detach_game()

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
            pystray.MenuItem("Quên vùng của game hiện tại", lambda: self.post("forget_game")),
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
