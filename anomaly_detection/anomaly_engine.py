# Placeholder for anomaly_detection/anomaly_engine.py
"""
Anomaly Detection Engine
Coordinates anomaly detection using multiple models
and produces a unified anomaly score.
"""

import numpy as np
from anomaly_detection.ensemble_logic import EnsembleDecision
from anomaly_detection.thresholding import DynamicThreshold


class AnomalyEngine:
    def __init__(self, models: dict, config: dict):
        """
        models: {
            "isolation_forest": model,
            "one_class_svm": model,
            "autoencoder": model (optional)
        }
        """
        self.models = models
        self.ensemble = EnsembleDecision(config)
        self.threshold = DynamicThreshold(config)

    def detect(self, feature_vector: np.ndarray) -> dict:
        """
        Run anomaly detection on a single feature vector
        """
        model_scores = {}

        for name, model in self.models.items():
            score = self._score_model(model, feature_vector)
            model_scores[name] = score

        ensemble_score = self.ensemble.combine(model_scores)
        anomaly_flag = self.threshold.is_anomalous(ensemble_score)

        return {
            "anomaly": anomaly_flag,
            "ensemble_score": ensemble_score,
            "model_scores": model_scores
        }

    def _score_model(self, model, feature_vector: np.ndarray) -> float:
        """
        Normalize model outputs to a common anomaly score scale
        """
        try:
            raw_score = model.decision_function(feature_vector.reshape(1, -1))[0]
            return abs(raw_score)
        except Exception:
            # Fallback for reconstruction-based models
            reconstructed = model.predict(feature_vector.reshape(1, -1))
            return float(np.mean((feature_vector - reconstructed[0]) ** 2))
