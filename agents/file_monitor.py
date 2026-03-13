import time
from collections import deque
from typing import Callable

import requests
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from ml_detector.realtime_scanner import RealTimeScanner


class FileMonitor:
    def __init__(
        self,
        agent_id: str,
        server_url: str,
        watch_paths,
        entropy_threshold: float,
        rate_threshold: int,
        rate_window_seconds: int,
    ):
        self.agent_id = agent_id
        self.server_url = server_url
        self.watch_paths = watch_paths
        self.scanner = RealTimeScanner(entropy_threshold=entropy_threshold)
        self.rate_threshold = rate_threshold
        self.rate_window_seconds = rate_window_seconds
        self.event_times = deque()
        self.last_rate_alert = 0.0

        self.observer = Observer()
        self.handler = _FileEventHandler(self._handle_file_event)

    def start(self):
        for path in self.watch_paths:
            self.observer.schedule(self.handler, path, recursive=True)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

    def _handle_file_event(self, path: str):
        now = time.time()
        self.event_times.append(now)
        while self.event_times and now - self.event_times[0] > self.rate_window_seconds:
            self.event_times.popleft()

        if len(self.event_times) >= self.rate_threshold:
            if now - self.last_rate_alert > self.rate_window_seconds:
                self.last_rate_alert = now
                self._send_alert(
                    level="WARNING",
                    alert_type="HIGH_FILE_CHANGE_RATE",
                    message=f"High file change rate detected: {len(self.event_times)} changes in window",
                    details={
                        "rate_window_seconds": self.rate_window_seconds,
                        "event_count": len(self.event_times),
                    },
                )

        result = self.scanner.scan_file(path)
        if result:
            self._send_alert(
                level=result.get("severity", "WARNING"),
                alert_type="SUSPICIOUS_FILE_ACTIVITY",
                message=f"Suspicious file detected: {result.get('file_name')}",
                details=result,
            )

    def _send_alert(self, level: str, alert_type: str, message: str, details=None):
        payload = {
            "level": level,
            "type": alert_type,
            "message": message,
            "agent_id": self.agent_id,
            "timestamp": time.time(),
            "details": details or {},
        }
        try:
            requests.post(f"{self.server_url}/api/alerts", json=payload, timeout=5)
        except Exception:
            pass


class _FileEventHandler(FileSystemEventHandler):
    def __init__(self, on_event: Callable[[str], None]):
        super().__init__()
        self.on_event = on_event

    def on_created(self, event):
        if not event.is_directory:
            self.on_event(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.on_event(event.src_path)
