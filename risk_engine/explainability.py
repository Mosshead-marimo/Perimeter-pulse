# Placeholder for risk_engine/explainability.py
"""
Explainability Engine
Produces human-readable explanations for alerts and reports
"""

class ExplainabilityEngine:
    def generate(
        self,
        anomaly_score: float,
        leakage_findings: list,
        severity: str
    ) -> dict:
        reasons = []

        if anomaly_score > 50:
            reasons.append("Significant deviation from normal network behavior")

        for finding in leakage_findings:
            reasons.append(finding.get("indicator", "Unknown leakage indicator"))

        summary = (
            f"Severity level {severity} assigned due to anomalous firewall behavior "
            f"and detected leakage indicators."
        )

        recommendation = self._recommend_action(severity)

        return {
            "summary": summary,
            "reasons": reasons,
            "recommended_action": recommendation
        }

    @staticmethod
    def _recommend_action(severity: str) -> str:
        actions = {
            "LOW": "Continue monitoring the system.",
            "MEDIUM": "Review traffic patterns and affected processes.",
            "HIGH": "Isolate host and begin forensic investigation.",
            "CRITICAL": "Immediately disconnect system and initiate incident response."
        }
        return actions.get(severity, "Review system activity.")
