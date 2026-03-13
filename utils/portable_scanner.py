import os
import time
from typing import Dict, Any, Optional

from utils.entropy_calculator import EntropyCalculator
from ml_detector.virus_total_api import VirusTotalChecker


class PortableDeviceScanner:
    def __init__(self, entropy_threshold: float = 7.5):
        self.entropy_threshold = entropy_threshold
        self.scan_results: Dict[str, Any] = {
            "threats_found": 0,
            "files_scanned": 0,
            "suspicious_files": [],
            "malware_detected": [],
            "scan_duration": 0,
            "scan_time": time.time(),
        }
        self.yara_rules = self._load_yara_rules()
        self.vt_checker = VirusTotalChecker()

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
                rule AutoRunInfection {
                    strings:
                        $autorun = "autorun.inf" nocase
                        $open = "open=" nocase
                        $shell = "shell\\" nocase
                    condition:
                        $autorun and ($open or $shell)
                }
            """)
        except Exception:
            return None

    def scan_device(self, device_path: str) -> Dict[str, Any]:
        start_time = time.time()

        for root, _, files in os.walk(device_path):
            for file in files:
                file_path = os.path.join(root, file)
                if file.startswith("."):
                    continue

                self.scan_results["files_scanned"] += 1
                try:
                    if self.quick_scan(file_path):
                        threat = self.deep_scan(file_path)
                        if threat:
                            self.scan_results["threats_found"] += 1
                            self.scan_results["suspicious_files"].append(threat)
                except Exception:
                    continue

        self.scan_results["scan_duration"] = time.time() - start_time
        return self.scan_results

    @staticmethod
    def quick_scan(file_path: str) -> bool:
        suspicious_extensions = {
            ".exe",
            ".scr",
            ".vbs",
            ".js",
            ".jar",
            ".bat",
            ".cmd",
            ".ps1",
        }
        suspicious_names = {"autorun.inf", "setup.exe", "installer.exe"}

        file_ext = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path).lower()
        return file_ext in suspicious_extensions or file_name in suspicious_names

    def deep_scan(self, file_path: str) -> Optional[Dict[str, Any]]:
        threat_info: Dict[str, Any] = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
            "detection_method": [],
            "severity": "LOW",
            "threat_name": None,
        }

        if self.yara_rules:
            try:
                matches = self.yara_rules.match(file_path)
                if matches:
                    threat_info["detection_method"].append("YARA")
                    threat_info["threat_name"] = str(matches)
                    threat_info["severity"] = "HIGH"
            except Exception:
                pass

        vt_result = self.vt_checker.check_file_hash(file_path)
        if vt_result and vt_result.get("positives", 0) > 0:
            threat_info["detection_method"].append("VIRUSTOTAL")
            threat_info["threat_name"] = vt_result.get("threat_name", "Unknown")
            threat_info["severity"] = "CRITICAL"
            threat_info["vt_results"] = vt_result

        entropy = EntropyCalculator.calculate_file_entropy(file_path)
        if entropy > self.entropy_threshold:
            threat_info["detection_method"].append("HIGH_ENTROPY")
            threat_info["entropy"] = entropy
            if threat_info["severity"] == "LOW":
                threat_info["severity"] = "MEDIUM"

        if len(threat_info["detection_method"]) >= 3:
            threat_info["severity"] = "CRITICAL"
        elif threat_info["detection_method"] and threat_info["severity"] == "LOW":
            threat_info["severity"] = "MEDIUM"

        return threat_info if threat_info["detection_method"] else None
