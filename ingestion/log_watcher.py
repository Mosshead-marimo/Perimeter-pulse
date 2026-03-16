# Placeholder for ingestion/log_watcher.py
"""
Real-Time Log Watcher
Monitors firewall logs for changes without altering evidence
"""

import time
from pathlib import Path
from datetime import datetime


class LogWatcher:
    def __init__(self, log_path: str, poll_interval: int = 5):
        self.log_path = Path(log_path)
        self.poll_interval = poll_interval
        self._last_size = self.log_path.stat().st_size if self.log_path.exists() else 0

    def watch(self):
        """
        Generator yielding new log lines in real time
        """
        while True:
            if not self.log_path.exists():
                time.sleep(self.poll_interval)
                continue

            current_size = self.log_path.stat().st_size

            if current_size > self._last_size:
                with open(self.log_path, "r") as f:
                    f.seek(self._last_size)
                    new_data = f.read()
                    self._last_size = current_size

                    for line in new_data.splitlines():
                        yield {
                            "timestamp": datetime.utcnow().isoformat(),
                            "raw_log": line
                        }

            time.sleep(self.poll_interval)
