"""
Covert channel heuristic detector.
"""

import pandas as pd
import numpy as np


class CovertChannelDetector:
    def __init__(self, entropy_threshold: float = 1.5):
        self.entropy_threshold = entropy_threshold

    def detect(self, df: pd.DataFrame) -> dict:
        if df is None or df.empty:
            return {"detected": False}

        traffic = df.copy()
        if "direction" not in traffic.columns:
            traffic["direction"] = "UNKNOWN"
        if "dst_port" not in traffic.columns:
            traffic["dst_port"] = 0
        if "line_number" not in traffic.columns:
            traffic["line_number"] = 0

        outbound = traffic[traffic["direction"].astype(str).str.upper() == "OUTBOUND"]
        if outbound.empty:
            return {"detected": False}

        ports = pd.to_numeric(outbound["dst_port"], errors="coerce").fillna(0).astype(int)
        port_counts = ports.value_counts(normalize=True)
        entropy = float(-np.sum(port_counts * np.log2(port_counts))) if not port_counts.empty else 0.0
        if entropy <= self.entropy_threshold:
            return {"detected": False}

        ratio = min(entropy / max(self.entropy_threshold, 0.1), 3.0)
        score = min(int(35 + ratio * 20), 90)
        confidence = "HIGH" if entropy >= self.entropy_threshold * 1.7 else "MEDIUM"

        return {
            "detected": True,
            "indicator": "Potential covert channel behavior",
            "details": f"Outbound destination port entropy: {entropy:.2f}",
            "confidence": confidence,
            "score": score,
            "affected_lines": outbound["line_number"].head(25).astype(int).tolist(),
            "type": "covert_channel",
        }
