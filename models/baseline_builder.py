# Placeholder for models/baseline_builder.py
"""
Baseline Builder
Creates behavioral baselines from normal firewall activity
"""

import numpy as np
import pickle
from pathlib import Path


class BaselineBuilder:
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.baseline_scores = []

    def update(self, anomaly_score: float):
        self.baseline_scores.append(anomaly_score)

    def save(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "wb") as f:
            pickle.dump({
                "mean": np.mean(self.baseline_scores),
                "std": np.std(self.baseline_scores),
                "scores": self.baseline_scores
            }, f)

    @staticmethod
    def load(path: str) -> dict:
        with open(path, "rb") as f:
            return pickle.load(f)
