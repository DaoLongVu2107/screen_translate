"""Dich nhanh mot lan (kieu Google Lens): khoanh vung -> hien o ban dich canh vung do."""
import tkinter as tk

from .overlay import _blend
from .winutil import exclude_from_capture, round_corners


class QuickPopup:
    def __init__(self, root, cfg: dict, region, on_close=None):
        o = cfg["overlay"]
        self.on_close = on_close
        fg, bg = o["fg"], o["bg"]
        family, size = o["font_family"], o["font_size"]
        self.translation = ""
        bar_bg = _blend(bg, "#ffffff", 0.08)

        self.win = w = tk.Toplevel(root)
        w.withdraw()
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.attributes("-alpha", max(0.9, o["opacity"]))
        w.configure(bg=bg)

        bar = tk.Frame(w, bg=bar_bg)
        bar.pack(fill="x")
        tk.Label(bar, text="Dịch nhanh", font=(family, 8), fg="#9a9a9a", bg=bar_bg,
                 padx=8, pady=2).pack(side="left")
        close = tk.Label(bar, text="✕", font=(family, 9), fg="#9a9a9a", bg=bar_bg, padx=8,
                         cursor="hand2")
        close.pack(side="right")
        close.bind("<Button-1>", lambda e: self.close())
        bar.bind("<Button-1>", lambda e: "break")
        self.copy_btn = tk.Label(bar, text="Copy", font=(family, 8), fg="#9a9a9a", bg=bar_bg,
                                 padx=8, cursor="hand2")
        self.copy_btn.pack(side="right")
        self.copy_btn.bind("<Button-1>", lambda e: self._copy())

        width = max(region[2], 320)
        self.orig = tk.Label(w, text="", font=(family, max(8, size - 4)), fg=_blend(fg, bg, 0.5),
                             bg=bg, justify="left", anchor="w", wraplength=width - 24, padx=12)
        self.orig.pack(fill="x", pady=(6, 0))
        self.text = tk.Label(w, text="Đang dịch…", font=(family, size), fg=fg, bg=bg,
                             justify="left", anchor="w", wraplength=width - 24, padx=12, pady=8)
        self.text.pack(fill="x")
        for wid in (w, self.orig, self.text):
            wid.bind("<Button-1>", lambda e: self.close())
        w.bind("<Escape>", lambda e: self.close())

        self._place(region, width)
        w.deiconify()
        exclude_from_capture(w)
        round_corners(w)
        w.focus_force()

    def _place(self, region, width):
        left, top, rw, rh = region
        self.win.update_idletasks()
        h = max(self.win.winfo_reqheight(), 80)
        screen_h = self.win.winfo_screenheight()
        y = top + rh + 6 if top + rh + 6 + h < screen_h else max(0, top - h - 6)
        self.win.geometry(f"{width}x{h}+{left}+{y}")
        self._region, self._width = region, width

    def show_result(self, original: str, translated: str):
        if not self.win.winfo_exists():
            return
        self.translation = translated
        self.orig.configure(text=original)
        self.text.configure(text=translated or "Không đọc được chữ trong vùng này.")
        self.win.geometry("")          # tinh lai chieu cao theo noi dung
        self._place(self._region, self._width)

    def show_error(self, msg: str):
        if self.win.winfo_exists():
            self.text.configure(text="Lỗi: " + msg.splitlines()[0][:200], fg="#ff6b6b")
            self.win.geometry("")
            self._place(self._region, self._width)

    def _copy(self):
        if self.translation:
            self.win.clipboard_clear()
            self.win.clipboard_append(self.translation)
            self.copy_btn.configure(text="Đã copy")
        return "break"

    def close(self):
        if getattr(self, "_closed", False):
            return "break"
        self._closed = True
        if self.win.winfo_exists():
            self.win.destroy()
        if self.on_close:
            self.on_close(self)
        return "break"
