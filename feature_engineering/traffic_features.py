import pandas as pd


def extract_traffic_features(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return _empty_features()

    traffic_scope = df
    if "direction" in df.columns and (df["direction"] == "OUTBOUND").any():
        traffic_scope = df[df["direction"] == "OUTBOUND"]

    bytes_col = "bytes_sent" if "bytes_sent" in traffic_scope.columns else None
    dst_ip_col = "dst_ip" if "dst_ip" in traffic_scope.columns else None
    dst_port_col = "dst_port" if "dst_port" in traffic_scope.columns else None
    src_ip_col = "src_ip" if "src_ip" in traffic_scope.columns else None

    total_bytes = (
        pd.to_numeric(traffic_scope[bytes_col], errors="coerce").fillna(0).sum()
        if bytes_col
        else 0
    )
    avg_bytes = (
        pd.to_numeric(traffic_scope[bytes_col], errors="coerce").fillna(0).mean()
        if bytes_col
        else 0
    )

    common_port = 0
    if dst_port_col:
        ports = pd.to_numeric(traffic_scope[dst_port_col], errors="coerce").dropna()
        if not ports.mode().empty:
            common_port = int(ports.mode().iloc[0])

    error_ratio = 0
    if "level" in df.columns and len(df) > 0:
        levels = df["level"].astype(str).str.upper()
        error_ratio = float(levels.isin({"ERROR", "CRITICAL", "FATAL"}).sum() / len(df))

    return {
        "avg_bytes_sent": float(avg_bytes) if pd.notna(avg_bytes) else 0,
        "total_bytes_sent": float(total_bytes),
        "connection_count": int(len(traffic_scope)),
        "unique_destination_ips": int(traffic_scope[dst_ip_col].nunique()) if dst_ip_col else 0,
        "common_destination_port": common_port,
        "unique_source_ips": int(traffic_scope[src_ip_col].nunique()) if src_ip_col else 0,
        "total_events": int(len(df)),
        "error_event_ratio": error_ratio,
    }


def _empty_features():
    return {
        "avg_bytes_sent": 0,
        "total_bytes_sent": 0,
        "connection_count": 0,
        "unique_destination_ips": 0,
        "common_destination_port": 0,
        "unique_source_ips": 0,
        "total_events": 0,
        "error_event_ratio": 0,
    }
