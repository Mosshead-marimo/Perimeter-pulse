import pandas as pd
from datetime import time

BUSINESS_START = time(9, 0)
BUSINESS_END = time(18, 0)


def extract_temporal_features(df: pd.DataFrame) -> dict:
    if df is None or df.empty or "timestamp" not in df.columns:
        return {
            "off_hours_ratio": 0,
            "connections_per_hour": 0,
            "peak_hour_volume": 0,
        }

    timestamps = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    temporal_df = df.copy()
    temporal_df["timestamp"] = timestamps
    temporal_df = temporal_df[temporal_df["timestamp"].notna()]

    if temporal_df.empty:
        return {
            "off_hours_ratio": 0,
            "connections_per_hour": 0,
            "peak_hour_volume": 0,
        }

    off_hours = temporal_df[
        (temporal_df["timestamp"].dt.time < BUSINESS_START) |
        (temporal_df["timestamp"].dt.time > BUSINESS_END)
    ]
    per_hour = temporal_df.groupby(temporal_df["timestamp"].dt.hour).size()

    return {
        "off_hours_ratio": float(len(off_hours) / len(temporal_df)),
        "connections_per_hour": float(per_hour.mean()) if not per_hour.empty else 0,
        "peak_hour_volume": int(per_hour.max()) if not per_hour.empty else 0,
    }
