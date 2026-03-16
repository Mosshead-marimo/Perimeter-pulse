# Placeholder for forensics/incident_report.py
"""
Incident Report Generator
Creates structured, human-readable forensic reports
"""

from datetime import datetime
from pathlib import Path


class IncidentReport:
    def __init__(self, case_id: str):
        self.case_id = case_id
        self.sections = []

    def add_section(self, title: str, content: str):
        self.sections.append({
            "title": title,
            "content": content
        })

    def generate(self, output_path: str):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as report:
            report.write(f"INCIDENT REPORT\n")
            report.write(f"Case ID: {self.case_id}\n")
            report.write(f"Generated At: {datetime.utcnow().isoformat()}\n")
            report.write("=" * 60 + "\n\n")

            for section in self.sections:
                report.write(section["title"].upper() + "\n")
                report.write("-" * len(section["title"]) + "\n")
                report.write(section["content"] + "\n\n")

        return output_path
