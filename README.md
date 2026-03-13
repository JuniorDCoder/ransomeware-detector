# Ransomware Detector

End-to-end ransomware detection with local agents, centralized alerting, external device scanning, and a real-time dashboard — packaged as a cross-platform installable application.

---

## Quick Install

### Linux / macOS

```bash
bash install.sh   # one-time setup: creates .venv, installs deps, copies config
bash run.sh       # starts server + dashboard + opens browser automatically
```

### Windows (CMD)

```bat
install.bat
run.bat
```

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
run.bat
```

### Docker

```bash
docker compose up
# Server    → http://localhost:5000
# Dashboard → http://localhost:5001
```

> After running, the **dashboard opens automatically** at `http://localhost:5001`.
> To deploy only the server centrally, use Docker and point agents at its public IP.

---

## CLI Commands (after install)

| Command | Description |
|---|---|
| `rds-server` | Start the API server (port 5000) |
| `rds-dashboard` | Start the web dashboard (port 5001) |
| `rds-agent --config config.json` | Start an agent on a monitored machine |

---


## Features

- File activity monitoring with real-time scanning (extensions, entropy, optional YARA/VT hooks).
- External device (USB/external drives) detection and scanning on connect.
- Network activity monitoring (connection count and throughput).
- Central alert storage with WebSocket broadcast to dashboards.
- Command channel for remote actions (isolate, scan external) with audit trail.
- Optional cloud sync server, Telegram bot, and webhook receiver.
- Mobile API endpoints for a lightweight client.

## How It Works

1. **Agent** runs on each monitored machine.
   - Watches file system events and flags suspicious files.
   - Tracks network activity and raises alerts on high connection counts.
   - Detects removable drives and scans them on connect.
   - Sends heartbeats and alerts to the central server.
   - Polls for commands (isolate, scan) from the server.

2. **Server** receives and stores alerts and agent status.
   - REST API for alerts, stats, and commands.
   - WebSocket broadcast for real-time dashboards.
   - Computes aggregated statistics.
   - Optional Firebase push notifications.

3. **Dashboard** displays live stats and recent alerts.

4. **Cloud server** (optional) syncs and exposes remote APIs for alerts/stats.

## Project Structure

```
agents/                Agent runtime and monitors
server/                Central API, detection engine, database
ml_detector/           Real-time scanner hooks + model training
utils/                 Entropy and portable device scanning
dashboard/             Web dashboard + mobile API endpoints
cloud/                 Cloud sync, Telegram bot, webhook server
```

## Requirements

- Python 3.9+ recommended
- For a quick local run, use the runtime set:

```
requirements.runtime.txt
```

For full feature set (ML stack, cloud, Telegram, plots), use:

```
requirements.txt
```

Note: Some packages are platform-specific (Windows/macOS) and are guarded with markers.

## Configuration

Copy the example config and edit as needed:

```
cp config.example.json config.json
```

Key settings:
- `server_url`: API server URL
- `agent_id`: unique ID for the agent
- `watch_paths`: list of directories to monitor
- `scan_on_connect`: scan external drives on connect
- `entropy_threshold`: high entropy threshold
- `file_change_rate_threshold`: alert on high file activity

Optional environment variables:
- `RDS_SERVER_URL`: override server URL
- `RDS_AGENT_ID`: override agent ID
- `VIRUS_TOTAL_API_KEY`: enable VirusTotal checks
- `RDS_USER` / `RDS_PASSWORD`: API login credentials
- `TELEGRAM_BOT_TOKEN`: Telegram bot

## Run the System (Local)

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install runtime dependencies:

```bash
pip install -r requirements.runtime.txt
```

3. Start the API server:

```bash
python -m server.main_server
```

4. Start the dashboard (new terminal):

```bash
python -m dashboard.app
```

5. Start an agent (new terminal):

```bash
cp config.example.json config.json
python -m agents.agent_client --config config.json
```

The dashboard will query the server every 5 seconds for stats and recent alerts.

## Optional Components

- Cloud sync server:

```bash
python -m server.cloud_server
```

- Webhook receiver:

```bash
python -m cloud.webhook_server
```

- Telegram bot:

```bash
export TELEGRAM_BOT_TOKEN=your_token
python -m cloud.telegram_bot
```

## Main API Endpoints

- `POST /api/agents/heartbeat`
- `GET /api/agents`
- `POST /api/alerts`
- `GET /api/alerts/recent?limit=50`
- `POST /api/alert/<id>/acknowledge`
- `GET /api/stats`
- `POST /api/device/<id>/isolate`
- `POST /api/scan/external`
- `GET /api/commands/<agent_id>`
- `POST /api/commands/<id>/complete`

## Notes and Limitations

- Device isolation is a safe simulation; no destructive network actions are performed by default.
- VirusTotal checks are optional and rate-limited by your API key.
- On Linux, external drive detection uses `pyudev` if available; otherwise it falls back to polling.

## Troubleshooting

- If installs fail on heavy ML packages, run with `requirements.runtime.txt` first.
- If binding to `0.0.0.0` is not permitted, set host via:
  - `RDS_SERVER_HOST=127.0.0.1`
  - `RDS_DASHBOARD_HOST=127.0.0.1`

## License

MIT
