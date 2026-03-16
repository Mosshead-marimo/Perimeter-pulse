# Placeholder for ingestion/eventlog_collector.py
"""
Windows Event Log Collector (Optional Enhancement)
Collects Security & System event logs relevant to network activity
"""

import subprocess
from pathlib import Path
from datetime import datetime


class EventLogCollector:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def collect(self, log_type: str = "Security") -> str:
        """
        Exports Windows Event Logs using wevtutil
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        output_file = self.output_dir / f"{log_type}_events_{timestamp}.evtx"

        command = [
            "wevtutil",
            "epl",
            log_type,
            str(output_file)
        ]

        subprocess.run(command, capture_output=True, text=True)

        return str(output_file)
