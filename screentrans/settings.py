"""Cua so cai dat (giong Translumo): ngon ngu, nhan dang chu, may dich, giao dien, phim tat."""
import copy
import threading
import tkinter as tk
from tkinter import colorchooser, filedialog, font as tkfont, messagebox, ttk

from .config import DEFAULTS, HOTKEY_NAMES, LANGUAGES

POSITIONS = {"below": "Bên dưới vùng chọn", "above": "Bên trên vùng chọn", "over": "Đè lên vùng chọn"}
OCR_ENGINES = {"windows": "Windows OCR (có sẵn, nhanh)", "tesseract": "Tesseract"}
TRANSLATORS = {"google": "Google Dịch (miễn phí)", "deepl": "DeepL (cần API key)"}


class _Choice:
    """Combobox hien ten tieng Viet nhung tra ve ma."""

    def __init__(self, parent, mapping: dict, value: str, width=32):
        self.mapping = mapping
        self.var = tk.StringVar(value=mapping.get(value, next(iter(mapping.values()))))
        self.widget = ttk.Combobox(parent, textvariable=self.var, values=list(mapping.values()),
                                   state="readonly", width=width)

    def get(self) -> str:
        for k, v in self.mapping.items():
            if v == self.var.get():
                return k
        return next(iter(self.mapping))


