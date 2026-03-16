# Placeholder for forensics/evidence_export.py
"""
Evidence Export Module
Packages logs, alerts, and models as forensic evidence
"""

import shutil
from pathlib import Path
from datetime import datetime


class EvidenceExporter:
    def __init__(self, case_id: str):
        self.case_id = case_id
        self.export_root = Path(f"forensic_cases/{case_id}")
        self.export_root.mkdir(parents=True, exist_ok=True)

    def export_file(self, source_path: str, category: str):
        category_path = self.export_root / category
        category_path.mkdir(exist_ok=True)

        destination = category_path / Path(source_path).name
        shutil.copy2(source_path, destination)

        return str(destination)

    def export_metadata(self, metadata: dict):
        metadata_path = self.export_root / "metadata.json"
        metadata["exported_at"] = datetime.utcnow().isoformat()

        with open(metadata_path, "w") as f:
            import json
            json.dump(metadata, f, indent=4)

        return str(metadata_path)
