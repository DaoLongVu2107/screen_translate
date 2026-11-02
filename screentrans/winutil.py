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


# --- Nhan dien cua so game (de nho vung theo tung game) ---
GA_ROOT = 2
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

if IS_WIN:
    from ctypes import wintypes

    _user32 = ctypes.windll.user32
    _kernel32 = ctypes.windll.kernel32
    _user32.WindowFromPoint.argtypes = [wintypes.POINT]
    _user32.WindowFromPoint.restype = wintypes.HWND
    _user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    _user32.GetAncestor.restype = wintypes.HWND
    _user32.GetForegroundWindow.restype = wintypes.HWND
    _user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    _user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
    _user32.IsWindow.argtypes = [wintypes.HWND]
    _user32.IsIconic.argtypes = [wintypes.HWND]
    _user32.IsWindowVisible.argtypes = [wintypes.HWND]
    _user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]


def window_at(x: int, y: int):
    """Cua so goc (top-level) tai diem man hinh (x, y)."""
    if not IS_WIN:
        return None
    hwnd = _user32.WindowFromPoint(wintypes.POINT(int(x), int(y)))
    return _user32.GetAncestor(hwnd, GA_ROOT) if hwnd else None


def foreground_window():
    if not IS_WIN:
        return None
    hwnd = _user32.GetForegroundWindow()
    return _user32.GetAncestor(hwnd, GA_ROOT) if hwnd else None


def window_pid(hwnd) -> int:
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def window_exe(hwnd):
    """Ten file exe cua cua so, vd 'Arknights.exe' (None neu khong lay duoc)."""
    if not IS_WIN or not hwnd:
        return None
    handle = _kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, window_pid(hwnd))
    if not handle:
        return None
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(len(buf))
        if not _kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return None
        return buf.value.replace("/", "\\").rsplit("\\", 1)[-1]
    finally:
        _kernel32.CloseHandle(handle)


def window_title(hwnd) -> str:
    if not IS_WIN or not hwnd:
        return ""
    buf = ctypes.create_unicode_buffer(256)
    _user32.GetWindowTextW(hwnd, buf, len(buf))
    return buf.value


def client_origin(hwnd):
    """Goc tren-trai vung noi dung cua cua so tren man hinh, hoac None neu cua so da dong."""
    if not IS_WIN or not hwnd or not _user32.IsWindow(hwnd):
        return None
    pt = wintypes.POINT(0, 0)
    if not _user32.ClientToScreen(hwnd, ctypes.byref(pt)):
        return None
    return pt.x, pt.y


def window_alive(hwnd) -> bool:
    return bool(IS_WIN and hwnd and _user32.IsWindow(hwnd))


def window_minimized(hwnd) -> bool:
    return bool(IS_WIN and hwnd and (_user32.IsIconic(hwnd) or not _user32.IsWindowVisible(hwnd)))


# --- Giao dien kieu Windows 11 ---
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2


def _dwm_set(tk_window, attr: int, value: int):
    if not IS_WIN:
        return
    try:
        v = ctypes.c_int(value)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(_hwnd(tk_window), attr, ctypes.byref(v),
                                                   ctypes.sizeof(v))
    except Exception:
        pass


def dark_title_bar(tk_window):
    """Thanh tieu de mau toi (Windows 10 20H1+ / 11)."""
    _dwm_set(tk_window, DWMWA_USE_IMMERSIVE_DARK_MODE, 1)


def round_corners(tk_window):
    """Bo goc cua so nhu Windows 11 (Windows 10 bo qua)."""
    _dwm_set(tk_window, DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUND)


def client_size(hwnd):
    """Kich thuoc vung noi dung cua cua so (rong, cao), hoac None."""
    if not IS_WIN or not hwnd or not _user32.IsWindow(hwnd):
        return None
    rc = wintypes.RECT()
    if not _user32.GetClientRect(hwnd, ctypes.byref(rc)):
        return None
    return rc.right - rc.left, rc.bottom - rc.top
