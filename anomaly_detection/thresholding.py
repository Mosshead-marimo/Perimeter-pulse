# Placeholder for anomaly_detection/thresholding.py
"""
Dynamic Thresholding
Determines whether a given score represents an anomaly
based on adaptive thresholds.
"""

import numpy as np


class DynamicThreshold:
    def __init__(self, config: dict):
        self.method = config.get("threshold_method", "zscore")
        self.sensitivity = config.get("sensitivity", 2.5)
        self.baseline_scores = []

    def update_baseline(self, score: float):
        """
        Update baseline distribution during learning phase
        """
        self.baseline_scores.append(score)

    def is_anomalous(self, score: float) -> bool:
        """
        Determine anomaly using adaptive logic
        """
        if not self.baseline_scores:
            return False

        mean = np.mean(self.baseline_scores)
        std = np.std(self.baseline_scores)

        if std == 0:
            return False

        z_score = (score - mean) / std
        return z_score > self.sensitivity
