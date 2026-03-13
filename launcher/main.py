"""
RansomGuard Launcher — Windows System Tray Application
Starts the API server, dashboard, and agent as background processes.
Adds a system tray icon with menu to open the dashboard and stop the app.

Built with: PyInstaller (bundled .exe), pystray, Pillow
"""

import os
import sys
import time
import threading
import subprocess
import webbrowser

# ── Resolve paths ──────────────────────────────────────────────────────────────
# When running as a PyInstaller bundle, _MEIPASS holds the extracted payload.
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS                    # inside the bundle
    EXE_DIR  = os.path.dirname(sys.executable) # next to the .exe
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    EXE_DIR  = BASE_DIR

CONFIG_FILE = os.path.join(EXE_DIR, "config.json")
DATA_DIR    = EXE_DIR  # data.db lives next to the .exe

# ── Environment ────────────────────────────────────────────────────────────────
os.environ.setdefault("RDS_SERVER_HOST",    "127.0.0.1")
os.environ.setdefault("RDS_SERVER_PORT",    "5000")
os.environ.setdefault("RDS_DASHBOARD_HOST", "127.0.0.1")
os.environ.setdefault("RDS_DASHBOARD_PORT", "5001")
os.environ.setdefault("RDS_DATA_DIR",       DATA_DIR)

DASHBOARD_URL = (
    f"http://{os.environ['RDS_DASHBOARD_HOST']}:{os.environ['RDS_DASHBOARD_PORT']}"
)

_procs: list[subprocess.Popen] = []


def _find_python():
    """Return path to this interpreter (frozen) or python3 (dev)."""
    if getattr(sys, "frozen", False):
        return sys.executable  # PyInstaller: launcher itself IS the container
    for candidate in ("python3", "python"):
        import shutil
        p = shutil.which(candidate)
        if p:
            return p
    return sys.executable


def _start(module: str, *extra_args):
    """Start a Python module as a detached subprocess."""
    cmd = [_find_python(), "-m", module, *extra_args]
    env = {**os.environ}
    p = subprocess.Popen(
        cmd,
        cwd=EXE_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    _procs.append(p)
    return p


def _wait_for_server(timeout=15):
    import urllib.request, urllib.error
    for _ in range(timeout * 4):
        try:
            urllib.request.urlopen(
                f"http://{os.environ['RDS_SERVER_HOST']}:{os.environ['RDS_SERVER_PORT']}/api/stats",
                timeout=1,
            )
            return True
        except Exception:
            time.sleep(0.25)
    return False


def _copy_default_config():
    if not os.path.exists(CONFIG_FILE):
        example = os.path.join(BASE_DIR, "config.example.json")
        if os.path.exists(example):
            import shutil
            shutil.copy(example, CONFIG_FILE)


def _start_all():
    _copy_default_config()
    _start("server")
    _wait_for_server()
    _start("dashboard")
    time.sleep(1)
    _start("agents", "--config", CONFIG_FILE)
    time.sleep(1)
    webbrowser.open(DASHBOARD_URL)


def _stop_all():
    for p in _procs:
        try:
            p.terminate()
        except Exception:
            pass
    for p in _procs:
        try:
            p.wait(timeout=5)
        except Exception:
            pass


# ── Tray icon ──────────────────────────────────────────────────────────────────
def _build_icon():
    """Create a simple shield icon programmatically (Pillow)."""
    try:
        from PIL import Image, ImageDraw
        img  = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Shield shape
        draw.polygon([(32, 4), (60, 16), (60, 36), (32, 60), (4, 36), (4, 16)],
                     fill=(99, 102, 241))
        # Check mark
        draw.line([(18, 32), (28, 44), (46, 20)], fill="white", width=5)
        return img
    except ImportError:
        return None


def run_tray():
    try:
        import pystray
        from pystray import MenuItem as Item
    except ImportError:
        # If pystray not available, just run headless and keep alive
        _start_all()
        try:
            while all(p.poll() is None for p in _procs if _procs):
                time.sleep(2)
        except KeyboardInterrupt:
            pass
        _stop_all()
        return

    icon_image = _build_icon()

    def on_open(icon, item):
        webbrowser.open(DASHBOARD_URL)

    def on_quit(icon, item):
        _stop_all()
        icon.stop()

    menu = pystray.Menu(
        Item("Open Dashboard", on_open, default=True),
        pystray.Menu.SEPARATOR,
        Item("Stop RansomGuard", on_quit),
    )

    tray = pystray.Icon(
        "RansomGuard",
        icon_image,
        "RansomGuard — Running",
        menu,
    )

    # Start processes in background, then enter tray loop
    threading.Thread(target=_start_all, daemon=True).start()
    tray.run()


if __name__ == "__main__":
    run_tray()
