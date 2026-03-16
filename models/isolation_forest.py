# Placeholder for models/isolation_forest.py
"""
Isolation Forest Model Wrapper
"""

from sklearn.ensemble import IsolationForest


class IsolationForestModel:
    def __init__(self, config: dict):
        self.model = IsolationForest(
            n_estimators=config.get("n_estimators", 150),
            contamination=config.get("contamination", 0.03),
            random_state=config.get("random_state", 42)
        )

    def train(self, X):
        self.model.fit(X)

    def decision_function(self, X):
        return self.model.decision_function(X)
