"""Khung hien thi ban dich: luon nam tren cung, keo de di chuyen, chuot phai mo menu."""
import tkinter as tk

from .winutil import exclude_from_capture


class Overlay:
    def __init__(self, root: tk.Tk, cfg: dict, on_menu):
        self.cfg = cfg["overlay"]
        self.on_menu = on_menu           # on_menu(command_name)
        self.original = ""
        self.translated = ""
        self.visible = False
        self._moved_by_user = False

        self.win = tk.Toplevel(root)
        self.win.withdraw()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", self.cfg["opacity"])
        self.win.configure(bg=self.cfg["bg"])

        font = (self.cfg["font_family"], self.cfg["font_size"])
        self.label = tk.Label(self.win, text="", justify="left", anchor="nw", font=font,
                              fg=self.cfg["fg"], bg=self.cfg["bg"], padx=10, pady=6)
        self.label.pack(fill="both", expand=True)
        self.status = tk.Label(self.win, text="", anchor="e", font=(self.cfg["font_family"], 8),
                               fg="#888888", bg=self.cfg["bg"], padx=6)
        self.status.pack(fill="x")

        for w in (self.label, self.status):
            w.bind("<ButtonPress-1>", self._start_move)
            w.bind("<B1-Motion>", self._move)
            w.bind("<Button-3>", self._popup)

        self.menu = tk.Menu(self.win, tearoff=0)
        self.menu.add_command(label="Chọn vùng mới", command=lambda: on_menu("select_region"))
        self.menu.add_command(label="Tạm dừng / tiếp tục", command=lambda: on_menu("toggle_auto"))
        self.menu.add_command(label="Dịch lại ngay", command=lambda: on_menu("translate_once"))
        self.menu.add_separator()
        self.menu.add_command(label="Copy bản dịch", command=lambda: self._copy(self.translated))
        self.menu.add_command(label="Copy chữ gốc", command=lambda: self._copy(self.original))
        self.menu.add_command(label="Hiện / ẩn chữ gốc", command=self._toggle_original)
        self.menu.add_separator()
        self.menu.add_command(label="Ẩn khung", command=self.hide)
        self.menu.add_command(label="Cài đặt…", command=lambda: on_menu("open_settings"))
        self.menu.add_command(label="Thoát", command=lambda: on_menu("quit"))

        exclude_from_capture(self.win)

    # --- vi tri ---
    def place_for_region(self, region):
        left, top, w, h = region
        width = max(w, self.cfg["min_width"])
        self.label.configure(wraplength=width - 20)
        pos = self.cfg["position"]
        if pos == "over":
            x, y = left, top
        elif pos == "above":
            self.win.update_idletasks()
            x, y = left, top - max(self.win.winfo_reqheight(), 60) - 4
        else:
            x, y = left, top + h + 4
        self.win.geometry(f"+{x}+{y}")
        self.win.minsize(width, 1)
        self._moved_by_user = False

    def _start_move(self, e):
        self._dx, self._dy = e.x_root - self.win.winfo_x(), e.y_root - self.win.winfo_y()

    def _move(self, e):
        self.win.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")
        self._moved_by_user = True

    # --- noi dung ---
    def show_text(self, original: str, translated: str):
        self.original, self.translated = original, translated
        self._render()
        self.show()

    def _render(self):
        text = self.translated
        if self.cfg.get("show_original") and self.original:
            text = f"{self.original}\n───\n{self.translated}"
        self.label.configure(text=text)

    def set_status(self, text: str):
        self.status.configure(text=text)

    def _toggle_original(self):
        self.cfg["show_original"] = not self.cfg.get("show_original")
        self._render()

    def _copy(self, text):
        self.win.clipboard_clear()
        self.win.clipboard_append(text)

    def _popup(self, e):
        self.menu.tk_popup(e.x_root, e.y_root)

    def show(self):
        self.win.deiconify()
        self.win.attributes("-topmost", True)
        self.visible = True

    def hide(self):
        self.win.withdraw()
        self.visible = False

    def toggle(self):
        self.hide() if self.visible else self.show()
