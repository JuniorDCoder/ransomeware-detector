import argparse
import json
import platform
import time
from typing import Dict, Any

import requests

from agents.file_monitor import FileMonitor
from agents.network_monitor import NetworkMonitor
from agents.external_device_monitor import ExternalDeviceMonitor
from utils.config import load_config


def send_heartbeat(server_url: str, agent_id: str, data: Dict[str, Any]):
    payload = {
        "agent_id": agent_id,
        "timestamp": time.time(),
        "data": data,
    }
    try:
        requests.post(f"{server_url}/api/agents/heartbeat", json=payload, timeout=5)
    except Exception:
        pass


def send_alert(server_url: str, agent_id: str, level: str, alert_type: str, message: str, details=None):
    payload = {
        "level": level,
        "type": alert_type,
        "message": message,
        "agent_id": agent_id,
        "timestamp": time.time(),
        "details": details or {},
    }
    try:
        requests.post(f"{server_url}/api/alerts", json=payload, timeout=5)
    except Exception:
        pass


def poll_commands(server_url: str, agent_id: str):
    try:
        resp = requests.get(f"{server_url}/api/commands/{agent_id}", timeout=5)
        if resp.status_code == 200:
            return resp.json().get("commands", [])
    except Exception:
        pass
    return []


def complete_command(server_url: str, command_id: str, status: str, result=None):
    try:
        requests.post(
            f"{server_url}/api/commands/{command_id}/complete",
            json={"status": status, "result": result or {}},
            timeout=5,
        )
    except Exception:
        pass


def run_agent(config_path: str):
    cfg = load_config(config_path)
    server_url = cfg["server_url"]
    agent_id = cfg["agent_id"]

    file_monitor = None
    if cfg.get("enable_file_monitor", True):
        file_monitor = FileMonitor(
            agent_id=agent_id,
            server_url=server_url,
            watch_paths=cfg.get("watch_paths", ["."]),
            entropy_threshold=cfg.get("entropy_threshold", 7.5),
            rate_threshold=cfg.get("file_change_rate_threshold", 120),
            rate_window_seconds=cfg.get("file_change_window_seconds", 60),
        )
        try:
            file_monitor.start()
        except Exception:
            file_monitor = None

    external_monitor = None
    if cfg.get("enable_external_device_monitor", True):
        try:
            external_monitor = ExternalDeviceMonitor(
                agent_id=agent_id,
                server_url=server_url,
                scan_on_connect=cfg.get("scan_on_connect", True),
            )
        except Exception:
            external_monitor = None

    network_monitor = None
    if cfg.get("enable_network_monitor", True):
        network_monitor = NetworkMonitor(
            connection_threshold=cfg.get("network_connection_threshold", 200)
        )

    base_info = {
        "system": {
            "platform": platform.platform(),
            "python": platform.python_version(),
        }
    }

    while True:
        stats: Dict[str, Any] = {}
        if network_monitor:
            net_stats = network_monitor.collect_stats()
            stats["network"] = net_stats
            if network_monitor.is_suspicious(net_stats):
                send_alert(
                    server_url,
                    agent_id,
                    level="WARNING",
                    alert_type="SUSPICIOUS_NETWORK_ACTIVITY",
                    message="High number of network connections detected",
                    details=net_stats,
                )

        data = {"stats": stats, **base_info}
        send_heartbeat(server_url, agent_id, data)

        commands = poll_commands(server_url, agent_id)
        for cmd in commands:
            command_id = cmd.get("id")
            command_type = cmd.get("command")
            if command_type == "ISOLATE":
                # Placeholder: no destructive network changes in this reference implementation
                result = {"status": "simulated_isolation"}
                complete_command(server_url, command_id, "completed", result=result)
            elif command_type == "SCAN_EXTERNAL":
                result = {"status": "scan_requested"}
                complete_command(server_url, command_id, "completed", result=result)
            else:
                complete_command(server_url, command_id, "ignored", result={})

        time.sleep(cfg.get("heartbeat_interval", 5))


def main():
    parser = argparse.ArgumentParser(description="Ransomware Detection Agent")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    args = parser.parse_args()
    run_agent(args.config)


if __name__ == "__main__":
    main()
