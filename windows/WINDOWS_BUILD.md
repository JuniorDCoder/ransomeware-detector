# RansomGuard — Windows Build Guide

## What You Get

Running `python windows/build.py` on a Windows machine produces:

```
windows/dist/
├── RansomGuardApp/          ← Folder with all files (can be zipped and distributed)
│   ├── RansomGuard.exe      ← Main launcher (double-click to start)
│   └── ... (supporting files)
└── RansomGuard-Setup.exe    ← Single installer EXE (if Inno Setup is installed)
```

## Step-by-Step Build Instructions (Run on Windows)

### 1. Prerequisites

- **Python 3.9+** — [python.org](https://python.org)
- **Git** (to clone the repo) — [git-scm.com](https://git-scm.com)
- **Inno Setup 6** (for the installer .exe) — [jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php)

### 2. Clone and Install

```bat
git clone <your-repo-url> RansomGuard
cd RansomGuard
install.bat
```

### 3. Build the EXE

```bat
python windows\build.py
```

This will:
1. Auto-install PyInstaller, pystray, Pillow
2. Run PyInstaller with `windows\RansomGuard.spec`
3. Bundle everything into `windows\dist\RansomGuardApp\`
4. If Inno Setup is found: compile `windows\setup.iss` → `windows\dist\RansomGuard-Setup.exe`

### 4. Distribute

- **For a single file installer**: send `RansomGuard-Setup.exe` to users.
- **For a portable version**: zip up `windows\dist\RansomGuardApp\` and distribute.

## What Happens When a User Runs the Installer

1. Inno Setup wizard runs — standard "Next / Install" flow
2. Files are copied to `C:\Program Files\RansomGuard\`
3. Start Menu shortcut is created
4. Optional: Desktop shortcut + Windows startup entry
5. `config.json` is created from the example if it doesn't exist
6. **The app launches automatically** — a 🛡️ shield icon appears in the system tray

## What the App Does (After Installing)

- A **system tray icon** appears in the notification area (bottom-right)
- Right-click the icon → **Open Dashboard** — opens `http://localhost:5001` in your browser
- Right-click → **Stop RansomGuard** — shuts everything down cleanly
- All three services run invisibly in the background:
  - API Server on port 5000
  - Dashboard on port 5001
  - Agent monitoring files, network, and USB drives

## Ports

| Service    | Port |
|------------|------|
| API Server | 5000 |
| Dashboard  | 5001 |

These can be changed via environment variables or by editing `config.json` in the install folder.

## Customising the Config

After install, edit: `C:\Program Files\RansomGuard\config.json`

| Key | Default | Description |
|---|---|---|
| `server_url` | `http://localhost:5000` | Where the agent sends alerts |
| `watch_paths` | `["."]` | Folders to monitor |
| `agent_id` | hostname | This machine's name in the dashboard |

Then restart RansomGuard from the tray icon.
