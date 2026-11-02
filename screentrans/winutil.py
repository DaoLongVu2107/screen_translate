"""Ham Win32 qua ctypes (khong lam gi neu khong phai Windows)."""
import ctypes
import sys

IS_WIN = sys.platform == "win32"
WDA_EXCLUDEFROMCAPTURE = 0x11


def enable_dpi_awareness():
    """De toa do tkinter khop voi pixel that khi Windows scale 125%/150%."""
    if not IS_WIN:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def virtual_screen():
    """(x, y, w, h) bao toan bo cac man hinh."""
    if IS_WIN:
        m = ctypes.windll.user32.GetSystemMetrics
        return m(76), m(77), m(78), m(79)
    import mss
    with mss.mss() as s:
        mon = s.monitors[0]
        return mon["left"], mon["top"], mon["width"], mon["height"]


def _hwnd(tk_window) -> int:
    tk_window.update_idletasks()
    return ctypes.windll.user32.GetParent(tk_window.winfo_id()) or tk_window.winfo_id()


def exclude_from_capture(tk_window):
    """An cua so khoi anh chup man hinh (Win10 2004+) -> khung dich khong bi OCR lai."""
    if not IS_WIN:
        return
    try:
        ctypes.windll.user32.SetWindowDisplayAffinity(_hwnd(tk_window), WDA_EXCLUDEFROMCAPTURE)
    except Exception:
        pass
