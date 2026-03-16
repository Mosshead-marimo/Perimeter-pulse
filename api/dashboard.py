from flask import Blueprint, request, jsonify, session
from pathlib import Path
import subprocess, sys, time, json

dashboard_bp = Blueprint("dashboard", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
REPORT_SNAPSHOTS_DIR = DATA_DIR / "report_snapshots"
REPORT_INDEX_PATH = DATA_DIR / "report_index.json"
ANALYSIS_RESULT_PATH = DATA_DIR / "analysis_result.json"
RUNTIME_STATUS_PATH = DATA_DIR / "runtime_status.json"
PARSED_LOGS_PATH = DATA_DIR / "parsed_logs" / "logs.json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def safe_json(path, default):
    try:
        if not path.exists() or path.stat().st_size == 0:
            return default
        return json.loads(path.read_text())
    except Exception:
        return default


def build_entry_details(parsed_logs, analysis):
    if not isinstance(parsed_logs, list):
        return []

    flagged_entries = analysis.get("flagged_entries", []) if isinstance(analysis, dict) else []
    leakage_indicators = analysis.get("leakage_indicators", []) if isinstance(analysis, dict) else []
    flagged_by_line = {}
    for flagged in flagged_entries:
        line_number = flagged.get("line_number")
        if line_number is not None:
            flagged_by_line[int(line_number)] = flagged
    leakage_by_line = {}
    for indicator in leakage_indicators:
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

    entry_details = []
    for idx, row in enumerate(parsed_logs, start=1):
        record = row if isinstance(row, dict) else {}
        line_number = int(record.get("line_number", idx) or idx)
        flagged = flagged_by_line.get(line_number, {})
        leakage_hits = leakage_by_line.get(line_number, [])

        entry_details.append({
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

    entry_details.sort(key=lambda item: item["line_number"])
    return entry_details


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_reports_with_legacy(report_index, history):
    index_reports = report_index if isinstance(report_index, list) else []
    history_reports = history if isinstance(history, list) else []

    merged = []
    seen = set()

    for report in index_reports:
        report_id = report.get("report_id")
        if not report_id:
            continue
        seen.add(report_id)
        merged.append({
            "report_id": report_id,
            "timestamp": report.get("timestamp", ""),
            "uploaded_file": report.get("uploaded_file", "Uploaded Log"),
            "severity": report.get("severity", "N/A"),
            "risk_score": report.get("risk_score", report.get("anomaly_score", 0)),
            "source": "snapshot",
        })

    for item in history_reports:
        timestamp = item.get("timestamp", "")
        if not timestamp:
            continue
        legacy_id = f"legacy-{timestamp}"
        if legacy_id in seen:
            continue
        merged.append({
            "report_id": legacy_id,
            "timestamp": timestamp,
            "uploaded_file": item.get("uploaded_file", "Legacy Report"),
            "severity": item.get("severity", "N/A"),
            "risk_score": item.get("risk_score", item.get("anomaly_score", 0)),
            "source": "history",
        })
        seen.add(legacy_id)

    merged.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
    return merged

@dashboard_bp.route("/upload", methods=["POST"])
def upload():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401

    f = request.files.get("file")
    if not f:
        return {"error": "No file"}, 400

    original_name = f.filename or ""
    suffix = Path(original_name).suffix if original_name else ""
    p = UPLOAD_DIR / f"upload_{int(time.time())}{suffix}"
    f.save(p)

    # Reset live view so a new file starts from a blank analysis state.
    write_json(
        ANALYSIS_RESULT_PATH,
        {
            "status": "PROCESSING",
            "uploaded_file": original_name or p.name,
            "timestamp": "",
            "anomaly_score": 0,
            "risk_score": 0,
            "severity": "N/A",
            "recommendation": "",
            "flagged_entries": [],
            "leakage_indicators": [],
            "anomaly_breakdown": [],
            "risk_breakdown": {},
            "explanation": {},
        },
    )
    write_json(
        RUNTIME_STATUS_PATH,
        {
            "last_run": "",
            "logs_processed": 0,
            "anomaly_score": 0,
            "risk_score": 0,
            "leakage_indicators": 0,
            "severity": "PROCESSING",
        },
    )
    write_json(PARSED_LOGS_PATH, [])

    subprocess.Popen(
        [sys.executable, "pipeline.py", str(p), "--source-name", original_name],
        cwd=BASE_DIR,
    )
    return {"status": "pipeline_started"}

@dashboard_bp.route("/data")
def data():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401

    history = safe_json(DATA_DIR / "analysis_history.json", [])
    report_index = safe_json(REPORT_INDEX_PATH, [])
    reports = build_reports_with_legacy(report_index, history)
    requested_report_id = request.args.get("report_id")
    live_analysis = safe_json(ANALYSIS_RESULT_PATH, {})

    if not requested_report_id and isinstance(live_analysis, dict) and live_analysis.get("status") == "PROCESSING":
        return {
            "analysis": live_analysis,
            "runtime": safe_json(RUNTIME_STATUS_PATH, {}),
            "history": history,
            "entries": [],
            "reports": reports,
            "selected_report_id": "",
        }

    selected_report_id = requested_report_id
    if not selected_report_id and reports:
        selected_report_id = reports[0].get("report_id")

    analysis = {}
    entries = []
    if selected_report_id:
        if selected_report_id.startswith("legacy-"):
            legacy_timestamp = selected_report_id[len("legacy-"):]
            analysis = next(
                (item for item in history if item.get("timestamp") == legacy_timestamp),
                {},
            )
            analysis = dict(analysis) if isinstance(analysis, dict) else {}
            analysis.setdefault("report_id", selected_report_id)
            analysis.setdefault("uploaded_file", "Legacy Report")
            analysis["report_source"] = "history"
            analysis.setdefault("explanation", {
                "summary": "Legacy report loaded from history (entry-level snapshot unavailable).",
                "reasons": [],
                "recommended_action": analysis.get("recommendation", ""),
            })
            entries = []
        else:
            snapshot = safe_json(REPORT_SNAPSHOTS_DIR / f"{selected_report_id}.json", {})
            analysis = snapshot.get("analysis", {}) if isinstance(snapshot, dict) else {}
            entries = snapshot.get("entries", []) if isinstance(snapshot, dict) else []

    if not analysis:
        # Fallback for older runs before snapshot support
        analysis = live_analysis or safe_json(DATA_DIR / "analysis_result.json", {})
        parsed_logs = safe_json(DATA_DIR / "parsed_logs" / "logs.json", [])
        entries = build_entry_details(parsed_logs, analysis)

    return {
        "analysis": analysis,
        "runtime": safe_json(DATA_DIR / "runtime_status.json", {}),
        "history": history,
        "entries": entries,
        "reports": reports,
        "selected_report_id": selected_report_id,
    }
