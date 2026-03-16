# Placeholder for anomaly_detection/ensemble_logic.py
"""
Ensemble Logic
Combines anomaly scores from multiple models
using weighted voting.
"""

class EnsembleDecision:
    def __init__(self, config: dict):
        self.weights = config.get("model_weights", {
            "isolation_forest": 0.4,
            "one_class_svm": 0.4,
            "autoencoder": 0.2
        })

    def combine(self, model_scores: dict) -> float:
        """
        Weighted anomaly score aggregation
        """
        total_score = 0.0
        total_weight = 0.0

        for model_name, score in model_scores.items():
            weight = self.weights.get(model_name, 0)
            total_score += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return total_score / total_weight
