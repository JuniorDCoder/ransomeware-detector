import os
from typing import Dict, Any, Optional

from utils.entropy_calculator import EntropyCalculator
from ml_detector.virus_total_api import VirusTotalChecker


class RealTimeScanner:
    def __init__(self, entropy_threshold: float = 7.5):
        self.entropy_threshold = entropy_threshold
        self.vt_checker = VirusTotalChecker()
        self.yara_rules = self._load_yara_rules()

    def _load_yara_rules(self):
        try:
            import yara
            return yara.compile(source="""
                rule SuspiciousExecutable {
                    strings:
                        $mz = {4d 5a}
                        $elf = {7f 45 4c 46}
                    condition:
                        $mz at 0 or $elf at 0
                }
            """)
        except Exception:
            return None

    def scan_file(self, path: str) -> Optional[Dict[str, Any]]:
        if not os.path.isfile(path):
            return None

        info: Dict[str, Any] = {
            "file_path": path,
            "file_name": os.path.basename(path),
            "file_size": os.path.getsize(path),
            "detection_method": [],
            "severity": "LOW",
        }

        ext = os.path.splitext(path)[1].lower()
        if ext in {".exe", ".scr", ".vbs", ".js", ".jar", ".bat", ".cmd", ".ps1"}:
            info["detection_method"].append("SUSPICIOUS_EXTENSION")
            info["severity"] = "MEDIUM"

        if self.yara_rules:
            try:
                matches = self.yara_rules.match(path)
                if matches:
                    info["detection_method"].append("YARA")
                    info["severity"] = "HIGH"
            except Exception:
                pass

        entropy = EntropyCalculator.calculate_file_entropy(path)
        if entropy >= self.entropy_threshold:
            info["detection_method"].append("HIGH_ENTROPY")
            if info["severity"] == "LOW":
                info["severity"] = "MEDIUM"
            info["entropy"] = entropy

        vt = self.vt_checker.check_file_hash(path)
        if vt and vt.get("positives", 0) > 0:
            info["detection_method"].append("VIRUSTOTAL")
            info["severity"] = "CRITICAL"
            info["vt_results"] = vt

        if not info["detection_method"]:
            return None

        if len(info["detection_method"]) >= 3:
            info["severity"] = "CRITICAL"

        return info
