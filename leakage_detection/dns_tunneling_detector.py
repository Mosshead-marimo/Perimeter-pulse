"""
DNS tunneling heuristic detector.
"""

import pandas as pd


class DNSTunnelingDetector:
    def __init__(self, query_rate_threshold: int = 20):
        self.query_rate_threshold = query_rate_threshold

    def detect(self, df: pd.DataFrame) -> dict:
        if df is None or df.empty:
            return {"detected": False}

        traffic = df.copy()
        if "protocol" not in traffic.columns:
            traffic["protocol"] = ""
        if "dst_port" not in traffic.columns:
            traffic["dst_port"] = 0
        if "line_number" not in traffic.columns:
            traffic["line_number"] = 0

        protocol = traffic["protocol"].astype(str).str.upper()
        dst_port = pd.to_numeric(traffic["dst_port"], errors="coerce").fillna(0).astype(int)
        dns_traffic = traffic[(protocol.isin({"UDP", "DNS"})) & (dst_port == 53)]

        if dns_traffic.empty:
            return {"detected": False}

        query_count = int(len(dns_traffic))
        if query_count <= self.query_rate_threshold:
            return {"detected": False}

        ratio = min(query_count / max(self.query_rate_threshold, 1), 3.0)
        score = min(int(40 + ratio * 20), 95)
        confidence = "HIGH" if query_count >= self.query_rate_threshold * 2 else "MEDIUM"

        return {
            "detected": True,
            "indicator": "Possible DNS tunneling",
            "details": f"Observed {query_count} DNS-like UDP queries to port 53",
            "confidence": confidence,
            "score": score,
            "affected_lines": dns_traffic["line_number"].head(25).astype(int).tolist(),
            "type": "dns_tunneling",
        }
