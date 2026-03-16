"""
Data exfiltration heuristic detector.
"""

import pandas as pd


class ExfiltrationDetector:
    def __init__(self, threshold_mb: float = 50.0):
        self.threshold_bytes = float(threshold_mb) * 1024 * 1024

    def detect(self, df: pd.DataFrame) -> dict:
        if df is None or df.empty:
            return {"detected": False}

        traffic = df.copy()
        if "direction" not in traffic.columns:
            traffic["direction"] = "UNKNOWN"
        if "bytes_sent" not in traffic.columns:
            traffic["bytes_sent"] = 0
        if "line_number" not in traffic.columns:
            traffic["line_number"] = 0

        outbound = traffic[traffic["direction"].astype(str).str.upper() == "OUTBOUND"].copy()
        if outbound.empty:
            return {"detected": False}

        outbound["bytes_sent"] = pd.to_numeric(outbound["bytes_sent"], errors="coerce").fillna(0)
        total_bytes = float(outbound["bytes_sent"].sum())
        if total_bytes <= self.threshold_bytes:
            return {"detected": False}

        ratio = min(total_bytes / max(self.threshold_bytes, 1), 4.0)
        score = min(int(45 + ratio * 15), 98)
        confidence = "HIGH" if ratio >= 2 else "MEDIUM"

        top_lines = outbound.nlargest(25, "bytes_sent")["line_number"].astype(int).tolist()
        return {
            "detected": True,
            "indicator": "High outbound data volume",
            "details": f"Total outbound transfer {total_bytes / (1024 * 1024):.2f} MB exceeded threshold",
            "confidence": confidence,
            "score": score,
            "affected_lines": top_lines,
            "type": "exfiltration",
        }
