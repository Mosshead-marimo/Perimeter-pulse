"""
Master Execution Script
Runs the Log Analyzer pipeline end-to-end

Stages:
1. Ingestion
2. Parsing
3. Feature Engineering
4. Anomaly Detection
5. Leakage Detection
6. Risk Scoring
7. Alerts
"""

import sys
import json
import traceback
from pathlib import Path
from datetime import datetime
import yaml
from reports.report_generator import generate_html_report
# Windows-safe stdout
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ================= REAL IMPORTS (EXISTING) =================
from ingestion.firewall_log_collector import LogCollector
from parsing.firewall_parser import GenericLogParser
from feature_engineering import generate_feature_vector
from leakage_detection.dns_tunneling_detector import DNSTunnelingDetector
from leakage_detection.covert_channel_detector import CovertChannelDetector
from leakage_detection.beaconing_detector import BeaconingDetector
from leakage_detection.exfiltration_detector import ExfiltrationDetector
from risk_engine.risk_scoring import RiskEngine


# ================= CONFIG (FROM OLD CODE) =================
RAW_LOG_OUTPUT_DIR = "data/raw_logs"
PARSED_OUTPUT = "data/parsed_logs/logs.json"
HOSTNAME = "UPLOADED-SOURCE"
ANOMALY_THRESHOLD = 45
MAX_FLAGGED_ENTRIES = 200
REPORT_SNAPSHOTS_DIR = Path("data/report_snapshots")
REPORT_INDEX_PATH = Path("data/report_index.json")
RISK_CONFIG_PATH = Path("config/risk_scoring.yaml")
ALERT_CONFIG_PATH = Path("config/alert_config.yaml")
DEFAULT_RISK_CONFIG = {
    "risk_weights": {
        "anomaly_score": 0.4,
        "data_volume": 0.25,
        "destination_risk": 0.2,
        "temporal_anomaly": 0.15,
    },
    "severity_thresholds": {"LOW": 20, "MEDIUM": 45, "HIGH": 70, "CRITICAL": 85},
    "leakage_indicators": {
        "outbound_data_spike_mb": 50,
        "repeated_beaconing_count": 5,
    },
    "alerting": {"trigger_on_severity": ["HIGH", "CRITICAL"]},
}

def update_pipeline_status(stage, message):
    status = {
        "stage": stage,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }

    Path("data").mkdir(exist_ok=True)
    with open("data/pipeline_status.json", "w", encoding="utf-8") as f:
        json.dump(status, f, indent=4)
# ================= SAFE INTERNAL LOGIC =================
def load_yaml_config(path: Path, default: dict) -> dict:
    try:
        if not path.exists():
            return default
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(loaded, dict):
            merged = dict(default)
            merged.update(loaded)
            return merged
    except Exception:
        pass
    return default


def to_safe_dataframe(df):
    if df is None:
        return df
    safe = df.copy()
    defaults = {
        "timestamp": "",
        "protocol": "",
        "direction": "UNKNOWN",
        "src_ip": "",
        "dst_ip": "",
        "src_port": 0,
        "dst_port": 0,
        "bytes_sent": 0,
        "level": "",
        "action": "",
        "process_name": "",
        "line_number": 0,
        "message": "",
    }
    for col, val in defaults.items():
        if col not in safe.columns:
            safe[col] = val
    safe["bytes_sent"] = safe["bytes_sent"].fillna(0)
    safe["src_port"] = safe["src_port"].fillna(0)
    safe["dst_port"] = safe["dst_port"].fillna(0)
    safe["direction"] = safe["direction"].astype(str).str.upper()
    safe["protocol"] = safe["protocol"].astype(str).str.upper()
    safe["level"] = safe["level"].astype(str).str.upper()
    safe["action"] = safe["action"].astype(str).str.upper()
    return safe


def _normalize_score(value, max_value):
    if max_value <= 0:
        return 0
    return max(0, min((float(value) / float(max_value)) * 100, 100))


