import pandas as pd
from math import log2


def _entropy(series: pd.Series) -> float:
    probabilities = series.value_counts(normalize=True)
    return -sum(p * log2(p) for p in probabilities if p > 0)


def extract_entropy_features(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {
            "port_entropy": 0,
            "destination_entropy": 0,
            "source_entropy": 0,
        }

    entropy_scope = df
    if "direction" in df.columns and (df["direction"] == "OUTBOUND").any():
        entropy_scope = df[df["direction"] == "OUTBOUND"]

    return {
        "port_entropy": _entropy(entropy_scope["dst_port"])
        if "dst_port" in entropy_scope.columns and not entropy_scope["dst_port"].empty
        else 0,

        "destination_entropy": _entropy(entropy_scope["dst_ip"])
        if "dst_ip" in entropy_scope.columns and not entropy_scope["dst_ip"].empty
        else 0,
        "source_entropy": _entropy(entropy_scope["src_ip"])
        if "src_ip" in entropy_scope.columns and not entropy_scope["src_ip"].empty
        else 0,
    }
