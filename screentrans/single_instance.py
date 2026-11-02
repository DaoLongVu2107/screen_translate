"""Chi chay mot ban app. Ban mo sau bao cho ban dang chay (bat cua so cai dat) roi thoat."""
import logging
import os
import socket
import sys
import tempfile
import threading

log = logging.getLogger(__name__)

NAME = "ScreenTranslator_SingleInstance"
PORT_FILE = os.path.join(tempfile.gettempdir(), "screentrans_instance.port")
ERROR_ALREADY_EXISTS = 183


class SingleInstance:
    def __init__(self):
        self._handle = None
        self._lock_file = None
        self._server = None

    def acquire(self) -> bool:
        """True neu day la ban dau tien."""
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CreateMutexW.restype = ctypes.c_void_p
            self._handle = kernel32.CreateMutexW(None, False, "Local\\" + NAME)
            return ctypes.get_last_error() != ERROR_ALREADY_EXISTS
        try:
            import fcntl
            self._lock_file = open(os.path.join(tempfile.gettempdir(), NAME + ".lock"), "w")
            fcntl.flock(self._lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            return False

    def listen(self, on_command):
        """Nghe lenh tu cac ban mo sau (chi tren may nay, 127.0.0.1)."""
        try:
            self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server.bind(("127.0.0.1", 0))
            self._server.listen(2)
            with open(PORT_FILE, "w") as f:
                f.write(str(self._server.getsockname()[1]))
        except OSError:
            log.exception("Khong mo duoc cong nhan lenh")
            return

        def loop():
            while True:
                try:
                    conn, _ = self._server.accept()
                except OSError:
                    return
                with conn:
                    conn.settimeout(2)
                    try:
                        cmd = conn.recv(64).decode("ascii", "ignore").strip()
                    except OSError:
                        continue
                    if cmd:
                        on_command(cmd)
        threading.Thread(target=loop, daemon=True).start()

    @staticmethod
    def notify(cmd: str) -> bool:
        """Gui lenh cho ban dang chay. True neu gui duoc."""
        try:
            with open(PORT_FILE) as f:
                port = int(f.read().strip())
            with socket.create_connection(("127.0.0.1", port), timeout=2) as s:
                s.sendall(cmd.encode("ascii"))
            return True
        except (OSError, ValueError):
            return False
