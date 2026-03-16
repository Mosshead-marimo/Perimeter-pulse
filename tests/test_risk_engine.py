# Placeholder for tests/test_risk_engine.py
"""
Tests for risk scoring and severity classification
"""

from risk_engine.risk_scoring import RiskEngine


RISK_CONFIG = {
    "risk_weights": {
        "anomaly_score": 0.6,
        "destination_risk": 0.4
    },
    "severity_thresholds": {
        "LOW": 20,
        "MEDIUM": 45,
        "HIGH": 70,
        "CRITICAL": 85
    },
    "alerting": {
        "trigger_on_severity": ["HIGH", "CRITICAL"]
    }
}


def test_risk_score_calculation():
    engine = RiskEngine(RISK_CONFIG)

    result = engine.calculate_risk(
        anomaly_score=80,
        leakage_findings=[
            {"indicator": "High outbound data volume"}
        ],
        context={"host": "TEST-HOST"}
    )

    assert result["risk_score"] >= 40
    assert result["severity"] in ["MEDIUM", "HIGH", "CRITICAL"]


def test_explainability_output():
    engine = RiskEngine(RISK_CONFIG)

    result = engine.calculate_risk(
        anomaly_score=90,
        leakage_findings=[],
        context={}
    )

    explanation = result["explanation"]
    assert "summary" in explanation
    assert "recommended_action" in explanation
