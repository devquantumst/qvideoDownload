import webview
import threading
import http.server
import socketserver
import os
import sys
import time
import re
import ctypes
import win32gui

# === CONFIG ===
PORT = 8000
WINDOW_TITLE = "QvideoDownloader"
ICON_FILE = 'Qvideo.ico'  # Must be .ico format
WINDOW_WIDTH = 930
WINDOW_HEIGHT = 670
MIN_WIDTH = 870
MIN_HEIGHT = 650

# Support PyInstaller: detect if running from a bundle
if hasattr(sys, '_MEIPASS'):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

WEB_DIR = os.path.join(base_dir, 'public')
ICON_PATH = os.path.join(base_dir, ICON_FILE)


# === HTTP Server ===
def start_server():
    os.chdir(WEB_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        httpd.serve_forever()


# === Find and Set Window Icon ===
class WindowMgr:
    def __init__(self):
        self._handle = None

    @property
    def handle(self):
        return self._handle

    def _window_enum_callback(self, hwnd, wildcard):
        if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) is not None:
            self._handle = hwnd

    def find_window_wildcard(self, wildcard):
        self._handle = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)
        return self


def set_icon(icon_path: str, hWnd=None):
    assert os.path.exists(icon_path), f"Invalid icon path: {icon_path}"
    user32 = ctypes.windll.user32
    ICON_SMALL = 0
    ICON_BIG = 1
    WM_SETICON = 0x0080

    hIcon = user32.LoadImageW(None, icon_path, 1, 0, 0, 0x00000010)
    ctypes.windll.user32.SendMessageW(hWnd, WM_SETICON, ICON_SMALL, hIcon)
    ctypes.windll.user32.SendMessageW(hWnd, WM_SETICON, ICON_BIG, hIcon)


def set_window_icon(icon_path: str, window_title: str, tries: int = 10):
    def _set_icon():
        for _ in range(tries):
            hwnd = WindowMgr().find_window_wildcard(window_title).handle
            if hwnd:
                set_icon(icon_path, hwnd)
                break
            time.sleep(1)
    threading.Thread(target=_set_icon, daemon=True).start()


# === WebView loaded callback ===
def on_loaded():
    time.sleep(0.5)
    set_window_icon(ICON_PATH, WINDOW_TITLE)


# === Start server and launch window ===
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

webview.create_window(
    WINDOW_TITLE,
    f"http://localhost:{PORT}/index.html",
    width=WINDOW_WIDTH,
    height=WINDOW_HEIGHT,
    min_size=(MIN_WIDTH, MIN_HEIGHT)
)

webview.start(on_loaded)
