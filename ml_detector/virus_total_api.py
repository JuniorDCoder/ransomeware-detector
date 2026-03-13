import hashlib
import os
from typing import Optional, Dict, Any


class VirusTotalChecker:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("VIRUS_TOTAL_API_KEY")
        self.cache: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def calculate_file_hash(file_path: str, hash_type: str = "sha256") -> str:
        hash_func = hashlib.sha256() if hash_type == "sha256" else hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def check_file_hash(self, file_path: str) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None
        try:
            file_hash = self.calculate_file_hash(file_path)
            if file_hash in self.cache:
                return self.cache[file_hash]

            import vt

            client = vt.Client(self.api_key)
            try:
                file_obj = client.get_object(f"/files/{file_hash}")
                result = {
                    "positives": file_obj.last_analysis_stats.get("malicious", 0),
                    "total": sum(file_obj.last_analysis_stats.values()),
                    "threat_name": file_obj.meaningful_name,
                    "scan_date": file_obj.last_analysis_date,
                    "permalink": f"https://www.virustotal.com/gui/file/{file_hash}",
                }
                self.cache[file_hash] = result
                return result
            finally:
                client.close()
        except Exception:
            return None
