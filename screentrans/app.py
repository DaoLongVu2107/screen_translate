"""Ung dung chinh: phim tat toan cuc + khay he thong + dieu phoi cac thanh phan."""
import logging
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox

from . import config, theme
from .overlay import Overlay
from .quick import QuickPopup
from .region_editor import RegionEditor
from .single_instance import SingleInstance
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
        theme.apply(self.root, self.cfg.get("ui_theme", "light"))

        self.selecting = False
        self.region = None
        self.settings = None
        self.user_hidden = False           # nguoi dung tu an khung -> khong tu hien lai
        self.quick_popup = None
        self.editor = None                 # dang chinh vung (vien xanh)
        self._lookup = None
        # Game dang gan voi vung dich (de nho vung va bam theo cua so game)
        self.game_hwnd = self.game_exe = self.game_origin = self.game_size = None
        self.game_base = (None, None)
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
        return Overlay(self.root, self.cfg, on_menu=self.post, on_geometry=self._on_overlay_moved,
                       lookup=self._lookup_word)

    def _new_worker(self):
        w = TranslateWorker(
            self.cfg,
            on_result=lambda src, dst: self.post("result", src, dst),
            on_error=lambda msg: self.post("error", msg),
            on_status=lambda msg: self.post("status", msg),
            gate=self._can_capture,
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
            f"{hk['quick_translate']}: dịch nhanh một lần\n"
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
                self._show_overlay()
            return
        self.region = region
        self.overlay.place_for_region(region)
        self._remember_game(region)
        self.overlay.set_status(self._running_status())
        self.user_hidden = False
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
        ox, oy = origin
        size = winutil.client_size(hwnd)
        self._attach_game(hwnd, exe, origin, (left - ox, top - oy, w, h), size)
        ow = self.overlay.geometry()
        self.cfg["profiles"][exe] = {
            "title": winutil.window_title(hwnd),
            "region": [left - ox, top - oy, w, h],
            "client": list(size) if size else None,
            "overlay": [ow[0] - ox, ow[1] - oy, ow[2], ow[3]],
        }
        config.save(self.cfg)
        log.info("Da luu vung cho %s", exe)

    def _attach_game(self, hwnd, exe, origin, base_rel=None, base_size=None):
        self.game_hwnd, self.game_exe, self.game_origin = hwnd, exe, origin
        self.game_size = winutil.client_size(hwnd)
        # Vung goc (tinh tu goc cua so) va kich thuoc cua so luc chon vung: dung de co gian
        self.game_base = (tuple(base_rel) if base_rel else None,
                          tuple(base_size) if base_size else self.game_size)
        self.game_suspended = False
        self._dismissed.discard(hwnd)

    def _region_for(self, origin, size):
        """Vung dich tren man hinh ung voi vi tri / kich thuoc cua so hien tai."""
        rel, base = self.game_base
        dx, dy, w, h = rel
        sx = sy = 1.0
        if self.cfg.get("scale_with_window", True) and base and size and base[0] and base[1]:
            sx, sy = size[0] / base[0], size[1] / base[1]
        return (round(origin[0] + dx * sx), round(origin[1] + dy * sy),
                max(8, round(w * sx)), max(8, round(h * sy)))

    def _detach_game(self):
        self.game_hwnd = self.game_exe = self.game_origin = self.game_size = None
        self.game_base = (None, None)
        self.game_suspended = False

    def _load_profile(self, hwnd, exe):
        prof = self.cfg["profiles"].get(exe)
        origin = winutil.client_origin(hwnd)
        if not prof or not origin:
            return
        ox, oy = origin
        self._attach_game(hwnd, exe, origin, prof["region"], prof.get("client"))
        region = self._region_for(origin, self.game_size)
        self.region = region
        if prof.get("overlay"):
            x, y, ow, oh = prof["overlay"]
            self.overlay.set_geometry(ox + x, oy + y, ow, oh)
        else:
            self.overlay.place_for_region(region)
        self.overlay.set_status(self._running_status() + " (vùng đã lưu)")
        self.user_hidden = False
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
        if not winutil.IS_WIN or self.selecting or self.editor:
            return
        hwnd = self.game_hwnd
        if hwnd:
            if not winutil.window_alive(hwnd):                 # game da tat
                log.info("%s da dong", self.game_exe)
                self.worker.set_auto(False)
                self.overlay.hide()
                self.overlay.set_status("app đã đóng")
                self.region = None
                self._detach_game()
            else:
                reason = self._suspend_reason(hwnd)
                if reason and not self.game_suspended:          # thu nho / chuyen cua so khac
                    self.game_suspended = True
                    self._was_auto = self.worker.auto
                    self.worker.set_auto(False)
                    self.worker.drop_pending()
                    self.overlay.hide()
                    log.info("Tam dung dich: %s", reason)
                elif not reason and self.game_suspended:        # quay lai game
                    self.game_suspended = False
                    self.worker.set_auto(self._was_auto)
                    self._show_overlay()
                    self.overlay.set_status(self._running_status() if self._was_auto else "❚❚ tạm dừng")
                origin = winutil.client_origin(hwnd)
                size = winutil.client_size(hwnd)
                if not self.game_suspended and origin and self.region and size and size[0] > 0 \
                        and (origin != self.game_origin or size != self.game_size):
                    # Keo cua so: vung di theo. Doi kich thuoc: vung co gian theo ty le cua so.
                    dx, dy = origin[0] - self.game_origin[0], origin[1] - self.game_origin[1]
                    if self.game_base[0]:
                        self.region = self._region_for(origin, size)
                    else:
                        left, top, w, h = self.region
                        self.region = (left + dx, top + dy, w, h)
                    self.game_origin, self.game_size = origin, size
                    self.worker.move_region(self.region)
                    if dx or dy:
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

    def _can_capture(self) -> bool:
        """Goi tu luong dich ngay truoc khi chup / gui dich: game dang gan ma bi che
        hoac thu nho thi khong chup, tranh dich nham chu cua cua so khac."""
        if self.selecting or self.editor:   # dang khoanh / chinh vung
            return False
        hwnd = self.game_hwnd
        if not hwnd or not winutil.IS_WIN:
            return True
        try:
            return self._suspend_reason(hwnd) is None
        except Exception:
            return True

    def _suspend_reason(self, hwnd):
        """Ly do tam dung dich (None = cu dich binh thuong)."""
        if winutil.window_minimized(hwnd):
            return "app bị thu nhỏ"
        if not self.cfg.get("pause_when_unfocused", True):
            return None
        fg = winutil.foreground_window()
        if not fg or fg == hwnd:
            return None
        pid = winutil.window_pid(fg)
        # Cua so cua chinh app (khung dich, cai dat) hoac hop thoai phu cua game -> van dich
        if pid == os.getpid() or pid == winutil.window_pid(hwnd):
            return None
        return "app không ở phía trước"

    def cmd_forget_game(self):
        if not self.game_exe:
            self.overlay.set_status("vùng hiện tại không gắn với app nào")
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
        if self.game_suspended:          # dang tam dung vi roi game: doi trang thai khi quay lai
            self._was_auto = not self._was_auto
            return
        on = not self.worker.auto
        self.worker.set_auto(on)
        self.overlay.set_status(self._running_status() if on else "❚❚ tạm dừng")
        self._show_overlay()

    def cmd_translate_once(self):
        if not self.region:
            return self.cmd_select_region()
        if self.game_suspended:          # khong chup khi game dang bi che / thu nho
            return
        self.overlay.set_status("↻ đang dịch lại…")
        self.worker.translate_once()

    # --- ho tro cho khung xem truoc trong cai dat ---
    def _capture_region(self):
        if not self.region:
            return None
        import mss
        from PIL import Image
        left, top, w, h = self.region
        with mss.mss() as sct:
            shot = sct.grab({"left": left, "top": top, "width": w, "height": h})
        return Image.frombytes("RGB", shot.size, shot.rgb)

    def _ocr_async(self, img, cfg, callback):
        def work():
            from . import ocr as ocr_mod
            try:
                text = ocr_mod.create(cfg).recognize(img).strip()
            except Exception as e:
                text = f"Lỗi OCR: {e}"
            self.post("call", callback, text)
        threading.Thread(target=work, daemon=True).start()

    def cmd_call(self, fn, *args):
        fn(*args)

    # --- tra tung tu ---
    def _lookup_word(self, word, callback):
        cfg = self.cfg

        def work():
            try:
                if self._lookup is None:
                    from .config import lang_info
                    from .lookup import WordLookup
                    self._lookup = WordLookup(lang_info(cfg["source_lang"])[3],
                                              lang_info(cfg["target_lang"])[3])
                result = self._lookup.lookup(word)
            except Exception as e:
                log.info("Tra tu '%s' that bai: %s", word, e)
                result = e
            self.post("lookup_result", callback, result)
        threading.Thread(target=work, daemon=True).start()

    def cmd_lookup_result(self, callback, result):
        callback(result)

    # --- chinh vung truc tiep ---
    def cmd_edit_region(self):
        if self.editor:                  # bam lai phim tat -> luu
            self.editor.finish(True)
            return
        if not self.region:
            return self.cmd_select_region()
        if self.selecting:
            return
        self.editor = RegionEditor(self.root, self.region, self._on_region_edited,
                                   hotkey=self.cfg["hotkeys"].get("edit_region", ""))

    def _on_region_edited(self, region):
        self.editor = None
        if not region:
            return
        self.region = region
        self.worker.move_region(region)
        # Neu vung dang gan voi mot app: luu vung moi cho app do
        if self.game_hwnd and self.game_origin and self.game_exe in self.cfg["profiles"]:
            ox, oy = self.game_origin
            rel = (region[0] - ox, region[1] - oy, region[2], region[3])
            self.game_base = (rel, self.game_size)
            prof = self.cfg["profiles"][self.game_exe]
            prof["region"] = list(rel)
            prof["client"] = list(self.game_size) if self.game_size else None
            config.save(self.cfg)
        self.overlay.set_status("vùng dịch đã cập nhật")
        self.worker.translate_once()

    # --- dich nhanh mot lan ---
    def cmd_quick_translate(self):
        if self.selecting:
            return
        if self.quick_popup:
            self.quick_popup.close()
        self.selecting = True
        RegionSelector(self.root, self._on_quick_region)

    def _on_quick_region(self, region):
        self.selecting = False
        if region is None:
            return
        popup = QuickPopup(self.root, self.cfg, region, on_close=self._on_quick_closed)
        self.quick_popup = popup
        cfg = self.cfg

        def work():
            import time
            import mss
            from PIL import Image
            from . import ocr as ocr_mod
            from .translator import Translator
            try:
                time.sleep(0.15)          # cho lop chon vung bien mat han
                left, top, w, h = region
                with mss.mss() as sct:
                    shot = sct.grab({"left": left, "top": top, "width": w, "height": h})
                img = Image.frombytes("RGB", shot.size, shot.rgb)
                scale = float(cfg.get("upscale", 1.0))
                if scale > 1.0:
                    img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
                from . import imgfilter
                img = imgfilter.apply(img, cfg.get("ocr_filter"))
                raw = ocr_mod.create(cfg).recognize(img).strip()
                if not raw:
                    self.post("quick_result", popup, "", "")
                    return
                original, translated = Translator(cfg).translate_dialogue(raw)
                self.post("quick_result", popup, original, translated)
            except Exception as e:
                log.exception("Dich nhanh that bai")
                self.post("quick_error", popup, str(e))
        threading.Thread(target=work, daemon=True).start()

    def cmd_quick_result(self, popup, original, translated):
        popup.show_result(original, translated)
        if translated:
            self.overlay.add_entry(original, translated)      # luu vao lich su

    def cmd_quick_error(self, popup, msg):
        popup.show_error(msg)

    def _on_quick_closed(self, popup):
        if self.quick_popup is popup:
            self.quick_popup = None
        self.editor = None                 # dang chinh vung (vien xanh)
        self._lookup = None

    def _show_overlay(self):
        """Hien khung dich, tru khi nguoi dung da tu an."""
        if not self.user_hidden:
            self.overlay.show()

    def cmd_toggle_overlay(self):
        if self.overlay.visible:
            self.cmd_hide_overlay()
        else:
            self.user_hidden = False
            self.overlay.show()

    def cmd_toggle_click_through(self):
        on = not self.overlay.click_through
        self.overlay.set_click_through(on)
        config.save(self.cfg)
        hk = self.cfg["hotkeys"].get("toggle_click_through") or "menu ở khay hệ thống"
        self.overlay.set_status(f"chuột xuyên qua: bật, tắt bằng {hk}" if on else "chuột xuyên qua: tắt")
        self._show_overlay()

    def cmd_hide_overlay(self):
        self.user_hidden = True
        self.overlay.hide()

    def cmd_result(self, original, translated):
        self.overlay.add_entry(original, translated)
        self._show_overlay()
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
                                       resume_hotkeys=self.register_hotkeys,
                                       hooks={"capture": self._capture_region,
                                              "ocr": self._ocr_async})

    def apply_config(self, cfg):
        """Luu cai dat va ap dung ngay, khong can khoi dong lai."""
        deleted = cfg.pop("_deleted_profiles", None)
        if deleted is not None:   # giu cac game vua luu trong luc cua so cai dat dang mo
            cfg["profiles"] = {k: v for k, v in self.cfg["profiles"].items() if k not in deleted}
        self._lookup = None              # ngon ngu co the da doi
        if cfg.get("ui_theme") != self.cfg.get("ui_theme"):
            theme.apply(self.root, cfg.get("ui_theme", "light"))
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
            item("quick_translate"),
            item("toggle_overlay"),
            item("toggle_click_through"),
            item("edit_region"),
            pystray.MenuItem("Quên vùng của app hiện tại", lambda: self.post("forget_game")),
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
    instance = SingleInstance()
    if not instance.acquire():
        log.info("App da dang chay, bat cua so cai dat cua ban dang chay")
        if not SingleInstance.notify("open_settings"):
            try:
                root = tk.Tk()
                root.withdraw()
                messagebox.showinfo("Screen Translator",
                                    "App đang chạy rồi. Tìm biểu tượng ở khay hệ thống "
                                    "(góc phải thanh taskbar).")
                root.destroy()
            except Exception:
                pass
        return
    app = App()
    instance.listen(lambda cmd: app.post(cmd) if cmd in ("open_settings",) else None)
    app.run()
