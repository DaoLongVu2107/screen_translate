"""Lop phu toan man hinh de keo chuot chon vung can dich."""
import tkinter as tk

from .winutil import virtual_screen


class RegionSelector:
    def __init__(self, root: tk.Tk, on_done):
        self.on_done = on_done           # on_done((left, top, w, h)) hoac on_done(None)
        vx, vy, vw, vh = virtual_screen()
        self.vx, self.vy = vx, vy

        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.35)
        self.win.geometry(f"{vw}x{vh}+{vx}+{vy}")
        self.win.configure(cursor="crosshair", bg="black")

        self.canvas = tk.Canvas(self.win, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_text(vw // 2, 40, fill="white", font=("Segoe UI", 16),
                                text="Kéo chuột để chọn vùng cần dịch  •  Esc / chuột phải để hủy")
        self.rect = None
        self.start = None

        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<ButtonPress-3>", lambda e: self._finish(None))
        self.win.bind("<Escape>", lambda e: self._finish(None))
        self.win.focus_force()
        self.win.grab_set()

    def _press(self, e):
        self.start = (e.x, e.y)
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(e.x, e.y, e.x, e.y, outline="#00E5FF",
                                                 width=2, fill="white")

    def _drag(self, e):
        if self.start:
            self.canvas.coords(self.rect, *self.start, e.x, e.y)

    def _release(self, e):
        if not self.start:
            return
        x1, y1 = self.start
        x2, y2 = e.x, e.y
        left, top = min(x1, x2), min(y1, y2)
        w, h = abs(x2 - x1), abs(y2 - y1)
        if w < 8 or h < 8:
            self._finish(None)
            return
        self._finish((left + self.vx, top + self.vy, w, h))

    def _finish(self, region):
        try:
            self.win.grab_release()
        finally:
            self.win.destroy()
        self.on_done(region)
