# Placeholder for alerts/siem_export.py
"""
SIEM Export Module
Exports alerts in JSON format for SIEM ingestion
(Splunk, QRadar, Elastic, Sentinel, etc.)
"""

import json
from pathlib import Path
from datetime import datetime


class SIEMExporter:
    def __init__(self, config: dict):
        self.export_path = Path(
            config.get("siem_export_path", "data/siem_exports")
        )
        self.export_path.mkdir(parents=True, exist_ok=True)

    def export(self, alert: dict):
        filename = f"siem_alert_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        file_path = self.export_path / filename

        try:
            with open(file_path, "w") as f:
                json.dump(alert, f, indent=4)
        except Exception as e:
            print(f"[Alert Error] SIEM export failed: {e}")