def anomaly_engine_stub(features: dict) -> tuple[int, list]:
    """
    Heuristic anomaly scoring using engineered features.
    Returns (score_0_to_100, component_breakdown).
    """
    if not features:
        return 0, []

    components = [
        ("data_volume", _normalize_score(features.get("total_bytes_sent", 0), 20 * 1024 * 1024), 0.25),
        ("error_ratio", _normalize_score(features.get("error_event_ratio", 0), 0.4), 0.2),
        ("off_hours_activity", _normalize_score(features.get("off_hours_ratio", 0), 0.5), 0.2),
        ("port_entropy", _normalize_score(features.get("port_entropy", 0), 4.0), 0.15),
        ("destination_entropy", _normalize_score(features.get("destination_entropy", 0), 5.0), 0.1),
        ("rare_processes", _normalize_score(features.get("rare_process_ratio", 0), 0.7), 0.1),
    ]

    weighted_score = sum(score * weight for _, score, weight in components)
    breakdown = [
        {"name": name, "signal": round(score, 2), "weight": weight, "contribution": round(score * weight, 2)}
        for name, score, weight in components
    ]
    return min(int(weighted_score), 100), breakdown


def leakage_detection_stub(df, risk_config: dict):
    """
    Runs leakage heuristics and returns normalized findings list.
    """
    if df is None or df.empty:
        return []

    thresholds = risk_config.get("leakage_indicators", {})
    detectors = [
        ExfiltrationDetector(threshold_mb=thresholds.get("outbound_data_spike_mb", 50)),
        BeaconingDetector(min_beacons=thresholds.get("repeated_beaconing_count", 5)),
        DNSTunnelingDetector(query_rate_threshold=20),
        CovertChannelDetector(entropy_threshold=1.5),
    ]

    findings = []
    for detector in detectors:
        try:
            result = detector.detect(df)
            if not result or not result.get("detected"):
                continue
            findings.append({
                "type": result.get("type", detector.__class__.__name__),
                "indicator": result.get("indicator", "Leakage indicator"),
                "details": result.get("details", ""),
                "confidence": result.get("confidence", "MEDIUM"),
                "score": int(result.get("score", 50)),
                "affected_lines": result.get("affected_lines", []),
            })
        except Exception as e:
            print(f"[WARN] Detector {detector.__class__.__name__} failed: {e}")

    return findings

def extract_flagged_entries_stub(df, score_for_attribution: int, leakage_findings: list | None = None):
    """
    Produces per-entry anomalies so the dashboard can show exactly
    which log rows were flagged by the model layer.
    """
    if df is None or df.empty:
        return []

    df_scored = df.copy()
    bytes_series = (
        df_scored["bytes_sent"]
        if "bytes_sent" in df_scored.columns
        else 0
    )
    bytes_series = bytes_series.fillna(0).astype(float) if hasattr(bytes_series, "fillna") else 0

    high_bytes_threshold = float(bytes_series.quantile(0.90)) if hasattr(bytes_series, "quantile") else 0

    if "level" not in df_scored.columns:
        df_scored["level"] = ""
    if "action" not in df_scored.columns:
        df_scored["action"] = ""
    if "line_number" not in df_scored.columns:
        df_scored["line_number"] = 0
    if "timestamp" not in df_scored.columns:
        df_scored["timestamp"] = ""
    if "direction" not in df_scored.columns:
        df_scored["direction"] = ""
    if "src_ip" not in df_scored.columns:
        df_scored["src_ip"] = ""
    if "dst_ip" not in df_scored.columns:
        df_scored["dst_ip"] = ""
    if "dst_port" not in df_scored.columns:
        df_scored["dst_port"] = 0

    leakage_findings = leakage_findings or []
    leakage_line_map = {}
    for finding in leakage_findings:
        finding_type = finding.get("type", "leakage")
        finding_score = int(finding.get("score", 0))
        for line_number in finding.get("affected_lines", []):
            if line_number not in leakage_line_map:
                leakage_line_map[line_number] = []
            leakage_line_map[line_number].append((finding_type, finding_score))

    flagged = []
    for row in df_scored.to_dict(orient="records"):
        reasons = []

        row_bytes = int(float(row.get("bytes_sent", 0) or 0))
        row_level = str(row.get("level", "")).upper()
        row_action = str(row.get("action", "")).upper()

        if row_bytes > 0 and row_bytes >= high_bytes_threshold:
            reasons.append("high_bytes_sent")
        if row_level in {"ERROR", "CRITICAL", "FATAL"}:
            reasons.append("error_level_event")
        if row_action in {"DENY", "BLOCK", "REJECT", "DROP"}:
            reasons.append("blocked_or_rejected_action")

        line_number = int(float(row.get("line_number", 0) or 0))
        line_leakage = leakage_line_map.get(line_number, [])
        if line_leakage:
            reasons.extend([f"leakage_{item[0]}" for item in line_leakage])

        if not reasons:
            continue

        confidence = "Low"
        if len(reasons) >= 2:
            confidence = "High"
        elif "high_bytes_sent" in reasons:
            confidence = "Medium"

        base_points = 0
        if "high_bytes_sent" in reasons:
            base_points += 40
        if "error_level_event" in reasons:
            base_points += 35
        if "blocked_or_rejected_action" in reasons:
            base_points += 25

        if high_bytes_threshold > 0 and row_bytes > 0:
            relative_bytes = min(row_bytes / high_bytes_threshold, 3.0)
            base_points += int(relative_bytes * 8)
        if line_leakage:
            base_points += int(sum(item[1] for item in line_leakage) / max(len(line_leakage), 1))

        flagged.append({
            "line_number": int(float(row.get("line_number", 0) or 0)),
            "timestamp": row.get("timestamp") or "",
            "direction": row.get("direction") or "UNKNOWN",
            "src_ip": row.get("src_ip") or "",
            "dst_ip": row.get("dst_ip") or "",
            "dst_port": int(float(row.get("dst_port", 0) or 0)),
            "bytes_sent": row_bytes,
            "reason": ", ".join(reasons),
            "confidence": confidence,
            "base_points": base_points,
        })

    total_base_points = sum(item.get("base_points", 0) for item in flagged)
    if total_base_points > 0 and score_for_attribution > 0:
        for item in flagged:
            raw_share = item.get("base_points", 0) / total_base_points
            contribution = round(raw_share * score_for_attribution, 2)
            item["risk_contribution"] = contribution
            item["risk_contribution_pct"] = round(raw_share * 100, 2)
    else:
        for item in flagged:
            item["risk_contribution"] = 0
            item["risk_contribution_pct"] = 0

    for item in flagged:
        item.pop("base_points", None)

    flagged.sort(
        key=lambda item: (item.get("risk_contribution", 0), item["bytes_sent"], item["line_number"]),
        reverse=True,
    )
    return flagged[:MAX_FLAGGED_ENTRIES]


