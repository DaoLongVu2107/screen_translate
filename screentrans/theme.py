"""Giao dien cua so cai dat: Sang / Toi. Dung theme Sun Valley (Fluent kieu Windows 11)
neu co, roi tu dat lai mau cho tung loai thanh phan de ca cua so luon dong bo."""
import logging
from tkinter import ttk

log = logging.getLogger(__name__)

PALETTES = {
    # Trung mau goc cua Sun Valley de khong bi lech mang nen
    "light": dict(bg="#fafafa", fg="#1c1c1c", card="#fafafa", field="#ffffff", border="#d0d0d0",
                  hint="#6e6e6e", accent="#005fb8"),
    "dark": dict(bg="#1c1c1c", fg="#fafafa", card="#1c1c1c", field="#2b2b2b", border="#3f3f3f",
                 hint="#9a9a9a", accent="#4c9aff"),
}

current = "light"


def palette() -> dict:
    return PALETTES[current]


def apply(root, mode: str):
    """Ap giao diện cho toan app. mode: 'light' hoac 'dark'."""
    global current
    current = mode if mode in PALETTES else "light"
    p = PALETTES[current]
    try:
        import sv_ttk
        sv_ttk.set_theme(current, root)
    except Exception as e:
        log.info("Khong dung duoc sv_ttk (%s), dung theme co san", e)
        try:
            ttk.Style(root).theme_use("clam")
        except Exception:
            pass
    st = ttk.Style(root)
    # Dat lai mau co ban cho moi thanh phan: tranh tinh trang nua sang nua toi
    st.configure(".", background=p["bg"], foreground=p["fg"])
    for name in ("TFrame", "TLabel", "TCheckbutton", "TRadiobutton", "TLabelframe",
                 "TLabelframe.Label", "TSeparator"):
        st.configure(name, background=p["bg"], foreground=p["fg"])
    st.configure("Card.TFrame", background=p["card"])
    st.configure("Hint.TLabel", background=p["bg"], foreground=p["hint"])
    st.configure("Title.TLabel", background=p["bg"], foreground=p["fg"], font=("Segoe UI Semibold", 18))
    st.configure("TNotebook", background=p["bg"])
    st.map("TCheckbutton", background=[("active", p["bg"])])
    root.option_add("*TCombobox*Listbox.background", p["field"])
    root.option_add("*TCombobox*Listbox.foreground", p["fg"])
    root.option_add("*TCombobox*Listbox.selectBackground", p["accent"])
    root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")


def field_options() -> dict:
    """Mau cho Text / Listbox (khong phai widget ttk)."""
    p = palette()
    return dict(bg=p["field"], fg=p["fg"], relief="flat", highlightthickness=1,
                highlightbackground=p["border"], highlightcolor=p["accent"],
                selectbackground=p["accent"], selectforeground="#ffffff", insertbackground=p["fg"])
