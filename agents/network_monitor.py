import time
from typing import Dict, Any

import psutil


class NetworkMonitor:
    def __init__(self, connection_threshold: int = 200):
        self.connection_threshold = connection_threshold
        self.last_io = psutil.net_io_counters()
        self.last_time = time.time()

    def collect_stats(self) -> Dict[str, Any]:
        now = time.time()
        try:
            io = psutil.net_io_counters()
            delta_time = max(now - self.last_time, 1)
            connections = len(psutil.net_connections(kind="inet"))
            stats = {
                "connections": connections,
                "bytes_sent_per_sec": (io.bytes_sent - self.last_io.bytes_sent) / delta_time,
                "bytes_recv_per_sec": (io.bytes_recv - self.last_io.bytes_recv) / delta_time,
            }
        except Exception:
            stats = {"connections": 0, "bytes_sent_per_sec": 0.0, "bytes_recv_per_sec": 0.0}

        self.last_io = io if "io" in locals() else self.last_io
        self.last_time = now
        return stats

    def is_suspicious(self, stats: Dict[str, Any]) -> bool:
        return stats.get("connections", 0) >= self.connection_threshold
