"""
Feature Engineering Orchestrator
"""

import pandas as pd

from feature_engineering.traffic_features import extract_traffic_features
from feature_engineering.temporal_features import extract_temporal_features
from feature_engineering.entropy_features import extract_entropy_features
from feature_engineering.process_features import extract_process_features


def generate_feature_vector(parsed_logs: list) -> dict:
    """Converts parsed logs into a single feature vector."""
    if isinstance(parsed_logs, pd.DataFrame):
        df = parsed_logs.copy()
    else:
        df = pd.DataFrame(parsed_logs)

    features = {}
    features.update(extract_traffic_features(df))
    features.update(extract_temporal_features(df))
    features.update(extract_entropy_features(df))
    features.update(extract_process_features(df))

    return features
