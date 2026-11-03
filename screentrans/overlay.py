"""Khung dich: luon nam tren cung, keo thanh tren de di chuyen, keo goc duoi-phai de doi
kich thuoc. Cau moi hien o duoi cung, cau cu bi day len tren thanh lich su (lan chuot de xem).
Keo bat ky cho nao tren khung de di chuyen."""
import tkinter as tk

from .winutil import exclude_from_capture, round_corners, set_click_through

MIN_W, MIN_H = 180, 70
MAX_ENTRIES = 200


def _blend(c1: str, c2: str, t: float) -> str:
    """Tron mau c1 voi c2 (t=0 -> c1, t=1 -> c2)."""
    try:
        a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
        b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
        return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))
    except (ValueError, IndexError):
        return c1


class Overlay:
    def __init__(self, root: tk.Tk, cfg: dict, on_menu, on_geometry=None, lookup=None):
        o = self.cfg = cfg["overlay"]
        self.lookup = lookup if cfg.get("word_lookup", True) else None   # lookup(tu, callback)
        self._hover_word = None
        self._hover_job = None
        self._tip = None
        self.on_menu = on_menu               # on_menu(command_name)
        self.on_geometry = on_geometry       # goi khi nguoi dung keo/doi kich thuoc xong
        self.entries: list[tuple[str, str]] = []
        self.max_entries = max(10, int(cfg.get("history_max", MAX_ENTRIES)))
        self.visible = False

        fg, bg = o["fg"], o["bg"]
        bar_bg = _blend(bg, "#ffffff", 0.08)
        dim = _blend(fg, bg, 0.45)
        family, size = o["font_family"], o["font_size"]

        self.win = w = tk.Toplevel(root)
        w.withdraw()
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.attributes("-alpha", o["opacity"])
        w.configure(bg=bg)
        w.minsize(MIN_W, MIN_H)

        # Thanh tren: keo de di chuyen, hien trang thai, nut an
        self.bar = tk.Frame(w, bg=bar_bg, cursor="fleur")
        self.bar.pack(fill="x", side="top")
        self.status = tk.Label(self.bar, text="", anchor="w", font=(family, 8), fg="#9a9a9a",
                               bg=bar_bg, padx=8, pady=2, cursor="fleur")
        self.status.pack(side="left", fill="x", expand=True)
        close = tk.Label(self.bar, text="✕", font=(family, 9), fg="#9a9a9a", bg=bar_bg,
                         padx=8, cursor="hand2")
        close.pack(side="right")
        close.bind("<Button-1>", lambda e: on_menu("hide_overlay"))
        close.bind("<Enter>", lambda e: close.configure(fg="#ffffff", bg="#c42b1c"))
        close.bind("<Leave>", lambda e: close.configure(fg="#9a9a9a", bg=bar_bg))
        self._bar_bg = bar_bg
        self.ct_label = tk.Label(self.bar, text="", font=(family, 8), fg="#5aa9f0", bg=bar_bg, padx=6)
        self.ct_label.pack(side="right")
        for wid in (self.bar, self.status):
            wid.bind("<ButtonPress-1>", self._start_move)
            wid.bind("<B1-Motion>", self._move)
            wid.bind("<ButtonRelease-1>", self._changed)

        # Noi dung: lich su dich
        self.text = tk.Text(w, wrap="word", bg=bg, fg=fg, font=(family, size), relief="flat",
                            bd=0, highlightthickness=0, padx=10, pady=6, cursor="arrow",
                            spacing3=max(4, size // 2), insertwidth=0,
                            selectbackground=_blend(bg, "#3a7bd5", 0.7))
        self.text.pack(fill="both", expand=True)
        self.text.tag_configure("old", foreground=dim)
        self.text.tag_configure("new", foreground=fg)
        self.text.tag_configure("orig", foreground=_blend(fg, bg, 0.6),
                                font=(family, max(8, size - 3)))
        self.text.tag_raise("orig")
        self.text.tag_configure("hover", underline=True, foreground=_blend(fg, "#4c9aff", 0.5))
        self.text.tag_raise("hover")
        self.text.bind("<Motion>", self._hover)
        self.text.bind("<Leave>", lambda e: self._hover_clear())
        self.text.configure(state="disabled")
        # Keo bat ky cho nao tren khung de di chuyen (copy chu qua menu chuot phai)
        self.text.bind("<ButtonPress-1>", lambda e: (self._start_move(e), "break")[1])
        self.text.bind("<B1-Motion>", lambda e: (self._move(e), "break")[1])
        self.text.bind("<ButtonRelease-1>", lambda e: (self._changed(), "break")[1])
        self.text.bind("<Double-Button-1>", lambda e: "break")
        self.text.configure(cursor="fleur")

        # Goc keo doi kich thuoc
        self.grip = tk.Label(w, text="◢", font=(family, 9), fg=dim, bg=bg,
                             cursor="bottom_right_corner")
        self.grip.place(relx=1.0, rely=1.0, anchor="se")
        self.grip.bind("<ButtonPress-1>", self._start_resize)
        self.grip.bind("<B1-Motion>", self._resize)
        self.grip.bind("<ButtonRelease-1>", self._changed)

        self.menu = m = tk.Menu(w, tearoff=0)
        m.add_command(label="Chọn vùng mới", command=lambda: on_menu("select_region"))
        m.add_command(label="Tạm dừng / tiếp tục", command=lambda: on_menu("toggle_auto"))
        m.add_command(label="Dịch lại ngay", command=lambda: on_menu("translate_once"))
        m.add_separator()
        m.add_command(label="Copy câu mới nhất", command=lambda: self._copy(self.latest()[1]))
        m.add_command(label="Copy chữ gốc mới nhất", command=lambda: self._copy(self.latest()[0]))
        m.add_command(label="Copy toàn bộ lịch sử", command=self._copy_all)
        m.add_command(label="Hiện / ẩn chữ gốc", command=self._toggle_original)
        m.add_command(label="Xóa lịch sử", command=self.clear)
        m.add_separator()
        m.add_command(label="Chuột bấm xuyên qua khung", command=lambda: on_menu("toggle_click_through"))
        m.add_command(label="Quên vùng của app này", command=lambda: on_menu("forget_game"))
        m.add_command(label="Cài đặt…", command=lambda: on_menu("open_settings"))
        m.add_command(label="Ẩn khung", command=lambda: on_menu("hide_overlay"))
        m.add_command(label="Thoát", command=lambda: on_menu("quit"))
        for wid in (self.bar, self.status, self.text, self.grip):
            wid.bind("<Button-3>", self._popup)
            wid.bind("<Control-MouseWheel>", self._wheel_opacity)

        exclude_from_capture(w)
        round_corners(w)
        self.click_through = False
        self.set_click_through(bool(o.get("click_through")))

    # --- vi tri & kich thuoc ---
    def geometry(self):
        self.win.update_idletasks()
        return (self.win.winfo_x(), self.win.winfo_y(),
                self.win.winfo_width(), self.win.winfo_height())

    def set_geometry(self, x, y, w, h):
        self.win.geometry(f"{max(MIN_W, int(w))}x{max(MIN_H, int(h))}+{int(x)}+{int(y)}")

    def move_by(self, dx, dy):
        x, y, w, h = self.geometry()
        self.set_geometry(x + dx, y + dy, w, h)

    def place_for_region(self, region):
        left, top, w, h = region
        width = max(w, self.cfg["min_width"])
        height = self.cfg.get("height", 160)
        pos = self.cfg["position"]
        if pos == "over":
            x, y = left, top
        elif pos == "above":
            x, y = left, top - height - 4
        else:
            x, y = left, top + h + 4
        self.set_geometry(x, y, width, height)

    def _start_move(self, e):
        self._hover_clear()
        self._dx, self._dy = e.x_root - self.win.winfo_x(), e.y_root - self.win.winfo_y()

    def _move(self, e):
        self.win.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    def _start_resize(self, e):
        self._rs = (e.x_root, e.y_root, self.win.winfo_width(), self.win.winfo_height())

    def _resize(self, e):
        x0, y0, w0, h0 = self._rs
        w, h = max(MIN_W, w0 + e.x_root - x0), max(MIN_H, h0 + e.y_root - y0)
        self.win.geometry(f"{w}x{h}")
        self.text.see("end")

    def _changed(self, e=None):
        if self.on_geometry:
            self.on_geometry(self.geometry())

    def _wheel_opacity(self, e):
        step = 0.05 if e.delta > 0 else -0.05
        self.cfg["opacity"] = round(max(0.2, min(1.0, self.cfg["opacity"] + step)), 2)
        self.win.attributes("-alpha", self.cfg["opacity"])
        if self.click_through:
            set_click_through(self.win, True)
        self.set_status(f"độ trong suốt {round((1 - self.cfg['opacity']) * 100)}%")
        self._changed()      # luu lai
        return "break"

    # --- tra tung tu khi re chuot vao chu goc ---
    def _hover(self, e):
        if not self.lookup:
            return
        t = self.text
        idx = t.index(f"@{e.x},{e.y}")
        if "orig" not in t.tag_names(idx):
            self._hover_clear()
            return
        start, end = t.index(f"{idx} wordstart"), t.index(f"{idx} wordend")
        word = t.get(start, end).strip(" .,!?;:\"'()[]{}…—-「」『』、。！？")
        if not word or len(word) > 30 or not any(c.isalpha() for c in word):
            self._hover_clear()
            return
        if word == self._hover_word:
            return
        self._hover_clear()
        self._hover_word = word
        t.tag_add("hover", start, end)
        x, y = e.x_root, e.y_root
        self._hover_job = self.win.after(
            350, lambda: self.lookup(word, lambda res: self._show_tip(word, res, x, y)))

    def _hover_clear(self):
        if self._hover_job:
            self.win.after_cancel(self._hover_job)
            self._hover_job = None
        self.text.tag_remove("hover", "1.0", "end")
        self._hover_word = None
        if self._tip is not None:
            try:
                self._tip.destroy()
            except tk.TclError:
                pass
            self._tip = None

    def _show_tip(self, word, result, x, y):
        if word != self._hover_word or not self.win.winfo_exists():
            return                       # chuot da roi khoi tu nay
        if self._tip is not None:
            self._tip.destroy()
        o = self.cfg
        fg, bg = o["fg"], _blend(o["bg"], "#ffffff", 0.12)
        family = o["font_family"]
        tip = self._tip = tk.Toplevel(self.win)
        tip.overrideredirect(True)
        tip.attributes("-topmost", True)
        tip.configure(bg=bg)
        tk.Label(tip, text=word, font=(family, 11, "bold"), fg=fg, bg=bg, anchor="w",
                 padx=10, pady=(4)).pack(fill="x")
        if isinstance(result, Exception):
            lines = [("", f"Không tra được: {result}")]
        else:
            main, senses = result
            lines = [("", main or "(không có nghĩa)")] + [(pos, ", ".join(terms)) for pos, terms
                                                       in senses[:4] if terms]
        for pos, text in lines:
            row = tk.Frame(tip, bg=bg)
            row.pack(fill="x", padx=10, pady=1)
            if pos:
                tk.Label(row, text=pos, font=(family, 9, "italic"), fg=_blend(fg, bg, 0.45),
                         bg=bg).pack(side="left", anchor="n")
            tk.Label(row, text=text, font=(family, 10), fg=fg, bg=bg, justify="left",
                     wraplength=320).pack(side="left", anchor="w", padx=(6 if pos else 0, 0))
        tk.Frame(tip, bg=bg, height=4).pack()
        tip.update_idletasks()
        sw, sh = tip.winfo_screenwidth(), tip.winfo_screenheight()
        tx = min(x + 14, sw - tip.winfo_reqwidth() - 4)
        ty = y + 18 if y + 18 + tip.winfo_reqheight() < sh else y - tip.winfo_reqheight() - 8
        tip.geometry(f"+{tx}+{ty}")
        exclude_from_capture(tip)

    # --- noi dung ---
    def latest(self):
        return self.entries[-1] if self.entries else ("", "")

    def show_text(self, original: str, translated: str):
        self.add_entry(original, translated)
        self.show()

    def add_entry(self, original: str, translated: str):
        if not translated:
            return
        self.entries.append((original, translated))
        t = self.text
        at_bottom = t.yview()[1] >= 0.999
        t.configure(state="normal")
        if len(self.entries) > 1:
            t.tag_remove("new", "1.0", "end")
            t.tag_add("old", "1.0", "end")
            t.insert("end", "\n")
        if self.cfg.get("show_original") and original:
            t.insert("end", original + "\n", ("orig",))
        t.insert("end", translated, ("new",))
        if len(self.entries) > self.max_entries:   # bo bot lich su qua cu
            self.entries = self.entries[-self.max_entries:]
            self._rerender()
        t.configure(state="disabled")
        if at_bottom:
            t.see("end")

    def _rerender(self):
        entries, self.entries = self.entries, []
        t = self.text
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.configure(state="disabled")
        for o, tr in entries:
            self.add_entry(o, tr)

    def clear(self):
        self.entries = []
        self._rerender()

    STATUS_COLORS = {"●": "#4cc26a", "❚": "#e0a43a", "⏳": "#e0a43a", "↻": "#5aa9f0", "⚠": "#ff6b6b"}

    def set_status(self, text: str):
        color = self.STATUS_COLORS.get(text[:1], "#9a9a9a")
        self.status.configure(text=text, fg=color)

    def _toggle_original(self):
        self.cfg["show_original"] = not self.cfg.get("show_original")
        self._rerender()
        self.text.see("end")

    def _copy(self, text):
        if text:
            self.win.clipboard_clear()
            self.win.clipboard_append(text)

    def _copy_all(self):
        self._copy("\n".join(t for _, t in self.entries))

    def _popup(self, e):
        self.menu.tk_popup(e.x_root, e.y_root)

    def set_click_through(self, enabled: bool):
        """Chuot bam xuyen qua khung dich xuong app ben duoi."""
        self.click_through = enabled
        self.cfg["click_through"] = enabled
        set_click_through(self.win, enabled)
        self.ct_label.configure(text="chuột xuyên qua" if enabled else "")

    def show(self):
        self.win.deiconify()
        self.win.attributes("-topmost", True)
        self.visible = True
        if self.click_through:           # dam bao van giu che do sau khi hien lai
            set_click_through(self.win, True)

    def hide(self):
        self.win.withdraw()
        self.visible = False

    def toggle(self):
        self.hide() if self.visible else self.show()
