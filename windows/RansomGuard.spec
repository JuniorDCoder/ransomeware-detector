# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for RansomGuard Windows Application.

This builds a FOLDER distribution (one directory with an exe + all dependencies).
The Inno Setup script (setup.iss) then packs that folder into a single installer .exe.

To build (on Windows, from project root):
    python windows/build.py
Or directly:
    pyinstaller windows/RansomGuard.spec
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

a = Analysis(
    [os.path.join(ROOT, "launcher", "main.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[
        # Dashboard HTML templates
        (os.path.join(ROOT, "dashboard", "templates"), "dashboard/templates"),
        # Default config
        (os.path.join(ROOT, "config.example.json"), "."),
        # All source packages
        (os.path.join(ROOT, "server"),      "server"),
        (os.path.join(ROOT, "agents"),      "agents"),
        (os.path.join(ROOT, "dashboard"),   "dashboard"),
        (os.path.join(ROOT, "utils"),       "utils"),
        (os.path.join(ROOT, "cloud"),       "cloud"),
        (os.path.join(ROOT, "ml_detector"), "ml_detector"),
    ],
    hiddenimports=[
        # Flask & extensions
        "flask", "flask_socketio", "flask_cors", "flask_jwt_extended",
        "python_socketio", "engineio", "eventlet", "eventlet.hubs.epolls",
        "eventlet.hubs.kqueue", "eventlet.hubs.selects",
        # Monitoring
        "watchdog", "watchdog.observers", "watchdog.observers.polling",
        "psutil",
        # Tray
        "pystray", "pystray._win32",
        "PIL", "PIL.Image", "PIL.ImageDraw",
        # All project modules
        *collect_submodules("server"),
        *collect_submodules("agents"),
        *collect_submodules("dashboard"),
        *collect_submodules("utils"),
        # Windows-specific
        "win32api", "win32con", "win32gui",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy unused extras
        "scikit_learn", "pandas", "numpy", "matplotlib",
        "firebase_admin", "telegram",
        "tkinter", "_tkinter",
        "test", "unittest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RansomGuard",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,         # No console window — tray app only
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="windows/icon.ico",  # Uncomment if you add an icon file
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RansomGuardApp",
)
