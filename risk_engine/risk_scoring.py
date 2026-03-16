"""
Risk Scoring Engine
Fuses anomaly scores and leakage indicators into a unified risk score
"""

from risk_engine.severity_classifier import SeverityClassifier
from risk_engine.explainability import ExplainabilityEngine
from alerts.alert_manager import AlertManager


class RiskEngine:
    def __init__(self, risk_config: dict, alert_config: dict | None = None):
        self.weights = risk_config["risk_weights"]
        self.severity_classifier = SeverityClassifier(
            risk_config["severity_thresholds"]
        )
        self.explainability = ExplainabilityEngine()
        self.alert_manager = AlertManager(alert_config) if alert_config else None
        self.alert_triggers = risk_config["alerting"]["trigger_on_severity"]

    def calculate_risk(
        self,
        anomaly_score: float,
        leakage_findings: list,
        context: dict
    ) -> dict:
        """
        Computes overall risk score and severity
        """

        anomaly_component = float(anomaly_score) * float(self.weights.get("anomaly_score", 0.4))

        leakage_scores = [float(item.get("score", 0)) for item in leakage_findings if isinstance(item, dict)]
        leakage_intensity = min(sum(leakage_scores) / max(len(leakage_scores), 1), 100) if leakage_scores else 0
        leakage_component = leakage_intensity * float(self.weights.get("destination_risk", 0.2))

        total_bytes = float(context.get("total_bytes_sent", 0))
        data_volume_mb = total_bytes / (1024 * 1024)
        data_volume_signal = min((data_volume_mb / 50.0) * 100, 100)
        data_volume_component = data_volume_signal * float(self.weights.get("data_volume", 0.25))

        off_hours_ratio = float(context.get("off_hours_ratio", 0))
        temporal_signal = min(max(off_hours_ratio, 0), 1) * 100
        temporal_component = temporal_signal * float(self.weights.get("temporal_anomaly", 0.15))

        risk_score = min(int(anomaly_component + leakage_component + data_volume_component + temporal_component), 100)

        severity = self.severity_classifier.classify(risk_score)

        explanation = self.explainability.generate(
            anomaly_score=anomaly_score,
            leakage_findings=leakage_findings,
            severity=severity
        )

        result = {
            "risk_score": risk_score,
            "severity": severity,
            "explanation": explanation,
            "leakage_indicators": leakage_findings,
            "breakdown": {
                "anomaly_component": round(anomaly_component, 2),
                "leakage_component": round(leakage_component, 2),
                "data_volume_component": round(data_volume_component, 2),
                "temporal_component": round(temporal_component, 2),
            },
        }

        if self.alert_manager and severity in self.alert_triggers:
            self.alert_manager.generate_alert({
                "host": context.get("host"),
                "severity": severity,
                "risk_score": risk_score,
                "alert_type": "Information Leakage Risk",
                "description": explanation["summary"],
                "indicators": leakage_findings,
                "recommended_action": explanation["recommended_action"]
            })

        return result
