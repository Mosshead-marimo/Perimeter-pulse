# Placeholder for scripts/analyze_logs.py
"""
Analyze Logs Script
Runs the full detection pipeline
"""

import pandas as pd
import numpy as np

from parsing.firewall_parser import FirewallLogParser
from parsing.normalizer import LogNormalizer
from feature_engineering import generate_feature_vector
from models.model_registry import ModelRegistry
from anomaly_detection.anomaly_engine import AnomalyEngine
from leakage_detection.exfiltration_detector import ExfiltrationDetector
from leakage_detection.dns_tunneling_detector import DNSTunnelingDetector
from leakage_detection.beaconing_detector import BeaconingDetector
from leakage_detection.covert_channel_detector import CovertChannelDetector
from risk_engine.risk_scoring import RiskEngine

# ---------------- CONFIG ----------------
FIREWALL_LOG = "data/raw_logs/pfirewall.log"
HOSTNAME = "WIN-CLIENT-01"

MODEL_CONFIG = {
    "isolation_forest": {"enabled": True},
    "one_class_svm": {"enabled": True},
    "autoencoder": {"enabled": False}
}

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
# ----------------------------------------


def main():
    print("[+] Running log analysis...")

    parser = FirewallLogParser()
    normalizer = LogNormalizer()

    records = parser.parse_file(FIREWALL_LOG)
    df = normalizer.normalize(records)

    feature_dict = generate_feature_vector(df.to_dict(orient="records"))
    X = np.array(list(feature_dict.values())).reshape(1, -1)

    registry = ModelRegistry(MODEL_CONFIG)
    models = registry.initialize(feature_dim=X.shape[1])
    registry.train_all(X)

    anomaly_engine = AnomalyEngine(models, config={})
    anomaly_result = anomaly_engine.detect(X.flatten())

    detectors = [
        ExfiltrationDetector(),
        DNSTunnelingDetector(),
        BeaconingDetector(),
        CovertChannelDetector()
    ]

    leakage_findings = []
    for detector in detectors:
        res = detector.detect(df)
        if res.get("detected"):
            leakage_findings.append(res)

    risk_engine = RiskEngine(RISK_CONFIG)
    risk_result = risk_engine.calculate_risk(
        anomaly_score=int(anomaly_result["ensemble_score"] * 100),
        leakage_findings=leakage_findings,
        context={"host": HOSTNAME}
    )

    print("[✓] Analysis completed")
    print(risk_result)


if __name__ == "__main__":
    main()
