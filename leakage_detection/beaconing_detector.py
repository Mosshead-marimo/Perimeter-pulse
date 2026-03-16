"""
Beaconing heuristic detector.
"""

import pandas as pd


class BeaconingDetector:
    def __init__(self, min_beacons: int = 5):
        self.min_beacons = min_beacons

    def detect(self, df: pd.DataFrame) -> dict:
        if df is None or df.empty:
            return {"detected": False}

        traffic = df.copy()
        if "direction" not in traffic.columns:
            traffic["direction"] = "UNKNOWN"
        if "timestamp" not in traffic.columns:
            traffic["timestamp"] = ""
        if "dst_ip" not in traffic.columns:
            traffic["dst_ip"] = ""
        if "line_number" not in traffic.columns:
            traffic["line_number"] = 0

        outbound = traffic[traffic["direction"].astype(str).str.upper() == "OUTBOUND"].copy()
        if outbound.empty:
            return {"detected": False}

        outbound["timestamp"] = pd.to_datetime(outbound["timestamp"], errors="coerce", utc=True)
        outbound = outbound[outbound["timestamp"].notna()]
        if outbound.empty:
            return {"detected": False}

        suspicious_ips = []
        affected_lines = []
        for ip, group in outbound.groupby("dst_ip"):
            if not ip:
                continue
            ordered = group.sort_values("timestamp")
            if len(ordered) < self.min_beacons:
                continue
            diffs = ordered["timestamp"].diff().dt.total_seconds().dropna()
            if diffs.empty:
                continue
            mean = float(diffs.mean())
            std = float(diffs.std()) if len(diffs) > 1 else 0.0
            cv = std / mean if mean > 0 else 99.0

            # Stable short interval repeated calls => beaconing-like behavior
            if cv <= 0.25 and mean <= 600:
                suspicious_ips.append(ip)
                affected_lines.extend(ordered["line_number"].astype(int).tolist())

        if not suspicious_ips:
            return {"detected": False}

        score = min(50 + len(suspicious_ips) * 8, 95)
        confidence = "HIGH" if len(suspicious_ips) >= 2 else "MEDIUM"
        unique_ips = sorted(set(suspicious_ips))
        unique_lines = sorted(set(affected_lines))[:50]
        return {
            "detected": True,
            "indicator": "Beaconing behavior detected",
            "details": f"Periodic outbound traffic to {', '.join(unique_ips)}",
            "confidence": confidence,
            "score": int(score),
            "affected_lines": unique_lines,
            "type": "beaconing",
        }
