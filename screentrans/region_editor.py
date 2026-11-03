"""Hien vien vung dang dich va chinh truc tiep: keo canh / goc de doi kich thuoc,
keo tay nam de doi ca vung. Enter hoac phim tat de luu, Esc de huy."""
import tkinter as tk

from .winutil import exclude_from_capture

T = 6           # do day vien
C = 14          # kich thuoc o goc
MIN = 20        # vung nho nhat
COLOR = "#4c9aff"
CURSORS = {"n": "sb_v_double_arrow", "s": "sb_v_double_arrow", "w": "sb_h_double_arrow",
           "e": "sb_h_double_arrow", "nw": "top_left_corner", "ne": "top_right_corner",
           "sw": "bottom_left_corner", "se": "bottom_right_corner", "move": "fleur"}


class RegionEditor:
    def __init__(self, root, region, on_done, hotkey=""):
        self.on_done = on_done            # on_done((left, top, w, h)) hoac on_done(None) neu huy
        self.l, self.t, self.w, self.h = region
        self._orig = tuple(region)
        self.parts = {}
        for part in ("n", "s", "w", "e", "nw", "ne", "sw", "se"):
            self.parts[part] = self._window(root, part, bg=COLOR)
        # Tay nam: keo de doi ca vung, kem huong dan
        self.handle = self._window(root, "move", bg="#1f1f1f")
        tip = f"⠿  Kéo để dời vùng · kéo viền để chỉnh · Enter{' / ' + hotkey if hotkey else ''} lưu · Esc hủy"
        self.label = tk.Label(self.handle, text=tip, fg="white", bg="#1f1f1f",
                              font=("Segoe UI", 9), padx=8, pady=3, cursor=CURSORS["move"])
        self.label.pack()
        self._bind(self.label, "move")
        self.size_label = tk.Label(self.handle, text="", fg="#9a9a9a", bg="#1f1f1f",
                                   font=("Segoe UI", 8), padx=8)
        self.size_label.pack(anchor="w")
        self._bind(self.size_label, "move")
        self._layout()
        self.handle.focus_force()
        for win in [self.handle, *self.parts.values()]:
            win.bind("<Return>", lambda e: self.finish(True))
            win.bind("<KP_Enter>", lambda e: self.finish(True))
            win.bind("<Escape>", lambda e: self.finish(False))

    def _window(self, root, part, bg):
        w = tk.Toplevel(root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.configure(bg=bg, cursor=CURSORS[part])
        self._bind(w, part)
        exclude_from_capture(w)
        return w

    def _bind(self, widget, part):
        widget.bind("<ButtonPress-1>", lambda e, p=part: self._press(e, p))
        widget.bind("<B1-Motion>", self._drag)
        widget.bind("<Double-Button-1>", lambda e: self.finish(True))

    @staticmethod
    def _geo(win, x, y, w, h):
        win.geometry(f"{max(1, int(w))}x{max(1, int(h))}+{int(x)}+{int(y)}")

    def _layout(self):
        l, t, w, h = self.l, self.t, self.w, self.h
        p = self.parts
        self._geo(p["n"], l - T, t - T, w + 2 * T, T)
        self._geo(p["s"], l - T, t + h, w + 2 * T, T)
        self._geo(p["w"], l - T, t, T, h)
        self._geo(p["e"], l + w, t, T, h)
        for name, (cx, cy) in {"nw": (l, t), "ne": (l + w, t), "sw": (l, t + h),
                               "se": (l + w, t + h)}.items():
            self._geo(p[name], cx - C // 2, cy - C // 2, C, C)
        self.size_label.configure(text=f"{int(w)} × {int(h)}")
        self.handle.update_idletasks()
        hh = self.handle.winfo_reqheight()
        y = t - T - hh - 2 if t - T - hh - 2 > 0 else t + h + T + 2
        self.handle.geometry(f"+{int(l - T)}+{int(y)}")
        for win in [*p.values(), self.handle]:
            win.lift()

    def _press(self, e, part):
        self._part = part
        self._start = (e.x_root, e.y_root, self.l, self.t, self.w, self.h)

    def _drag(self, e):
        x0, y0, l, t, w, h = self._start
        dx, dy = e.x_root - x0, e.y_root - y0
        part = self._part
        if part == "move":
            l, t = l + dx, t + dy
        else:
            if "w" in part:
                dx = min(dx, w - MIN)
                l, w = l + dx, w - dx
            if "e" in part:
                w = max(MIN, w + dx)
            if "n" in part:
                dy = min(dy, h - MIN)
                t, h = t + dy, h - dy
            if "s" in part:
                h = max(MIN, h + dy)
        self.l, self.t, self.w, self.h = l, t, w, h
        self._layout()

    def region(self):
        return int(self.l), int(self.t), int(self.w), int(self.h)

    def finish(self, apply: bool):
        if getattr(self, "_closed", False):
            return
        self._closed = True
        for win in [*self.parts.values(), self.handle]:
            try:
                win.destroy()
            except tk.TclError:
                pass
        changed = apply and self.region() != self._orig
        self.on_done(self.region() if changed else None)
