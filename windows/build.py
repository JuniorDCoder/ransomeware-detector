"""
Build script — creates the Windows .exe with PyInstaller.

Run this on WINDOWS (or in a Windows VM/container) from the project root:
    python windows/build.py

Output:
    windows/dist/RansomGuard-Setup.exe   ← installer (if Inno Setup found)
    windows/dist/RansomGuardApp/         ← raw PyInstaller folder build

Requirements (auto-installed):
    pip install pyinstaller pystray pillow

Inno Setup (optional, for the .exe installer):
    Download from https://jrsoftware.org/isdl.php and install, then re-run this script.
"""

import os
import sys
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIN_DIR  = os.path.join(ROOT, "windows")
DIST_DIR = os.path.join(WIN_DIR, "dist")
WORK_DIR = os.path.join(WIN_DIR, "build_work")
SPEC     = os.path.join(WIN_DIR, "RansomGuard.spec")
ISS      = os.path.join(WIN_DIR, "setup.iss")


def run(cmd, **kw):
    print(f"  $ {' '.join(cmd)}")
    subprocess.check_call(cmd, **kw)


def ensure_deps():
    missing = []
    for pkg in ("PyInstaller", "pystray", "Pillow"):
        try:
            __import__(pkg.lower().replace("-", "_").replace("pyinstaller", "PyInstaller"))
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"  Installing: {', '.join(missing)}")
        run([sys.executable, "-m", "pip", "install", "-q"] + missing)


def build_exe():
    print("\n  Building with PyInstaller…")
    run([
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        f"--distpath={DIST_DIR}",
        f"--workpath={WORK_DIR}",
        SPEC,
    ])
    print("  PyInstaller build complete.")


def build_installer():
    """Try to compile the Inno Setup .iss into a single .exe installer."""
    # Common Inno Setup install locations
    iscc_candidates = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        shutil.which("iscc"),
    ]
    iscc = next((p for p in iscc_candidates if p and os.path.exists(p)), None)
    if not iscc:
        print("\n  [SKIP] Inno Setup not found — only folder build produced.")
        print("         Download from https://jrsoftware.org/isdl.php, install, then re-run.")
        return
    print(f"\n  Building installer with Inno Setup…")
    run([iscc, f"/O{DIST_DIR}", ISS])
    installer = os.path.join(DIST_DIR, "RansomGuard-Setup.exe")
    if os.path.exists(installer):
        size_mb = os.path.getsize(installer) / 1024 / 1024
        print(f"\n  \033[32m✔  Installer: {installer} ({size_mb:.1f} MB)\033[0m")


if __name__ == "__main__":
    os.chdir(ROOT)
    ensure_deps()
    os.makedirs(DIST_DIR, exist_ok=True)
    build_exe()
    build_installer()
    print("\n  Done!\n")
