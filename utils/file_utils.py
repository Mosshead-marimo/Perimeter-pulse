# Placeholder for utils/file_utils.py
"""
File Utilities
Handles hashing, safe file operations, and integrity checks
"""

import hashlib
from pathlib import Path


def sha256_hash(file_path: str) -> str:
    """
    Calculate SHA-256 hash of a file
    """
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()
    except FileNotFoundError:
        return "FILE_NOT_FOUND"


def safe_write(path: str, data: str):
    """
    Safely write data to file, creating directories if needed
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(data)


def file_exists(path: str) -> bool:
    """
    Check if file exists
    """
    return Path(path).exists()
