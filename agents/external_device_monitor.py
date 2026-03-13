import os
import platform
import threading
import time
from typing import Dict

import psutil
import requests

from utils.portable_scanner import PortableDeviceScanner

try:
    if platform.system() == "Windows":
        import win32api
        import win32con
        import win32file
except Exception:
    win32api = None
    win32con = None
    win32file = None


class ExternalDeviceMonitor:
    def __init__(self, agent_id: str, server_url: str, scan_on_connect: bool = True):
        self.agent_id = agent_id
        self.server_url = server_url
        self.scan_on_connect = scan_on_connect
        self.connected_devices: Dict[str, Dict] = {}
        self.device_history = []
        self.scan_threads = []
        self.running = True

        self.monitor_thread = threading.Thread(target=self.monitor_devices, daemon=True)
        self.monitor_thread.start()

    def stop(self):
        self.running = False

    def monitor_devices(self):
        system = platform.system()
        if system == "Windows":
            self.monitor_windows_devices()
        elif system == "Linux":
            self.monitor_linux_devices()
        elif system == "Darwin":
            self.monitor_mac_devices()
        else:
            self.poll_drives()

    def monitor_windows_devices(self):
        try:
            import wmi

            c = wmi.WMI()
            watcher = c.watch_for(
                notification_type="Creation", wmi_class="Win32_USBControllerDevice"
            )

            while self.running:
                usb = watcher()
                if usb:
                    self.refresh_drives_once()
        except Exception:
            self.poll_drives()

    def monitor_linux_devices(self):
        try:
            import pyudev

            context = pyudev.Context()
            monitor = pyudev.Monitor.from_netlink(context)
            monitor.filter_by(subsystem="block")

            for device in iter(monitor.poll, None):
                if not self.running:
                    break
                if device.action in {"add", "remove"}:
                    self.refresh_drives_once()
        except Exception:
            self.poll_drives()

    def monitor_mac_devices(self):
        self.poll_drives()

    def poll_drives(self):
        known_drives = set(self.connected_devices.keys())
        while self.running:
            current_drives = self.get_removable_drives()

            for drive in current_drives - known_drives:
                self.handle_new_device(drive)

            for drive in known_drives - current_drives:
                self.handle_device_removal(drive)

            known_drives = set(self.connected_devices.keys())
            time.sleep(2)

    def refresh_drives_once(self):
        current_drives = self.get_removable_drives()
        known_drives = set(self.connected_devices.keys())

        for drive in current_drives - known_drives:
            self.handle_new_device(drive)

        for drive in known_drives - current_drives:
            self.handle_device_removal(drive)

    def get_removable_drives(self):
        drives = set()
        system = platform.system()

        if system == "Windows":
            for part in psutil.disk_partitions():
                if "removable" in part.opts.lower():
                    drives.add(part.device)
        elif system == "Darwin":
            for part in psutil.disk_partitions():
                if part.mountpoint.startswith("/Volumes/"):
                    drives.add(part.mountpoint)
        else:
            for part in psutil.disk_partitions():
                if part.mountpoint.startswith("/media/") or part.mountpoint.startswith("/mnt/"):
                    drives.add(part.mountpoint)
                if part.mountpoint.startswith("/run/media/"):
                    drives.add(part.mountpoint)

        return drives

    def handle_new_device(self, device_path: str):
        device_info = self.get_device_info(device_path)
        self.connected_devices[device_path] = {
            "info": device_info,
            "connected_at": time.time(),
            "scan_status": "pending",
        }

        self.send_alert(
            {
                "level": "INFO",
                "type": "EXTERNAL_DEVICE_CONNECTED",
                "message": f"External device connected: {device_info['name']}",
                "device": device_info,
                "timestamp": time.time(),
            }
        )

        if self.scan_on_connect:
            scan_thread = threading.Thread(
                target=self.scan_device, args=(device_path, device_info), daemon=True
            )
            scan_thread.start()
            self.scan_threads.append(scan_thread)

    def handle_device_removal(self, device_path: str):
        if device_path not in self.connected_devices:
            return

        device_info = self.connected_devices[device_path]
        self.device_history.append(
            {
                "device": device_info["info"],
                "connected_at": device_info["connected_at"],
                "disconnected_at": time.time(),
                "scan_status": device_info["scan_status"],
            }
        )

        self.send_alert(
            {
                "level": "INFO",
                "type": "EXTERNAL_DEVICE_REMOVED",
                "message": f"External device removed: {device_info['info']['name']}",
                "device": device_info["info"],
                "timestamp": time.time(),
            }
        )

        del self.connected_devices[device_path]

    def get_device_info(self, device_path: str):
        info = {
            "path": device_path,
            "name": os.path.basename(device_path) or device_path,
            "type": "Unknown",
            "size": 0,
            "filesystem": "Unknown",
            "serial": None,
            "vendor": None,
            "product": None,
        }

        try:
            system = platform.system()
            if system == "Windows" and win32file and win32con and win32api:
                drive_type = win32file.GetDriveType(device_path)
                if drive_type == win32con.DRIVE_REMOVABLE:
                    info["type"] = "USB Drive"
                elif drive_type == win32con.DRIVE_CDROM:
                    info["type"] = "CD/DVD"

                volume_name, serial, _, _, fs = win32api.GetVolumeInformation(device_path)
                info["name"] = volume_name or info["name"]
                info["serial"] = serial
                info["filesystem"] = fs

                usage = psutil.disk_usage(device_path)
                info["size"] = usage.total
                info["free"] = usage.free
            else:
                stat = os.statvfs(device_path)
                info["size"] = stat.f_frsize * stat.f_blocks
                info["free"] = stat.f_frsize * stat.f_bfree
                with open("/proc/mounts", "r", encoding="utf-8") as f:
                    for line in f:
                        if device_path in line:
                            parts = line.split()
                            info["filesystem"] = parts[2]
                            break
        except Exception:
            pass

        return info

    def scan_device(self, device_path: str, device_info: Dict):
        if device_path in self.connected_devices:
            self.connected_devices[device_path]["scan_status"] = "scanning"

        scanner = PortableDeviceScanner()
        scan_results = scanner.scan_device(device_path)

        if device_path in self.connected_devices:
            self.connected_devices[device_path]["scan_status"] = "completed"
            self.connected_devices[device_path]["scan_results"] = scan_results

        if scan_results.get("threats_found", 0) > 0:
            self.send_alert(
                {
                    "level": "CRITICAL",
                    "type": "DEVICE_THREAT_DETECTED",
                    "message": f"Found {scan_results['threats_found']} threats on {device_info['name']}",
                    "device": device_info,
                    "scan_results": scan_results,
                    "timestamp": time.time(),
                }
            )
        else:
            self.send_alert(
                {
                    "level": "INFO",
                    "type": "DEVICE_SCAN_COMPLETE",
                    "message": f"Device {device_info['name']} scan complete - No threats found",
                    "device": device_info,
                    "scan_results": scan_results,
                    "timestamp": time.time(),
                }
            )

    def send_alert(self, alert_data: Dict):
        try:
            alert_data["agent_id"] = self.agent_id
            requests.post(f"{self.server_url}/api/alerts", json=alert_data, timeout=5)
        except Exception:
            pass
