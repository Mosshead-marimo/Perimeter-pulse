import pandas as pd


def extract_process_features(df: pd.DataFrame) -> dict:
    if df is None or df.empty or "process_name" not in df.columns:
        return {
            "unique_process_count": 0,
            "non_standard_process_ratio": 0,
            "rare_process_ratio": 0,
        }

    process_scope = df
    if "direction" in df.columns and (df["direction"] == "OUTBOUND").any():
        process_scope = df[df["direction"] == "OUTBOUND"]

    if process_scope.empty:
        return {
            "unique_process_count": 0,
            "non_standard_process_ratio": 0,
            "rare_process_ratio": 0,
        }

    common_processes = {
        "chrome.exe", "firefox.exe", "msedge.exe", "outlook.exe"
    }

    names = process_scope["process_name"].fillna("").astype(str).str.lower()
    non_standard = names[~names.isin(common_processes)]
    frequency = names.value_counts()
    rare_ratio = (
        float((names.map(frequency) <= 1).sum() / len(names))
        if len(names) > 0
        else 0
    )

    return {
        "unique_process_count": int(names.nunique()),
        "non_standard_process_ratio": float(len(non_standard) / len(names)),
        "rare_process_ratio": rare_ratio,
    }