class SettingsWindow:
    def __init__(self, root, cfg: dict, on_save, pause_hotkeys, resume_hotkeys):
        self.cfg = copy.deepcopy(cfg)
        self.on_save = on_save
        self.pause_hotkeys = pause_hotkeys
        self.resume_hotkeys = resume_hotkeys
        self._recording = None

        self.win = w = tk.Toplevel(root)
        w.title("Cài đặt – Screen Translator")
        w.resizable(False, False)
        w.attributes("-topmost", True)
        w.protocol("WM_DELETE_WINDOW", self.close)

        nb = ttk.Notebook(w)
        nb.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        self._tab_languages(self._tab(nb, "Ngôn ngữ"))
        self._tab_ocr(self._tab(nb, "Nhận dạng chữ"))
        self._tab_translator(self._tab(nb, "Dịch"))
        self._tab_appearance(self._tab(nb, "Giao diện"))
        self._tab_hotkeys(self._tab(nb, "Phím tắt"))

        bar = ttk.Frame(w)
        bar.pack(fill="x", padx=10, pady=10)
        ttk.Button(bar, text="Khôi phục mặc định", command=self.reset).pack(side="left")
        ttk.Button(bar, text="Hủy", command=self.close).pack(side="right")
        ttk.Button(bar, text="Lưu", command=self.save).pack(side="right", padx=6)
        w.focus_force()

    # --- tien ich dung giao dien ---
    @staticmethod
    def _tab(nb, title):
        f = ttk.Frame(nb, padding=14)
        f.columnconfigure(1, weight=1)
        nb.add(f, text=title)
        return f

    @staticmethod
    def _row(parent, r, label, widget, hint=None):
        ttk.Label(parent, text=label).grid(row=r, column=0, sticky="w", pady=5, padx=(0, 12))
        widget.grid(row=r, column=1, sticky="we", pady=5)
        if hint:
            ttk.Label(parent, text=hint, foreground="#777", wraplength=380).grid(
                row=r + 1, column=1, sticky="w")

    # --- cac tab ---
    def _tab_languages(self, f):
        names = {k: v[0] for k, v in LANGUAGES.items()}
        self.src = _Choice(f, names, self.cfg["source_lang"])
        self.dst = _Choice(f, names, self.cfg["target_lang"])
        self._row(f, 0, "Ngôn ngữ gốc (trên màn hình)", self.src.widget,
                  "Với Windows OCR, máy cần cài gói ngôn ngữ này: Settings → Time & language → "
                  "Language & region → Add a language.")
        self._row(f, 2, "Dịch sang", self.dst.widget)

    def _tab_ocr(self, f):
        self.engine = _Choice(f, OCR_ENGINES, self.cfg["ocr_engine"])
        self._row(f, 0, "Bộ nhận dạng chữ", self.engine.widget)

        self.tess = tk.StringVar(value=self.cfg["tesseract_cmd"])
        box = ttk.Frame(f)
        ttk.Entry(box, textvariable=self.tess).pack(side="left", fill="x", expand=True)
        ttk.Button(box, text="…", width=3, command=self._browse_tesseract).pack(side="left", padx=(4, 0))
        self._row(f, 1, "Đường dẫn tesseract.exe", box)

        self.interval = tk.IntVar(value=self.cfg["interval_ms"])
        self._row(f, 2, "Tần suất quét (ms)",
                  ttk.Spinbox(f, from_=100, to=5000, increment=100, textvariable=self.interval, width=8),
                  "Càng nhỏ thì dịch càng nhanh nhưng tốn CPU hơn.")

        self.sensitivity = tk.DoubleVar(value=self.cfg["change_threshold"] * 100)
        self._row(f, 4, "Ngưỡng thay đổi (%)",
                  ttk.Spinbox(f, from_=0.5, to=30, increment=0.5, textvariable=self.sensitivity, width=8),
                  "Tăng lên nếu nền động (video, hiệu ứng) làm app dịch liên tục.")

        self.upscale = tk.DoubleVar(value=self.cfg["upscale"])
        self._row(f, 6, "Phóng to ảnh trước khi đọc",
                  ttk.Spinbox(f, from_=1, to=4, increment=0.5, textvariable=self.upscale, width=8),
                  "Giúp đọc chữ nhỏ chính xác hơn.")

    def _tab_translator(self, f):
        self.translator = _Choice(f, TRANSLATORS, self.cfg["translator"])
        self._row(f, 0, "Máy dịch", self.translator.widget)
        self.deepl_key = tk.StringVar(value=self.cfg["deepl_api_key"])
        self._row(f, 1, "DeepL API key", ttk.Entry(f, textvariable=self.deepl_key, show="•"),
                  "Lấy miễn phí tại deepl.com/pro-api (gói Free).")

    def _tab_appearance(self, f):
        o = self.cfg["overlay"]
        self.position = _Choice(f, POSITIONS, o["position"])
        self._row(f, 0, "Vị trí khung dịch", self.position.widget)

        families = sorted(set(tkfont.families()))
        self.font_family = tk.StringVar(value=o["font_family"])
        self._row(f, 1, "Phông chữ", ttk.Combobox(f, textvariable=self.font_family, values=families))

        self.font_size = tk.IntVar(value=o["font_size"])
        self._row(f, 2, "Cỡ chữ", ttk.Spinbox(f, from_=8, to=48, textvariable=self.font_size, width=8))

        self.fg = tk.StringVar(value=o["fg"])
        self.bg = tk.StringVar(value=o["bg"])
        self._row(f, 3, "Màu chữ", self._color_button(f, self.fg))
        self._row(f, 4, "Màu nền", self._color_button(f, self.bg))

        self.opacity = tk.IntVar(value=int(o["opacity"] * 100))
        self._row(f, 5, "Độ đậm nền (%)",
                  ttk.Spinbox(f, from_=20, to=100, increment=5, textvariable=self.opacity, width=8))

        self.show_original = tk.BooleanVar(value=o["show_original"])
        ttk.Checkbutton(f, text="Hiện cả chữ gốc phía trên bản dịch",
                        variable=self.show_original).grid(row=6, column=1, sticky="w", pady=5)

    def _tab_hotkeys(self, f):
        self.hk_vars = {}
        for r, (key, label) in enumerate(HOTKEY_NAMES.items()):
            var = tk.StringVar(value=self.cfg["hotkeys"].get(key, ""))
            self.hk_vars[key] = var
            box = ttk.Frame(f)
            ttk.Entry(box, textvariable=var, state="readonly", width=20).pack(side="left")
            ttk.Button(box, text="Đổi", width=5,
                       command=lambda k=key: self._record(k)).pack(side="left", padx=4)
            ttk.Button(box, text="Xóa", width=5, command=lambda v=var: v.set("")).pack(side="left")
            self._row(f, r, label, box)
        ttk.Label(f, text="Bấm “Đổi” rồi nhấn tổ hợp phím mới (Esc để hủy).",
                  foreground="#777").grid(row=len(HOTKEY_NAMES), column=1, sticky="w", pady=(8, 0))

    # --- hanh dong ---
    def _color_button(self, parent, var):
        btn = tk.Button(parent, width=10, relief="groove", bg=var.get(), activebackground=var.get())

        def pick():
            c = colorchooser.askcolor(var.get(), parent=self.win)[1]
            if c:
                var.set(c)
                btn.configure(bg=c, activebackground=c)
        btn.configure(command=pick)
        return btn

    def _browse_tesseract(self):
        path = filedialog.askopenfilename(parent=self.win, title="Chọn tesseract.exe",
                                          filetypes=[("tesseract.exe", "tesseract.exe"), ("*", "*")])
        if path:
            self.tess.set(path)

    def _record(self, key):
        if self._recording:
            return
        try:
            import keyboard
        except ImportError:
            return
        var = self.hk_vars[key]
        old = var.get()
        var.set("Nhấn phím…")
        self.pause_hotkeys()
        result = {}

        def worker():
            try:
                result["hk"] = keyboard.read_hotkey(suppress=False)
            except Exception:
                result["hk"] = None
        self._recording = threading.Thread(target=worker, daemon=True)
        self._recording.start()

        def wait():
            if self._recording.is_alive():
                self.win.after(50, wait)
                return
            self._recording = None
            hk = result.get("hk")
            var.set(old if not hk or hk == "esc" else hk)
            self.resume_hotkeys()
        wait()

    def _collect(self) -> dict:
        c = self.cfg
        c["source_lang"], c["target_lang"] = self.src.get(), self.dst.get()
        c["ocr_engine"] = self.engine.get()
        c["tesseract_cmd"] = self.tess.get().strip()
        c["interval_ms"] = int(self.interval.get())
        c["change_threshold"] = float(self.sensitivity.get()) / 100
        c["upscale"] = float(self.upscale.get())
        c["translator"] = self.translator.get()
        c["deepl_api_key"] = self.deepl_key.get().strip()
        o = c["overlay"]
        o["position"] = self.position.get()
        o["font_family"] = self.font_family.get()
        o["font_size"] = int(self.font_size.get())
        o["fg"], o["bg"] = self.fg.get(), self.bg.get()
        o["opacity"] = max(0.2, min(1.0, int(self.opacity.get()) / 100))
        o["show_original"] = bool(self.show_original.get())
        c["hotkeys"] = {k: v.get() for k, v in self.hk_vars.items()}
        return c

    def save(self):
        try:
            cfg = self._collect()
        except (tk.TclError, ValueError):
            messagebox.showerror("Cài đặt", "Có ô nhập số không hợp lệ.", parent=self.win)
            return
        used = [h for h in cfg["hotkeys"].values() if h]
        if len(used) != len(set(used)):
            messagebox.showerror("Cài đặt", "Có hai chức năng đang dùng chung một phím tắt.",
                                 parent=self.win)
            return
        if cfg["translator"] == "deepl" and not cfg["deepl_api_key"]:
            messagebox.showerror("Cài đặt", "Cần nhập DeepL API key.", parent=self.win)
            return
        self.on_save(cfg)
        self.close()

    def reset(self):
        if messagebox.askyesno("Cài đặt", "Đưa mọi cài đặt về mặc định?", parent=self.win):
            self.on_save(copy.deepcopy(DEFAULTS))
            self.close()

    def close(self):
        if self._recording:      # dang cho nhan phim tat
            return
        self.win.destroy()
