# Placeholder for forensics/chain_of_custody.py
"""
Chain of Custody Management
Maintains forensic integrity and traceability of evidence
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path


class ChainOfCustody:
    def __init__(self, case_id: str, investigator: str):
        self.case_id = case_id
        self.investigator = investigator
        self.created_at = datetime.utcnow().isoformat()
        self.entries = []

    def add_entry(self, evidence_path: str, action: str):
        hash_value = self._calculate_hash(evidence_path)

        entry = {
            "case_id": self.case_id,
            "timestamp": datetime.utcnow().isoformat(),
            "investigator": self.investigator,
            "action": action,
            "evidence_path": evidence_path,
            "sha256": hash_value
        }

        self.entries.append(entry)

    def export(self, output_path: str):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump({
                "case_id": self.case_id,
                "created_at": self.created_at,
                "entries": self.entries
            }, f, indent=4)

    @staticmethod
    def _calculate_hash(file_path: str) -> str:
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for block in iter(lambda: f.read(4096), b""):
                    sha256.update(block)
            return sha256.hexdigest()
        except FileNotFoundError:
            return "FILE_NOT_FOUND"
