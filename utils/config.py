import json
import os
import socket
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "server_url": "http://localhost:5000",
    "agent_id": socket.gethostname(),
    "watch_paths": ["."],
    "scan_on_connect": True,
    "heartbeat_interval": 5,
    "entropy_threshold": 7.5,
    "file_change_rate_threshold": 120,
    "file_change_window_seconds": 60,
    "network_connection_threshold": 200,
    "enable_external_device_monitor": True,
    "enable_network_monitor": True,
    "enable_file_monitor": True,
}


def load_config(path: str = "config.json") -> Dict[str, Any]:
    cfg = DEFAULT_CONFIG.copy()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                cfg.update(data)
        except Exception:
            pass

    # Environment overrides
    cfg["server_url"] = os.getenv("RDS_SERVER_URL", cfg["server_url"])
    cfg["agent_id"] = os.getenv("RDS_AGENT_ID", cfg["agent_id"])
    return cfg