def risk_engine_stub(anomaly_score: int, leakage_findings: list, feature_dict: dict):
    risk_config = load_yaml_config(RISK_CONFIG_PATH, DEFAULT_RISK_CONFIG)
    alert_yaml = load_yaml_config(ALERT_CONFIG_PATH, {})
    alert_settings = (alert_yaml.get("alerts") or {}) if isinstance(alert_yaml, dict) else {}
    email_cfg = alert_settings.get("email", {})
    siem_cfg = alert_settings.get("siem", {})

    runtime_alert_config = {
        "email_alerts": bool(email_cfg.get("enabled")) and bool(email_cfg.get("recipient")),
        "siem_export": bool(siem_cfg.get("enabled", True)),
        "smtp_server": email_cfg.get("smtp_server"),
        "smtp_port": email_cfg.get("smtp_port", 587),
        "smtp_username": email_cfg.get("username"),
        "smtp_password": email_cfg.get("password"),
        "email_sender": email_cfg.get("sender"),
        "email_recipient": email_cfg.get("recipient"),
        "siem_export_path": siem_cfg.get("export_path", "data/siem_exports"),
    }

    risk_engine = RiskEngine(risk_config, runtime_alert_config)
    return risk_engine.calculate_risk(
        anomaly_score=anomaly_score,
        leakage_findings=leakage_findings,
        context={
            "host": HOSTNAME,
            "total_bytes_sent": feature_dict.get("total_bytes_sent", 0),
            "off_hours_ratio": feature_dict.get("off_hours_ratio", 0),
        },
    )


def write_runtime_status(logs_processed, anomaly_score, leakage_count, severity, risk_score=None):
    status = {
        "last_run": datetime.utcnow().isoformat(),
        "logs_processed": logs_processed,
        "anomaly_score": anomaly_score,
        "risk_score": anomaly_score if risk_score is None else risk_score,
        "leakage_indicators": leakage_count,
        "severity": severity
    }

    Path("data").mkdir(exist_ok=True)
    with open("data/runtime_status.json", "w", encoding="utf-8") as f:
        json.dump(status, f, indent=4)


