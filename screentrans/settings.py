"""Cua so cai dat (giong Translumo): ngon ngu, nhan dang chu, may dich, giao dien, phim tat."""
import copy
import threading
import tkinter as tk
from tkinter import colorchooser, filedialog, font as tkfont, messagebox, ttk

import webbrowser

from .ai_translator import PROVIDERS as AI_PROVIDERS
from .config import DEFAULTS, HOTKEY_NAMES, LANGUAGES
from . import theme
from .winutil import dark_title_bar

HINT = "#8a8a8a"
LABEL_W = 175         # cot nhan co dinh de cac o thang hang

# ten, mau chu, mau nen
THEMES = [("Tối", "#FFFFFF", "#101010"), ("Sáng", "#111111", "#F5F5F5"),
          ("Phụ đề vàng", "#FFE14D", "#000000"), ("Xanh đêm", "#E8F1FF", "#0F2A4A"),
          ("Xanh lá", "#B8FFB0", "#0B1F0E")]

UI_THEMES = {"light": "Sáng", "dark": "Tối"}
OVERLAY_MODES = {"history": "Lịch sử các câu", "subtitle": "Phụ đề câu mới nhất"}

POSITIONS = {"below": "Bên dưới vùng chọn", "above": "Bên trên vùng chọn", "over": "Đè lên vùng chọn"}
OCR_ENGINES = {"windows": "Windows OCR", "tesseract": "Tesseract"}
TRANSLATORS = {"google": "Google Dịch", "google_cloud": "Google Cloud Translation", "deepl": "DeepL",
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
    def __init__(self, root, cfg: dict, on_save, pause_hotkeys, resume_hotkeys, hooks=None):
        self.hooks = hooks or {}          # capture() -> anh vung dich; ocr(anh, cfg, callback)
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
        w.configure(bg=theme.palette()["bg"])
        if theme.current == "dark":     # dat sau khi cua so hien de Windows ve lai thanh tieu de
            w.after(30, lambda: (dark_title_bar(w), w.withdraw(), w.deiconify()))

        head = ttk.Frame(w, padding=(18, 14, 18, 0))
        head.pack(fill="x")
        ttk.Label(head, text="Cài đặt", style="Title.TLabel").pack(side="left")
        # Dai bao loi cai dat (to do), an khi khong co loi
        self.banner = tk.Label(w, text="", justify="left", anchor="w", wraplength=700, padx=12, pady=8,
                               fg="#a4262c" if theme.current == "light" else "#ff9b9b",
                               bg="#fde7e9" if theme.current == "light" else "#442726")

        nb = self.nb = ttk.Notebook(w)
        nb.pack(fill="both", expand=True, padx=18, pady=(10, 0))
        self._tab_languages(self._tab(nb, "Ngôn ngữ"))
        self._tab_ocr(self._tab(nb, "Nhận dạng"))
        self._tab_translator(self._tab(nb, "Dịch"))
        self._tab_appearance(self._tab(nb, "Giao diện"))
        self._tab_games(self._tab(nb, "App"))
        self._tab_filter(self._tab(nb, "Lọc ảnh"))
        self._tab_subs(self._tab(nb, "Thay thế"))
        self._tab_advanced(self._tab(nb, "Nâng cao"))
        self._tab_system(self._tab(nb, "Hệ thống"))
        self._tab_hotkeys(self._tab(nb, "Phím tắt"))

        bar = ttk.Frame(w)
        bar.pack(fill="x", padx=18, pady=14)
        ttk.Button(bar, text="Khôi phục mặc định", command=self.reset).pack(side="left")
        ttk.Button(bar, text="Hủy", command=self.close).pack(side="right")
        ttk.Button(bar, text="Lưu", style="Accent.TButton", command=self.save).pack(side="right", padx=8)
        w.focus_force()
        # Kiem tra cai dat sai ngay khi mo
        try:
            from .validate import validate
            self._mark_problems(validate(self.cfg, deep=True, hotkey_errors=self.hooks.get("hotkey_errors")))
        except Exception:
            pass

    # --- tien ich dung giao dien ---
    @staticmethod
    def _tab(nb, title):
        f = ttk.Frame(nb, padding=(18, 16))
        f.columnconfigure(0, minsize=LABEL_W)
        f.columnconfigure(1, weight=1)
        nb.add(f, text=title)
        return f

    @staticmethod
    def _row(parent, r, label, widget, hint=None):
        ttk.Label(parent, text=label).grid(row=r, column=0, sticky="w", pady=6, padx=(0, 16))
        widget.grid(row=r, column=1, sticky="we", pady=6)
        if hint:
            ttk.Label(parent, text=hint, foreground=theme.palette()["hint"], wraplength=440).grid(
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

        self.upscale = tk.DoubleVar(value=self.cfg["upscale"])
        self._row(f, 6, "Phóng to ảnh trước khi đọc",
                  ttk.Spinbox(f, from_=1, to=4, increment=0.5, textvariable=self.upscale, width=8),
                  "Giúp đọc chữ nhỏ chính xác hơn.")

    def _tab_translator(self, f):
        from .translator import engine_chain
        # Thu tu may dich: may tren cung dung truoc, loi thi chuyen may ke tiep
        self.chain = engine_chain(self.cfg)
        cbox = ttk.Frame(f)
        self.chain_list = tk.Listbox(cbox, height=4, activestyle="none", exportselection=False,
                                     font=("Segoe UI", 10),
                                     **{k: v for k, v in theme.field_options().items()
                                        if k != "insertbackground"})
        self.chain_list.pack(side="left", fill="x", expand=True)
        self.chain_list.bind("<<ListboxSelect>>", lambda e: self._chain_selected())
        btns = ttk.Frame(cbox)
        btns.pack(side="left", padx=(6, 0), anchor="n")
        for text, cmd in (("Lên", lambda: self._chain_move(-1)), ("Xuống", lambda: self._chain_move(1)),
                          ("Xóa", self._chain_remove)):
            ttk.Button(btns, text=text, width=6, command=cmd).pack(pady=(0, 3))
        self._row(f, 0, "Thứ tự máy dịch", cbox,
                  "Dùng máy trên cùng trước; máy đó bị chặn, mất mạng hay lỗi thì tự chuyển sang máy kế tiếp.")

        pick = ttk.Frame(f)
        self.translator = _Choice(pick, TRANSLATORS, self.chain[0], width=26)
        self.translator.widget.pack(side="left")
        self.translator.widget.bind("<<ComboboxSelected>>", lambda e: self._show_engine())
        ttk.Button(pick, text="Thêm vào thứ tự", command=self._chain_add).pack(side="left", padx=(6, 0))
        self._row(f, 2, "Máy dịch", pick, "Chọn một máy để xem và nhập API key, model của máy đó.")

        # DeepL
        self.deepl_frame = ttk.Frame(f)
        self.deepl_frame.columnconfigure(0, minsize=LABEL_W)
        self.deepl_frame.columnconfigure(1, weight=1)
        self.deepl_key = tk.StringVar(value=self.cfg["deepl_api_key"])
        self._row(self.deepl_frame, 0, "DeepL API key", ttk.Entry(self.deepl_frame, textvariable=self.deepl_key, show="•"),
                  "Lấy miễn phí tại deepl.com/pro-api, chọn gói Free.")

        # Google Cloud Translation
        self.gcloud_frame = ttk.Frame(f)
        self.gcloud_frame.columnconfigure(0, minsize=LABEL_W)
        self.gcloud_frame.columnconfigure(1, weight=1)
        self.gcloud_key = tk.StringVar(value=self.cfg.get("google_cloud_api_key", ""))
        gbox = ttk.Frame(self.gcloud_frame)
        ttk.Entry(gbox, textvariable=self.gcloud_key, show="•").pack(side="left", fill="x", expand=True)
        ttk.Button(gbox, text="Lấy key", command=lambda: webbrowser.open(
            "https://console.cloud.google.com/apis/library/translate.googleapis.com")).pack(side="left", padx=(4, 0))
        self._row(self.gcloud_frame, 0, "Google Cloud API key", gbox,
                  "Bản chính thức của Google Dịch, không bị chặn khi dịch nhiều. Bật “Cloud Translation API” "
                  "trong Google Cloud rồi tạo API key ở mục Credentials. Mỗi tháng được miễn phí một lượng ký tự.")

        # AI: moi nha cung cap co key + model rieng
        self.ai_store = copy.deepcopy(self.cfg["ai"])
        self.ai_frame = af = ttk.Frame(f)
        af.columnconfigure(0, minsize=LABEL_W)
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
        self.ai_notes = tk.Text(af, height=4, width=40, wrap="word", font=("Segoe UI", 10),
                                padx=8, pady=6, **theme.field_options())
        self.ai_notes.insert("1.0", self.cfg.get("ai_notes", ""))
        self.ai_notes.grid(row=5, column=1, sticky="we", pady=5)
        ttk.Label(af, text="Ví dụ: “Doctor dịch là Tiến sĩ; giữ nguyên tên nhân vật; giọng văn trẻ trung.”",
                  foreground=theme.palette()["hint"], wraplength=380).grid(row=6, column=1, sticky="w")

        test_box = ttk.Frame(af)
        self.test_btn = ttk.Button(test_box, text="Thử dịch", command=self._test_ai)
        self.test_btn.pack(side="left")
        self.test_result = ttk.Label(test_box, text="", wraplength=300)
        self.test_result.pack(side="left", padx=8)
        test_box.grid(row=7, column=1, sticky="w", pady=(8, 0))

        # Xu ly chu truoc khi dich (ap dung cho moi may dich)
        opts = ttk.Frame(f)
        opts.grid(row=5, column=0, columnspan=2, sticky="we", pady=(14, 0))
        ttk.Separator(opts).pack(fill="x", pady=(0, 10))
        self.clean_ocr = tk.BooleanVar(value=self.cfg.get("clean_ocr", True))
        self.split_speaker = tk.BooleanVar(value=self.cfg.get("split_speaker", True))
        for var, text in ((self.clean_ocr, "Làm sạch chữ OCR trước khi dịch"),
                          (self.split_speaker, "Tách tên người nói, giữ nguyên tên")):
            ttk.Checkbutton(opts, text=text, variable=var).pack(anchor="w", pady=2)

        nums = ttk.Frame(f)
        nums.grid(row=6, column=0, columnspan=2, sticky="we", pady=(8, 0))
        nums.columnconfigure(0, minsize=LABEL_W)
        nums.columnconfigure(1, weight=1)
        self.google_ctx = tk.IntVar(value=self.cfg.get("google_context_lines", 0))
        self._row(nums, 0, "Câu trước gửi kèm",
                  ttk.Spinbox(nums, from_=0, to=5, textvariable=self.google_ctx, width=8),
                  "Số câu trước gửi kèm cho Google Dịch miễn phí, 0 là tắt. Google trả về không tách đúng "
                  "thì tự dịch riêng câu hiện tại.")
        self.send_gap = tk.DoubleVar(value=self.cfg.get("min_send_gap", 1.0))
        self._row(nums, 2, "Giãn cách gửi dịch",
                  ttk.Spinbox(nums, from_=0.2, to=10, increment=0.1, textvariable=self.send_gap,
                              width=8, format="%.1f"),
                  "Tính bằng giây: hai lần gửi dịch cách nhau ít nhất bấy nhiêu. Tăng lên nếu hay "
                  "bị Google chặn, giảm xuống nếu muốn câu mới hiện nhanh hơn.")

        self._current_ai = None
        self._chain_refresh(0)
        self._show_engine()

    def _chain_refresh(self, select=None):
        self.chain_list.delete(0, "end")
        for i, eng in enumerate(self.chain, 1):
            self.chain_list.insert("end", f"{i}. {TRANSLATORS.get(eng, eng)}")
        if select is not None and self.chain:
            self.chain_list.selection_set(select)
            self.chain_list.see(select)

    def _chain_selected(self):
        sel = self.chain_list.curselection()
        if sel:
            self.translator.var.set(TRANSLATORS[self.chain[sel[0]]])
            self._show_engine()

    def _chain_add(self):
        eng = self.translator.get()
        if eng not in self.chain:
            self.chain.append(eng)
        self._chain_refresh(self.chain.index(eng))

    def _chain_move(self, step):
        sel = self.chain_list.curselection()
        if not sel:
            return
        i, j = sel[0], sel[0] + step
        if 0 <= j < len(self.chain):
            self.chain[i], self.chain[j] = self.chain[j], self.chain[i]
            self._chain_refresh(j)

    def _chain_remove(self):
        sel = self.chain_list.curselection()
        if not sel:
            return
        if len(self.chain) == 1:
            messagebox.showinfo("Cài đặt", "Cần giữ ít nhất một máy dịch.", parent=self.win)
            return
        del self.chain[sel[0]]
        self._chain_refresh(min(sel[0], len(self.chain) - 1))

    def _save_ai_fields(self):
        if self._current_ai:
            self.ai_store[self._current_ai] = {"api_key": self.ai_key.get().strip(),
                                               "model": self.ai_model.get().strip()}

    def _show_engine(self):
        self._save_ai_fields()
        engine = self.translator.get()
        self.deepl_frame.grid_forget()
        self.gcloud_frame.grid_forget()
        self.ai_frame.grid_forget()
        if engine == "deepl":
            self.deepl_frame.grid(row=4, column=0, columnspan=2, sticky="we")
        elif engine == "google_cloud":
            self.gcloud_frame.grid(row=4, column=0, columnspan=2, sticky="we")
        elif engine in AI_PROVIDERS:
            self.ai_frame.grid(row=4, column=0, columnspan=2, sticky="we")
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
        self.test_result.configure(text="Đang thử…", foreground=theme.palette()["hint"])

        def done(result, err):
            self.test_btn.configure(state="normal")
            if err:
                self.test_result.configure(text=f"Lỗi: {err}"[:200], foreground="#ff6b6b" if theme.current == "dark" else "#c42b1c")
            else:
                self.test_result.configure(text=f"OK: {result}", foreground="#5cd65c" if theme.current == "dark" else "#0f7b0f")
        self._run_bg(lambda: AiTranslator(provider, key, model, "English", dst,
                                          context_lines=0).translate("Hello, how are you today?"), done)

    def _tab_appearance(self, f):
        o = self.cfg["overlay"]
        # Kieu khung dich + co chu phu de
        mbox = ttk.Frame(f)
        self.ov_mode = _Choice(mbox, OVERLAY_MODES, o.get("mode", "history"), width=20)
        self.ov_mode.widget.pack(side="left")
        ttk.Label(mbox, text="Cỡ chữ phụ đề").pack(side="left", padx=(14, 6))
        self.sub_size = tk.IntVar(value=int(o.get("subtitle_font_size", 24)))
        ttk.Spinbox(mbox, from_=12, to=72, textvariable=self.sub_size, width=5).pack(side="left")
        self._row(f, 0, "Kiểu khung dịch", mbox,
                  "Phụ đề chỉ hiện câu mới nhất, chữ to, căn giữa phía dưới màn hình.")

        self.position = _Choice(f, POSITIONS, o["position"])
        self._row(f, 2, "Vị trí khung dịch", self.position.widget)

        # Phong chu + co chu tren mot dong
        fbox = ttk.Frame(f)
        families = sorted(set(tkfont.families()))
        self.font_family = tk.StringVar(value=o["font_family"])
        ttk.Combobox(fbox, textvariable=self.font_family, values=families, width=22).pack(side="left")
        ttk.Label(fbox, text="Cỡ chữ").pack(side="left", padx=(14, 6))
        self.font_size = tk.IntVar(value=o["font_size"])
        ttk.Spinbox(fbox, from_=8, to=48, textvariable=self.font_size, width=5).pack(side="left")
        self._row(f, 3, "Phông chữ", fbox)

        # Mau chu + mau nen tren mot dong, mau co san ben duoi
        self.fg = tk.StringVar(value=o["fg"])
        self.bg = tk.StringVar(value=o["bg"])
        cbox = ttk.Frame(f)
        self._fg_btn = self._color_button(cbox, self.fg)
        self._bg_btn = self._color_button(cbox, self.bg)
        ttk.Label(cbox, text="Chữ").pack(side="left", padx=(0, 6))
        self._fg_btn.configure(width=6)
        self._fg_btn.pack(side="left")
        ttk.Label(cbox, text="Nền").pack(side="left", padx=(14, 6))
        self._bg_btn.configure(width=6)
        self._bg_btn.pack(side="left")
        self._row(f, 4, "Màu", cbox)
        presets = ttk.Frame(f)
        for name, fg, bg in THEMES:
            tk.Button(presets, text=name, fg=fg, bg=bg, activeforeground=fg, activebackground=bg,
                      relief="flat", bd=0, padx=10, pady=3, cursor="hand2",
                      command=lambda a=fg, b=bg: self._set_colors(a, b)).pack(side="left", padx=(0, 4))
        self._row(f, 5, "Mẫu màu", presets)

        self.transparency = tk.IntVar(value=round((1 - o["opacity"]) * 100))
        tbox = ttk.Frame(f)
        tlabel = ttk.Label(tbox, width=5)
        ttk.Scale(tbox, from_=0, to=80, variable=self.transparency, orient="horizontal",
                  command=lambda v: tlabel.configure(text=f"{round(float(v))}%")
                  ).pack(side="left", fill="x", expand=True)
        tlabel.pack(side="left", padx=(6, 0))
        tlabel.configure(text=f"{self.transparency.get()}%")
        self._row(f, 6, "Độ trong suốt", tbox,
                  "Áp dụng cho cả khung lẫn chữ. Giữ Ctrl và lăn chuột trên khung dịch để chỉnh nhanh.")

        self.show_original = tk.BooleanVar(value=o["show_original"])
        self.word_lookup = tk.BooleanVar(value=self.cfg.get("word_lookup", True))
        self.auto_hide = tk.BooleanVar(value=self.cfg.get("auto_hide_empty", True))
        chk = ttk.Frame(f)
        chk.grid(row=8, column=1, sticky="w", pady=4)
        for var, text in ((self.show_original, "Hiện cả chữ gốc phía trên bản dịch"),
                          (self.word_lookup, "Rê chuột vào chữ gốc để tra từ, giữ Shift kéo để tra cụm"),
                          (self.auto_hide, "Tự ẩn khung khi vùng dịch không còn chữ")):
            ttk.Checkbutton(chk, text=text, variable=var).pack(anchor="w", pady=1)

        ttk.Label(f, text="Xem trước").grid(row=9, column=0, sticky="nw", pady=(6, 0))
        self.preview = tk.Label(f, text="Tiến sĩ, nhiệm vụ đã sẵn sàng.", anchor="w",
                                justify="left", padx=10, pady=6)
        self.preview.grid(row=9, column=1, sticky="we", pady=(6, 0))
        for var in (self.fg, self.bg, self.font_family, self.font_size):
            var.trace_add("write", lambda *a: self._update_preview())
        self._update_preview()

        self.ui_theme = _Choice(f, UI_THEMES, self.cfg.get("ui_theme", "light"), width=20)
        self._row(f, 10, "Cửa sổ cài đặt", self.ui_theme.widget,
                  "Giao diện sáng hoặc tối. Bấm Lưu rồi mở lại cửa sổ cài đặt để thấy thay đổi.")

    def _set_colors(self, fg, bg):
        self.fg.set(fg)
        self.bg.set(bg)
        self._fg_btn.configure(bg=fg, activebackground=fg)
        self._bg_btn.configure(bg=bg, activebackground=bg)

    def _update_preview(self):
        try:
            self.preview.configure(fg=self.fg.get(), bg=self.bg.get(),
                                   font=(self.font_family.get(), int(self.font_size.get())))
        except (tk.TclError, ValueError):
            pass

    def _tab_games(self, f):
        self.remember_games = tk.BooleanVar(value=self.cfg.get("remember_games", True))
        self.auto_start_games = tk.BooleanVar(value=self.cfg.get("auto_start_games", True))
        ttk.Checkbutton(f, text="Nhớ vùng dịch theo từng app", variable=self.remember_games
                        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Label(f, text="Khi chọn vùng trên cửa sổ một app, vùng đó được nhớ theo app. Kéo cửa sổ "
                          "app đi đâu, vùng dịch đi theo; thu nhỏ hoặc tắt app thì tự dừng.",
                  foreground=theme.palette()["hint"], wraplength=440).grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(f, text="Tự bật dịch khi mở app đã lưu vùng", variable=self.auto_start_games
                        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 4))

        self.scale_window = tk.BooleanVar(value=self.cfg.get("scale_with_window", True))
        sf = ttk.Frame(f)
        sf.grid(row=8, column=0, columnspan=2, sticky="we", pady=(8, 0))
        ttk.Checkbutton(sf, text="Vùng dịch co giãn theo kích thước cửa sổ app",
                        variable=self.scale_window).pack(anchor="w")
        ttk.Label(sf, text="Đổi kích thước cửa sổ hoặc độ phân giải thì vùng dịch phóng to thu nhỏ "
                           "theo. Di chuyển cửa sổ không ảnh hưởng, vùng dịch luôn đi theo.",
                  foreground=theme.palette()["hint"], wraplength=440).pack(anchor="w")
        self.pause_unfocused = tk.BooleanVar(value=self.cfg.get("pause_when_unfocused", True))
        ttk.Checkbutton(f, text="Chỉ dịch khi app đang ở phía trước", variable=self.pause_unfocused
                        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Label(f, text="Chuyển sang cửa sổ khác thì tạm dừng và ẩn khung dịch, tránh dịch nhầm chữ "
                          "của cửa sổ khác. Quay lại app thì dịch tiếp.",
                  foreground=theme.palette()["hint"], wraplength=440).grid(row=4, column=0, columnspan=2, sticky="w")

        ttk.Label(f, text="App đã lưu vùng:").grid(row=10, column=0, columnspan=2, sticky="w", pady=(12, 2))
        self.profiles = copy.deepcopy(self.cfg.get("profiles", {}))
        self._deleted_profiles = set()
        self.profile_list = tk.Listbox(f, height=6, activestyle="none", font=("Segoe UI", 10),
                                       **{k: v for k, v in theme.field_options().items() if k != "insertbackground"})
        self.profile_list.grid(row=11, column=0, columnspan=2, sticky="we")
        self._fill_profiles()
        ttk.Button(f, text="Xóa app đã chọn", command=self._delete_profile
                   ).grid(row=12, column=0, sticky="w", pady=6)

    def _fill_profiles(self):
        self.profile_list.delete(0, "end")
        self._profile_keys = list(self.profiles)
        for exe in self._profile_keys:
            title = self.profiles[exe].get("title") or ""
            self.profile_list.insert("end", f"{exe}   —   {title}" if title else exe)
        if not self._profile_keys:
            self.profile_list.insert("end", "Chưa có. Bấm phím chọn vùng trên cửa sổ một app để lưu.")

    def _delete_profile(self):
        sel = self.profile_list.curselection()
        if sel and self._profile_keys:
            exe = self._profile_keys[sel[0]]
            self.profiles.pop(exe, None)
            self._deleted_profiles.add(exe)
            self._fill_profiles()

    def _num(self, f, row, label, key, default, lo, hi, step, hint, fmt=None, scale=1.0):
        """Mot dong cai dat so: luu bien vao self._nums de doc lai khi luu."""
        is_int = isinstance(default, int) and scale == 1.0
        val = self.cfg.get(key, default) * scale
        var = tk.IntVar(value=int(round(val))) if is_int else tk.DoubleVar(value=round(val, 4))
        spin = ttk.Spinbox(f, from_=lo, to=hi, increment=step, textvariable=var, width=8,
                           **({"format": fmt} if fmt else {}))
        self._row(f, row, label, spin, hint)
        self._nums[key] = (var, scale, lo, hi, is_int)

    # --- loc anh truoc OCR + xem truoc ---
    def _tab_filter(self, f):
        from . import imgfilter
        fc = {**imgfilter.DEFAULT, **self.cfg.get("ocr_filter", {})}
        self.f_color_on = tk.BooleanVar(value=fc["text_color_on"])
        self.f_color = tk.StringVar(value=fc["text_color"])
        self.f_tol = tk.IntVar(value=int(fc["color_tolerance"]))
        self.f_contrast = tk.BooleanVar(value=fc["autocontrast"])
        self.f_invert = tk.BooleanVar(value=fc["invert"])
        self.f_sharpen = tk.BooleanVar(value=fc["sharpen"])
        self.f_threshold = tk.IntVar(value=int(fc["threshold"]))

        row = ttk.Frame(f)
        ttk.Checkbutton(row, text="Chỉ giữ chữ có màu", variable=self.f_color_on).pack(side="left")
        self._f_color_btn = self._color_button(row, self.f_color)
        self._f_color_btn.configure(width=6)
        self._f_color_btn.pack(side="left", padx=8)
        self._row(f, 0, "Lọc theo màu chữ", row,
                  "Bỏ hết nền, chỉ giữ chữ đúng màu này. Bấm vào ảnh gốc bên dưới để lấy màu chữ.")
        self._row(f, 2, "Độ lệch màu", ttk.Spinbox(f, from_=1, to=100, textvariable=self.f_tol, width=8),
                  "Phần trăm lệch so với màu chữ vẫn được giữ. Tăng nếu chữ bị mất nét.")
        opts = ttk.Frame(f)
        for var, text in ((self.f_contrast, "Tăng tương phản"), (self.f_invert, "Đảo màu"),
                          (self.f_sharpen, "Làm nét")):
            ttk.Checkbutton(opts, text=text, variable=var).pack(side="left", padx=(0, 14))
        self._row(f, 4, "Xử lý thêm", opts)
        self._row(f, 5, "Chuyển đen trắng",
                  ttk.Spinbox(f, from_=0, to=100, textvariable=self.f_threshold, width=8),
                  "Ngưỡng sáng tính theo %, điểm sáng hơn thành trắng, tối hơn thành đen. 0 là tắt.")

        bar = ttk.Frame(f)
        bar.grid(row=7, column=0, columnspan=2, sticky="we", pady=(10, 4))
        ttk.Button(bar, text="Chụp vùng dịch để xem trước", command=self._preview_capture).pack(side="left")
        self.f_status = ttk.Label(bar, text="", foreground=theme.palette()["hint"])
        self.f_status.pack(side="left", padx=10)
        prev = ttk.Frame(f)
        prev.grid(row=8, column=0, columnspan=2, sticky="we")
        ttk.Label(prev, text="Ảnh gốc").grid(row=0, column=0, sticky="w")
        self.f_orig = tk.Label(prev, bg=theme.palette()["field"], cursor="crosshair")
        self.f_orig.grid(row=1, column=0, sticky="w", pady=(2, 8))
        self.f_orig.bind("<Button-1>", self._preview_pick_color)
        ttk.Label(prev, text="Sau khi lọc").grid(row=2, column=0, sticky="w")
        self.f_out = tk.Label(prev, bg=theme.palette()["field"])
        self.f_out.grid(row=3, column=0, sticky="w", pady=(2, 8))
        self.f_text = ttk.Label(prev, text="", wraplength=600, justify="left")
        self.f_text.grid(row=4, column=0, sticky="w")
        self._prev_img = None
        self._prev_job = None
        for var in (self.f_color_on, self.f_color, self.f_tol, self.f_contrast, self.f_invert,
                    self.f_sharpen, self.f_threshold):
            var.trace_add("write", lambda *a: self._preview_schedule())

    def _filter_values(self) -> dict:
        def num(var, lo, hi):
            try:
                return max(lo, min(hi, int(var.get())))
            except (tk.TclError, ValueError):
                return lo
        return {"text_color_on": bool(self.f_color_on.get()), "text_color": self.f_color.get(),
                "color_tolerance": num(self.f_tol, 1, 100), "autocontrast": bool(self.f_contrast.get()),
                "invert": bool(self.f_invert.get()), "sharpen": bool(self.f_sharpen.get()),
                "threshold": num(self.f_threshold, 0, 100)}

    def _preview_capture(self):
        if "capture" not in self.hooks:
            return
        self.win.withdraw()               # an cua so cai dat de khong chup de len vung dich

        def grab():
            img = self.hooks["capture"]()
            self.win.deiconify()
            self.win.lift()
            if img is None:
                self.f_status.configure(text="Chưa có vùng dịch. Bấm phím chọn vùng trước.")
                return
            self._prev_img = img
            self._preview_refresh()
        self.win.after(250, grab)

    def _preview_schedule(self):
        if self._prev_img is None:
            return
        if self._prev_job:
            self.win.after_cancel(self._prev_job)
        self._prev_job = self.win.after(400, self._preview_refresh)

    @staticmethod
    def _fit(img, max_w=600, max_h=90):
        k = min(max_w / img.width, max_h / img.height, 1.0)
        return img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))))

    def _preview_refresh(self):
        from PIL import Image, ImageTk
        from . import imgfilter
        self._prev_job = None
        src = self._prev_img
        if src is None or not self.win.winfo_exists():
            return
        try:
            scale = float(self.upscale.get())
        except (tk.TclError, ValueError, AttributeError):
            scale = 1.0
        big = src.resize((int(src.width * scale), int(src.height * scale)), Image.LANCZOS) \
            if scale > 1 else src
        out = imgfilter.apply(big, self._filter_values())
        shown = self._fit(src)
        self._prev_scale = src.width / shown.width
        self._tk_orig = ImageTk.PhotoImage(shown)
        self._tk_out = ImageTk.PhotoImage(self._fit(out.convert("RGB")))
        self.f_orig.configure(image=self._tk_orig)
        self.f_out.configure(image=self._tk_out)
        self.f_text.configure(text="Đang đọc chữ…")
        if "ocr" in self.hooks:
            cfg = dict(self.cfg)
            cfg.update(source_lang=self.src.get(), ocr_engine=self.engine.get(),
                       tesseract_cmd=self.tess.get().strip())
            self.hooks["ocr"](out, cfg, self._preview_text)

    def _preview_text(self, text):
        if self.win.winfo_exists():
            self.f_text.configure(text="Chữ đọc được: " + (text.replace("\n", " / ") or "(không đọc được chữ nào)"))

    def _preview_pick_color(self, e):
        if self._prev_img is None:
            return
        x = min(self._prev_img.width - 1, int(e.x * self._prev_scale))
        y = min(self._prev_img.height - 1, int(e.y * self._prev_scale))
        r, g, b = self._prev_img.convert("RGB").getpixel((x, y))[:3]
        c = f"#{r:02X}{g:02X}{b:02X}"
        self.f_color.set(c)
        self._f_color_btn.configure(bg=c, activebackground=c)
        self.f_color_on.set(True)
        self.f_status.configure(text=f"Đã lấy màu chữ {c}")

    # --- bang thay the loi OCR ---
    def _tab_subs(self, f):
        self.subs = [dict(x) for x in self.cfg.get("ocr_substitutions", [])]
        ttk.Label(f, text="Tự sửa những chữ OCR hay đọc nhầm trước khi dịch, ví dụ “rn” thành “m”, "
                          "“0” thành “O”. Áp dụng từ trên xuống dưới.",
                  foreground=theme.palette()["hint"], wraplength=640).grid(row=0, column=0, columnspan=2,
                                                                           sticky="w", pady=(0, 8))
        cols = ("from", "to", "word")
        self.subs_tree = ttk.Treeview(f, columns=cols, show="headings", height=8, selectmode="browse")
        for c, text, width in (("from", "Chữ OCR đọc nhầm", 230), ("to", "Sửa thành", 230), ("word", "Cả từ", 80)):
            self.subs_tree.heading(c, text=text)
            self.subs_tree.column(c, width=width, anchor="w" if c != "word" else "center",
                                  stretch=c != "word")
        self.subs_tree.grid(row=1, column=0, columnspan=2, sticky="we")
        self.subs_tree.bind("<<TreeviewSelect>>", lambda e: self._subs_pick())
        form = ttk.Frame(f)
        form.grid(row=2, column=0, columnspan=2, sticky="we", pady=(8, 0))
        self.sub_from, self.sub_to = tk.StringVar(), tk.StringVar()
        self.sub_word = tk.BooleanVar(value=True)
        ttk.Entry(form, textvariable=self.sub_from, width=22).pack(side="left")
        ttk.Label(form, text="→").pack(side="left", padx=6)
        ttk.Entry(form, textvariable=self.sub_to, width=22).pack(side="left")
        ttk.Checkbutton(form, text="Cả từ", variable=self.sub_word).pack(side="left", padx=8)
        btns = ttk.Frame(f)
        btns.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))
        for text, cmd in (("Thêm", self._subs_add), ("Sửa dòng đang chọn", self._subs_update),
                          ("Xóa", self._subs_delete), ("Lên", lambda: self._subs_move(-1)),
                          ("Xuống", lambda: self._subs_move(1))):
            ttk.Button(btns, text=text, command=cmd).pack(side="left", padx=(0, 4))
        ttk.Label(f, text="“Cả từ”: chỉ sửa khi đứng riêng thành một từ, để “Dr” → “Doctor” không làm "
                          "hỏng chữ “Drone”.", foreground=theme.palette()["hint"],
                  wraplength=640).grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))
        test = ttk.Frame(f)
        test.grid(row=5, column=0, columnspan=2, sticky="we", pady=(12, 0))
        ttk.Label(test, text="Thử:").pack(side="left")
        self.sub_test = tk.StringVar()
        ttk.Entry(test, textvariable=self.sub_test, width=36).pack(side="left", padx=6)
        self.sub_test_out = ttk.Label(test, text="", foreground=theme.palette()["hint"])
        self.sub_test_out.pack(side="left")
        self.sub_test.trace_add("write", lambda *a: self._subs_test())
        self._subs_refresh()

    def _subs_refresh(self, select=None):
        self.subs_tree.delete(*self.subs_tree.get_children())
        for i, sub in enumerate(self.subs):
            self.subs_tree.insert("", "end", iid=str(i), values=(sub.get("from", ""), sub.get("to", ""),
                                                                 "✓" if sub.get("word") else ""))
        if select is not None and 0 <= select < len(self.subs):
            self.subs_tree.selection_set(str(select))
        self._subs_test()

    def _subs_sel(self):
        sel = self.subs_tree.selection()
        return int(sel[0]) if sel else None

    def _subs_pick(self):
        i = self._subs_sel()
        if i is not None:
            sub = self.subs[i]
            self.sub_from.set(sub.get("from", ""))
            self.sub_to.set(sub.get("to", ""))
            self.sub_word.set(bool(sub.get("word")))

    def _subs_value(self):
        frm = self.sub_from.get()
        return {"from": frm, "to": self.sub_to.get(), "word": bool(self.sub_word.get())} if frm else None

    def _subs_add(self):
        v = self._subs_value()
        if v:
            self.subs.append(v)
            self._subs_refresh(len(self.subs) - 1)

    def _subs_update(self):
        i, v = self._subs_sel(), self._subs_value()
        if i is not None and v:
            self.subs[i] = v
            self._subs_refresh(i)

    def _subs_delete(self):
        i = self._subs_sel()
        if i is not None:
            del self.subs[i]
            self._subs_refresh(min(i, len(self.subs) - 1))

    def _subs_move(self, step):
        i = self._subs_sel()
        if i is not None and 0 <= i + step < len(self.subs):
            self.subs[i], self.subs[i + step] = self.subs[i + step], self.subs[i]
            self._subs_refresh(i + step)

    def _subs_test(self):
        from .textproc import apply_substitutions
        text = self.sub_test.get() if hasattr(self, "sub_test") else ""
        self.sub_test_out.configure(text=("→ " + apply_substitutions(text, self.subs)) if text else "")

    # --- he thong ---
    def _tab_system(self, f):
        from . import __version__, sysutil
        self.autostart = tk.BooleanVar(value=sysutil.is_autostart())
        ttk.Checkbutton(f, text="Khởi động cùng Windows", variable=self.autostart
                        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 2))
        ttk.Label(f, text="App tự chạy ẩn ở khay hệ thống mỗi khi bật máy.",
                  foreground=theme.palette()["hint"]).grid(row=1, column=0, columnspan=2, sticky="w")
        self.proxy = tk.StringVar(value=self.cfg.get("proxy", ""))
        self._row(f, 2, "Proxy", ttk.Entry(f, textvariable=self.proxy),
                  "Dùng khi mạng chặn Google hoặc phải đi qua proxy công ty, ví dụ http://127.0.0.1:8080. "
                  "Để trống là không dùng.")
        self.check_updates = tk.BooleanVar(value=self.cfg.get("check_updates", True))
        ttk.Checkbutton(f, text="Tự kiểm tra bản mới khi mở app", variable=self.check_updates
                        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 2))
        upd = ttk.Frame(f)
        upd.grid(row=5, column=0, columnspan=2, sticky="w")
        ttk.Label(upd, text=f"Phiên bản hiện tại: {__version__}").pack(side="left")
        ttk.Button(upd, text="Kiểm tra ngay", command=self._check_update_now).pack(side="left", padx=10)
        self.update_result = ttk.Label(upd, text="", foreground=theme.palette()["hint"])
        self.update_result.pack(side="left")
        ttk.Label(f, text="config.json và app.log nằm cùng thư mục với app, chép cả thư mục sang máy "
                          "khác là dùng được ngay.", foreground=theme.palette()["hint"],
                  wraplength=640).grid(row=6, column=0, columnspan=2, sticky="w", pady=(14, 0))

    def _check_update_now(self):
        from . import sysutil
        self.update_result.configure(text="Đang kiểm tra…")

        def done(result, err):
            if err:
                self.update_result.configure(text=f"Không kiểm tra được: {err}"[:120])
                return
            newer, tag, url = result
            if newer:
                self.update_result.configure(text=f"Có bản mới {tag}")
                if messagebox.askyesno("Cập nhật", f"Có bản mới {tag}. Mở trang tải về?", parent=self.win):
                    webbrowser.open(url)
            else:
                self.update_result.configure(text="Đang dùng bản mới nhất." if tag else
                                             "Chưa có bản phát hành nào trên GitHub.")
        self._run_bg(sysutil.check_update, done)

    # --- to do cac muc cai dat sai ---
    def _mark_problems(self, problems):
        bad = {tab for tab, _ in problems}
        for tab_id in self.nb.tabs():
            name = self.nb.tab(tab_id, "text").removeprefix("⚠ ")
            self.nb.tab(tab_id, text=("⚠ " + name) if name in bad else name)
        if problems:
            lines = [f"• {tab}: {msg}" for tab, msg in problems[:3]]
            if len(problems) > 3:
                lines.append(f"• … và {len(problems) - 3} chỗ khác, xem các tab có dấu ⚠")
            self.banner.configure(text="Có chỗ cài đặt chưa đúng:\n" + "\n".join(lines))
            self.banner.pack(fill="x", padx=18, pady=(8, 0), after=self.banner.master.winfo_children()[0])
        else:
            self.banner.pack_forget()

    def _tab_advanced(self, f):
        self._nums = {}
        self._num(f, 0, "Ngưỡng thay đổi", "change_pixels", 0.0001, 0, 5, 0.01,
                  "Phần trăm điểm ảnh trong vùng phải đổi thì mới đọc lại chữ. Để thấp cho chắc "
                  "không sót câu; chỉ tăng nếu nền động làm máy chạy nặng.", fmt="%.3f", scale=100)
        self._num(f, 2, "Mức đổi một điểm ảnh", "pixel_delta_pct", 11, 1, 60, 1,
                  "Một điểm ảnh sáng hoặc tối đi bao nhiêu phần trăm thì mới tính là đổi. Tăng nếu "
                  "nhiễu hình làm app đọc lại liên tục.")
        self._num(f, 4, "Số lần đọc giống nhau", "confirm_reads", 2, 1, 5, 1,
                  "Đọc ra cùng một chữ bấy nhiêu lần liên tiếp mới dịch, tránh dịch chữ đang hiện "
                  "dần. 1 là dịch ngay.")
        self._num(f, 6, "Số lần đọc khác nhau", "unstable_max", 5, 0, 20, 1,
                  "Chữ đổi liên tục bấy nhiêu lần thì dịch luôn bản mới nhất. 0 là tắt.")
        self._num(f, 8, "Nghỉ khi bị chặn", "block_pause", 30, 5, 600, 5,
                  "Số giây tạm nghỉ khi máy dịch báo gửi quá nhiều, lần sau gấp đôi.")
        self._num(f, 10, "Số câu trong lịch sử", "history_max", 200, 10, 2000, 10,
                  "Số câu giữ lại trong khung dịch để lăn chuột xem lại.")
        self._num(f, 12, "Ẩn khi không thấy chữ", "hide_after_empty", 2, 1, 20, 1,
                  "Đọc bấy nhiêu lần liên tiếp không thấy chữ thì tự ẩn khung, nếu bật tự ẩn.")

        self.debug_log = tk.BooleanVar(value=self.cfg.get("debug_log", False))
        ttk.Checkbutton(f, text="Ghi log chi tiết để tìm lỗi", variable=self.debug_log
                        ).grid(row=14, column=1, sticky="w", pady=(10, 0))
        ttk.Label(f, text="Ghi từng lần đọc chữ và dịch vào app.log. Chỉ bật khi cần tìm lỗi.",
                  foreground=theme.palette()["hint"], wraplength=440).grid(row=15, column=1, sticky="w")
        ttk.Button(f, text="Đặt lại mục này về mặc định", command=self._reset_advanced
                   ).grid(row=16, column=1, sticky="w", pady=(12, 0))

    def _reset_advanced(self):
        for key, (var, scale, _lo, _hi, is_int) in self._nums.items():
            v = DEFAULTS[key] * scale
            var.set(int(round(v)) if is_int else round(v, 4))
        self.debug_log.set(DEFAULTS["debug_log"])

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
                  foreground=theme.palette()["hint"]).grid(row=len(HOTKEY_NAMES), column=1, sticky="w", pady=(8, 0))

    # --- hanh dong ---
    def _color_button(self, parent, var):
        btn = tk.Button(parent, width=10, relief="flat", bd=0, highlightthickness=1,
                        highlightbackground=theme.palette()["border"], bg=var.get(), activebackground=var.get(),
                        cursor="hand2")

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
        for key, (var, scale, lo, hi, is_int) in self._nums.items():
            v = min(hi, max(lo, float(var.get()))) / scale
            c[key] = int(round(v)) if is_int else v
        c["debug_log"] = bool(self.debug_log.get())
        c["ocr_filter"] = self._filter_values()
        c["ocr_substitutions"] = [dict(x) for x in self.subs]
        c["proxy"] = self.proxy.get().strip()
        c["check_updates"] = bool(self.check_updates.get())
        c["autostart"] = bool(self.autostart.get())
        c["upscale"] = float(self.upscale.get())
        c["translator_chain"] = list(self.chain) or ["google"]
        c["translator"] = c["translator_chain"][0]
        c["deepl_api_key"] = self.deepl_key.get().strip()
        c["google_cloud_api_key"] = self.gcloud_key.get().strip()
        self._save_ai_fields()
        c["ai"] = copy.deepcopy(self.ai_store)
        c["clean_ocr"] = bool(self.clean_ocr.get())
        c["split_speaker"] = bool(self.split_speaker.get())
        c["google_context_lines"] = max(0, min(5, int(self.google_ctx.get())))
        c["min_send_gap"] = max(0.2, min(10.0, round(float(self.send_gap.get()), 1)))
        c["ai_notes"] = self.ai_notes.get("1.0", "end").strip()
        c["ai_context_lines"] = int(self.ai_context.get())
        o = c["overlay"]
        o["position"] = self.position.get()
        o["font_family"] = self.font_family.get()
        o["font_size"] = int(self.font_size.get())
        o["fg"], o["bg"] = self.fg.get(), self.bg.get()
        o["opacity"] = max(0.2, min(1.0, 1 - round(float(self.transparency.get())) / 100))
        o["show_original"] = bool(self.show_original.get())
        c["word_lookup"] = bool(self.word_lookup.get())
        o["mode"] = self.ov_mode.get()
        o["subtitle_font_size"] = max(12, min(72, int(self.sub_size.get())))
        c["auto_hide_empty"] = bool(self.auto_hide.get())
        c["hotkeys"] = {k: v.get() for k, v in self.hk_vars.items()}
        c["ui_theme"] = self.ui_theme.get()
        c["remember_games"] = bool(self.remember_games.get())
        c["auto_start_games"] = bool(self.auto_start_games.get())
        c["pause_when_unfocused"] = bool(self.pause_unfocused.get())
        c["scale_with_window"] = bool(self.scale_window.get())
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
        from .validate import validate
        problems = validate(cfg, deep=False)
        if problems:
            text = "\n".join(f"• {tab}: {msg}" for tab, msg in problems)
            if not messagebox.askyesno("Cài đặt", f"Có chỗ cài đặt chưa đúng:\n\n{text}\n\nVẫn lưu?",
                                       parent=self.win):
                self._mark_problems(problems)
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
