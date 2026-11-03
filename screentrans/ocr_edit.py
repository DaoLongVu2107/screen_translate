"""Sua chu OCR doc nham roi dich lai; tuy chon luu cac cho sua vao bang thay the loi OCR."""
import difflib
import re
import tkinter as tk
from tkinter import ttk

from . import theme
from .winutil import dark_title_bar


def word_fixes(old: str, new: str):
    """Cac cap (tu cu -> tu moi) nguoi dung da sua, chi lay cho thay 1 tu bang 1 tu."""
    a, b = re.findall(r"\S+", old), re.findall(r"\S+", new)
    strip = lambda w: w.strip(".,!?;:\"'()[]…")   # noqa: E731
    fixes = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if op == "replace" and i2 - i1 == j2 - j1:
            for x, y in zip(a[i1:i2], b[j1:j2]):
                x, y = strip(x), strip(y)
                if x and y and x != y:
                    fixes.append((x, y))
    return fixes


class OcrEditDialog:
    def __init__(self, root, text: str, on_submit):
        self.on_submit = on_submit          # on_submit(chu_moi, luu_vao_bang_thay_the)
        self.original = text
        p = theme.palette()
        self.win = w = tk.Toplevel(root)
        w.title("Sửa chữ gốc rồi dịch lại")
        w.attributes("-topmost", True)
        w.configure(bg=p["bg"])
        if theme.current == "dark":
            w.after(30, lambda: dark_title_bar(w))
        body = ttk.Frame(w, padding=16)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Sửa những chỗ OCR đọc nhầm rồi bấm Dịch lại:").pack(anchor="w")
        self.text = tk.Text(body, width=64, height=5, wrap="word", font=("Segoe UI", 11),
                            padx=8, pady=6, **theme.field_options())
        self.text.pack(fill="both", expand=True, pady=(6, 8))
        self.text.insert("1.0", text)
        self.save_subs = tk.BooleanVar(value=True)
        ttk.Checkbutton(body, text="Lưu các chỗ sửa vào bảng thay thế OCR để lần sau tự sửa",
                        variable=self.save_subs).pack(anchor="w")
        bar = ttk.Frame(body)
        bar.pack(fill="x", pady=(12, 0))
        ttk.Button(bar, text="Hủy", command=w.destroy).pack(side="right")
        ttk.Button(bar, text="Dịch lại", style="Accent.TButton", command=self.submit).pack(side="right", padx=8)
        w.bind("<Control-Return>", lambda e: self.submit())
        w.bind("<Escape>", lambda e: w.destroy())
        self.text.focus_set()
        self.text.tag_add("sel", "1.0", "end-1c")

    def submit(self):
        new = " ".join(self.text.get("1.0", "end").split())
        if new:
            self.on_submit(new, word_fixes(self.original, new) if self.save_subs.get() else [])
        self.win.destroy()
