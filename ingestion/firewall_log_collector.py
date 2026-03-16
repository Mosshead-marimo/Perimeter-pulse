"""
Generic Log Collector
Responsible for securely collecting uploaded log files.
"""

from pathlib import Path
from datetime import datetime
import shutil


class LogCollector:
    def __init__(self, log_path: str, output_dir: str):
        self.log_path = Path(log_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def collect(self) -> str:
        """Copies a log file to a timestamped evidence-safe location."""
        if not self.log_path.exists():
            raise FileNotFoundError("Log file not found")

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        suffix = self.log_path.suffix if self.log_path.suffix else ".log"
        destination = self.output_dir / f"log_{timestamp}{suffix}"

        shutil.copy2(self.log_path, destination)

        return str(destination)


# Backward-compatible alias
FirewallLogCollector = LogCollector
