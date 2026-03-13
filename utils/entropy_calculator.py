import math


class EntropyCalculator:
    @staticmethod
    def calculate_bytes_entropy(data: bytes) -> float:
        if not data:
            return 0.0
        freq = [0] * 256
        for b in data:
            freq[b] += 1
        entropy = 0.0
        length = len(data)
        for count in freq:
            if count == 0:
                continue
            p = count / length
            entropy -= p * math.log2(p)
        return entropy

    @staticmethod
    def calculate_file_entropy(path: str, max_bytes: int = 1024 * 1024) -> float:
        try:
            with open(path, "rb") as f:
                data = f.read(max_bytes)
            return EntropyCalculator.calculate_bytes_entropy(data)
        except Exception:
            return 0.0