# ================= PIPELINE =================
def run_pipeline(log_path: str, source_name: str = ""):
    df = None
    leakage_findings = []
    anomaly_score = 0
    anomaly_breakdown = []
    flagged_entries = []
    risk_result = {}

    try:
        print("[1] Collecting Logs")

        log_path = Path(log_path)
        if not log_path.exists():
            raise FileNotFoundError(log_path)

        collector = LogCollector(
            log_path=str(log_path),
            output_dir=RAW_LOG_OUTPUT_DIR
        )
        collected_log = collector.collect()
        print("[OK] Log collected")
        update_pipeline_status("INGESTION", "Collecting logs")

        print("[2] Parsing Logs")
        parser = GenericLogParser()
        records = parser.parse_file(collected_log)
        update_pipeline_status("PARSING", "Parsing logs")
        import pandas as pd
        df = to_safe_dataframe(pd.DataFrame(records))
        
        Path("data/parsed_logs").mkdir(parents=True, exist_ok=True)
        df.to_json(PARSED_OUTPUT, orient="records", indent=2)
        print("[OK] Parsed logs saved")

        print("[3] Feature Engineering")
        feature_dict = generate_feature_vector(df)
        print("[OK] Feature vector generated")
        update_pipeline_status("FEATURE_ENGINEERING", "Generating feature vector")
        print("[4] Anomaly Detection")
        anomaly_score, anomaly_breakdown = anomaly_engine_stub(feature_dict)
        print(f"[OK] Anomaly Score: {anomaly_score}")
        update_pipeline_status("ANOMALY_DETECTION", f"Anomaly score: {anomaly_score}")
        print("[5] Leakage Detection")
        risk_config = load_yaml_config(RISK_CONFIG_PATH, DEFAULT_RISK_CONFIG)
        leakage_findings = leakage_detection_stub(df, risk_config)
        if leakage_findings:
            print("[WARN] Leakage indicators detected")
        else:
            print("[OK] No leakage indicators")

        print("[6] Risk Scoring & Alerts")
        risk_result = risk_engine_stub(anomaly_score, leakage_findings, feature_dict)
        risk_score = int(risk_result.get("risk_score", anomaly_score))
        flagged_entries = extract_flagged_entries_stub(df, risk_score, leakage_findings)
        update_pipeline_status("RISK_SCORING", "Calculating risk")
        update_pipeline_status("COMPLETED", "Analysis completed successfully")

        # Persist runtime status
        write_runtime_status(
            logs_processed=len(df),
            anomaly_score=anomaly_score,
            leakage_count=len(leakage_findings),
            severity=risk_result["severity"],
            risk_score=risk_score,
        )
        generate_html_report()

        # Persist event for dashboard
        Path("data/siem_exports").mkdir(parents=True, exist_ok=True)
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "host": HOSTNAME,
            "severity": risk_result.get("severity", "LOW"),
            "risk_score": risk_score,
            "alert_type": "Generic Log Analysis",
            "description": "Log analyzed successfully",
            "indicators": leakage_findings,
            "recommended_action": risk_result.get("explanation", {}).get("recommended_action", "Review logs"),
        }

        with open(
            f"data/siem_exports/event_{int(datetime.utcnow().timestamp())}.json",
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(event, f, indent=4)

        print("[OK] Pipeline execution completed")
        report_id = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        parsed_records = df.to_dict(orient="records")
        entries = build_entry_details_records(parsed_records, flagged_entries, leakage_findings)
        dashboard_result = {
            "report_id": report_id,
            "timestamp": datetime.utcnow().isoformat(),
            "host": HOSTNAME,
            "uploaded_file": source_name or Path(log_path).name,
            "anomaly_score": anomaly_score,
            "anomaly_breakdown": anomaly_breakdown,
            "risk_score": risk_score,
            "risk_breakdown": risk_result.get("breakdown", {}),
            "severity": risk_result.get("severity", "LOW"),
            "leakage_count": len(leakage_findings),
            "leakage_indicators": leakage_findings,
            "flagged_entries": flagged_entries,
            "explanation": risk_result.get("explanation", {}),
            "recommendation": risk_result.get("explanation", {}).get("recommended_action", ""),
        }
        write_analysis_result(dashboard_result)
        append_history(dashboard_result)
        persist_report_snapshot(
            report_id=report_id,
            metadata={
                "report_id": report_id,
                "timestamp": dashboard_result["timestamp"],
                "uploaded_file": dashboard_result["uploaded_file"],
                "severity": dashboard_result["severity"],
                "risk_score": dashboard_result["risk_score"],
                "anomaly_score": dashboard_result["anomaly_score"],
            },
            analysis=dashboard_result,
            entries=entries,
        )

    except Exception as e:
        print("[ERROR] Pipeline execution failed")
        print(str(e))
        traceback.print_exc()
        update_pipeline_status("ERROR", "Pipeline execution failed")

        write_runtime_status(0, 0, 0, "ERROR")


def write_analysis_result(result: dict):
    path = Path("data/analysis_result.json")
    path.parent.mkdir(exist_ok=True)

    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    tmp.replace(path)


def build_entry_details_records(parsed_logs, flagged_entries, leakage_indicators):
    flagged_by_line = {}
    for flagged in flagged_entries or []:
        line_number = flagged.get("line_number")
        if line_number is not None:
            flagged_by_line[int(line_number)] = flagged

    leakage_by_line = {}
    for indicator in leakage_indicators or []:
        indicator_type = indicator.get("type", "leakage")
        indicator_confidence = indicator.get("confidence", "")
        for line_number in indicator.get("affected_lines", []) or []:
            key = int(line_number)
            if key not in leakage_by_line:
                leakage_by_line[key] = []
            leakage_by_line[key].append({
                "type": indicator_type,
                "confidence": indicator_confidence,
            })

    rows = []
    for idx, row in enumerate(parsed_logs or [], start=1):
        record = row if isinstance(row, dict) else {}
        line_number = int(record.get("line_number", idx) or idx)
        flagged = flagged_by_line.get(line_number, {})
        leakage_hits = leakage_by_line.get(line_number, [])

        rows.append({
            "line_number": line_number,
            "timestamp": record.get("timestamp", ""),
            "log_type": record.get("log_type", ""),
            "level": record.get("level", ""),
            "action": record.get("action", ""),
            "direction": record.get("direction", ""),
            "src_ip": record.get("src_ip", ""),
            "dst_ip": record.get("dst_ip", ""),
            "src_port": record.get("src_port", 0),
            "dst_port": record.get("dst_port", 0),
            "bytes_sent": record.get("bytes_sent", 0),
            "message": record.get("message", ""),
            "risk_flagged": bool(flagged),
            "risk_reason": flagged.get("reason", ""),
            "risk_confidence": flagged.get("confidence", ""),
            "risk_contribution": flagged.get("risk_contribution", 0),
            "risk_contribution_pct": flagged.get("risk_contribution_pct", 0),
            "leakage_flagged": len(leakage_hits) > 0,
            "leakage_types": ", ".join(sorted({item["type"] for item in leakage_hits})) if leakage_hits else "",
            "leakage_confidence": ", ".join(sorted({item["confidence"] for item in leakage_hits if item["confidence"]})) if leakage_hits else "",
        })

    rows.sort(key=lambda item: item["line_number"])
    return rows


def persist_report_snapshot(report_id: str, metadata: dict, analysis: dict, entries: list):
    REPORT_SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_path = REPORT_SNAPSHOTS_DIR / f"{report_id}.json"
    payload = {
        "report_id": report_id,
        "metadata": metadata,
        "analysis": analysis,
        "entries": entries,
    }
    snapshot_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    index = []
    if REPORT_INDEX_PATH.exists():
        try:
            index = json.loads(REPORT_INDEX_PATH.read_text(encoding="utf-8"))
        except Exception:
            index = []

    index = [item for item in index if item.get("report_id") != report_id]
    index.append(metadata)
    index.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
    REPORT_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_INDEX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")


def append_history(entry):
    history_file = Path("data/analysis_history.json")
    history = []

    if history_file.exists():
        try:
            history = json.loads(history_file.read_text())
        except:
            history = []

    history.append(entry)
    history_file.write_text(json.dumps(history, indent=2))

# ================= ENTRY POINT =================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERROR] No log path provided")
        sys.exit(0)

    source_name = ""
    if len(sys.argv) >= 4 and sys.argv[2] == "--source-name":
        source_name = sys.argv[3]

    run_pipeline(sys.argv[1], source_name=source_name)
