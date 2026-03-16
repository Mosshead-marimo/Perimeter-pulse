"""
Severity Classification
Maps numerical risk scores to human-readable severity
"""

class SeverityClassifier:
    def __init__(self, thresholds: dict):
        self.thresholds = thresholds

    def classify(self, risk_score: int) -> str:
        if risk_score >= self.thresholds["CRITICAL"]:
            return "CRITICAL"
        elif risk_score >= self.thresholds["HIGH"]:
            return "HIGH"
        elif risk_score >= self.thresholds["MEDIUM"]:
            return "MEDIUM"
        else:
            return "LOW"
