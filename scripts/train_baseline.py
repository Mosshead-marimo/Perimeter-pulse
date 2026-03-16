# Placeholder for scripts/train_baseline.py
"""
Train Baseline Script
Builds baseline anomaly score distribution from normal traffic
"""

import json
import numpy as np

from parsing.firewall_parser import FirewallLogParser
from parsing.normalizer import LogNormalizer
from feature_engineering import generate_feature_vector
from models.model_registry import ModelRegistry
from anomaly_detection.anomaly_engine import AnomalyEngine
from models.baseline_builder import BaselineBuilder

# ---------------- CONFIG ----------------
FIREWALL_LOG = "data/raw_logs/pfirewall.log"
BASELINE_OUTPUT = "data/baselines/system_baseline.pkl"

MODEL_CONFIG = {
    "isolation_forest": {"enabled": True},
    "one_class_svm": {"enabled": True},
    "autoencoder": {"enabled": False}
}
# ----------------------------------------


def main():
    print("[+] Training baseline...")

    parser = FirewallLogParser()
    normalizer = LogNormalizer()

    records = parser.parse_file(FIREWALL_LOG)
    df = normalizer.normalize(records)

    features = generate_feature_vector(df.to_dict(orient="records"))
    X = np.array(list(features.values())).reshape(1, -1)

    registry = ModelRegistry(MODEL_CONFIG)
    models = registry.initialize(feature_dim=X.shape[1])
    registry.train_all(X)

    anomaly_engine = AnomalyEngine(models, config={})
    baseline = BaselineBuilder(BASELINE_OUTPUT)

    result = anomaly_engine.detect(X.flatten())
    baseline.update(result["ensemble_score"])
    baseline.save()

    print("[✓] Baseline training completed")


if __name__ == "__main__":
    main()
