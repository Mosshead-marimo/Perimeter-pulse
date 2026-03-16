import pandas as pd


class LogNormalizer:
    """
    Enforces a strict, ML-safe schema for firewall logs
    """

    SCHEMA = {
        "timestamp": pd.NaT,
        "action": "UNKNOWN",
        "protocol": "UNKNOWN",
        "src_ip": "0.0.0.0",
        "dst_ip": "0.0.0.0",
        "src_port": 0,
        "dst_port": 0,
        "bytes_sent": 0,
        "direction": "UNKNOWN"
    }

    def normalize(self, records: list) -> pd.DataFrame:
        # Build DataFrame safely
        df = pd.DataFrame(records)

        # Enforce schema (THIS IS THE KEY FIX)
        for col, default in self.SCHEMA.items():
            if col not in df.columns:
                df[col] = default

        # Normalize types
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["bytes_sent"] = pd.to_numeric(df["bytes_sent"], errors="coerce").fillna(0)
        df["src_port"] = pd.to_numeric(df["src_port"], errors="coerce").fillna(0)
        df["dst_port"] = pd.to_numeric(df["dst_port"], errors="coerce").fillna(0)
        df["direction"] = df["direction"].astype(str).str.upper()

        return df
