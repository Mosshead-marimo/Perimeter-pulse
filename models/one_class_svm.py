# Placeholder for models/one_class_svm.py
"""
One-Class SVM Model Wrapper
"""

from sklearn.svm import OneClassSVM


class OneClassSVMModel:
    def __init__(self, config: dict):
        self.model = OneClassSVM(
            kernel=config.get("kernel", "rbf"),
            nu=config.get("nu", 0.05),
            gamma=config.get("gamma", "scale")
        )

    def train(self, X):
        self.model.fit(X)

    def decision_function(self, X):
        return self.model.decision_function(X)
