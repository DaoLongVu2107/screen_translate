"""Tien ich he thong: khoi dong cung Windows, proxy, kiem tra ban moi."""
import logging
import os
import re
import sys

from . import __version__

log = logging.getLogger(__name__)
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "ScreenTranslator"
REPO = "DaoLongVu2107/screen_translate"


def _command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    exe = sys.executable
    pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    main = os.path.join(os.path.dirname(os.path.abspath(__file__)), "__main__.py")
    return f'"{pyw if os.path.isfile(pyw) else exe}" "{main}"'


def is_autostart() -> bool:
    if sys.platform != "win32":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, APP_NAME)
            return True
    except OSError:
        return False


def set_autostart(enabled: bool) -> bool:
    """Bat / tat khoi dong cung Windows (khoa Run cua nguoi dung hien tai)."""
    if sys.platform != "win32":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if enabled:
                winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, _command())
            else:
                try:
                    winreg.DeleteValue(k, APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        log.exception("Khong doi duoc khoi dong cung Windows")
        return False


_PROXY_VARS = ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy")
_saved_env = None                # gia tri proxy cua he thong truoc khi app dat de


def apply_proxy(url: str):
    """Dat proxy cho moi ket noi mang cua app (Google, DeepL, AI...). Bo trong thi tra lai
    dung proxy cua he thong nhu truoc."""
    global _saved_env
    url = (url or "").strip()
    if url:
        if _saved_env is None:
            _saved_env = {v: os.environ.get(v) for v in _PROXY_VARS}
        for v in _PROXY_VARS:
            os.environ[v] = url
    elif _saved_env is not None:
        for v, old in _saved_env.items():
            if old is None:
                os.environ.pop(v, None)
            else:
                os.environ[v] = old
        _saved_env = None


def install_ocr_language(capability: str) -> bool:
    """Cai goi nhan dang chu cua Windows (hoi quyen quan tri). Chay xong moi tra ve.
    True neu lenh chay xong (khong chac da cai duoc, kiem tra lai sau)."""
    if sys.platform != "win32" or not re.fullmatch(r"Language\.OCR~~~[A-Za-z-]+~0\.0\.1\.0", capability):
        return False
    import subprocess
    inner = f"Add-WindowsCapability -Online -Name '{capability}'"
    cmd = ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command",
           f"Start-Process powershell -Verb RunAs -Wait -WindowStyle Normal "
           f"-ArgumentList '-NoProfile','-Command',\"{inner}\""]
    try:
        subprocess.run(cmd, check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return True
    except Exception:
        log.exception("Khong chay duoc lenh cai goi OCR")
        return False


def _ver(tag: str):
    """'v1.2.3' -> (1, 2, 3)."""
    nums = [int(n) for n in re.findall(r"\d+", tag or "")[:3]]
    return tuple(nums + [0] * (3 - len(nums)))


def check_update():
    """(co ban moi?, ten ban moi, link trang tai). Chua co release nao -> (False, None, link)."""
    import requests
    url = f"https://github.com/{REPO}/releases/latest"
    r = requests.get(f"https://api.github.com/repos/{REPO}/releases/latest", timeout=8,
                     headers={"Accept": "application/vnd.github+json"})
    if r.status_code == 404:
        return False, None, url
    r.raise_for_status()
    data = r.json()
    tag = data.get("tag_name") or ""
    return _ver(tag) > _ver(__version__), tag, data.get("html_url") or url
