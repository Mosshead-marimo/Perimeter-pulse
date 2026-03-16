from pathlib import Path
import json
from datetime import datetime

REPORT_DIR = Path("data/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def generate_html_report():
    status_file = Path("data/runtime_status.json")
    events_dir = Path("data/siem_exports")

    if not status_file.exists():
        return None

    with open(status_file, "r", encoding="utf-8") as f:
        status = json.load(f)

    events = []
    for file in events_dir.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            events.append(json.load(f))

    latest_event = sorted(events, key=lambda x: x["timestamp"])[-1] if events else {}

    report_html = f"""
    <html>
    <head>
        <title>Log Analyzer Report</title>
        <style>
            body {{ font-family: Arial; padding: 20px; }}
            h1 {{ color: #2c3e50; }}
            .box {{ border: 1px solid #ccc; padding: 15px; margin-bottom: 15px; }}
        </style>
    </head>
    <body>
        <h1>Log Analysis Report</h1>
        <p><b>Generated:</b> {datetime.utcnow().isoformat()} UTC</p>

        <div class="box">
            <h2>System Summary</h2>
            <p><b>Severity:</b> {status["severity"]}</p>
            <p><b>Anomaly Score:</b> {status["anomaly_score"]}</p>
            <p><b>Logs Processed:</b> {status["logs_processed"]}</p>
        </div>

        <div class="box">
            <h2>Risk Decision</h2>
            <pre>{json.dumps(latest_event, indent=2)}</pre>
        </div>
    </body>
    </html>
    """

    report_path = REPORT_DIR / f"log_report_{int(datetime.utcnow().timestamp())}.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_html)

    return report_path
