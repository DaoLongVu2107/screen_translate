"""Cua so cai dat (giong Translumo): ngon ngu, nhan dang chu, may dich, giao dien, phim tat."""
import copy
import threading
import tkinter as tk
from tkinter import colorchooser, filedialog, font as tkfont, messagebox, ttk

import webbrowser

from .ai_translator import PROVIDERS as AI_PROVIDERS
from .config import DEFAULTS, HOTKEY_NAMES, LANGUAGES

POSITIONS = {"below": "Bên dưới vùng chọn", "above": "Bên trên vùng chọn", "over": "Đè lên vùng chọn"}
OCR_ENGINES = {"windows": "Windows OCR", "tesseract": "Tesseract"}
TRANSLATORS = {"google": "Google Dịch", "deepl": "DeepL",
               **{k: v[0] for k, v in AI_PROVIDERS.items()}}


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
        self._tab_games(self._tab(nb, "Game"))
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
        self._row(f, 0, "Ngôn ngữ gốc", self.src.widget,
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
        self._row(f, 2, "Tần suất quét",
                  ttk.Spinbox(f, from_=100, to=5000, increment=100, textvariable=self.interval, width=8),
                  "Tính bằng mili giây. Càng nhỏ thì dịch càng nhanh nhưng tốn CPU hơn.")

        self.sensitivity = tk.DoubleVar(value=self.cfg["change_threshold"] * 100)
        self._row(f, 4, "Ngưỡng thay đổi",
                  ttk.Spinbox(f, from_=0.5, to=30, increment=0.5, textvariable=self.sensitivity, width=8),
                  "Tính theo %. Tăng lên nếu nền có video, hiệu ứng động làm app dịch liên tục.")

        self.upscale = tk.DoubleVar(value=self.cfg["upscale"])
        self._row(f, 6, "Phóng to ảnh trước khi đọc",
                  ttk.Spinbox(f, from_=1, to=4, increment=0.5, textvariable=self.upscale, width=8),
                  "Giúp đọc chữ nhỏ chính xác hơn.")

    def _tab_translator(self, f):
        self.translator = _Choice(f, TRANSLATORS, self.cfg["translator"])
        self.translator.widget.bind("<<ComboboxSelected>>", lambda e: self._show_engine())
        self._row(f, 0, "Máy dịch", self.translator.widget)

        # DeepL
        self.deepl_frame = ttk.Frame(f)
        self.deepl_frame.columnconfigure(1, weight=1)
        self.deepl_key = tk.StringVar(value=self.cfg["deepl_api_key"])
        self._row(self.deepl_frame, 0, "DeepL API key", ttk.Entry(self.deepl_frame, textvariable=self.deepl_key, show="•"),
                  "Lấy miễn phí tại deepl.com/pro-api, chọn gói Free.")

        # AI: moi nha cung cap co key + model rieng
        self.ai_store = copy.deepcopy(self.cfg["ai"])
        self.ai_frame = af = ttk.Frame(f)
        af.columnconfigure(1, weight=1)
        self.ai_key = tk.StringVar()
        key_box = ttk.Frame(af)
        ttk.Entry(key_box, textvariable=self.ai_key, show="•").pack(side="left", fill="x", expand=True)
        ttk.Button(key_box, text="Lấy key", command=self._open_key_page).pack(side="left", padx=(4, 0))
        self._row(af, 0, "API key", key_box)

        self.ai_model = tk.StringVar()
        model_box = ttk.Frame(af)
        self.model_combo = ttk.Combobox(model_box, textvariable=self.ai_model, width=30)
        self.model_combo.pack(side="left", fill="x", expand=True)
        self.list_btn = ttk.Button(model_box, text="Tải danh sách", command=self._fetch_models)
        self.list_btn.pack(side="left", padx=(4, 0))
        self._row(af, 1, "Model", model_box, "Có thể gõ tên model bất kỳ. Bấm “Tải danh sách” để lấy "
                                             "các model mới nhất bằng key của bạn.")

        self.ai_context = tk.IntVar(value=self.cfg.get("ai_context_lines", 3))
        self._row(af, 3, "Số câu trước gửi kèm",
                  ttk.Spinbox(af, from_=0, to=10, textvariable=self.ai_context, width=8),
                  "Giúp AI hiểu mạch hội thoại, xưng hô nhất quán. 0 = không gửi.")

        ttk.Label(af, text="Ghi chú cho AI").grid(row=5, column=0, sticky="nw", pady=5)
        self.ai_notes = tk.Text(af, height=4, width=40, wrap="word", font=("Segoe UI", 9))
        self.ai_notes.insert("1.0", self.cfg.get("ai_notes", ""))
        self.ai_notes.grid(row=5, column=1, sticky="we", pady=5)
        ttk.Label(af, text="Ví dụ: “Doctor dịch là Tiến sĩ; giữ nguyên tên nhân vật; giọng văn trẻ trung.”",
                  foreground="#777", wraplength=380).grid(row=6, column=1, sticky="w")

        test_box = ttk.Frame(af)
        self.test_btn = ttk.Button(test_box, text="Thử dịch", command=self._test_ai)
        self.test_btn.pack(side="left")
        self.test_result = ttk.Label(test_box, text="", wraplength=300)
        self.test_result.pack(side="left", padx=8)
        test_box.grid(row=7, column=1, sticky="w", pady=(8, 0))

        self._current_ai = None
        self._show_engine()

    def _save_ai_fields(self):
        if self._current_ai:
            self.ai_store[self._current_ai] = {"api_key": self.ai_key.get().strip(),
                                               "model": self.ai_model.get().strip()}

    def _show_engine(self):
        self._save_ai_fields()
        engine = self.translator.get()
        self.deepl_frame.grid_forget()
        self.ai_frame.grid_forget()
        if engine == "deepl":
            self.deepl_frame.grid(row=1, column=0, columnspan=2, sticky="we")
        elif engine in AI_PROVIDERS:
            self.ai_frame.grid(row=1, column=0, columnspan=2, sticky="we")
            data = self.ai_store.get(engine, {})
            self.ai_key.set(data.get("api_key", ""))
            self.ai_model.set(data.get("model") or AI_PROVIDERS[engine][1][0])
            self.model_combo.configure(values=AI_PROVIDERS[engine][1])
            self.test_result.configure(text="")
        self._current_ai = engine if engine in AI_PROVIDERS else None

    def _open_key_page(self):
        if self._current_ai:
            webbrowser.open(AI_PROVIDERS[self._current_ai][2])

    def _run_bg(self, func, done):
        """Chay func() o luong nen roi goi done(ket_qua, loi) tren luong giao dien."""
        box = {}

        def work():
            try:
                box["result"] = func()
            except Exception as e:
                box["error"] = e
        t = threading.Thread(target=work, daemon=True)
        t.start()

        def wait():
            if not self.win.winfo_exists():
                return
            if t.is_alive():
                self.win.after(100, wait)
            else:
                done(box.get("result"), box.get("error"))
        wait()

    def _fetch_models(self):
        from .ai_translator import list_models
        provider, key = self._current_ai, self.ai_key.get().strip()
        if not key:
            messagebox.showinfo("Cài đặt", "Nhập API key trước.", parent=self.win)
            return
        self.list_btn.configure(state="disabled", text="Đang tải…")

        def done(models, err):
            self.list_btn.configure(state="normal", text="Tải danh sách")
            if err:
                messagebox.showerror("Cài đặt", f"Không tải được danh sách model:\n{err}", parent=self.win)
            elif models:
                self.model_combo.configure(values=models)
                self.model_combo.event_generate("<Down>")
        self._run_bg(lambda: list_models(provider, key), done)

    def _test_ai(self):
        from .ai_translator import AiTranslator
        provider = self._current_ai
        key, model = self.ai_key.get().strip(), self.ai_model.get().strip()
        dst = LANGUAGES[self.dst.get()][0]
        self.test_btn.configure(state="disabled")
        self.test_result.configure(text="Đang thử…", foreground="#777")

        def done(result, err):
            self.test_btn.configure(state="normal")
            if err:
                self.test_result.configure(text=f"Lỗi: {err}"[:200], foreground="#c00")
            else:
                self.test_result.configure(text=f"OK: {result}", foreground="#080")
        self._run_bg(lambda: AiTranslator(provider, key, model, "English", dst,
                                          context_lines=0).translate("Hello, how are you today?"), done)

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
        self._row(f, 5, "Độ đậm nền",
                  ttk.Spinbox(f, from_=20, to=100, increment=5, textvariable=self.opacity, width=8))

        self.show_original = tk.BooleanVar(value=o["show_original"])
        ttk.Checkbutton(f, text="Hiện cả chữ gốc phía trên bản dịch",
                        variable=self.show_original).grid(row=6, column=1, sticky="w", pady=5)

    def _tab_games(self, f):
        self.remember_games = tk.BooleanVar(value=self.cfg.get("remember_games", True))
        self.auto_start_games = tk.BooleanVar(value=self.cfg.get("auto_start_games", True))
        ttk.Checkbutton(f, text="Nhớ vùng dịch theo từng game", variable=self.remember_games
                        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Label(f, text="Khi chọn vùng trên cửa sổ game, app nhớ vùng đó theo game. Kéo cửa sổ "
                          "game đi đâu, vùng dịch đi theo; thu nhỏ hoặc tắt game thì tự dừng.",
                  foreground="#777", wraplength=440).grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(f, text="Tự bật dịch khi mở game đã lưu vùng", variable=self.auto_start_games
                        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 4))

        ttk.Label(f, text="Game đã lưu vùng:").grid(row=3, column=0, columnspan=2, sticky="w", pady=(12, 2))
        self.profiles = copy.deepcopy(self.cfg.get("profiles", {}))
        self._deleted_profiles = set()
        self.profile_list = tk.Listbox(f, height=6, activestyle="none")
        self.profile_list.grid(row=4, column=0, columnspan=2, sticky="we")
        self._fill_profiles()
        ttk.Button(f, text="Xóa game đã chọn", command=self._delete_profile
                   ).grid(row=5, column=0, sticky="w", pady=6)

    def _fill_profiles(self):
        self.profile_list.delete(0, "end")
        self._profile_keys = list(self.profiles)
        for exe in self._profile_keys:
            title = self.profiles[exe].get("title") or ""
            self.profile_list.insert("end", f"{exe}   —   {title}" if title else exe)
        if not self._profile_keys:
            self.profile_list.insert("end", "Chưa có. Bấm phím chọn vùng trên cửa sổ game để lưu.")

    def _delete_profile(self):
        sel = self.profile_list.curselection()
        if sel and self._profile_keys:
            exe = self._profile_keys[sel[0]]
            self.profiles.pop(exe, None)
            self._deleted_profiles.add(exe)
            self._fill_profiles()

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
        ttk.Label(f, text="Bấm “Đổi” rồi nhấn tổ hợp phím mới, Esc để hủy.",
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
        self._save_ai_fields()
        c["ai"] = copy.deepcopy(self.ai_store)
        c["ai_notes"] = self.ai_notes.get("1.0", "end").strip()
        c["ai_context_lines"] = int(self.ai_context.get())
        o = c["overlay"]
        o["position"] = self.position.get()
        o["font_family"] = self.font_family.get()
        o["font_size"] = int(self.font_size.get())
        o["fg"], o["bg"] = self.fg.get(), self.bg.get()
        o["opacity"] = max(0.2, min(1.0, int(self.opacity.get()) / 100))
        o["show_original"] = bool(self.show_original.get())
        c["hotkeys"] = {k: v.get() for k, v in self.hk_vars.items()}
        c["remember_games"] = bool(self.remember_games.get())
        c["auto_start_games"] = bool(self.auto_start_games.get())
        c["_deleted_profiles"] = sorted(self._deleted_profiles)
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
        if cfg["translator"] in AI_PROVIDERS and not cfg["ai"][cfg["translator"]]["api_key"]:
            messagebox.showerror("Cài đặt", "Cần nhập API key cho máy dịch AI.", parent=self.win)
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
